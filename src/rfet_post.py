# -*- coding: utf-8 -*-
"""
rfet_post.py
================================================================================
STEP 3-D : 후처리. rfet_fem_reference.py 또는 rfet_poisson_devsim.py 가 저장한 .npz 를 읽어
          "raw" 전위 응답을 그림과 표로 보여준다. 지표(crosstalk 등)는 정의하지 않는다.

.npz 형식 (두 solver 공통)
  xy (N,2) nm,  tri (M,3),  tri_region (M,) 문자열,  psi_<금속> (N,) : 그 금속에 1 V, 나머지 0 V 일 때의 ψ [V]

무엇을 보는가
  1) WSe2 박막 중앙선(두께의 절반 높이)을 따라 ψ_TG(x), ψ_BG(x) — "게이트 1 V 당 채널 전위 변화"
     논문 메커니즘이 맞다면: ψ_BG 는 source junction 쪽(x≈0)에서 크고 drain 쪽(x≈L)에서 작아야 하고,
     ψ_TG 는 그 반대여야 한다.
  2) 2D 전위 지도 (채널 구간 확대)
  3) junction 근처 몇 지점의 값 표. 모서리 점 자체는 격자 의존이므로 10 nm 이상 떨어진 점을 읽는다
     (STEP 2 에서 정한 규칙; 이 거리 선택은 [수치해석 설정]이며 10/25/50 nm 세 값을 모두 보여준다).

실행:  python rfet_post.py rfet_fem_bridge_perp.npz [rfet_fem_sag45_perp.npz ...]
"""
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

import rfet_geometry as geo

# [수치해석 설정] junction 에서 떨어진 거리로 읽는 위치 [nm]
PROBE_OFFSETS_NM = (10.0, 25.0, 50.0)


def film_mid_y(p: geo.Params, x):
    """WSe2 박막 중앙선 높이 y(x) = 아랫면(x) + t/2"""
    return p.film_bottom(x) + 0.5 * p.t_wse2


def draw_structure(ax, pts, polys, p):
    """전위 지도 위에 구조를 그린다: 금속은 회색 채움 + 이름, 유전체/공기/채널 경계는 흰 윤곽선."""
    import rfet_plotstyle as st
    from matplotlib.patches import Polygon as MplPolygon
    for name in geo.REGIONS:
        ax.add_patch(MplPolygon(geo.polygon_xy(pts, polys[name]), closed=True, fill=False, edgecolor="white", linewidth=0.8))
    for name in geo.METALS:
        ax.add_patch(MplPolygon(geo.polygon_xy(pts, polys[name]), closed=True, facecolor="#d8d8d4", edgecolor="#555", linewidth=0.6))
    L = p.l_ch
    y_src_top = p.t_wse2 + p.t_source
    txt = dict(fontsize=8, ha="center", va="center", color=st.INK)
    ax.text(-90, 0.5 * (p.t_wse2 + y_src_top), "Source", **txt)
    ax.text(L + 90, 0.5 * p.t_drain, "Drain", **txt)
    ax.text(0.5 * L, pts["hbn_kink_drn"][1] + 11, "Top gate", **txt)
    ax.text(0.5 * L, -62, "SiO₂", color="white", fontsize=8, ha="center")
    ax.text(0.5 * L, -108, "back gate at y = −300 nm", color="white", fontsize=7.5, ha="center")
    ax.text(L + 90, pts["hbn_kink_drn"][1] - 13, "h-BN", color="white", fontsize=8, ha="center")
    ax.text(-90, pts["hbn_tl"][1] - 13, "h-BN", color="white", fontsize=8, ha="center")
    ax.text(0.30 * L, 0.5 * p.film_top(0.30 * L) * 0.45, "air", color="white", fontsize=7.5, ha="center")
    ax.text(0.25 * L, 0.5 * (y_src_top + p.film_top(0.25 * L)) + 2, "air", color="white", fontsize=7.5, ha="center")
    ax.annotate("", xy=(L, p.film_top(L) + 14), xytext=(0, p.film_top(0) + 14), arrowprops=dict(arrowstyle="<->", color="white", lw=0.9))
    ax.text(0.5 * L, 0.5 * (p.film_top(0) + p.film_top(L)) + 22, "WSe₂ channel (9.1 nm)", color="white", fontsize=8, ha="center")
    ax.plot([0, L], [p.t_wse2, p.t_drain], "o", color=st.RED, ms=4.5, mec="white", mew=0.7, zorder=6)
    ax.text(-90, -18, "WSe₂ under Source", color="white", fontsize=7.5, ha="center")
    ax.text(L + 90, p.t_drain + p.t_wse2 + 4, "WSe₂ on Drain", color="white", fontsize=7.5, ha="center", va="bottom")


def load(path):
    d = np.load(path, allow_pickle=False)
    out = {k: d[k] for k in d.files}
    out["config"] = str(out["config"])
    out["variant"] = str(out["variant"])
    out["solver"] = str(out["solver"])
    return out


def film_profile(d, metal, xs):
    """박막 중앙선을 따라 psi_<metal> 을 보간. WSe2 요소만으로 삼각분할을 만들어 다른 영역의 값이 섞이지 않게 한다."""
    p = geo.CONFIGS[d["config"]]
    sel = d["tri_region"] == "WSe2"
    T = mtri.Triangulation(d["xy"][:, 0], d["xy"][:, 1], d["tri"][sel])
    f = mtri.LinearTriInterpolator(T, d[f"psi_{metal}"])
    return np.array(f(xs, film_mid_y(p, xs)))


