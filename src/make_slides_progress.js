// 진행 보고 발표용 (INU 스타일). 글자 최소·크게, 수식은 이미지(eq/*.png, matplotlib mathtext), 이론 페이지 분리.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const FIG = (n) => "/home/claude/rfet_repo/figures/" + n;
const MEDIA = "/tmp/claude-0/-home-claude/23b40f53-557b-5ad1-805e-4e71c03a7588/scratchpad/prev/x/ppt/media/";
const EQD = "/home/claude/rfet_ppt/eq/";
const EQI = JSON.parse(fs.readFileSync(EQD + "index.json", "utf8"));
const NAVY = "1F3A8A", BLUE = "2A78D6", GOLD = "F2B134", INK = "1A1A1A", GRAY = "5E6470", LT = "F3F5FA", LINE = "D6DAE6";
const ORANGE = "EB6834", GREEN = "1BAF7A", RED = "E34948";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: "Malgun Gothic", bodyFontFace: "Malgun Gothic" };

function header(s, title) {
  s.background = { color: "FFFFFF" };
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: NAVY }, line: { color: NAVY } });
  s.addText(title, { x: 0.5, y: 0.25, w: 10.6, h: 0.75, fontSize: 26, bold: true, color: NAVY, margin: 0, valign: "middle" });
  s.addShape(pres.ShapeType.line, { x: 0.5, y: 1.02, w: 12.33, h: 0, line: { color: NAVY, width: 1.5 } });
  s.addText("INU", { x: 11.55, y: 0.22, w: 1.0, h: 0.5, fontSize: 24, bold: true, color: NAVY, margin: 0, align: "right" });
  s.addShape(pres.ShapeType.line, { x: 12.0, y: 0.3, w: 0.55, h: 0.0, line: { color: GOLD, width: 3 }, rotate: -35 });
  s.addText("인천대학교", { x: 11.3, y: 0.68, w: 1.3, h: 0.25, fontSize: 9, color: GRAY, margin: 0, align: "right" });
  s.addText("WSe₂ RFET · DEVSIM", { x: 0.5, y: 7.1, w: 5, h: 0.25, fontSize: 9, color: GRAY, margin: 0 });
  s.slideNumber = { x: 12.4, y: 7.1, w: 0.5, h: 0.25, fontSize: 9, color: GRAY, align: "right" };
}
function fit(s, file, box, ratio) { let w = box.w, h = w / ratio; if (h > box.h) { h = box.h; w = h * ratio; }
  s.addImage({ path: file, x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h }); }
// 수식 이미지: 높이 h(인치) 기준, 왼쪽 정렬, 폭 제한
function eq(s, name, x, y, h, maxW) { const r = EQI[name].ratio; let hh = h, w = h * r; if (maxW && w > maxW) { w = maxW; hh = w / r; }
  s.addImage({ path: EQD + name + ".png", x, y, w, h: hh }); return hh; }

// 아래첨자/위첨자: "E_c", "φ_Bn", "ψ_TG" (한 글자 기호 + _) → subscript run,  "Γ^−¼" → superscript run
function S(t, extra = {}) {
  if (typeof t !== "string" || !/[_^]/.test(t)) return t;
  const re = /(^|[^A-Za-z0-9])([A-Za-zΦφψχεμηΓ])_([A-Za-z0-9]+)|\^([^\s),]+)/g;
  const runs = []; let last = 0, m;
  while ((m = re.exec(t)) !== null) {
    if (m[4] !== undefined) {                     // 위첨자
      if (m.index > last) runs.push({ text: t.slice(last, m.index), options: { ...extra } });
      runs.push({ text: m[4], options: { ...extra, superscript: true } });
    } else {
      const pre = t.slice(last, m.index) + m[1] + m[2];
      if (pre) runs.push({ text: pre, options: { ...extra } });
      runs.push({ text: m[3], options: { ...extra, subscript: true } });
    }
    last = m.index + m[0].length;
  }
  if (last < t.length) runs.push({ text: t.slice(last), options: { ...extra } });
  return runs;
}
const T = (rows) => rows.map(r => r.map(c => (typeof c === "string" && /[_^]/.test(c)) ? { text: S(c) } : c));

function card(s, x, y, w, h, fill = LT) { s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 }); }
function txt(s, t, x, y, w, h, size = 16, color = INK, bold = false, align = "left", valign = "top") {
  s.addText(S(t), { x, y, w, h, fontSize: size, color, bold, margin: 0, align, valign }); }
