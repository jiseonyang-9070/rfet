# -*- coding: utf-8 -*-
"""
rfet_plotstyle.py
================================================================================
모든 그림이 같은 규칙을 쓰도록 하는 스타일 모듈. (물리와 무관한 표현 규칙만 들어 있다)

규칙
  - 색은 "무엇을 나타내는가"로 정한다.
      · 구조(config) 구분  : bridge = 파랑, sag45 = 주황  (고정, 순서 바꾸지 않음)
      · ε 변형 구분        : perp 실선, para 점선, tensor 파선  (색이 아니라 선 종류)
      · 게이트 전압 sweep  : 음(−) 파랑 ← 회색(0) → 양(+) 주황 의 발산(diverging) 색상
      · 재료               : SiO2 회색, WSe2 보라, h-BN 민트, 공기 흰색+빗금, 금속 금색
  - 선은 가늘게(1.6 pt), 격자는 연하게, 위/오른쪽 테두리는 없앤다.
  - 수치는 축 라벨에 단위를 적고, 중요한 점은 그림 안에 직접 적는다(direct label).
팔레트: colour-blind safe 한 8색 세트 중 앞 4개 (blue #2a78d6, orange #eb6834, aqua #1baf7a, yellow #eda100)
"""
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

# ---- 팔레트 ------------------------------------------------------------------
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#e34948"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

CONFIG_COLOR = {"bridge": BLUE, "sag45": ORANGE, "elastic": AQUA, "ramp140": VIOLET, "ramp70": RED, "conf70": MAGENTA, "conf140": YELLOW,
                "line140": BLUE, "curve140": ORANGE, "line70": AQUA, "curve70": RED}
CONFIG_LABEL = {"bridge": "bridge (h-BN taut, l = L)", "sag45": "sag45 (h-BN 45° descent)",
                "elastic": "elastic (ramp 0→L, h-BN touch 449)", "ramp140": "ramp140 (flat + 140 nm ramp, 27°)", "ramp70": "ramp70 (flat + 70 nm ramp, 45°)",
                "conf70": "conf70 (h-BN conformal, 70 nm ramp)", "conf140": "conf140 (h-BN conformal, 140 nm ramp)",
                "line140": "line140 (plate h-BN, kinked ramp 140)", "curve140": "curve140 (plate h-BN, S-curve ramp 140)",
                "line70": "line70 (plate h-BN, kinked ramp 70)", "curve70": "curve70 (plate h-BN, S-curve ramp 70)"}
VARIANT_LS = {"perp": "-", "para": ":", "tensor": "--"}
VARIANT_LABEL = {"perp": r"$\varepsilon_\perp$ scalar", "para": r"$\varepsilon_\parallel$ scalar", "tensor": r"$\varepsilon$ tensor"}

MATERIAL_FACE = {
    "SiO2": "#e9e9e6", "WSe2": "#b9a7e6", "hBN": "#c9ebdc", "AirBot": "#ffffff", "AirTop": "#ffffff",
    "Source": "#f1cf6a", "Drain": "#f1cf6a", "TG": "#8c8c88", "BG": "#8c8c88",
}
MATERIAL_LABEL = {"SiO2": "SiO₂", "WSe2": "WSe₂", "hBN": "h-BN", "AirBot": "air", "AirTop": "air",
                  "Source": "Source (Pd/Au)", "Drain": "Drain (Au/Ti)", "TG": "Top gate", "BG": "Back gate"}

# 발산 색상: 음의 전압 파랑, 0 회색, 양의 전압 주황
DIVERGING = LinearSegmentedColormap.from_list("rfet_div", [BLUE, "#9a9a97", ORANGE])


def voltage_color(v, vmax):
    """-vmax..+vmax 를 발산 색상에 매핑"""
    return DIVERGING(TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax)(v))


def apply():
    """rcParams 일괄 설정. 각 그림 스크립트 첫머리에서 한 번 호출."""
    matplotlib.use("Agg")
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
        "font.size": 9.5, "axes.titlesize": 10.5, "axes.labelsize": 9.5, "legend.fontsize": 8.5,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.8,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "lines.linewidth": 1.6, "legend.frameon": False, "legend.handlelength": 2.2,
        "axes.titleweight": "medium", "axes.titlelocation": "left",
    })


