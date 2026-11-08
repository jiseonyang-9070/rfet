# -*- coding: utf-8 -*-
"""
rfet_semiconductor.py
================================================================================
STEP 4-A : WSe2 를 "반도체"로 만드는 물성과, 그로부터 전하밀도 ρ(ψ) 를 만드는 모델.
          (유전율은 rfet_materials.py 에 그대로 두고, 여기서는 밴드·캐리어·접점 장벽만 다룬다)

--------------------------------------------------------------------------------
에너지 기준 (이 파일과 solver 전체에서 하나로 통일)
--------------------------------------------------------------------------------
  ψ(x,y) = 정전 전위 [V].  전자의 진공 준위 E_vac = -qψ.
  E_c = E_vac - χ = -qψ - χ,   E_v = E_c - E_g                (χ: 전자친화도)
  금속이 전압 V 에 있으면 그 금속의 페르미 준위 E_Fm = -qV.
  STEP 4 는 V_S = V_D = 0 인 평형 상태만 다루므로 WSe2 안의 페르미 준위 E_F = 0 이다.
    -> n = N_c · ln(1 + exp((E_F - E_c)/kT)),  p = N_v · ln(1 + exp((E_v - E_F)/kT))   (아래 DOS 모델 참조)
  Schottky 접점 (금속-WSe2):  E_c(접점) - E_Fm = φ_Bn   ->   ψ_contact = V - (φ_Bn + χ)/q
  게이트 (금속-유전체):       E_vac(표면) = E_Fm + Φ_m   ->   ψ_gate = V_g - Φ_m/q
  단위: 에너지 eV, 전위 V (q = 1 로 두면 숫자가 같다), 길이 nm, 농도 nm^-3 (FEM) / cm^-3 (DEVSIM).

--------------------------------------------------------------------------------
[문헌값] 출처 요약 (값 옆 태그 참조)
--------------------------------------------------------------------------------
  W14  D. Wickramaratne, F. Zahid, R. K. Lake, "Electronic and thermoelectric properties of few-layer
       transition metal dichalcogenides", J. Chem. Phys. 140, 124710 (2014), DOI 10.1063/1.4869142
       (arXiv:1401.0502). DFT(VASP, PBE+SOC). Table II: 유효질량, Table III: 밴드갭.
  M14  S. McDonnell et al., ACS Nano 8, 6265 (2014), DOI 10.1021/nn501728w. Table 3: bulk WSe2
       전자친화도 4.03 ± 0.1 eV, 이온화에너지 5.19 ± 0.1 eV, 밴드갭 1.16 ± 0.03 eV (Kautek 인용값).
  S17  J. T. Smyth et al., 2D Mater. 4, 025084 (2017), DOI 10.1088/2053-1583/aa6bea. XPS, bulk WSe2,
       UHV 증착 Au: 전자 Schottky 장벽 0.53 eV (Fig. 1, 4). bulk 밴드갭 1.3 ± 0.1 eV (STS, 인용값).
  J22  J. Jang et al., Adv. Mater. 34, 2109899 (2022), DOI 10.1002/adma.202109899. 8~12 nm 다층 WSe2 에
       증착한 Ti, Au, Pd: 전자 장벽 ≈ 0.19~0.25 eV (Fig. 3f), pinning factor S = 0.03 (온도 의존 I-V).
  C17  A. Prakash & J. Appenzeller 등, "Understanding contact gating in Schottky barrier transistors from
       2D channels", Sci. Rep. 7, 12596 (2017): Ni/WSe2 전자 장벽 0.4~0.5 eV (두께 의존).
"""
import math

import numpy as np

import rfet_materials as mat

# ==============================================================================
# 섹션 1. 상수
# ==============================================================================
# [문헌값] CODATA 2018 (NIST)
KB_EV = 8.617333262e-5          # 볼츠만 상수 [eV/K]
HBAR_EVS = 6.582119569e-16      # ħ [eV·s]
M0_KG = 9.1093837015e-31        # 전자 질량 [kg]
Q_C = 1.602176634e-19           # 전자 전하 [C]
# [모델 가정] 온도 300 K (논문 본문에 측정 온도 명시 없음 -> 실온 가정)
T_K = 300.0
KT_EV = KB_EV * T_K             # 0.02585 eV