const TBL = (fs) => ({ fontSize: fs, color: INK, border: { type: "solid", pt: 0.75, color: LINE }, valign: "middle", margin: 0.06 });
const hdr = (t) => ({ text: S(t), options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, align: "center" } });
const B = (t) => ({ text: t, options: { bold: true } });
// 이론 페이지: 왼쪽 라벨 + 수식 이미지 줄들, 아래 기호 표
function theory(s, title, lines, symbols, note) {
  header(s, title);
  let y = 1.3;
  lines.forEach(([name, h, label]) => {
    txt(s, label, 0.6, y, 2.0, h, 16, NAVY, true, "left", "middle");
    eq(s, name, 2.6, y, h, 10.0);
    y += h + 0.18;
  });
  if (symbols && symbols.length) {
    const rows = [[hdr("기호"), hdr("뜻"), hdr("우리 값")]].concat(symbols);
    const ty = Math.max(y + 0.05, 4.55);
    s.addTable(T(rows), { x: 0.6, y: ty, w: 12.1, colW: [1.5, 6.4, 4.2], rowH: 0.33, ...TBL(13) });
    y = ty + rows.length * 0.4 + 0.05;
  }
  if (note) txt(s, note, 0.6, Math.min(Math.max(y, 6.3), 6.72), 12.1, 0.4, 13.5, GRAY);
}


// 코드 보여주기 슬라이드: 왼쪽 코드(고정폭), 오른쪽 짧은 메모
function codeSlide(title, file, code, notes, codeW = 8.0, fs = 12) {
  const s = pres.addSlide(); header(s, title);
  s.addShape(pres.ShapeType.rect, { x: 0.5, y: 1.25, w: codeW, h: 5.6, fill: { color: "1E1E2E" }, line: { color: "1E1E2E" } });
  s.addText(file, { x: 0.6, y: 1.3, w: codeW - 0.2, h: 0.3, fontSize: 11, color: "9DA5B4", fontFace: "Consolas", margin: 0 });
  s.addText(code, { x: 0.6, y: 1.65, w: codeW - 0.2, h: 5.1, fontSize: fs, color: "E6E6E6", fontFace: "Consolas", margin: 0, valign: "top", lineSpacingMultiple: 1.05 });
  const nx = 0.5 + codeW + 0.3, nw = 12.83 - nx, hh = 5.6 / notes.length;
  notes.forEach((n, i) => { const y = 1.25 + i * hh;
    card(s, nx, y, nw, hh - 0.12);
    if (typeof n === "object" && n.eq) {
      const r = EQI[n.eq].ratio; let w = nw - 0.4, h = w / r; if (h > hh - 0.5) { h = hh - 0.5; w = h * r; }
      s.addImage({ path: EQD + n.eq + ".png", x: nx + (nw - w) / 2, y: y + (hh - 0.12 - h) / 2, w, h });
    } else {
      s.addText(n, { x: nx + 0.15, y: y + 0.1, w: nw - 0.3, h: hh - 0.3, fontSize: 15, color: NAVY, bold: true, margin: 0, valign: "middle" });
    }
  });
}

// ---------- 1. 표지 ----------
{
  const s = pres.addSlide(); s.background = { color: "FFFFFF" };
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: NAVY }, line: { color: NAVY } });
  s.addText("INU", { x: 11.55, y: 0.22, w: 1.0, h: 0.5, fontSize: 24, bold: true, color: NAVY, margin: 0, align: "right" });
  s.addText("인천대학교", { x: 11.3, y: 0.68, w: 1.3, h: 0.25, fontSize: 9, color: GRAY, margin: 0, align: "right" });
  s.addText("Channel Scaling Limits in Complementary Electrostatic Shielding-Based Reconfigurable FETs: A DEVSIM Simulation Study",
    { x: 0.7, y: 1.3, w: 8.3, h: 1.5, fontSize: 22, bold: true, color: NAVY, margin: 0, valign: "top" });
  s.addText("DEVSIM 시뮬레이션을 통한 상보적 정전기 차폐 기반 RFET의 채널 스케일링 한계 분석", { x: 0.7, y: 2.9, w: 8.3, h: 0.5, fontSize: 15, color: INK, margin: 0 });
  s.addText("진행 보고 — 500 nm 소자 재현", { x: 0.7, y: 3.5, w: 8.3, h: 0.45, fontSize: 15, color: BLUE, bold: true, margin: 0 });
  s.addText("양지선 · 이은수 · 이종명", { x: 0.7, y: 6.2, w: 6, h: 0.4, fontSize: 13, color: GRAY, margin: 0 });
  s.addImage({ path: MEDIA + "image1.png", x: 8.6, y: 4.4, w: 4.2, h: 4.2 * 315 / 610 });
  s.addShape(pres.ShapeType.rect, { x: 0, y: 7.1, w: 13.33, h: 0.4, fill: { color: NAVY }, line: { color: NAVY } });
  s.addShape(pres.ShapeType.rect, { x: 0, y: 7.1, w: 4.5, h: 0.4, fill: { color: GOLD }, line: { color: GOLD } });
}

