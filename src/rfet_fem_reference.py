# -*- coding: utf-8 -*-
"""
rfet_fem_reference.py
================================================================================
STEP 3-B : DEVSIM 과 독립적인 "참조 solver" — 같은 .msh 위에서 Poisson 을 1차 유한요소법(P1 FEM)으로 푼다.

왜 따로 만드는가
  1) 교차 검증: DEVSIM(유한체적, edge 기반)과 이 코드(유한요소, 삼각형 기반)는 이산화 방식이 다르다.
     같은 mesh, 같은 ε, 같은 경계조건으로 두 결과가 일치하면 "코드가 맞다"는 근거가 하나 더 생긴다.
  2) 이방성: FEM 은 요소마다 ε 를 2x2 텐서로 넣는 것이 자연스럽다. DEVSIM 기본 이산화는 스칼라 ε 라서
     (원칙 8) 스칼라 단순화의 오차를 이 코드로 숫자로 잴 수 있다.
  3) 이 코드는 numpy/scipy 만 쓰므로 DEVSIM 없이도 돌아간다.

풀이하는 식 (물리 모델)
  ∇·(ε ∇ψ) = 0      (ρ = 0, rfet_materials.RHO_MODEL 참조)
  금속 접점: ψ = V_metal (Dirichlet).  그 외 외곽: ∂ψ/∂n = 0 (Neumann, 자연 경계조건).
  계면: ψ 연속, (ε∇ψ)·n 연속 -> FEM 에서는 노드를 공유하고 요소마다 ε 를 다르게 두면 자동으로 만족된다.

수치 방법 (수치해석 설정)
  P1(선형) 삼각형 요소. 요소 강성행렬 K_e = A_e · Bᵀ ε B  (B: 2x3 기울기 행렬, A_e: 면적).
  희소 행렬 조립 후 Dirichlet 노드를 소거하고 직접법(spsolve)으로 푼다.
  단위: 좌표 nm, ε 는 상대값. ρ = 0 이면 ε0 과 길이 단위가 해에 영향을 주지 않는다 (ψ 는 V).

실행:  python rfet_fem_reference.py selftest                  (2층 평행판 해석해와 비교)
       python rfet_fem_reference.py bridge [perp|para|tensor] (rfet_bridge_nm.msh 풀이 -> rfet_fem_bridge_<variant>.npz)
"""
import math
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import rfet_geometry as geo
import rfet_materials as mat
import rfet_mesh_tools as tools


# ==============================================================================
# 섹션 1. 편향(bias) 정의 — 단위 응답
#   ρ = 0 이면 문제가 선형이므로 "금속 i 에 1 V, 나머지 0 V" 인 해 ψ_i 네 개만 있으면
#   임의의 (V_S, V_D, V_TG, V_BG) 의 해는 ψ = V_S ψ_S + V_D ψ_D + V_TG ψ_TG + V_BG ψ_BG 이다.
#   (금속 일함수 차이는 상수 오프셋이라 이 "응답"에는 들어오지 않는다 — rfet_materials 섹션 5)
# ==============================================================================
UNIT_CASES = {m: {m: 1.0} for m in geo.METALS}      # {"Source": {"Source":1.0}, "Drain": {...}, "TG": ..., "BG": ...}


def contact_voltages(bias):
    """{금속: 전압} 을 받아 모든 금속에 대해 전압을 돌려준다 (없으면 0 V)."""
    return {m: float(bias.get(m, 0.0)) for m in geo.METALS}


# ==============================================================================
# 섹션 2. P1 FEM
# ==============================================================================
def element_matrices(xy, tri):
    """모든 삼각형의 면적 A (M,) 와 기울기 행렬 B (M, 2, 3): ∇φ_k = B[:, :, k]"""
    a, b, c = xy[tri[:, 0]], xy[tri[:, 1]], xy[tri[:, 2]]
    det = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
    area = 0.5 * det
    if np.any(area <= 0):
        raise ValueError("면적이 0 이하인 삼각형이 있다 (방향 또는 퇴화)")
    B = np.empty((len(tri), 2, 3))
    B[:, 0, 0] = (b[:, 1] - c[:, 1]) / det
    B[:, 0, 1] = (c[:, 1] - a[:, 1]) / det
    B[:, 0, 2] = (a[:, 1] - b[:, 1]) / det
    B[:, 1, 0] = (c[:, 0] - b[:, 0]) / det
    B[:, 1, 1] = (a[:, 0] - c[:, 0]) / det
    B[:, 1, 2] = (b[:, 0] - a[:, 0]) / det
    return area, B


