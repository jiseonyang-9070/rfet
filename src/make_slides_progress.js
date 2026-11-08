// 진행 보고 발표용 (INU 스타일: 흰 배경, 상단 파란 선, 좌측 제목, 우측 INU 로고) — 글자 최소, 그림·표 중심
const pptxgen = require("pptxgenjs");
const FIG = (n) => "/home/claude/rfet_repo/figures/" + n;
const MEDIA = "/tmp/claude-0/-home-claude/23b40f53-557b-5ad1-805e-4e71c03a7588/scratchpad/prev/x/ppt/media/";
const NAVY = "1F3A8A", BLUE = "2A78D6", GOLD = "F2B134", INK = "1A1A1A", GRAY = "5E6470", LT = "F3F5FA", LINE = "D6DAE6";
const ORANGE = "EB6834", GREEN = "1BAF7A", RED = "E34948";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.33 x 7.5 in
pres.theme = { headFontFace: "Malgun Gothic", bodyFontFace: "Malgun Gothic" };

function header(s, title) {
  s.background = { color: "FFFFFF" };
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: NAVY }, line: { color: NAVY } });
  s.addText(title, { x: 0.5, y: 0.25, w: 10.6, h: 0.75, fontSize: 26, bold: true, color: NAVY, margin: 0, valign: "middle" });
  s.addShape(pres.ShapeType.line, { x: 0.5, y: 1.02, w: 12.33, h: 0, line: { color: NAVY, width: 1.5 } });
  // INU 로고 (텍스트 재현)
  s.addText("INU", { x: 11.55, y: 0.22, w: 1.0, h: 0.5, fontSize: 24, bold: true, color: NAVY, margin: 0, align: "right" });
  s.addShape(pres.ShapeType.line, { x: 12.0, y: 0.3, w: 0.55, h: 0.0, line: { color: GOLD, width: 3 }, rotate: -35 });
  s.addText("인천대학교", { x: 11.3, y: 0.68, w: 1.3, h: 0.25, fontSize: 9, color: GRAY, margin: 0, align: "right" });
  s.addText("WSe₂ RFET · DEVSIM", { x: 0.5, y: 7.1, w: 5, h: 0.25, fontSize: 9, color: GRAY, margin: 0 });
  s.slideNumber = { x: 12.4, y: 7.1, w: 0.5, h: 0.25, fontSize: 9, color: GRAY, align: "right" };
}
function fit(s, file, box, ratio) { let w = box.w, h = w / ratio; if (h > box.h) { h = box.h; w = h * ratio; }
  s.addImage({ path: file, x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h }); }
function cap(s, t, x, y, w, size = 13, color = INK, bold = false, align = "left") {
  s.addText(t, { x, y, w, h: 0.45, fontSize: size, color, bold, margin: 0, align, valign: "middle" }); }
function card(s, x, y, w, h, fill = LT) { s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 }); }
const TBL = (fs) => ({ fontSize: fs, color: INK, border: { type: "solid", pt: 0.75, color: LINE }, valign: "middle", margin: 0.06 });
const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, align: "center" } });
const B = (t) => ({ text: t, options: { bold: true } });