// ---------- 2. 선행논문 ----------
{
  const s = pres.addSlide(); header(s, "선행논문 : 상보적 정전기 차폐 RFET (Jiao et al., APL 2026)");
  s.addImage({ path: MEDIA + "image2.png", x: 0.6, y: 1.35, w: 5.6, h: 5.6 * 478 / 656 });
  s.addImage({ path: MEDIA + "image3.png", x: 6.5, y: 1.35, w: 6.3, h: 6.3 * 627 / 954 });
  card(s, 0.6, 5.7, 12.2, 1.1, LT);
  txt(s, "Source 는 박막 위  →  Source 접합은 BG 만 제어", 0.8, 5.78, 6.0, 0.5, 17, NAVY, true, "left", "middle");
  txt(s, "Drain 은 박막 아래  →  Drain 접합은 TG 만 제어", 6.9, 5.78, 6.0, 0.5, 17, NAVY, true, "left", "middle");
  txt(s, "한 게이트 = 한 접합   ·   채널 ≈ 500 nm", 0.8, 6.28, 11.8, 0.45, 16, INK);
}

// ---------- 3. 연구 질문 ----------
{
  const s = pres.addSlide(); header(s, "연구 질문 : 채널을 줄이면 어디서부터 선택적 제어가 무너지나");
  const xs = [1.2, 4.3, 7.4, 10.5], labs = ["2 µm", "500 nm", "200 nm", "100 nm"], sub = ["", "선행논문 · 우리 재현", "", "crosstalk?"];
  s.addShape(pres.ShapeType.line, { x: 1.2, y: 3.0, w: 9.6, h: 0, line: { color: NAVY, width: 2.5 } });
  xs.forEach((x, i) => {
    s.addShape(pres.ShapeType.ellipse, { x: x - 0.14, y: 2.86, w: 0.28, h: 0.28, fill: { color: i === 1 ? GOLD : NAVY }, line: { color: "FFFFFF", width: 1 } });
    txt(s, labs[i], x - 1.2, 2.1, 2.4, 0.6, 22, i === 1 ? ORANGE : NAVY, true, "center");
    if (sub[i]) txt(s, sub[i], x - 1.5, 3.25, 3.0, 0.4, 14, GRAY, false, "center");
  });
  card(s, 0.8, 4.3, 5.9, 1.9); card(s, 6.9, 4.3, 5.9, 1.9);
  s.addText([B("1단계 (지금까지)"), { text: "\n500 nm 소자 재현 — 전위 · 밴드 · 전류", options: {} }], { x: 1.0, y: 4.45, w: 5.6, h: 1.6, fontSize: 18, color: INK, margin: 0, valign: "top" });
  s.addText([B("2단계 (다음)"), { text: "\n터널링 → p형  ·  채널 길이 스윕", options: {} }], { x: 7.1, y: 4.45, w: 5.6, h: 1.6, fontSize: 18, color: INK, margin: 0, valign: "top" });
}

// ---------- 4. 원칙 ----------
{
  const s = pres.addSlide(); header(s, "진행 원칙");
  const items = [["독립 구현", "구조 · 물리 · 코드를 처음부터\n→ 두 가지 방법으로 교차 검증", NAVY],
                 ["숫자 분류", "[A] 논문값\n[B] 1차 문헌값\n[C] 모델 가정", BLUE],
                 ["하지 않은 것", "단층 물성을 14층에 그대로\n실험 전류 fitting\n임의 지표", ORANGE]];
  items.forEach((it, i) => { const x = 0.6 + i * 4.15;
    card(s, x, 1.6, 3.9, 3.6);
    s.addShape(pres.ShapeType.rect, { x, y: 1.6, w: 3.9, h: 0.8, fill: { color: it[2] }, line: { color: it[2] } });
    txt(s, it[0], x, 1.6, 3.9, 0.8, 22, "FFFFFF", true, "center", "middle");
    s.addText(it[1], { x: x + 0.25, y: 2.6, w: 3.4, h: 2.4, fontSize: 18, color: INK, margin: 0, valign: "top", paraSpaceAfter: 10 });
  });
}

