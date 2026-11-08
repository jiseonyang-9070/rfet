# -*- coding: utf-8 -*-
"""
rfet_geometry.py   (v2: h-BN 박편의 단차 통과 형상을 파라미터로 둠)
================================================================================
STEP 2-A : WSe2 RFET 2D 단면 geometry 정의
기준 논문 : Fubo Jiao et al., Appl. Phys. Lett. 128, 263504 (2026)
            doi:10.1063/5.0338649   (본문 6쪽만 사용, Supplementary Material 없음)

v1 -> v2 에서 바뀐 것과 그 이유
  v1은 h-BN 윗면을 평평(y = 110.1)하게 두었다. 그러면 Source 위 h-BN 두께가 46 nm, Source 벽 옆이
  101 nm가 되어 논문의 "30 nm-thick h-BN"(두께가 일정한 박편 하나)과 모순된다. v2는 h-BN의
  수직 두께를 어디서나 t_hbn 으로 고정하고, 박편 "아랫면이 Source 단차를 어떻게 넘는가"만
  파라미터 l_hbn_step 으로 둔다.
    - l_hbn_step = L  : "bridge" 극단. 박편이 Source 윗면 모서리에서 Drain 쪽 WSe2 윗면까지
                        팽팽한 직선으로 걸쳐지고, 그 아래 경사 WSe2와의 사이에 공기 쐐기(AirTop)가 생긴다.
    - l_hbn_step < L  : "sag" 변형. 박편이 Source 모서리에서 내려와 x = l_hbn_step 에서 경사 WSe2에
                        닿고(touch point) 그 뒤로는 밀착한다. 작을수록 conformal에 가깝다.
  하한은 h-BN의 굽힘 강성이 정하지만 1차 문헌값을 확보하지 못했으므로, 이 파일은 하한을
  "하강 각도 45도"라는 기하학적 선택(CONFIGS["sag45"])으로 두고 [모델 가정]으로 명시한다.

이 파일이 하는 일 (물리 모델의 "모양"만 다룬다)
  1) 파라미터를 [논문값] / [모델 가정]으로 구분해서 한 곳에 모은다.
  2) 점(point) -> 다각형(polygon)으로 영역을 정의한다.
  3) 다각형들이 맞닿는 선(edge)에서 접점(contact)과 계면(interface)을 자동으로 뽑는다.
  4) geometry가 기하학적으로 말이 되는지 검사한다 (겹침, 빈틈, 방향, T-junction, 면적).
  5) 그림으로 그려서 눈으로 확인한다.

이 파일이 하지 않는 일
  - gmsh, DEVSIM을 import하지 않는다. (mesh = 수치해석 설정은 rfet_mesh_gmsh.py)
  - Poisson 방정식을 풀지 않는다. 유전율, 일함수, 전하밀도도 아직 없다 (STEP 3).

--------------------------------------------------------------------------------
[좌표계]  논문 Fig. 1(a)와 같은 방향: Source가 왼쪽, Drain이 오른쪽
--------------------------------------------------------------------------------
  x [nm] : 채널 방향. x = 0 -> Source 금속의 오른쪽 벽 (source junction 모서리)
                      x = L -> Drain 금속의 왼쪽 벽   (drain junction 모서리), L = 채널 길이
  y [nm] : 수직 방향. y = 0 -> SiO2 윗면 (Drain 금속과 WSe2가 얹히는 바닥 평면), 위가 +
  z      : 폭 방향. 2D 단면 모델이므로 z 방향으로 변하지 않는다고 가정한다.
           [모델 단순화] 실제 소자의 폭 가장자리 fringe field는 이 모델에 없다.

실행:  python rfet_geometry.py            (모든 CONFIGS 검사 + 좌표표 + 그림 rfet_geometry_<이름>.png)
       python rfet_geometry.py sag45      (하나만)
"""
from dataclasses import dataclass, replace
import math
import sys
import numpy as np


