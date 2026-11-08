// 비대칭 구조 — 치수·근거·경사·빈 공간 (2장)
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/root/.claude/skills/synced/113d6e39-a176-431c-9ca6-39995820802c_4d635005-59e9-4798-8614-4ba581775b9d/pptx/scripts/apply_theme.js");
const FIG = (n) => "/home/claude/rfet_repo/figures/" + n;
const THEME = { name: "RFET Violet", headFontFace: "Malgun Gothic", bodyFontFace: "Malgun Gothic",
  colors: { dk1: "1A1630", lt1: "FFFFFF", dk2: "4F4B63", lt2: "F3F1F8", accent1: "2A78D6", accent2: "EB6834", accent3: "6250D6", accent4: "1BAF7A", accent5: "EDA100", accent6: "E34948", hlink: "2A78D6", folHlink: "6250D6" } };
const H = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.defineSlideMaster({ title: "CONTENT", background: { color: H.lt1 }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 12.1, h: 0.8, fontSize: 30, bold: true, color: H.dk1, align: "left", valign: "middle", margin: 0 } } },
  { text: { text: "WSe₂ RFET · DEVSIM", options: { x: 0.6, y: 7.05, w: 5, h: 0.3, fontSize: 10, color: H.dk2, margin: 0 } } },
  { slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: H.dk2, align: "right" } } ] });
const TBL = (fs) => ({ fontSize: fs, color: H.dk1, border: { type: "solid", pt: 0.75, color: "D9D6E6" }, valign: "middle", margin: 0.05 });
const hdr = (t) => ({ text: t, options: { bold: true, color: H.lt1, fill: { color: H.dk1 }, align: "center" } });
function fit(slide, file, box, ratio, name) { let w = box.w, h = w / ratio; if (h > box.h) { h = box.h; w = h * ratio; }
  slide.addImage({ path: file, x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h, objectName: name }); }
function card(s, x, y, w, h) { s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: H.lt2 }, line: { color: H.lt2 }, rectRadius: 0.1, objectName: "card" }); }

// ---------- 1. 치수와 근거 ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("비대칭 구조 — 각 요소의 치수와 근거 (단위 nm)", { placeholder: "title" });
  fit(s, FIG("fig_mesh_bridge.png"), { x: 0.4, y: 1.15, w: 6.0, h: 2.75 }, 1.77, "mesh");
  card(s, 6.6, 1.2, 6.3, 2.65);
  s.addText([
    { text: "왜 이 비대칭인가", options: { bold: true, fontSize: 16, color: H.dk1, breakLine: true } },
    { text: "Source 가 WSe₂ 위 → TG 전기장을 가림 → source 접합은 BG 만 제어", options: { fontSize: 13, color: H.dk1, breakLine: true } },
    { text: "Drain 이 WSe₂ 아래 → BG 전기장을 가림 → drain 접합은 TG 만 제어", options: { fontSize: 13, color: H.dk1, breakLine: true } },
    { text: "박막이 Drain(71 nm) 위로 올라가야 하므로 채널은 경사가 되고, 경사 위·아래에 빈 공간이 생긴다", options: { fontSize: 12, color: H.dk2, breakLine: true } },
    { text: "[A] 논문값   [C] 모델 가정   ·   두께는 모두 수직 두께 (경사에서도 일정)", options: { fontSize: 10.5, color: H.dk2 } },
  ], { x: 6.85, y: 1.25, w: 5.9, h: 2.55, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 5, objectName: "why" });
  const rows = [
    [hdr("요소"), hdr("x 범위 (길이)"), hdr("두께 y"), hdr("분류 · 왜 이 값인가")],
    ["Source (Pd/Au)", "−1000 → 0  (1000)", "55", "[A] 5/50 합, 박막 위 증착.  패드 1000 은 [C]: 경계가 fringe(≈300)의 3배 밖"],
    ["Drain (Au/Ti)", "500 → 1500  (1000)", "71", "[A] 1/70 합, 박막 아래 vdW 전사.  패드 [C] 동일"],
    ["채널 L", "0 → 500", "—", "[A] ≈500.  [C] Source 모서리 ↔ Drain 벽 수평거리로 해석"],
    ["WSe₂", "−1000 → 1500", "9.1", "[A].  0→L 에서 y 0 → 71 직선 경사 (8.1°)"],
    ["h-BN", "−1000 → 1500", "30", "[A].  Source 윗면에서 Drain 쪽 박막 윗면까지 직선 = bridge (탄성 추정 ℓ≈450≈L)"],
    ["Top gate", "−300 → 800  (1100)", "선", "[C] overhang 300/300 대칭: TG–WSe₂ 거리의 3배, 한쪽 편애 없음"],
    ["SiO₂ / Back gate", "−1000 → 1500", "300 / 선", "[A] 300.  BG = y −300 선"],
    ["AirBot / AirTop", "0 → 500", "쐐기 0→71 / 55→0", "경사 때문에 생김. ε = 1 [C] (하한, 보수적).  면적 17,750 / 13,750 nm²"],
  ];
  s.addTable(rows, { x: 0.4, y: 4.05, w: 12.5, colW: [1.7, 2.0, 1.5, 7.3], rowH: 0.31, ...TBL(11), objectName: "dims" });
}

