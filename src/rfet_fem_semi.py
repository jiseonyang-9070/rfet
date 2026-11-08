# -*- coding: utf-8 -*-
"""
rfet_fem_semi.py
================================================================================
STEP 4-B : 반도체 정전기 — WSe2 에 캐리어(전자·정공)를 넣은 비선형 Poisson 을 P1 FEM + Newton 으로 푼다.
          (DEVSIM 과 독립적인 참조 solver. 선형 버전 rfet_fem_reference.py 의 조립 함수를 재사용한다.)

풀이하는 식 (물리 모델)
  ∇·(ε_r ∇ψ) = -(q/ε0) [p(ψ) - n(ψ)]      WSe2 안   (n, p 는 rfet_semiconductor.carriers, 평형 E_F = 0)
  ∇·(ε_r ∇ψ) = 0                           유전체·공기
  Schottky 접점 (Source, Drain): ψ = V - (φ_Bn + χ)        게이트 (TG, BG): ψ = V_g - Φ_m
  그 외 외곽: ∂ψ/∂n = 0
  STEP 4 의 한계: V_S = V_D = 0 (평형) 만 다룬다. V_DS ≠ 0 는 캐리어 수송(quasi-Fermi 준위)이 필요하다 (STEP 5+).

수치 방법 (수치해석 설정)
  잔차 R(ψ) = K ψ - b(ψ),  b_i = (q/ε0)·[p-n](ψ_i)·A_i,  A_i = 노드 i 에 배분된 WSe2 요소 면적 (lumped mass)
  야코비안 J = K - diag((q/ε0)·d[p-n]/dψ·A_i)      (d[p-n]/dψ < 0 이므로 J 는 K 보다 더 양정치)
  Newton + backtracking line search. 게이트 전압은 작은 단계로 올린다(continuation): 이전 해가 다음 초기값.
  단위: nm, V, ε 상대값.  q/ε0 = 1.602e-19 C / 8.854e-21 F/nm = 18.095 V·nm  (농도 nm^-3 기준)

실행:  python rfet_fem_semi.py selftest                      (1D 적층 구조: ODE shooting 해와 비교)
       python rfet_fem_semi.py bridge [perp|para|tensor] [lit|equal_mid|equal_lo|equal_hi]
          -> rfet_semi_<config>_<eps>_<phi>.npz   (rfet_post_semi.py 가 읽음)
"""
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import rfet_geometry as geo
import rfet_materials as mat
import rfet_mesh_tools as tools
import rfet_semiconductor as semi
from rfet_fem_reference import assemble, element_matrices, region_eps_tensors, structured_mesh

Q_OVER_EPS0 = semi.Q_C / (mat.EPS0_F_PER_M * 1e-9)       # [V·nm]  (ε0 를 F/nm 로)

# ==============================================================================
# 섹션 1. 편향(bias) 목록  — STEP 4 는 V_S = V_D = 0 고정
# ==============================================================================
# [수치해석 설정] continuation 단계 크기: TG 는 0.5 V, BG 는 5 V 씩 올린다 (수렴 실패 시 줄일 것)
TG_STEP, BG_STEP = 0.5, 5.0
BIAS_SET = (
    [("TG", v, 0.0) for v in (-5.0, -2.5, 2.5, 5.0)]        # (이름, V_TG, V_BG)
    + [("BG", 0.0, v) for v in (-60.0, -30.0, 30.0, 60.0)]
    + [("flat", 0.0, 0.0)]
)


