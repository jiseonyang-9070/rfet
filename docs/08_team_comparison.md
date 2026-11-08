# 08. 팀원 코드와의 비교, 그리고 합친 것 (STEP 5-DD)

팀원 저장소 `eungoooooooo00/WSe2-RFET-scaling-with-DEVSIM` — `main` (483b425) 과 브랜치 `step3-drain-step-fermi` (0094c12) — 를
읽고(2026-11-09), 사용자 PC 에서 실제로 돌려(main 전부, 평면 step3 + 우리 문헌값) 비교했다.
결론: **두 코드는 서로 다른 반쪽을 갖고 있다.** 우리는 구조·물성·검증이 강하고 전류가 없다. 팀원은 전류(DD)와 DEVSIM 수송 설정이
강하고 구조·물성·검증이 약하다. 그래서 전류 단계(STEP 5-DD)를 **우리 모델 위에 팀원의 DD 레시피를 얹는** 방식으로 합쳤다.

## 1. 실행으로 확인한 사실

| 팀원 코드 | 실행 결과 (PC, devsim 2.11.2) |
|---|---|
| main step12 (Si 근사 / WSe₂) | README 수치 재현: on/off 6.5×10⁴ / 2.3×10⁵, 최소 전류 7.92×10⁻¹⁶ A/µm at −1 V, 장벽 폭 8.7 nm — **코드는 정직하고 재현된다** |
| main step3 (평면, 0.6/0.6, Boltzmann) | n-모드만 수렴 (on/off 40, 2.5), p-모드 Vbg +4 V 에서 수렴 실패 후 종료 — README 기술 그대로 |
| main step3 + **우리 문헌값** (S 0.22 / D 0.53, ε 7.9/3.76, m*_h 0.997) | **4조합 모두 ±60 V 수렴**. n-모드 on/off 10⁶, p-모드 on 전류가 n-모드의 10⁻⁶ (정공 장벽 0.98 eV) |
| step12 + φ_Bn 0.22 | 수렴 실패 — Boltzmann DD 가 낮은 장벽의 큰 전류를 못 버팀 |
| 브랜치 step3 (단차 + FD) | 아직 미실행 (`team_step3/run_team_step3.py` 준비됨). 저장소 그림: Vtg −5 일 때 Id 가 Vbg 에 무관 → TG 가 drain 접합을 막는 효과 |

## 2. 항목별 비교

| 항목 | 팀원 (브랜치 기준) | 우리 | 합친 결과에 채택 |
|---|---|---|---|
| **구조** | Source = 두께 없는 선, Source 위 h-BN 없음, TG 가 x=0 에서 시작, Drain = 선 + 벽, 채널 500 + 45° 경사 70 nm, 경사 위 막 두께 0.71배 | 55/71 nm 금속 블록, h-BN 이 Source 위를 넘어감(bridge/sag45 두 극단), TG overhang 300, 경사 500 nm 전체, 막 두께 일정, gmsh 비정형 격자 | **우리** (Source 쪽 TG 차폐를 시험하려면 TG 가 Source 를 덮어야 함) |
| **격자** | 직사각형 반분 삼각형, 손으로 짠 좌표 | gmsh + 크기 규칙 4개 + 수렴 검사 4/6/8 | **우리** |
| **유전율** | 7.0(가정) / 8.7(Kumar 2012 DFT), h-BN 3.9(가정) | 7.9/16.0, 3.76/6.93 (Laturia 2018, 원문 확인), 텐서 비교 | **우리** |
| **밴드·질량** | m*_e 0.36 (단층값), m*_h 0.36 가정, E_g 1.2 (Sahin DFT) | bulk Σ/Γ 0.489/0.643/0.997 (Wickramaratne 2014), E_g 1.2 (실험 1.20 + 범위) | **우리** |
| **장벽** | 0.45 가정 (Ni 범위; Au 로 잘못 전제) / 0.6 가정 | Pd 0.22 (Jang 2022) / Au 0.53 (Smyth 2017) + 대조군 3종 | **우리** (+ 대조군 유지) |
| **통계** | 3D N_c + Boltzmann → ±10 V 까지; 브랜치는 Joyce–Dixon FD (근사, u>8 은 이어붙임) | 2D DOS × 14층, n = N_c ln(1+e^η) 닫힌꼴 FD, ±60 V 수렴 | **우리** — 게다가 역함수가 닫힌꼴이라 FD 보정 g(u) 가 **정확식** |
| **접점 BC** | ψ = V + V_t ln(N_c/n_i) − φ_Bn (진성 준위 기준), n = N_c e^{−φ/kT}, p = n_i²/n | ψ = V − (φ_Bn + χ) (진공 준위 기준), n, p 를 2D-DOS 식으로 | **우리** (χ 가 명시되어 게이트 Φ_m 과 같은 축) |
| **전류 (DD)** | simple_physics 로 연속식 + SG 전류, FD 는 "유효 전위 ψ − V_t g(n/N_c)" 로 전류식만 교체, rampbias, REL 1e-7 발견 | 없음 | **팀원** — 구조와 API 호출 순서를 그대로 차용 |
| **측정 흉내** | Vds ±2, Vtg ±5, Vbg 0→±60 (1 V/5 V 간격), 밴드 저장 Vbg ±20 | 평형 바이어스 9점 | **팀원** |
| **검증** | 전류 보존 1개, Boltzmann vs FD 비교 | 독립 FEM, 해석해, 1D ODE, mesh 수렴 | **우리** 습관 유지: DD 평형 해에서 Id = Is ≈ 0 확인, 전류 보존 매 점 기록 |
| **문서화** | params.py 태그([문헌값]/[문헌 계산값]/[가정값]), notes.md 솔직한 한계 목록 | 네 태그 + 검증 상태 + 원문 대조 | 둘 다 좋음; 우리 문서에 팀원 발견(REL 1e-7)을 출처 명시해 반영 |