// ---------- 5. 코드 구성 ----------
{
  const s = pres.addSlide(); header(s, "코드 구성과 각 단계의 방정식");
  const steps = [["rfet_geometry.py", "단면 정의\n[논문값] / [모델 가정]", NAVY],
                 ["rfet_mesh_gmsh.py", "삼각형 격자", BLUE],
                 ["rfet_poisson_devsim.py\nrfet_fem_reference.py", "STEP 3  정전기", GREEN],
                 ["rfet_semiconductor.py\nrfet_poisson_semi_devsim.py", "STEP 4  밴드", ORANGE],
                 ["rfet_transport_devsim.py", "STEP 5  전류", RED]];
  const w = 2.3, gap = 0.17, x0 = 0.55;
  steps.forEach((st_, i) => { const x = x0 + i * (w + gap);
    s.addShape(pres.ShapeType.rect, { x, y: 1.5, w, h: 0.95, fill: { color: st_[2] }, line: { color: st_[2] } });
    s.addText(st_[0], { x, y: 1.5, w, h: 0.95, fontSize: 10.5, bold: true, color: "FFFFFF", fontFace: "Consolas", align: "center", valign: "middle", margin: 0.05 });
    card(s, x, 2.55, w, 1.0);
    txt(s, st_[1], x + 0.1, 2.6, w - 0.2, 0.9, 15, INK, false, "center", "middle");
    if (i < steps.length - 1) txt(s, "→", x + w - 0.05, 1.75, gap + 0.1, 0.4, 16, NAVY, false, "center");
  });
  const rows = [["정전기", "poisson", "gauss"], ["밴드", "band", "fd"], ["전류", "cont", "dd"]];
  let y = 3.85;
  rows.forEach(([lab, a, b]) => {
    txt(s, lab, 0.6, y, 1.2, 0.8, 17, NAVY, true, "left", "middle");
    eq(s, a, 1.9, y + 0.05, 0.7, 5.2); eq(s, b, 7.4, y + 0.05, 0.7, 5.4);
    y += 1.05;
  });
}


// ---------- 5b. 코드: 푸아송 ----------
codeSlide("코드 · STEP 3 푸아송 (DEVSIM)", "rfet_poisson_devsim.py",
`# 미지수: 노드마다 전위 ψ
devsim.node_solution(device, region, name="Potential")

# edge 전기장  E = (ψ_n0 − ψ_n1) / L_edge
devsim.edge_model(device, region, name="ElectricField",
    equation="(Potential@n0 - Potential@n1)*EdgeInverseLength")

# 전속밀도  D = ε E
devsim.edge_model(device, region, name="PotentialEdgeFlux",
    equation="Permittivity*ElectricField")

# Σ D·A = Q   (STEP 3: Q = 0)
devsim.equation(device, region, name="PotentialEquation",
    variable_name="Potential", edge_model="PotentialEdgeFlux")

# 금속: ψ = V          재료 경계: ψ, εE 연속
devsim.contact_node_model(device, contact, name=bc,
    equation=f"Potential - {bias}")
devsim.interface_equation(device, interface,
    name="PotentialEquation", type="continuous")`,
  ["방정식을 문자열로 적는다", "edge 마다 D = εE → 합산 (가우스 법칙)", "금속 = Dirichlet · 경계 = continuous", "같은 격자를 FEM 코드도 읽어 비교"]);

// ---------- 5c. 코드: 캐리어 ----------
codeSlide("코드 · STEP 4 캐리어 밀도 (2D-DOS 페르미–디랙)", "rfet_semiconductor.py",
`# [문헌값] Wickramaratne 2014 (bulk)
ME_SIGMA_L, ME_SIGMA_T, MH_GAMMA = 0.489, 0.643, 0.997
EG_EV, CHI_EV = 1.2, 4.03                 # [문헌값]
PHI_BN_SOURCE, PHI_BN_DRAIN = 0.22, 0.53  # [문헌값] Pd / Au

# 한 층당 2D 유효 상태밀도 → × 14층 / 9.1 nm
NC_EQ = layers_2d_dos(ME_SIGMA_L, ME_SIGMA_T, g_v=6) * N_LAYERS / T_WSE2_NM

def softplus(x):                  # ln(1 + e^x)
    return np.where(x > 0, x, 0.0) + np.log1p(np.exp(-np.abs(x)))

def carriers(psi):
    eta_n = ( psi + CHI_EV) / KT_EV           # (E_F − E_c)/kT
    eta_p = (-psi - CHI_EV - EG_EV) / KT_EV   # (E_v − E_F)/kT
    return NC_EQ * softplus(eta_n), NV_EQ * softplus(eta_p)

def rho(psi):
    n, p = carriers(psi)
    return p - n                              # 도핑 0 [모델 가정]

# 접점:  ψ = V − (φ_Bn + χ)      게이트:  ψ = V_g − Φ_m`,
  [{ eq: "fd" }, { eq: "band" }, { eq: "nc14" }, "값마다 [문헌값] / [모델 가정] 표시"]);

