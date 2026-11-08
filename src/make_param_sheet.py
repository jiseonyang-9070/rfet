# -*- coding: utf-8 -*-
"""파라미터 검증 스프레드시트: 값 · 출처 · 결정 근거 · 검증 상태 · 코드 일치 여부"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "/home/claude/rfet_xlsx/WSe2_RFET_parameters.xlsx"
F = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1A1630")
HDR_FONT = Font(name=F, bold=True, color="FFFFFF", size=10)
SEC_FILL = PatternFill("solid", fgColor="E9E6F5")
OK_FILL = PatternFill("solid", fgColor="DDF3E8")
WARN_FILL = PatternFill("solid", fgColor="FFF1D6")
thin = Side(style="thin", color="D9D6E6")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()

# ------------------------------------------------------------------ 시트 1: 파라미터
ws = wb.active
ws.title = "파라미터"
cols = ["구분", "항목", "값", "단위", "분류", "출처 (저자, 저널, 연도)", "DOI", "원문 위치", "원문에서 확인한 내용",
        "왜 이 값인가", "바뀌면 달라지는 것", "검증 상태", "확인 방법", "확인일", "코드 변수", "코드 파일"]
widths = [10, 22, 16, 8, 10, 34, 24, 18, 42, 42, 32, 11, 22, 11, 22, 22]
ws.append(cols)
for c, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(c)].width = w
    cell = ws.cell(row=1, column=c); cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.alignment = Alignment(wrap_text=True, vertical="center"); cell.border = BORDER
ws.row_dimensions[1].height = 30
ws.freeze_panes = "C2"

JIAO = ("Jiao et al., Appl. Phys. Lett. 128, 263504 (2026)", "10.1063/5.0338649")
LAT = ("Laturia, Van de Put, Vandenberghe, npj 2D Mater. Appl. 2, 6 (2018)", "10.1038/s41699-018-0050-x")
WIC = ("Wickramaratne, Zahid, Lake, J. Chem. Phys. 140, 124710 (2014)", "10.1063/1.4869142")
MCD = ("McDonnell et al., ACS Nano 8, 6265 (2014)", "10.1021/nn501728w")
SMY = ("Smyth et al., 2D Mater. 4, 025084 (2017)", "10.1088/2053-1583/aa6bea")
JANG = ("Jang et al., Adv. Mater. 34, 2109899 (2022)", "10.1002/adma.202109899")
FAL = ("Falin et al., Nat. Commun. 8, 15815 (2017)", "10.1038/ncomms15815")
KOE = ("Koenig, Boddeti, Dunn, Bunch, Nat. Nanotechnol. 6, 543 (2011)", "10.1038/nnano.2011.123")
SZE = ("Sze & Ng, Physics of Semiconductor Devices, 3rd ed., Wiley (2007)", "")
COD = ("CODATA 2018 (NIST)", "")
NONE = ("— (문헌 없음, 모델이 정함)", "")
D = "2026-11-09"
OK, WARN = "✅ 원문 확인", "⚠️ 간접 확인"

rows = [
 # 구분, 항목, 값, 단위, 분류, 출처, DOI, 위치, 원문 내용, 왜, 영향, 상태, 방법, 확인일, 변수, 파일
 ("구조", "WSe₂ 두께", 9.1, "nm", "[A] 논문값", *JIAO, "p.2", '"a 9.1 nm-thick WSe₂ (Fig. S1) thin film"', "논문값 그대로", "—", OK, "사용자 제공 PDF 본문", D, "Params.t_wse2", "rfet_geometry.py"),
 ("구조", "WSe₂ 층수", 14, "층", "[C] 모델 가정", *LAT, "Table 3", "단층 두께 6.52 Å", "9.1 nm ÷ 0.652 nm ≈ 14. 유전율·유효질량을 bulk 값으로 택하는 근거", "13–15층 어느 쪽이든 bulk 선택 불변", OK, "par.nsf.gov 공개본", D, "N_LAYERS / wse2_layer_count()", "rfet_semiconductor.py / rfet_materials.py"),
 ("구조", "h-BN 두께", 30, "nm", "[A] 논문값", *JIAO, "p.2", '"a 30 nm-thick h-BN layer as the top-gate dielectric"', "박편 하나 → 어디서나 수직 두께 30 nm", "—", OK, "사용자 제공 PDF 본문", D, "Params.t_hbn", "rfet_geometry.py"),
 ("구조", "SiO₂ 두께", 300, "nm", "[A] 논문값", *JIAO, "p.2", '"SiO₂ (300 nm)/Si substrate"', "논문값 그대로. BG = 도핑 Si", "—", OK, "사용자 제공 PDF 본문", D, "Params.t_ox", "rfet_geometry.py"),
 ("구조", "Source 전극 두께 (Pd/Au 5/50)", 55, "nm", "[A] 논문값", *JIAO, "p.2", '"source electrode (Pd/Au, 5/50 nm)"', "합산은 모델이 함. 박막 위 증착, WSe₂와 닿는 금속 = Pd", "단차 높이 → h-BN 형상·TG 거리", OK, "사용자 제공 PDF 본문", D, "Params.t_source", "rfet_geometry.py"),
 ("구조", "Drain 전극 두께 (Ti/Au 1/70)", 71, "nm", "[A] 논문값", *JIAO, "p.2", '"drain electrode (Ti/Au, 1/70 nm)"', "합산은 모델이 함. 박막 아래 vdW 전사, WSe₂와 닿는 금속 = Au", "WSe₂ 경사 높이", OK, "사용자 제공 PDF 본문", D, "Params.t_drain", "rfet_geometry.py"),
 ("구조", "채널 길이 L", 500, "nm", "[A] 논문값(근사)", *JIAO, "Abstract, p.2, p.4", '"approximately 500 nm"', "측정 기준점은 Fig. S2(미확보). Source 모서리(x=0) ↔ Drain 벽(x=L) 수평거리로 해석 [C]", "정의가 다르면 L ±수십 nm", OK, "사용자 제공 PDF 본문", D, "Params.l_ch", "rfet_geometry.py"),
 ("구조", "x = 0 위치", "Source 금속 오른쪽 벽", "", "[A] 논문값", *JIAO, "p.2", '"source electrode … edge was positioned at the base of the transition region"', "논문 서술 그대로", "—", OK, "사용자 제공 PDF 본문", D, "build_points()", "rfet_geometry.py"),
 ("구조", "WSe₂ 경사 형상", "직선, 0→L, ≈8°", "", "[C] 모델 가정", *NONE, "", "Fig. S2 미확보", "가장 단순한 가정", "탄성 추정 ℓ≈140 nm → Drain 쪽에서 더 급할 수 있음 (민감도 미실시)", "—", "해당 없음", "", "Params.film_top()", "rfet_geometry.py"),
 ("구조", "Source/Drain 패드 길이", 1000, "nm", "[C] 모델 가정", *NONE, "", "", "계산 영역 끝(Neumann)이 BG fringe 퍼짐(≈SiO₂ 300 nm)의 3배 이상 떨어지게", "이론상 영향 없음 (2000 nm 비교 미실시)", "—", "해당 없음", "", "Params.l_src_pad / l_drn_pad", "rfet_geometry.py"),
 ("구조", "TG overhang", "300 / 300", "nm", "[C] 모델 가정", *NONE, "", "논문에 TG 수치 없음 (Fig. 1 개략도만)", "대칭으로 두어 한쪽 junction 을 미리 유리하게 하지 않음", "비대칭이면 한쪽 차폐 과대/과소", "—", "해당 없음", "", "Params.tg_overhang_src / _drn", "rfet_geometry.py"),
 ("구조", "h-BN 단차 통과 형상", "bridge (ℓ = L)", "", "[C] 모델 가정 + 탄성 추정", *NONE, "", "", "ℓ = (3Dh²/Γ)^¼ ≈ 450 nm ≈ L → 박편이 채널 위에 걸침", "sag45(48 nm)에서 TG→source 결합 2배 (비물리적 극단)", "—", "해당 없음", "", "CONFIGS, sag_step_elastic()", "rfet_geometry.py"),
 ("구조", "h-BN 영률 E", 0.86, "TPa", "[B] 문헌값", *FAL, "본문 (AFM 압입)", "1L 0.865 ± 0.073, 9L 0.856 ± 0.003 TPa", "층수에 거의 무관 → 30 nm 박편에 적용", "ℓ ∝ E^¼ → 둔감", OK, "PMC 공개본", D, "sag_step_elastic(E_pa)", "rfet_geometry.py"),
 ("구조", "접착에너지 Γ (차용)", 0.45, "J/m²", "[B] 문헌값(차용)", *KOE, "본문", "단층 그래핀/SiO₂ 0.45, 2–5층 0.31 J/m²", "h-BN/WSe₂ 값 미확보 → 차용. ℓ ∝ Γ^(−1/4) 라 0.1–1 J/m² 에서 ℓ = 650–370 nm", "결론(ℓ ≈ L) 불변", WARN, "같은 호 News & Views (R. Huang) 경유", D, "sag_step_elastic(gamma_j_m2)", "rfet_geometry.py"),
 ("구조", "포아송비 ν", 0.2, "", "[C] 모델 가정", *NONE, "", "", "얇은 판 근사 관례값", "ℓ 에 수 % 영향", "—", "해당 없음", "", "sag_step_elastic(nu)", "rfet_geometry.py"),
 ("구조", "빈 공간(쐐기) 매질", "공기 ε = 1", "", "[C] 모델 가정", *NONE, "", "충전물 언급 없음", "ε = 1 은 하한 → 결합을 과소평가하는 보수적 선택", "잔류물(PMMA ε≈3)이면 TG 결합 증가 (민감도 미실시)", "—", "해당 없음", "", "AIR_EPS", "rfet_materials.py"),
 ("유전율", "ε(WSe₂) 정적, 면외 ⊥", 7.9, "", "[B] 문헌값", *LAT, "Table 2, Bulk 행", "1L 7.5, 2L 7.7, Bulk 7.9 (ε₀, ⊥)", "1L→bulk 변화 5%로 포화. 14층은 bulk. DC 게이트 → 정적값", "DEVSIM baseline 스칼라", OK, "par.nsf.gov 공개본", D, "WSE2_EPS['perp']", "rfet_materials.py"),
 ("유전율", "ε(WSe₂) 정적, 면내 ∥", 16.0, "", "[B] 문헌값", *LAT, "Table 2, Bulk 행", "1L 15.3, 2L 15.5, Bulk 16.0 (ε₀, ∥)", "텐서 계산·민감도용", "텐서 vs 스칼라 10–15%", OK, "par.nsf.gov 공개본", D, "WSE2_EPS['para']", "rfet_materials.py"),
 ("유전율", "ε(h-BN) 정적, 면외 ⊥", 3.76, "", "[B] 문헌값", *LAT, "Table 1, Bulk 행", "1L 3.29, 2L 3.44, Bulk 3.76", "30 nm ≈ 90층 → bulk", "—", OK, "par.nsf.gov 공개본", D, "HBN_EPS['perp']", "rfet_materials.py"),
 ("유전율", "ε(h-BN) 정적, 면내 ∥", 6.93, "", "[B] 문헌값", *LAT, "Table 1, Bulk 행", "1L 6.82, 2L 6.86, Bulk 6.93", "텐서 계산·민감도용", "—", OK, "par.nsf.gov 공개본", D, "HBN_EPS['para']", "rfet_materials.py"),
 ("유전율", "ε(SiO₂)", 3.9, "", "[B] 문헌값(교과서)", *SZE, "Appendix", "εr = 3.9 (열산화막)", "교과서 표준값", "—", WARN, "교과서 표준값, 원문 미대조", "", "SIO2_EPS", "rfet_materials.py"),
 ("유전율", "ε₀", 8.8541878128e-12, "F/m", "[B] 상수", *COD, "", "", "표준 상수", "—", OK, "NIST", D, "EPS0_F_PER_M", "rfet_materials.py"),
 ("유전율", "스칼라 선택", "ε⊥", "", "[C] 단순화", *NONE, "", "", "DEVSIM 은 영역별 스칼라만. 게이트 전기장이 박막을 ⊥로 지남", "텐서 대비 10–15% 과대 (FEM 으로 정량화)", "—", "해당 없음", "", "scalar_eps('perp')", "rfet_materials.py"),
 ("밴드", "유효질량 m*_e (종/횡)", "0.489 / 0.643", "m₀", "[B] 문헌값", *WIC, "Table II, Bulk 행", "CB 최소 = Σ점, Σ_l 0.489, Σ_t 0.643 (PBE+SOC). 1L 은 K점 0.345", "bulk CB 최소는 Σ점. 단층 K 값과 다름 → bulk 사용 (원칙 4)", "N_c (DOS)", OK, "arXiv 1401.0502", D, "ME_SIGMA_L, ME_SIGMA_T, GV_CB=6", "rfet_semiconductor.py"),
 ("밴드", "유효질량 m*_h", 0.997, "m₀", "[B] 문헌값", *WIC, "Table II, Bulk 행", "VB 최대 = Γ점, 0.997. 1L 은 K점 0.341", "bulk VB 최대는 Γ점", "N_v (DOS)", OK, "arXiv 1401.0502", D, "MH_GAMMA, GV_VB=1", "rfet_semiconductor.py"),
 ("밴드", "E_g 계산값 (참고)", 1.188, "eV", "[B] 문헌값", *WIC, "Table III, Bulk 행", "간접 Γ_v→Σ_c 1.188 eV (PBE+SOC)", "참고", "—", OK, "arXiv 1401.0502", D, "(주석)", "rfet_semiconductor.py"),
 ("밴드", "E_g 실험 인용값", 1.20, "eV", "[B] 문헌값", *WIC, "Table I, experimental", "bulk WSe₂ 실험값 1.20 eV", "baseline 1.2 eV 의 직접 근거", "—", OK, "arXiv 1401.0502", D, "EG_EV", "rfet_semiconductor.py"),
 ("밴드", "E_g 실험 (범위 하한)", "1.16 ± 0.03", "eV", "[B] 문헌값", *MCD, "Table 3 (Kautek et al. 측정 인용, 각주 *)", "E_g = 1.16 ± 0.03 eV (실험)", "EG_RANGE 하한", "—", OK, "Berkeley 공개본 PDF", D, "EG_RANGE[0]", "rfet_semiconductor.py"),
 ("밴드", "E_g 실험 (범위 상한)", "1.3 ± 0.1", "eV", "[B] 문헌값", *SMY, "본문 (ref. 44 STS 인용)", '"Monolayer (bilayer, bulk) WSe₂ exhibits a band gap of 2.2 (1.8, 1.3) ±0.1 eV as measured by STS"', "EG_RANGE 상한", "—", OK, "IOP 원문", D, "EG_RANGE[1]", "rfet_semiconductor.py"),
 ("밴드", "E_g 채택값", 1.2, "eV", "[B] 종합", "위 세 출처", "", "", "세 실험값(1.16, 1.20, 1.3)의 중앙이자 Wickramaratne Table I 값", "±0.1 eV → 진성 농도·p 분기 장벽", OK, "—", D, "EG_EV", "rfet_semiconductor.py"),
 ("밴드", "이온화에너지 IE", 5.19, "eV", "[B] 문헌값", *MCD, "Table 3, SKexp 행 (Schlaf et al. 실험 인용)", "IE = 5.19 ± 0.1 eV (실험 *)", "χ 유도에 사용", "—", OK, "Berkeley 공개본 PDF", D, "(주석)", "rfet_semiconductor.py"),
 ("밴드", "이온화에너지 IE (교차)", 5.33, "eV", "[B] 문헌값", *SMY, "본문 (ref. 68 인용)", '"Assuming bulk WSe₂ exhibits an ionization energy of 5.33 eV"', "χ 교차확인: 5.33 − 1.3 = 4.03", "—", OK, "IOP 원문", D, "(주석)", "rfet_semiconductor.py"),
 ("밴드", "전자친화도 χ", 4.03, "eV", "[B] 문헌값(유도)", *MCD, "Table 3, SKexp 행", "χ = 4.03 ± 0.1 = IE 5.19 − E_g 1.16 (유도값). LDA 계산도 4.03", "직접 측정값이 아니라 유도값. Smyth 의 5.33 − 1.3 과 일치", "Φ_m 과 함께 전압축 평행이동만", OK, "Berkeley 공개본 PDF", D, "CHI_EV", "rfet_semiconductor.py"),
 ("밴드", "DOS 모델", "층당 2D DOS × 14층", "", "[C] 모델 가정", *NONE, "", "", "3D 식에 필요한 c축 질량이 문헌에 없음. 2D 는 FD 적분 닫힌꼴 n = N_c ln(1+e^η)", "N_c,eq 5.6e20, N_v,eq 1.66e20 cm⁻³", "—", "해당 없음", "", "NC_EQ, NV_EQ, carriers()", "rfet_semiconductor.py"),
 ("밴드", "온도 T", 300, "K", "[C] 모델 가정", *NONE, "", "논문에 측정 온도 없음", "실온 가정", "kT = 25.85 meV", "—", "해당 없음", "", "T_K", "rfet_semiconductor.py"),
 ("밴드", "도핑·고정전하·트랩", 0, "", "[C] 모델 가정", *NONE, "", "논문에 값 없음", "진성 WSe₂. V_th 맞추기는 fitting 이라 안 함", "실제 V_th 오프셋 재현 불가", "—", "해당 없음", "", "N_DOPING", "rfet_semiconductor.py"),
 ("접점", "φ_Bn Drain (Au, vdW)", 0.53, "eV", "[B] 문헌값", *SMY, "본문 문장 (표/그림 없음)", '"The 0.53 eV electron Schottky barrier measured in this work" — XPS, UHV 증착 Au / bulk WSe₂', "증착 Au 값. 논문 Drain 은 vdW 전사 Au 라 다를 수 있음", "절대 E_c ±0.2 eV", OK, "IOP 원문 (출처 위치 정정: Fig. 1, 4 → 본문)", D, "PHI_BN_DRAIN", "rfet_semiconductor.py"),
 ("접점", "φ_Bn Source (Pd, 증착)", 0.22, "eV", "[B] 문헌값(범위 중앙)", *JANG, "Fig. 3f", '증착 Ti/Au/Pd on 8–12 nm WSe₂: "≈190 to 250 meV", 금속 일함수에 거의 무관, S = 0.03. 온도 의존 I–V(열전자, flat-band)로 추출', "논문은 Pd 개별값 없이 범위만 줌 → 0.22 = 중앙값. 두께 8–12 nm 가 9.1 nm 와 일치", "±0.03 eV (범위 폭)", OK, "DNB 공개본 PDF (d-nb.info)", D, "PHI_BN_SOURCE", "rfet_semiconductor.py"),
 ("접점", "pinning factor S (증착)", 0.03, "", "[B] 문헌값", *JANG, "Fig. 3f", "S = 0.03 (강한 pinning)", "증착 금속이면 종류와 무관하게 비슷한 장벽 → Pd 라서가 아니라 증착이라서 0.22", "—", OK, "DNB 공개본 PDF", D, "(주석)", "rfet_semiconductor.py"),
 ("접점", "대조군 장벽", "0.60/0.60, 0.22/0.22, 0.53/0.53", "eV", "[C] 방법", "팀 저장소 step3 발상 차용", "", "", "", "두 문헌값이 다른 시료·방법 → 장벽을 같게 두어 금속 비대칭 제거, 기하 효과만 분리", "핵심 결론의 근거", "—", "해당 없음", "", "PHI_BN_VARIANTS", "rfet_semiconductor.py"),
 ("접점", "φ_Bp", "E_g − φ_Bn", "eV", "[C] 모델 가정", *NONE, "", "", "pinning 준위 하나 가정", "p 분기 장벽", "—", "해당 없음", "", "carriers()", "rfet_semiconductor.py"),
 ("접점", "게이트 일함수 Φ_m", 4.63, "eV", "[C] 모델 가정", *NONE, "", "TG 금속·BG 도핑 미상", "χ + E_g/2 = flat-band 조건", "V_g 축 평행이동만, 분포 모양 불변", "—", "해당 없음", "", "PHI_M_GATE", "rfet_semiconductor.py"),
]
for r in rows:
    ws.append(list(r))
for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    for cell in row:
        cell.font = Font(name=F, size=9); cell.alignment = WRAP; cell.border = BORDER
    st = row[11].value
    if st == OK: row[11].fill = OK_FILL
    elif st == WARN: row[11].fill = WARN_FILL
    row[0].fill = SEC_FILL; row[0].font = Font(name=F, size=9, bold=True)
ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
N_PARAM = ws.max_row

# ------------------------------------------------------------------ 시트 2: 정정 사항
ws2 = wb.create_sheet("정정 사항")
hdr2 = ["#", "항목", "이전 기술 (잘못/부정확)", "정정 후 (원문 대조 결과)", "코드 숫자 변경", "바뀐 곳", "결과표·그림 영향"]
ws2.append(hdr2)
for c, w in enumerate([4, 22, 40, 50, 12, 36, 18], 1):
    ws2.column_dimensions[get_column_letter(c)].width = w
    cell = ws2.cell(row=1, column=c); cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.alignment = Alignment(wrap_text=True, vertical="center"); cell.border = BORDER
fixes = [
 (1, "Smyth 2017 Au 장벽 0.53 eV 의 출처 위치", '"Fig. 1, 4" 에 있다고 기술', '값은 본문 문장 "The 0.53 eV electron Schottky barrier measured in this work" 에만 있고 표/그림에 정리돼 있지 않음', "없음 (0.53 그대로)", "docs/01, docs/references.md, rfet_semiconductor.py 주석", "없음"),
 (2, "χ = 4.03 eV 의 성격", "McDonnell 2014 의 측정값처럼 기술", "Table 3 SKexp 행: Schlaf 의 실험 IE 5.19 − Kautek 의 실험 E_g 1.16 = 4.03 ± 0.1 (유도값). 같은 표 LDA 계산도 4.03. Smyth 의 5.33 − 1.3 과 일치", "없음 (4.03 그대로)", "docs/01, docs/references.md, rfet_semiconductor.py 주석", "없음"),
 (3, "Pd 장벽 0.22 eV 의 성격", "Jang 2022 Fig. 3f 의 Pd 값처럼 기술", 'Fig. 3f 는 증착 Ti/Au/Pd 를 묶어 "≈190 to 250 meV" 범위만 줌 (S = 0.03, 금속 종류에 거의 무관). 0.22 eV 는 범위 중앙값', "없음 (0.22 그대로)", "docs/01, docs/references.md, rfet_semiconductor.py 주석", "없음"),
 (4, "E_g 1.2 eV 의 근거", "실험 범위(1.16–1.3)의 중앙값이라고만 기술", "Wickramaratne 2014 Table I 에 실험 인용값 1.20 eV 가 직접 있음 → 근거 추가", "없음 (1.2 그대로)", "docs/01, docs/references.md, rfet_semiconductor.py 주석", "없음"),
]
for f in fixes: ws2.append(list(f))
for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row):
    for cell in row:
        cell.font = Font(name=F, size=9); cell.alignment = WRAP; cell.border = BORDER

# ------------------------------------------------------------------ 시트 3: 코드 일치 확인
ws3 = wb.create_sheet("코드 일치 확인")
hdr3 = ["변수", "파일", "결과 계산 당시 값 (첫 push bc82a6f)", "현재 코드 값 (838eef1)", "동일 여부", "비고"]
ws3.append(hdr3)
for c, w in enumerate([24, 24, 22, 22, 12, 40], 1):
    ws3.column_dimensions[get_column_letter(c)].width = w
    cell = ws3.cell(row=1, column=c); cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.alignment = Alignment(wrap_text=True, vertical="center"); cell.border = BORDER
consts = [
 ("EG_EV", "rfet_semiconductor.py", 1.2, 1.2, "밴드갭"),
 ("CHI_EV", "rfet_semiconductor.py", 4.03, 4.03, "전자친화도"),
 ("PHI_BN_SOURCE", "rfet_semiconductor.py", 0.22, 0.22, "Source 장벽"),
 ("PHI_BN_DRAIN", "rfet_semiconductor.py", 0.53, 0.53, "Drain 장벽"),
 ("ME_SIGMA_L", "rfet_semiconductor.py", 0.489, 0.489, "전자 종질량"),
 ("ME_SIGMA_T", "rfet_semiconductor.py", 0.643, 0.643, "전자 횡질량"),
 ("MH_GAMMA", "rfet_semiconductor.py", 0.997, 0.997, "정공 질량"),
 ("T_K", "rfet_semiconductor.py", 300, 300, "온도"),
 ("WSE2_EPS perp", "rfet_materials.py", 7.9, 7.9, ""),
 ("WSE2_EPS para", "rfet_materials.py", 16.0, 16.0, ""),
 ("HBN_EPS perp", "rfet_materials.py", 3.76, 3.76, ""),
 ("HBN_EPS para", "rfet_materials.py", 6.93, 6.93, ""),
 ("SIO2_EPS", "rfet_materials.py", 3.9, 3.9, ""),
 ("t_wse2", "rfet_geometry.py", 9.1, 9.1, ""),
 ("t_hbn", "rfet_geometry.py", 30, 30, ""),
 ("t_ox", "rfet_geometry.py", 300, 300, ""),
 ("t_source", "rfet_geometry.py", 55, 55, ""),
 ("t_drain", "rfet_geometry.py", 71, 71, ""),
 ("l_ch", "rfet_geometry.py", 500, 500, ""),
]
for i, (v, f, a, b, note) in enumerate(consts, start=2):
    ws3.append([v, f, a, b, None, note])
    ws3.cell(row=i, column=5).value = f'=IF(C{i}=D{i},"동일","변경")'
for row in ws3.iter_rows(min_row=2, max_row=ws3.max_row):
    for cell in row:
        cell.font = Font(name=F, size=9); cell.alignment = WRAP; cell.border = BORDER
last3 = ws3.max_row
ws3.cell(row=last3 + 2, column=1, value="변경된 변수 수").font = Font(name=F, bold=True, size=9)
ws3.cell(row=last3 + 2, column=2, value=f'=COUNTIF(E2:E{last3},"변경")').font = Font(name=F, bold=True, size=9)
ws3.cell(row=last3 + 3, column=1, value="판정").font = Font(name=F, bold=True, size=9)
ws3.cell(row=last3 + 3, column=2, value=f'=IF(B{last3+2}=0,"숫자 변경 없음 → 결과표·그림 재생성 불필요","재계산 필요")').font = Font(name=F, bold=True, size=9)
ws3.cell(row=last3 + 5, column=1, value="확인 방법: git diff bc82a6f 838eef1 -- src/ 에서 주석 외 변경 없음; 모듈 import 후 값 출력으로 대조 (2026-11-09)").font = Font(name=F, italic=True, size=9, color="52514E")

# ------------------------------------------------------------------ 시트 4: 검증 요약
ws4 = wb.create_sheet("검증 요약")
ws4.column_dimensions["A"].width = 22; ws4.column_dimensions["B"].width = 12; ws4.column_dimensions["C"].width = 60
ws4.append(["검증 상태", "항목 수", "뜻"])
for c in range(1, 4):
    cell = ws4.cell(row=1, column=c); cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.border = BORDER
ws4.append([OK, f"=COUNTIF('파라미터'!L2:L{N_PARAM},\"{OK}\")", "원문(또는 저자 공개본)을 열어 표·문장을 직접 대조"])
ws4.append([WARN, f"=COUNTIF('파라미터'!L2:L{N_PARAM},\"{WARN}\")", "교과서 표준값 / 같은 호 News & Views 경유 — 결론에 영향 없는 값"])
ws4.append(["❌ 미확인", f"=COUNTIF('파라미터'!L2:L{N_PARAM},\"❌ 미확인\")", "원문을 열지 못한 문헌값 (2026-11-09 기준 0)"])
ws4.append(["— (가정, 문헌 없음)", f"=COUNTIF('파라미터'!L2:L{N_PARAM},\"—\")", "[C] 모델 가정 — 검증 대상 아님, 이유·영향은 파라미터 시트에"])
ws4.append(["합계", f"=SUM(B2:B5)", ""])
ws4.append([])
ws4.append(["분류", "항목 수", ""])
r0 = ws4.max_row
for c in range(1, 4):
    cell = ws4.cell(row=r0, column=c); cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.border = BORDER
for lab in ["[A]", "[B]", "[C]"]:
    ws4.append([lab, f"=COUNTIF('파라미터'!E2:E{N_PARAM},\"{lab}*\")", {"[A]": "기준 논문 Jiao 2026 본문", "[B]": "다른 1차 문헌 (DOI·위치 명시)", "[C]": "모델이 정한 값"}[lab]])
for row in ws4.iter_rows(min_row=2, max_row=ws4.max_row):
    for cell in row:
        if cell.value is not None:
            cell.font = Font(name=F, size=10); cell.border = BORDER; cell.alignment = WRAP
ws4["A2"].fill = OK_FILL; ws4["A3"].fill = WARN_FILL
ws4.cell(row=ws4.max_row + 2, column=1, value="원문 공개본 링크").font = Font(name=F, bold=True, size=10)
links = [
 ("Laturia 2018", "https://par.nsf.gov/servlets/purl/10063423"),
 ("Wickramaratne 2014", "https://arxiv.org/pdf/1401.0502"),
 ("Smyth 2017", "https://iopscience.iop.org/article/10.1088/2053-1583/aa6bea"),
 ("McDonnell 2014", "https://nano.eecs.berkeley.edu/publications/ACSNano_2014_MoO3-TMDC%20interface.pdf"),
 ("Jang 2022", "https://d-nb.info/1254874194/34"),
 ("Falin 2017", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5489686"),
 ("Koenig 2011 (News & Views)", "https://sites.utexas.edu/ruihuang/files/2021/03/nnano2011.pdf"),
]
for name, url in links:
    ws4.append([name, "", url])
    ws4.cell(row=ws4.max_row, column=1).font = Font(name=F, size=10)
    c = ws4.cell(row=ws4.max_row, column=3); c.hyperlink = url; c.font = Font(name=F, size=10, color="2A78D6", underline="single")

wb.save(OUT)
print("saved", OUT, "params:", N_PARAM - 1)