# ==============================================================================
# 섹션 1. 파라미터  (단위: 모두 nm)
# ==============================================================================
@dataclass(frozen=True)
class Params:
    """각 변수 바로 위의 태그가 값의 출처다. 이 단계의 geometry에는 [문헌값]이 필요한 항목이 없다."""

    # ---- (1-a) 논문에서 확인되는 값 -------------------------------------------
    # [논문값] Jiao 2026, p.263504-2 본문 "a 9.1 nm-thick WSe2 (Fig. S1) thin film"
    # WSe2 박막 두께 [nm]. 이 모델에서는 어디서나 "수직 방향 두께"가 일정하다.
    # 층수는 본문에 없다. 층수 의존 물성(유전율, 밴드갭)은 STEP 3 이후에 따로 다룬다.
    t_wse2: float = 9.1

    # [논문값] Jiao 2026, p.263504-2 본문 "a 30 nm-thick h-BN layer as the top-gate dielectric"
    # h-BN 두께 [nm]. v2에서는 어디서나 수직 두께가 이 값이다 (박편 하나라는 논문 서술에 맞춤).
    t_hbn: float = 30.0

    # [논문값] Jiao 2026, p.263504-2 본문 "SiO2 (300 nm)/Si substrate"
    # Back Gate(Si)와 WSe2 사이 SiO2 두께 [nm].
    t_ox: float = 300.0

    # [논문값(합산)] Jiao 2026, p.263504-2 본문 "drain electrode (Ti/Au, 1/70 nm)"
    # Drain 금속 두께 = Ti 1 + Au 70 = 71 nm. 합산은 내가 한 것이고 논문에 "71"이 적힌 것은 아니다.
    # 증착 공칭 두께이며 실측 단차 높이는 본문에 없다.
    t_drain: float = 71.0

    # [논문값(합산)] Jiao 2026, p.263504-2 본문 "source electrode (Pd/Au, 5/50 nm)"
    # Source 금속 두께 = Pd 5 + Au 50 = 55 nm.
    t_source: float = 55.0

    # [논문값(근사)] Jiao 2026, Abstract / p.2 / p.4 의 "approximately 500 nm"
    # 채널 길이 L [nm]. 본문은 "~500 nm"라고만 쓰고 어느 두 점 사이인지는 Fig. S2(첨부 없음)에 있다.
    # 여기서는 본문 "source electrode ... edge was positioned at the base of the transition region"에
    # 근거해 "Source 금속 모서리(경사 아래, x=0)와 Drain 금속 벽(경사 위, x=L) 사이의 수평 거리"로
    # 해석했다. -> 이 해석 자체는 [모델 가정]이다.
    l_ch: float = 500.0

    # ---- (1-b) 논문에 없어서 모델이 정해야 하는 값 ---------------------------------
    # [모델 가정] Source 금속 패드의 채널 방향 길이 [nm]. (논문 본문에 수치 없음)
    # 왜 필요한가: 도메인 왼쪽 끝을 정해야 한다. 잘린 벽에는 Neumann 조건이 걸리므로 junction에서
    #   충분히 멀어야 한다. 기준: BG fringe field의 가로 퍼짐 ~ SiO2 두께(300 nm)의 3배 이상.
    #   이 선택이 결과를 바꾸는지는 STEP 3에서 1000 vs 2000 nm 비교로 확인해야 한다.
    l_src_pad: float = 1000.0

    # [모델 가정] Drain 금속 패드의 채널 방향 길이 [nm]. 이유와 기준은 l_src_pad와 같다.
    l_drn_pad: float = 1000.0

    # [모델 가정] Top Gate가 Source 모서리(x=0)보다 왼쪽(Source 금속 위)으로 연장되는 길이 [nm].
    # 논문에는 TG 크기/위치 수치가 없다 (Fig. 1(a,b)에 개략도·현미경 사진만 있다).
    # 왜 필요한가: TG가 Source 금속 위를 얼마나 덮는지가 "Source가 TG를 가린다"는 차폐 서술의 핵심이다.
    #   정답을 모르므로 좌/우 대칭(300 nm)으로 두어 한쪽 junction을 미리 유리하게 만들지 않았다.
    #   300 nm는 TG-WSe2 거리(30~100 nm)의 3배 이상이다. 0보다 커야 한다 (TG 끝이 단차 모서리와 겹치면 안 됨).
    tg_overhang_src: float = 300.0

    # [모델 가정] Top Gate가 Drain 모서리(x=L)보다 오른쪽(Drain 금속 위)으로 연장되는 길이 [nm].
    tg_overhang_drn: float = 300.0

    # [모델 가정] h-BN 박편 아랫면이 Source 단차를 넘는 전이 길이 [nm]. 파일 머리말 참조.
    #   None 이면 l_ch 와 같게 둔다 (= bridge 극단). 0 < l_hbn_step <= l_ch 이어야 한다.
    #   왜 필요한가: TG가 source junction 바로 오른쪽 WSe2에 얼마나 가까이 오는지를 이 값이 정한다.
    #   영향: 작을수록 TG -> source junction 결합이 강해져 "TG 차폐"가 약해 보인다 (차폐에 불리한 쪽).
    l_hbn_step: float = None

    # [모델 가정 + 탄성 추정] WSe2 가 SiO2 에서 떠서 Drain 윗면(71 nm)까지 올라가는 경사의 가로 길이 ℓ [nm]. 경사는 x = L 에서
    #   끝난다 (Drain 벽 = 경사 꼭대기). 경사 시작점 x_lift = L − ℓ.  None 이면 ℓ = L (경사가 Source 모서리에서 시작).
    #   어디서 시작하나(= ℓ 값)의 근거: 논문에 단면 사진(Fig. S2)이 없으므로 "굽힘 에너지 vs 접착 에너지" 최소화로 정한다
    #   (ramp_length_elastic, 유도는 그 위 주석): E(WSe2) 167 GPa [문헌값], t 9.1, h 71, Γ 0.45 차용 → ℓ* ≈ 217 nm.
    #   → 채널 0 ~ 283 nm 는 SiO2 위에 평평, 283 ~ 500 nm 만 올라간다. 비교용으로 팀원 값 70 nm(45°) 도 돌린다.
    #   영향: 짧을수록 drain junction 앞 경사가 급하고, Source 쪽 채널이 SiO2 에 붙어 BG 결합이 커진다.
    l_slope: float = None

    # [모델 가정] 경사의 모양.
    #   "smooth" = 클램프 큐빅(clamped–clamped cubic) S자 곡선 y = t_drain·(3u² − 2u³), u = (x − x_lift)/l_ramp.
    #      이것은 오일러-베르누이 판의 평형식 D·y''''=0 에 "양 끝에서 높이·기울기 연속(밀착)" 조건을 넣은 유일한 해이며
    #      굽힘 에너지가 최소인 모양이다 (유도: 아래 '탄성 추정' 블록). 2차식은 양 끝 기울기 0 을 동시에 만족 못 한다.
    #      곡선은 ramp_segments 개의 직선 조각으로 근사한다 (면적 오차 < 0.1 %, analytic_areas 에서 검사).
    #   "linear" = 꺾인 직선(평평 → 일정 기울기 → 평평, 꺾임점 2개). 꺾임점은 곡률 무한대라 역학적 근거는 없고
    #      (i) 팀원 모델(45° 직선)과의 비교, (ii) "모양이 결과에 영향을 주나" 를 보는 기하학적 대조군으로만 쓴다.
    ramp_shape: str = "linear"
    ramp_segments: int = 16

    # [모델 가정] Top Gate / Back Gate 금속 "본체"의 두께 [nm]. 시각화와 접점 판별 전용.
    # 정전기 계산에서는 금속 내부를 풀지 않고 h-BN 윗면 / SiO2 아랫면의 선에 전압을 걸 뿐이다.
    t_gate_dummy: float = 20.0

    @property
    def l_step(self):
        return self.l_ch if self.l_hbn_step is None else float(self.l_hbn_step)

    @property
    def l_ramp(self):
        """경사 가로 길이 (None 이면 L)"""
        return self.l_ch if self.l_slope is None else float(self.l_slope)

    @property
    def x_lift(self):
        """WSe2 가 SiO2 에서 떨어지기 시작하는 x (= 경사 시작점, AirBot 쐐기 끝)"""
        return self.l_ch - self.l_ramp

    @property
    def slope_deg(self):
        return math.degrees(math.atan2(self.t_drain, self.l_ramp))

    def film_bottom(self, x):
        """WSe2 아랫면 높이 y(x): x < x_lift 는 0 (SiO2 위), 경사 구간은 직선 또는 S자 곡선, x >= L 는 t_drain. 배열 가능."""
        x = np.asarray(x, dtype=float)
        u = np.clip((x - self.x_lift) / self.l_ramp, 0.0, 1.0)
        if self.ramp_shape == "smooth":
            u = u * u * (3.0 - 2.0 * u)
        return u * self.t_drain

    def film_slope(self, x):
        """WSe2 아랫면 기울기 dy/dx"""
        x = np.asarray(x, dtype=float)
        u = (x - self.x_lift) / self.l_ramp
        inside = (u > 0) & (u < 1)
        if self.ramp_shape == "smooth":
            d = 6.0 * u * (1.0 - u)
        else:
            d = np.ones_like(u)
        return np.where(inside, d, 0.0) * self.t_drain / self.l_ramp

    def ramp_breakpoints(self):
        """경사 구간을 나타내는 꺾은선의 x 좌표 (양 끝 포함). linear 는 [x_lift, L], smooth 는 ramp_segments+1 개."""
        if self.ramp_shape == "smooth":
            return list(np.linspace(self.x_lift, self.l_ch, self.ramp_segments + 1))
        return [self.x_lift, self.l_ch]

    def film_top(self, x):
        """WSe2 윗면 높이 y(x) = 아랫면 + t_wse2"""
        return self.film_bottom(x) + self.t_wse2


def sag_step_for_angle(p: Params, angle_deg):
    """h-BN 아랫면이 Source 모서리 (0, y_src_top)에서 각도 angle_deg 로 내려와 경사 WSe2 윗면에
    닿는 전이 길이 l 을 푼다.  (y_src_top - film_top(l)) / l = tan(angle)
    -> (t_src + t_wse2 - t_wse2 - t_drain*l/L) / l = tan  -> l = t_src / (tan + t_drain/L)"""
    tan = math.tan(math.radians(angle_deg))
    # 평평 구간(x < x_lift)에 닿는 경우: l = t_source / tan.  경사 구간에 닿는 경우: 선형식.
    l_flat = p.t_source / tan
    if l_flat <= p.x_lift:
        return l_flat
    k = p.t_drain / p.l_ramp
    return (p.t_source + k * p.x_lift) / (tan + k)


