# 01. STEP 1 — 파라미터 출처 표

모든 숫자를 세 부류로 나눈다.
- **[A] 논문값**: Jiao et al. 2026 본문(6쪽)에서 직접 읽은 값. (Supplementary Material 은 확보하지 못함 → Fig. S1, S2 참조 항목은 "본문에 없음"으로 처리)
- **[B] 문헌값**: 다른 1차 문헌. 반드시 제목·저자·저널·연도·DOI·표/그림 위치·실제값·사용 근거를 적는다.
- **[C] 모델 가정**: 어떤 문헌에도 없어서 모델이 정해야 하는 값. 이유와 "이 값이 바뀌면 무엇이 바뀌는가"를 적는다.

> 코드에서는 `[논문값]`, `[문헌값]`, `[모델 가정]`, `[수치해석 설정]` 네 태그를 쓴다. `[수치해석 설정]` 은 물리가 아니라 계산 격자·수렴 기준 등으로, 값을 바꿔도 **수렴하면 결과가 같아야 하는** 것들이다.

## 1-A. 논문에서 직접 확인한 값 [A]

| 항목 | 값 | 논문 위치 | 비고 |
|---|---|---|---|
| WSe₂ 두께 | 9.1 nm | p.2 "a 9.1 nm-thick WSe₂ (Fig. S1) thin film" | 층수는 본문에 없음 → 0.652 nm/층(Laturia 2018 Table 3)으로 **14층** 환산 [C] |
| h-BN 두께 (TG 유전체) | 30 nm | p.2 "a 30 nm-thick h-BN layer as the top-gate dielectric" | 박편 하나 → 수직 두께 어디서나 30 nm 로 둠 |
| SiO₂ 두께 (BG 유전체) | 300 nm | p.2 "SiO₂ (300 nm)/Si substrate" | BG = 도핑 Si (도핑 미상) |
| Drain 금속 | Ti/Au 1/70 nm → **71 nm** | p.2 "drain electrode (Ti/Au, 1/70 nm)" | 합산은 내가 한 것. Drain 은 **박막 아래**(bottom contact). WSe₂ 와 닿는 쪽은 vdW 전사된 Au |
| Source 금속 | Pd/Au 5/50 nm → **55 nm** | p.2 "source electrode (Pd/Au, 5/50 nm)" | **박막 위**(top contact), 증착. WSe₂ 와 닿는 쪽은 Pd |
| 채널 길이 | ≈ 500 nm | Abstract, p.2, p.4 "approximately 500 nm" | 어느 두 점 사이인지는 Fig. S2(없음). "Source 모서리 ↔ Drain 벽 수평거리"로 해석 [C] |
| Source 모서리 위치 | 전이 구간 밑 | p.2 "source electrode ... edge was positioned at the base of the transition region" | x = 0 을 여기로 둔 근거 |
| TG 전압 범위 | ±5 V 수준 | Fig. 2–3 | STEP 4 sweep 범위 선택의 근거 |
| BG 전압 범위 | ±60 V 수준 | Fig. 2–3 | 〃 |
| 측정 온도 | 본문에 없음 | — | 300 K 가정 [C] |
| TG 금속·크기·위치 | 본문에 없음 (Fig.1 개략도만) | — | overhang 300/300 nm 대칭 [C] |

## 1-B. 다른 1차 문헌에서 가져온 값 [B]

| 항목 | 값 | 출처 (전체 서지는 references.md) | 위치 | 사용 근거 |
|---|---|---|---|---|
| ε(WSe₂) 정적, bulk | ε⊥ 7.9, ε∥ 16.0 | Laturia, Van de Put, Vandenberghe, *npj 2D Mater. Appl.* 2, 6 (2018), DOI 10.1038/s41699-018-0050-x | Table 2 | DFT+DFPT. 14층은 1L→bulk 변화(7.5→7.9)가 포화된 영역이므로 bulk |
| ε(h-BN) 정적, bulk | ε⊥ 3.76, ε∥ 6.93 | 〃 | Table 1 | 30 nm ≈ 90층 → bulk |
| WSe₂ 층 두께 | 0.652 nm | 〃 | Table 3 | 층수 환산 전용 |
| ε(SiO₂) | 3.9 | Sze & Ng, *Physics of Semiconductor Devices* 3rd ed. (2007) | Appendix 표 | 교과서 표준값 (2차 문헌이지만 열산화막 표준값) |
| ε₀ | 8.8541878128e-12 F/m | CODATA 2018 (NIST) | — | 상수 |
| E_g(WSe₂ bulk) | **1.2 eV** (범위 1.16–1.3) | McDonnell et al., *ACS Nano* 8, 6265 (2014), DOI 10.1021/nn501728w Table 3: 1.16±0.03 ; Smyth et al., *2D Mater.* 4, 025084 (2017), DOI 10.1088/2053-1583/aa6bea: 1.3±0.1 (STS 인용) ; Wickramaratne et al., *J. Chem. Phys.* 140, 124710 (2014), DOI 10.1063/1.4869142 Table III: 1.188 (DFT) | | 실험 범위의 중앙값. `EG_RANGE` 로 민감도 가능 |
| χ(WSe₂ bulk) 전자친화도 | 4.03 ± 0.1 eV | McDonnell 2014 Table 3 | | Smyth 2017 의 이온화에너지 5.33 → χ≈4.0 과 0.1 eV 내 일치 |
| m*_e (bulk, CB 최소 Σ점) | 0.489 / 0.643 m₀ (종/횡), 밸리 6 | Wickramaratne 2014 Table II | | 단층(K점, 0.34)과 전혀 다름 → bulk 값 |
| m*_h (bulk, VB 최대 Γ점) | 0.997 m₀, 밸리 1 | 〃 | | |
| φ_Bn Source (증착 Pd / 다층 WSe₂) | **0.22 eV** | Jang et al., *Adv. Mater.* 34, 2109899 (2022), DOI 10.1002/adma.202109899 | Fig. 3f: 증착 Ti/Au/Pd 0.19–0.25 eV, S = 0.03 | 8–12 nm 다층 — 우리 9.1 nm 와 두께 일치 |
| φ_Bn Drain (Au / bulk WSe₂) | **0.53 eV** | Smyth 2017 | Fig. 1, 4 (XPS, UHV 증착 Au) | vdW 접점은 증착과 다를 수 있음 → 불확실 |
| (참고) Ni/WSe₂ | 0.4–0.5 eV | Prakash & Appenzeller, *Sci. Rep.* 7, 12596 (2017) | | 장벽 값의 산포를 보이기 위한 참고 |
| E(h-BN) 영률 | 0.86 TPa | Falin et al., *Nat. Commun.* 8, 15815 (2017) | 1L 0.865±0.073, 9L 0.856±0.003 | h-BN 단차 형상의 탄성 추정에만 사용 |
| Γ 접착에너지 (그래핀/SiO₂, 차용) | 0.45 J/m² | Koenig et al., *Nat. Nanotechnol.* 6, 543 (2011) | | h-BN/WSe₂ 값 미확보 → 차용임을 명시, 0.1–1 J/m² 민감도 |