# ==============================================================================
# 섹션 2. 밴드 파라미터 (다층 ≈ bulk, 9.1 nm = 14층: rfet_materials.wse2_layer_count)
# ==============================================================================
# [문헌값] 밴드갭 E_g [eV]. 실험값 범위가 넓다: 1.16 ± 0.03 (M14 Table 3), 1.3 ± 0.1 (S17 인용 STS),
#   DFT(PBE+SOC) bulk 간접갭 1.188 (W14 Table III). baseline 1.2 eV 는 이 범위의 중앙값이며
#   "실험 범위 1.16~1.3 eV 안의 대표값" 이라는 의미의 선택이다. 민감도: EG_RANGE.
EG_EV = 1.2
EG_RANGE = (1.16, 1.3)

# [문헌값] 전자친화도 χ [eV] = 4.03 ± 0.1 (M14 Table 3, bulk, 실험 SKexp). 이온화에너지 5.19 - E_g 1.16.
#   참고: S17 은 이온화에너지 5.33 eV 를 인용 -> χ ≈ 4.0. 두 출처가 0.1 eV 안에서 일치.
CHI_EV = 4.03

# [문헌값] 유효질량 [m0], bulk WSe2 (W14 Table II, PBE+SOC)
#   전도대 최소점: Σ(=Q/Λ) 점, 면내 종/횡 질량 0.489 / 0.643.  BZ 안에 Σ 점이 6개 -> 밸리 겹침 g = 6.
#   가전자대 최대점: Γ 점, 면내 질량 0.997.  밸리 1개.
#   주의: 단층(K점, m ≈ 0.34)과 전혀 다르다. 원칙 7 에 따라 bulk 값을 쓴다 (14층은 bulk 로 간주).
ME_SIGMA_L, ME_SIGMA_T, GV_CB = 0.489, 0.643, 6
MH_GAMMA, GV_VB = 0.997, 1
# 면내 상태밀도 질량 = sqrt(m_l m_t)
ME_DOS_2D = math.sqrt(ME_SIGMA_L * ME_SIGMA_T)     # 0.561
MH_DOS_2D = MH_GAMMA                                # 0.997

# ==============================================================================
# 섹션 3. 상태밀도(DOS) 모델 — [모델 가정] "층마다 2D DOS, 층을 쌓아 부피 밀도로 환산"
# ------------------------------------------------------------------------------
# 왜 3D 식 N_c = 2(2π m kT/h²)^{3/2} 을 안 쓰는가: 그 식에는 면외(c축) 질량이 필요한데 W14 는 면내 값만 준다.
#   층간 결합이 약한 다층 TMD 는 "2D 밴드가 N_layer 개 겹친 것" 으로 보는 것이 물리적으로 더 자연스럽고,
#   필요한 값(면내 질량, 밸리 수)이 모두 [문헌값] 이다. 대신 층간 분산을 무시하므로 이것도 가정이다.
#   2D DOS 의 장점: 페르미-디랙 적분이 닫힌 꼴 -> n_2D = N_2D · ln(1 + e^η)  (η = (E_F - E_c)/kT)
#   볼츠만 극한(η ≪ 0)에서 ln(1+e^η) → e^η 이므로 자동으로 볼츠만을 포함한다 (팀원 코드의 ±10 V 제한 없음).
# 부피 환산: N_eq [nm^-3] = N_2D [nm^-2] × (층수 / 두께)  -> 2D 단면 Poisson 의 부피 전하밀도에 그대로 쓴다.
# ==============================================================================
def dos_2d_per_layer(m_dos, g_valley):
    """2D 유효 상태밀도 [nm^-2] = g_v · m kT / (π ħ²)  (스핀 2 포함)"""
    m_kg = m_dos * M0_KG
    kT_J = KT_EV * Q_C
    hbar_Js = HBAR_EVS * Q_C
    n_m2 = g_valley * m_kg * kT_J / (math.pi * hbar_Js ** 2)      # [m^-2]
    return n_m2 * 1e-18                                           # [nm^-2]


