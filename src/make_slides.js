// WSe2 RFET 발표용 덱 — 글자는 최소, 그림/표/차트 중심
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require("/root/.claude/skills/synced/113d6e39-a176-431c-9ca6-39995820802c_4d635005-59e9-4798-8614-4ba581775b9d/pptx/scripts/apply_theme.js");

const FIG = (n) => path.join("/home/claude/rfet_repo/figures", n);

const THEME = {
  name: "RFET Violet",
  headFontFace: "Malgun Gothic",
  bodyFontFace: "Malgun Gothic",
  colors: {
    dk1: "1A1630",   // 잉크 (제목 슬라이드 배경, 본문 글자)
    lt1: "FFFFFF",
    dk2: "4F4B63",   // 보조 글자
    lt2: "F3F1F8",   // 카드 배경 (연보라 회색)
    accent1: "2A78D6", // 파랑: TG, bridge
    accent2: "EB6834", // 주황: BG, sag45
    accent3: "6250D6", // 보라: WSe2
    accent4: "1BAF7A", // 민트: 검증 OK
    accent5: "EDA100", // 금: 금속
    accent6: "E34948", // 빨강: junction
    hlink: "2A78D6", folHlink: "6250D6",
  },
};
const H = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "WSe2 RFET electrostatics";
const C = pres.SchemeColor;
const W = 13.333, Hh = 7.5;

// ---- 레이아웃 ----
pres.defineSlideMaster({
  title: "DARK", background: { color: H.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.3, w: 11.7, h: 1.6, fontSize: 44, bold: true, color: H.lt1, align: "left", valign: "bottom", margin: 0 } } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.05, w: 11.7, h: 1.6, fontSize: 22, color: "CFCBE6", align: "left", valign: "top", margin: 0 } } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: H.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 11.0, h: 0.9, fontSize: 32, bold: true, color: H.dk1, align: "left", valign: "middle", margin: 0 } } },
    { text: { text: "WSe₂ RFET · DEVSIM", options: { x: 0.6, y: 7.0, w: 5, h: 0.35, fontSize: 10, color: H.dk2, margin: 0 } } },
    { slideNumber: { x: 12.2, y: 7.0, w: 0.6, h: 0.35, fontSize: 10, color: H.dk2, align: "right" } },
  ],
});

// 단계 배지 (오른쪽 위)
function badge(slide, text, color) {
  slide.addShape(pres.ShapeType.roundRect, { x: 11.75, y: 0.45, w: 1.0, h: 0.6, fill: { color }, line: { color }, rectRadius: 0.12, objectName: "step badge" });
  slide.addText(text, { x: 11.75, y: 0.45, w: 1.0, h: 0.6, fontSize: 14, bold: true, color: H.lt1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "step badge text" });
}
function content(title, step, color) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: step ? step : "소개" });
  s.addText(title, { placeholder: "title" });
  if (step) badge(s, step, color || H.accent3);
  return s;
}
// 그림을 상자 안에 비율 유지로 넣기
function fitImage(slide, file, box, ratio, name) {
  let w = box.w, h = w / ratio;
  if (h > box.h) { h = box.h; w = h * ratio; }
  const x = box.x + (box.w - w) / 2, y = box.y + (box.h - h) / 2;
  slide.addImage({ path: file, x, y, w, h, objectName: name || path.basename(file) });
}
function card(slide, x, y, w, h, name) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: H.lt2 }, line: { color: H.lt2 }, rectRadius: 0.12, objectName: name || "card" });
}
function stat(slide, x, y, w, big, label, color, fs = 48) {
  slide.addText(big, { x, y, w, h: 0.95, fontSize: fs, bold: true, color, align: "center", valign: "bottom", margin: 0, isTextBox: true, objectName: "stat " + label });
  slide.addText(label, { x, y: y + 0.95, w, h: 0.5, fontSize: 15, color: H.dk2, align: "center", valign: "top", margin: 0, isTextBox: true, objectName: "stat label " + label });
}
function caption(slide, text, x, y, w) {
  slide.addText(text, { x, y, w, h: 0.4, fontSize: 13, color: H.dk2, margin: 0, isTextBox: true, objectName: "caption" });
}
const TBL = (fs = 16) => ({ fontSize: fs, color: H.dk1, border: { type: "solid", pt: 0.75, color: "D9D6E6" }, valign: "middle", margin: 0.08 });
function hdr(t, color) { return { text: t, options: { bold: true, color: H.lt1, fill: { color: color || H.dk1 }, align: "center" } }; }