## 1-C. 모델이 정해야 했던 값 [C] — 이유와 영향

| 항목 | 선택 | 왜 필요한가 | 이 선택이 결과에 주는 영향 |
|---|---|---|---|
| Source/Drain 패드 길이 | 1000 nm 각 | 계산 영역의 좌우 끝을 정해야 함. 잘린 벽엔 Neumann 조건 | BG fringe 의 가로 퍼짐(~SiO₂ 두께 300 nm)의 3배 이상이면 junction 에 영향 없음. 2000 nm 비교는 미실시(→ 06) |
| TG overhang | 300 / 300 nm 대칭 | TG 가 Source 금속 위를 얼마나 덮는지가 "Source 가 TG 를 가린다"의 핵심인데 논문에 수치 없음 | 대칭으로 두어 한쪽 junction 을 미리 유리하게 하지 않음. TG–WSe₂ 거리(30–100 nm)의 3배 |
| h-BN 단차 통과 형상 `l_hbn_step` | bridge(=L) baseline, elastic(449 nm), sag45(48 nm) | 30 nm 박편이 55 nm Source 단차를 어떻게 넘는지 논문에 없음 | TG 가 source junction 에 얼마나 가까이 오는지를 결정 → TG 차폐의 세기. 자세히 02 |
| 빈 공간(쐐기)의 매질 | 공기 ε = 1 | 경사 WSe₂ 아래/위 쐐기에 무엇이 있는지 논문에 없음 | 공기는 ε 하한. 잔류물(PMMA ε≈3)이면 결합이 커짐 → 06 에 민감도 항목 |
| 게이트 금속 두께 `t_gate_dummy` | 20 nm | 시각화·접점 판별 전용 | 정전기 계산에 영향 없음 (금속 내부는 풀지 않음) |
| 온도 | 300 K | 논문에 없음 | kT = 25.85 meV |
| 게이트 일함수 Φ_m | χ + E_g/2 (flat-band) | TG 금속 미상, BG 도핑 미상 | 이상 유전체에선 **전압축 평행이동만** 유발, 분포 모양 불변. 논문 V_th 재현 조정은 fitting 이므로 안 함 |
| 도핑·고정전하·트랩 | 0 | 논문에 값 없음 | 진성 WSe₂. 실제 소자의 V_th 오프셋은 재현 안 됨 |
| DOS 모델 | 층별 2D DOS × 14층 | 3D 식에 필요한 c축 질량이 문헌에 없음 | 층간 분산 무시. 04 에 상세 |
| φ_Bp | E_g − φ_Bn | pinning 준위 하나 가정 | p-분기 장벽은 이 가정에 의존 |

## 1-D. 값을 넣지 않은 항목 (현재 문헌 근거 없음)

| 항목 | 왜 필요한가 | 지금 처리 |
|---|---|---|
| h-BN / WSe₂ 접착 에너지 | 단차 형상 탄성 추정 | 그래핀/SiO₂ 값 차용 + 민감도 |
| WSe₂ 경사 구간의 실제 형상 (SEM/AFM) | 경사 길이·곡률 | 직선 경사 가정 (Fig. S2 없음) |
| vdW Au / WSe₂ 장벽 (전사 접점) | Drain 장벽 | 증착 Au 값 0.53 사용 + S/D 동일 대조군 |
| 측정 온도, TG 금속, BG 도핑 | Φ_m, kT | [C] 가정으로 처리 |
| 이동도, 터널링 질량 | STEP 5 이후 | 아직 필요 없음 (전류 계산 안 함) |