# ------------------------------------------------------------------------------
# 탄성(굽힘 vs 접착) 추정 — "박막이 단차 h 를 어느 가로 길이 ℓ 에 걸쳐 넘는가"
# ------------------------------------------------------------------------------
#  모델: 두께 t, 영률 E 의 얇은 판(박막)이 기판에 Γ [J/m²] 로 붙어 있다가 높이 h 의 단차를 넘어 다시 밀착한다.
#  단차 구간(가로 길이 ℓ)에서 판은 기판에서 떠 있고 양 끝에서는 기판에 밀착(기울기 0)한다.
#
#  (1) 모양: 오일러-베르누이 판(Euler–Bernoulli beam) 의 평형식 D·y'''' = 0 (분포 하중 없음) 의 해는 3차 다항식.
#      경계조건 y(0)=0, y'(0)=0, y(ℓ)=h, y'(ℓ)=0 (양 끝 밀착 → 높이와 기울기 연속) 을 넣으면
#          y(u) = h·(3u² − 2u³),  u = x/ℓ            ← "clamped–clamped" 큐빅, ramp_shape="smooth" 가 바로 이 식.
#      2차식 y = a u² 은 조건 4개 중 3개만 만족시킬 수 있어(끝에서 기울기 0 불가) 밀착 조건을 깨뜨린다.
#  (2) 굽힘 에너지 (단위 폭당):  U_b = (D/2)∫₀^ℓ y''² dx = (D/2)(h²/ℓ⁴)·ℓ·∫₀¹(6−12u)² du = (D/2)(h²/ℓ³)·12 = 6 D h² / ℓ³
#      D = E t³ / 12(1−ν²)  (판의 굽힘 강성).
#  (3) 접착 에너지: 떠 있는 길이 ℓ 만큼 기판과의 접착을 잃는다 → U_a = Γ ℓ.
#  (4) 총 에너지 U = 6Dh²/ℓ³ + Γℓ 를 ℓ 로 최소화: dU/dℓ = −18Dh²/ℓ⁴ + Γ = 0
#          →  ℓ* = (18 D h² / Γ)^(1/4)
#      [정정] 이전 버전은 계수 3 (U_b ~ Dh²/ℓ³ 의 거친 스케일링) 을 썼다. 정확한 적분값은 6 이고 미분하면 18 이다.
#             ℓ 은 계수의 1/4 제곱에 비례하므로 (18/3)^¼ = 1.565 배 길어진다. 기존 결과(h-BN 449 nm)는 coeff=3 으로 재현된다.
#  [모델 가정] (a) 박막이 늘어나지 않는다(inextensible; 전사(transfer) 과정에서 박막이 미끄러져 길이를 보충).
#               늘어남까지 금지하면 막 에너지 ~0.18 E t h⁴/ℓ³ 가 더해져 ℓ 이 (1 + 0.36(1−ν²)(h/t)²)^¼ 배 길어진다
#               (WSe2: h/t = 7.8 → ×2.2, ≈ L). 즉 ℓ* 는 하한, L 은 상한이다.
#            (b) 기판 쪽 단차 모서리에서 박막이 들리는 것(lift-off)은 무시. (c) 폭 방향 균일(2D).
def bending_rigidity(E_pa, t_m, nu=0.2):
    """판의 굽힘 강성 D = E t³ / 12(1−ν²) [J]."""
    return E_pa * t_m ** 3 / (12.0 * (1.0 - nu ** 2))


def transition_length_elastic(E_pa, t_nm, h_nm, gamma_j_m2, nu=0.2, coeff=18.0):
    """ℓ* = (coeff · D h² / Γ)^(1/4) [nm].  coeff = 18 (정확한 클램프 큐빅 빔), 3 = 구(舊) 거친 추정 (재현용)."""
    D = bending_rigidity(E_pa, t_nm * 1e-9, nu)
    return (coeff * D * (h_nm * 1e-9) ** 2 / gamma_j_m2) ** 0.25 * 1e9


def sag_step_elastic(p: Params, E_pa=0.86e12, nu=0.2, gamma_j_m2=0.45, coeff=18.0):
    """h-BN 박편(두께 t_hbn)이 Source 단차(높이 t_source)를 내려와 WSe2 위에 다시 밀착하기까지의 전이 길이 [nm].
      [문헌값] E(h-BN) = 0.86 TPa: Falin et al., Nat. Commun. 8, 15815 (2017), 1L 0.865±0.073, 9L 0.856±0.003 TPa (AFM 압입)
      [모델 가정] ν = 0.2 (얇은 판 관례값; 결과에 수 %), Γ = 0.45 J/m² 차용 (아래 ramp_length_elastic 의 Γ 설명 참조).
    결과 ≈ 703 nm > L = 500 nm  → h-BN 은 채널 안에서 내려와 다시 밀착할 수 없다 = 채널 전체를 곧은 판으로 건넌다.
    (coeff=3 이면 449 nm — 정정 전 추정값, config 'elastic' 재현용.)"""
    return transition_length_elastic(E_pa, p.t_hbn, p.t_source, gamma_j_m2, nu, coeff)


def ramp_length_elastic(p: Params, E_pa=167.3e9, nu=0.2, gamma_j_m2=0.45, coeff=18.0):
    """WSe2 박막(두께 t_wse2)이 SiO2 에서 떠서 Drain 윗면(높이 t_drain)으로 올라가는 경사의 가로 길이 ℓ* [nm].
      [문헌값] E(WSe2 다층) = 167.3 ± 6.7 GPa: R. Zhang, V. Koutsos, R. Cheung, "Elastic properties of suspended multilayer WSe2",
               Appl. Phys. Lett. 108, 042104 (2016), DOI 10.1063/1.4940982. AFM 압입, 기계적 박리 5·6·12·14층 (14층: 165 ± 6 GPa),
               두께에 통계적으로 무관 → 우리 14층(9.1 nm) 박막에 그대로 적용 가능 (단층값 차용이 아님). 파단 변형률 ≈ 7.3 %.
               (원문 초록 OSTI 기록 + Table 1 (리뷰 재인용) 로 확인 2026-11-09)
      [문헌값(차용)] Γ = 0.45 J/m²: 그래핀/SiO2 (Koenig et al., Nat. Nanotechnol. 6, 543 (2011), 1L 0.45, 2–5L 0.31).
               WSe2/SiO2 직접 측정값은 확보 못함. 같은 TMD 인 MoS2/SiO2 는 0.34–0.48 J/m² (Torres et al.,
               Phys. Status Solidi A 215, 1700512 (2018), 블리스터법) 로 같은 범위. ℓ ∝ Γ^(−1/4) 라 Γ 0.1–1 J/m² 에서
               ℓ = 317–178 nm 로 둔감하다.
      [모델 가정] ν = 0.2.
    결과 ≈ 217 nm (< L = 500) → 채널은 Source 쪽 약 283 nm 가 SiO2 위에 평평, Drain 앞 217 nm 만 S자로 올라간다.
    팀원 모델의 70 nm(45°) 가 나오려면 Γ ≈ 41 J/m² 가 필요해(217/70 = 3.1, 3.1⁴ ≈ 92 배) 반데르발스 접착(0.1–1)으로는 설명 안 됨."""
    return transition_length_elastic(E_pa, p.t_wse2, p.t_drain, gamma_j_m2, nu, coeff)


def ramp_mechanics(p: Params, eps_break=0.073):
    """경사 곡선의 역학적 자기검사: 최대 기울기각, 최소 곡률반경, 표면 변형률 t/2R 과 파단 변형률(7.3 %, Zhang 2016) 비교.
    smooth: y'' 최대 = 6h/ℓ² (양 끝), 기울기 최대 = 1.5 h/ℓ (가운데).  linear: 꺾임점은 곡률 무한대 → 검사 불가(기하 근사)."""
    h, l, t = p.t_drain, p.l_ramp, p.t_wse2
    if p.ramp_shape != "smooth":
        return dict(shape="linear", slope_max_deg=p.slope_deg, radius_min_nm=float("inf"), strain_surface=float("nan"), ok=None)
    kappa = 6.0 * h / l ** 2
    R = 1.0 / kappa
    strain = t / (2.0 * R)
    return dict(shape="smooth", slope_max_deg=math.degrees(math.atan(1.5 * h / l)), radius_min_nm=R,
                strain_surface=strain, ok=strain < eps_break)


def hbn_tangent_touch(p: Params):
    """직사각형(직선) h-BN 판이 Source 윗면 모서리 (0, y_src_top) 에서 출발해 WSe2 윗면 꺾은선과 처음 만나는(접하는) x.
    직선 경사(linear)에서는 꼭대기 (L) 에서 만난다. S자 곡선에서는 그보다 앞에서 접하므로, 꺾은선의 각 꼭짓점 중
    "모서리에서 본 기울기" 가 최대인 점이 접점이다 (볼록 껍질 논리). 그 점 뒤로 h-BN 은 박막에 밀착한다."""
    y0 = p.t_wse2 + p.t_source
    xs = [x for x in p.ramp_breakpoints() if x > 1e-9] + [p.l_ch]
    best, best_slope = p.l_ch, -np.inf
    for x in xs:
        sl = (float(p.film_top(x)) - y0) / x
        if sl > best_slope + 1e-15:
            best, best_slope = x, sl
    return float(best)