def main(paths):
    import os
    missing = [pth for pth in paths if not os.path.exists(pth)]
    for pth in missing:
        print(f"[건너뜀] 파일 없음: {pth}")
    paths = [pth for pth in paths if os.path.exists(pth)]
    if not paths:
        raise SystemExit("읽을 .npz 가 하나도 없습니다")
    data = [load(pth) for pth in paths]
    p0 = geo.CONFIGS[data[0]["config"]]
    xs = np.linspace(-200.0, p0.l_ch + 200.0, 801)

    # ---- 그림 1: 박막 중앙선 전위 응답 (config = 색, ε 변형 = 선 종류, solver = 마커) ----
    import rfet_plotstyle as st
    st.apply()
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), sharex=True)
    for d in data:
        color = st.CONFIG_COLOR.get(d["config"], st.INK2)
        ls = st.VARIANT_LS.get(d["variant"], "-")
        label = f"{d['config']} · {st.VARIANT_LABEL.get(d['variant'], d['variant'])}"
        for ax, metal in zip(axes, ("TG", "BG")):
            prof = film_profile(d, metal, xs)
            if d["solver"] == "devsim":            # DEVSIM 은 점으로 겹쳐 그려 FEM 과의 일치를 보이게
                ax.plot(xs[::40], prof[::40], "o", ms=4, mfc="white", mec=color, mew=1.1, label=label + " (DEVSIM)", zorder=4)
            else:
                ax.plot(xs, prof, ls=ls, color=color, label=label + " (FEM)", zorder=3)
    for ax, metal, ttl in zip(axes, ("TG", "BG"), ("a  Top-gate response", "b  Back-gate response")):
        st.shade_metal_regions(ax, p0.l_ch)
        ax.set_title(ttl, pad=34)
        ax.set_xlabel("x (nm)   (0 = source junction, L = drain junction)")
        ax.set_ylabel(f"∂ψ/∂V$_{{{metal}}}$ at film mid-plane (V/V)")
        ax.set_xlim(xs[0], xs[-1])
        ax.set_ylim(bottom=0)
        st.structure_strip(ax, p0)
    axes[0].legend(loc="upper left", fontsize=7.5)
    fig.suptitle("Linear electrostatics (ρ = 0): channel potential response per volt on each gate", x=0.01, y=1.0, ha="left", fontsize=10, color=st.INK2)
    fig.tight_layout()
    fig.savefig("rfet_post_profiles.png")
    plt.close(fig)

    # ---- 그림 2: 2D 전위 지도 + 등전위선 + 구조 윤곽 (첫 번째 데이터) ----
    d = data[0]
    p = geo.CONFIGS[d["config"]]
    pts = geo.build_points(p)
    polys = geo.build_polygons(p)
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.2))
    T = mtri.Triangulation(d["xy"][:, 0], d["xy"][:, 1], d["tri"])
    for ax, metal, ttl in zip(axes, ("TG", "BG"), ("a  ∂ψ/∂V$_{TG}$", "b  ∂ψ/∂V$_{BG}$")):
        z = d[f"psi_{metal}"]
        im = ax.tripcolor(T, z, shading="gouraud", cmap="magma", vmin=0, vmax=1, rasterized=True)
        ax.tricontour(T, z, levels=np.arange(0.1, 1.0, 0.1), colors="white", linewidths=0.5, alpha=0.8)
        draw_structure(ax, pts, polys, p)
        ax.set_xlim(-150, p.l_ch + 150)
        ax.set_ylim(-120, 135)
        ax.set_aspect("equal")
        ax.grid(False)
        ax.set_xlabel("x (nm)"); ax.set_ylabel("y (nm)")
        ax.set_title(f"{ttl}   —   {d['config']}, {st.VARIANT_LABEL.get(d['variant'], d['variant'])}, {d['solver']}")
        cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.04)
        cb.set_label(f"∂ψ/∂V$_{{{metal}}}$ (V/V)"); cb.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig("rfet_post_maps.png")
    plt.close(fig)

    # ---- 표: junction 근처 값 ----
    print("\n[박막 중앙선 전위 응답, V per V]   (x 는 junction 에서의 거리; S쪽 = x, D쪽 = L - x)")
    hdr = "  data                      gate | " + " ".join(f"S+{o:>3.0f}" for o in PROBE_OFFSETS_NM) + " | " \
          + " ".join(f"D-{o:>3.0f}" for o in PROBE_OFFSETS_NM) + " | mid"
    print(hdr)
    for d in data:
        p = geo.CONFIGS[d["config"]]
        for metal in ("TG", "BG"):
            xs_s = np.array(PROBE_OFFSETS_NM)
            xs_d = p.l_ch - np.array(PROBE_OFFSETS_NM)
            vs = film_profile(d, metal, xs_s)
            vd = film_profile(d, metal, xs_d)
            vm = film_profile(d, metal, np.array([0.5 * p.l_ch]))[0]
            print(f"  {d['config']+'/'+d['variant']+' ('+d['solver']+')':26s} {metal:4s} | "
                  + " ".join(f"{v:5.3f}" for v in vs) + " | " + " ".join(f"{v:5.3f}" for v in vd) + f" | {vm:5.3f}")
    print("\n그림 저장: rfet_post_profiles.png, rfet_post_maps.png")


if __name__ == "__main__":
    main(sys.argv[1:] or ["rfet_fem_bridge_perp.npz"])
