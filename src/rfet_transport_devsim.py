# -*- coding: utf-8 -*-
"""
rfet_transport_devsim.py
================================================================================
STEP 5-DD : 드리프트-확산(drift-diffusion, DD) 전류 — 우리 모델 + 팀원 코드의 장점을 합친 것

무엇을 어디서 가져왔는가 (docs/08_team_comparison.md)
  [우리 쪽]  geometry·mesh (단차·경사·h-BN 형상, gmsh), 유전율·밴드·장벽 [문헌값] 전부,
             2D DOS 기반 캐리어 통계 n = N_c,eq ln(1+e^η) (닫힌꼴 FD), Schottky/게이트 경계조건 (진공 준위 기준),
             교차 검증 습관 (전류 보존, 평형 해와의 비교)
  [팀원 쪽]  DEVSIM 에서 DD 를 세우는 순서와 API 사용법 (CreateSolution → CreateSiliconDriftDiffusion → 전류 모델 덮어쓰기),
             "FD = 볼츠만 SG 식의 ψ 를 유효 전위 ψ − V_t·g(n/N_c) 로 바꾸기" 라는 구현 아이디어 (브랜치 step3),
             rampbias 식 전압 램프와 수렴 기준(REL 1e-7: 정공 식 반올림 한계 때문), Id–Vbg 측정 흉내 (Vds ±2, Vtg ±5, Vbg ±60)
  [개선]     팀원은 3D DOS 에 Joyce–Dixon 근사 g(u) 를 썼다. 우리 2D DOS 는 역함수가 닫힌꼴이라
             g(u) = η − ln u = ln((e^u − 1)/u) 가 **정확**하다 (근사 없음, 과대 u 에서도 overflow 없음).

물리 모델 (STEP 4 와 동일한 기준 + 수송)
  Poisson:    ∇·(ε∇ψ) = −q(p − n)                                  (전 영역, WSe2 만 전하)
  연속식:     ∇·J_n = 0,  ∇·J_p = 0                                 (생성·재결합 없음 — [모델 가정], 아래 참조)
  전류:       Scharfetter–Gummel, 유효 전위 ψ_n = ψ − V_t g(n/N_c,eq),  ψ_p = ψ + V_t g(p/N_v,eq)
  통계:       n = N_c,eq ln(1+e^η)  →  η = ln(e^{n/N_c} − 1)        (2D DOS × 14층, rfet_semiconductor)
  Schottky:   ψ = V − (φ_Bn + χ),  n = N_c,eq ln(1+e^{−φ_Bn/V_t}),  p = N_v,eq ln(1+e^{−(E_g−φ_Bn)/V_t})   (접점 노드 고정)
  게이트:     ψ = V_g − Φ_m
  [모델 가정] 이동도 μ_n = μ_p = MU_CM2VS (팀원과 같은 100 cm²/Vs — 문헌값 아님, 전류 절대값은 μ 에 비례)
  [모델 가정] SRH/Auger 생성·재결합 0 (도핑 없는 박막, 접점 주입 지배 → 1차 근사; 켜려면 SRH_TAU_S 에 값)
  [한계]      터널링 없음 → 장벽 '위'로 넘는 열전자 전류만. 논문의 on 전류(터널링 지배)보다 수 자릿수 작다.
              2D 폭 1 cm 기준 A/cm → A/µm 로 환산해 출력.

실행:  python rfet_transport_devsim.py bridge [perp] [lit|equal_mid|equal_lo|equal_hi] [--quick]
       --quick : Vbg ±10 V, (Vds, Vtg) 2 조합만 (동작 확인용, 수 분)
출력:  rfet_idvbg_<config>_<eps>_<phi>.csv / .png,  rfet_band_<...>.npz
"""
import os
import sys
import time

import numpy as np
import devsim
from devsim.python_packages.model_create import CreateEdgeModel, CreateContactNodeModel, CreateSolution
from devsim.python_packages.simple_physics import CreateSiliconDriftDiffusion

import rfet_geometry as geo
import rfet_materials as mat
import rfet_semiconductor as semi
import rfet_poisson_devsim as lin
import rfet_poisson_semi_devsim as psd