# 이름 붙은 설정.
_base = Params()
CONFIGS = {
    # bridge: 처짐 0. l = L.  탄성 추정 l(≈450 nm) 이 L(500 nm) 에 가까우므로 물리적으로도 baseline 에 가장 가깝다.
    "bridge": _base,
    # elastic: [정정 전 추정값 재현용] h-BN 전이 길이를 구(舊) 계수 3 으로 계산한 449 nm. 정확한 계수 18 로는 703 nm > L 이 되어
    #          bridge 와 같아지므로(min(ℓ, L) = L) 지금은 "bridge 가 과장이 아님" 을 보이는 민감도 점으로만 남긴다 (STEP 3 결과 있음).
    "elastic": replace(_base, l_hbn_step=min(sag_step_elastic(_base, coeff=3.0), _base.l_ch)),
    # sag45: 하강 각도 45도. 30 nm 두께 박편이 곡률반경 ~40 nm 로 꺾이려면 표면 변형률 t/2R ≈ 35% 가 필요해
    #        물리적으로 불가능하다. "TG 가 채널에 최대한 가까운 가상의 하한" 으로서 민감도 비교에만 쓴다.
    "sag45": replace(_base, l_hbn_step=sag_step_for_angle(_base, 45.0)),
}
# ---- "판 h-BN" 설정 (현재 기준): h-BN·TG 는 두께 일정한 곧은 판(직사각형), WSe2 만 휜다 ----
#   왜 판인가: h-BN 의 탄성 전이 길이 ℓ*(h-BN) ≈ 703 nm > L = 500 nm (sag_step_elastic). 채널 안에서 내려와 다시 밀착할
#   길이가 없으므로 Source 윗면(y 64.1)에 얹혀 Drain 쪽 WSe2 윗면(y 80.1)에 닿을 때까지 곧게 간다. 두 높이 차 16 nm 때문에
#   1.8° 기울고(꺾임 없음, 두께 일정), 가운데 채널 위에는 최대 55 nm 공기층이 생긴다.
#   WSe2 경사: 가로 길이 ℓ 는 ramp_length_elastic ≈ 217 nm (에너지 최소화) → x_lift ≈ 283 nm 부터 올라간다.
#     curve_el : S자 곡선(클램프 큐빅, 역학적 근거 있음) — **기준(baseline)**
#     line_el  : 같은 ℓ 의 꺾인 직선 — "모양만 바꾸면 결과가 얼마나 변하나" 대조군
#     curve70 / line70 : ℓ = 70 nm (팀원 모델 45°) — 팀원 모델과의 비교. 역학적으로는 Γ ≈ 41 J/m² 가 필요해 비현실적.
#     curve_el_eq : [민감도] t_source 를 Drain 과 같은 71 로 → Source 윗면(80.1) = Drain 쪽 WSe2 윗면(80.1) 이라 판이 정확히 수평.
#                   논문값(55)을 바꾼 것이므로 기준이 아니라 "16 nm 두께 차 → 1.8° 기울기" 의 영향만 보는 용도.
#   곡선에서는 판이 꼭대기보다 앞에서 곡선에 접하고(hbn_tangent_touch) 그 뒤로는 박막 위에 얹힌다. 직선에서는 꼭대기(L)에서 만난다.
L_RAMP_ELASTIC = ramp_length_elastic(_base)          # ≈ 216.7 nm (값은 실행 시 계산; 하드코딩하지 않음)


def _plate_config(base: Params, l_ramp, shape, **kw):
    """판 h-BN 설정 생성: h-BN 아랫면이 WSe2 윗면에 처음 접하는 x 를 l_hbn_step 으로 (꼭대기면 None = bridge 형)."""
    q = replace(base, l_slope=float(l_ramp), ramp_shape=shape, **kw)
    touch = hbn_tangent_touch(q)
    return replace(q, l_hbn_step=None if touch >= q.l_ch - 1e-9 else touch)


CONFIGS["curve_el"] = _plate_config(_base, L_RAMP_ELASTIC, "smooth")
CONFIGS["line_el"] = _plate_config(_base, L_RAMP_ELASTIC, "linear")
CONFIGS["curve70"] = _plate_config(_base, 70.0, "smooth")
CONFIGS["line70"] = _plate_config(_base, 70.0, "linear")
CONFIGS["curve_el_eq"] = _plate_config(_base, L_RAMP_ELASTIC, "smooth", t_source=71.0)


# ==============================================================================
# 섹션 2. 점(point) 정의
#   모든 영역은 "이름 붙은 점들을 반시계(CCW) 방향으로 이은 다각형"이다.
#   같은 위치는 반드시 같은 점을 공유한다 -> 이웃 영역과 선이 정확히 일치(conforming)한다.
# ==============================================================================
def build_points(p: Params) -> dict:
    """Params -> {점 이름: (x, y)} 사전. 단위 nm."""
    if p.l_ch <= 0 or p.l_src_pad <= 0 or p.l_drn_pad <= 0:
        raise ValueError("길이 파라미터는 양수여야 한다")
    if not (0 < p.tg_overhang_src <= p.l_src_pad and 0 < p.tg_overhang_drn <= p.l_drn_pad):
        raise ValueError("TG 연장 길이는 0보다 크고 금속 패드 길이 이하여야 한다")
    if not (0 < p.l_step <= p.l_ch):
        raise ValueError("l_hbn_step 은 0 < l <= l_ch 이어야 한다")

    x_min, x_max = -p.l_src_pad, p.l_ch + p.l_drn_pad
    x_tg0, x_tg1 = -p.tg_overhang_src, p.l_ch + p.tg_overhang_drn

    y_bg = -p.t_ox
    y_src_bot = p.t_wse2                       # Source 아랫면 = Source 쪽 WSe2 윗면
    y_src_top = p.t_wse2 + p.t_source          # Source 윗면
    y_drn_top = p.t_drain                      # Drain 윗면 = Drain 쪽 WSe2 아랫면
    y_film_drn_top = p.t_drain + p.t_wse2      # Drain 쪽 WSe2 윗면
    # h-BN 윗면 = 아랫면 + t_hbn (수직 두께 일정). 아랫면은 Source 위에서는 Source 윗면,
    # Drain 쪽에서는 WSe2 윗면이다.
    y_hbn_top_src = y_src_top + p.t_hbn
    y_hbn_top_drn = y_film_drn_top + p.t_hbn

    d = p.t_gate_dummy
    pts = {
        # --- 도메인 왼쪽 벽 (x = x_min), 아래에서 위로 ---
        "bg_l":   (x_min, y_bg),
        "ox_l":   (x_min, 0.0),
        "src_bl": (x_min, y_src_bot),
        "src_tl": (x_min, y_src_top),
        "hbn_tl": (x_min, y_hbn_top_src),
        # --- 채널 구간 ---
        "apex":          (p.x_lift, 0.0),        # 아래 공기 쐐기(AirBot)의 뾰족한 끝 = WSe2 가 SiO2 에서 뜨는 점
        "src_edge_bot":  (0.0, y_src_bot),       # ***** source junction (금속-WSe2 모서리) *****
        "src_edge_top":  (0.0, y_src_top),       # Source 윗면 오른쪽 모서리 = h-BN 아랫면이 꺾이는 점
        "hbn_kink_src":  (0.0, y_hbn_top_src),   # h-BN 윗면(=TG 선)이 꺾이는 점
        "dr_bl":         (p.l_ch, 0.0),          # Drain 왼쪽 아래 모서리
        "drn_corner":    (p.l_ch, y_drn_top),    # ***** drain junction (금속-WSe2 모서리) *****
        "slope_top_end": (p.l_ch, y_film_drn_top),
        "hbn_kink_drn":  (p.l_ch, y_hbn_top_drn),
        # --- 도메인 오른쪽 벽 (x = x_max) ---
        "bg_r":       (x_max, y_bg),
        "ox_r":       (x_max, 0.0),
        "drn_tr":     (x_max, y_drn_top),
        "film_r_top": (x_max, y_film_drn_top),
        "hbn_tr":     (x_max, y_hbn_top_drn),
        # --- TG 접촉선의 양 끝 (h-BN 윗면 위) ---
        "tg_l": (x_tg0, y_hbn_top_src),
        "tg_r": (x_tg1, y_hbn_top_drn),
        # --- 접점 판별/시각화 전용 더미 점 ---
        "tg_tl":  (x_tg0, y_hbn_top_src + d),
        "tg_tr":  (x_tg1, y_hbn_top_drn + d),
        "bgd_bl": (x_min, y_bg - d),
        "bgd_br": (x_max, y_bg - d),
    }
    # h-BN 아랫면이 경사 WSe2 윗면에 닿는 점(touch). l_step == L 이면 기존 점 slope_top_end 와 같으므로
    # 새 점을 만들지 않는다 (같은 위치에 점이 둘 있으면 T-junction/0길이 선이 생긴다).
    if p.l_step < p.l_ch:
        same = [k for k, xk in enumerate(p.ramp_breakpoints()[1:-1], start=1) if abs(xk - p.l_step) < 1e-9]
        if same:            # 접점이 곡선 꼭짓점 rt_k 와 일치: 그 꼭짓점을 touch 로 쓴다 (같은 위치 점 2개 금지)
            k = same[0]
            del pts[f"rt_{k}"]
            pts["touch"] = (p.l_step, float(p.film_top(p.l_step)))
        else:
            pts["touch"] = (p.l_step, float(p.film_top(p.l_step)))
        pts["hbn_kink_touch"] = (p.l_step, float(p.film_top(p.l_step)) + p.t_hbn)
    # S자 곡선 경사: 꺾은선 내부 꼭짓점 (아랫면 rb_k, 윗면 rt_k)
    for k, xk in enumerate(p.ramp_breakpoints()[1:-1], start=1):
        pts[f"rb_{k}"] = (xk, float(p.film_bottom(xk)))
        pts[f"rt_{k}"] = (xk, float(p.film_top(xk)))
    for name in [n for n in list(pts) if n.startswith("rt_")]:
        xk, yk = pts[name]
        if xk > p.l_step + 1e-9:                    # 접점 뒤: h-BN 이 박막 위에 얹혀 같이 꺾인다
            pts["hk_" + name[3:]] = (xk, yk + p.t_hbn)
    # 경사 시작점이 Source 모서리보다 오른쪽이면 WSe2 윗면이 꺾이는 점 lift_top 이 생긴다.
    # (touch 와 같은 x 이면 점을 하나만 둔다 — 같은 위치 점 2개 금지)
    if p.x_lift > 1e-9 and not (p.l_step < p.l_ch and abs(p.l_step - p.x_lift) < 1e-9):
        pts["lift_top"] = (p.x_lift, p.t_wse2)
        if p.l_step < p.x_lift:        # h-BN 이 이미 박막에 닿아 있으면 h-BN 윗면(TG 선)도 여기서 꺾인다
            pts["hbn_kink_lift"] = (p.x_lift, p.t_wse2 + p.t_hbn)
    return {k: (float(v[0]), float(v[1])) for k, v in pts.items()}


