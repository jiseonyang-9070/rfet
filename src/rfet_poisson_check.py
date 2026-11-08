# -*- coding: utf-8 -*-
"""
rfet_poisson_check.py
================================================================================
STEP 3-C (검증) : rfet_poisson_devsim.py 의 Poisson 설정(섹션 1~2 함수)을 해석해가 있는 구조에서 검증한다.
                 geometry 두 벌을 비교하기 전에 "solver 설정이 맞는가"를 먼저 확인하는 단계.

구조: 2층 평행판.  아래 SiO2 (ε1 = 3.9, 300 nm), 위 h-BN 스칼라 ε2 (3.76, 30 nm).
      아래 전극 0 V, 위 전극 1 V.
해석해: D 연속 ε1 E1 = ε2 E2, E1 t1 + E2 t2 = V  ->  E1 = V / (t1 + t2 ε1/ε2), 계면 전위 = E1 t1.
        ψ 는 각 층에서 x 에 무관하고 y 에 선형이다.

mesh: DEVSIM 내장 2D 직사각형 mesher(add_2d_contact)가 접점 노드를 잡지 못하는 문제가 있어(실행 로그에서 확인:
      "there are only 0 contacts"), 구조 격자를 파이썬으로 직접 만들어 gmsh v2.2 .msh 파일로 쓰고
      RFET mesh 와 똑같은 경로(create_gmsh_mesh -> add_gmsh_region/contact/interface)로 읽는다.
      이 경로는 rfet_devsim_load.py 에서 이미 검증되었다.

통과 기준 (수치해석 설정): 모든 노드에서 |ψ_DEVSIM - ψ_해석| < 1e-9 V.
  (선형 해는 어떤 격자에서도 유한체적법이 정확히 재현해야 하므로 반올림 오차 수준이어야 한다.)

실행:  python rfet_poisson_check.py
"""
import numpy as np
import devsim

import rfet_materials as mat
import rfet_poisson_devsim as P

NM = 1.0e-7          # 1 nm in cm
MSH = "pp_check_cm.msh"


def write_structured_msh(path, t1, t2, W, n1=10, n2=10, nx=5):
    """2층 평행판의 구조 삼각형 mesh 를 gmsh v2.2 ASCII 로 쓴다 (좌표 cm).
    physical: 2D  1=R_SiO2, 2=R_hBN  /  1D  3=C_BG, 4=C_TG, 5=I_SiO2_hBN"""
    ys = np.concatenate([np.linspace(0, t1, n1 + 1)[:-1], np.linspace(t1, t1 + t2, n2 + 1)]) * NM
    xs = np.linspace(0, W, nx + 1) * NM
    nxp = len(xs)
    nid = lambda i, j: j * nxp + i + 1                       # 1-based 노드 번호
    nodes = [(nid(i, j), xs[i], ys[j]) for j in range(len(ys)) for i in range(nxp)]
    elems = []
    j_if = n1                                                # 계면 줄 번호 (y = t1)
    for j in range(len(ys) - 1):
        phys = 1 if j < j_if else 2
        for i in range(nxp - 1):
            a, b, c, d = nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)
            elems.append((2, phys, [a, b, c]))
            elems.append((2, phys, [a, c, d]))
    for i in range(nxp - 1):
        elems.append((1, 3, [nid(i, 0), nid(i + 1, 0)]))                  # BG: 아랫면
        elems.append((1, 4, [nid(i, len(ys) - 1), nid(i + 1, len(ys) - 1)]))  # TG: 윗면
        elems.append((1, 5, [nid(i, j_if), nid(i + 1, j_if)]))            # 계면
    with open(path, "w") as f:
        f.write("$MeshFormat\n2.2 0 8\n$EndMeshFormat\n$PhysicalNames\n5\n")
        f.write('2 1 "R_SiO2"\n2 2 "R_hBN"\n1 3 "C_BG"\n1 4 "C_TG"\n1 5 "I_SiO2_hBN"\n$EndPhysicalNames\n')
        f.write(f"$Nodes\n{len(nodes)}\n")
        for n, x, y in nodes:
            f.write(f"{n} {x:.12e} {y:.12e} 0\n")
        f.write(f"$EndNodes\n$Elements\n{len(elems)}\n")
        for k, (etype, phys, nl) in enumerate(elems, start=1):
            f.write(f"{k} {etype} 2 {phys} {phys} " + " ".join(map(str, nl)) + "\n")
        f.write("$EndElements\n")