N_LAYERS = mat.wse2_layer_count(9.1)                               # 14
T_FILM_NM = 9.1                                                    # [논문값] 두께
NC_2D = dos_2d_per_layer(ME_DOS_2D, GV_CB)                         # [nm^-2] per layer
NV_2D = dos_2d_per_layer(MH_DOS_2D, GV_VB)
NC_EQ = NC_2D * N_LAYERS / T_FILM_NM                               # [nm^-3]
NV_EQ = NV_2D * N_LAYERS / T_FILM_NM
NM3_TO_CM3 = 1e21


# ==============================================================================
# 섹션 4. 접점 파라미터
# ==============================================================================
# [문헌값] Schottky 장벽 (전자 기준, φ_Bp = E_g - φ_Bn 는 pinning 된 준위가 하나라는 가정)
#   Source = 증착 Pd (WSe2 위) : J22 Fig. 3f 의 증착 Pd 범위 0.19~0.25 eV -> 0.22 eV. 8~12 nm 다층(우리 9.1 nm 와 일치).
#   Drain  = vdW Au (WSe2 아래): S17 Au/bulk WSe2 XPS 0.53 eV. (증착이 아닌 vdW 계면 -> J22 의 강한 pinning 과 다를 수 있음)
#   주의: 두 값은 서로 다른 시료·방법에서 나온 것이라 "같은 소자에서 같은 방법으로 잰 값" 이 아니다.
#   불확실성이 크므로 PHI_BN_VARIANTS 로 민감도를 반드시 돌린다. 특히 "S/D 같은 장벽" 은 금속 비대칭을
#   제거하고 기하(차폐) 효과만 보는 대조군이다 (팀 저장소 step3 의 아이디어를 방법론으로 차용).
PHI_BN_SOURCE = 0.22
PHI_BN_DRAIN = 0.53
PHI_BN_VARIANTS = {
    "lit":      {"Source": 0.22, "Drain": 0.53},   # 문헌값 그대로
    "equal_mid": {"Source": 0.5 * EG_EV, "Drain": 0.5 * EG_EV},  # 대조군: 둘 다 midgap (0.6 eV)
    "equal_lo": {"Source": 0.22, "Drain": 0.22},   # 대조군: 둘 다 Pd 값
    "equal_hi": {"Source": 0.53, "Drain": 0.53},   # 대조군: 둘 다 Au 값
}

# [모델 가정] 게이트 금속 일함수 Φ_m [eV]. TG 금속 종류는 논문에 없고 BG 는 도핑 Si (도핑 미상).
#   이상 유전체에서는 Φ_m 이 게이트 전압 축의 평행이동(ΔV = ΔΦ_m/q)만 일으키고 전위 분포의 "모양" 은 바꾸지 않는다.
#   baseline: Φ_m = χ + E_g/2 (진성 WSe2 와 flat-band 가 되는 값) -> V_g = 0 이 flat band.
#   논문의 최소 전류 위치(V_bg 축 오프셋)를 재현하려면 이 값을 조정해야 하지만, 그것은 fitting 이므로 하지 않는다.
PHI_M_GATE = {"TG": CHI_EV + 0.5 * EG_EV, "BG": CHI_EV + 0.5 * EG_EV}

# [모델 가정] 계면 고정전하, 트랩, 도핑 = 0 (논문에 값 없음). 진성 WSe2.
N_DOPING = 0.0


# ==============================================================================
# 섹션 5. 전하밀도 ρ(ψ) 와 그 도함수 (FEM Newton 과 DEVSIM 수식의 공통 정의)
# ==============================================================================
def softplus(x):
    """ln(1 + e^x) 를 overflow 없이."""
    x = np.asarray(x, dtype=float)
    return np.where(x > 0, x, 0.0) + np.log1p(np.exp(-np.abs(x)))


