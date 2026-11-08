# -*- coding: utf-8 -*-
"""
rfet_plot_ramp.py
================================================================================
WSe2 경사 "어디서 시작하고 어떤 모양인가" 를 정한 근거 그림 (docs/02 §2-3b).
  a  config 별 WSe2 아랫면 프로파일 (bridge 0→L 직선 / curve_el / line_el / curve70)   — y 축 10배 과장
  b  총 에너지 U(ℓ) = 6Dh²/ℓ³ + Γℓ  와 최소점 ℓ* = (18Dh²/Γ)^¼ ≈ 217 nm;  70 nm(팀원), 500 nm(구 bridge) 표시
  c  경사 모양: 클램프 큐빅(3차식) vs 2차식 — 2차식은 한쪽 끝에서 기울기가 0 이 아니어서 꺾임이 생김
실행:  python rfet_plot_ramp.py   ->  fig_ramp_shapes.png
"""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import rfet_geometry as geo
import rfet_plotstyle as st


def main():
    st.apply()
    b = geo.CONFIGS["bridge"]
    L, h, t = b.l_ch, b.t_drain, b.t_wse2
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6), gridspec_kw=dict(wspace=0.32, left=0.05, right=0.99, top=0.84, bottom=0.15))

    # ---------- a. 프로파일 ----------
    ax = axes[0]
    x = np.linspace(0, L, 801)
    for name in ["bridge", "curve_el", "line_el", "curve70"]:
        p = geo.CONFIGS[name]
        ax.plot(x, p.film_bottom(x), color=st.CONFIG_COLOR.get(name, st.INK2), lw=2.0, label=st.CONFIG_LABEL[name].split(" (")[0]
                + {"bridge": " (구: 0→L 직선 8°)", "curve_el": " (기준: S자 217 nm)", "line_el": " (직선 217 nm)", "curve70": " (팀원 70 nm)"}[name])
    ax.axhline(0, color=st.GRID, lw=1); ax.axhline(h, color=st.GRID, lw=1)
    ax.text(L - 12, h + 3, "Drain 윗면 71 nm", fontsize=8.5, color=st.INK2, va="bottom", ha="right")
    ax.text(5, 2, "SiO₂ 윗면 (BG 쪽)", fontsize=8.5, color=st.INK2, va="bottom")
    ax.axvline(L, color=st.INK2, lw=0.8, ls=":"); ax.text(L - 4, h * 0.45, "Drain 벽", rotation=90, fontsize=8.5, color=st.INK2, ha="right")
    ax.set_xlim(0, L + 10); ax.set_ylim(-6, h + 16)
    ax.set_xlabel("x (nm)  — Source 모서리 = 0"); ax.set_ylabel("WSe₂ 아랫면 y (nm)")
    ax.set_title("a  경사 시작점·모양 (y 축 과장)", loc="left")
    ax.legend(fontsize=8.5, loc="upper left", bbox_to_anchor=(0.0, 0.93), frameon=False)

    # ---------- b. 에너지 ----------
    ax = axes[1]
    E, nu, G = 167.3e9, 0.2, 0.45
    D = geo.bending_rigidity(E, t * 1e-9, nu)
    l_nm = np.linspace(40, 600, 600)
    l = l_nm * 1e-9
    Ub = 6 * D * (h * 1e-9) ** 2 / l ** 3
    Ua = G * l
    scale = 1e9      # J/m (단위 폭당) -> nJ/m
    ax.plot(l_nm, Ub * scale, color=st.AQUA, lw=1.6, ls="--", label="굽힘  6Dh²/ℓ³")
    ax.plot(l_nm, Ua * scale, color=st.ORANGE, lw=1.6, ls="--", label="접착 손실  Γℓ")
    ax.plot(l_nm, (Ub + Ua) * scale, color=st.BLUE, lw=2.4, label="합  U(ℓ)")
    lstar = geo.ramp_length_elastic(b)
    Ustar = (6 * D * (h * 1e-9) ** 2 / (lstar * 1e-9) ** 3 + G * lstar * 1e-9) * scale
    ax.plot([lstar], [Ustar], "o", color=st.BLUE, ms=8, mec="white", mew=1.2, zorder=5)
    ax.annotate(f"ℓ* = (18Dh²/Γ)^¼ = {lstar:.0f} nm", xy=(lstar, Ustar), xytext=(lstar + 40, Ustar * 1.9), fontsize=9.5, color=st.INK,
                arrowprops=dict(arrowstyle="-", color=st.INK2, lw=0.8))
    for xv, lab, col in [(70, "팀원 70 nm\n(Γ≈41 J/m² 필요)", st.RED), (L, "구 bridge 500 nm\n(늘어남 금지 상한 ≈)", st.INK2)]:
        ax.axvline(xv, color=col, lw=1.0, ls=":")
        ax.text(xv + 6, 0.62 * 3.5 * Ustar, lab, fontsize=8.5, color=col, va="top")
    ax.set_ylim(0, 3.5 * Ustar); ax.set_xlim(40, 600)
    ax.set_xlabel("경사 가로 길이 ℓ (nm)"); ax.set_ylabel("단위 폭당 에너지 (nJ/m)")
    ax.set_title("b  왜 217 nm 인가: 굽힘 vs 접착 (E 167 GPa, t 9.1, h 71, Γ 0.45)", loc="left")
    ax.legend(fontsize=8.5, loc="upper right", frameon=False)

    # ---------- c. 모양 ----------
    ax = axes[2]
    u = np.linspace(0, 1, 401)
    cubic = 3 * u ** 2 - 2 * u ** 3
    quad = u ** 2                      # y(0)=0, y'(0)=0, y(1)=1 → y'(1)=2 ≠ 0
    ax.plot(u, cubic, color=st.BLUE, lw=2.4, label="3차식  3u² − 2u³  (양 끝 기울기 0 — 채택)")
    ax.plot(u, quad, color=st.RED, lw=1.8, ls="--", label="2차식  u²  (끝에서 기울기 2h/ℓ ≠ 0 → 꺾임)")
    ax.plot(u, np.where(u < 1, u, 1), color=st.ORANGE, lw=1.4, ls=":", label="직선 u  (양 끝 꺾임, 곡률 ∞)")
    ax.plot([1.0, 1.25], [1.0, 1.0], color=st.INK2, lw=1.0)          # Drain 윗면 연장
    ax.plot([1.0, 1.25], [1.0, 1.0 + 2 * 0.25], color=st.RED, lw=1.0, ls="--", alpha=0.6)   # 2차식 접선
    ax.text(1.02, 1.17, "2차식은 여기서\n윗면과 각을 이룸", fontsize=8.5, color=st.RED, va="bottom")
    ax.plot([-0.25, 0], [0, 0], color=st.INK2, lw=1.0)
    ax.set_xlim(-0.25, 1.3); ax.set_ylim(-0.08, 1.5)
    ax.set_xlabel("u = (x − x_lift) / ℓ"); ax.set_ylabel("y / h")
    ax.set_title("c  모양: 밀착 조건 4개(높이·기울기 × 양 끝) → 3차식만 가능", loc="left")
    ax.legend(fontsize=8.5, loc="upper left", frameon=False)
    m = geo.ramp_mechanics(geo.CONFIGS["curve_el"])
    ax.text(0.98, 0.33, f"curve_el 자기검사:\n최대 기울기 {m['slope_max_deg']:.0f}°, 최소 R {m['radius_min_nm']:.0f} nm\n표면 변형률 {100*m['strain_surface']:.1f} % < 파단 7.3 % (Zhang 2016)",
            fontsize=8.5, color=st.INK2, transform=ax.transAxes, va="top", ha="right", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9))

    fig.suptitle("WSe₂ 경사의 시작점과 모양 — 굽힘·접착 에너지 최소화 (Euler–Bernoulli clamped–clamped beam)", x=0.05, y=0.975, ha="left", fontsize=11.5, color=st.INK)
    out = "fig_ramp_shapes.png"
    fig.savefig(out, dpi=200)
    print("저장:", out)


if __name__ == "__main__":
    main()
