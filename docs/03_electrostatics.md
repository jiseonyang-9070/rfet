# 03. STEP 3 — 선형 정전기 (ρ = 0): 게이트 전기장은 어디까지 닿는가

코드: `src/rfet_materials.py`(ε), `src/rfet_poisson_devsim.py`(DEVSIM), `src/rfet_fem_reference.py`(독립 FEM), `src/rfet_poisson_check.py`(해석해 검증), `src/rfet_post.py`(후처리)
그림: `figures/fig_step3_profiles.png`, `figures/fig_step3_maps_bridge.png`
표: `results/step3_profile_table.txt`

## 3-1. 왜 전하 없이 먼저 푸는가

∇·(ε∇ψ) = −ρ 에서 ρ = 0 이면 문제가 **선형**이다. 선형이면
1. 파라미터가 **유전율 하나뿐**이라 결과를 의심할 곳이 적다.
2. 해는 전압에 비례하므로 **단위 응답** 네 개(ψ_S, ψ_D, ψ_TG, ψ_BG: 그 전극만 1 V, 나머지 0 V)만 풀면 임의 전압 조합은 중첩으로 얻는다. `∂ψ/∂V_TG(x)` 가 바로 "TG 1 V 가 채널 그 자리를 몇 V 움직이는가"다.
3. 평행판 해석해와 비교할 수 있어 **DEVSIM 설정 자체를 검증**할 수 있다.

WSe₂ 를 "이동 전하 없는 유전체"로 보는 것이 이 단계의 유일한 물리 가정이다. 실제 캐리어가 있으면 전기장이 차폐되어 응답이 줄어들므로, STEP 3 의 값은 **게이트 결합의 상한**이다.

## 3-2. 유전율 — 출처와 선택

| 재료 | 값 | 출처 | 왜 이 값 |
|---|---|---|---|
| WSe₂ | ε⊥ 7.9, ε∥ 16.0 (정적, bulk) | Laturia 2018 Table 2 | 14층은 1L→bulk 변화(7.5→7.9, 5%)가 포화된 영역. DC 게이트이므로 이온 분극 포함 **정적값** |
| h-BN | ε⊥ 3.76, ε∥ 6.93 (정적, bulk) | Laturia 2018 Table 1 | 30 nm ≈ 90층 → bulk |
| SiO₂ | 3.9 | Sze & Ng 2007 | 열산화막 표준값 |
| 공기 | 1.0 | — | 하한 (03-4) |

**이방성 처리** (원칙 5): DEVSIM 기본 Poisson 이산화는 영역별 **스칼라** ε 를 전제한다. 게이트 전기장은 박막을 면외(⊥)로 지나므로 baseline 스칼라 = ε⊥. 단순화의 영향을 숫자로 말하기 위해 세 가지를 모두 돌렸다:
- `perp` : ε⊥ 스칼라 (DEVSIM + FEM) — baseline
- `para` : ε∥ 스칼라 (FEM) — 스칼라 선택 오차의 반대쪽 끝
- `tensor` : 대각 텐서 (ε_xx = ε∥, ε_yy = ε⊥) (FEM 만 가능) — 참값에 가장 가까움

경사 구간(8°)에서 주축 회전에 의한 비대각 성분 sin8°·(ε∥−ε⊥)/2 ≈ 0.56 은 무시했다 (FEM 은 회전 텐서를 받을 수 있게 만들어 둠).

## 3-3. 경계조건과 DEVSIM 구현

- 금속 경계선: Dirichlet ψ = V (`contact_equation`, 접점마다 파라미터 `<금속>_bias`).
- 계면(WSe₂/공기, h-BN/공기 …): ψ 연속 + 법선 변위 D 연속 (`interface_equation(type="continuous")`; 유한체적 flux 균형이 D 연속을 자동으로 보장).
- 도메인 바깥 벽(x = ±끝): Neumann (자연 경계). 패드 1000 nm 가 fringe 퍼짐의 3배 이상이라 junction 에 영향 없음 [C].
- DEVSIM 모델: `node_solution Potential` → `edge_from_node_model` → `edge_model ElectricField = (Potential@n0 − Potential@n1)·EdgeInverseLength`, `PotentialEdgeFlux = Permittivity·ElectricField` → `equation(..., edge_model="PotentialEdgeFlux")`.

