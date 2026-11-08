# -*- coding: utf-8 -*-
"""
rfet_poisson_semi_devsim.py
================================================================================
STEP 4-B (DEVSIM) : WSe2 에 캐리어를 넣은 비선형 Poisson. rfet_fem_semi.py 와 같은 물리 모델,
                    같은 편향 목록, 같은 .npz 형식 -> rfet_post_semi.py 로 비교한다.

준비:  rfet_<config>_cm.msh (rfet_mesh_gmsh.py),  STEP 3 의 rfet_poisson_check.py 가 통과한 상태
실행:  python rfet_poisson_semi_devsim.py bridge [perp|para] [lit|equal_mid|equal_lo|equal_hi]
출력:  rfet_semi_devsim_<config>_<eps>_<phi>.npz

물리 모델 (rfet_semiconductor.py 와 동일한 기준)
  WSe2:  ∇·(ε∇ψ) = -q(p - n),   n = N_c,eq·ln(1+e^{η_n}),  p = N_v,eq·ln(1+e^{η_p})
         η_n = (ψ + χ)/V_t,  η_p = (-ψ - χ - E_g)/V_t      (평형, E_F = 0, V_S = V_D = 0)
  Schottky 접점: ψ = V - (φ_Bn + χ)      게이트: ψ = V_g - Φ_m
DEVSIM 구현 메모 (수치해석 설정)
  - 전하 node model 의 부호 규약은 DEVSIM 의 simple_physics 와 같게 둔다:
      PotentialNodeCharge = -ElectronCharge*(p - n)  와  PotentialEdgeFlux = Permittivity*ElectricField
    (equation 의 잔차 = Σ(edge flux) + node_model·부피 = 0 이 되도록 DEVSIM 이 조립한다.)
  - ln(1+e^x) 는 x 가 수백이 되면 exp 가 overflow 하므로  max(x,0) + log(1 + exp(-abs(x)))  로 쓴다.
    (DEVSIM 수식 언어의 max/abs 지원 여부는 사용자 환경에서 확인할 것. 안 되면 devsim.register_function
     으로 파이썬 softplus 를 등록하는 방법이 있다.)
  - 비선형이므로 전압을 단계적으로 올린다(continuation). Newton 은 DEVSIM 내부.
"""
import sys

import numpy as np
import devsim

import rfet_geometry as geo
import rfet_materials as mat
import rfet_semiconductor as semi
import rfet_poisson_devsim as lin          # STEP 3 의 영역/접점/계면 설정 함수 재사용
import rfet_fem_semi as fs                 # BIAS_SET, TG_STEP, BG_STEP 공유

CM_TO_NM = 1.0e7


# ==============================================================================
# 섹션 1. WSe2 전하 모델
# ==============================================================================
def setup_wse2_charge(device, region):
    """WSe2 영역에 n, p, 전하 node model 을 만들고 Poisson 식의 node_model 로 연결한다."""
    # [문헌값/모델] rfet_semiconductor 의 값들을 cm 단위로. 농도 nm^-3 -> cm^-3 (x1e21)
    for name, val in (("chi", semi.CHI_EV), ("Eg", semi.EG_EV), ("V_t", semi.KT_EV),
                      ("Nc_eq", semi.NC_EQ * semi.NM3_TO_CM3), ("Nv_eq", semi.NV_EQ * semi.NM3_TO_CM3),
                      ("ElectronCharge", semi.Q_C)):
        devsim.set_parameter(device=device, region=region, name=name, value=val)

    def splus(x):
        return f"(max({x},0) + log(1 + exp(-abs({x}))))"

    eta_n = "(Potential + chi)/V_t"
    eta_p = "(-Potential - chi - Eg)/V_t"
    # node model + Potential 에 대한 도함수 (DEVSIM 은 ':' 이름 규약으로 도함수를 찾는다)
    devsim.node_model(device=device, region=region, name="Electrons", equation=f"Nc_eq*{splus(eta_n)}")
    devsim.node_model(device=device, region=region, name="Holes", equation=f"Nv_eq*{splus(eta_p)}")
    sig_n = f"(1/(1+exp(-({eta_n}))))"
    sig_p = f"(1/(1+exp(-({eta_p}))))"
    devsim.node_model(device=device, region=region, name="Electrons:Potential", equation=f"Nc_eq*{sig_n}/V_t")
    devsim.node_model(device=device, region=region, name="Holes:Potential", equation=f"-Nv_eq*{sig_p}/V_t")
    devsim.node_model(device=device, region=region, name="PotentialNodeCharge",
                      equation="-ElectronCharge*(Holes - Electrons)")
    devsim.node_model(device=device, region=region, name="PotentialNodeCharge:Potential",
                      equation="-ElectronCharge*(Holes:Potential - Electrons:Potential)")
    # STEP 3 에서 만든 방정식을 node_model 이 포함된 것으로 다시 정의한다 (같은 이름이면 덮어씀)
    devsim.equation(device=device, region=region, name="PotentialEquation", variable_name="Potential",
                    node_model="PotentialNodeCharge", edge_model="PotentialEdgeFlux", variable_update="default")