// ---------- 1. 표지 ----------
{
  const s = pres.addSlide(); s.background = { color: "FFFFFF" };
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: NAVY }, line: { color: NAVY } });
  s.addText("INU", { x: 11.55, y: 0.22, w: 1.0, h: 0.5, fontSize: 24, bold: true, color: NAVY, margin: 0, align: "right" });
  s.addText("인천대학교", { x: 11.3, y: 0.68, w: 1.3, h: 0.25, fontSize: 9, color: GRAY, margin: 0, align: "right" });
  s.addText("Channel Scaling Limits in Complementary Electrostatic Shielding-Based Reconfigurable FETs: A DEVSIM Simulation Study",
    { x: 0.7, y: 1.3, w: 8.3, h: 1.5, fontSize: 22, bold: true, color: NAVY, margin: 0, valign: "top" });
  s.addText("DEVSIM 시뮬레이션을 통한 상보적 정전기 차폐 기반 RFET의 채널 스케일링 한계 분석", { x: 0.7, y: 2.9, w: 8.3, h: 0.5, fontSize: 15, color: INK, margin: 0 });
  s.addText("진행 보고 — 500 nm 소자 재현 (STEP 0 → 5)", { x: 0.7, y: 3.5, w: 8.3, h: 0.45, fontSize: 15, color: BLUE, bold: true, margin: 0 });
  s.addText("양지선 · 이은수 · 이종명", { x: 0.7, y: 6.2, w: 6, h: 0.4, fontSize: 13, color: GRAY, margin: 0 });
  s.addImage({ path: MEDIA + "image1.png", x: 8.6, y: 4.4, w: 4.2, h: 4.2 * 315 / 610 });
  s.addShape(pres.ShapeType.rect, { x: 0, y: 7.1, w: 13.33, h: 0.4, fill: { color: NAVY }, line: { color: NAVY } });
  s.addShape(pres.ShapeType.rect, { x: 0, y: 7.1, w: 4.5, h: 0.4, fill: { color: GOLD }, line: { color: GOLD } });
}

// ---------- 2. 선행논문: 소자와 원리 ----------
{
  const s = pres.addSlide(); header(s, "선행논문 : 상보적 정전기 차폐 RFET (Jiao et al., APL 2026)");
  s.addImage({ path: MEDIA + "image2.png", x: 0.6, y: 1.35, w: 5.6, h: 5.6 * 478 / 656 });
  s.addImage({ path: MEDIA + "image3.png", x: 6.5, y: 1.35, w: 6.3, h: 6.3 * 627 / 954 });
  card(s, 0.6, 5.65, 12.2, 1.1, LT);
  s.addText("Source 는 박막 위 → TG 를 가림 → Source 접합은 BG 만 제어", { x: 0.8, y: 5.7, w: 6.0, h: 0.5, fontSize: 14, bold: true, color: NAVY, margin: 0, valign: "middle" });
  s.addText("Drain 은 박막 아래 → BG 를 가림 → Drain 접합은 TG 만 제어", { x: 6.9, y: 5.7, w: 6.0, h: 0.5, fontSize: 14, bold: true, color: NAVY, margin: 0, valign: "middle" });
  s.addText("한 게이트 = 한 접합  →  TG 로 n/p 선택, BG 로 on/off  (채널 ≈ 500 nm)", { x: 0.8, y: 6.2, w: 11.8, h: 0.45, fontSize: 14, color: INK, margin: 0 });
}

// ---------- 3. 연구 질문 ----------
{
  const s = pres.addSlide(); header(s, "연구 질문 : 채널을 줄이면 어디서부터 선택적 제어가 무너지나");
  const xs = [1.2, 4.3, 7.4, 10.5], labs = ["2 µm", "500 nm", "200 nm", "100 nm"], sub = ["", "선행논문 · 우리 재현", "", "crosstalk?"];
  s.addShape(pres.ShapeType.line, { x: 1.2, y: 3.0, w: 9.6, h: 0, line: { color: NAVY, width: 2.5 } });
  xs.forEach((x, i) => {
    s.addShape(pres.ShapeType.ellipse, { x: x - 0.14, y: 2.86, w: 0.28, h: 0.28, fill: { color: i === 1 ? GOLD : NAVY }, line: { color: "FFFFFF", width: 1 } });
    s.addText(labs[i], { x: x - 1.2, y: 2.1, w: 2.4, h: 0.6, fontSize: 20, bold: true, color: i === 1 ? ORANGE : NAVY, align: "center", margin: 0 });
    if (sub[i]) s.addText(sub[i], { x: x - 1.5, y: 3.25, w: 3.0, h: 0.4, fontSize: 13, color: GRAY, align: "center", margin: 0 });
  });
  card(s, 0.8, 4.3, 5.9, 2.3); card(s, 6.9, 4.3, 5.9, 2.3);
  s.addText([B("1단계 (지금까지)"), { text: "\n500 nm 소자를 처음부터 독립 구현\n전위 → 밴드 → 전류에서 \"한 게이트 = 한 접합\" 확인", options: {} }],
    { x: 1.0, y: 4.4, w: 5.6, h: 2.1, fontSize: 15, color: INK, margin: 0, valign: "top" });
  s.addText([B("2단계 (다음)"), { text: "\n터널링 추가 → p형 재현\n채널 길이를 줄이며 TG→Source 번짐(fringe) 추적", options: {} }],
    { x: 7.1, y: 4.4, w: 5.6, h: 2.1, fontSize: 15, color: INK, margin: 0, valign: "top" });
}

