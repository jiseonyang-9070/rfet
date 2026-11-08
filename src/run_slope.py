# -*- coding: utf-8 -*-
"""
run_slope.py : WSe2 경사 형상 민감도 (docs/06 G2).  h-BN·TG 는 곧은 판(두께 일정, 꺾임 없음), WSe2 만 Drain 앞에서 휨.
  경사 시작점: 굽힘-접착 에너지 최소화 ℓ* = (18Dh²/Γ)^¼ ≈ 217 nm (rfet_geometry.ramp_length_elastic) → x ≈ 283 nm 부터 올라감.
  curve = 클램프 큐빅 S자 곡선(역학적 해, 기준), line = 같은 ℓ 의 꺾인 직선(모양 대조군); 70 nm = 팀원 45° 비교; _eq = Source 두께 71 민감도.
  비교 기준(bridge)은 이미 계산돼 있음.
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

CFGS = ["curve_el", "line_el", "curve70", "line70", "curve_el_eq"]   # 판 h-BN + WSe2 만 휨: 곡선(기준) vs 직선, 217(탄성) vs 70(팀원)
rc = {}
rc["geo"] = run("geometry 검사 (전체 config)", ["rfet_geometry.py"])
for c in CFGS:
    rc[f"mesh_{c}"] = run(f"mesh {c}", ["rfet_mesh_gmsh.py", c])
    rc[f"load_{c}"] = run(f"DEVSIM load {c}", ["rfet_devsim_load.py", c])
    rc[f"fem3_{c}"] = run(f"STEP 3 FEM {c}", ["rfet_fem_reference.py", c, "perp"])
    rc[f"dev3_{c}"] = run(f"STEP 3 DEVSIM {c}", ["rfet_poisson_devsim.py", c, "perp"])
    rc[f"fem4_{c}"] = run(f"STEP 4 FEM {c} lit", ["rfet_fem_semi.py", c, "perp", "lit"])
rc["post3"] = run("STEP 3 비교 그림/표", ["rfet_post.py"] + [f"rfet_fem_{c}_perp.npz" for c in CFGS] + [f"rfet_devsim_{c}_perp.npz" for c in CFGS])
rc["post4"] = run("STEP 4 비교 표 (다섯 config)", ["rfet_post_semi.py"] + [f"rfet_semi_{c}_perp_lit.npz" for c in CFGS])
rc["figs"] = run("mesh 그림", ["rfet_plot_mesh.py"] + [f"rfet_{c}_nm.msh" for c in CFGS])
print("\n요약:", rc, "\n로그: results\\run_slope_log.txt"); LOG.write(f"\n요약: {rc}\n"); LOG.close()
input("끝났습니다. 아무 키나 누르면 닫힙니다.")