def shade_metal_regions(ax, L, x_left=-1e9, x_right=1e9, label=False):
    """박막이 금속에 덮인 구간(x<0: Source 아래, x>L: Drain 위)을 연한 금색으로 칠한다."""
    ax.axvspan(x_left, 0, color="#f1cf6a", alpha=0.22, lw=0, zorder=0)
    ax.axvspan(L, x_right, color="#f1cf6a", alpha=0.22, lw=0, zorder=0)
    ax.axvline(0, color=INK2, lw=0.7, ls=(0, (4, 3)), zorder=1)
    ax.axvline(L, color=INK2, lw=0.7, ls=(0, (4, 3)), zorder=1)
    if label:
        tr = ax.get_xaxis_transform()
        ax.text(0, 0.985, "source\njunction", ha="center", va="top", fontsize=7.5, color=INK2, transform=tr,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
        ax.text(L, 0.985, "drain\njunction", ha="center", va="top", fontsize=7.5, color=INK2, transform=tr,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))


def panel_label(ax, s):
    ax.text(-0.08, 1.06, s, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom", ha="left")


def add_colorbar(fig, ax, vmax, label):
    sm = plt.cm.ScalarMappable(cmap=DIVERGING, norm=TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax))
    cb = fig.colorbar(sm, ax=ax, pad=0.02, fraction=0.05)
    cb.set_label(label)
    cb.outline.set_visible(False)
    return cb


def structure_strip(ax, p, height=0.16):
    """x 프로파일 그림 위에 얇은 '구조 띠' 를 붙여 x 구간마다 박막 위/아래에 무엇이 있는지 보여준다.
    (왼쪽: Source 금속이 WSe₂ 위, 가운데: 채널 — 위아래 공기 쐐기와 h-BN/SiO₂, 오른쪽: Drain 금속이 WSe₂ 아래)"""
    from matplotlib.patches import Rectangle
    L = p.l_ch
    ins = ax.inset_axes([0, 1.02, 1, height], sharex=ax)
    ins.set_ylim(0, 1); ins.axis("off")
    x0, x1 = ax.get_xlim()
    film_y, film_h = 0.42, 0.16
    # 배경 유전체 (아래 SiO2, 위 h-BN)
    ins.add_patch(Rectangle((x0, 0.0), x1 - x0, film_y, fc=MATERIAL_FACE["SiO2"], ec="none"))
    ins.add_patch(Rectangle((x0, film_y + film_h), x1 - x0, 1 - film_y - film_h, fc=MATERIAL_FACE["hBN"], ec="none"))
    # 채널 구간의 공기 쐐기 (아래: SiO2 와 박막 사이, 위: 박막과 h-BN 사이)
    ins.add_patch(Rectangle((0, 0.0), L, film_y, fc="white", ec="none", hatch="////", lw=0))
    ins.add_patch(Rectangle((0, film_y + film_h), L, 1 - film_y - film_h, fc="white", ec="none", hatch="////", lw=0))
    # 박막
    ins.add_patch(Rectangle((x0, film_y), x1 - x0, film_h, fc=MATERIAL_FACE["WSe2"], ec=INK2, lw=0.5))
    # 금속: Source 는 박막 위 (x<0), Drain 은 박막 아래 (x>L)
    ins.add_patch(Rectangle((x0, film_y + film_h), -x0, 1 - film_y - film_h, fc=MATERIAL_FACE["Source"], ec=INK2, lw=0.5))
    ins.add_patch(Rectangle((L, 0.0), x1 - L, film_y, fc=MATERIAL_FACE["Drain"], ec=INK2, lw=0.5))
    kw = dict(fontsize=7, ha="center", va="center", color=INK)
    kwh = dict(kw, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))   # 빗금 위 글자는 흰 바탕
    ins.text(x0 / 2, film_y + film_h + 0.5 * (1 - film_y - film_h), "Source metal", **kw)
    ins.text(L + (x1 - L) / 2, film_y / 2, "Drain metal", **kw)
    ins.text(L / 2, film_y + film_h + 0.5 * (1 - film_y - film_h), "air gap → h-BN → TG", **kwh)
    ins.text(L / 2, film_y / 2, "air gap → SiO₂ → BG", **kwh)
    ins.text(x0 / 2, film_y / 2, "SiO₂", **kw)
    ins.text(L + (x1 - L) / 2, film_y + film_h + 0.5 * (1 - film_y - film_h), "h-BN · TG", **kw)
    ins.text(x1, film_y + film_h / 2, " WSe₂", fontsize=7, ha="left", va="center", color=INK, clip_on=False)
    return ins
