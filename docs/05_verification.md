# 05. 검증 — 숫자를 믿을 수 있는 이유

원칙 8: 모든 수치 결과는 **독립적인 두 번째 방법**으로 교차 검증한다. 같은 코드를 두 번 돌리는 것은 검증이 아니다. 여기서 "독립"이란 이산화 방식(유한체적 vs 유한요소), 코드 작성자(DEVSIM 내부 vs 직접 작성), 그리고 가능한 곳에서는 해석해를 뜻한다.

## 5-1. 검증 사슬

```
해석해 (평행판 2층)  ──→  FEM selftest        오차 6e-14 V      ✔
해석해 (평행판 2층)  ──→  DEVSIM 설정 check   기준 1e-9 V       (v3, run_figs.py 에서 실행 — 아래 5-5)
1D shooting ODE     ──→  비선형 FEM selftest  차이 ≤ 1.7 mV     ✔
FEM (P1 삼각형)     ←→  DEVSIM (유한체적)    STEP 3 ±0.001 V/V, STEP 4 E_c 소수 둘째자리, n/p 1% 이내  ✔
mesh N=4 → 6 → 8                               ψ ≤ 0.001 V/V, E_c ≤ 5 meV  ✔
geometry 10 검사  ──→  gmsh mesh_report  ──→  DEVSIM check_device   전부 OK  ✔
```

## 5-2. STEP 3: DEVSIM vs FEM (bridge, ε⊥) — `results/step3_profile_table.txt`

| | S+10 | S+25 | S+50 | D−10 | D−25 | D−50 | mid |
|---|---|---|---|---|---|---|---|
| TG DEVSIM | 0.078 | 0.152 | 0.265 | 0.335 | 0.513 | 0.666 | 0.688 |
| TG FEM | 0.078 | 0.152 | 0.265 | 0.336 | 0.513 | 0.667 | 0.687 |
| BG DEVSIM | 0.079 | 0.129 | 0.180 | 0.008 | 0.018 | 0.036 | 0.188 |
| BG FEM | 0.080 | 0.129 | 0.180 | 0.008 | 0.018 | 0.037 | 0.188 |

최대 차이 0.001 V/V. 두 방법은 같은 mesh 노드를 쓰지만 이산화가 다르다(DEVSIM: edge 기반 유한체적 flux 균형, FEM: P1 Galerkin). 1차 요소에서 두 방법은 같은 수렴 차수를 가지므로 mesh 가 충분하면 일치해야 하고, 실제로 그렇다.

## 5-3. STEP 4: DEVSIM vs FEM (bridge, ε⊥, lit) — `results/step4_devsim_vs_fem_bridge_lit.txt`

표의 위 9행이 FEM, 아래 9행이 DEVSIM. 모든 바이어스에서 E_c 가 소수 둘째자리까지 같고, n_mid/p_mid 는 1% 이내 (예: BG+60 n_mid 2.7e18 양쪽; TG+2.5 n_mid 3.3e17 vs 3.4e17). 비선형 문제에서 두 독립 Newton 구현이 일치하므로 ρ(ψ) 수식(softplus)과 Schottky/게이트 경계값이 양쪽에 같게 들어갔음이 확인된다.

## 5-4. Mesh 수렴 — `results/mesh_convergence_bridge.txt`, `figures/fig_mesh_convergence_bridge.png`

`N_LAYERS_FILM` (WSe₂ 두께 방향 요소 수)을 4 → 6 → 8 로 올리면 규칙 1–3 이 모두 비례해서 촘촘해진다.

| | N=4 | N=6 | N=8 |
|---|---|---|---|
| 노드 | 25,658 | 40,915 | 59,893 |
| 삼각형 | 49,700 | 79,734 | 117,222 |

연속 mesh 간 최대 차이 (junction ±10 nm 제외 — 모서리 특이점은 본질적으로 격자 의존):

| 양 | N4 vs N6 | N6 vs N8 | 기준 |
|---|---|---|---|
| ψ_TG | 0.0010 | 0.0004 | 0.005 V/V |
| ψ_BG | 0.0003 | 0.0001 | 0.005 V/V |
| E_c TG+5 | 0.0026 | 0.0016 | 0.01 eV |
| E_c BG+60 | 0.0009 | 0.0004 | 0.01 eV |
| E_c BG−60 | 0.0049 | 0.0037 | 0.01 eV |
| E_c flat | 0.0002 | 0.0001 | 0.01 eV |

차이가 세대마다 줄고(수렴 중) 기준 안이다. 기준의 근거: kT = 26 meV 이므로 E_c 오차 10 meV 는 캐리어 밀도 오차 e^{0.4} ≈ 1.5배로, 장벽 값 불확실성(±0.2 eV → 2000배)보다 훨씬 작다. 결론: **N=4 로 충분**. BG−60 (p 축퇴에 가까움)이 가장 느리게 수렴하는데, 이는 공핍층이 얇아지는 곳에서 두께 방향 분해능이 필요하기 때문이다.

## 5-5. 아직 실제 실행 결과가 없는 검증

`rfet_poisson_check.py` (DEVSIM 평행판 해석해 비교)는 v1/v2 에서 "Contact BG_SiO2 does not exist" 오류를 냈다 (DEVSIM `add_2d_contact` 가 접점 노드를 0개 잡음; 로그 3 참조). v3 는 구조 격자 `.msh` 를 직접 써서 본 계산과 같은 gmsh 경로로 로드한다. 사용자 PC 에서 `py run_figs.py` 또는 `py run_check.py` 로 실행하면 통과/실패가 출력된다. **이것이 통과하기 전까지 DEVSIM 접점 설정의 해석해 검증은 "미완"**이다. 다만 DEVSIM 결과가 독립 FEM(해석해 통과)과 0.001 V/V 로 일치하므로 설정 오류 가능성은 낮다.

## 5-6. 실행 로그 (`results/run_logs/`)

| 파일 | 내용 |
|---|---|
| `run_log_1_first_run.txt` | 첫 실행. gmsh mesh 생성 성공, DEVSIM import 실패 "Error loading math libraries" (Windows MKL 미설치) |
| `run_log_2_resume_devsim.txt` | `pip install mkl` 후 DEVSIM 2.11.2 import OK, `check_device` 전부 OK, STEP 3/4 DEVSIM 완료 |
| `run_log_3_convergence.txt` | N=6, 8 재계산과 수렴 리포트 |

환경: Windows, Python 3.15.2 venv, devsim 2.11.2, gmsh 4.15.2, numpy/scipy/matplotlib 최신.
