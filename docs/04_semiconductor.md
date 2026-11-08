# 04. STEP 4 — 반도체 정전기: 밴드는 어디서 휘는가

코드: `src/rfet_semiconductor.py`(물성·ρ(ψ)), `src/rfet_fem_semi.py`(독립 Newton FEM), `src/rfet_poisson_semi_devsim.py`(DEVSIM), `src/rfet_post_semi.py`
그림: `figures/fig_step4_bands_*.png`, `figures/fig_step4_carriers_*.png`
표: `results/step4_table_*.txt`, `results/step4_devsim_vs_fem_bridge_lit.txt`

## 4-1. 이 단계가 더하는 것과 더하지 않는 것

**더함**: WSe₂ 안의 이동 전하 n, p (ρ = q(p − n)), Schottky 접점(금속–WSe₂)의 밴드 정렬, 게이트 일함수.
**더하지 않음**: 전류, 수송, 터널링, 트랩, 도핑. V_S = V_D = 0 **평형**만. 평형이면 WSe₂ 안의 페르미 준위가 하나(E_F = 0)이고 n, p 가 ψ 의 함수로 닫힌다 → 비선형 Poisson 하나만 풀면 된다. 전류를 넣으면 연속 방정식 둘이 더 생기고 이동도·재결합이라는 불확실 파라미터가 따라온다.

## 4-2. 에너지 기준 (코드 전체에서 하나)

- ψ: 정전 전위. 전자의 진공 준위 E_vac = −qψ.
- E_c = −ψ − χ, E_v = E_c − E_g (eV, q = 1 로 숫자 동일).
- 금속 전압 V → E_Fm = −V. 평형이므로 E_F = 0.
- **Schottky 접점**: E_c(접점) − E_Fm = φ_Bn → **ψ_contact = V − (φ_Bn + χ)**.
- **게이트**: E_vac(표면) = E_Fm + Φ_m → **ψ_gate = V_g − Φ_m**.

팀 저장소 코드의 Schottky BC 는 ψ = V + V_t ln(N_c/n_i) − φ_Bn 꼴로 "진성 준위 기준"이고 전하는 Boltzmann n = N_c exp(−φ_Bn/kT) 였다. 여기서는 진공 준위 기준을 택해 χ 가 명시적으로 들어가고, 아래 FD 닫힌꼴로 Boltzmann 제한(팀 코드의 ±10 V 범위)이 없다. 두 기준은 상수 이동으로 등가이지만, χ 를 명시해야 게이트 Φ_m 과 접점 φ_Bn 을 같은 축에서 비교할 수 있다.

## 4-3. 밴드 파라미터 — 출처와 선택 (전체 서지 references.md)

| 항목 | 값 | 출처 | 왜 |
|---|---|---|---|
| E_g | 1.2 eV (1.16–1.3) | McDonnell 2014 Table 3 (1.16±0.03), Smyth 2017 (1.3±0.1 STS), Wickramaratne 2014 Table III (DFT 1.188) | 실험 범위 중앙값 |
| χ | 4.03 ± 0.1 eV | McDonnell 2014 Table 3 | Smyth 2017 (≈4.0) 과 일치 |
| m*_e | 0.489/0.643 m₀, Σ점 밸리 6 | Wickramaratne 2014 Table II | **bulk CB 최소는 Σ(Q) 점**. 단층 K 점(0.34)과 다름 → 원칙 4 |
| m*_h | 0.997 m₀, Γ점 밸리 1 | 〃 | bulk VB 최대 Γ |
| T | 300 K [C] | — | 논문에 없음 |

## 4-4. DOS 모델 — 왜 3D 식을 안 썼나 [C]

3D 식 N_c = 2(2πm*kT/h²)^{3/2} 는 **c축(면외) 질량**이 필요한데 Wickramaratne 2014 는 면내 값만 준다. 층간 결합이 약한 다층 TMD 는 "2D 밴드가 N_layer 개 겹친 것"으로 보는 편이 자연스럽고 필요한 값(면내 DOS 질량 √(m_l m_t), 밸리 수)이 전부 문헌값이다.

- 층당 2D 유효 DOS: N_2D = g_v · m* kT / (πħ²) (스핀 포함)
- 부피 환산: N_eq = N_2D × 14층 / 9.1 nm → **N_c,eq = 5.6×10²⁰ cm⁻³, N_v,eq = 1.66×10²⁰ cm⁻³**
- 2D DOS 의 페르미–디랙 적분은 닫힌 꼴: **n = N_c,eq · ln(1 + e^η)**, η = (E_F − E_c)/kT. η ≪ 0 에서 자동으로 Boltzmann. 축퇴 영역(η > 0)에서도 발산 없음 → ±60 V 까지 수렴.
- DEVSIM 에는 overflow 없는 softplus `max(x,0) + log(1+exp(−abs(x)))` 로 넣었다 (`max`, `abs` 가 DEVSIM 수식 파서에서 동작함을 확인).
- 가정: 층간 분산 무시, 밴드 비포물선성 무시, 양자 구속 무시(14층이라 작음).

## 4-5. 접점 장벽 — 가장 불확실한 물리 파라미터

| 접점 | 금속 (WSe₂ 와 닿는 쪽) | φ_Bn | 출처 | 주의 |
|---|---|---|---|---|
| Source (박막 위, 증착) | **Pd** | 0.22 eV | Jang 2022 Fig. 3f: 증착 Ti/Au/Pd 0.19–0.25 eV, S = 0.03 (강한 pinning), 8–12 nm 다층 | 두께 일치 |
| Drain (박막 아래, vdW 전사) | **Au** | 0.53 eV | Smyth 2017 Fig. 1, 4 (XPS, UHV 증착 Au / bulk) | vdW 접점은 증착 Au 와 다를 수 있음 |