// 공통 차트 옵션
const chartBase = {
  catAxisLabelColor: H.dk1, valAxisLabelColor: H.dk2, catAxisLabelFontSize: 14, valAxisLabelFontSize: 12,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", titleFontFace: "+mn-lt",
  valGridLine: { color: "E4E3DF", size: 0.5 }, catGridLine: { style: "none" },
  showValue: true, dataLabelFontSize: 13, dataLabelColor: H.dk1, dataLabelPosition: "outEnd",
  showLegend: true, legendPos: "t", legendFontSize: 13, legendColor: H.dk1,
  showTitle: false,
};

// =====================================================================
pres.addSection({ title: "소개" });
// 1. 표지
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "소개" });
  s.addText("WSe₂ RFET 정전기 모델", { placeholder: "title" });
  s.addText([
    { text: "DEVSIM 독립 구현과 검증  ·  STEP 1 – 4", options: { breakLine: true } },
    { text: "기준 논문: Jiao et al., Appl. Phys. Lett. 128, 263504 (2026)", options: { fontSize: 16, color: "9A95B8" } },
  ], { placeholder: "body" });
  fitImage(s, FIG("fig_schematic_bridge.png"), { x: 8.0, y: 0.5, w: 4.9, h: 2.6 }, 1.74, "schematic");
}

// 2. 연구 질문
{
  const s = content("연구 질문: 두 게이트가 서로 다른 접합부를 제어하는가", null);
  fitImage(s, FIG("fig_schematic_bridge.png"), { x: 0.6, y: 1.45, w: 7.6, h: 4.2 }, 1.74, "schematic");
  // 오른쪽: 두 메커니즘 카드
  card(s, 8.6, 1.5, 4.15, 1.75, "card BG");
  s.addText([{ text: "Back Gate → Source", options: { bold: true, color: H.accent2, fontSize: 22, breakLine: true } },
             { text: "Drain 금속이 BG 전기장을 가림", options: { fontSize: 15, color: H.dk2 } }],
    { x: 8.85, y: 1.6, w: 3.7, h: 1.55, valign: "middle", margin: 0, isTextBox: true, objectName: "mech BG" });
  card(s, 8.6, 3.45, 4.15, 1.75, "card TG");
  s.addText([{ text: "Top Gate → Drain", options: { bold: true, color: H.accent1, fontSize: 22, breakLine: true } },
             { text: "Source 금속이 TG 전기장을 가림", options: { fontSize: 15, color: H.dk2 } }],
    { x: 8.85, y: 3.55, w: 3.7, h: 1.55, valign: "middle", margin: 0, isTextBox: true, objectName: "mech TG" });
  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 5.9, w: 12.15, h: 0.9, fill: { color: H.dk1 }, line: { color: H.dk1 }, rectRadius: 0.1, objectName: "question bar" });
  s.addText("최종 질문 — 채널 길이를 줄이면 이 선택적 제어는 어디서부터 깨지는가?  (현재 L = 500 nm)",
    { x: 0.8, y: 5.9, w: 11.8, h: 0.9, fontSize: 20, bold: true, color: H.lt1, valign: "middle", margin: 0, isTextBox: true, objectName: "question" });
}