# ==============================================================================
# 섹션 1. 파라미터
# ==============================================================================
# [모델 가정] 이동도 [cm^2/Vs]. 팀원 코드와 같은 값 (비교 가능하게). 문헌 범위는 다층 WSe2 실온 수십~수백.
MU_CM2VS = 100.0
# [모델 가정] SRH 수명 [s]. None 이면 생성·재결합 항을 넣지 않는다.
SRH_TAU_S = None
# [수치해석 설정] 측정 흉내 조건 (논문 Fig. 2 와 팀원 STEP3_BIAS 와 동일)
VDS_LIST = (2.0, -2.0)
VTG_LIST = (5.0, -5.0)
VBG_MAX, VBG_FINE, STEP_FINE, STEP_COARSE = 60.0, 6.0, 1.0, 5.0
VBG_BAND = 20.0                                   # 밴드 저장 Vbg
# [수치해석 설정] Newton 허용오차. 팀원 발견: 상대오차 1e-10 은 정공 식 반올림 한계(~1e-9)보다 작아 '수렴 실패' 가 났다 → 1e-7
REL, ABS, MAXIT = 1e-7, 1e10, 60
RAMP_STEP0, RAMP_MIN = 0.5, 0.002                 # 전압 램프 초기 간격 / 최소 간격 [V]
CARRIER_FLOOR = 1e-3                              # [수치해석 설정] 캐리어 초기값 바닥 [cm^-3] (0 방지)
A_PER_CM_TO_A_PER_UM = 1e-4


# ==============================================================================
# 섹션 2. 2D-DOS 축퇴 보정 g(u) — 정확식
# ------------------------------------------------------------------------------
# n = N_c ln(1+e^η)  ⇔  η = ln(e^u − 1),  u = n/N_c.   볼츠만은 η_B = ln u.
# g(u) = η − η_B = ln((e^u − 1)/u) = u + ln((1 − e^{−u})/u)   ← 큰 u 에서도 overflow 없음
# u → 0 에서 g → u/2 → 0 (볼츠만 극한), u ≫ 1 에서 g → u − ln u (축퇴).
# 미분이 필요하므로 (DEVSIM 이 기호 미분) max() 대신 u 에 아주 작은 상수를 더해 u = 0 특이점을 피한다.
# ==============================================================================
def g_exact(u_expr):
    us = f"({u_expr} + 1e-12)"
    return f"({us} + log((1 - exp(-{us}))/{us}))"


# ==============================================================================
# 섹션 3. DD 조립
# ==============================================================================
def setup_equilibrium_charge(device, region="WSe2"):
    """STEP 4 (rfet_poisson_semi_devsim.setup_wse2_charge) 와 같은 닫힌꼴 n, p 이지만 이름을 n_eq/p_eq 로 둔다.
    (나중에 'Electrons'/'Holes' 를 미지수(node_solution)로 만들 때 이름이 겹치지 않게 하려는 것)"""
    for name, val in (("chi", semi.CHI_EV), ("Eg", semi.EG_EV), ("V_t", semi.KT_EV),
                      ("Nc_eq", semi.NC_EQ * semi.NM3_TO_CM3), ("Nv_eq", semi.NV_EQ * semi.NM3_TO_CM3),
                      ("ElectronCharge", semi.Q_C)):
        devsim.set_parameter(device=device, region=region, name=name, value=val)
    splus = lambda x: f"(max({x},0) + log(1 + exp(-abs({x}))))"
    eta_n, eta_p = "(Potential + chi)/V_t", "(-Potential - chi - Eg)/V_t"
    devsim.node_model(device=device, region=region, name="n_eq", equation=f"Nc_eq*{splus(eta_n)}")
    devsim.node_model(device=device, region=region, name="p_eq", equation=f"Nv_eq*{splus(eta_p)}")
    devsim.node_model(device=device, region=region, name="n_eq:Potential", equation=f"Nc_eq*(1/(1+exp(-({eta_n}))))/V_t")
    devsim.node_model(device=device, region=region, name="p_eq:Potential", equation=f"-Nv_eq*(1/(1+exp(-({eta_p}))))/V_t")
    devsim.node_model(device=device, region=region, name="PotentialNodeCharge", equation="-ElectronCharge*(p_eq - n_eq)")
    devsim.node_model(device=device, region=region, name="PotentialNodeCharge:Potential",
                      equation="-ElectronCharge*(p_eq:Potential - n_eq:Potential)")
    devsim.equation(device=device, region=region, name="PotentialEquation", variable_name="Potential",
                    node_model="PotentialNodeCharge", edge_model="PotentialEdgeFlux", variable_update="default")


