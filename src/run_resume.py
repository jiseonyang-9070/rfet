# -*- coding: utf-8 -*-
"""
run_resume.py : 1차 실행(run_all.py)에서 남은 것만 이어서 실행한다.
  1) DEVSIM 이 "math libraries" 오류로 import 되지 않은 문제 -> Intel MKL 설치 (pip install mkl)
  2) DEVSIM 단계 (STEP 2-C, 3, 4), 후처리
  출력은 화면에 실시간으로 보이고 run_log_resume.txt 에도 남는다. 창을 닫지 말고 "DONE" 까지 기다릴 것.
  (STEP 4 는 한 case 당 1~2 분 걸릴 수 있다. 아무것도 안 나와도 멈춘 것이 아니다.)
사용법:  py run_resume.py
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
LOG = open("run_log_resume.txt", "w", encoding="utf-8")
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
VPY = os.path.join("venv", "Scripts", "python.exe")


def log(msg):
    print(msg, flush=True)
    LOG.write(msg + "\n")
    LOG.flush()


def run(cmd, title):
    log(f"\n===== {title} =====")
    log("$ " + " ".join(cmd))
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", env=ENV, bufsize=1)
    for line in p.stdout:                      # 실시간 출력
        log(line.rstrip())
    p.wait()
    log(f"[exit {p.returncode}, {time.time() - t0:.1f} s]")
    return p.returncode


log(f"=== resume start {time.ctime()} ===")
if not os.path.exists(VPY):
    log("venv 가 없습니다. 먼저 run_all.py 를 실행하세요.")
    sys.exit(1)

# ---- DEVSIM 수학 라이브러리: Windows 에서는 Intel MKL 이 필요 (DEVSIM 오류 메시지의 안내대로) ----
run([VPY, "-m", "pip", "install", "mkl"], "pip install mkl (DEVSIM BLAS/LAPACK)")
rc = run([VPY, "-c", "import devsim; print('devsim OK', devsim.__version__)"], "devsim import check")
if rc != 0:
    # MKL 의 DLL 이 venv\Library\bin 에 설치되는데 DEVSIM 이 그 경로를 못 찾는 경우: 경로를 직접 지정해 본다
    libbin = os.path.join(HERE, "venv", "Library", "bin")
    cands = []
    if os.path.isdir(libbin):
        cands = [f for f in os.listdir(libbin) if f.lower().startswith("mkl_rt")]
    log(f"venv\\Library\\bin 의 mkl_rt 파일: {cands}")
    if cands:
        ENV["DEVSIM_MATH_LIBS"] = os.path.join(libbin, cands[0])
        ENV["PATH"] = libbin + os.pathsep + ENV.get("PATH", "")
        rc = run([VPY, "-c", "import devsim; print('devsim OK', devsim.__version__)"], "devsim import check (DEVSIM_MATH_LIBS)")
DEVSIM_OK = (rc == 0)
log(f"DEVSIM 사용 가능: {DEVSIM_OK}")

steps = []
if DEVSIM_OK:
    steps += [
        (["rfet_devsim_load.py", "bridge"], "STEP 2-C DEVSIM load bridge"),
        (["rfet_devsim_load.py", "sag45"], "STEP 2-C DEVSIM load sag45"),
        (["rfet_poisson_check.py"], "STEP 3 poisson check (analytic)"),
        (["rfet_poisson_devsim.py", "bridge", "perp"], "STEP 3 DEVSIM poisson bridge perp"),
    ]
steps += [
    (["rfet_post.py", "rfet_devsim_bridge_perp.npz", "rfet_fem_bridge_perp.npz", "rfet_fem_bridge_tensor.npz", "rfet_fem_sag45_perp.npz"], "STEP 3 post"),
    (["rfet_fem_semi.py", "bridge", "perp", "lit"], "STEP 4 FEM semi bridge lit  (약 1분)"),
    (["rfet_fem_semi.py", "bridge", "perp", "equal_mid"], "STEP 4 FEM semi bridge equal_mid  (약 1분)"),
    (["rfet_fem_semi.py", "sag45", "perp", "lit"], "STEP 4 FEM semi sag45 lit  (약 1분)"),
]
if DEVSIM_OK:
    steps += [(["rfet_poisson_semi_devsim.py", "bridge", "perp", "lit"], "STEP 4 DEVSIM semi bridge lit")]
steps += [(["rfet_post_semi.py", "rfet_semi_bridge_perp_lit.npz", "rfet_semi_devsim_bridge_perp_lit.npz",
            "rfet_semi_sag45_perp_lit.npz", "rfet_semi_bridge_perp_equal_mid.npz"], "STEP 4 post")]
for args, title in steps:
    run([VPY] + args, title)

log(f"\n=== DONE {time.ctime()} ===")
LOG.close()
print("\nDONE. See run_log_resume.txt")
try:
    input("Press Enter to close...")
except Exception:
    pass