# ==============================================================================
# 섹션 2. 접점 전위 (Schottky / 게이트) — STEP 3 의 '<금속>_bias' parameter 를 그대로 쓰되 오프셋을 더한다
# ==============================================================================
def set_contact_biases(device, v_tg, v_bg, phi_bn, v_s=0.0, v_d=0.0):
    devsim.set_parameter(device=device, name="Source_bias", value=semi.contact_potential("Source", v_s, phi_bn))
    devsim.set_parameter(device=device, name="Drain_bias", value=semi.contact_potential("Drain", v_d, phi_bn))
    devsim.set_parameter(device=device, name="TG_bias", value=semi.gate_potential("TG", v_tg))
    devsim.set_parameter(device=device, name="BG_bias", value=semi.gate_potential("BG", v_bg))


def solve_once():
    # [수치해석 설정] 비선형이므로 반복 허용. 절대오차는 전하 방정식 크기(C/cm) 때문에 상대오차로 판정.
    devsim.solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=50)


def ramp_to(device, v_tg, v_bg, phi_bn):
    n = max(1, int(np.ceil(abs(v_tg) / fs.TG_STEP)), int(np.ceil(abs(v_bg) / fs.BG_STEP)))
    for k in range(1, n + 1):
        s = k / n
        set_contact_biases(device, s * v_tg, s * v_bg, phi_bn)
        solve_once()


# ==============================================================================
# 섹션 3. 실행
# ==============================================================================
def main():
    config = sys.argv[1] if len(sys.argv) > 1 else "bridge"
    eps_variant = sys.argv[2] if len(sys.argv) > 2 else "perp"
    phi_variant = sys.argv[3] if len(sys.argv) > 3 else "lit"
    phi_bn = semi.PHI_BN_VARIANTS[phi_variant]
    print(f"=== DEVSIM 반도체 Poisson: {config}, ε {eps_variant}, φ_Bn {phi_variant} ===")

    device = lin.build(config, eps_variant)         # STEP 3 설정 (선형 Poisson + 접점 + 계면)
    setup_wse2_charge(device, "WSe2")               # WSe2 에 전하 추가 -> 비선형
    set_contact_biases(device, 0.0, 0.0, phi_bn)
    solve_once()                                    # flat band 해 (초기값)

    import rfet_mesh_tools as tools
    from scipy.spatial import cKDTree
    m = tools.read_msh2(f"rfet_{config}_nm.msh")
    tri_names = {t: nm for (d, t), nm in m["names"].items() if d == 2}
    out = {"xy": m["xy"], "tri": m["tri"], "tri_region": np.array([tri_names[t][2:] for t in m["tri_phys"]]),
           "solver": "devsim_semi", "config": config, "eps_variant": eps_variant, "phi_variant": phi_variant,
           "phi_bn_source": phi_bn["Source"], "phi_bn_drain": phi_bn["Drain"]}
    tree = cKDTree(m["xy"])

    for name, v_tg, v_bg in fs.BIAS_SET:
        set_contact_biases(device, 0.0, 0.0, phi_bn)
        solve_once()
        ramp_to(device, v_tg, v_bg, phi_bn)
        res = lin.gather_nodes(device)
        _, idx = tree.query(np.column_stack([res["x"], res["y"]]))
        psi = np.full(len(m["xy"]), np.nan)
        psi[idx] = res["psi"]
        key = f"{name}_TG{v_tg:+.1f}_BG{v_bg:+.1f}"
        n, p = semi.carriers(psi)                   # 후처리용 (DEVSIM 내부 n, p 와 같은 식)
        out[f"psi_{key}"], out[f"n_{key}"], out[f"p_{key}"] = psi, n, p
        print(f"  {key}: psi 범위 [{np.nanmin(psi):+.3f}, {np.nanmax(psi):+.3f}] V")
    path = f"rfet_semi_devsim_{config}_{eps_variant}_{phi_variant}.npz"
    np.savez(path, **out)
    print("  저장:", path)


if __name__ == "__main__":
    main()