두 값은 **서로 다른 시료·방법**에서 왔다. 그래서 반드시 대조군을 함께 돌린다 (`PHI_BN_VARIANTS`):
- `lit` : 0.22 / 0.53 (문헌)
- `equal_mid` : 0.60 / 0.60 (둘 다 midgap) — **금속 비대칭을 제거하고 기하(차폐) 효과만 보는 대조군**. 이 발상은 팀 저장소 step3 에서 방법론으로 차용.
- `equal_lo`, `equal_hi` : 0.22/0.22, 0.53/0.53.

φ_Bp = E_g − φ_Bn (pinning 준위 하나 가정 [C]).

**게이트 일함수** Φ_m = χ + E_g/2 = 4.63 eV (flat-band 조건) [C]. 이상 유전체·고정전하 0 에서 Φ_m 은 **V_g 축의 평행이동만** 일으키고 분포 모양은 바꾸지 않는다. 논문의 전류 최소점 위치를 맞추려 조정하는 것은 fitting 이므로 하지 않았다.

## 4-6. 수치 방법

- **FEM**: P1 삼각형, Newton + backtracking line search + 전압 continuation(0 → 목표 전압을 단계적으로). Jacobian 에 dρ/dψ = −q(N_c σ(η_n) + N_v σ(η_p))/kT 해석적 사용.
- **DEVSIM**: `node_model PotentialNodeCharge = −q(p − n)` + 그 도함수 `:Potential` 을 `equation(node_model=...)` 에. `ramp_to` 로 전압을 단계적으로 올림.
- selftest: 균일 박막 1D 문제를 shooting 으로 풀어 FEM 과 비교, 차이 ≤ 1.7 mV.
- 바이어스 집합: flat(0,0), TG ±2.5/±5 V (BG 0), BG ±30/±60 V (TG 0). 범위는 논문 Fig. 2–3 의 sweep 범위.

## 4-7. 결과 (bridge, ε⊥, 문헌 장벽, DEVSIM = FEM 소수 둘째자리)

E_c − E_F [eV], junction 에서 떨어진 거리에서 읽음:

| bias | S+10 | S+25 | S+50 | D−10 | D−25 | D−50 | n_mid | p_mid [cm⁻³] |
|---|---|---|---|---|---|---|---|---|
| flat 0/0 | 0.29 | 0.33 | 0.40 | 0.55 | 0.57 | 0.58 | 1.4e11 | 4.5e9 |
| **TG +5** | 0.23 | 0.21 | 0.20 | **0.18** | 0.17 | 0.17 | 7.6e17 | — |
| **TG −5** | 0.46 | 0.69 | 0.96 | **1.04** | 1.06 | 1.06 | — | 7.4e17 |
| **BG +60** | **0.16** | 0.16 | 0.16 | 0.40 | 0.26 | 0.19 | 2.7e18 | — |
| **BG −60** | **1.03** | 1.07 | 1.07 | 0.72 | 0.92 | 1.04 | — | 2.7e18 |

읽는 법:
- flat band 에서도 S 쪽(0.29)과 D 쪽(0.55)의 E_c 가 다른 것은 **장벽 비대칭(0.22 vs 0.53)** 때문이지 게이트 때문이 아니다. → `equal_mid` 대조군에서는 flat 이 양쪽 모두 0.60 (표 `step4_table_bridge_equalmid.txt`).
- **TG −5 V**: drain 쪽 E_c 가 1.04 eV 까지 올라가 p 형(E_v 가 E_F 근처)이 되지만, source 옆 10 nm 는 0.46 eV 로 절반만 움직임 → TG 가 Drain 쪽만 재구성한다. 채널 중앙은 p = 7.4e17.
- **BG ±60 V**: source 옆 E_c 가 0.16 ↔ 1.03 으로 완전히 바뀌는데 drain 옆 10 nm 는 0.40 ↔ 0.72 로 절반 → BG 는 Source 쪽을 재구성한다.
- `equal_mid` 대조군에서도 같은 패턴(TG +5: S+10 0.46 vs D−10 0.18; BG +60: S+10 0.18 vs D−10 0.44) → **선택적 제어는 금속 비대칭이 아닌 기하(차폐)에서 온다**.
- sag45: TG −5 에서 S+10 이 0.57 (bridge 0.46) — TG→source 누설이 커지지만 여전히 D 쪽(1.04)보다 작다.

캐리어 그림(`fig_step4_carriers_*`)은 박막 두께 평균 n, p 를 log 로 보여 어느 게이트가 어느 쪽을 n/p 로 만드는지 raw 로 보인다. "장벽 폭" 같은 지표는 아직 정의하지 않았다 (원칙 6; 정의하려면 WKB 등 물리 근거가 필요 → 07).

## 4-8. 이 단계의 한계
- 평형(V_DS = 0)만. 실제 동작 V_DS 에서는 drain 쪽 준페르미 준위가 갈라진다.
- 장벽 값은 서로 다른 시료에서 온 것 → 대조군으로 보정했지만 절대값은 ±0.2 eV 불확실.
- 계면 트랩·고정전하 0 → 실제 V_th 오프셋 재현 안 됨.
- DEVSIM 은 스칼라 ε (03-4 의 10–15%).
- 접점에서 image-force lowering, 금속 유도 갭 상태(MIGS) 없음.