### 평행판 해석해 검증 (`rfet_poisson_check.py`)
2층 평행판(ε₁ d₁ / ε₂ d₂)의 ψ 는 구간별 1차식으로 손으로 풀린다. 같은 DEVSIM 설정 코드로 이 구조를 풀어 1e-9 V 안에서 일치하는지 본다. DEVSIM 내장 `add_2d_contact` 로 만든 접점이 0개로 잡히는 문제가 있어, 구조 격자 `.msh` 를 직접 써서 **본 계산과 똑같은 gmsh 경로**로 로드하도록 바꿨다 (v3). FEM 쪽 selftest 는 오차 6e-14 V 통과. DEVSIM 쪽 v3 실행은 `py run_figs.py` 에서 수행 (05 참조).

## 3-4. 결과 — 박막 중앙선 응답 (V/V, bridge, DEVSIM = FEM)

x 는 junction 에서의 거리. 모서리 점은 격자 의존이라 **10/25/50 nm 떨어진 점**에서 읽는다 (02-5 규칙 2).

| 게이트 | S+10 | S+25 | S+50 | D−10 | D−25 | D−50 | 채널 중앙 |
|---|---|---|---|---|---|---|---|
| **TG** | 0.078 | 0.152 | 0.265 | **0.335** | 0.513 | 0.666 | 0.688 |
| **BG** | **0.079** | 0.129 | 0.180 | 0.008 | 0.018 | 0.036 | 0.188 |

읽는 법:
- **TG** 는 drain junction 옆 10 nm 를 0.34 V/V 움직이지만 source junction 옆은 0.08 V/V 뿐 → Source 금속이 TG 전기장을 가린다 (논문 주장 그대로, 4배 차이).
- **BG** 는 source junction 옆을 0.08 V/V 움직이고 drain junction 옆은 0.008 V/V (10배 차이) → Drain 금속이 BG 를 가린다.
- BG 의 절대 결합이 작은 것은 SiO₂ 300 nm vs h-BN 30 nm 의 두께 비(10:1) 때문이고, 그래서 논문도 BG 를 ±60 V, TG 를 ±5 V 로 쓴다.

### ε 단순화의 영향 (FEM, bridge)
| variant | TG S+10 | TG D−10 | BG S+10 |
|---|---|---|---|
| ε⊥ 스칼라 | 0.078 | 0.336 | 0.080 |
| 텐서 | 0.073 | 0.291 | 0.068 |

텐서가 스칼라 ε⊥ 보다 10–15% 작다: 면내 ε∥ = 16 이 큰 WSe₂ 박막이 **채널 방향으로 전위를 더 잘 퍼뜨려** 국소 응답을 줄인다. 결론은 바뀌지 않지만(차폐 비율 유지) DEVSIM 스칼라 결과는 10–15% 과대라는 점을 항상 적어야 한다.

### h-BN 형상의 영향 (FEM, ε⊥)
| config | TG S+10 | TG D−10 | BG S+10 |
|---|---|---|---|
| bridge | 0.078 | 0.336 | 0.080 |
| sag45 | **0.170** | 0.377 | 0.056 |

sag45 는 TG 가 source junction 옆 채널에 바로 밀착하므로 TG→source 결합이 2배 넘게 커진다 — "TG 차폐"는 h-BN 형상에 민감하다. 다만 sag45 는 비물리적 하한(02-3)이고, 물리적 추정(elastic 449 nm)은 bridge 와 거의 같다.

## 3-5. 이 단계의 한계
- ρ = 0: 캐리어 차폐 없음 → 응답은 상한. STEP 4 에서 보정.
- 스칼라 ε: 10–15% 과대 (위).
- 2D: 폭 방향 fringe 없음.
- 패드 길이 2000 nm 비교 미실시.
