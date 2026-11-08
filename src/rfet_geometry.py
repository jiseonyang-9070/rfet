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

    # [모델 가정] Top Gate / Back Gate 금속 "본체"의 두께 [nm]. 시각화와 접점 판별 전용.
    # 정전기 계산에서는 금속 내부를 풀지 않고 h-BN 윗면 / SiO2 아랫면의 선에 전압을 걸 뿐이다.
    t_gate_dummy: float = 20.0

    @property
    def l_step(self):
        return self.l_ch if self.l_hbn_step is None else float(self.l_hbn_step)

    def film_top(self, x):
        """경사 구간(0 <= x <= L)에서 WSe2 윗면 높이 y(x)"""
        return self.t_wse2 + self.t_drain * x / self.l_ch


def sag_step_for_angle(p: Params, angle_deg):
    """h-BN 아랫면이 Source 모서리 (0, y_src_top)에서 각도 angle_deg 로 내려와 경사 WSe2 윗면에
    닿는 전이 길이 l 을 푼다.  (y_src_top - film_top(l)) / l = tan(angle)
    -> (t_src + t_wse2 - t_wse2 - t_drain*l/L) / l = tan  -> l = t_src / (tan + t_drain/L)"""
    return p.t_source / (math.tan(math.radians(angle_deg)) + p.t_drain / p.l_ch)


def sag_step_elastic(p: Params, E_pa=0.86e12, nu=0.2, gamma_j_m2=0.45):
    """h-BN 박편이 높이 h 의 단차를 넘어 다시 기판(WSe2)에 밀착하기까지의 전이 길이 l 의 탄성 추정 [nm].
    판의 굽힘 에너지 ~ D h^2 / l^3 (D = E t^3 / 12(1-ν^2)) 와 밀착으로 얻는 접착 에너지 ~ Γ l 의 합을 l 로
    최소화하면  l = (3 D h^2 / Γ)^(1/4).
      [문헌값] E(h-BN) = 0.86 TPa: Falin et al., Nat. Commun. 8, 15815 (2017), 1L 0.865±0.073, 9L 0.856±0.003 TPa (AFM 압입)
      [모델 가정] ν = 0.2 (얇은 판 근사에서 결과에 수 % 영향), Γ = 0.45 J/m^2 는 그래핀/SiO2 의 고전적 측정값
                 (Koenig et al., Nat. Nanotechnol. 6, 543 (2011)) 을 차용한 것. h-BN/WSe2 의 Γ 는 확보하지 못함.
                 Γ 를 0.1~1 J/m^2 로 바꿔도 l 은 1/4 제곱으로만 변한다 (0.1 -> 650 nm, 1 -> 370 nm).
    h = Source 단차 높이 = t_source (h-BN 아랫면이 Source 윗면에서 경사 WSe2 윗면으로 내려오는 높이, 경사 보정은 무시)."""
    t = p.t_hbn * 1e-9
    D = E_pa * t ** 3 / (12.0 * (1.0 - nu ** 2))
    h = p.t_source * 1e-9
    return (3.0 * D * h ** 2 / gamma_j_m2) ** 0.25 * 1e9


# 이름 붙은 설정.
_base = Params()
CONFIGS = {
    # bridge: 처짐 0. l = L.  탄성 추정 l(≈450 nm) 이 L(500 nm) 에 가까우므로 물리적으로도 baseline 에 가장 가깝다.
    "bridge": _base,
    # elastic: 탄성 추정 전이 길이 (sag_step_elastic). bridge 와 차이가 작아 "bridge 가 과장이 아님" 을 보이는 용도.
    "elastic": replace(_base, l_hbn_step=min(sag_step_elastic(_base), _base.l_ch)),
    # sag45: 하강 각도 45도. 30 nm 두께 박편이 곡률반경 ~40 nm 로 꺾이려면 표면 변형률 t/2R ≈ 35% 가 필요해
    #        물리적으로 불가능하다. "TG 가 채널에 최대한 가까운 가상의 하한" 으로서 민감도 비교에만 쓴다.
    "sag45": replace(_base, l_hbn_step=sag_step_for_angle(_base, 45.0)),
}


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
        "apex":          (0.0, 0.0),             # 아래 공기 쐐기(AirBot)의 뾰족한 끝
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
        pts["touch"] = (p.l_step, p.film_top(p.l_step))
        pts["hbn_kink_touch"] = (p.l_step, p.film_top(p.l_step) + p.t_hbn)
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