# ==============================================================================
# 섹션 2. 비선형 Poisson (Newton)
# ==============================================================================
class SemiPoisson:
    def __init__(self, xy, tri, tri_region, eps_elem, metal_nodes, phi_bn):
        self.xy, self.tri, self.tri_region = xy, tri, tri_region
        self.K = assemble(xy, tri, eps_elem).tocsr()
        self.metal_nodes = metal_nodes
        self.phi_bn = phi_bn
        # lumped area: WSe2 요소 면적을 세 꼭짓점에 1/3 씩 배분
        area, _ = element_matrices(xy, tri)
        self.A = np.zeros(len(xy))
        sel = tri_region == "WSe2"
        np.add.at(self.A, tri[sel].ravel(), np.repeat(area[sel] / 3.0, 3))
        self.semi_nodes = np.where(self.A > 0)[0]
        n = len(xy)
        self.fixed = np.concatenate([np.array(sorted(v), dtype=int) for v in metal_nodes.values()])
        self.free = np.setdiff1d(np.arange(n), self.fixed)

    def dirichlet_values(self, v_tg, v_bg, v_s=0.0, v_d=0.0):
        psi = np.zeros(len(self.xy))
        vals = {"Source": semi.contact_potential("Source", v_s, self.phi_bn),
                "Drain": semi.contact_potential("Drain", v_d, self.phi_bn),
                "TG": semi.gate_potential("TG", v_tg), "BG": semi.gate_potential("BG", v_bg)}
        for m, nodes in self.metal_nodes.items():
            psi[sorted(nodes)] = vals[m]
        return psi

    def residual_and_jacobian(self, psi):
        rho, drho = semi.rho_and_derivative(psi)
        b = Q_OVER_EPS0 * rho * self.A
        R = self.K @ psi - b
        J = self.K - sp.diags(Q_OVER_EPS0 * drho * self.A)
        return R, J.tocsr()

    def solve(self, v_tg, v_bg, psi0=None, tol=1e-9, max_iter=60, verbose=False):
        psi = self.dirichlet_values(v_tg, v_bg)
        if psi0 is not None:
            psi[self.free] = psi0[self.free]
        else:                                   # 초기값: 캐리어 없는 선형 해
            Kff = self.K[self.free][:, self.free]
            psi[self.free] = spla.spsolve(Kff.tocsc(), -self.K[self.free][:, self.fixed] @ psi[self.fixed])
        f = self.free
        for it in range(max_iter):
            R, J = self.residual_and_jacobian(psi)
            rn = np.linalg.norm(R[f])
            if verbose:
                print(f"    it {it:2d}  |R| = {rn:.3e}")
            if rn < tol:
                return psi, it
            d = spla.spsolve(J[f][:, f].tocsc(), -R[f])
            # backtracking: 잔차가 줄 때까지 보폭을 반으로 (지수 비선형성 때문에 필요)
            step = 1.0
            for _ in range(30):
                trial = psi.copy()
                trial[f] += step * d
                Rt, _ = self.residual_and_jacobian(trial)
                if np.linalg.norm(Rt[f]) < rn:
                    psi = trial
                    break
                step *= 0.5
            else:
                raise RuntimeError(f"line search 실패 (it {it}, |R| = {rn:.3e})")
        raise RuntimeError(f"Newton 이 {max_iter}회 안에 수렴하지 않음 (|R| = {rn:.3e})")

    def ramp_solve(self, v_tg, v_bg, verbose=False):
        """flat band (0, 0) 에서 목표 전압까지 단계적으로 올리며 푼다 (continuation)."""
        psi, _ = self.solve(0.0, 0.0)
        n_tg = max(1, int(np.ceil(abs(v_tg) / TG_STEP)))
        n_bg = max(1, int(np.ceil(abs(v_bg) / BG_STEP)))
        n = max(n_tg, n_bg)
        total_it = 0
        for k in range(1, n + 1):
            s = k / n
            psi, it = self.solve(s * v_tg, s * v_bg, psi0=psi)
            total_it += it
        if verbose:
            print(f"  V_TG = {v_tg:+5.1f}, V_BG = {v_bg:+5.1f}: {n} 단계, Newton 총 {total_it}회")
        return psi


# ==============================================================================
# 섹션 3. RFET mesh 풀이
# ==============================================================================
MESH_TAG = __import__("os").environ.get("RFET_MESH_TAG", "")     # [수치해석 설정] 수렴 검사용 mesh 태그