// ---------- 6. 값과 출처 (출처 셀 = DOI 하이퍼링크) ----------
{
  const s = pres.addSlide(); header(s, "값과 출처   (출처 클릭 → 논문)");
  const DOI = { jiao: "https://doi.org/10.1063/5.0338649", lat: "https://doi.org/10.1038/s41699-018-0050-x", mcd: "https://doi.org/10.1021/nn501728w",
    smy: "https://doi.org/10.1088/2053-1583/aa6bea", wic: "https://doi.org/10.1063/1.4869142", jang: "https://doi.org/10.1002/adma.202109899",
    zha: "https://doi.org/10.1063/1.4940982", koe: "https://doi.org/10.1038/nnano.2011.123" };
  const L = (t, k) => ({ text: t, options: { hyperlink: { url: DOI[k] }, color: BLUE } });
  const rows = [
    [hdr("항목"), hdr("값"), hdr("분류"), hdr("출처")],
    ["WSe₂ / h-BN / SiO₂ 두께", "9.1 / 30 / 300 nm", "[A]", L("Jiao 2026, APL 128, 263504", "jiao")],
    ["Source Pd/Au · Drain Ti/Au", "5/50 → 55 · 1/70 → 71 nm", "[A]", L("Jiao 2026", "jiao")],
    ["채널 길이 L", "≈ 500 nm", "[A]", L("Jiao 2026", "jiao")],
    ["ε WSe₂ ⊥/∥ · h-BN ⊥/∥", "7.9/16.0 · 3.76/6.93", "[B]", L("Laturia 2018, npj 2D Mater. Appl. 2, 6 (Table 1·2)", "lat")],
    ["E_g · χ", "1.2 eV · 4.03 eV", "[B]", { text: [L("McDonnell 2014, ACS Nano 8, 6265", "mcd"), { text: "  ·  " }, L("Smyth 2017, 2D Mater. 4, 025084", "smy")] }],
    ["m*  (e 종/횡, h)", "0.489 / 0.643 / 0.997 m₀", "[B]", L("Wickramaratne 2014, J. Chem. Phys. 140, 124710", "wic")],
    ["φ_Bn  Pd · Au", "0.22 · 0.53 eV", "[B]", { text: [L("Jang 2022, Adv. Mater. 34, 2109899", "jang"), { text: "  ·  " }, L("Smyth 2017", "smy")] }],
    ["E (WSe₂) · Γ", "167 GPa · 0.45 J/m²", "[B]", { text: [L("Zhang 2016, APL 108, 042104", "zha"), { text: "  ·  " }, L("Koenig 2011, Nat. Nanotechnol. 6, 543", "koe")] }],
    ["패드 · TG 여유 · 쐐기 ε", "1000 · 300/300 nm · 1", "[C]", "fringe 3배 밖 · 대칭 · 하한"],
    ["도핑 · 고정전하 · μ", "0 · 0 · 100 cm²/Vs", "[C]", "값 없음, fitting 금지"],
  ];
  s.addTable(T(rows), { x: 0.5, y: 1.25, w: 12.33, colW: [3.0, 2.8, 0.8, 5.73], rowH: 0.46, ...TBL(13.5) });
}

// ---------- 이론 ① 정전기 ----------
{
  const s = pres.addSlide();
  theory(s, "이론 ① 정전기 — 푸아송 방정식과 게이트",
    [["poisson", 0.55, "푸아송"], ["cap", 0.64, "커패시터"], ["superpos", 0.45, "선형 중첩"], ["gauss", 0.74, "유한체적"]],
    [["ψ", "정전기 전위 (전압)", "미지수"], ["ε", "유전율 — 층 방향 ⊥ 값 (이방성은 FEM 텐서로 확인)", "WSe₂ 7.9 · h-BN 3.76 · SiO₂ 3.9 · 공기 1"],
     ["ψ_TG", "TG 1 V, 나머지 0 V 일 때의 해  →  단위 V/V", "STEP 3 결과"], ["Q_node", "노드 주위 상자 안의 전하", "STEP 3: 0  ·  STEP 4: q(p−n)"]],
    "금속 내부는 풀지 않음 — 등전위, 경계선에 전압만 (Dirichlet) → 금속 뒤쪽은 전기장을 못 느낀다 = 차폐");
}