def setup_transport(device, region="WSe2"):
    """STEP 4 의 평형 Poisson(닫힌꼴 n,p) 위에 Electrons/Holes 를 미지수로 승격하고 연속식·전류식을 만든다."""
    # 3-1. 팀원 코드의 DEVSIM 관례 파라미터 이름 (simple_physics 가 이 이름들을 읽는다)
    for name, val in (("mu_n", MU_CM2VS), ("mu_p", MU_CM2VS), ("T", semi.T_K), ("kT", semi.KT_EV * semi.Q_C),
                      ("V_t", semi.KT_EV), ("ElectronCharge", semi.Q_C),
                      ("Nc", semi.NC_EQ * semi.NM3_TO_CM3), ("Nv", semi.NV_EQ * semi.NM3_TO_CM3)):
        devsim.set_parameter(device=device, region=region, name=name, value=val)
    n_i = float(np.sqrt(semi.NC_EQ * semi.NV_EQ) * np.exp(-semi.EG_EV / (2 * semi.KT_EV)) * semi.NM3_TO_CM3)
    for name, val in (("n_i", n_i), ("n1", n_i), ("p1", n_i),
                      ("taun", SRH_TAU_S or 1e30), ("taup", SRH_TAU_S or 1e30)):
        devsim.set_parameter(device=device, region=region, name=name, value=val)

    # 3-2. 평형 해의 닫힌꼴 n_eq, p_eq 를 초기값으로 하여 Electrons / Holes 를 미지수(node_solution)로 만든다
    # [수치해석 설정] 닫힌꼴 p_eq 는 η_p ≪ 0 인 노드에서 정확히 0 (exp 언더플로)이 되는데, DEVSIM 의 variable_update="positive"
    #   는 0 이하 값을 허용하지 않아 첫 solve 에서 "negative or zero value before update" 로 죽는다 (PC 실행, 2026-11-09).
    #   → 초기값에 바닥 CARRIER_FLOOR 를 둔다. 물리적으로 무의미한 크기(1e-3 cm^-3)라 결과에 영향 없음.
    for var, init in (("Electrons", "n_eq"), ("Holes", "p_eq")):
        CreateSolution(device, region, var)                           # node_solution + edge_from_node_model
        vals = np.maximum(np.array(devsim.get_node_model_values(device=device, region=region, name=init)), CARRIER_FLOOR)
        devsim.set_node_values(device=device, region=region, name=var, values=list(map(float, vals)))
    devsim.node_model(device=device, region=region, name="NetDoping", equation="0")   # [모델 가정] 도핑 0 (simple_physics 가 요구)

    # 3-3. 팀원 방식: simple_physics.CreateSiliconDriftDiffusion 이
    #      (a) PotentialNodeCharge = -q(Holes - Electrons + NetDoping) 와 그 도함수(:Electrons, :Holes) 를 다시 정의하고
    #      (b) 연속식 + 볼츠만 SG 전류 + SRH 를 만든다.  그 뒤 전류 모델만 FD 로 덮어쓴다.
    #      평형 단계에서 만든 'PotentialNodeCharge:Potential' 은 이제 틀린 식이므로 0 으로 덮어쓴다 (DEVSIM 은 이름으로 도함수를 찾는다).
    CreateSiliconDriftDiffusion(device, region, "mu_n", "mu_p")
    devsim.node_model(device=device, region=region, name="PotentialNodeCharge:Potential", equation="0")
    for carrier in ("Electrons", "Holes"):
        _fd_current(device, region, carrier)
    if SRH_TAU_S is None:
        # 생성·재결합 없음: simple_physics 가 만든 USRH 를 쓰지 않도록 연속식을 edge 항만으로 다시 정의
        devsim.equation(device=device, region=region, name="ElectronContinuityEquation", variable_name="Electrons",
                        edge_model="ElectronCurrent", variable_update="positive")
        devsim.equation(device=device, region=region, name="HoleContinuityEquation", variable_name="Holes",
                        edge_model="HoleCurrent", variable_update="positive")