// 3. 접근 순서 (사슬)
{
  const s = content("왜 전류가 아니라 정전기(electrostatics)부터 보는가", null);
  const steps = [
    ["전극 배치", "geometry", H.accent3, "STEP 2"],
    ["전기장이\n어디 닿는가", "ρ = 0 Poisson", H.accent1, "STEP 3"],
    ["밴드가\n어디서 휘는가", "n, p + Schottky", H.accent1, "STEP 4"],
    ["장벽 폭", "WKB", "B8B4CC", "STEP 5"],
    ["터널링 전류", "Landauer", "B8B4CC", "STEP 6+"],
  ];
  const x0 = 0.6, bw = 2.25, gap = 0.22, y = 2.1;
  steps.forEach((st, i) => {
    const x = x0 + i * (bw + gap);
    s.addShape(pres.ShapeType.roundRect, { x, y, w: bw, h: 1.9, fill: { color: st[2] }, line: { color: st[2] }, rectRadius: 0.15, objectName: "chain " + i });
    s.addText(st[0], { x, y: y + 0.15, w: bw, h: 1.1, fontSize: 20, bold: true, color: H.lt1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "chain t " + i });
    s.addText(st[1], { x, y: y + 1.25, w: bw, h: 0.5, fontSize: 14, color: H.lt1, align: "center", margin: 0, isTextBox: true, objectName: "chain s " + i });
    s.addText(st[3], { x, y: y + 2.0, w: bw, h: 0.45, fontSize: 16, bold: true, color: i < 3 ? H.dk1 : "B8B4CC", align: "center", margin: 0, isTextBox: true, objectName: "chain step " + i });
    if (i < steps.length - 1) s.addShape(pres.ShapeType.rightArrow, { x: x + bw + 0.02, y: y + 0.75, w: gap - 0.04, h: 0.4, fill: { color: H.dk2 }, line: { color: H.dk2 }, objectName: "arrow " + i });
  });
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: 1.65, w: 3 * bw + 2 * gap, h: 0.08, fill: { color: H.accent4 }, line: { color: H.accent4 }, objectName: "done bar" });
  s.addText("완료 — 파라미터가 유전율·밴드값만", { x: 0.6, y: 1.25, w: 7.2, h: 0.4, fontSize: 15, bold: true, color: H.accent4, margin: 0, isTextBox: true, objectName: "done label" });
  s.addText("다음 — 이동도·터널링 질량 등 불확실 값 등장", { x: 0.6 + 3 * (bw + gap), y: 1.25, w: 5, h: 0.4, fontSize: 15, bold: true, color: "8E8AA6", margin: 0, isTextBox: true, objectName: "next label" });
  card(s, 0.6, 5.0, 12.15, 1.6, "why card");
  s.addText([
    { text: "구조 때문인지, 파라미터 때문인지를 분리하려면", options: { fontSize: 20, color: H.dk1, bold: true, breakLine: true } },
    { text: "불확실한 값이 가장 적은 단계부터 쌓아 올린다", options: { fontSize: 20, color: H.dk1 } },
  ], { x: 0.9, y: 5.0, w: 11.6, h: 1.6, valign: "middle", margin: 0, isTextBox: true, objectName: "why text" });
}

// =====================================================================
pres.addSection({ title: "STEP 1" });
{
  const s = content("STEP 1 — 모든 숫자에 출처를 붙인다", "STEP 1", H.accent3);
  const rows = [
    [hdr("분류"), hdr("뜻"), hdr("항목 (값)")],
    [{ text: "[A] 논문값", options: { bold: true, color: H.accent3 } }, "Jiao 2026 본문", "WSe₂ 9.1 nm · h-BN 30 nm · SiO₂ 300 nm · Drain Au/Ti 71 nm · Source Pd/Au 55 nm · L ≈ 500 nm"],
    [{ text: "[B] 문헌값", options: { bold: true, color: H.accent1 } }, "다른 1차 논문 (DOI·표 위치)", "ε (Laturia 2018) · E_g 1.2 eV, χ 4.03 eV (McDonnell 2014) · m* (Wickramaratne 2014) · φ_Bn Pd 0.22 / Au 0.53 eV (Jang 2022, Smyth 2017)"],
    [{ text: "[C] 모델 가정", options: { bold: true, color: H.accent2 } }, "문헌에 없어 정해야 한 값", "패드 1000 nm · TG overhang 300 nm · h-BN 단차 형상 · 빈 공간 = 공기 · T = 300 K · Φ_m flat-band"],
    [{ text: "근거 없음", options: { bold: true, color: H.dk2 } }, "값을 넣지 않음", "h-BN/WSe₂ 접착에너지 · 경사 실제 형상 (Fig. S2) · vdW Au 장벽 · TG 금속"],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 12.15, colW: [2.1, 2.9, 7.15], rowH: [0.55, 1.0, 1.15, 1.0, 0.95], ...TBL(15), objectName: "param table" });
  caption(s, "원칙: 단층 값을 다층(14층)에 쓰지 않음 · 실험 전류 fitting 금지 · 임의 지표 금지", 0.6, 6.45, 12);
}