// ---------- 이론 ② 밴드 · 쇼트키 ----------
{
  const s = pres.addSlide();
  theory(s, "이론 ② 밴드와 쇼트키 장벽",
    [["band", 0.48, "밴드 ↔ 전압"], ["schottky", 0.48, "장벽"], ["contact", 0.72, "경계조건"], ["thermionic", 0.72, "열전자 방출"]],
    [["χ", "전자친화도 (E_c 에서 진공까지)", "4.03 eV"], ["E_g", "밴드갭", "1.2 eV"], ["φ_Bn", "전자 쇼트키 장벽 (핀닝 S = 0.03 → 금속에 거의 무관)", "Pd 0.22 · Au 0.53 eV"],
     ["Φ_m", "게이트 일함수 — flat band 가 되는 값 [C]", "χ + E_g/2 = 4.63 eV"]],
    "φ_Bp = 1.2 − 0.22 = 0.98 eV  →  exp(−0.98/0.0259) ≈ 10⁻¹⁷ : 열전자만으로는 p형 전류가 나오지 않는 이유");
}

// ---------- 이론 ③ 캐리어 밀도 ----------
{
  const s = pres.addSlide();
  theory(s, "이론 ③ 캐리어 밀도 — 2차원 상태밀도 페르미–디랙",
    [["dos2d", 0.66, "2D 상태밀도"], ["fd", 0.72, "전자 밀도"], ["fdlimits", 0.48, "극한"], ["nc14", 0.44, "14층"]],
    [["m_d", "상태밀도 유효질량 √(m_l m_t)", "전자 0.56 m₀ · 정공 0.997 m₀"], ["g_v", "골짜기 수 (스핀 포함)", "전자 6 · 정공 2"],
     ["η", "(E_F − E_c)/kT — 게이트가 바꾸는 양", "STEP 4 표의 E_c − E_F"], ["ρ", "q(p − n), 도핑 0 [C]", "푸아송 우변"]],
    "적분이 닫힌 꼴 → 전자가 많이 모여도 발산 없음 → V_BG ±60 V 수렴  (Boltzmann 근사는 ±10 V 가 한계)");
}

// ---------- 이론 ④ 박막 휨 ----------
{
  const s = pres.addSlide();
  theory(s, "이론 ④ 박막이 휘는 모양과 길이 — 에너지 최소화",
    [["beam", 0.7, "판의 평형"], ["bend", 0.8, "굽힘 에너지"], ["lstar", 0.76, "접착과 균형"], ["strain", 0.7, "변형률 검사"]],
    [["E, ν", "영률 · 포아송비", "167 GPa (Zhang 2016) · 0.2 [C]"], ["t, h", "박막 두께 · 올라갈 높이 (Drain)", "9.1 · 71 nm"], ["Γ", "접착 에너지 (차용)", "0.45 J/m²   (ℓ ∝ Γ^−¼ )"]],
    "경계조건 4개(양 끝 높이·기울기) → 3차식만 가능.  h-BN 에 같은 식: ℓ* ≈ 700 nm > L → 곧은 판");
}

// ---------- 이론 ⑤ 수송 ----------
{
  const s = pres.addSlide();
  theory(s, "이론 ⑤ 전류 — 드리프트–확산",
    [["dd", 0.58, "전류 밀도"], ["cont", 0.52, "연속 방정식"], ["einstein", 0.5, "아인슈타인 관계"], ["wkb", 0.9, "터널링 (다음)"]],
    [["μ", "이동도 [C] — 전류 절대값 ∝ μ", "100 cm²/Vs"], ["접점 n, p", "장벽 높이에 해당하는 평형값 (열전자)", "ψ = V − (φ_Bn + χ)/q"], ["T", "WKB 터널링 확률 — 아직 없음", "STEP 5 다음"]],
    "푸아송 + 전자 연속 + 정공 연속을 동시에 Newton 으로 풀고, 전압은 0.5~2 V 씩 올린다");
}

// ---------- 구조 ----------
{
  const s = pres.addSlide(); header(s, "비대칭 구조 — 기준 config curve_el");
  fit(s, FIG("rfet_geometry_curve_el.png"), { x: 0.4, y: 1.2, w: 8.4, h: 5.7 }, 1.5);
  const rows = [[hdr("요소"), hdr("nm")], ["Source (Pd/Au)", "55, 박막 위"], ["Drain (Au/Ti)", "71, 박막 아래"], ["채널 L", "500"],
    ["WSe₂", "9.1 · 283→500 S자"], ["h-BN", "30 · 곧은 판"], ["TG", "−300 → 800"], ["SiO₂", "300"], ["빈 공간", "공기 ε = 1"]];
  s.addTable(T(rows), { x: 9.0, y: 1.4, w: 3.9, colW: [1.7, 2.2], rowH: 0.55, ...TBL(14) });
}