# ==============================================================================
# 섹션 3. 영역(다각형) 정의
#   - mesh 영역(= DEVSIM region) 5개 : SiO2, WSe2, AirBot, AirTop, hBN
#   - mesh 없는 금속 본체 4개       : Source, Drain, TG, BG (이상적 등전위체, 내부를 풀지 않음)
#   점은 반드시 반시계(CCW) 순서. 이웃 영역과 공유하는 선은 서로 반대 방향으로 지난다.
# ==============================================================================
REGIONS = ["SiO2", "WSe2", "AirBot", "AirTop", "hBN"]
METALS = ["Source", "Drain", "TG", "BG"]
REGION_MATERIAL = {"SiO2": "SiO2", "WSe2": "WSe2", "AirBot": "Air", "AirTop": "Air", "hBN": "hBN"}
TILING = ["SiO2", "WSe2", "AirBot", "AirTop", "hBN", "Source", "Drain"]   # 도메인을 빈틈없이 채우는 7개


def film_top_chain(p: Params, points):
    """WSe2 윗면을 왼쪽(src_edge_bot)에서 오른쪽(slope_top_end)으로 따라갈 때 지나는 점 이름들."""
    mid = []
    if "touch" in points:
        mid.append((points["touch"][0], "touch"))
    if "lift_top" in points:
        mid.append((points["lift_top"][0], "lift_top"))
    mid += [(v[0], n) for n, v in points.items() if n.startswith("rt_")]
    mid.sort()
    return ["src_edge_bot"] + [n for _, n in mid] + ["slope_top_end"]


def film_bottom_chain(points):
    """WSe2 아랫면: apex 에서 drn_corner 까지 (곡선 꼭짓점 rb_k 포함, x 오름차순)"""
    mid = sorted((v[0], n) for n, v in points.items() if n.startswith("rb_"))
    return ["apex"] + [n for _, n in mid] + ["drn_corner"]


KINK_OF = {"touch": "hbn_kink_touch", "lift_top": "hbn_kink_lift"}   # rt_k → hk_k 는 build_points 에서 추가


def build_polygons(p: Params, points=None) -> dict:
    """Params -> {영역 이름: [점 이름, ...]} (CCW).
    touch(h-BN 이 박막에 닿는 점)와 lift_top(박막이 SiO2 에서 뜨는 점)의 유무·순서에 따라 WSe2/AirTop/hBN/TG 가 달라진다."""
    points = points or build_points(p)
    chain = film_top_chain(p, points)                     # src_edge_bot ... slope_top_end
    touch = "touch" if "touch" in points else "slope_top_end"
    i_t = chain.index(touch)
    before = chain[:i_t + 1]                              # 박막 윗면 중 h-BN 이 닿지 않는 구간 (AirTop 의 아랫변)
    after = chain[i_t:]                                   # 박막 윗면 중 h-BN 이 닿는 구간 (hBN 의 아랫변 일부)
    def kink_of(n):
        return KINK_OF.get(n, "hk_" + n[3:] if n.startswith("rt_") else None)
    kinks_after = [kink_of(n) for n in after[:-1] if kink_of(n)]     # slope_top_end 의 kink 는 hbn_kink_drn
    bottom = film_bottom_chain(points)                                # apex ... drn_corner
    return {
        # SiO2: 윗면이 x_lift, x=L 에서 꺾이는 이유는 구간마다 접하는 상대(WSe2 / 공기 / Drain)가 다르기 때문
        "SiO2": ["bg_l", "bg_r", "ox_r", "dr_bl", "apex", "ox_l"],
        # WSe2: 수직 두께 일정한 띠. 아랫면(왼->오): ox_l, apex, drn_corner, drn_tr. 윗면(오->왼): chain 역순
        "WSe2": ["ox_l"] + bottom + ["drn_tr", "film_r_top"] + chain[::-1] + ["src_bl"],
        # AirBot: 경사진 WSe2 아래의 직각삼각형 (x_lift,0), (L,0), (L,t_drain). 꼭지각 atan(t_drain/l_ramp)
        "AirBot": ["apex", "dr_bl", "drn_corner"] + bottom[1:-1][::-1],
        # AirTop: Source 벽 + 박막 윗면(touch 까지) + h-BN 아랫면(하강선)
        "AirTop": before + ["src_edge_top"],
        # hBN: 아랫면 = Source 윗면 -> 하강선 -> 박막 윗면(touch 이후) -> Drain 쪽. 윗면 = 아랫면 + t_hbn (kink 점들)
        "hBN": (["src_tl", "src_edge_top"] + after + ["film_r_top", "hbn_tr", "tg_r", "hbn_kink_drn"]
                + kinks_after[::-1] + ["hbn_kink_src", "tg_l", "hbn_tl"]),
        # --- 금속 본체 (mesh 없음) ---
        "Source": ["src_bl", "src_edge_bot", "src_edge_top", "src_tl"],
        "Drain":  ["dr_bl", "ox_r", "drn_tr", "drn_corner"],
        "TG":     ["tg_l", "hbn_kink_src"] + kinks_after + ["hbn_kink_drn", "tg_r", "tg_tr", "tg_tl"],
        "BG":     ["bgd_bl", "bgd_br", "bg_r", "bg_l"],
    }