def _fd_current(device, region, carrier):
    """팀원 브랜치 create_fermi_current 와 같은 구조(SG 전류의 ψ 를 유효 전위로 교체)이지만,
    (1) g(u) 는 2D-DOS 정확식, (2) 도함수를 전부 손으로 적는다.
    [수치해석 설정] 처음 버전은 DEVSIM 의 기호 미분(CreateEdgeModelDerivatives)에 맡겼는데, exp/log 가 중첩된 식을
    네 변수(Potential@n0/n1, 캐리어@n0/n1)로 미분·단순화하는 단계에서 멈춰 버렸다(사용자 PC, 2026-11-09). 그래서 수식마다
    ':변수@노드' 도함수 모델을 직접 만든다 — STEP 3·4 의 Poisson 에서도 같은 방식을 썼다.

    전자:  ψ_n = ψ − V_t g(n/N_c),  Δ = (ψ_n(n0) − ψ_n(n1))/V_t,  J_n = K [ n1 B(Δ) + n1 Δ − n0 B(Δ) ] = K [ n1 B(−Δ) − n0 B(Δ) ]
    정공:  ψ_p = ψ + V_t g(p/N_v),  Δ = (ψ_p(n0) − ψ_p(n1))/V_t,  J_p = −K [ p1 B(Δ) − p0 B(Δ) − p0 Δ ] = −K [ p1 B(Δ) − p0 B(−Δ) ]
    K = q μ V_t / L_edge.   g(u) = u + ln((1−e^{−u})/u),   g'(u) = 1/(1−e^{−u}) − 1/u   (u 에 1e-12 를 더해 u=0 회피)"""
    electron = carrier == "Electrons"
    dos, mu, tag = ("Nc", "mu_n", "n") if electron else ("Nv", "mu_p", "p")
    sgn = -1.0 if electron else +1.0                       # ψ_eff = ψ + sgn·V_t·g
    vdiff, bern, J = f"vdiff_{tag}", f"Bern01_{tag}", ("ElectronCurrent" if electron else "HoleCurrent")
    K = f"(ElectronCharge*{mu}*EdgeInverseLength*V_t)"

    def u(nd):      # 정규화 농도 (0 회피)
        return f"({carrier}@{nd}/{dos} + 1e-12)"
    def g(nd):
        return f"({u(nd)} + log((1 - exp(-{u(nd)}))/{u(nd)}))"
    def dg(nd):     # g'(u)
        return f"(1/(1 - exp(-{u(nd)})) - 1/{u(nd)})"

    # --- Δ 와 도함수 ---
    E = lambda name, eq: CreateEdgeModel(device, region, name, eq)
    E(vdiff, f"(Potential@n0 - Potential@n1)/V_t + ({sgn:+.0f})*({g('n0')} - {g('n1')})")
    E(f"{vdiff}:Potential@n0", "1/V_t")
    E(f"{vdiff}:Potential@n1", "-1/V_t")
    E(f"{vdiff}:{carrier}@n0", f"({sgn:+.0f})*{dg('n0')}/{dos}")
    E(f"{vdiff}:{carrier}@n1", f"({-sgn:+.0f})*{dg('n1')}/{dos}")
    # --- Bernoulli 와 도함수 (연쇄법칙) ---
    E(bern, f"B({vdiff})")
    for v in ("Potential", carrier):
        for nd in ("n0", "n1"):
            E(f"{bern}:{v}@{nd}", f"dBdx({vdiff})*{vdiff}:{v}@{nd}")
    # --- 전류와 도함수 ---
    if electron:
        n0, n1 = "Electrons@n0", "Electrons@n1"
        E(J, f"{K}*kahan3({n1}*{bern}, {n1}*{vdiff}, -{n0}*{bern})")
        for v in ("Potential",):
            for nd in ("n0", "n1"):
                E(f"{J}:{v}@{nd}", f"{K}*({n1}*{bern}:{v}@{nd} + {n1}*{vdiff}:{v}@{nd} - {n0}*{bern}:{v}@{nd})")
        E(f"{J}:Electrons@n0", f"{K}*({n1}*{bern}:Electrons@n0 + {n1}*{vdiff}:Electrons@n0 - {n0}*{bern}:Electrons@n0 - {bern})")
        E(f"{J}:Electrons@n1", f"{K}*({bern} + {vdiff} + {n1}*{bern}:Electrons@n1 + {n1}*{vdiff}:Electrons@n1 - {n0}*{bern}:Electrons@n1)")
    else:
        p0, p1 = "Holes@n0", "Holes@n1"
        E(J, f"-{K}*kahan3({p1}*{bern}, -{p0}*{bern}, -{p0}*{vdiff})")
        for v in ("Potential",):
            for nd in ("n0", "n1"):
                E(f"{J}:{v}@{nd}", f"-{K}*({p1}*{bern}:{v}@{nd} - {p0}*{bern}:{v}@{nd} - {p0}*{vdiff}:{v}@{nd})")
        E(f"{J}:Holes@n0", f"-{K}*({p1}*{bern}:Holes@n0 - {p0}*{bern}:Holes@n0 - {p0}*{vdiff}:Holes@n0 - {bern} - {vdiff})")
        E(f"{J}:Holes@n1", f"-{K}*({bern} + {p1}*{bern}:Holes@n1 - {p0}*{bern}:Holes@n1 - {p0}*{vdiff}:Holes@n1)")


