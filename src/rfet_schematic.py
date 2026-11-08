# -*- coding: utf-8 -*-
"""
rfet_schematic.py
================================================================================
발표/논문용 소자 "개략도"(schematic). 정확한 치수의 단면도(rfet_geometry.py 그림)와 달리
두께를 과장해 구조가 한눈에 읽히게 그린다.  ** 비례도가 아님 (not to scale) **
(v2: 입체 옆면/윗면 없이 정면(2D 단면)만, 모든 층의 좌우 끝을 도메인 경계에 맞춤 — 모델 geometry 와 동일)

그리는 요소 (우리 모델의 적층 순서 그대로)
  Si(BG) / SiO2 / Drain(아래 접촉) / WSe2(원자 층으로 표현, Source 아래 평평 → Drain 위로 경사) /
  Source(위 접촉) / h-BN / Top gate.   l_hbn_step 에 따라 h-BN 아랫면이 bridge(팽팽) 또는 sag(처짐)으로 바뀐다.

실행:  python rfet_schematic.py            -> fig_schematic_bridge.png, fig_schematic_sag45.png
"""
import math

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
import matplotlib.patheffects as pe

import rfet_geometry as geo

# ---- 색 (재료 관례색) -----------------------------------------------------------
C = {
    "Si":    ("#a9a9a9", "#8d8d8d", "#6e6e6e"),
    "SiO2":  ("#b47fd0", "#a06ac0", "#7f4f9c"),
    "metal": ("#f2cf63", "#e0b63f", "#b8901f"),
    "hBN":   ("#d9edcb", "#c6e2b3", "#9fc48a"),
    "W":     "#3b6fd6",
    "Se":    "#f2c94c",
}
EDGE = "#3a3a3a"


def box2d(ax, x0, y0, w, h, colors, z=1):
    """정면 사각형 하나. colors[0] = 면 색 (옆면·윗면은 그리지 않는다: 2D 단면 모델이므로)"""
    ax.add_patch(Polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], closed=True,
                         fc=colors[0], ec=EDGE, lw=0.9, zorder=z))


def label(ax, x, y, text, z=10, fs=11, color="#1a1a1a", weight="bold"):
    halo = "#333333" if color == "white" else "white"          # 흰 글자는 어두운 테두리, 검은 글자는 흰 테두리
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, fontweight=weight, color=color, zorder=z,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=halo, alpha=0.85)])


