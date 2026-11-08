# -*- coding: utf-8 -*-
"""
rfet_post_semi.py
================================================================================
STEP 4-C : 반도체 정전기 결과(rfet_fem_semi.py / rfet_poisson_semi_devsim.py 의 .npz) 후처리.
  1) WSe2 박막 중앙선을 따라 밴드 다이어그램 E_c(x), E_v(x)  (E_F = 0 기준)  — 게이트 전압별
  2) source / drain junction 근처 확대: 금속에서 채널 쪽으로 E_c 가 얼마나 빨리 내려오는가(장벽 "모양")
  3) 캐리어 밀도 n(x), p(x) 박막 평균 — 어느 게이트가 어느 쪽을 n/p 로 만드는가 (raw)
  지표(장벽 폭 등)는 정의하지 않는다. 정의가 필요해지면 WKB 등 물리 근거와 함께 따로 논의한다.

실행:  python rfet_post_semi.py rfet_semi_bridge_perp_lit.npz [다른 npz ...]
"""
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

import rfet_geometry as geo
import rfet_semiconductor as semi
from rfet_post import film_mid_y


def load(path):
    d = np.load(path, allow_pickle=False)
    out = {k: d[k] for k in d.files}
    for k in ("config", "eps_variant", "phi_variant", "solver"):
        out[k] = str(out[k])
    return out


def film_interp(d, key, xs):
    p = geo.CONFIGS[d["config"]]
    sel = d["tri_region"] == "WSe2"
    T = mtri.Triangulation(d["xy"][:, 0], d["xy"][:, 1], d["tri"][sel])
    f = mtri.LinearTriInterpolator(T, d[key])
    return np.array(f(xs, film_mid_y(p, xs)))


def film_average(d, key, xs):
    """두께 방향 5점 평균 (중앙선 하나보다 박막 전체를 대표)"""
    p = geo.CONFIGS[d["config"]]
    sel = d["tri_region"] == "WSe2"
    T = mtri.Triangulation(d["xy"][:, 0], d["xy"][:, 1], d["tri"][sel])
    f = mtri.LinearTriInterpolator(T, d[key])
    acc = np.zeros_like(xs)
    for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
        y = film_mid_y(p, xs) - 0.5 * p.t_wse2 + frac * p.t_wse2
        acc += np.array(f(xs, y))
    return acc / 5.0


def bias_keys(d, kind):
    keys = sorted(k[4:] for k in d if k.startswith("psi_") and k[4:].startswith(kind + "_"))
    def vol(k):
        tg = float(k.split("_TG")[1].split("_BG")[0])
        bg = float(k.split("_BG")[1])
        return tg if kind == "TG" else bg
    return sorted(keys, key=vol), vol


