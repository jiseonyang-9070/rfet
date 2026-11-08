# -*- coding: utf-8 -*-
"""
run_converge.py : (1) 해석해 검증 재실행  (2) mesh 수렴 검사: N_LAYERS_FILM = 6, 8 로 bridge mesh 를 다시 만들고
                  STEP 3 선형 + STEP 4 비선형(lit)을 다시 풀어 N=4 결과와 비교한다.
출력: 화면 + run_log_converge.txt.  "DONE" 까지 창을 닫지 말 것 (총 5~10분).
사용법:  py run_converge.py
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
LOG = open("run_log_converge.txt", "w", encoding="utf-8")
BASE_ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
VPY = os.path.join("venv", "Scripts", "python.exe")

def log(m):
    print(m, flush=True); LOG.write(m + "\n"); LOG.flush()

def run(cmd, title, env=None):
    log(f"\n===== {title} =====\n$ " + " ".join(cmd)); t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                         errors="replace", env=env or BASE_ENV, bufsize=1)
    for line in p.stdout:
        log(line.rstrip())
    p.wait(); log(f"[exit {p.returncode}, {time.time()-t0:.1f} s]"); return p.returncode

log(f"=== start {time.ctime()} ===")
run([VPY, "rfet_poisson_check.py"], "STEP 3 DEVSIM 해석해 검증 (bloat 수정본)")
for n, tag in ((6, "_n6"), (8, "_n8")):
    env = dict(BASE_ENV, RFET_N_LAYERS=str(n), RFET_MESH_TAG=tag)
    run([VPY, "rfet_mesh_gmsh.py", "bridge"], f"mesh bridge N_LAYERS_FILM={n}", env)
    run([VPY, "rfet_fem_reference.py", "bridge", "perp"], f"STEP 3 FEM bridge N={n}", env)
    run([VPY, "rfet_fem_semi.py", "bridge", "perp", "lit"], f"STEP 4 FEM semi bridge lit N={n}  (1~3분)", env)
run([VPY, "rfet_converge_report.py", "bridge"], "수렴 리포트")
log(f"\n=== DONE {time.ctime()} ===")
print("\nDONE. See run_log_converge.txt")
try:
    input("Press Enter to close...")
except Exception:
    pass
