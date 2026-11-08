# -*- coding: utf-8 -*-
"""run_check.py : venv 의 DEVSIM 으로 해석해 검증(rfet_poisson_check.py)만 실행. 사용법: py run_check.py"""
import os, subprocess, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
rc = subprocess.call([os.path.join("venv", "Scripts", "python.exe"), "rfet_poisson_check.py"], env=env)
print(f"\n[exit {rc}]  (0 이면 통과)")
input("Press Enter to close...")