def build_polygons(p: Params) -> dict:
    """Params -> {영역 이름: [점 이름, ...]} (CCW). touch 점 유무에 따라 WSe2/AirTop/hBN 이 달라진다."""
    has_touch = p.l_step < p.l_ch
    touch = "touch" if has_touch else "slope_top_end"
    # 경사 WSe2 윗면: src_edge_bot -> (touch) -> slope_top_end 순으로 올라간다
    slope_top_up = ["src_edge_bot"] + (["touch"] if has_touch else []) + ["slope_top_end"]
    return {
        # SiO2: 윗면이 x=0, x=L에서 꺾이는 이유는 구간마다 접하는 상대(WSe2 / 공기 / Drain)가 다르기 때문
        "SiO2": ["bg_l", "bg_r", "ox_r", "dr_bl", "apex", "ox_l"],
        # WSe2: 수직 두께 일정한 Z자 띠. 윗면(오른쪽->왼쪽)은 slope_top_up 의 역순
        "WSe2": ["ox_l", "apex", "drn_corner", "drn_tr", "film_r_top"] + slope_top_up[::-1] + ["src_bl"],
        # AirBot: 경사진 WSe2 아래의 직각삼각형 (0,0), (L,0), (L,t_drain). 꼭지각 atan(t_drain/L)
        "AirBot": ["apex", "dr_bl", "drn_corner"],
        # AirTop: Source 벽, 경사 WSe2 윗면, h-BN 아랫면(하강선)으로 둘러싸인 삼각형
        #         (0,t_wse2) -> touch -> (0,y_src_top). 꼭지각은 touch 점에 있다.
        "AirTop": ["src_edge_bot", touch, "src_edge_top"],
        # hBN: 아랫면 = Source 윗면 -> 하강선 (src_edge_top -> touch) -> 경사 WSe2 윗면 (touch -> slope_top_end)
        #      -> Drain 쪽 WSe2 윗면.  윗면 = 아랫면 + t_hbn, 그 위에 TG 선 (tg_l ~ tg_r).
        "hBN": (["src_tl", "src_edge_top", touch]
                + (["slope_top_end"] if has_touch else [])
                + ["film_r_top", "hbn_tr", "tg_r", "hbn_kink_drn"]
                + (["hbn_kink_touch"] if has_touch else [])
                + ["hbn_kink_src", "tg_l", "hbn_tl"]),
        # --- 금속 본체 (mesh 없음) ---
        "Source": ["src_bl", "src_edge_bot", "src_edge_top", "src_tl"],
        "Drain":  ["dr_bl", "ox_r", "drn_tr", "drn_corner"],
        "TG":     ["tg_l", "hbn_kink_src"] + (["hbn_kink_touch"] if has_touch else [])
                  + ["hbn_kink_drn", "tg_r", "tg_tr", "tg_tl"],
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
    # AirTop: 꼭짓점 (0, t_wse2), (l, film_top(l)), (0, y_src_top) -> 밑변이 x=0 위의 수직선(길이 t_source), 높이 l
    return {
        "SiO2": w * p.t_ox,
        "WSe2": w * p.t_wse2,
        "AirBot": 0.5 * p.l_ch * p.t_drain,
        "AirTop": 0.5 * p.t_source * l,
        "hBN": w * p.t_hbn,
        "Source": p.l_src_pad * p.t_source,
        "Drain": p.l_drn_pad * p.t_drain,
    }


def domain_area(points, p: Params):
    """도메인 전체 면적: 아랫변 y = -t_ox, 윗변 = h-BN 윗면 꺾은선 (hbn_tl -> ... -> hbn_tr)"""
    top = ["hbn_tl", "tg_l", "hbn_kink_src"] + (["hbn_kink_touch"] if "touch" in points else []) \
          + ["hbn_kink_drn", "tg_r", "hbn_tr"]
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
    top_names = ["hbn_tl", "hbn_kink_src"] + (["hbn_kink_touch"] if "touch" in points else []) \
                + ["hbn_kink_drn", "hbn_tr"]
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
    bot_names = ["src_tl", "src_edge_top"] + (["touch"] if "touch" in points else []) \
                + ["slope_top_end", "film_r_top"]
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
    theta = math.degrees(math.atan2(p.t_drain, p.l_ch))
    l = p.l_step
    y_src_top = p.t_wse2 + p.t_source
    desc = math.degrees(math.atan2(y_src_top - p.film_top(l), l))     # h-BN 하강선 각도 (아래쪽 +)
    print("\n[기하 요약]")
    print(f"  l_hbn_step = {l:.2f} nm  ({'bridge: 처짐 없음' if l >= p.l_ch else 'sag: 경사 WSe2에 닿음'})")
    print(f"  WSe2 경사각 = atan(t_drain/L) = {theta:.3f} deg,  경사 길이 {math.hypot(p.l_ch, p.t_drain):.2f} nm")
    print(f"  h-BN 하강선 각도 = {desc:.2f} deg (수평 아래로),  하강 구간의 h-BN 법선 두께 = "
          f"{p.t_hbn * math.cos(math.radians(desc)):.1f} nm  (수직 두께 {p.t_hbn} nm; 차이는 '수직 두께 일정' 근사의 오차)")
    print(f"  위 공기 쐐기(AirTop) 꼭지각 = {theta + desc:.2f} deg,  최대 높이(x=0) = {p.t_source} nm")
    # TG(h-BN 윗면)와 경사 WSe2 윗면 사이의 수직 거리: TG 꺾은선과 WSe2 윗면을 x에서 보간
    tgx = [points["hbn_kink_src"][0]] + ([points["hbn_kink_touch"][0]] if "touch" in points else []) + [points["hbn_kink_drn"][0]]
    tgy = [points["hbn_kink_src"][1]] + ([points["hbn_kink_touch"][1]] if "touch" in points else []) + [points["hbn_kink_drn"][1]]
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