// ---------- 2. 경사와 빈 공간: 우리 vs 팀원 ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("채널 경사와 빈 공간 — 우리 모델 vs 팀원 모델", { placeholder: "title" });
  fit(s, FIG("fig_mesh_bridge.png"), { x: 0.4, y: 1.55, w: 6.2, h: 2.7 }, 1.77, "ours");
  fit(s, "/mnt/user-data/outputs/team_branch_step3_mesh.png", { x: 6.75, y: 1.55, w: 6.2, h: 2.7 }, 2.61, "team");
  s.addText("우리: 경사가 0 → L 전체 (8°)", { x: 0.4, y: 1.15, w: 6.2, h: 0.4, fontSize: 16, bold: true, color: H.accent1, margin: 0, isTextBox: true, objectName: "l1" });
  s.addText("팀원: 평평 500 + 45° 경사 70 (Drain 앞에서만)", { x: 6.75, y: 1.15, w: 6.2, h: 0.4, fontSize: 16, bold: true, color: H.accent2, margin: 0, isTextBox: true, objectName: "l2" });
  const rows = [
    [hdr(""), hdr("우리"), hdr("팀원"), hdr("근거 / 비고")],
    ["경사 구간", "0 → 500 (채널 전체), 8.1°", "500 → 570, 45° (가정)", "논문 \"source edge … at the base of the transition region\" → 전이 구간이 Source 모서리에서 시작"],
    ["Source ↔ Drain 벽", "500", "570", "팀원은 '500' 을 평평한 부분으로 봄"],
    ["빈 공간", "아래 + 위 쐐기, ε = 1", "아래 삼각형만 ε = 1", "충전물 언급 없음 → 공기(하한). 잔류물 ε≈3 은 민감도 예정"],
    ["빈 공간 격자", "별도 영역, 높이 ≥3 요소, 끝점 0.57 nm", "세로 6칸 부채꼴", "쐐기 끝 = 전기장 특이점"],
    ["경사 위 막 두께", "수직 두께 일정", "cos45° = 0.71 배 얇아짐", "팀원 본인 명시"],
    ["미해결", "WSe₂ 경사 탄성 추정 ℓ≈140 → Drain 쪽에서 더 급할 수 있음", "—", "Fig. S2 미확보 → 경사 형상 민감도 (scaling 전 필수)"],
  ];
  s.addTable(rows, { x: 0.4, y: 4.45, w: 12.55, colW: [1.6, 3.4, 2.6, 4.95], rowH: 0.33, ...TBL(11), objectName: "cmp" });
}

(async () => { const out = "/home/claude/rfet_ppt/RFET_asymmetric_structure.pptx"; await pres.writeFile({ fileName: out }); await applyTheme(out, THEME); console.log("written", out); })();