def sigmoid(x):
    x = np.asarray(x, dtype=float)
    return 0.5 * (1.0 + np.tanh(0.5 * x))


def carriers(psi, chi=CHI_EV, eg=EG_EV, nc=NC_EQ, nv=NV_EQ, ef=0.0):
    """ψ [V] -> (n, p) [nm^-3].  E_c = -ψ - χ, E_v = E_c - E_g, 페르미 준위 ef [eV]."""
    eta_n = (ef + psi + chi) / KT_EV            # (E_F - E_c)/kT
    eta_p = (-psi - chi - eg - ef) / KT_EV      # (E_v - E_F)/kT
    return nc * softplus(eta_n), nv * softplus(eta_p)


def rho_and_derivative(psi, **kw):
    """부피 전하밀도 ρ/q [nm^-3] = p - n + N_doping 와 d(ρ/q)/dψ [nm^-3/V]"""
    chi, eg, nc, nv, ef = (kw.get("chi", CHI_EV), kw.get("eg", EG_EV), kw.get("nc", NC_EQ),
                           kw.get("nv", NV_EQ), kw.get("ef", 0.0))
    eta_n = (ef + psi + chi) / KT_EV
    eta_p = (-psi - chi - eg - ef) / KT_EV
    n, p = nc * softplus(eta_n), nv * softplus(eta_p)
    dn = nc * sigmoid(eta_n) / KT_EV
    dp = -nv * sigmoid(eta_p) / KT_EV
    return (p - n + N_DOPING), (dp - dn)


def contact_potential(metal, v_bias, phi_bn):
    """Schottky 접점 (Source/Drain) 의 ψ [V]:  ψ = V - (φ_Bn + χ)"""
    return v_bias - (phi_bn[metal] + CHI_EV)


def gate_potential(metal, v_bias):
    """게이트 (TG/BG) 의 ψ [V]:  ψ = V_g - Φ_m"""
    return v_bias - PHI_M_GATE[metal]


def band_edges(psi):
    """ψ [V] -> (E_c, E_v) [eV], E_F(=0) 기준"""
    ec = -np.asarray(psi) - CHI_EV
    return ec, ec - EG_EV


if __name__ == "__main__":
    print(f"T = {T_K} K, kT = {KT_EV:.5f} eV,  E_g = {EG_EV} eV (범위 {EG_RANGE}),  χ = {CHI_EV} eV")
    print(f"층수 {N_LAYERS},  m_e,dos(2D) = {ME_DOS_2D:.3f} m0 (g={GV_CB}),  m_h,dos(2D) = {MH_DOS_2D:.3f} m0 (g={GV_VB})")
    print(f"N_c,2D = {NC_2D:.4e} nm^-2/layer = {NC_2D*1e14:.3e} cm^-2,   N_v,2D = {NV_2D:.4e} nm^-2/layer")
    print(f"부피 환산 N_c,eq = {NC_EQ*NM3_TO_CM3:.3e} cm^-3,  N_v,eq = {NV_EQ*NM3_TO_CM3:.3e} cm^-3")
    ni = math.sqrt(NC_EQ * NV_EQ) * math.exp(-EG_EV / (2 * KT_EV))
    print(f"진성 농도 (볼츠만 극한) n_i ≈ {ni*NM3_TO_CM3:.3e} cm^-3")
    for m, v in (("Source", 0.0), ("Drain", 0.0)):
        print(f"ψ({m}, V=0) = {contact_potential(m, v, PHI_BN_VARIANTS['lit']):+.3f} V")
    for g in ("TG", "BG"):
        print(f"ψ({g}, V=0) = {gate_potential(g, 0.0):+.3f} V  (flat-band 기준)")
    for psi in (-4.63, -4.4, -4.2, -4.0):
        n, p = carriers(psi)
        print(f"ψ = {psi:+.2f} V: E_c = {-psi-CHI_EV:+.3f} eV, n = {n*NM3_TO_CM3:.3e}, p = {p*NM3_TO_CM3:.3e} cm^-3")