def load_mesh(config, msh=None):
    m = tools.read_msh2(msh or f"rfet_{config}{MESH_TAG}_nm.msh")
    tri_names = {t: nm for (d, t), nm in m["names"].items() if d == 2}
    line_names = {t: nm for (d, t), nm in m["names"].items() if d == 1}
    tri_region = np.array([tri_names[t][2:] for t in m["tri_phys"]])
    metal_nodes = {mtl: set() for mtl in geo.METALS}
    for t, nm in line_names.items():
        if nm.startswith("C_"):
            metal_nodes[nm[2:].split("_")[0]].update(m["line"][m["line_phys"] == t].ravel().tolist())
    return m["xy"], m["tri"], tri_region, metal_nodes


def solve_rfet(config, eps_variant="perp", phi_variant="lit", verbose=True):
    p = geo.CONFIGS[config]
    xy, tri, tri_region, metal_nodes = load_mesh(config)
    eps = region_eps_tensors(eps_variant, p, xy, tri, tri_region)
    model = SemiPoisson(xy, tri, tri_region, eps, metal_nodes, semi.PHI_BN_VARIANTS[phi_variant])
    out = {"xy": xy, "tri": tri, "tri_region": tri_region, "solver": "fem_semi", "config": config,
           "eps_variant": eps_variant, "phi_variant": phi_variant,
           "phi_bn_source": semi.PHI_BN_VARIANTS[phi_variant]["Source"],
           "phi_bn_drain": semi.PHI_BN_VARIANTS[phi_variant]["Drain"]}
    for name, v_tg, v_bg in BIAS_SET:
        psi = model.ramp_solve(v_tg, v_bg, verbose=verbose)
        n, pdens = semi.carriers(psi)
        key = f"{name}_TG{v_tg:+.1f}_BG{v_bg:+.1f}"
        out[f"psi_{key}"], out[f"n_{key}"], out[f"p_{key}"] = psi, n, pdens
    path = f"rfet_semi_{config}{MESH_TAG}_{eps_variant}_{phi_variant}.npz"
    np.savez(path, **out)
    if verbose:
        print("  저장:", path)
    return path


# ==============================================================================
# 섹션 4. 자체 검증 — 1D 적층 (BG / SiO2 300 / WSe2 9.1 / h-BN 30 / TG), 측면 Neumann
#   같은 문제를 독립적인 방법(ODE 적분 + shooting)으로 풀어 FEM 과 비교한다.
#   1D 식: (ε_r ψ')' = -(q/ε0)(p-n)   [WSe2],  ψ'' = 0 [유전체],  계면에서 ε_r ψ' 연속.
#   shooting: BG 에서의 전속 D = ε_r ψ' 을 미지수로 두고 적분해 TG 전위를 맞춘다 (brentq).
# ==============================================================================
def shooting_1d(v_tg, v_bg, t_ox=300.0, t_s=9.1, t_h=30.0):
    from scipy.integrate import solve_ivp
    from scipy.optimize import brentq
    e_ox, e_s, e_h = mat.SIO2_EPS, mat.WSE2_EPS["perp"], mat.HBN_EPS["perp"]
    psi_bg, psi_tg = semi.gate_potential("BG", v_bg), semi.gate_potential("TG", v_tg)

    def integrate(D0):
        # SiO2: ψ 선형, ψ' = D0/e_ox
        psi_a = psi_bg + (D0 / e_ox) * t_ox
        # WSe2: ψ'' = -(q/ε0)(p-n)/e_s,  상태 [ψ, D]  (D = e_s ψ')
        def rhs(y, s):
            rho, _ = semi.rho_and_derivative(s[0])
            return [s[1] / e_s, -Q_OVER_EPS0 * rho]
        sol = solve_ivp(rhs, (0.0, t_s), [psi_a, D0], rtol=1e-11, atol=1e-13, dense_output=True)
        psi_b, D1 = sol.y[0, -1], sol.y[1, -1]
        # h-BN: ψ 선형
        psi_top = psi_b + (D1 / e_h) * t_h
        return psi_top, sol

    # D0 의 부호/크기 범위를 넓게 잡고 근 찾기
    f = lambda D0: integrate(D0)[0] - psi_tg
    lo, hi = -10.0, 10.0
    while f(lo) > 0:
        lo *= 2
    while f(hi) < 0:
        hi *= 2
    D0 = brentq(f, lo, hi, xtol=1e-14, rtol=1e-13, maxiter=500)
    _, sol = integrate(D0)
    return D0, sol