# ==============================================================================
# 섹션 4. 위상(topology): 맞닿는 선으로부터 contact / interface를 자동으로 뽑는다
#   (mesh 영역) 선 (mesh 영역) -> interface,  (mesh 영역) 선 (금속) -> contact,  한 영역만 -> Neumann
# ==============================================================================
def edges_of(vertex_names):
    n = len(vertex_names)
    return [(vertex_names[i], vertex_names[(i + 1) % n]) for i in range(n)]


def edge_key(a, b):
    return tuple(sorted((a, b)))


def classify_edges(polygons):
    owners = {}
    for pname, vnames in polygons.items():
        for a, b in edges_of(vnames):
            owners.setdefault(edge_key(a, b), []).append(pname)
    contacts, interfaces, outer = {}, {}, {}
    for key in sorted(owners):
        ps = owners[key]
        if len(ps) == 1:
            if ps[0] in REGIONS:
                outer.setdefault(ps[0], []).append(key)
        elif len(ps) == 2:
            a_reg, b_reg = ps[0] in REGIONS, ps[1] in REGIONS
            if a_reg and b_reg:
                pair = tuple(sorted(ps, key=REGIONS.index))
                interfaces.setdefault(pair, []).append(key)
            elif a_reg != b_reg:
                region, metal = (ps[0], ps[1]) if a_reg else (ps[1], ps[0])
                contacts.setdefault((metal, region), []).append(key)
            else:
                raise ValueError(f"금속끼리 맞닿은 선: {key} {ps}")
        else:
            raise ValueError(f"한 선을 3개 이상의 다각형이 공유: {key} {ps}")
    return contacts, interfaces, outer


# 이름 규칙 (DEVSIM 이름과 gmsh physical group 이름을 한 곳에서 만든다)
def contact_name(metal, region):
    return f"{metal}_{region}"


def interface_name(r1, r2):
    return f"{r1}_{r2}"


def gmsh_region_name(region):
    return f"R_{region}"


def gmsh_contact_name(metal, region):
    return f"C_{metal}_{region}"


def gmsh_interface_name(r1, r2):
    return f"I_{r1}_{r2}"


# ==============================================================================
# 섹션 5. geometry 검사
# ==============================================================================
def polygon_xy(points, vertex_names):
    return np.array([points[n] for n in vertex_names], dtype=float)