def atoms_along(ax, xs, ys, z=6, spacing=9.0, r=3.2):
    """경로 (xs, ys) 를 따라 W(파랑)-Se(노랑) 원자를 번갈아 두 줄로 그려 WSe2 층을 표현한다."""
    seg = np.hypot(np.diff(xs), np.diff(ys))
    s = np.concatenate([[0], np.cumsum(seg)])
    n = int(s[-1] // spacing)
    for k in range(n + 1):
        t = k * spacing
        x = np.interp(t, s, xs); y = np.interp(t, s, ys)
        i = min(np.searchsorted(s, t), len(xs) - 1)
        tx, ty = xs[i] - xs[i - 1], ys[i] - ys[i - 1]
        nrm = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / nrm, tx / nrm                       # 경로의 법선
        ax.add_patch(Circle((x + nx * 3.5, y + ny * 3.5), r, fc=C["Se"], ec=EDGE, lw=0.5, zorder=z))
        ax.add_patch(Circle((x - nx * 3.5, y - ny * 3.5), r, fc=C["Se"], ec=EDGE, lw=0.5, zorder=z))
        ax.add_patch(Circle((x, y), r * 1.15, fc=C["W"], ec=EDGE, lw=0.5, zorder=z + 0.1))


def draw(config, outfile):
    p = geo.CONFIGS[config]
    # 개략도 치수 (과장): 가로는 실제 비율에 가깝게, 세로는 보이도록 키움
    Ls, L, Ld = 230.0, 260.0, 230.0
    x_s0, x_s1 = 0.0, Ls                   # Source 패드
    x_d0, x_d1 = Ls + L, Ls + L + Ld       # Drain 패드
    h_si, h_ox, h_d, h_s, h_bn, h_tg = 40.0, 70.0, 55.0, 55.0, 40.0, 38.0
    t_film = 12.0                          # WSe2 층 두께(그림)
    y_si, y_ox = 0.0, h_si
    y0 = h_si + h_ox                       # SiO2 윗면
    y_film_s = y0 + t_film                 # Source 쪽 WSe2 윗면
    y_src_top = y_film_s + h_s
    y_film_d = y0 + h_d + t_film           # Drain 쪽 WSe2 윗면
    l_frac = p.l_step / p.l_ch             # h-BN 전이 길이 비율 (bridge 1.0, sag45 ≈ 0.1)

    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.set_aspect("equal"); ax.axis("off")

    X0, X1 = x_s0, x_d1                    # 도메인 좌우 끝: 모든 층(Si, SiO2, WSe2, h-BN)과 S/D 패드가 여기서 끝난다
    # 1) Si, SiO2
    box2d(ax, X0, y_si, X1 - X0, h_si, C["Si"], z=1)
    box2d(ax, X0, y_ox, X1 - X0, h_ox, C["SiO2"], z=2)
    # 2) Drain (SiO2 위, 아래 접촉) — 오른쪽 끝까지
    box2d(ax, x_d0, y0, X1 - x_d0, h_d, C["metal"], z=3)
    # 3) WSe2: Source 아래 평평 -> 경사 -> Drain 위 평평 (원자 층), 왼쪽 끝 ~ 오른쪽 끝
    xs = np.array([X0, Ls, x_d0, X1])
    ys = np.array([y0 + t_film / 2, y0 + t_film / 2, y0 + h_d + t_film / 2, y0 + h_d + t_film / 2])
    xx = np.linspace(xs[0], xs[-1], 400); yy = np.interp(xx, xs, ys)
    atoms_along(ax, xx, yy, z=6)
    # 4) Source (WSe2 위, 위 접촉) — 왼쪽 끝부터 x = Ls (source junction) 까지
    box2d(ax, X0, y_film_s, Ls - X0, h_s, C["metal"], z=7)
    # 5) h-BN: 아랫면 = Source 윗면 -> (전이) -> 경사 WSe2 윗면 -> Drain 쪽 WSe2 윗면, 윗면 = 아랫면 + h_bn
    x_touch = Ls + l_frac * L
    y_touch = np.interp(x_touch, xs, ys) + t_film / 2 + 4
    bottom = [(X0, y_src_top), (Ls, y_src_top), (x_touch, y_touch)]
    if l_frac < 1.0:
        bottom.append((x_d0, y_film_d + 4))
    bottom.append((X1, y_film_d + 4))
    top = [(x, y + h_bn) for (x, y) in bottom]
    ax.add_patch(Polygon(bottom + top[::-1], closed=True, fc=C["hBN"][0], ec=EDGE, lw=0.9, zorder=8))
    # 6) Top gate: h-BN 윗면을 따라 (Source 일부 ~ Drain 일부)
    x_tg0, x_tg1 = Ls - 70, x_d0 + 70
    tg_bottom = [(x, np.interp(x, [q[0] for q in top], [q[1] for q in top])) for x in
                 sorted({x_tg0, x_tg1} | {q[0] for q in top if x_tg0 < q[0] < x_tg1})]
    tg_top = [(x, y + h_tg) for (x, y) in tg_bottom]
    ax.add_patch(Polygon(tg_bottom + tg_top[::-1], closed=True, fc=C["metal"][0], ec=EDGE, lw=0.9, zorder=9))

    # 7) 라벨
    label(ax, (X0 + X1) / 2, y_si + h_si / 2, "Si  (back gate, BG)", color="white")
    label(ax, Ls * 0.55, y_ox + h_ox / 2, "SiO₂  300 nm", color="white")
    label(ax, (X0 + Ls) / 2, y_film_s + h_s / 2, "Source (S)\nPd/Au")
    label(ax, (x_d0 + X1) / 2, y0 + h_d / 2, "Drain (D)\nAu/Ti")
    label(ax, (x_tg0 + x_tg1) / 2, np.mean([q[1] for q in tg_top]) - h_tg / 2 + 1, "Top gate (TG)")
    label(ax, X1 - 70, y_film_d + 4 + h_bn / 2, "h-BN  30 nm", fs=9.5, weight="semibold")
    ax.annotate("WSe₂  9.1 nm", xy=(Ls + 0.55 * L, np.interp(Ls + 0.55 * L, xs, ys) + 7), xytext=(Ls + 0.55 * L + 20, y_src_top + h_bn + h_tg + 55),
                fontsize=10.5, fontweight="bold", ha="left", arrowprops=dict(arrowstyle="-", color=EDGE, lw=0.9), zorder=12)
    ax.annotate("", xy=(x_d0, y0 - 40), xytext=(Ls, y0 - 40), arrowprops=dict(arrowstyle="<->", color="white", lw=1.1), zorder=12)
    label(ax, Ls + L / 2, y0 - 56, "L ≈ 500 nm", fs=10, weight="semibold", color="white")
    # 접합 표시
    for (x, y, t) in ((Ls, y_film_s, "source junction"), (x_d0, y0 + h_d, "drain junction")):
        ax.add_patch(Circle((x, y), 4.5, fc="#e34948", ec="white", lw=1.0, zorder=13))
    halo = [pe.withStroke(linewidth=2.5, foreground="white", alpha=0.9)]
    ax.annotate("source junction", xy=(Ls, y_film_s), xytext=(Ls + 28, y0 - 8), fontsize=8.5, color="#b3302f", fontweight="semibold",
                ha="left", va="top", zorder=13, path_effects=halo, arrowprops=dict(arrowstyle="-", color="#b3302f", lw=0.8))
    ax.annotate("drain junction", xy=(x_d0, y0 + h_d), xytext=(x_d0 - 28, y0 + h_d - 22), fontsize=8.5, color="#b3302f", fontweight="semibold",
                ha="right", va="top", zorder=13, path_effects=halo, arrowprops=dict(arrowstyle="-", color="#b3302f", lw=0.8))

    title = {"bridge": "h-BN taut over the step (bridge)", "sag45": "h-BN sagging onto the channel (sag45)",
             "elastic": "h-BN step length from elastic estimate"}.get(config, config)
    ax.set_title(f"WSe₂ reconfigurable FET — model cross-section schematic   ·   {title}", loc="left", fontsize=11, pad=10)
    ax.text(X1, y_si - 12, "schematic, not to scale (vertical thicknesses exaggerated)", ha="right", va="top", fontsize=8, color="#666", style="italic")
    ax.set_xlim(X0 - 12, X1 + 12)
    ax.set_ylim(y_si - 45, y_src_top + h_bn + h_tg + 90)
    fig.savefig(outfile, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return outfile


if __name__ == "__main__":
    for cfg in ("bridge", "sag45"):
        print("저장:", draw(cfg, f"fig_schematic_{cfg}.png"))