def main(paths):
    import os
    missing = [pth for pth in paths if not os.path.exists(pth)]
    for pth in missing:
        print(f"[건너뜀] 파일 없음: {pth}")
    paths = [pth for pth in paths if os.path.exists(pth)]
    if not paths:
        raise SystemExit("읽을 .npz 가 하나도 없습니다")
    data = [load(pth) for pth in paths]
    d0 = data[0]
    p0 = geo.CONFIGS[d0["config"]]
    L = p0.l_ch
    xs = np.linspace(-150.0, L + 150.0, 1201)

    # ---- 그림 1: 밴드 다이어그램 (첫 번째 데이터) — 왼쪽 TG sweep, 오른쪽 BG sweep; 전압은 발산 색상 ----
    import rfet_plotstyle as st
    st.apply()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.6), gridspec_kw={"height_ratios": [1.0, 1.0], "hspace": 0.45, "wspace": 0.22})
    for col, (kind, vmax) in enumerate((("TG", 5.0), ("BG", 60.0))):
        keys, vol = bias_keys(d0, kind)
        keys = ["flat_TG+0.0_BG+0.0"] + keys
        ax, axz = axes[0, col], axes[1, col]
        for k in keys:
            v = 0.0 if k.startswith("flat") else vol(k)
            color = st.voltage_color(v, vmax)
            psi = film_interp(d0, f"psi_{k}", xs)
            ec, ev = semi.band_edges(psi)
            ax.plot(xs, ec, color=color, lw=1.5)
            ax.plot(xs, ev, color=color, lw=1.5, ls=(0, (3, 2)))
            m1 = (xs >= -10) & (xs <= 60)
            m2 = (xs >= L - 60) & (xs <= L + 10)
            axz.plot(xs[m1], ec[m1], color=color, lw=1.5)
            axz.plot(140 - (L - xs[m2]), ec[m2], color=color, lw=1.5)
            axz.plot(xs[m1], ev[m1], color=color, lw=1.5, ls=(0, (3, 2)))
            axz.plot(140 - (L - xs[m2]), ev[m2], color=color, lw=1.5, ls=(0, (3, 2)))
        # 전체 그림
        ax.axhline(0, color=st.INK, lw=0.8, ls=":")
        ax.text(xs[-1], 0.02, "E$_F$", ha="right", va="bottom", fontsize=8)
        ax.text(xs[-1], semi.band_edges(film_interp(d0, "psi_flat_TG+0.0_BG+0.0", np.array([xs[-1]])))[0][0] + 0.03,
                "E$_c$", ha="right", va="bottom", fontsize=8)
        ax.text(xs[-1], semi.band_edges(film_interp(d0, "psi_flat_TG+0.0_BG+0.0", np.array([xs[-1]])))[1][0] - 0.03,
                "E$_v$", ha="right", va="top", fontsize=8)
        st.shade_metal_regions(ax, L)
        ax.set_title(f"{'ab'[col]}  Band edges on the WSe₂ mid-plane — {kind} sweep (other gate 0 V)", pad=34)
        ax.set_xlabel("x (nm)   (0 = source junction, L = drain junction)"); ax.set_ylabel("energy relative to E$_F$ (eV)")
        ax.set_xlim(xs[0], xs[-1])
        st.structure_strip(ax, p0)
        st.add_colorbar(fig, ax, vmax, f"V$_{{{kind}}}$ (V)")
        # 확대: 두 junction 근처
        axz.axhline(0, color=st.INK, lw=0.8, ls=":")
        axz.axvspan(-10, 0, color="#f1cf6a", alpha=0.35, lw=0); axz.axvspan(140, 150, color="#f1cf6a", alpha=0.35, lw=0)
        axz.axvline(0, color=st.INK2, lw=0.7); axz.axvline(140, color=st.INK2, lw=0.7)
        axz.axvspan(60, 80, color="white", lw=0, zorder=3)      # 두 구간 사이 끊김 표시
        axz.text(70, 0.5, "//", ha="center", va="center", fontsize=11, color=st.INK2, transform=axz.get_xaxis_transform(), zorder=4)
        axz.set_xlim(-10, 150)
        axz.set_xticks([0, 20, 40, 60, 80, 100, 120, 140])
        axz.set_xticklabels(["S", "+20", "+40", "+60", "−60", "−40", "−20", "D"])
        axz.set_title(f"{'cd'[col]}  Zoom: within 60 nm of the source edge (left) and drain edge (right)", pad=6)
        axz.set_xlabel("distance from the junction (nm)"); axz.set_ylabel("energy relative to E$_F$ (eV)")
        axz.text(-8, 0.03, "Source\nmetal", fontsize=7.5, ha="left", va="bottom", color=st.INK2, transform=axz.get_xaxis_transform())
        axz.text(148, 0.03, "Drain\nmetal", fontsize=7.5, ha="right", va="bottom", color=st.INK2, transform=axz.get_xaxis_transform())
        st.add_colorbar(fig, axz, vmax, f"V$_{{{kind}}}$ (V)")
    fig.suptitle(f"Semiconductor electrostatics, V$_S$ = V$_D$ = 0  —  {d0['config']}, "
                 f"φ$_{{Bn}}$: Source {float(d0['phi_bn_source']):.2f} eV / Drain {float(d0['phi_bn_drain']):.2f} eV, "
                 f"{st.VARIANT_LABEL.get(d0['eps_variant'], d0['eps_variant'])}, {d0['solver']}   (solid E$_c$, dashed E$_v$)",
                 x=0.01, ha="left", fontsize=10, color=st.INK2)
    fig.savefig("rfet_post_semi_bands.png")
    plt.close(fig)

    # ---- 그림 2: 캐리어 밀도 (박막 평균, log) — n 실선, p 파선, 색 = 전압 ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    for ax, (kind, vmax) in zip(axes, (("TG", 5.0), ("BG", 60.0))):
        keys, vol = bias_keys(d0, kind)
        for k in keys:
            v = vol(k); color = st.voltage_color(v, vmax)
            ax.semilogy(xs, film_average(d0, f"n_{k}", xs) * semi.NM3_TO_CM3, color=color, lw=1.5)
            ax.semilogy(xs, film_average(d0, f"p_{k}", xs) * semi.NM3_TO_CM3, color=color, lw=1.5, ls=(0, (3, 2)))
        st.shade_metal_regions(ax, L)
        ax.set_ylim(1e8, 1e21)
        ax.set_title(f"{'ab'[kind == 'BG']}  Carrier density (film average) — {kind} sweep   (solid n, dashed p)", pad=34)
        ax.set_xlabel("x (nm)   (0 = source junction, L = drain junction)"); ax.set_ylabel("density (cm$^{-3}$)")
        ax.set_xlim(xs[0], xs[-1])
        st.structure_strip(ax, p0)
        st.add_colorbar(fig, ax, vmax, f"V$_{{{kind}}}$ (V)")
    fig.tight_layout()
    fig.savefig("rfet_post_semi_carriers.png")
    plt.close(fig)

    # ---- 표: junction 에서 10/25/50 nm 떨어진 점의 E_c, 그리고 박막 평균 n, p ----------------------
    print("\n[E_c - E_F at distance from junction, eV]  (S+d: source 쪽, D-d: drain 쪽)")
    print("  data / bias                       | S+10  S+25  S+50 | D-10  D-25  D-50 | n_mid    p_mid  [cm^-3]")
    for d in data:
        p = geo.CONFIGS[d["config"]]
        tag = f"{d['config']}/{d['eps_variant']}/{d['phi_variant']}"
        for k in sorted(kk[4:] for kk in d if kk.startswith("psi_")):
            xs_s, xs_d = np.array([10., 25., 50.]), p.l_ch - np.array([10., 25., 50.])
            ec_s, _ = semi.band_edges(film_interp(d, f"psi_{k}", xs_s))
            ec_d, _ = semi.band_edges(film_interp(d, f"psi_{k}", xs_d))
            n_mid = film_average(d, f"n_{k}", np.array([0.5 * p.l_ch]))[0] * semi.NM3_TO_CM3
            p_mid = film_average(d, f"p_{k}", np.array([0.5 * p.l_ch]))[0] * semi.NM3_TO_CM3
            print(f"  {tag:14s} {k:20s} | " + " ".join(f"{v:5.2f}" for v in ec_s) + " | "
                  + " ".join(f"{v:5.2f}" for v in ec_d) + f" | {n_mid:8.1e} {p_mid:8.1e}")
    print("\n그림 저장: rfet_post_semi_bands.png, rfet_post_semi_carriers.png")


if __name__ == "__main__":
    main(sys.argv[1:] or ["rfet_semi_bridge_perp_lit.npz"])