def setup_schottky_carriers(device, phi_bn):
    """Source/Drain 의 WSe2 접점에서 n, p 를 2D-DOS 식으로 고정 (전위 BC 는 STEP 4 의 것이 그대로 있음)."""
    kT = semi.KT_EV
    for metal in ("Source", "Drain"):
        contact = geo.contact_name(metal, "WSe2")
        phi = phi_bn[metal]
        n_c = float(semi.NC_EQ * semi.NM3_TO_CM3 * np.log1p(np.exp(-phi / kT)))
        p_c = float(semi.NV_EQ * semi.NM3_TO_CM3 * np.log1p(np.exp(-(semi.EG_EV - phi) / kT)))
        for var, val, eq, cur in (("Electrons", n_c, "ElectronContinuityEquation", "ElectronCurrent"),
                                  ("Holes", p_c, "HoleContinuityEquation", "HoleCurrent")):
            pname = f"{metal}_{var}_contact"
            devsim.set_parameter(device=device, name=pname, value=val)
            model = f"{contact}_{var.lower()}_bc"
            CreateContactNodeModel(device, contact, model, f"{var} - {pname}")
            CreateContactNodeModel(device, contact, f"{model}:{var}", "1")
            devsim.contact_equation(device=device, contact=contact, name=eq, node_model=model, edge_current_model=cur)
        print(f"  {metal}: φ_Bn {phi:.2f} eV → n_c {n_c:.3e}, p_c {p_c:.3e} cm^-3")


# ==============================================================================
# 섹션 4. 풀이 보조 (팀원 rampbias 와 같은 동작: 실패하면 간격을 반으로)
# ==============================================================================
STATE = {"v_tg": 0.0, "v_bg": 0.0, "v_d": 0.0, "phi": None}


def _apply(device):
    psd.set_contact_biases(device, STATE["v_tg"], STATE["v_bg"], STATE["phi"], v_s=0.0, v_d=STATE["v_d"])


def solve():
    devsim.solve(type="dc", absolute_error=ABS, relative_error=REL, maximum_iterations=MAXIT)


def ramp(device, key, target):
    """STATE[key] 를 target 까지 램프. 수렴 실패 시 간격 반감, RAMP_MIN 이하이면 RuntimeError."""
    start = STATE[key]
    step = RAMP_STEP0 if abs(target - start) > RAMP_STEP0 else abs(target - start)
    v = start
    while abs(target - v) > 1e-12:
        trial = v + np.sign(target - v) * min(step, abs(target - v))
        STATE[key] = trial
        _apply(device)
        try:
            solve()
            v = trial
            step = min(step * 2.0, RAMP_STEP0)
        except devsim.error:
            STATE[key] = v
            _apply(device)
            step *= 0.5
            if step < RAMP_MIN:
                raise RuntimeError(f"ramp 실패: {key} {v:+.3f} → {target:+.3f} V (최소 간격 도달)")


def drain_current(device):
    c = geo.contact_name("Drain", "WSe2")
    ie = devsim.get_contact_current(device=device, contact=c, equation="ElectronContinuityEquation")
    ih = devsim.get_contact_current(device=device, contact=c, equation="HoleContinuityEquation")
    return (ie + ih) * A_PER_CM_TO_A_PER_UM, ie * A_PER_CM_TO_A_PER_UM, ih * A_PER_CM_TO_A_PER_UM