// =====================================================================
pres.addSection({ title: "STEP 2" });
// 5. 좌표계 / 구조
{
  const s = content("STEP 2 — 단면 구조 (실제 치수)", "STEP 2", H.accent3);
  fitImage(s, FIG("fig_geometry_bridge.png"), { x: 0.5, y: 1.35, w: 8.5, h: 5.5 }, 1.49, "geometry");
  const items = [
    ["x = 0", "source junction", H.accent6],
    ["x = L = 500", "drain junction", H.accent6],
    ["y = 0", "SiO₂ 윗면", H.dk2],
    ["경사 8°", "WSe₂ 가 Drain 위로", H.accent3],
    ["빈 공간 2곳", "공기 (ε = 1)", H.dk2],
  ];
  items.forEach((it, i) => {
    const y = 1.5 + i * 1.05;
    card(s, 9.3, y, 3.45, 0.9, "coord card " + i);
    s.addText([{ text: it[0], options: { bold: true, color: it[2], fontSize: 18, breakLine: true } }, { text: it[1], options: { fontSize: 14, color: H.dk2 } }],
      { x: 9.5, y, w: 3.1, h: 0.9, valign: "middle", margin: 0, isTextBox: true, objectName: "coord " + i });
  });
}
// 6. h-BN 형상 비교
{
  const s = content("STEP 2 — h-BN 이 Source 단차를 넘는 모양: 두 극단", "STEP 2", H.accent3);
  fitImage(s, FIG("fig_geometry_bridge.png"), { x: 0.5, y: 1.9, w: 6.1, h: 4.0 }, 1.49, "bridge");
  fitImage(s, FIG("fig_geometry_sag45.png"), { x: 6.75, y: 1.9, w: 6.1, h: 4.0 }, 1.49, "sag45");
  s.addText("bridge (다리형) — baseline", { x: 0.5, y: 1.4, w: 6.1, h: 0.45, fontSize: 20, bold: true, color: H.accent1, margin: 0, isTextBox: true, objectName: "lbl bridge" });
  s.addText("sag45 (처짐형) — 비물리적 하한", { x: 6.75, y: 1.4, w: 6.1, h: 0.45, fontSize: 20, bold: true, color: H.accent2, margin: 0, isTextBox: true, objectName: "lbl sag" });
  card(s, 0.5, 6.0, 6.1, 1.0, "elastic card");
  s.addText([{ text: "탄성 추정  ℓ = (3Dh²/Γ)^¼ ≈ 450 nm ≈ L", options: { fontSize: 18, bold: true, color: H.dk1, breakLine: true } },
             { text: "E(h-BN) 0.86 TPa (Falin 2017)  →  박편은 채널 위에 걸침", options: { fontSize: 13, color: H.dk2 } }],
    { x: 0.7, y: 6.0, w: 5.8, h: 1.0, valign: "middle", margin: 0, isTextBox: true, objectName: "elastic text" });
  card(s, 6.75, 6.0, 6.1, 1.0, "sag card");
  s.addText([{ text: "곡률반경 40 nm → 표면 변형률 36 %", options: { fontSize: 18, bold: true, color: H.dk1, breakLine: true } },
             { text: "물리적으로 불가능 → 민감도 비교용으로만 사용", options: { fontSize: 13, color: H.dk2 } }],
    { x: 6.95, y: 6.0, w: 5.8, h: 1.0, valign: "middle", margin: 0, isTextBox: true, objectName: "sag text" });
}
// 7. Mesh
{
  const s = content("STEP 2 — Mesh(계산 격자): 어디를 왜 촘촘히", "STEP 2", H.accent3);
  fitImage(s, FIG("fig_mesh_size_rules_bridge.png"), { x: 0.5, y: 1.4, w: 7.9, h: 4.6 }, 1.75, "mesh rules");
  const rules = [
    ["1", "WSe₂ 두께 방향 4 요소", "2.3 nm"],
    ["2", "금속–WSe₂ 모서리 (특이점)", "0.57 nm"],
    ["3", "공기 쐐기 끝", "높이 방향 3 요소"],
    ["4", "TG 끝 fringe", "5 nm"],
  ];
  rules.forEach((r, i) => {
    const y = 1.45 + i * 0.95;
    s.addShape(pres.ShapeType.ellipse, { x: 8.8, y: y + 0.12, w: 0.55, h: 0.55, fill: { color: H.accent3 }, line: { color: H.accent3 }, objectName: "rule n " + i });
    s.addText(r[0], { x: 8.8, y: y + 0.12, w: 0.55, h: 0.55, fontSize: 16, bold: true, color: H.lt1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "rule num " + i });
    s.addText([{ text: r[1], options: { fontSize: 16, bold: true, color: H.dk1, breakLine: true } }, { text: r[2], options: { fontSize: 14, color: H.dk2 } }],
      { x: 9.5, y, w: 3.3, h: 0.8, valign: "middle", margin: 0, isTextBox: true, objectName: "rule " + i });
  });
  stat(s, 8.8, 5.35, 2.0, "25,658", "노드", H.dk1, 32);
  stat(s, 10.85, 5.35, 2.0, "49,700", "삼각형", H.dk1, 32);
  caption(s, "결과는 모서리 '그 점'이 아니라 10 / 25 / 50 nm 떨어진 점에서 읽는다 (모서리 값은 격자 의존)", 0.5, 6.3, 8);
}