// ---------- 경사 민감도 ----------
{
  const s = pres.addSlide(); header(s, "경사 형상 : 에너지 최소화 결과와 민감도");
  fit(s, FIG("fig_ramp_shapes.png"), { x: 0.4, y: 1.1, w: 12.5, h: 3.4 }, 3.45);
  const rows = [
    [hdr("config"), hdr("경사"), hdr("TG→D"), hdr("TG→S"), hdr("BG→S"), hdr("BG→D")],
    [B("curve_el"), "S자 217 nm", B("0.35"), "0.07", "0.09", "0.009"],
    ["line_el", "직선 217 nm", "0.28", "0.07", "0.09", "0.012"],
    ["curve70", "S자 70 nm", "0.24", "0.07", "0.09", "0.014"],
    ["line70", "직선 70 nm", "0.18", "0.07", "0.09", "0.020"],
    ["curve_el_eq", "Source 두께 71", "0.34", B("0.06"), "0.09", "0.010"],
  ];
  s.addTable(T(rows), { x: 0.5, y: 4.6, w: 12.33, colW: [2.2, 3.0, 1.8, 1.8, 1.8, 1.73], rowH: 0.36, ...TBL(14), align: "center" });
}

// ---------- 격자 ----------
{
  const s = pres.addSlide(); header(s, "실제 계산 격자 (gmsh)");
  fit(s, FIG("fig_mesh_curve_el.png"), { x: 0.4, y: 1.15, w: 9.3, h: 5.9 }, 1.93);
  card(s, 9.9, 1.5, 3.0, 3.4);
  s.addText([B("크기 규칙"), { text: "\n박막 두께 ≥ 4층\n접합 근처 0.57 nm\n공기 쐐기 ≥ 3요소\n최대 50 nm", options: {} }], { x: 10.1, y: 1.6, w: 2.7, h: 3.2, fontSize: 16, color: INK, margin: 0, valign: "top" });
}

// ---------- STEP 3 ----------
{
  const s = pres.addSlide(); header(s, "STEP 3 · 게이트 1 V 가 채널 어디를 움직이나");
  fit(s, FIG("fig_step3_profiles_slope.png"), { x: 0.4, y: 1.1, w: 12.5, h: 4.1 }, 2.62);
  const rows = [[hdr("1 V 당"), hdr("Source 쪽"), hdr("Drain 쪽")], ["TG", "0.07", B("0.35")], ["BG", B("0.09"), "0.009"]];
  s.addTable(T(rows), { x: 0.8, y: 5.5, w: 5.2, colW: [1.4, 1.9, 1.9], rowH: 0.45, ...TBL(16), align: "center" });
  card(s, 6.5, 5.5, 6.4, 1.4);
  s.addText([B("TG → Drain 쪽  5배"), { text: "\n", options: {} }, B("BG → Source 쪽  10배")], { x: 6.7, y: 5.6, w: 6.1, h: 1.2, fontSize: 18, color: NAVY, margin: 0, valign: "top" });
}
{
  const s = pres.addSlide(); header(s, "STEP 3 · 전위 응답 지도");
  fit(s, FIG("fig_step3_maps_curve_el.png"), { x: 0.4, y: 1.15, w: 12.5, h: 5.9 }, 1.5);
}

// ---------- STEP 4 ----------
{
  const s = pres.addSlide(); header(s, "STEP 4 · 밴드 : 어느 게이트가 어느 쪽을 n/p 로 만드나");
  fit(s, FIG("fig_step4_bands_slope.png"), { x: 0.4, y: 1.15, w: 8.6, h: 5.9 }, 1.415);
  const rows = [[hdr("E_c − E_F (eV)"), hdr("S 쪽"), hdr("D 쪽")], ["0 V", "0.29", "0.55"], ["TG −5 V", "0.48", B("1.05")], ["BG −60 → +60", B("1.02 → 0.16"), "0.68 → 0.44"]];
  s.addTable(T(rows), { x: 9.2, y: 1.5, w: 3.7, colW: [1.5, 1.1, 1.1], rowH: 0.6, ...TBL(14), align: "center" });
  card(s, 9.2, 4.2, 3.7, 1.6);
  s.addText([B("TG → Drain 쪽만 p 형"), { text: "\n", options: {} }, B("BG → Source 쪽만")], { x: 9.35, y: 4.3, w: 3.4, h: 1.4, fontSize: 16, color: NAVY, margin: 0, valign: "top" });
}

