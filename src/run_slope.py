# -*- coding: utf-8 -*-
"""
run_slope.py : WSe2 경사 형상 민감도 (docs/06 G2).  elastic(경사 0→L) vs ramp140(탄성 추정) vs ramp70(팀원 45°)
  세 config 모두 h-BN 은 탄성 추정 전이 길이 449 nm → 다른 것은 'WSe2 가 어디서부터 올라가는가' 뿐.
  mesh(gmsh) → STEP 3 (FEM + DEVSIM) → STEP 4 (FEM, DEVSIM lit) → 비교 그림/표 → mesh 그림
사용법:  py C:\\Users\\대진\\Documents\\rfet\\run_slope.py       (10~20분)
"""
import os, re, subprocess, sys, time, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
VPY = os.path.join(HERE, "venv", "Scripts", "python.exe")
os.makedirs("results", exist_ok=True)
LOG = open(os.path.join("results", "run_slope_log.txt"), "w", encoding="utf-8")
NOISE = re.compile(r"^\s*(Device|Region|Equation|Iteration|Interface|Contact):|^Iteration|^\s*$")

def run(title, args, timeout=3600):
    print("\n" + "=" * 70 + f"\n[{title}]  {datetime.datetime.now():%H:%M:%S}", flush=True)
    LOG.write("\n" + "=" * 70 + f"\n[{title}]\n$ {' '.join(args)}\n"); LOG.flush(); t0 = time.time()
    p = subprocess.Popen([VPY, "-u"] + args, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", bufsize=1, env=dict(os.environ, PYTHONIOENCODING="utf-8", MPLBACKEND="Agg"))
    for line in p.stdout:
        LOG.write(line); LOG.flush()
        if not NOISE.match(line): print(line.rstrip("\n"), flush=True)
    p.wait(timeout=timeout); msg = f"-> 종료 코드 {p.returncode}, 소요 {time.time() - t0:.0f} s"
    print(msg, flush=True); LOG.write(msg + "\n"); LOG.flush(); return p.returncode

CFGS = ["elastic", "ramp140", "ramp70"]
rc = {}
rc["geo"] = run("geometry 검사 (전체 config)", ["rfet_geometry.py"])
for c in CFGS:
    rc[f"mesh_{c}"] = run(f"mesh {c}", ["rfet_mesh_gmsh.py", c])
    rc[f"load_{c}"] = run(f"DEVSIM load {c}", ["rfet_devsim_load.py", c])
    rc[f"fem3_{c}"] = run(f"STEP 3 FEM {c}", ["rfet_fem_reference.py", c, "perp"])
    rc[f"dev3_{c}"] = run(f"STEP 3 DEVSIM {c}", ["rfet_poisson_devsim.py", c, "perp"])
    rc[f"fem4_{c}"] = run(f"STEP 4 FEM {c} lit", ["rfet_fem_semi.py", c, "perp", "lit"])
rc["post3"] = run("STEP 3 비교 그림/표", ["rfet_post.py"] + [f"rfet_fem_{c}_perp.npz" for c in CFGS] + [f"rfet_devsim_{c}_perp.npz" for c in CFGS])
rc["post4"] = run("STEP 4 비교 표 (세 config)", ["rfet_post_semi.py"] + [f"rfet_semi_{c}_perp_lit.npz" for c in CFGS])
rc["figs"] = run("mesh 그림", ["rfet_plot_mesh.py"] + [f"rfet_{c}_nm.msh" for c in CFGS])
print("\n요약:", rc, "\n로그: results\\run_slope_log.txt"); LOG.write(f"\n요약: {rc}\n"); LOG.close()
input("끝났습니다. 아무 키나 누르면 닫힙니다.")