// =====================================================================
pres.addSection({ title: "STEP 3" });
// 8. 전위 지도
{
  const s = content("STEP 3 — 게이트 1 V 의 전위 지도 (ρ = 0)", "STEP 3", H.accent1);
  fitImage(s, FIG("fig_step3_maps_bridge.png"), { x: 0.5, y: 1.3, w: 8.3, h: 5.6 }, 1.42, "maps");
  card(s, 9.1, 1.5, 3.65, 2.3, "map card 1");
  s.addText([{ text: "∂ψ/∂V_TG", options: { fontSize: 22, bold: true, color: H.accent1, breakLine: true } },
             { text: "Source 금속 아래로는\n거의 들어가지 못함", options: { fontSize: 15, color: H.dk2 } }],
    { x: 9.3, y: 1.5, w: 3.3, h: 2.3, valign: "middle", margin: 0, isTextBox: true, objectName: "map t1" });
  card(s, 9.1, 4.0, 3.65, 2.3, "map card 2");
  s.addText([{ text: "∂ψ/∂V_BG", options: { fontSize: 22, bold: true, color: H.accent2, breakLine: true } },
             { text: "Drain 금속 위로는\n거의 들어가지 못함", options: { fontSize: 15, color: H.dk2 } }],
    { x: 9.3, y: 4.0, w: 3.3, h: 2.3, valign: "middle", margin: 0, isTextBox: true, objectName: "map t2" });
}
// 9. 프로파일
{
  const s = content("STEP 3 — 채널 중앙선의 응답: DEVSIM(점) = FEM(선)", "STEP 3", H.accent1);
  fitImage(s, FIG("fig_step3_profiles.png"), { x: 0.4, y: 1.5, w: 12.5, h: 4.8 }, 2.63, "profiles");
  caption(s, "x = 0 source junction, x = L drain junction · 금색 띠 = 금속에 덮인 박막 구간 · 파랑 bridge, 주황 sag45", 0.6, 6.45, 12);
}
// 10. 결과 숫자 (차트)
{
  const s = content("STEP 3 — 각 게이트가 어느 접합부를 움직이는가", "STEP 3", H.accent1);
  s.addChart(pres.ChartType.bar, [
    { name: "Source 쪽 (10 nm)", labels: ["Top Gate", "Back Gate"], values: [0.078, 0.079] },
    { name: "Drain 쪽 (10 nm)", labels: ["Top Gate", "Back Gate"], values: [0.335, 0.008] },
  ], { x: 0.5, y: 1.4, w: 7.6, h: 5.4, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60,
       chartColors: [H.accent6, H.accent5], valAxisMinVal: 0, valAxisMaxVal: 0.4, valAxisTitle: "채널 전위 변화 (V per V)", showValAxisTitle: true, valAxisTitleFontSize: 13, valAxisTitleColor: H.dk2, valAxisTitleFontFace: "+mn-lt",
       dataLabelFormatCode: "0.000", ...chartBase });
  stat(s, 8.6, 1.6, 4.0, "4.3 ×", "TG: drain 쪽이 source 쪽보다", H.accent1);
  stat(s, 8.6, 3.5, 4.0, "10 ×", "BG: source 쪽이 drain 쪽보다", H.accent2);
  card(s, 8.6, 5.4, 4.0, 1.3, "step3 concl");
  s.addText("정전기만으로 논문 메커니즘 재현", { x: 8.8, y: 5.4, w: 3.6, h: 1.3, fontSize: 18, bold: true, color: H.dk1, valign: "middle", margin: 0, isTextBox: true, objectName: "s3 concl" });
}
// 11. 민감도
{
  const s = content("STEP 3 — 단순화와 가정의 영향", "STEP 3", H.accent1);
  s.addChart(pres.ChartType.bar, [
    { name: "ε⊥ 스칼라 (DEVSIM 기준)", labels: ["TG → source", "TG → drain", "BG → source"], values: [0.078, 0.336, 0.080] },
    { name: "ε 텐서 (FEM)", labels: ["TG → source", "TG → drain", "BG → source"], values: [0.073, 0.291, 0.068] },
  ], { x: 0.5, y: 1.9, w: 6.0, h: 4.4, barDir: "col", barGrouping: "clustered", barGapWidthPct: 50,
       chartColors: [H.accent3, "B9A7E6"], valAxisMinVal: 0, valAxisMaxVal: 0.45, dataLabelFormatCode: "0.000", ...chartBase });
  s.addChart(pres.ChartType.bar, [
    { name: "bridge", labels: ["TG → source", "TG → drain", "BG → source"], values: [0.078, 0.336, 0.080] },
    { name: "sag45", labels: ["TG → source", "TG → drain", "BG → source"], values: [0.170, 0.377, 0.056] },
  ], { x: 6.85, y: 1.9, w: 6.0, h: 4.4, barDir: "col", barGrouping: "clustered", barGapWidthPct: 50,
       chartColors: [H.accent1, H.accent2], valAxisMinVal: 0, valAxisMaxVal: 0.45, dataLabelFormatCode: "0.000", ...chartBase });
  s.addText("이방성 유전율 → 스칼라는 10–15 % 과대", { x: 0.5, y: 1.4, w: 6.0, h: 0.45, fontSize: 18, bold: true, color: H.dk1, margin: 0, isTextBox: true, objectName: "lbl eps" });
  s.addText("h-BN 형상 → TG→source 결합 2 배 (비물리적 극단)", { x: 6.85, y: 1.4, w: 6.0, h: 0.45, fontSize: 18, bold: true, color: H.dk1, margin: 0, isTextBox: true, objectName: "lbl shape" });
  caption(s, "두 경우 모두 차폐 비율(어느 쪽이 큰가)은 유지됨", 0.5, 6.45, 12);
}

