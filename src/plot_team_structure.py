# -*- coding: utf-8 -*-
"""팀원 브랜치(step3-drain-step-fermi)의 geometry/mesh 를 그대로 가져와 우리 스타일로 다시 그린다 (물리 계산 없음)."""
import sys, runpy, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Rectangle
sys.path.insert(0, "/home/claude/rfet_repo/src"); import rfet_plotstyle as st
sys.argv = ["step3_asymmetric_wip.py", "--mesh-only", "--outdir", "."]
try:
    g = runpy.run_path("src/step3_asymmetric_wip.py", run_name="__main__")
except SystemExit as e:
    g = e.__dict__.get("globals")  # not available; fallback below
# runpy 는 SystemExit 시 globals 를 안 돌려주므로 모듈로 실행
import types, builtins
code = open("src/step3_asymmetric_wip.py", encoding="utf-8").read().replace("if args.mesh_only:\n    sys.exit(0)", "if args.mesh_only:\n    raise RuntimeError('STOP')")
ns = {"__name__": "__main__", "__file__": "src/step3_asymmetric_wip.py"}
try:
    exec(compile(code, "step3", "exec"), ns)
except RuntimeError as e:
    assert str(e) == "STOP"
P = np.array(ns["coordinates"]).reshape(-1, 3)[:, :2] / ns["NM"]
tris, edges, G = ns["tris"], ns["edges"], ns["G"]
L, xd, Ld_, S, Hd, ts, th, tox = ns["L"], ns["xd"], ns["Ld_"], ns["S"], ns["Hd"], ns["ts"], ns["th"], ns["tox"]
x_tg = ns["x_tg"]
FACE = {"semi": "#1baf7a", "oxide": "#cfe0f3", "hbn": "#d9cff2", "void": "#ffffff"}
EDGE = {"semi": "#0b6b48", "oxide": "#5f7fa6", "hbn": "#7a66b8", "void": "#9a9a9a"}
CCOL = {"source": "#e0a400", "drain": "#e0a400", "drain_wall": "#e0a400", "tg": "#d1283a", "bg": "#444444"}
T_SRC = 55.0   # 팀원 코드엔 Source 두께가 없음(선). 그림에는 논문값 55 nm 블록으로 표시
st.apply()

def draw(ax, lw):
    for r in FACE:
        polys = [P[list(t[1:])] for t in tris if t[0] == G[r]]
        ax.add_collection(PolyCollection(polys, facecolors=FACE[r], edgecolors=EDGE[r], linewidths=lw, zorder=1))
    # 금속 블록 (팀원 모델은 금속 내부를 풀지 않고 경계선에 전압만 건다 — 블록은 위치 표시)
    ax.add_patch(Rectangle((-S, ts), S, T_SRC, fc="#f1cf6a", ec="none", alpha=0.55, zorder=2))
    ax.add_patch(Rectangle((xd, 0), Ld_, Hd, fc="#f1cf6a", ec="none", alpha=0.55, zorder=2))
    ax.add_patch(Rectangle((-S, -tox - 20), S + xd, 20, fc="#bdbdbd", ec="none", alpha=0.55, zorder=2))
    for gname, a, b in edges:
        if gname in CCOL:
            ax.plot(*P[[a, b]].T, color=CCOL[gname], lw=2.6, solid_capstyle="butt", zorder=4)
    # TG 금속 띠: h-BN 윗면 위 20 nm
    tg_segs = [P[[a, b]] for gname, a, b in edges if gname == "tg"]
    if tg_segs:
        top = np.array(sorted({tuple(p) for s in tg_segs for p in s}))
        ax.fill_between(top[:, 0], top[:, 1], top[:, 1] + 20, color="#f2a3ab", alpha=0.55, zorder=2, lw=0)
    ax.set_aspect("equal"); ax.grid(False)

fig = plt.figure(figsize=(13.5, 7.0))
gs = fig.add_gridspec(2, 3, hspace=0.28, wspace=0.22, top=0.91, bottom=0.08)
ax0 = fig.add_subplot(gs[0, :]); draw(ax0, 0.15)
ax0.set_xlim(-S, xd + Ld_); ax0.set_ylim(-tox - 25, Hd + ts + th + 40)
kw = dict(fontsize=8.5, ha="center", va="center", color=st.INK, zorder=6, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
ax0.text(-S / 2, ts + T_SRC / 2, "Source (선 접점, 두께 없음)", **kw); ax0.text(xd + Ld_ / 2, Hd / 2, "Drain", **kw)
ax0.text(L / 2, ts + th + 32, "Top gate (x = 0 ~ 570)", **kw); ax0.text(L / 2, -tox / 2, "SiO$_2$ 300 nm (x < 570 까지만)", **kw)
ax0.text(L / 2, -tox - 14, "Back gate", **kw); ax0.text(xd + Ld_ / 2, Hd + ts + th / 2, "h-BN (x ≥ 0 에만)", **kw)
ax0.text(L / 2, ts + th / 2, "h-BN 30 nm", fontsize=8, ha="center", va="center", color=st.INK, zorder=6)
ax0.set_xlabel("x (nm)"); ax0.set_ylabel("y (nm)")
ax0.set_title(f"a  팀원 모델 (브랜치 step3-drain-step-fermi) — {len(P):,} nodes, {len(tris):,} triangles   (금색: S/D, 분홍: TG 띠, 회색: BG)")
for k, (ttl, xl, yl) in enumerate([("b  Source 모서리 (x = 0)", (-80, 120), (-25, Hd + ts + th + 15)),
                                     ("c  채널 중앙 (평평)", (L / 2 - 60, L / 2 + 60), (-15, ts + th + 30)),
                                     ("d  Drain 단차 (x = 500 ~ 570)", (L - 60, xd + 80), (-25, Hd + ts + th + 15))]):
    ax = fig.add_subplot(gs[1, k]); draw(ax, 0.45); ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_title(ttl); ax.set_xlabel("x (nm)")
    if k == 0: ax.set_ylabel("y (nm)")
for ax in fig.axes:
    ax.plot([0, xd], [ts, Hd], "o", color=st.RED, ms=5, mec="white", mew=0.8, zorder=7)
fig.suptitle("팀원 비대칭 구조 — 저장소 코드 그대로 만든 격자 (물리 계산 없이 구조만 다시 그림)", x=0.01, y=0.985, ha="left", fontsize=11, color=st.INK2)
fig.savefig("fig_mesh_team_branch.png", dpi=200); print("saved")
