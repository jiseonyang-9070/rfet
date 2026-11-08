# 02. STEP 2 — Geometry 와 Mesh

코드: `src/rfet_geometry.py`(물리: 모양), `src/rfet_mesh_gmsh.py`(수치: 격자), `src/rfet_mesh_tools.py`, `src/rfet_devsim_load.py`, `src/rfet_size_map.py`, `src/rfet_schematic.py`
그림: `figures/fig_schematic_*.png`(개략), `figures/fig_geometry_*.png`(정확 치수), `figures/fig_mesh_size_rules_bridge.png`

## 2-1. 좌표계 — 왜 이렇게 잡았나

```
  y [nm]
   ^
   |            TG (h-BN 윗면 선에 전압)
   |   ┌──────────────────────────────────────────┐
   |   │                 h-BN 30 nm               │
   |   │ Source(Pd/Au 55) ─┐  air   WSe₂ 경사 9.1  │
   |   │  WSe₂ 9.1 ────────┴──────────┐  WSe₂ on  │
   |   │                   air        │  Drain    │
   |   │              SiO₂ 300        │ Drain(Au/Ti 71)
   |   └──────────────────────────────────────────┘
   |            BG (SiO₂ 아랫면 y = −300 선에 전압)
   +--------------------------------------------------> x [nm]
      x=−1000        x=0            x=L=500       x=1500
                 source junction  drain junction
```
- **x = 0 = Source 금속의 오른쪽 벽** (Source–WSe₂ 접촉 모서리). 논문 "source edge at the base of the transition region" 에 근거.
- **x = L = 500 = Drain 금속의 왼쪽 벽**. "~500 nm" 를 두 금속 벽 사이 수평 거리로 해석 (해석 자체는 [C]).
- **y = 0 = SiO₂ 윗면**. Drain 금속(71 nm)이 여기에 얹히고, Source 쪽 WSe₂ 도 여기에 눕는다.
- 논문 Fig. 1(a) 와 같은 방향(Source 왼쪽)으로 두어 그림을 바로 비교할 수 있게 했다.
- z(폭) 방향은 균일 가정 → 2D 단면. 폭 가장자리 fringe 는 없음 [C].

## 2-2. 영역과 그 유래

WSe₂ 는 Source 쪽에서 SiO₂ 위(y 0–9.1)에 눕고, Drain 금속(71 nm) 위로 올라가야 하므로 **채널 구간(0 < x < L)에서 직선 경사**로 올라간다고 두었다 (Fig. S2 가 없어 곡률은 알 수 없음; 기울기 atan(71/500) ≈ 8.1°).
그러면 자동으로 두 **빈 공간**이 생긴다:
- **AirBot**: 경사 WSe₂ 아래, SiO₂ 위, Drain 벽 왼쪽 → 삼각형 쐐기 (높이 0→71 nm).
- **AirTop**: 경사 WSe₂ 위, h-BN 아래 → 형상은 h-BN 이 단차를 어떻게 넘는지에 따라 다름 (2-3).

| 영역 | 재료 | 어디 | ε (03 참조) |
|---|---|---|---|
| SiO2 | SiO₂ | y −300 ~ 0, 전체 x (Drain 아래 포함) | 3.9 |
| WSe2 | WSe₂ | 두께 9.1 일정, 경사 포함 | 7.9 (⊥) |
| AirBot | 공기 | 경사 아래 쐐기 | 1 |
| AirTop | 공기 | 경사 위 쐐기 | 1 |
| hBN | h-BN | 수직 두께 30 일정 | 3.76 (⊥) |
| 금속 Source/Drain/TG/BG | — | 내부는 풀지 않음, 경계선에 Dirichlet | — |

**금속 내부를 풀지 않는 이유**: 이상 도체 내부는 등전위이므로 그 경계면만 Dirichlet 조건으로 두면 충분하다. 금속 두께는 경계선 위치(단차 높이)로만 들어온다.

**접점(contact)과 계면(interface)은 다각형이 맞닿는 선에서 자동 추출** (`classify_edges`). 손으로 적지 않는 이유: 형상 파라미터를 바꾸면 선 목록이 달라지는데, 손으로 관리하면 빠뜨리기 쉽다. 추출 결과는 `run_checks` 의 10가지 검사(겹침·빈틈·CCW 방향·T-junction·면적 합·점 공유 등)로 확인하고, DEVSIM 로드 뒤 `check_device` 가 region/contact/interface 목록과 좌표 범위를 geometry 와 다시 대조한다 (`results/run_logs/run_log_2_resume_devsim.txt` 148–170행 전부 OK).