def assemble(xy, tri, eps_elem):
    """전체 강성행렬 K (N x N, 희소). eps_elem: (M, 2, 2) 요소별 ε 텐서."""
    area, B = element_matrices(xy, tri)
    # K_e = A * B^T ε B  -> (M,3,3)
    Ke = area[:, None, None] * np.einsum("mik,mij,mjl->mkl", B, eps_elem, B)
    rows = np.repeat(tri, 3, axis=1).ravel()
    cols = np.tile(tri, (1, 3)).ravel()
    return sp.csr_matrix((Ke.ravel(), (rows, cols)), shape=(len(xy), len(xy)))


def solve_dirichlet(K, fixed_idx, fixed_val):
    """K ψ = 0 를 Dirichlet 노드(fixed)를 소거해서 푼다."""
    n = K.shape[0]
    free = np.setdiff1d(np.arange(n), fixed_idx)
    psi = np.zeros(n)
    psi[fixed_idx] = fixed_val
    rhs = -K[free][:, fixed_idx] @ fixed_val
    psi[free] = spla.spsolve(K[free][:, free].tocsc(), rhs)
    return psi


def element_field(xy, tri, psi):
    """요소별 전기장 E = -∇ψ  (M, 2). 단위: V/nm (좌표가 nm 일 때)"""
    _, B = element_matrices(xy, tri)
    return -np.einsum("mik,mk->mi", B, psi[tri])


# ==============================================================================
# 섹션 3. RFET mesh 풀이
# ==============================================================================
def region_eps_tensors(variant, p: geo.Params, xy, tri, tri_region, rotate_slope=True):
    """요소별 2x2 ε. variant: 'perp' / 'para' (스칼라) 또는 'tensor'."""
    M = len(tri)
    eps = np.zeros((M, 2, 2))
    if variant in ("perp", "para"):
        sc = mat.scalar_eps(variant)
        for r, val in sc.items():
            sel = tri_region == r
            eps[sel, 0, 0] = val
            eps[sel, 1, 1] = val
    elif variant == "tensor":
        tn = mat.tensor_eps()
        for r, (exx, eyy) in tn.items():
            sel = tri_region == r
            eps[sel, 0, 0] = exx
            eps[sel, 1, 1] = eyy
        if rotate_slope:
            # [모델 선택] 경사 구간(0 < x < L)의 WSe2 요소에서는 주축을 경사각 theta 만큼 회전한다:
            #   ε' = R ε Rᵀ,  R = [[cos, -sin],[sin, cos]]. 면내(∥) 축이 경사를 따라가므로 물리적으로 맞다.
            cen = xy[tri].mean(axis=1)
            th = math.atan2(p.t_drain, p.l_ch)
            R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
            sel = (tri_region == "WSe2") & (cen[:, 0] > 0) & (cen[:, 0] < p.l_ch)
            eps[sel] = R @ eps[sel] @ R.T
    else:
        raise ValueError(variant)
    return eps


MESH_TAG = __import__("os").environ.get("RFET_MESH_TAG", "")     # [수치해석 설정] 수렴 검사용 mesh 태그


def solve_rfet(config, variant="perp", msh=None, verbose=True):
    p = geo.CONFIGS[config]
    m = tools.read_msh2(msh or f"rfet_{config}{MESH_TAG}_nm.msh")
    xy, tri = m["xy"], m["tri"]
    tri_names = {t: nm for (d, t), nm in m["names"].items() if d == 2}
    line_names = {t: nm for (d, t), nm in m["names"].items() if d == 1}
    tri_region = np.array([tri_names[t][2:] for t in m["tri_phys"]])          # "R_WSe2" -> "WSe2"
    eps = region_eps_tensors(variant, p, xy, tri, tri_region)
    K = assemble(xy, tri, eps)

    # Dirichlet 노드: contact 선 요소("C_<금속>_<영역>")의 노드 -> 금속별로 모은다
    metal_nodes = {mtl: set() for mtl in geo.METALS}
    for t, nm in line_names.items():
        if nm.startswith("C_"):
            mtl = nm[2:].split("_")[0]
            seg = m["line"][m["line_phys"] == t]
            metal_nodes[mtl].update(seg.ravel().tolist())

    results = {}
    for case, bias in UNIT_CASES.items():
        V = contact_voltages(bias)
        idx, val = [], []
        for mtl, nodes in metal_nodes.items():
            idx += sorted(nodes)
            val += [V[mtl]] * len(nodes)
        idx, val = np.array(idx), np.array(val)
        # 한 노드가 두 금속에 속하면 안 된다 (geometry 상 금속끼리는 안 닿음)
        assert len(np.unique(idx)) == len(idx), "한 노드가 두 접점에 속한다"
        psi = solve_dirichlet(K, idx, val)
        results[case] = psi
        if verbose:
            print(f"  [{config}/{variant}] unit case {case:6s}: psi 범위 [{psi.min():+.4f}, {psi.max():+.4f}] V")
    out = f"rfet_fem_{config}{MESH_TAG}_{variant}.npz"
    np.savez(out, xy=xy, tri=tri, tri_region=tri_region, solver="fem", config=config, variant=variant,
             **{f"psi_{c}": v for c, v in results.items()})
    if verbose:
        print("  저장:", out)
    return out


