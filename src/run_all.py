# -*- coding: utf-8 -*-
"""
run_all.py : run_all.bat 과 같은 일을 파이썬으로. (배치 파일이 막히는 환경용)
  venv 생성 -> pip install -> STEP 2/3/4 전체 실행. 출력은 run_log.txt 에 저장하고 화면에도 보여준다.
사용법 (이 폴더에서):  py -3 run_all.py   또는   python run_all.py
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
LOG = open("run_log.txt", "w", encoding="utf-8")
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")


def log(msg):
    print(msg, flush=True)
    LOG.write(msg + "\n")
    LOG.flush()


def run(cmd, title):
    log(f"\n===== {title} =====")
    log("$ " + " ".join(cmd))
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if p.stdout:
        log(p.stdout.rstrip())
    if p.stderr:
        log("[stderr]\n" + p.stderr.rstrip())
    log(f"[exit {p.returncode}, {time.time() - t0:.1f} s]")
    return p.returncode


log(f"=== start {time.ctime()} ===")
log(f"launcher python: {sys.executable} {sys.version}")

VPY = os.path.join("venv", "Scripts", "python.exe")
if not os.path.exists(VPY):
    run([sys.executable, "-m", "venv", "venv"], "create venv")
run([VPY, "--version"], "venv python version")
run([VPY, "-m", "pip", "install", "--upgrade", "pip"], "pip upgrade")
run([VPY, "-m", "pip", "install", "devsim", "gmsh", "numpy", "scipy", "matplotlib"], "pip install packages")
run([VPY, "-c", "import devsim, gmsh, numpy, scipy, matplotlib; print('devsim', devsim.__version__, 'gmsh', gmsh.__version__, 'numpy', numpy.__version__, 'scipy', scipy.__version__)"], "import check")

steps = [
    (["rfet_geometry.py"], "STEP 2-A geometry"),
    (["rfet_mesh_gmsh.py"], "STEP 2-B mesh (gmsh)"),
    (["rfet_devsim_load.py", "bridge"], "STEP 2-C DEVSIM load bridge"),
    (["rfet_devsim_load.py", "sag45"], "STEP 2-C DEVSIM load sag45"),
    (["rfet_poisson_check.py"], "STEP 3 poisson check (analytic)"),
    (["rfet_poisson_devsim.py", "bridge", "perp"], "STEP 3 DEVSIM poisson bridge perp"),
    (["rfet_fem_reference.py", "selftest"], "STEP 3 FEM selftest"),
    (["rfet_fem_reference.py", "bridge", "perp", "para", "tensor"], "STEP 3 FEM bridge"),
    (["rfet_fem_reference.py", "sag45", "perp", "tensor"], "STEP 3 FEM sag45"),
    (["rfet_post.py", "rfet_devsim_bridge_perp.npz", "rfet_fem_bridge_perp.npz", "rfet_fem_bridge_tensor.npz", "rfet_fem_sag45_perp.npz"], "STEP 3 post"),
    (["rfet_fem_semi.py", "selftest"], "STEP 4 FEM semi selftest"),
    (["rfet_fem_semi.py", "bridge", "perp", "lit"], "STEP 4 FEM semi bridge lit"),
    (["rfet_fem_semi.py", "bridge", "perp", "equal_mid"], "STEP 4 FEM semi bridge equal_mid"),
    (["rfet_poisson_semi_devsim.py", "bridge", "perp", "lit"], "STEP 4 DEVSIM semi bridge lit"),
    (["rfet_post_semi.py", "rfet_semi_bridge_perp_lit.npz", "rfet_semi_devsim_bridge_perp_lit.npz", "rfet_semi_bridge_perp_equal_mid.npz"], "STEP 4 post"),
]
for args, title in steps:
    run([VPY] + args, title)

log(f"\n=== done {time.ctime()} ===")
LOG.close()
print("\nDONE. See run_log.txt")
try:
    input("Press Enter to close...")
except Exception:
    pass
