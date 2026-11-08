# -*- coding: utf-8 -*-
"""
rfet_size_map.py
================================================================================
STEP 2-B (시각화) : rfet_mesh_gmsh.py 의 mesh 크기 규칙을 gmsh 없이 그림으로 확인한다.

rfet_mesh_gmsh.py 섹션 4의 네 규칙(박막/접촉 모서리/쐐기 끝/TG 끝)을 numpy로 똑같이 계산해서
"위치별 목표 요소 크기"를 색으로 그린다. gmsh가 실제로 만드는 mesh는 이 목표 크기를
Frontal-Delaunay 알고리즘으로 근사한 것이다.  (numpy, matplotlib만 필요)

실행:  python rfet_size_map.py [config...]   -> rfet_size_map_<config>.png
"""
import math

import numpy as np

import rfet_geometry as geo
import rfet_mesh_gmsh as M


def seg_distance(px, py, a, b):
    """점들 (px, py) 에서 선분 a-b 까지의 거리"""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


def threshold(dist, size_min, dist_min, slope):
    """rfet_mesh_gmsh.threshold() 와 같은 규칙: 거리 dist_min 까지는 size_min, 그 뒤 slope 로 증가"""
    return np.minimum(M.S_MAX, size_min + slope * np.maximum(0.0, dist - dist_min))


def size_map(points, polygons, p: geo.Params, X, Y):
    s_film = p.t_wse2 / M.N_LAYERS_FILM
    s_edge = s_film / M.EDGE_REFINE
    theta = math.atan2(p.t_drain, p.l_ch)
    desc = math.atan2(p.t_wse2 + p.t_source - p.film_top(p.l_step), p.l_step)

    # 규칙 1: WSe2 경계선까지의 거리
    d_film = np.full(X.shape, np.inf)
    for a, b in geo.edges_of(polygons["WSe2"]):
        d_film = np.minimum(d_film, seg_distance(X, Y, points[a], points[b]))
    s1 = threshold(d_film, s_film, p.t_wse2 / 2.0, M.GROWTH)

    # 규칙 2: 금속 모서리 네 점
    d_edge = np.full(X.shape, np.inf)
    for name in ("src_edge_bot", "drn_corner", "src_edge_top", "dr_bl"):
        d_edge = np.minimum(d_edge, np.hypot(X - points[name][0], Y - points[name][1]))
    s2 = threshold(d_edge, s_edge, 0.0, M.GROWTH)

    # 규칙 3: 쐐기 끝 2곳 (아래 AirBot: apex, 위 AirTop: touch 또는 slope_top_end)
    top_apex = "touch" if "touch" in points else "slope_top_end"
    s3a = threshold(np.hypot(X - points["apex"][0], Y - points["apex"][1]), s_edge, 0.0, math.tan(theta) / M.N_ACROSS_WEDGE)
    s3b = threshold(np.hypot(X - points[top_apex][0], Y - points[top_apex][1]), s_edge, 0.0,
                    math.tan(theta + desc) / M.N_ACROSS_WEDGE)

    # 규칙 4: TG 양 끝 + 꺾임점
    d_tg = np.full(X.shape, np.inf)
    for name in ["tg_l", "tg_r", "hbn_kink_src", "hbn_kink_drn"] + (["hbn_kink_touch"] if "hbn_kink_touch" in points else []):
        d_tg = np.minimum(d_tg, np.hypot(X - points[name][0], Y - points[name][1]))
    s4 = threshold(d_tg, M.S_TG_EDGE, 0.0, M.GROWTH)

    return np.minimum.reduce([s1, s2, s3a, s3b, s4])


def main(config):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from matplotlib.patches import Polygon as MplPolygon

    outfile = f"rfet_size_map_{config}.png"
    p = geo.CONFIGS[config]
    pts = geo.build_points(p)
    polys = geo.build_polygons(p)
    x0, x1 = pts["bg_l"][0], pts["bg_r"][0]
    y0, y1 = pts["bg_l"][1], max(pts["hbn_tl"][1], pts["hbn_tr"][1])

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [1, 1.1]})
    windows = [((x0, x1), (y0, y1), 1200, 420, "target element size over the full domain [nm]"),
               ((-60, 560), (-40, 125), 1200, 500, "zoom: channel region")]
    for ax, (xl, yl, nx, ny, title) in zip(axes, windows):
        X, Y = np.meshgrid(np.linspace(*xl, nx), np.linspace(*yl, ny))
        S = size_map(pts, polys, p, X, Y)
        im = ax.pcolormesh(X, Y, S, norm=LogNorm(vmin=0.5, vmax=M.S_MAX), cmap="viridis", shading="auto")
        for name in geo.REGIONS + geo.METALS:
            ax.add_patch(MplPolygon(geo.polygon_xy(pts, polys[name]), closed=True,
                                    fill=(name in geo.METALS), facecolor="lightgray", alpha=0.9,
                                    edgecolor="w", linewidth=0.7))
        ax.set_xlim(*xl)
        ax.set_ylim(*yl)
        ax.set_aspect("equal" if ax is axes[1] else "auto")
        ax.set_title(title)
        ax.set_xlabel("x [nm]")
        ax.set_ylabel("y [nm]")
        fig.colorbar(im, ax=ax, label="target size [nm] (log)")
    fig.suptitle(f"mesh size rules of rfet_mesh_gmsh.py - config '{config}'  (gray = metal, not meshed)", fontsize=10)
    fig.tight_layout()
    fig.savefig(outfile, dpi=130)
    print("저장:", outfile)
    print(f"s_film = {p.t_wse2 / M.N_LAYERS_FILM:.3f} nm, s_edge = {p.t_wse2 / M.N_LAYERS_FILM / M.EDGE_REFINE:.3f} nm,"
          f" S_MAX = {M.S_MAX} nm, 경사각 {math.degrees(math.atan2(p.t_drain, p.l_ch)):.2f} deg")


if __name__ == "__main__":
    import sys
    for name in (sys.argv[1:] or list(geo.CONFIGS)):
        main(name)