def source_current(device):
    c = geo.contact_name("Source", "WSe2")
    return (devsim.get_contact_current(device=device, contact=c, equation="ElectronContinuityEquation")
            + devsim.get_contact_current(device=device, contact=c, equation="HoleContinuityEquation")) * A_PER_CM_TO_A_PER_UM


def band_midline(device, p):
    """WSe2 중앙선의 x, ψ, n, p (후처리용). E_c = -ψ - χ 는 rfet_semiconductor.band_edges 로."""
    x = np.array(devsim.get_node_model_values(device=device, region="WSe2", name="x")) * lin.CM_TO_NM
    y = np.array(devsim.get_node_model_values(device=device, region="WSe2", name="y")) * lin.CM_TO_NM
    psi = np.array(devsim.get_node_model_values(device=device, region="WSe2", name="Potential"))
    n = np.array(devsim.get_node_model_values(device=device, region="WSe2", name="Electrons"))
    pp = np.array(devsim.get_node_model_values(device=device, region="WSe2", name="Holes"))
    bottom = np.where(x < 0, 0.0, np.where(x < p.l_ch, p.t_drain * x / p.l_ch, p.t_drain))
    sel = np.abs(y - bottom - 0.5 * p.t_wse2) < 0.3 * p.t_wse2 / 4     # 중앙선 노드 층
    o = np.argsort(x[sel])
    return x[sel][o], psi[sel][o], n[sel][o], pp[sel][o]


# ==============================================================================
# 섹션 5. 실행
# ==============================================================================
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quick = "--quick" in sys.argv
    config = args[0] if len(args) > 0 else "bridge"
    eps_variant = args[1] if len(args) > 1 else "perp"
    phi_variant = args[2] if len(args) > 2 else "lit"
    phi_bn = semi.PHI_BN_VARIANTS[phi_variant]
    p = geo.CONFIGS[config]
    tag = f"{config}_{eps_variant}_{phi_variant}" + ("_quick" if quick else "")
    print(f"=== STEP 5-DD: {config}, ε {eps_variant}, φ_Bn {phi_variant} (S {phi_bn['Source']}, D {phi_bn['Drain']}), μ {MU_CM2VS} ===")
    t0 = time.time()

    # 5-1. STEP 4 와 동일한 평형 해 (초기값)
    device = lin.build(config, eps_variant)
    setup_equilibrium_charge(device, "WSe2")
    STATE.update(v_tg=0.0, v_bg=0.0, v_d=0.0, phi=phi_bn)
    _apply(device)
    psd.solve_once()
    print(f"  평형 Poisson 완료 ({time.time() - t0:.0f} s)")

    # 5-2. DD 로 승격
    setup_transport(device, "WSe2")
    setup_schottky_carriers(device, phi_bn)
    solve()
    i_d0, i_s0 = drain_current(device)[0], source_current(device)
    print(f"  DD 평형 해: Id = {i_d0:+.2e}, Is = {i_s0:+.2e} A/µm  (둘 다 ~0 이어야 함)  ({time.time() - t0:.0f} s)")

    # 5-3. 스윕
    vbg_max = 10.0 if quick else VBG_MAX
    vds_list = (VDS_LIST[0],) if quick else VDS_LIST
    vbg_pts = np.unique(np.concatenate([np.arange(0, min(VBG_FINE, vbg_max) + 1e-9, STEP_FINE),
                                        np.arange(np.ceil(VBG_FINE / STEP_COARSE) * STEP_COARSE, vbg_max + 1e-9, STEP_COARSE)]))
    rows, bands = [], {}
    for vds in vds_list:
        for vtg in VTG_LIST:
            ramp(device, "v_tg", 0.0); ramp(device, "v_bg", 0.0); ramp(device, "v_d", vds); ramp(device, "v_tg", vtg)
            for direction in (+1, -1):
                ramp(device, "v_bg", 0.0)
                for v in vbg_pts:
                    try:
                        ramp(device, "v_bg", direction * v)
                    except RuntimeError as e:
                        print("  !", e, f"(Vds {vds:+.0f}, Vtg {vtg:+.0f})  → 이 방향 중단")
                        break
                    i_tot, i_e, i_h = drain_current(device)
                    rows.append((vds, vtg, direction * v, i_tot, i_e, i_h, source_current(device)))
                    if abs(direction * v - direction * VBG_BAND) < 1e-9:
                        bands[(vds, vtg, direction * v)] = band_midline(device, p)
            sub = [r for r in rows if r[0] == vds and r[1] == vtg]
            m = np.abs([r[3] for r in sub])
            print(f"  Vds {vds:+.0f} V, Vtg {vtg:+.0f} V: |Id| {m.min():.2e} ~ {m.max():.2e} A/µm  on/off {m.max() / max(m.min(), 1e-300):.1e}   ({time.time() - t0:.0f} s)")

    # 5-4. 저장
    data = np.array(rows)
    np.savetxt(f"rfet_idvbg_{tag}.csv", data, delimiter=",", comments="",
               header="Vds_V,Vtg_V,Vbg_V,Id_A_per_um,Ie_A_per_um,Ih_A_per_um,Is_A_per_um")
    out = {"config": config, "eps_variant": eps_variant, "phi_variant": phi_variant, "mu": MU_CM2VS}
    for (vds, vtg, vbg), (x, psi, n, pp) in bands.items():
        k = f"Vds{vds:+.0f}_Vtg{vtg:+.0f}_Vbg{vbg:+.0f}"
        out[f"x_{k}"], out[f"psi_{k}"], out[f"n_{k}"], out[f"p_{k}"] = x, psi, n, pp
    np.savez(f"rfet_band_{tag}.npz", **out)
    _plot(data, bands, p, phi_bn, tag)
    print(f"  저장: rfet_idvbg_{tag}.csv/.png, rfet_band_{tag}.npz   총 {time.time() - t0:.0f} s")