## 2-3. h-BN 이 Source 단차를 넘는 형상 — 가장 큰 기하 불확실성

논문은 "30 nm h-BN 박편 하나"라고만 한다. Source 는 WSe₂ 위에 55 nm 솟아 있으므로 박편은 Source 윗면(y = 64.1)에서 Drain 쪽 WSe₂ 윗면(y = 80.1 at x = L, 그 사이는 경사)으로 내려와야 한다. 이것이 **TG 가 source junction 바로 옆 채널에 얼마나 가까이 오는가**를 정하고, 곧 "Source 가 TG 를 가린다"는 메커니즘의 세기를 정한다.

v1 에서는 h-BN 윗면을 평평하게 두었는데, 그러면 Source 위 h-BN 두께가 46 nm, Source 벽 옆이 101 nm 가 되어 "30 nm 박편" 과 모순 → v2 에서 **수직 두께 30 nm 고정 + 전이 길이 `l_hbn_step` 하나**로 바꿨다.

사용자 결정: 하나의 형상만 돌리지 않고 **극단 둘을 처음부터 함께** 돌린다.

| config | l_hbn_step | 의미 | 물리적 지위 |
|---|---|---|---|
| `bridge` | L = 500 nm | 박편이 Source 모서리에서 Drain 쪽 박막 윗면까지 팽팽한 직선 | **baseline** (아래 탄성 추정이 이에 가장 가까움) |
| `elastic` | 449 nm | 탄성 추정값 | bridge 와 거의 같음 → "bridge 가 과장이 아님"을 보이는 용도 |
| `sag45` | 48.2 nm | 45° 로 급하게 내려와 박막에 밀착 | **비물리적 하한**. 민감도 전용 |

**탄성 추정 (`sag_step_elastic`)**: 두께 t 판이 높이 h 단차를 넘어 다시 밀착할 때, 굽힘 에너지 ~ D h²/ℓ³ (D = Et³/12(1−ν²)) 와 접착 에너지 ~ Γℓ 의 합을 ℓ 로 최소화하면 ℓ = (3Dh²/Γ)^¼.
E = 0.86 TPa (Falin 2017), t = 30 nm, h = 55 nm, ν = 0.2 [C], Γ = 0.45 J/m² (그래핀/SiO₂ 차용) → **ℓ ≈ 450 nm**. Γ 를 0.1–1 J/m² 로 바꿔도 ℓ 는 650–370 nm (¼ 제곱 의존). 즉 어떤 합리적 Γ 에서도 ℓ 은 채널 길이와 비슷하고, 박편은 채널 위에서 사실상 다리처럼 걸쳐진다.
sag45 는 곡률 반경 ~40 nm 를 요구하는데, 30 nm 두께 판의 표면 변형률 t/2R ≈ 36% 는 물리적으로 불가능하다. 그래서 sag45 는 "TG 가 채널에 최대로 가까운 가상의 경우"로만 쓴다.

**빈 공간의 매질**: 공기(ε = 1)로 둔다. 이유: (i) 논문에 충전물 언급 없음, (ii) 건식 전사이면 공기/진공, (iii) ε = 1 은 하한이므로 결합을 **과소**평가하는 보수적 쪽. 전사 잔류물(PMMA ε≈3)이 있으면 TG→채널 결합이 커지므로 06 의 민감도 항목으로 남겼다.

같은 탄성 논리를 WSe₂ 경사 자체에 적용하면(9.1 nm, Drain 단차 71 nm) ℓ ≈ 140 nm 로 500 nm 보다 짧다. 즉 실제 WSe₂ 는 Drain 벽 근처에서 더 급하게 올라갈 수 있다. 이것은 drain junction 의 기하를 바꾸므로 STEP 5 이후 민감도로 남긴다 (06).

## 2-4. 좌표표 (bridge, nm)

