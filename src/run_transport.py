# -*- coding: utf-8 -*-
"""
STEP 5-DD (rfet_transport_devsim.py) 를 PC 에서 돌리는 스크립트.
  1) --quick  (Vds +2, Vtg ±5, Vbg ±10)  : 동작 확인, 수 분
  2) 전체     lit (S 0.22 / D 0.53)       : 논문 조건 ±60 V, 4 조합
  3) 전체     equal_mid (0.6 / 0.6)       : 금속 비대칭 제거 대조군
화면에는 결과 줄만, 전체 DEVSIM 출력은 results/run_transport_log.txt 에.
실행:  cd C:\\Users\\대진\\Documents\\rfet   →   py run_transport.py
"""
import os, sys, subprocess, time, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "venv", "Scripts", "python.exe")
if not os.path.exists(PY):
    PY = sys.executable
LOGDIR = os.path.join(HERE, "results"); os.makedirs(LOGDIR, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "run_transport_log.txt"), "w", encoding="utf-8")
NOISE = re.compile(r"^\s*(Device|Region|Equation|Iteration|Interface|Contact):|^\s*$")

def run(title, args, timeout):
    print("\n" + "=" * 70 + f"\n[{title}]  {datetime.datetime.now():%H:%M:%S}", flush=True)
    LOG.write("\n" + "=" * 70 + f"\n[{title}]\n$ {' '.join(args)}\n"); LOG.flush()
    t0 = time.time()
    p = subprocess.Popen([PY, "-u"] + args, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", bufsize=1, env=dict(os.environ, PYTHONIOENCODING="utf-8", MPLBACKEND="Agg"))
    for line in p.stdout:
        LOG.write(line); LOG.flush()
        if not NOISE.match(line):
            print(line.rstrip("\n"), flush=True)
    try:
        p.wait(timeout=timeout); rc = p.returncode
    except subprocess.TimeoutExpired:
        p.kill(); rc = "TIMEOUT"
    msg = f"-> 종료 코드 {rc}, 소요 {time.time() - t0:.0f} s"
    print(msg, flush=True); LOG.write(msg + "\n"); LOG.flush()
    return rc

r1 = run("quick: bridge lit", ["rfet_transport_devsim.py", "bridge", "perp", "lit", "--quick"], 1800)
r2 = r3 = "건너뜀"
if r1 == 0:
    r2 = run("전체: bridge lit (S 0.22 / D 0.53)", ["rfet_transport_devsim.py", "bridge", "perp", "lit"], 5400)
    r3 = run("전체: bridge equal_mid (0.60 / 0.60) 대조군", ["rfet_transport_devsim.py", "bridge", "perp", "equal_mid"], 5400)
print(f"\n요약: quick={r1}, lit={r2}, equal_mid={r3}\n로그: {LOG.name}")
LOG.close()
input("끝났습니다. 아무 키나 누르면 닫힙니다.")
