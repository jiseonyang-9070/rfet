# -*- coding: utf-8 -*-
"""
rfet_converge_report.py
================================================================================
mesh 수렴 검사 리포트. N_LAYERS_FILM = 4, 6, 8 로 만든 mesh 에서 얻은 결과를 비교한다.
  - STEP 3 (선형): 박막 중앙선의 ψ_TG(x), ψ_BG(x) 가 mesh 를 촘촘히 해도 변하지 않는가
  - STEP 4 (비선형): 대표 편향(TG+5, BG+60, BG-60)의 E_c(x) 가 변하지 않는가
수렴 판단(수치해석 설정): 연속한 두 단계(4→6, 6→8) 사이의 차이가 junction 10 nm 이상 떨어진 곳에서
  ψ 응답 < 0.005 V/V, E_c < 0.01 eV 이면 "4 layers mesh 로 충분" 으로 본다. (모서리 점 자체는 특이점이라 제외)
실행:  python rfet_converge_report.py bridge
"""
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import rfet_geometry as geo
import rfet_semiconductor as semi
import rfet_post as post
import rfet_post_semi as ps

TAGS = {4: "", 6: "_n6", 8: "_n8"}
PSI_TOL, EC_TOL = 0.005, 0.01


def main(config="bridge"):
    p = geo.CONFIGS[config]
    L = p.l_ch
    # 비교 구간: junction 에서 10 nm 이상 떨어진 채널 + 금속 위/아래 구간
    xs = np.concatenate([np.linspace(-200, -10, 60), np.linspace(10, L - 10, 300), np.linspace(L + 10, L + 200, 60)])

    lin = {n: post.load(f"rfet_fem_{config}{t}_perp.npz") for n, t in TAGS.items()}
    sem = {n: ps.load(f"rfet_semi_{config}{t}_perp_lit.npz") for n, t in TAGS.items()}
    print(f"[mesh 크기] " + ", ".join(f"N={n}: 노드 {len(d['xy'])}, 삼각형 {len(d['tri'])}" for n, d in lin.items()))
    import rfet_plotstyle as st
    st.apply()
    # 위: N=8 결과 곡선(수렴한 모양), 아래: 연속 mesh 간 |차이| (log) — 겹친 곡선 3개보다 차이를 직접 보여주는 쪽이 설득력 있다
    seq = {4: "#9fc3ea", 6: "#5a98dd", 8: st.BLUE}          # 한 색상의 밝기 단계 (순차)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), gridspec_kw={"hspace": 0.5, "wspace": 0.25})
    ok = True
    print("\n[STEP 3 선형] 연속 mesh 간 최대 차이 (V/V), junction ±10 nm 제외")
    for metal in ("TG", "BG"):
        prof = {n: post.film_profile(d, metal, xs) for n, d in lin.items()}
        ax = axes[0, 0]
        for n in TAGS:
            ax.plot(xs, prof[n], color=seq[n], lw=1.4 if n < 8 else 1.8, label=f"∂ψ/∂V$_{{{metal}}}$, N = {n}" if metal == "TG" else None,
                    ls="-" if metal == "TG" else (0, (3, 2)))
        for a, b in ((4, 6), (6, 8)):
            diff = np.abs(prof[a] - prof[b])
            axes[1, 0].semilogy(xs, np.maximum(diff, 1e-7), color=seq[b], lw=1.4, ls="-" if metal == "TG" else (0, (3, 2)),
                                label=f"{metal}: N{a} → N{b}")
            dmax = np.nanmax(diff); ok &= dmax < PSI_TOL
            print(f"  psi_{metal}: N{a} vs N{b}: {dmax:.4f}  -> {'OK' if dmax < PSI_TOL else 'NOT converged'}")
    axes[0, 0].set_title("a  Linear response on film mid-plane (solid TG, dashed BG)", pad=18)
    axes[0, 0].set_ylabel("∂ψ/∂V (V/V)"); axes[0, 0].legend(fontsize=7.5, loc="upper left")
    axes[1, 0].axhline(PSI_TOL, color=st.RED, lw=0.9, ls=":"); axes[1, 0].text(xs[-1], PSI_TOL * 1.15, f"tolerance {PSI_TOL}", ha="right", fontsize=7.5, color=st.RED)
    axes[1, 0].set_title("c  |difference| between successive meshes (linear)", pad=18)
    axes[1, 0].set_ylabel("|Δ ∂ψ/∂V| (V/V)"); axes[1, 0].set_ylim(1e-7, 1e-1); axes[1, 0].legend(fontsize=7.5, ncol=2, loc="upper right")

    print("\n[STEP 4 비선형] 연속 mesh 간 E_c 최대 차이 (eV), junction ±10 nm 제외")
    keys = ["TG_TG+5.0_BG+0.0", "BG_TG+0.0_BG+60.0", "BG_TG+0.0_BG-60.0", "flat_TG+0.0_BG+0.0"]
    short = {"TG_TG+5.0_BG+0.0": "V$_{TG}$ = +5 V", "BG_TG+0.0_BG+60.0": "V$_{BG}$ = +60 V",
             "BG_TG+0.0_BG-60.0": "V$_{BG}$ = −60 V", "flat_TG+0.0_BG+0.0": "flat band"}
    styles = {"TG_TG+5.0_BG+0.0": "-", "BG_TG+0.0_BG+60.0": (0, (3, 2)), "BG_TG+0.0_BG-60.0": (0, (1, 1.5)), "flat_TG+0.0_BG+0.0": (0, (5, 2, 1, 2))}
    for k in keys:
        prof = {}
        for n, d in sem.items():
            ec, _ = semi.band_edges(ps.film_interp(d, f"psi_{k}", xs))
            prof[n] = ec
        axes[0, 1].plot(xs, prof[8], color=st.ORANGE, lw=1.6, ls=styles[k], label=short[k])
        for a, b in ((4, 6), (6, 8)):
            diff = np.abs(prof[a] - prof[b]); dmax = np.nanmax(diff); ok &= dmax < EC_TOL
            axes[1, 1].semilogy(xs, np.maximum(diff, 1e-7), color={6: "#f3a37e", 8: st.ORANGE}[b], lw=1.3, ls=styles[k],
                                label=f"{short[k]}: N{a} → N{b}")
            print(f"  E_c {k:20s}: N{a} vs N{b}: {dmax:.4f}  -> {'OK' if dmax < EC_TOL else 'NOT converged'}")
    axes[0, 1].axhline(0, color=st.INK, lw=0.8, ls=":")
    axes[0, 1].set_title("b  E$_c$ − E$_F$ on film mid-plane, N = 8 mesh", pad=18)
    axes[0, 1].set_ylabel("E$_c$ − E$_F$ (eV)"); axes[0, 1].legend(fontsize=7.5, loc="center left")
    axes[1, 1].axhline(EC_TOL, color=st.RED, lw=0.9, ls=":"); axes[1, 1].text(xs[-1], EC_TOL * 1.15, f"tolerance {EC_TOL} eV", ha="right", fontsize=7.5, color=st.RED)
    axes[1, 1].set_title("d  |ΔE$_c$| between successive meshes (nonlinear)", pad=18)
    axes[1, 1].set_ylabel("|ΔE$_c$| (eV)"); axes[1, 1].set_ylim(1e-7, 1e-1); axes[1, 1].legend(fontsize=6.5, ncol=2, loc="upper right")
    for ax in axes.ravel():
        st.shade_metal_regions(ax, L)
        ax.set_xlabel("x (nm)"); ax.set_xlim(xs[0], xs[-1])
    for ax in axes[0]:
        ax.set_title(ax.get_title(), pad=34); st.structure_strip(ax, p)
    sizes = ", ".join(f"N = {n}: {len(d['tri']):,} triangles" for n, d in lin.items())
    fig.suptitle(f"Mesh convergence — {config}   ({sizes})", x=0.01, ha="left", fontsize=10, color=st.INK2)
    fig.savefig(f"rfet_converge_{config}.png")
    print(f"\n판정: {'수렴 (N_LAYERS_FILM=4 로 충분)' if ok else '수렴 안 됨 - 더 촘촘한 mesh 필요'}   그림: rfet_converge_{config}.png")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if main(sys.argv[1] if len(sys.argv) > 1 else "bridge") else 1)