// ---------- 4. 원칙 ----------
{
  const s = pres.addSlide(); header(s, "진행 원칙 : 처음부터 독립 구현, 모든 숫자에 출처");
  const items = [["처음부터", "팀 코드 참고만\n구조·물리·코드 독립\n→ 두 코드 교차 검증 가능", NAVY],
                 ["숫자 분류", "[A] 논문값\n[B] 1차 문헌값 (DOI·표 위치)\n[C] 모델 가정 (이유·영향 명시)", BLUE],
                 ["금지", "단층 물성을 14층에 그대로 ✗\n실험 전류 fitting ✗\n임의 crosstalk 지표 ✗", ORANGE]];
  items.forEach((it, i) => { const x = 0.6 + i * 4.15;
    card(s, x, 1.5, 3.9, 4.6);
    s.addShape(pres.ShapeType.rect, { x, y: 1.5, w: 3.9, h: 0.75, fill: { color: it[2] }, line: { color: it[2] } });
    s.addText(it[0], { x, y: 1.5, w: 3.9, h: 0.75, fontSize: 20, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText(it[1], { x: x + 0.25, y: 2.4, w: 3.4, h: 3.5, fontSize: 16, color: INK, margin: 0, valign: "top", paraSpaceAfter: 10 });
  });
  s.addText("raw 전위·밴드부터 본다 — 지표는 물리 근거가 생긴 뒤에", { x: 0.6, y: 6.3, w: 12.2, h: 0.45, fontSize: 15, color: GRAY, margin: 0, align: "center" });
}

// ---------- 5. 파라미터 ----------
{
  const s = pres.addSlide(); header(s, "STEP 1 · 값과 출처 (원문 대조 완료 · Γ 는 간접 확인)");
  const rows = [
    [hdr("항목"), hdr("값"), hdr("분류"), hdr("출처")],
    ["WSe₂ / h-BN / SiO₂ 두께", "9.1 / 30 / 300 nm", "[A]", "Jiao 2026 본문"],
    ["Source Pd/Au · Drain Ti/Au", "5/50 → 55 · 1/70 → 71 nm", "[A]", "Jiao 2026 본문"],
    ["채널 길이 L", "≈ 500 nm", "[A]", "Jiao 2026"],
    ["ε WSe₂ ⊥/∥ · h-BN ⊥/∥", "7.9/16.0 · 3.76/6.93 (bulk)", "[B]", "Laturia 2018, npj 2D Mater. Appl., Table 1·2"],
    ["E_g · χ", "1.2 eV · 4.03 eV", "[B]", "McDonnell 2014 · Smyth 2017 · Wickramaratne 2014"],
    ["m* (e 종/횡, h)", "0.489 / 0.643 / 0.997 m₀ (bulk)", "[B]", "Wickramaratne 2014, J. Chem. Phys."],
    ["φ_Bn Source (Pd) · Drain (Au)", "0.22 · 0.53 eV", "[B]", "Jang 2022 Fig. 3f · Smyth 2017 본문"],
    ["E (WSe₂ 다층) · Γ", "167 GPa · 0.45 J/m² (차용)", "[B]", "Zhang 2016 APL · Koenig 2011"],
    ["패드 · TG overhang · 쐐기 ε", "1000 · 300/300 nm · 1", "[C]", "이유: fringe 3배 밖 · 대칭 · 하한"],
    ["도핑 · 고정전하 · μ", "0 · 0 · 100 cm²/Vs", "[C]", "값 없음, fitting 금지 → 절대 전류는 비교 안 함"],
  ];
  s.addTable(rows, { x: 0.5, y: 1.3, w: 12.33, colW: [3.3, 3.4, 0.9, 4.73], rowH: 0.48, ...TBL(14) });
  s.addText("14층 = 9.1 nm ÷ 0.652 nm → bulk 값 사용 (1층→bulk 변화 5 %, 포화)", { x: 0.5, y: 6.65, w: 12.3, h: 0.4, fontSize: 13, color: GRAY, margin: 0 });
}

// ---------- 6. 구조 ----------
{
  const s = pres.addSlide(); header(s, "STEP 2 · 비대칭 구조 — 기준 config curve_el");
  fit(s, FIG("rfet_geometry_curve_el.png"), { x: 0.4, y: 1.2, w: 8.4, h: 5.7 }, 1.5);
  const rows = [
    [hdr("요소"), hdr("치수 nm"), hdr("분류")],
    ["Source (Pd/Au)", "두께 55, 박막 위", "[A]"],
    ["Drain (Au/Ti)", "두께 71, 박막 아래", "[A]"],
    ["채널 L", "500 (S 모서리 ↔ D 벽)", "[A]/[C]"],
    ["WSe₂", "9.1 · 0→283 평평 · 283→500 S자", "[A]/역학"],
    ["h-BN", "30 · 곧은 판, 1.8° 기움", "[A]/역학"],
    ["TG", "−300 → 800 (대칭 300)", "[C]"],
    ["SiO₂ / BG", "300 / 선", "[A]"],
    ["빈 공간", "공기 ε = 1 (하한)", "[C]"],
  ];
  s.addTable(rows, { x: 9.0, y: 1.35, w: 3.9, colW: [1.3, 2.0, 0.6], rowH: 0.5, ...TBL(11.5) });
  s.addText("STEP 3·4 는 이 구조 + 비교군 4개로 계산 (다음 장) · STEP 5 전류는 구 구조 bridge", { x: 9.0, y: 6.1, w: 3.9, h: 0.7, fontSize: 11, color: GRAY, margin: 0 });
}

// ---------- 7. 경사 근거 ----------
{
  const s = pres.addSlide(); header(s, "STEP 2 · 경사 형상 : 에너지 최소화와 민감도 결과");
  fit(s, FIG("fig_ramp_shapes.png"), { x: 0.4, y: 1.1, w: 12.5, h: 3.5 }, 3.45);
  const rows = [
    [hdr("config"), hdr("경사"), hdr("TG→D 쪽"), hdr("TG→S 쪽"), hdr("BG→S 쪽"), hdr("BG→D 쪽"), hdr("비고")],
    [B("curve_el"), "S자 217 (에너지 최소)", B("0.35"), "0.07", "0.09", "0.009", "기준 · 변형률 4.1 % < 7.3 %"],
    ["line_el", "직선 217", "0.28", "0.07", "0.09", "0.012", "모양만 바꿈 → D 쪽 −20 %"],
    ["curve70", "S자 70", "0.24", "0.07", "0.09", "0.014", "Γ≈41 J/m² 필요, 변형률 40 %"],
    ["line70", "직선 70 (이전 가정)", "0.18", "0.07", "0.09", "0.020", "D 쪽 TG 효율 절반"],
    ["curve_el_eq", "S자 217, Source 71", "0.34", B("0.06"), "0.09", "0.010", "Source 두꺼우면 TG→S 번짐 −15 %"],
  ];
  s.addTable(rows, { x: 0.5, y: 4.65, w: 12.33, colW: [1.4, 2.4, 1.2, 1.2, 1.2, 1.2, 3.73], rowH: 0.3, ...TBL(11.5), align: "center" });
  s.addText("단위 V/V, 접합 10 nm · Source 쪽은 모양과 무관 · Drain 쪽 TG 효율은 경사 모양에 2배까지 의존 · DEVSIM = FEM", { x: 0.5, y: 6.75, w: 12.3, h: 0.3, fontSize: 10.5, color: GRAY, margin: 0 });
}

// ---------- 8. 격자 ----------
{
  const s = pres.addSlide(); header(s, "STEP 2 · 실제 계산 격자 (gmsh)");
  fit(s, FIG("fig_mesh_curve_el.png"), { x: 0.4, y: 1.15, w: 9.3, h: 5.9 }, 1.93);
  card(s, 9.9, 1.4, 3.0, 4.9);
  s.addText([B("크기 규칙 4개"), { text: "\n\n박막 두께 ≥ 4층\n접합 근처 0.57 nm\n공기 쐐기 ≥ 3요소\n성장 30 %, 최대 50 nm\n\n", options: {} }, B("수렴 검사"), { text: "\n4 → 6 → 8층\n변화 < 0.1 %", options: {} }],
    { x: 10.1, y: 1.5, w: 2.7, h: 4.7, fontSize: 14, color: INK, margin: 0, valign: "top" });
}

// ---------- 9. STEP 3 결과 ----------
{
  const s = pres.addSlide(); header(s, "STEP 3 · 정전기 : 게이트 1 V 가 채널 어디를 움직이나");
  fit(s, FIG("fig_step3_profiles_slope.png"), { x: 0.4, y: 1.1, w: 12.5, h: 4.1 }, 2.62);
  const rows = [
    [hdr("1 V 당"), hdr("Source 쪽"), hdr("Drain 쪽")],
    ["TG", "0.07", B("0.35")],
    ["BG", B("0.09"), "0.009"],
  ];
  s.addTable(rows, { x: 0.8, y: 5.5, w: 5.2, colW: [1.4, 1.9, 1.9], rowH: 0.45, ...TBL(15), align: "center" });
  card(s, 6.5, 5.5, 6.4, 1.4);
  s.addText([B("TG → Drain 쪽 5배"), { text: "\n", options: {} }, B("BG → Source 쪽 10배"), { text: "\n\n기준 curve_el · 단위 V/V, 접합에서 10 nm\nDEVSIM(점) = FEM(선) · 5개 구조 모두 같은 패턴", options: { color: GRAY, fontSize: 12 } }],
    { x: 6.7, y: 5.55, w: 6.1, h: 1.3, fontSize: 14, color: NAVY, margin: 0, valign: "top" });
}

// ---------- 10. STEP 3 지도 ----------
{
  const s = pres.addSlide(); header(s, "STEP 3 · 전위 응답 지도 — 금속이 전기장을 가린다");
  fit(s, FIG("fig_step3_maps_curve_el.png"), { x: 0.4, y: 1.15, w: 12.5, h: 5.9 }, 1.5);
}

// ---------- 11. STEP 4 밴드 ----------
{
  const s = pres.addSlide(); header(s, "STEP 4 · 밴드 : 어느 게이트가 어느 쪽을 n/p 로 만드나");
  fit(s, FIG("fig_step4_bands_slope.png"), { x: 0.4, y: 1.15, w: 8.6, h: 5.9 }, 1.415);
  const rows = [
    [hdr("E_c − E_F (eV)"), hdr("S 쪽"), hdr("D 쪽")],
    ["0 V", "0.29", "0.55"],
    ["TG −5 V", "0.48", B("1.05")],
    ["BG −60 → +60", B("1.02 → 0.16"), "0.68 → 0.44"],
  ];
  s.addTable(rows, { x: 9.2, y: 1.5, w: 3.7, colW: [1.5, 1.1, 1.1], rowH: 0.55, ...TBL(13), align: "center" });
  card(s, 9.2, 4.0, 3.7, 2.4);
  s.addText([B("TG → Drain 쪽만 p 형"), { text: "\n", options: {} }, B("BG → Source 쪽만 재구성"), { text: "\n\n기준 curve_el (5개 구조 모두 같은 패턴)\n장벽 0.22/0.53 (다른 시료) → 대조군 0.6/0.6 도 같은 패턴", options: { color: GRAY, fontSize: 12 } }],
    { x: 9.35, y: 4.1, w: 3.4, h: 2.2, fontSize: 15, color: NAVY, margin: 0, valign: "top" });
}

// ---------- 12. STEP 5 전류 ----------
{
  const s = pres.addSlide(); header(s, "STEP 5 · 전류 (드리프트–확산, 터널링 없음)");
  cap(s, "문헌 장벽 lit (S 0.22 / D 0.53 eV)", 0.5, 1.15, 6.2, 14, NAVY, true);
  cap(s, "대조군 equal_mid (0.60 / 0.60 eV)", 6.8, 1.15, 6.2, 14, ORANGE, true);
  fit(s, FIG("rfet_idvbg_bridge_perp_lit.png"), { x: 0.4, y: 1.6, w: 6.2, h: 2.7 }, 2.73);
  fit(s, FIG("rfet_idvbg_bridge_perp_equal_mid.png"), { x: 6.7, y: 1.6, w: 6.2, h: 2.7 }, 2.73);
  const rows = [
    [hdr("조건"), hdr("lit"), hdr("equal_mid"), hdr("뜻")],
    ["n형 · TG +5", "BG 가 10⁻²⁰ → 10⁻⁴ (on/off 10¹⁵)", "10⁻²⁰ → 10⁻⁸", "BG 가 Source 접합을 켠다"],
    ["n형 · TG −5", "BG 무관 바닥 10⁻¹¹", "바닥 10⁻¹⁰", "TG 가 Drain 을 끄면 BG 로는 못 켠다"],
    ["p형 · TG −5", "정공 10⁻¹⁶ ≈ 0", "정공 10⁻⁹, BG 가 끔", "정공 장벽 0.98 eV → 열전자로 못 넘음 → 터널링 필요"],
  ];
  s.addTable(rows, { x: 0.5, y: 4.5, w: 12.33, colW: [1.7, 3.6, 2.4, 4.63], rowH: 0.5, ...TBL(13) });
  s.addText("구 구조 bridge 로 계산 (curve_el 재계산 예정; 정전기 차이 D 쪽 5 %) · μ = 100 cm²/Vs 가정 → on/off 와 모양만 · 전류 보존 6×10⁻⁵", { x: 0.5, y: 6.6, w: 12.3, h: 0.4, fontSize: 12, color: GRAY, margin: 0 });
}

// ---------- 13. 검증 ----------
{
  const s = pres.addSlide(); header(s, "검증 : 왜 이 숫자를 믿나");
  fit(s, FIG("fig_mesh_convergence_simple.png"), { x: 0.4, y: 1.3, w: 6.6, h: 5.4 }, 1.71);
  const rows = [
    [hdr("검증"), hdr("결과")],
    ["해석해 (2층 평행판)", "FEM 일치"],
    ["DEVSIM(유한체적) vs 직접 짠 FEM", "전위 소수 셋째 자리 · 밴드 둘째 자리 일치"],
    ["격자 4 → 6 → 8", "ψ ≤ 0.001 V/V · E_c ≤ 5 meV"],
    ["기하 검사 10가지", "모든 config 통과"],
    ["전류 보존", "6×10⁻⁵"],
    ["텐서 유전율 (FEM)", "스칼라 대비 10–15 % → 결론 불변"],
  ];
  s.addTable(rows, { x: 7.2, y: 1.5, w: 5.7, colW: [2.6, 3.1], rowH: 0.6, ...TBL(13) });
}

// ---------- 13b. 가정과 한계 ----------
{
  const s = pres.addSlide(); header(s, "가정과 한계 — 결과를 읽을 때 전제");
  const rows = [
    [hdr("가정"), hdr("왜"), hdr("영향 · 확인")],
    ["2D 단면 (폭 균일)", "3D 비용, 폭 수치 없음", "폭 가장자리 fringe 누락 · 미확인"],
    ["ε 스칼라 (⊥)", "DEVSIM 구조", "텐서 대비 10–15 % 과대 · FEM 으로 정량화"],
    ["장벽 0.22 / 0.53 (다른 시료)", "동일 소자 값 없음", "절대 E_c ±0.2 eV · 대조군 0.6/0.6 로 분리"],
    ["φ_Bp = E_g − φ_Bn", "핀닝 준위 하나 가정", "p형 전류 결정 · 터널링과 함께 재검토"],
    ["도핑·고정전하·트랩 0, Φ_m flat-band", "값 없음, fitting 금지", "V_th 위치는 비교 대상 아님 (평행이동)"],
    ["열전자 DD 만 (터널링 없음)", "STEP 5 단계", "p형 과소 → WKB 다음"],
    ["μ = 100 cm²/Vs", "가정", "전류 절대값 ∝ μ → on/off·모양만"],
    ["쐐기 ε = 1, 패드 1000, TG 300/300", "하한·경계·대칭", "민감도 예정 (ε 3, 패드 2000)"],
    ["경사 = 에너지 최소화 (Γ 차용)", "Fig. S2 없음", "5개 형상 비교: S 쪽 불변, D 쪽 TG 효율 0.18–0.35"],
  ];
  s.addTable(rows, { x: 0.5, y: 1.3, w: 12.33, colW: [3.6, 3.2, 5.53], rowH: 0.52, ...TBL(13.5) });
}

// ---------- 14. 정리·다음 ----------
{
  const s = pres.addSlide(); header(s, "정리와 다음 단계");
  const rows = [
    [hdr("단계"), hdr("결과"), hdr("상태")],
    ["STEP 1 값", "20개 값 전부 출처·원문 대조", "완료"],
    ["STEP 2 구조", "비대칭 + 판 h-BN + 경사 217 nm (에너지 최소화) · 형상 민감도 5종", "완료"],
    ["STEP 3 정전기", "TG→D 0.35 / S 0.07 · BG→S 0.09 / D 0.009 (curve_el)", "완료 · 검증됨"],
    ["STEP 4 밴드", "TG 는 Drain 쪽만, BG 는 Source 쪽만 재구성", "완료"],
    ["STEP 5 전류", "n형 선택적 제어 확인 · p형은 터널링 필요 (bridge)", "DD 완료 · curve_el 재계산 · WKB"],
    ["STEP 6 scaling", "L 500 → 300 → 200 → 100 nm, fringe 추적", "예정"],
  ];
  s.addTable(rows, { x: 0.5, y: 1.4, w: 12.33, colW: [2.2, 7.3, 2.83], rowH: 0.6, ...TBL(15) });
  s.addText("GitHub  jiseonyang-9070/rfet  — 코드 · 문서 · 그림 · 로그 전부", { x: 0.5, y: 6.3, w: 12.3, h: 0.45, fontSize: 13, color: GRAY, margin: 0, align: "center" });
}

(async () => { const out = "/home/claude/rfet_ppt/RFET_progress_INU.pptx"; await pres.writeFile({ fileName: out }); console.log("written", out); })();