def signed_area(xy):
    x, y = xy[:, 0], xy[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def points_in_polygon(pts, poly):
    x, y = pts[:, 0], pts[:, 1]
    inside = np.zeros(len(x), dtype=bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        crosses = (y1 > y) != (y2 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            x_int = (x2 - x1) * (y - y1) / (y2 - y1) + x1
        inside ^= crosses & (x < x_int)
    return inside


def analytic_areas(p: Params):
    """각 영역 면적을 다각형과 무관하게 손으로 푼 식으로 계산한다 (검사용).
    WSe2, hBN 은 "수직 두께가 일정한 띠"이므로 면적 = 두께 x 도메인 폭 이 정확히 성립한다."""
    w = p.l_src_pad + p.l_ch + p.l_drn_pad
    l = p.l_step
    y_src_top = p.t_wse2 + p.t_source
    # AirTop = ∫0^l [h-BN 아랫면(직선: y_src_top -> film_top(l)) - film_top(x)] dx
    #        = l*(y_src_top + film_top(l))/2 - [t_wse2*l + ∫0^l film_bottom]
    #   ∫0^l film_bottom = 0.5*(l - x_lift)*film_bottom(l)  (l > x_lift 일 때, 아니면 0)
    # 경사 꺾은선(폴리곤과 같은 꼭짓점) 아래 면적: 사다리꼴 합. 곡선일 때 폴리곤도 같은 꺾은선이므로 정확히 일치해야 한다.
    bx = np.array(p.ramp_breakpoints()); by = np.array([float(p.film_bottom(x)) for x in bx])
    def int_bottom_to(xe):
        """∫_{x_lift}^{xe} film_bottom(꺾은선) dx"""
        if xe <= p.x_lift:
            return 0.0
        xs_ = np.append(bx[bx < xe], xe); ys_ = np.append(by[bx < xe], float(p.film_bottom(xe)))
        return float(np.sum(0.5 * (ys_[1:] + ys_[:-1]) * np.diff(xs_)))
    air_bot = int_bottom_to(p.l_ch)
    air_top = l * (y_src_top + float(p.film_top(l))) / 2 - (p.t_wse2 * l + int_bottom_to(l))
    return {
        "SiO2": w * p.t_ox,
        "WSe2": w * p.t_wse2,
        "AirBot": air_bot,
        "AirTop": air_top,
        "hBN": w * p.t_hbn,
        "Source": p.l_src_pad * p.t_source,
        "Drain": p.l_drn_pad * p.t_drain,
    }


def hbn_top_kinks(points):
    """h-BN 윗면(TG 선)이 x=0 과 x=L 사이에서 꺾이는 점들 (x 오름차순)"""
    ks = [(points[n][0], n) for n in ("hbn_kink_touch", "hbn_kink_lift") if n in points]
    ks += [(v[0], n) for n, v in points.items() if n.startswith("hk_")]
    return [n for _, n in sorted(ks)]


def domain_area(points, p: Params):
    """도메인 전체 면적: 아랫변 y = -t_ox, 윗변 = h-BN 윗면 꺾은선 (hbn_tl -> ... -> hbn_tr)"""
    top = ["hbn_tl", "tg_l", "hbn_kink_src"] + hbn_top_kinks(points) + ["hbn_kink_drn", "tg_r", "hbn_tr"]
    area = 0.0
    for a, b in zip(top[:-1], top[1:]):
        (xa, ya), (xb, yb) = points[a], points[b]
        area += (xb - xa) * (0.5 * (ya + yb) + p.t_ox)
    return area


EXPECTED_CONTACTS = {
    ("Source", "WSe2"): "Source 금속이 WSe2 윗면에 직접 닿는다 (top contact)",
    ("Source", "AirTop"): "Source 금속의 오른쪽 벽은 위 공기 쐐기와 닿는다",
    ("Source", "hBN"): "Source 금속의 윗면이 h-BN과 닿는다 (TG 전기장을 막는 면)",
    ("Drain", "WSe2"): "Drain 금속이 WSe2 아랫면에 직접 닿는다 (bottom contact)",
    ("Drain", "SiO2"): "Drain 금속이 SiO2 위에 놓인다 (BG 전기장을 막는 면)",
    ("Drain", "AirBot"): "Drain 금속의 왼쪽 벽은 아래 공기 쐐기와 닿는다",
    ("TG", "hBN"): "Top Gate는 h-BN 윗면에만 닿는다 (꺾은선)",
    ("BG", "SiO2"): "Back Gate는 SiO2 아랫면에만 닿는다",
}
EXPECTED_INTERFACES = {
    ("SiO2", "WSe2"): "Source 아래에서 WSe2가 SiO2 위에 놓인다",
    ("SiO2", "AirBot"): "아래 공기 쐐기의 바닥",
    ("WSe2", "AirBot"): "경사진 WSe2의 아랫면",
    ("WSe2", "AirTop"): "경사진 WSe2 윗면 중 h-BN이 닿지 않는 구간 (0 ~ l_hbn_step)",
    ("WSe2", "hBN"): "WSe2 윗면 중 h-BN이 닿는 구간 (l_hbn_step ~ L) + Drain 쪽 평평한 윗면",
    ("AirTop", "hBN"): "h-BN 아랫면의 하강선",
}


def run_checks(points, polygons, p: Params, verbose=True):
    results = []

    def report(name, passed, detail=""):
        results.append(bool(passed))
        if verbose:
            print(f"  [{'OK  ' if passed else 'FAIL'}] {name}  {detail}")

    xy = {k: polygon_xy(points, v) for k, v in polygons.items()}
    areas = {k: signed_area(v) for k, v in xy.items()}
    report("모든 다각형이 반시계(CCW)", all(a > 0 for a in areas.values()),
           "(면적<=0: %s)" % [k for k, a in areas.items() if a <= 0])

    # 같은 위치의 점이 둘 이상 있으면 안 된다
    coords = {}
    for n, c in points.items():
        coords.setdefault((round(c[0], 9), round(c[1], 9)), []).append(n)
    dup = [v for v in coords.values() if len(v) > 1]
    report("같은 위치의 점 없음", not dup, f"{dup}" if dup else "")

    bad = []
    for pname, vn in polygons.items():
        for a, b in edges_of(vn):
            pa, pb = np.array(points[a]), np.array(points[b])
            ab = pb - pa
            for qn, q in points.items():
                if qn in (a, b):
                    continue
                t = np.dot(np.array(q) - pa, ab) / np.dot(ab, ab)
                dist = np.linalg.norm(np.array(q) - (pa + t * ab))
                if 1e-9 < t < 1 - 1e-9 and dist < 1e-9:
                    bad.append((pname, a, b, qn))
    report("T-junction 없음", not bad, f"{bad}" if bad else "")

    direction = {}
    for pname, vn in polygons.items():
        for a, b in edges_of(vn):
            direction.setdefault(edge_key(a, b), []).append((pname, a, b))
    bad = [k for k, v in direction.items()
           if len(v) > 2 or (len(v) == 2 and not (v[0][1] == v[1][2] and v[0][2] == v[1][1]))]
    report("공유 선은 2개 다각형이 반대 방향", not bad, f"{bad}" if bad else "")

    ana = analytic_areas(p)
    worst = max(abs(areas[k] - ana[k]) for k in ana)
    report("영역 면적 = 해석식", worst < 1e-6, f"(최대 오차 {worst:.2e} nm^2)")

    dom = domain_area(points, p)
    tot = sum(areas[k] for k in TILING)
    report("7개 영역 면적 합 = 도메인 면적", abs(tot - dom) < 1e-6, f"(합 {tot:.3f}, 도메인 {dom:.3f} nm^2)")

    # 래스터 검사: 도메인 안의 모든 표본점이 정확히 1개 영역에만 속한다
    x_min, x_max = points["bg_l"][0], points["bg_r"][0]
    y_lo = -p.t_ox
    y_hi = max(points["hbn_tl"][1], points["hbn_tr"][1])
    gx, gy = np.meshgrid(np.linspace(x_min + 0.1234, x_max - 0.1234, 1700),
                         np.linspace(y_lo + 0.0777, y_hi - 0.0777, 330))
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    # 도메인 윗변(h-BN 윗면 꺾은선) 아래의 점만 검사
    top_names = ["hbn_tl", "hbn_kink_src"] + hbn_top_kinks(points) + ["hbn_kink_drn", "hbn_tr"]
    tx = np.array([points[n][0] for n in top_names])
    ty = np.array([points[n][1] for n in top_names])
    pts = pts[pts[:, 1] < np.interp(pts[:, 0], tx, ty) - 1e-6]
    count = np.zeros(len(pts), dtype=int)
    for k in TILING:
        count += points_in_polygon(pts, xy[k]).astype(int)
    n_gap, n_dup = int(np.sum(count == 0)), int(np.sum(count > 1))
    report("표본점 %d개: 빈틈 0, 겹침 0" % len(pts), n_gap == 0 and n_dup == 0, f"(빈틈 {n_gap}, 겹침 {n_dup})")

    contacts, interfaces, _ = classify_edges(polygons)
    report("contact 목록 = 의도", set(contacts) == set(EXPECTED_CONTACTS),
           f"(차이: {set(contacts) ^ set(EXPECTED_CONTACTS)})")
    report("interface 목록 = 의도", set(interfaces) == set(EXPECTED_INTERFACES),
           f"(차이: {set(interfaces) ^ set(EXPECTED_INTERFACES)})")

    # h-BN 수직 두께가 어디서나 t_hbn 인지: 윗면 꺾은선과 아랫면 꺾은선의 차이를 표본 x에서 확인
    _chain = film_top_chain(p, points)
    bot_names = ["src_tl", "src_edge_top"] + _chain[_chain.index("touch" if "touch" in points else "slope_top_end"):] + ["film_r_top"]
    bx = np.array([points[n][0] for n in bot_names])
    by = np.array([points[n][1] for n in bot_names])
    xs = np.linspace(x_min, x_max, 5001)
    xs = xs[(xs > x_min) & (np.abs(xs) > 1e-6)]          # x=0 수직벽은 제외
    dev = np.max(np.abs((np.interp(xs, tx, ty) - np.interp(xs, bx, by)) - p.t_hbn))
    report("h-BN 수직 두께 = 논문값 (모든 x)", dev < 1e-9, f"(최대 편차 {dev:.2e} nm)")
    return all(results), results


# ==============================================================================
# 섹션 6. 그림
# ==============================================================================
def plot_geometry(points, polygons, p: Params, outfile, title=""):
    """전체 단면 + 두 junction 확대. 색: rfet_plotstyle.MATERIAL_FACE (재료별 고정)."""
    import rfet_plotstyle as st
    st.apply()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon, Patch, Rectangle

    fig = plt.figure(figsize=(11, 7.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25], hspace=0.42, wspace=0.18)
    ax0 = fig.add_subplot(gs[0, :])
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[1, 1])
    y_hi = max(points["hbn_tl"][1], points["hbn_tr"][1])
    L = p.l_ch
    zoom1 = ((-80, 200), (-20, 125))
    zoom2 = ((L - 150, L + 80), (-20, 125))
    windows = [(ax0, (points["bg_l"][0], points["bg_r"][0]), (-p.t_ox - 55, y_hi + 45)),
               (ax1, *zoom1), (ax2, *zoom2)]

    def draw(ax):
        for name, vn in polygons.items():
            ax.add_patch(MplPolygon(polygon_xy(points, vn), closed=True, facecolor=st.MATERIAL_FACE[name],
                                    edgecolor=st.INK2, linewidth=0.5,
                                    hatch="////" if name.startswith("Air") else None))
        for pt in ("src_edge_bot", "drn_corner"):
            ax.plot(*points[pt], "o", color=st.RED, ms=5, mec="white", mew=0.8, zorder=6)
        if "touch" in points:
            ax.plot(*points["touch"], "s", color=st.BLUE, ms=4.5, mec="white", mew=0.8, zorder=6)

    for ax, xlim, ylim in windows:
        draw(ax)
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        ax.set_aspect("equal")
        ax.set_xlabel("x (nm)"); ax.set_ylabel("y (nm)")
        ax.grid(False)
        ax.set_anchor("N")

    # --- 전체 그림: 이름, 치수 ---
    ax0.set_title(f"Cross-section — {title}")
    xc = 0.5 * (points["bg_l"][0] + points["bg_r"][0])
    ax0.text(xc, -p.t_ox / 2, "SiO₂  300 nm", ha="center", va="center", color=st.INK2)
    ax0.text(points["src_bl"][0] + 430, 0.5 * (p.t_wse2 + p.t_wse2 + p.t_source), "Source", ha="center", va="center", fontsize=8.5)
    ax0.text(points["dr_bl"][0] + 520, 0.5 * p.t_drain, "Drain", ha="center", va="center", fontsize=8.5)
    ax0.text(points["tg_r"][0] + 60, points["hbn_tr"][1] - 14, "h-BN 30 nm", ha="left", va="center", fontsize=8)
    ax0.text(0.5 * (points["tg_l"][0] + points["tg_r"][0]), y_hi + 30, "Top gate (metal line on h-BN)", ha="center", fontsize=8, color=st.INK2)
    ax0.text(xc, -p.t_ox - 36, "Back gate (metal line, SiO₂ bottom)", ha="center", va="top", fontsize=8, color=st.INK2)
    ax0.annotate("", xy=(L, -40), xytext=(0, -40), arrowprops=dict(arrowstyle="<->", color=st.INK, lw=0.9))
    ax0.text(L / 2, -58, f"L = {L:.0f} nm", ha="center", va="top", fontsize=8.5)
    for (xl, xh), (yl, yh) in (zoom1, zoom2):
        ax0.add_patch(Rectangle((xl, yl), xh - xl, yh - yl, fill=False, ec=st.INK, lw=0.8, ls=(0, (3, 2))))
    legend = [Patch(facecolor=st.MATERIAL_FACE[k], edgecolor=st.INK2, lw=0.5, label=st.MATERIAL_LABEL[k])
              for k in ("WSe2", "hBN", "SiO2", "Source")]
    legend.append(Patch(facecolor="white", edgecolor=st.INK2, hatch="////", lw=0.5, label="air gap"))
    ax0.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.0, -0.22), ncol=5, frameon=False)

    # --- 확대 그림 ---
    ax1.set_title("Source junction (zoom)")
    ax2.set_title("Drain junction (zoom)")
    ax1.annotate("source junction (0, 9.1)", points["src_edge_bot"], (30, -16), fontsize=8,
                 arrowprops=dict(arrowstyle="-", color=st.INK2, lw=0.7))
    ax1.annotate("upper air wedge", (40, 45), (95, 100), fontsize=8, arrowprops=dict(arrowstyle="-", color=st.INK2, lw=0.7))
    ax1.annotate("lower air wedge", (150, 10), (120, 60), fontsize=8, arrowprops=dict(arrowstyle="-", color=st.INK2, lw=0.7))
    ax1.text(-60, 36, "Source\n(Pd/Au, 55 nm)", ha="center", va="center", fontsize=8)
    ax1.text(-40, 3.5, "WSe₂ 9.1 nm", ha="center", va="center", fontsize=7.5)
    ax2.annotate("drain junction\n(L, 71)", points["drn_corner"], (L - 140, 100), fontsize=8,
                 arrowprops=dict(arrowstyle="-", color=st.INK2, lw=0.7))
    ax2.text(L + 40, 35, "Drain\n(Au/Ti, 71 nm)", ha="center", va="center", fontsize=8)
    ax2.text(L + 40, p.t_drain + p.t_wse2 / 2, "WSe₂", ha="center", va="center", fontsize=7.5)
    if "touch" in points:
        ax1.annotate("h-BN touches WSe₂", points["touch"], (points["touch"][0] + 40, points["touch"][1] + 40),
                     fontsize=8, arrowprops=dict(arrowstyle="-", color=st.INK2, lw=0.7))
    fig.savefig(outfile)
    plt.close(fig)
    return outfile