def selftest():
    t_ox, t_s, t_h, W = 300.0, 9.1, 30.0, 40.0
    # 구조 격자: y 방향으로 각 층을 나눈다 (WSe2 안을 촘촘히)
    ys = np.concatenate([np.linspace(-t_ox, 0, 31)[:-1], np.linspace(0, t_s, 41)[:-1], np.linspace(t_s, t_s + t_h, 16)])
    xs = np.linspace(0, W, 5)
    X, Y = np.meshgrid(xs, ys)
    xy = np.column_stack([X.ravel(), Y.ravel()])
    nx, ny = len(xs), len(ys)
    tri = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            n0 = j * nx + i
            tri += [(n0, n0 + 1, n0 + nx + 1), (n0, n0 + nx + 1, n0 + nx)]
    tri = np.array(tri)
    cy = xy[tri].mean(axis=1)[:, 1]
    tri_region = np.where(cy < 0, "SiO2", np.where(cy < t_s, "WSe2", "hBN")).astype(object)
    eps = np.zeros((len(tri), 2, 2))
    for r, val in (("SiO2", mat.SIO2_EPS), ("WSe2", mat.WSE2_EPS["perp"]), ("hBN", mat.HBN_EPS["perp"])):
        sel = tri_region == r
        eps[sel, 0, 0] = eps[sel, 1, 1] = val
    metal_nodes = {"BG": set(np.where(np.abs(xy[:, 1] + t_ox) < 1e-9)[0]),
                   "TG": set(np.where(np.abs(xy[:, 1] - (t_s + t_h)) < 1e-9)[0]),
                   "Source": set(), "Drain": set()}
    model = SemiPoisson(xy, tri, np.array(tri_region, dtype=str), eps, metal_nodes, semi.PHI_BN_VARIANTS["lit"])
    ok = True
    for v_tg, v_bg in ((0.0, 0.0), (5.0, 0.0), (-5.0, 0.0), (0.0, 60.0), (0.0, -60.0), (5.0, 60.0)):
        psi = model.ramp_solve(v_tg, v_bg)
        D0, sol = shooting_1d(v_tg, v_bg, t_ox, t_s, t_h)
        col = np.where(np.abs(xy[:, 0] - xs[2]) < 1e-9)[0]
        yc = xy[col, 1]
        ref = np.empty(len(col))
        for k, y in enumerate(yc):
            if y <= 0:
                ref[k] = semi.gate_potential("BG", v_bg) + (D0 / mat.SIO2_EPS) * (y + t_ox)
            elif y <= t_s:
                ref[k] = sol.sol(y)[0]
            else:
                psi_b, D1 = sol.y[0, -1], sol.y[1, -1]
                ref[k] = psi_b + (D1 / mat.HBN_EPS["perp"]) * (y - t_s)
        err = np.max(np.abs(psi[col] - ref))
        lateral = np.max(np.abs(psi.reshape(ny, nx) - psi.reshape(ny, nx)[:, [2]]))
        n, p = semi.carriers(psi[col][(yc >= 0) & (yc <= t_s)])
        print(f"[selftest] V_TG={v_tg:+4.1f} V_BG={v_bg:+5.1f}: FEM-shooting 최대 오차 {err:.2e} V, "
              f"x 방향 비균일 {lateral:.1e} V, 박막 최대 n = {n.max()*semi.NM3_TO_CM3:.2e}, p = {p.max()*semi.NM3_TO_CM3:.2e} cm^-3"
              f"  -> {'OK' if err < 2e-3 else 'FAIL'}")
        ok = ok and err < 2e-3
    print("[selftest] 판정:", "OK (FEM 이산화 오차 수준에서 1D 독립해와 일치)" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "selftest":
        raise SystemExit(0 if selftest() else 1)
    config = args[0]
    eps_v = args[1] if len(args) > 1 else "perp"
    phi_v = args[2] if len(args) > 2 else "lit"
    solve_rfet(config, eps_v, phi_v)