def _plot(data, bands, p, phi_bn, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import rfet_plotstyle as st
    st.apply()
    vds_vals = sorted(set(data[:, 0]), reverse=True)
    fig, axes = plt.subplots(1, len(vds_vals), figsize=(6.0 * len(vds_vals), 4.4), squeeze=False)
    for ax, vds in zip(axes[0], vds_vals):
        for vtg, color in ((VTG_LIST[0], st.ORANGE), (VTG_LIST[1], st.BLUE)):
            s = data[(data[:, 0] == vds) & (data[:, 1] == vtg)]
            s = s[np.argsort(s[:, 2])]
            if len(s):
                ax.semilogy(s[:, 2], np.abs(s[:, 3]), "-", color=color, lw=1.8, label=f"V$_{{TG}}$ = {vtg:+.0f} V")
        ax.set_title(f"V$_{{DS}}$ = {vds:+.0f} V  ({'n' if vds > 0 else 'p'}-mode programming)")
        ax.set_xlabel("V$_{BG}$ (V)"); ax.set_ylabel("|I$_D$| (A/µm)")
        ax.legend(loc="best")
    fig.suptitle(f"Drift-diffusion (no tunnelling), 2D-DOS FD statistics — {tag}, φ$_{{Bn}}$ S {phi_bn['Source']:.2f} / D {phi_bn['Drain']:.2f} eV, μ = {MU_CM2VS:g} cm²/Vs",
                 x=0.01, ha="left", fontsize=10, color=st.INK2)
    fig.tight_layout()
    fig.savefig(f"rfet_idvbg_{tag}.png")
    plt.close(fig)
    if bands:
        fig, axes = plt.subplots(1, len(bands), figsize=(5.2 * len(bands), 4.2), squeeze=False, sharey=True)
        for ax, ((vds, vtg, vbg), (x, psi, n, pp)) in zip(axes[0], sorted(bands.items())):
            ec, ev = semi.band_edges(psi)
            ax.plot(x, ec, color=st.RED, lw=1.6, label="E$_c$"); ax.plot(x, ev, color=st.BLUE, lw=1.6, label="E$_v$")
            ax.axhline(0, color=st.INK, lw=0.8, ls="--"); ax.axhline(-vds, color=st.INK2, lw=0.8, ls=":")
            st.shade_metal_regions(ax, p.l_ch)
            ax.set_title(f"V$_{{DS}}$ {vds:+.0f}, V$_{{TG}}$ {vtg:+.0f}, V$_{{BG}}$ {vbg:+.0f} V", fontsize=9.5)
            ax.set_xlabel("x (nm)"); ax.set_xlim(-150, p.l_ch + 150)
        axes[0][0].set_ylabel("energy vs source E$_F$ (eV)"); axes[0][0].legend(loc="best")
        fig.tight_layout(); fig.savefig(f"rfet_band_{tag}.png"); plt.close(fig)


if __name__ == "__main__":
    main()