# ==============================================================================
# 섹션 4. 자체 검증 — 2층 평행판 (해석해 있음)
#   아래 유전체 ε1 두께 t1 (y: 0~t1), 위 유전체 ε2 두께 t2 (y: t1~t1+t2). 아래 전극 0 V, 위 전극 V.
#   D 연속: ε1 E1 = ε2 E2,  E1 t1 + E2 t2 = V
#   -> E1 = V / (t1 + t2 ε1/ε2),  계면 전위 ψ(t1) = E1 t1.   ψ 는 각 층에서 선형이므로 P1 FEM 이
#      구조 격자에서 정확히(반올림 오차 수준) 맞아야 한다. 이방성 검증: ε2 를 텐서로 주고 ε_yy 만 관여함을 확인.
# ==============================================================================
def structured_mesh(W, H, nx, ny):
    xs, ys = np.linspace(0, W, nx + 1), np.linspace(0, H, ny + 1)
    X, Y = np.meshgrid(xs, ys)
    xy = np.column_stack([X.ravel(), Y.ravel()])
    tri = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i
            n1, n2, n3 = n0 + 1, n0 + nx + 1, n0 + nx + 2
            tri += [(n0, n1, n3), (n0, n3, n2)]
    return xy, np.array(tri)


def selftest():
    t1, t2, V = 300.0, 30.0, 1.0
    e1, e2 = 3.9, (16.0, 7.9)          # 위층을 이방성(xx, yy)으로 둔다; 평행판에선 yy 만 작용해야 한다
    xy, tri = structured_mesh(200.0, t1 + t2, 8, 66)
    cen_y = xy[tri].mean(axis=1)[:, 1]
    eps = np.zeros((len(tri), 2, 2))
    low = cen_y < t1
    eps[low, 0, 0] = eps[low, 1, 1] = e1
    eps[~low, 0, 0], eps[~low, 1, 1] = e2
    K = assemble(xy, tri, eps)
    bot = np.where(np.abs(xy[:, 1]) < 1e-9)[0]
    top = np.where(np.abs(xy[:, 1] - (t1 + t2)) < 1e-9)[0]
    psi = solve_dirichlet(K, np.concatenate([bot, top]), np.concatenate([np.zeros(len(bot)), np.full(len(top), V)]))
    E1 = V / (t1 + t2 * e1 / e2[1])
    y = xy[:, 1]
    exact = np.where(y <= t1, E1 * y, E1 * t1 + (e1 / e2[1]) * E1 * (y - t1))
    err = np.max(np.abs(psi - exact))
    print(f"[selftest] 2층 평행판: 계면 전위 해석해 {E1 * t1:.6f} V, FEM {psi[np.abs(y - t1) < 1e-9].mean():.6f} V, "
          f"최대 절대오차 {err:.2e} V  -> {'OK' if err < 1e-10 else 'FAIL'}")
    # 선형성(중첩) 검사: 위 전극 V 대신 2V 를 걸면 해가 정확히 2배
    psi2 = solve_dirichlet(K, np.concatenate([bot, top]), np.concatenate([np.zeros(len(bot)), np.full(len(top), 2 * V)]))
    lin = np.max(np.abs(psi2 - 2 * psi))
    print(f"[selftest] 선형성: |psi(2V) - 2 psi(1V)| 최대 {lin:.2e} V  -> {'OK' if lin < 1e-10 else 'FAIL'}")
    return err < 1e-10 and lin < 1e-10


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "selftest":
        ok = selftest()
        raise SystemExit(0 if ok else 1)
    config = args[0]
    variants = args[1:] or ["perp"]
    for v in variants:
        solve_rfet(config, v)