// =====================================================================
pres.addSection({ title: "STEP 4" });
// 12. 모델
{
  const s = content("STEP 4 — WSe₂ 를 반도체로: 밴드 · 접점 장벽", "STEP 4", H.accent1);
  // 왼쪽: 에너지 기준 식 카드
  card(s, 0.6, 1.45, 6.0, 2.5, "energy card");
  s.addText([
    { text: "E_c = −ψ − χ,   E_v = E_c − E_g", options: { fontSize: 20, bold: true, color: H.dk1, breakLine: true } },
    { text: "접점  ψ = V − (φ_Bn + χ)", options: { fontSize: 18, color: H.dk1, breakLine: true } },
    { text: "게이트  ψ = V_g − Φ_m", options: { fontSize: 18, color: H.dk1, breakLine: true } },
    { text: "n = N_c ln(1 + e^η)  — 2D DOS × 14 층, 발산 없음", options: { fontSize: 15, color: H.dk2 } },
  ], { x: 0.85, y: 1.45, w: 5.5, h: 2.5, valign: "middle", margin: 0, isTextBox: true, paraSpaceAfter: 6, objectName: "energy text" });
  // 오른쪽: 장벽 표
  const rows = [
    [hdr("접점"), hdr("금속"), hdr("φ_Bn"), hdr("출처")],
    ["Source (위)", "Pd 증착", { text: "0.22 eV", options: { bold: true, color: H.accent3 } }, "Jang 2022"],
    ["Drain (아래)", "Au vdW", { text: "0.53 eV", options: { bold: true, color: H.accent3 } }, "Smyth 2017"],
    [{ text: "대조군", options: { bold: true } }, "S = D", { text: "0.60 / 0.60", options: { bold: true, color: H.accent2 } }, "금속 효과 제거"],
  ];
  s.addTable(rows, { x: 6.9, y: 1.45, w: 5.85, colW: [1.6, 1.3, 1.45, 1.5], rowH: 0.62, ...TBL(15), objectName: "barrier table" });
  // 아래: 파라미터 스탯
  stat(s, 0.6, 4.4, 3.0, "1.2 eV", "E_g (1.16–1.3)", H.dk1);
  stat(s, 3.7, 4.4, 3.0, "4.03 eV", "χ 전자친화도", H.dk1);
  stat(s, 6.8, 4.4, 3.0, "5.6e20", "N_c,eq (cm⁻³)", H.dk1);
  stat(s, 9.9, 4.4, 3.0, "V_DS = 0", "평형만 (전류 없음)", H.dk1);
  caption(s, "장벽값은 서로 다른 시료에서 온 값 → S/D 를 같게 둔 대조군으로 '금속 비대칭'과 '기하 차폐'를 분리", 0.6, 6.45, 12.2);
}
// 13. 밴드 다이어그램
{
  const s = content("STEP 4 — 밴드 다이어그램 (bridge, 문헌 장벽)", "STEP 4", H.accent1);
  fitImage(s, FIG("fig_step4_bands_bridge_lit.png"), { x: 0.3, y: 1.3, w: 12.7, h: 5.6 }, 1.37, "bands");
}
// 14. 결과 차트 (lit vs equal)
{
  const s = content("STEP 4 — 접합부 옆 10 nm 의 E_c − E_F: 원인은 기하", "STEP 4", H.accent1);
  const labels = ["TG −5 V", "TG +5 V", "BG +60 V", "BG −60 V"];
  s.addChart(pres.ChartType.bar, [
    { name: "Source 쪽", labels, values: [0.46, 0.23, 0.16, 1.03] },
    { name: "Drain 쪽", labels, values: [1.04, 0.18, 0.40, 0.72] },
  ], { x: 0.5, y: 1.9, w: 6.0, h: 4.4, barDir: "col", barGrouping: "clustered", barGapWidthPct: 50,
       chartColors: [H.accent6, H.accent5], valAxisMinVal: 0, valAxisMaxVal: 1.2, dataLabelFormatCode: "0.00", ...chartBase });
  s.addChart(pres.ChartType.bar, [
    { name: "Source 쪽", labels, values: [0.75, 0.46, 0.18, 1.05] },
    { name: "Drain 쪽", labels, values: [1.05, 0.18, 0.44, 0.76] },
  ], { x: 6.85, y: 1.9, w: 6.0, h: 4.4, barDir: "col", barGrouping: "clustered", barGapWidthPct: 50,
       chartColors: [H.accent6, H.accent5], valAxisMinVal: 0, valAxisMaxVal: 1.2, dataLabelFormatCode: "0.00", ...chartBase });
  s.addText("문헌 장벽  Pd 0.22 / Au 0.53 eV", { x: 0.5, y: 1.4, w: 6.0, h: 0.45, fontSize: 18, bold: true, color: H.dk1, margin: 0, isTextBox: true, objectName: "lbl lit" });
  s.addText("대조군  S = D = 0.60 eV", { x: 6.85, y: 1.4, w: 6.0, h: 0.45, fontSize: 18, bold: true, color: H.accent2, margin: 0, isTextBox: true, objectName: "lbl eq" });
  caption(s, "TG 는 drain 쪽을, BG 는 source 쪽을 크게 움직임 — 장벽을 같게 해도 같은 패턴  →  선택적 제어는 금속이 아니라 전극 기하에서 온다", 0.5, 6.45, 12.3);
}
// 15. 캐리어
{
  const s = content("STEP 4 — 캐리어 밀도: 어느 게이트가 어느 쪽을 n / p 로", "STEP 4", H.accent1);
  fitImage(s, FIG("fig_step4_carriers_bridge_lit.png"), { x: 0.4, y: 1.5, w: 12.5, h: 4.6 }, 2.86, "carriers");
  caption(s, "실선 n, 파선 p · 색 = 게이트 전압 (파랑 −, 주황 +) · 채널 중앙 n, p ≈ 10¹⁷–10¹⁸ cm⁻³", 0.6, 6.3, 12);
}

