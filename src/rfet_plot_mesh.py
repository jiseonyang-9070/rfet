# -*- coding: utf-8 -*-
"""
rfet_plot_mesh.py
================================================================================
실제 gmsh mesh(.msh, nm 단위)를 읽어 "구조 + 격자" 그림을 그린다.
  - 영역(SiO2 / WSe2 / h-BN / 공기)은 재료 색으로 채우고 삼각형 변을 가늘게 그린다.
  - 금속 접점(Source, Drain, TG, BG)은 굵은 선 + 금속 블록(반투명)으로 표시한다.
    (금속 내부는 mesh 가 없다 — 등전위라서 경계선에 전압만 건다. 블록은 "여기에 금속이 있다"는 표시다.)
  - 패널: 전체 / source junction 확대 / drain junction 확대 / 채널 중앙(쐐기) 확대
실행:  python rfet_plot_mesh.py rfet_bridge_nm.msh [rfet_sag45_nm.msh ...]   ->  fig_mesh_<config>.png
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Polygon as MplPolygon

import rfet_geometry as geo
import rfet_mesh_tools as tools
import rfet_plotstyle as st

REGION_FACE = {"SiO2": "#cfe0f3", "WSe2": "#1baf7a", "hBN": "#d9cff2", "AirBot": "#ffffff", "AirTop": "#ffffff"}
REGION_EDGE = {"SiO2": "#5f7fa6", "WSe2": "#0b6b48", "hBN": "#7a66b8", "AirBot": "#9a9a9a", "AirTop": "#9a9a9a"}
CONTACT_COLOR = {"Source": "#e0a400", "Drain": "#e0a400", "TG": "#d1283a", "BG": "#444444"}
METAL_FACE = {"Source": "#f1cf6a", "Drain": "#f1cf6a", "TG": "#f2a3ab", "BG": "#bdbdbd"}


def draw(ax, m, pts, polys, p, lw_tri=0.25, metal_alpha=0.55):
    xy, tri, phys = m["xy"], m["tri"], m["tri_phys"]
    names = m["names"]
    # 영역별 삼각형
    for code in np.unique(phys):
        reg = names[(2, int(code))][2:]                       # 'R_SiO2' -> 'SiO2'
        sel = tri[phys == code]
        pc = PolyCollection(xy[sel], facecolors=REGION_FACE[reg], edgecolors=REGION_EDGE[reg],
                            linewidths=lw_tri, alpha=1.0, zorder=1)
        ax.add_collection(pc)
    # 금속 블록 (기하 다각형, 반투명) + 접점 선
    for metal in geo.METALS:
        poly = geo.polygon_xy(pts, polys[metal])
        ax.add_patch(MplPolygon(poly, closed=True, facecolor=METAL_FACE[metal], edgecolor="none", alpha=metal_alpha, zorder=2))
    for code in np.unique(m["line_phys"]):
        nm = names[(1, int(code))]
        if not nm.startswith("C_"):
            continue
        metal = nm.split("_")[1]
        seg = xy[m["line"][m["line_phys"] == code]]
        ax.add_collection(LineCollection(seg, colors=CONTACT_COLOR[metal], linewidths=2.6, zorder=4))
    ax.set_aspect("equal")
    ax.grid(False)


def label_regions(ax, p, pts):
    L = p.l_ch
    kw = dict(fontsize=8.5, ha="center", va="center", color=st.INK, zorder=6,
              bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.text(-0.5 * p.l_src_pad, p.t_wse2 + 0.5 * p.t_source, "Source (Pd/Au)", **kw)
    ax.text(L + 0.5 * p.l_drn_pad, 0.5 * p.t_drain, "Drain (Au/Ti)", **kw)
    ax.text(0.5 * L, pts["hbn_kink_drn"][1] + 12, "Top gate", **kw)
    ax.text(0.5 * L, -0.5 * p.t_ox, "SiO₂ 300 nm", **kw)
    ax.text(0.5 * L, -p.t_ox - 14, "Back gate", **kw)
    ax.text(0.5 * L, 0.5 * p.film_top(0.5 * L) * 0.5, "air", fontsize=8, ha="center", va="center", color=st.INK2, zorder=6)
    ax.text(L + 0.5 * p.l_drn_pad, p.t_drain + p.t_wse2 + 0.5 * p.t_hbn, "h-BN 30 nm", **kw)
    ax.annotate("WSe₂ 9.1 nm", xy=(-0.5 * p.l_src_pad, 0.5 * p.t_wse2), xytext=(-0.5 * p.l_src_pad, -60), fontsize=8.5, ha="center", va="top", color=st.INK, zorder=6,
                arrowprops=dict(arrowstyle="-", color=st.INK2, lw=0.8), bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))


def main(paths):
    st.apply()
    for path in paths:
        cfg = os.path.basename(path).replace("rfet_", "").replace("_nm.msh", "").split("_n")[0]
        p = geo.CONFIGS[cfg]
        pts, polys = geo.build_points(p), geo.build_polygons(p)
        m = tools.read_msh2(path)
        L = p.l_ch
        fig = plt.figure(figsize=(13.5, 7.0))
        gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.0], hspace=0.28, wspace=0.22, top=0.91, bottom=0.08)
        ax0 = fig.add_subplot(gs[0, :])
        draw(ax0, m, pts, polys, p, lw_tri=0.15)
        label_regions(ax0, p, pts)
        ax0.set_xlim(-p.l_src_pad, L + p.l_drn_pad); ax0.set_ylim(-p.t_ox - 30, pts["hbn_kink_drn"][1] + 40)
        ax0.set_xlabel("x (nm)"); ax0.set_ylabel("y (nm)")
        ax0.set_title(f"a  Full domain — config '{cfg}'   ·   {len(m['xy']):,} nodes, {len(m['tri']):,} triangles   "
                      f"(gold: Source/Drain, red: Top gate, dark: Back gate)")
        zooms = [
            ("b  Source junction (x = 0)", (-80, 120), (-25, pts["hbn_kink_src"][1] + 15)),
            ("c  Channel mid / air wedges", (0.5 * L - 60, 0.5 * L + 60), (-15, p.film_top(0.5 * L) + 45)),
            ("d  Drain junction (x = L)", (L - 120, L + 80), (-25, pts["hbn_kink_drn"][1] + 15)),
        ]
        for k, (ttl, xl, yl) in enumerate(zooms):
            ax = fig.add_subplot(gs[1, k])
            draw(ax, m, pts, polys, p, lw_tri=0.45)
            ax.set_xlim(*xl); ax.set_ylim(*yl)
            ax.set_title(ttl); ax.set_xlabel("x (nm)")
            if k == 0:
                ax.set_ylabel("y (nm)")
        # junction 점
        for ax in fig.axes:
            ax.plot([0, L], [p.t_wse2, p.t_drain], "o", color=st.RED, ms=5, mec="white", mew=0.8, zorder=7)
        fig.suptitle("WSe₂ RFET — geometry and finite-volume mesh actually used (gmsh, nm units)", x=0.01, y=0.985, ha="left", fontsize=11, color=st.INK2)
        out = f"fig_mesh_{cfg}.png"
        fig.savefig(out, dpi=200)
        plt.close(fig)
        print("저장:", out)


if __name__ == "__main__":
    main(sys.argv[1:] or ["rfet_bridge_nm.msh"])