| 점 | (x, y) | 뜻 |
|---|---|---|
| src_edge_bot | (0, 9.1) | **source junction** — Source 아랫면 오른쪽 모서리 = WSe₂ 윗면 |
| src_edge_top | (0, 64.1) | Source 윗면 오른쪽 모서리 = h-BN 아랫면 꺾임 |
| hbn_kink_src | (0, 94.1) | h-BN 윗면(TG 선) 꺾임 |
| apex | (0, 0) | AirBot 쐐기 끝 (WSe₂ 가 SiO₂ 에서 떨어지기 시작) |
| drn_edge | (500, 71) | **drain junction** — Drain 윗면 왼쪽 모서리 = WSe₂ 아랫면 |
| film_top at L | (500, 80.1) | Drain 쪽 WSe₂ 윗면 = h-BN 아랫면 (bridge 의 touch point) |
| hbn_kink_drn | (500, 110.1) | h-BN 윗면 꺾임 |
| TG 끝 | x = −300, x = 800 | overhang 300 대칭 |
| 도메인 | x ∈ [−1000, 1500], y ∈ [−300, 110.1] | |

## 2-5. Mesh — 어디를 왜 촘촘히 하는가 ([수치해석 설정])

gmsh 의 background field(Distance → Threshold → Min)로 "위치별 삼각형 한 변 길이"를 정한다. 네 규칙:

| 규칙 | 대상 | 크기 | 이유 |
|---|---|---|---|
| 1 | WSe₂ 박막 전체 | 두께/`N_LAYERS_FILM`(4) = 2.3 nm | 캐리어가 몰리고 두께 방향 전위 변화를 풀어야 함. 수렴 검사에서 4→6→8 |
| 2 | 금속–WSe₂ 접촉 모서리 2곳 + 금속 상단 모서리 2곳 | 2.3/`EDGE_REFINE`(4) = 0.57 nm | 직각 도체 모서리에서 E ~ r^(−1/3) 로 발산하는 특이점. **모서리 "그 점"은 격자 의존이므로 결과는 10/25/50 nm 떨어진 점에서 읽는다** (03) |
| 3 | 두 쐐기의 뾰족한 끝 | 끝에서 거리 d 일 때 d·tanθ/`N_ACROSS_WEDGE`(3) | 쐐기 높이가 0 으로 가는 곳에서도 높이 방향 ≥3 요소 |
| 4 | TG 양 끝 + h-BN 꺾임점 | `S_TG_EDGE` 5 nm | TG 모서리 fringe. WSe₂ 에서 30 nm 이상 떨어져 있어 접촉 모서리보다 덜 촘촘해도 됨 |
| — | 성장률 `GROWTH` 0.3, 최대 `S_MAX` 50 nm | | 급한 성장은 삼각형 품질을 떨어뜨림. SiO₂ 깊은 곳은 완만 |

**nm 로 mesh 를 만들고 좌표만 cm 로 바꾸는 이유**: gmsh 의 기하 허용오차(1e-8)가 좌표 단위 그대로 적용되어, cm 단위로 0.57 nm(5.7e-8 cm) 요소를 만들면 점이 겹친 것으로 판정될 수 있다. DEVSIM 은 cm 관례이므로 `.msh` 저장 뒤 `rescale_msh2` 로 1e-7 배.

**MSH 2.2 포맷**: DEVSIM `create_gmsh_mesh` 가 읽는 형식. 물리 그룹 이름 규칙 `R_<region>`, `C_<metal>_<region>`, `I_<regionA>_<regionB>` 로 통일해 DEVSIM 쪽 `add_gmsh_region/contact/interface` 가 이름만으로 연결되게 했다.

실제 결과 (사용자 PC, gmsh 4.15.2): bridge 25,658 노드 / 49,700 삼각형, sag45 20,006 / 38,552. `mesh_report` 가 영역 면적 합 = 다각형 면적, 접점 선 길이 = geometry 선 길이를 FAIL 기준으로 검사하고 최소 각도·Delaunay 를 진단으로 출력.

## 2-6. 타당성 검토 결과

- 10가지 기하 검사 전부 통과 (세 config). 다각형 면적 합 = 도메인 면적 (오차 < 1e-9 nm²).
- DEVSIM 로드 후 region 5, contact 8 (`Source_WSe2, Source_hBN, Source_AirTop, Drain_WSe2, Drain_SiO2, Drain_AirBot, TG_hBN, BG_SiO2`), interface 5 가 geometry 와 일치.
- 좌표 범위: WSe2 y ∈ [0, 80.1], hBN y ∈ [64.1, 110.1], AirBot x ∈ [0, 500] y ∈ [0, 71] 등 기대값과 일치.