## 3. 합친 코드: `src/rfet_transport_devsim.py` (STEP 5-DD)

```
우리 STEP 4 평형 해 (gmsh mesh, 문헌 ε·E_g·χ·φ_Bn, 2D-DOS 닫힌꼴 n_eq/p_eq)
   └→ Electrons / Holes 를 미지수로 승격 (초기값 = n_eq, p_eq)
   └→ [팀원] simple_physics.CreateSiliconDriftDiffusion : 연속식 + Boltzmann SG 전류
   └→ [팀원 아이디어 + 우리 정확식] 전류식의 ψ 를 ψ_n = ψ − V_t·g(n/N_c,eq) 로 교체,
        g(u) = ln((e^u − 1)/u)   ← 2D DOS 의 역함수에서 바로 나옴 (Joyce–Dixon 불필요)
   └→ 접점: ψ = V − (φ_Bn + χ),  n_c = N_c,eq ln(1+e^{−φ_Bn/kT}),  p_c = N_v,eq ln(1+e^{−(E_g−φ_Bn)/kT})
   └→ [팀원] 램프(실패 시 반감), REL 1e-7, Vds ±2 / Vtg ±5 / Vbg ±60 스윕, Id·Ie·Ih·Is 기록
```

왜 2D-DOS 에서 g(u) 가 정확한가: n = N_c ln(1+e^η) 를 η 에 대해 풀면 η = ln(e^u − 1) (u = n/N_c).
Boltzmann 은 η_B = ln u 이므로 보정 g = η − η_B = ln((e^u−1)/u) = u + ln((1−e^{−u})/u).
u→0 에서 g→u/2→0 (Boltzmann 극한), u≫1 에서 g→u−ln u. 어떤 u 에서도 overflow 가 없다.
팀원의 3D DOS 에서는 역함수가 닫히지 않아 Joyce–Dixon 근사와 u>8 이어붙이기가 필요했다 — 2D 모델의 부수적 이점이다.

### [모델 가정]으로 남는 것
- 이동도 μ_n = μ_p = 100 cm²/Vs (팀원과 같게 두어 비교 가능). 전류 절대값은 μ 에 비례하므로 **on/off 비와 모양만** 해석한다.
- 생성·재결합 0 (기본). SRH 를 켜려면 `SRH_TAU_S` 에 값.
- 터널링 없음 → 열전자 전류만. 논문 on 전류와 절대값 비교 불가 (팀원도 동일).

### 예상되는 결과와 읽는 법
- 평면 step3 + 문헌값 실행에서 이미 본 것: 정공 장벽 0.98 eV(Source Pd) 때문에 **p-모드 전류가 n-모드의 10⁻⁶**. 단차 구조로 가도 열전자만으로는 같을 것이다.
  → 논문의 양극성 재구성을 설명하려면 **터널링(STEP 5-WKB)이 필수**라는 것이 이 단계의 가장 중요한 산출물이 될 가능성이 높다.
- `equal_mid` (0.6/0.6) 대조군과 비교해 "기하 차폐"와 "금속 비대칭"을 전류 수준에서도 분리한다.

## 4. 실행
```
cd C:\Users\대진\Documents\rfet
py run_transport.py      # quick (수 분) → lit 전체 → equal_mid 전체 (각 10~30분)
```
출력: `rfet_idvbg_bridge_perp_<phi>.csv/.png`, `rfet_band_bridge_perp_<phi>.npz/.png`, 로그 `results/run_transport_log.txt`.
DEVSIM 반복 출력은 로그 파일에만 남고 화면에는 결과 줄만 나온다.

## 5. 팀원에게 돌려줄 수 있는 것 (역방향 보완)
- 원문 대조된 파라미터 표(docs/01)와 출처 — 특히 Source 가 Pd 라는 점, m*_e 0.36 이 단층 K점 값이라는 점.
- h-BN 이 Source 위를 덮는 구조와 TG overhang — Source 쪽 차폐를 시험하려면 필요.
- 2D-DOS 닫힌꼴 통계 — Joyce–Dixon 을 대체하고 ±60 V 수렴 문제를 근본적으로 없앤다.
- mesh 수렴 검사와 독립 solver 교차 검증 절차.