def main():
    t1, t2, V = 300.0, 30.0, 1.0            # nm, nm, V   ([모델 가정] 검증용 치수: 논문 SiO2/h-BN 두께와 같게)
    e1, e2 = mat.SIO2_EPS, mat.HBN_EPS["perp"]
    W = 100.0
    write_structured_msh(MSH, t1, t2, W)

    mesh, device = "pp_mesh", "pp"
    devsim.create_gmsh_mesh(mesh=mesh, file=MSH)
    devsim.add_gmsh_region(mesh=mesh, gmsh_name="R_SiO2", region="SiO2", material="SiO2")
    devsim.add_gmsh_region(mesh=mesh, gmsh_name="R_hBN", region="hBN", material="hBN")
    devsim.add_gmsh_contact(mesh=mesh, gmsh_name="C_BG", region="SiO2", name="BG_SiO2", material="metal")
    devsim.add_gmsh_contact(mesh=mesh, gmsh_name="C_TG", region="hBN", name="TG_hBN", material="metal")
    devsim.add_gmsh_interface(mesh=mesh, gmsh_name="I_SiO2_hBN", region0="SiO2", region1="hBN", name="SiO2_hBN")
    devsim.finalize_mesh(mesh=mesh)
    devsim.create_device(mesh=mesh, device=device)
    print("contacts:", devsim.get_contact_list(device=device), " interfaces:", devsim.get_interface_list(device=device))

    # 본 코드와 "같은 함수"로 설정한다 — 검증 대상은 이 함수들이다
    P.setup_region_poisson(device, "SiO2", e1)
    P.setup_region_poisson(device, "hBN", e2)
    P.setup_contact(device, "BG_SiO2", "SiO2", "BG")
    P.setup_contact(device, "TG_hBN", "hBN", "TG")
    P.setup_interface(device, "SiO2_hBN")

    devsim.set_parameter(device=device, name="BG_bias", value=0.0)
    devsim.set_parameter(device=device, name="TG_bias", value=V)
    devsim.solve(type="dc", absolute_error=1e-10, relative_error=1e-12, maximum_iterations=10)

    E1 = V / (t1 + t2 * e1 / e2)
    worst = 0.0
    for r in ("SiO2", "hBN"):
        y = np.array(devsim.get_node_model_values(device=device, region=r, name="y")) / NM
        psi = np.array(devsim.get_node_model_values(device=device, region=r, name="Potential"))
        exact = np.where(y <= t1 + 1e-9, E1 * y, E1 * t1 + (e1 / e2) * E1 * (y - t1))
        worst = max(worst, float(np.max(np.abs(psi - exact))))
    print(f"계면 전위 해석해 {E1 * t1:.6f} V,  최대 절대오차 {worst:.2e} V  -> {'OK' if worst < 1e-9 else 'FAIL'}")

    # 게이트 전하로 용량 검증: Q = ε1 E1 W (단위 깊이, 2D) -> C/cm.  DEVSIM 접점 전하는 edge_charge_model 적분값.
    try:
        q = devsim.get_contact_charge(device=device, contact="TG_hBN", equation="PotentialEquation")
        q_exact = e1 * mat.EPS0_F_PER_CM * (E1 / NM) * (W * NM)      # E1 [V/nm] -> V/cm, W -> cm
        print(f"TG 전하: DEVSIM {q:+.4e} C/cm, 해석 {q_exact:.4e} C/cm  (비 {abs(q) / q_exact:.6f}; 부호 규약은 DEVSIM 정의)")
    except Exception as e:
        print("접점 전하 조회 생략:", e)
    raise SystemExit(0 if worst < 1e-9 else 1)


if __name__ == "__main__":
    main()