# ==============================================================================
# 섹션 7. 실행
# ==============================================================================
def print_summary(points, polygons, p: Params):
    theta = p.slope_deg
    l = p.l_step
    y_src_top = p.t_wse2 + p.t_source
    desc = math.degrees(math.atan2(y_src_top - p.film_top(l), l))     # h-BN 하강선 각도 (아래쪽 +)
    print("\n[기하 요약]")
    print(f"  l_hbn_step = {l:.2f} nm  ({'bridge: 처짐 없음' if l >= p.l_ch else 'sag: 경사 WSe2에 닿음'})")
    print(f"  WSe2 경사: x = {p.x_lift:.1f} → {p.l_ch:.1f} (가로 {p.l_ramp:.1f} nm), 모양 {p.ramp_shape}, 평균 경사각 atan(t_drain/l_ramp) = {theta:.3f} deg,  경사 길이 {math.hypot(p.l_ramp, p.t_drain):.2f} nm")
    mech = ramp_mechanics(p)
    if mech["shape"] == "smooth":
        print(f"  경사 역학 검사(클램프 큐빅): 최대 기울기 {mech['slope_max_deg']:.1f} deg (가운데), 최소 곡률반경 {mech['radius_min_nm']:.0f} nm (양 끝), "
              f"표면 변형률 t/2R = {100 * mech['strain_surface']:.1f} %  {'< 파단 7.3 % OK' if mech['ok'] else '>= 파단 7.3 % — 비현실적'}")
    else:
        print("  경사 역학 검사: 꺾인 직선은 꺾임점 곡률이 무한대 → 기하 근사(역학적 근거 없음, 대조군)")
    print(f"  탄성 추정 참고: ℓ*(WSe2) = {ramp_length_elastic(p):.1f} nm,  ℓ*(h-BN) = {sag_step_elastic(p):.1f} nm {'> L → 판' if sag_step_elastic(p) > p.l_ch else '< L'}")
    print(f"  h-BN 하강선 각도 = {desc:.2f} deg (수평 아래로),  하강 구간의 h-BN 법선 두께 = "
          f"{p.t_hbn * math.cos(math.radians(desc)):.1f} nm  (수직 두께 {p.t_hbn} nm; 차이는 '수직 두께 일정' 근사의 오차)")
    slope_at_touch = theta if l > p.x_lift + 1e-9 else 0.0
    print(f"  위 공기 쐐기(AirTop) 꼭지각 = {slope_at_touch + desc:.2f} deg,  최대 높이(x=0) = {p.t_source} nm")
    # TG(h-BN 윗면)와 경사 WSe2 윗면 사이의 수직 거리: TG 꺾은선과 WSe2 윗면을 x에서 보간
    _kn = ["hbn_kink_src"] + hbn_top_kinks(points) + ["hbn_kink_drn"]
    tgx = [points[n][0] for n in _kn]
    tgy = [points[n][1] for n in _kn]
    gaps = [(x, float(np.interp(x, tgx, tgy)) - p.film_top(x)) for x in (0.0, 25.0, l, 0.5 * p.l_ch, p.l_ch)]
    print("  TG - 경사 WSe2 윗면 수직 거리 [nm]: " + ", ".join(f"x={x:.0f}: {g:.1f}" for x, g in gaps))
    print("\n[영역별 좌표 범위 (nm)]")
    for name in REGIONS + METALS:
        xy = polygon_xy(points, polygons[name])
        print(f"  {name:7s}  x: [{xy[:, 0].min():8.1f}, {xy[:, 0].max():8.1f}]   "
              f"y: [{xy[:, 1].min():7.1f}, {xy[:, 1].max():7.1f}]   꼭짓점 {len(xy)}")
    contacts, interfaces, outer = classify_edges(polygons)
    print("\n[contact]")
    for (m, r), keys in sorted(contacts.items()):
        length = sum(np.linalg.norm(np.array(points[a]) - np.array(points[b])) for a, b in keys)
        print(f"  {contact_name(m, r):14s} {len(keys)}개  길이 {length:8.1f} nm   - {EXPECTED_CONTACTS[(m, r)]}")
    print("[interface]")
    for (r1, r2), keys in sorted(interfaces.items()):
        length = sum(np.linalg.norm(np.array(points[a]) - np.array(points[b])) for a, b in keys)
        print(f"  {interface_name(r1, r2):14s} {len(keys)}개  길이 {length:8.1f} nm   - {EXPECTED_INTERFACES[(r1, r2)]}")
    print("[Neumann 경계 선 개수]  " + ", ".join(f"{r}: {len(outer.get(r, []))}" for r in REGIONS))


def run_config(name, p: Params, plot=True):
    pts = build_points(p)
    polys = build_polygons(p)
    print(f"\n######## CONFIG '{name}' ########")
    print("=== geometry 검사 ===")
    ok, _ = run_checks(pts, polys, p)
    print_summary(pts, polys, p)
    if plot:
        print("그림 저장:", plot_geometry(pts, polys, p, f"rfet_geometry_{name}.png",
                                     f"config '{name}'  (l_hbn_step = {p.l_step:.1f} nm)"))
    print("판정:", "모두 통과" if ok else "FAIL 있음")
    return ok


if __name__ == "__main__":
    names = sys.argv[1:] or list(CONFIGS)
    all_ok = all(run_config(n, CONFIGS[n]) for n in names)
    raise SystemExit(0 if all_ok else 1)