// =====================================================================
pres.addSection({ title: "검증" });
{
  const s = content("검증 — 독립적인 두 방법이 같은 답을 내는가", "검증", H.accent4);
  const ok = { text: "✔", options: { bold: true, color: H.accent4, align: "center", fontSize: 20 } };
  const rows = [
    [hdr("비교", H.accent4), hdr("결과", H.accent4), hdr("", H.accent4)],
    ["FEM  vs  2층 평행판 해석해", "6 × 10⁻¹⁴ V", ok],
    ["비선형 FEM  vs  1D shooting", "≤ 1.7 mV", ok],
    ["DEVSIM(유한체적)  vs  FEM(유한요소), STEP 3", "≤ 0.001 V/V", ok],
    ["DEVSIM  vs  FEM, STEP 4", "E_c 둘째자리, n/p 1 %", ok],
    ["Mesh 수렴  4 → 6 → 8", "ψ ≤ 0.001 V/V, E_c ≤ 5 meV", ok],
    ["DEVSIM  vs  평행판 해석해", "미실행 (run_check.py)", { text: "…", options: { color: H.dk2, align: "center", fontSize: 20 } }],
  ];
  s.addTable(rows, { x: 0.5, y: 1.4, w: 6.9, colW: [3.9, 2.4, 0.6], rowH: 0.68, ...TBL(14), objectName: "verify table" });
  fitImage(s, FIG("fig_mesh_convergence_bridge.png"), { x: 7.6, y: 1.4, w: 5.3, h: 4.9 }, 1.54, "convergence");
  caption(s, "같은 코드를 두 번 돌리는 것은 검증이 아니다 — 이산화 방식이 다른 solver 와 해석해로 교차 확인", 0.5, 6.45, 12.3);
}

