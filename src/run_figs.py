# -*- coding: utf-8 -*-
"""
run_figs.py : 이미 계산된 결과(.npz)로 모든 그림을 새 스타일로 다시 그리고, 해석해 검증(rfet_poisson_check.py)도 돌린다.
출력 그림:
  rfet_geometry_bridge.png / rfet_geometry_sag45.png      구조 단면
  fig_step3_profiles.png / fig_step3_maps.png               STEP 3 전위 응답 (DEVSIM vs FEM)
  fig_step4_bands_bridge_lit.png / fig_step4_bands_bridge_equalmid.png / fig_step4_bands_sag45_lit.png   밴드 다이어그램
  fig_step4_carriers_bridge_lit.png                         캐리어 밀도
  rfet_converge_bridge.png                                  mesh 수렴
사용법:  py run_figs.py
"""
import os, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
VPY = os.path.join("venv", "Scripts", "python.exe")
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")

def run(args, title):
    print(f"\n===== {title} =====", flush=True)
    rc = subprocess.call([VPY] + args, env=ENV)
    print(f"[exit {rc}]", flush=True)
    return rc

def mv(src, dst):
    if os.path.exists(src):
        shutil.move(src, dst); print(f"  -> {dst}")

run(["rfet_poisson_check.py"], "DEVSIM 해석해 검증 (평행판)")
run(["rfet_geometry.py"], "구조 단면(정확한 치수)")
run(["rfet_schematic.py"], "구조 개략도(발표용)")
run(["rfet_post.py", "rfet_devsim_bridge_perp.npz", "rfet_fem_bridge_perp.npz", "rfet_fem_bridge_tensor.npz", "rfet_fem_sag45_perp.npz"], "STEP 3 그림")
mv("rfet_post_profiles.png", "fig_step3_profiles.png"); mv("rfet_post_maps.png", "fig_step3_maps.png")
for npz, tag in (("rfet_semi_bridge_perp_lit.npz", "bridge_lit"), ("rfet_semi_bridge_perp_equal_mid.npz", "bridge_equalmid"),
                 ("rfet_semi_sag45_perp_lit.npz", "sag45_lit")):
    if os.path.exists(npz):
        run(["rfet_post_semi.py", npz], f"STEP 4 그림 {tag}")
        mv("rfet_post_semi_bands.png", f"fig_step4_bands_{tag}.png"); mv("rfet_post_semi_carriers.png", f"fig_step4_carriers_{tag}.png")
if os.path.exists("rfet_fem_bridge_n8_perp.npz"):
    run(["rfet_converge_report.py", "bridge"], "mesh 수렴 그림")
print("\nDONE")
input("Press Enter to close...")