// ---------- STEP 5 ----------
{
  const s = pres.addSlide(); header(s, "STEP 5 · 전류 (드리프트–확산, 터널링 없음)");
  txt(s, "문헌 장벽 (S 0.22 / D 0.53 eV)", 0.5, 1.15, 6.2, 0.4, 15, NAVY, true);
  txt(s, "대조군 (0.60 / 0.60 eV)", 6.8, 1.15, 6.2, 0.4, 15, ORANGE, true);
  fit(s, FIG("rfet_idvbg_bridge_perp_lit.png"), { x: 0.4, y: 1.6, w: 6.2, h: 2.7 }, 2.73);
  fit(s, FIG("rfet_idvbg_bridge_perp_equal_mid.png"), { x: 6.7, y: 1.6, w: 6.2, h: 2.7 }, 2.73);
  const rows = [
    [hdr("조건"), hdr("문헌 장벽"), hdr("대조군")],
    ["n형 · TG +5", "BG 가 10⁻²⁰ → 10⁻⁴ 로 켬", "10⁻²⁰ → 10⁻⁸"],
    ["n형 · TG −5", "BG 무관 바닥 10⁻¹¹", "바닥 10⁻¹⁰"],
    ["p형 · TG −5", "정공 10⁻¹⁶ ≈ 0", "정공 10⁻⁹, BG 가 끔"],
  ];
  s.addTable(T(rows), { x: 0.5, y: 4.5, w: 12.33, colW: [2.6, 5.0, 4.73], rowH: 0.5, ...TBL(15) });
  txt(s, "구조 bridge 로 계산 (curve_el 재계산 예정) · 단위 A/µm", 0.5, 6.6, 12.3, 0.4, 13, GRAY);
}

// ---------- 검증 ----------
{
  const s = pres.addSlide(); header(s, "검증");
  fit(s, FIG("fig_mesh_convergence_simple.png"), { x: 0.4, y: 1.3, w: 6.6, h: 5.4 }, 1.71);
  const rows = [[hdr("검증"), hdr("결과")], ["해석해 (2층 평행판)", "FEM 일치"], ["DEVSIM vs 직접 짠 FEM", "소수 셋째 자리 일치"],
    ["격자 4 → 6 → 8", "ψ ≤ 0.001 V/V · E_c ≤ 5 meV"], ["전류 보존", "6×10⁻⁵"], ["텐서 유전율", "스칼라 대비 10–15 %"]];
  s.addTable(T(rows), { x: 7.2, y: 1.6, w: 5.7, colW: [2.7, 3.0], rowH: 0.65, ...TBL(15) });
}

// ---------- 가정과 한계 ----------
{
  const s = pres.addSlide(); header(s, "가정과 한계");
  const rows = [[hdr("가정"), hdr("영향")], ["2D 단면 (폭 균일)", "폭 가장자리 fringe 누락"], ["ε 스칼라 (⊥)", "텐서 대비 10–15 % 과대"],
    ["장벽 0.22 / 0.53 — 다른 시료 값", "절대 E_c ±0.2 eV → 대조군으로 분리"], ["φ_Bp = E_g − φ_Bn", "p형 전류 결정"],
    ["도핑 · 고정전하 0, flat-band Φ_m", "V_th 위치는 비교 대상 아님"], ["열전자 DD 만", "p형 과소 → 터널링 다음"],
    ["μ = 100 cm²/Vs", "전류 절대값 ∝ μ"], ["Γ 차용, 박막 늘어남 무시", "ℓ: 217 (하한) ~ 500 (상한)"]];
  s.addTable(T(rows), { x: 0.5, y: 1.3, w: 12.33, colW: [6.0, 6.33], rowH: 0.58, ...TBL(16) });
}

// ---------- 정리 ----------
{
  const s = pres.addSlide(); header(s, "정리와 다음 단계");
  const rows = [[hdr("단계"), hdr("결과"), hdr("상태")], ["값", "전부 출처 · 원문 대조", "완료"],
    ["구조", "비대칭 + 판 h-BN + 경사 217 nm · 형상 민감도 5종", "완료"],
    ["STEP 3 정전기", "TG→D 0.35 / S 0.07 · BG→S 0.09 / D 0.009", "완료 · 검증"],
    ["STEP 4 밴드", "TG 는 Drain 쪽만, BG 는 Source 쪽만", "완료"],
    ["STEP 5 전류", "n형 선택적 제어 확인 · p형은 터널링 필요", "DD 완료"],
    ["다음", "터널링 (WKB) → 채널 길이 500 → 100 nm", "예정"]];
  s.addTable(T(rows), { x: 0.5, y: 1.4, w: 12.33, colW: [2.4, 7.4, 2.53], rowH: 0.65, ...TBL(17) });
  txt(s, "GitHub  jiseonyang-9070/rfet", 0.5, 6.4, 12.3, 0.45, 14, GRAY, false, "center");
}

(async () => { const out = "/home/claude/rfet_ppt/RFET_progress_INU.pptx"; await pres.writeFile({ fileName: out }); console.log("written", out); })();
