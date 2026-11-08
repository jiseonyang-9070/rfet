# -*- coding: utf-8 -*-
"""발표용 격자 수렴 요약 그림: results/mesh_convergence_bridge.txt 의 최대 차이를 막대로 (log y) — fig_mesh_convergence_simple.png"""
import re, sys
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
import rfet_plotstyle as st

def main(path):
    txt = open(path, encoding="utf-8").read()
    rows = []
    for m in re.finditer(r"(psi_TG|psi_BG|E_c \S+)\s*: N(\d) vs N(\d): ([0-9.]+)", txt):
        rows.append((m.group(1), f"N{m.group(2)}→N{m.group(3)}", float(m.group(4))))
    labels = {"psi_TG": "ψ/V_TG", "psi_BG": "ψ/V_BG", "E_c TG_TG+5.0_BG+0.0": "E_c (TG +5)", "E_c BG_TG+0.0_BG+60.0": "E_c (BG +60)",
              "E_c BG_TG+0.0_BG-60.0": "E_c (BG −60)", "E_c flat_TG+0.0_BG+0.0": "E_c (flat)"}
    keys = [k for k in labels if any(r[0] == k for r in rows)]
    st.apply()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(keys)); w = 0.36
    for j, (step, col) in enumerate([("N4→N6", st.AQUA), ("N6→N8", st.BLUE)]):
        v = [next(r[2] for r in rows if r[0] == k and r[1] == step) for k in keys]
        ax.bar(x + (j - 0.5) * w, v, w, color=col, label=f"격자 {step} (더 촘촘히)")
        for xi, vi in zip(x + (j - 0.5) * w, v):
            ax.text(xi, vi * 1.25, f"{vi:.4f}", ha="center", fontsize=7.5, color=st.INK2)
    ax.axhline(0.005, color=st.RED, ls=":", lw=1.2); ax.text(len(keys) - 0.5, 0.0058, "허용 0.005 V/V", color=st.RED, fontsize=8, ha="right")
    ax.axhline(0.01, color=st.ORANGE, ls=":", lw=1.2); ax.text(len(keys) - 0.5, 0.0115, "허용 0.01 eV", color=st.ORANGE, fontsize=8, ha="right")
    ax.set_yscale("log"); ax.set_ylim(5e-5, 3e-2)
    ax.set_xticks(x); ax.set_xticklabels([labels[k] for k in keys], fontsize=9)
    ax.set_ylabel("연속 격자 간 최대 차이  (V/V 또는 eV)")
    ax.set_title("격자 수렴 (bridge): 2배 촘촘히 해도 결과 변화 < 허용값  — 접합 ±10 nm 제외", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.tight_layout(); fig.savefig("fig_mesh_convergence_simple.png", dpi=200); print("저장: fig_mesh_convergence_simple.png")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../results/mesh_convergence_bridge.txt")