// =====================================================================
pres.addSection({ title: "정리" });
{
  const s = content("어디까지 왔고, 무엇을 할 것인가", "정리", H.dk1);
  const done = [["STEP 1", "파라미터 출처 표"], ["STEP 2", "geometry 3종 · mesh"], ["STEP 3", "선형 정전기 — 차폐 재현"], ["STEP 4", "밴드 — 원인은 기하"], ["검증", "2 solver · 해석해 · 수렴"]];
  const next = [["STEP 5", "장벽 폭 · WKB 터널링"], ["STEP 6", "L = 500 → 50 nm scaling"], ["민감도", "쐐기 ε · 경사 형상 · E_g"]];
  s.addText("완료", { x: 0.6, y: 1.35, w: 6, h: 0.5, fontSize: 22, bold: true, color: H.accent4, margin: 0, isTextBox: true, objectName: "done hdr" });
  done.forEach((d, i) => {
    const y = 1.95 + i * 0.95;
    s.addShape(pres.ShapeType.ellipse, { x: 0.6, y: y + 0.15, w: 0.5, h: 0.5, fill: { color: H.accent4 }, line: { color: H.accent4 }, objectName: "done dot " + i });
    s.addText("✔", { x: 0.6, y: y + 0.15, w: 0.5, h: 0.5, fontSize: 14, bold: true, color: H.lt1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "done chk " + i });
    s.addText([{ text: d[0] + "  ", options: { bold: true, color: H.dk1, fontSize: 18 } }, { text: d[1], options: { fontSize: 16, color: H.dk2 } }],
      { x: 1.3, y, w: 5.3, h: 0.8, valign: "middle", margin: 0, isTextBox: true, objectName: "done " + i });
  });
  s.addText("다음", { x: 7.3, y: 1.35, w: 6, h: 0.5, fontSize: 22, bold: true, color: H.accent2, margin: 0, isTextBox: true, objectName: "next hdr" });
  next.forEach((d, i) => {
    const y = 1.95 + i * 1.3;
    s.addShape(pres.ShapeType.roundRect, { x: 7.3, y, w: 5.45, h: 1.1, fill: { color: H.lt2 }, line: { color: H.lt2 }, rectRadius: 0.12, objectName: "next card " + i });
    s.addText([{ text: d[0], options: { bold: true, color: H.accent2, fontSize: 18, breakLine: true } }, { text: d[1], options: { fontSize: 16, color: H.dk1 } }],
      { x: 7.55, y, w: 5.0, h: 1.1, valign: "middle", margin: 0, isTextBox: true, objectName: "next " + i });
  });
  caption(s, "미완 1건: DEVSIM 평행판 해석해 비교 (run_check.py)", 0.6, 6.7, 6);
}
// 마지막: 한 문장
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "정리" });
  s.addText("정전기만으로 차폐 메커니즘을 재현했고,\n선택적 제어의 원인이 전극 기하임을 분리했다", { placeholder: "title" });
  s.addText([
    { text: "남은 불확실성: h-BN 단차 형상 · 접점 장벽값  →  극단값 민감도에서 결론 유지", options: { breakLine: true } },
    { text: "github.com/jiseonyang-9070/rfet", options: { fontSize: 16, color: "9A95B8" } },
  ], { placeholder: "body" });
}

(async () => {
  const out = "/home/claude/rfet_ppt/WSe2_RFET_electrostatics.pptx";
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("written", out);
})();
