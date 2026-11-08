# -*- coding: utf-8 -*-
"""
rfet_mesh_gmsh.py
================================================================================
STEP 2-B : rfet_geometry.py의 geometry -> 삼각형 mesh (gmsh) -> .msh 파일 (DEVSIM 입력)

준비:  pip install gmsh numpy
       gmsh >= 4.7 필요. 4.7.0 changelog: "uniformized commands, options and field option names
       (CharacteristicLength -> MeshSize, Line -> Curve, ...; old names are still accepted, but
       deprecated)". 이 파일은 새 이름(MeshSize*, CurvesList, PointsList, SizeMin/Max, Sampling)만 쓴다.
실행:  python rfet_mesh_gmsh.py bridge        (gmsh 창 없이 mesh 생성, 검사 리포트 출력)
       python rfet_mesh_gmsh.py sag45 -gui    (끝나고 gmsh 창에서 mesh 확인)
       python rfet_mesh_gmsh.py               (모든 CONFIGS)
출력:  rfet_<config>_nm.msh   (좌표 단위 nm, 확인/검사용)
       rfet_<config>_cm.msh   (좌표 단위 cm, DEVSIM 입력용)

이 파일의 역할 구분 (교수님께 설명할 때 이 구분이 중요하다)
  - [물리 모델]      : geometry(어디에 무엇이 있는가). 전부 rfet_geometry.py에 있고 여기서는 읽기만 한다.
  - [수치해석 설정]  : mesh 크기(어디를 얼마나 촘촘히). 이 파일의 섹션 1이 전부이다.
                       값을 바꿔도 "물리 모델"은 바뀌지 않고, 수렴하면 결과가 같아야 한다.
  - mesh를 촘촘히 한다는 것 = 전위가 급하게 변하는 곳에 계산 격자점(노드)을 더 둔다는 뜻이다.
"""
import math
import sys

import rfet_geometry as geo
import rfet_mesh_tools as tools


# ==============================================================================
# 섹션 1. [수치해석 설정]  mesh 크기 규칙   (길이 단위 nm)
#   gmsh에는 "background field"라는 기능으로 "위치마다 원하는 삼각형 한 변의 길이"를 정해 준다.
#   Distance 필드 = 어떤 점/선에서의 거리,  Threshold 필드 = 그 거리에 따라 크기를 선형으로 키움,
#   Min 필드 = 여러 규칙 중 가장 작은 값을 채택.
# ==============================================================================
# [수치해석 설정] WSe2 두께 방향 요소 개수. 이동 전하(STEP 4 이후)가 몰리는 곳이고,
#   박막 안에서 수직 방향 전위 변화를 풀어야 하므로 두께당 최소 4개 요소(= 노드 5개 층)를 둔다.
#   두께 9.1 nm -> 요소 크기 2.275 nm.  (수렴 확인 때 4 -> 6 -> 8로 올려 본다)
N_LAYERS_FILM = 4
# [수치해석 설정] mesh 수렴 검사용 덮어쓰기: 환경변수 RFET_N_LAYERS (예: 6, 8). 결과 파일 이름에는 RFET_MESH_TAG 가 붙는다.
import os as _os
if _os.environ.get("RFET_N_LAYERS"):
    N_LAYERS_FILM = int(_os.environ["RFET_N_LAYERS"])
MESH_TAG = _os.environ.get("RFET_MESH_TAG", "")

# [수치해석 설정] 금속-WSe2 접촉 모서리(source/drain junction)의 요소 크기 = S_FILM / EDGE_REFINE.
#   금속의 직각 모서리 근처에서는 전기장이 이론상 발산(E ~ r^(-1/3) 꼴)하는 특이점이라
#   격자를 가장 촘촘히 한다. 이 값이 작아질수록 모서리 "바로 그 점"의 전기장은 계속 커지므로
#   (격자 의존적), STEP 3에서 junction 응답을 읽을 때는 모서리 점 자체가 아니라
#   모서리에서 일정 거리 떨어진 위치를 읽는 규칙을 따로 정해야 한다.
EDGE_REFINE = 4.0

# [수치해석 설정] 공기 쐐기(WSe2 경사 아래의 얇은 공기층) 높이 방향 요소 개수.
#   쐐기 높이 h(x) = x * tan(theta) 는 끝점(x=0)에서 0이므로, 끝점에서 거리 d만큼 떨어진 곳의
#   요소 크기를 d*tan(theta)/N_ACROSS_WEDGE 로 키운다 -> 어디서나 높이 방향으로 약 3개 요소.
N_ACROSS_WEDGE = 3.0

# [수치해석 설정] 크기 증가율. 거리 1 nm 멀어질 때마다 요소 크기가 0.3 nm씩 커진다.
#   (너무 급하게 키우면 이웃 삼각형 크기 차이가 커져 모양이 나빠진다. 0.3 이하가 무난하다.)
GROWTH = 0.3

# [수치해석 설정] 가장 큰 요소 크기 [nm]. SiO2 깊은 곳처럼 전위가 완만하게 변하는 곳.
S_MAX = 50.0

# [수치해석 설정] Top Gate 양 끝 아래 h-BN 표면의 요소 크기 [nm]. TG 모서리의 fringe field를
#   대략 풀기 위한 값이다. TG 모서리는 WSe2에서 30 nm 이상 떨어져 있어 접촉 모서리보다 덜 촘촘해도 된다.
S_TG_EDGE = 5.0

# 출력 파일 이름 (config 이름이 붙는다)
def msh_names(config):
    return f"rfet_{config}{MESH_TAG}_nm.msh", f"rfet_{config}{MESH_TAG}_cm.msh"


# [수치해석 설정] 1 nm = 1e-7 cm.  DEVSIM 관례(길이 cm)에 맞추려는 단위 변환이다.
#   mesh를 nm 단위로 만든 뒤 좌표만 cm로 바꾸는 이유: gmsh의 기하 허용오차(Geometry.Tolerance,
#   기본 1e-8)는 좌표 단위 그대로 적용되므로, cm 단위로 0.57 nm(=5.7e-8 cm)짜리 요소를 만들면
#   점이 서로 같다고 판정되는 등의 문제가 생길 수 있다. nm 단위에서는 그런 문제가 없다.
NM_TO_CM = 1.0e-7


# ==============================================================================
# 섹션 2. geometry를 gmsh 안에 옮긴다 (점 -> 선 -> 면)
#   핵심 규칙 한 가지: 두 영역이 공유하는 선은 gmsh 안에서도 "같은 선 하나"를 쓴다.
#   그러면 gmsh가 그 선 위에 노드를 한 벌만 만들어서 두 영역의 mesh가 계면에서
#   정확히 일치(conforming)한다 -> 계면에서 노드가 어긋나는 일이 없다.
# ==============================================================================
def build_gmsh_geometry(points, polygons):
    import gmsh
    g = gmsh.model.geo

    # (a) 점. 메쉬를 만드는 4개 영역이 쓰는 점만 만든다. (금속 더미 점은 gmsh에 불필요)
    used = []
    for r in geo.REGIONS:
        for name in polygons[r]:
            if name not in used:
                used.append(name)
    point_tag = {}
    for i, name in enumerate(used, start=1):
        x, y = points[name]
        # 4번째 인자 0 = "이 점에서의 요소 크기를 따로 지정하지 않음" (크기는 섹션 4의 필드가 정함)
        g.addPoint(x, y, 0.0, 0.0, i)
        point_tag[name] = i

    # (b) 선. 같은 두 점을 잇는 선은 한 번만 만들고, 반대 방향이면 음수 태그로 재사용한다.
    line_of = {}

    def get_line(a, b):
        if (a, b) in line_of:
            return line_of[(a, b)]
        if (b, a) in line_of:
            return -line_of[(b, a)]
        tag = g.addLine(point_tag[a], point_tag[b])
        line_of[(a, b)] = tag
        return tag

    # (c) 면. 영역마다 선을 반시계 순서로 이어 "curve loop"를 만들고 평면으로 채운다.
    loops, surface = {}, {}
    for r in geo.REGIONS:
        tags = [get_line(a, b) for a, b in geo.edges_of(polygons[r])]
        loops[r] = tags
        surface[r] = g.addPlaneSurface([g.addCurveLoop(tags)])

    g.synchronize()    # geo 커널의 정의를 gmsh 모델에 반영 (이후 physical group/필드에 필요)
    return point_tag, line_of, loops, surface


def line_tag_of_edge(line_of, key):
    """(정렬된) 점 이름 쌍 -> gmsh 선 태그 (양수)"""
    a, b = key
    return line_of[(a, b)] if (a, b) in line_of else line_of[(b, a)]


# ==============================================================================
# 섹션 3. physical group = DEVSIM이 읽는 "이름표"
#   gmsh는 physical group으로 묶인 요소만 파일에 저장한다.
#   - 면(2D) 그룹   -> DEVSIM region (재료가 같은 연속 영역)
#   - 선(1D) 그룹   -> DEVSIM contact (금속과 닿는 선) / interface (두 region이 맞닿는 선)
#   어떤 선이 contact인지 interface인지는 rfet_geometry.classify_edges()가 정한다.
# ==============================================================================
def add_physical_groups(polygons, line_of, surface):
    import gmsh
    for r in geo.REGIONS:
        tag = gmsh.model.addPhysicalGroup(2, [surface[r]])
        gmsh.model.setPhysicalName(2, tag, geo.gmsh_region_name(r))

    contacts, interfaces, _ = geo.classify_edges(polygons)
    for (metal, region), keys in sorted(contacts.items()):
        lines = [line_tag_of_edge(line_of, k) for k in keys]
        tag = gmsh.model.addPhysicalGroup(1, lines)
        gmsh.model.setPhysicalName(1, tag, geo.gmsh_contact_name(metal, region))
    for (r1, r2), keys in sorted(interfaces.items()):
        lines = [line_tag_of_edge(line_of, k) for k in keys]
        tag = gmsh.model.addPhysicalGroup(1, lines)
        gmsh.model.setPhysicalName(1, tag, geo.gmsh_interface_name(r1, r2))


# ==============================================================================
# 섹션 4. mesh 크기 필드  ("어디를 왜 촘촘히 하는가"가 이 섹션의 전부이다)
# ==============================================================================
def add_size_fields(points, point_tag, line_of, loops, p: geo.Params):
    import gmsh
    F = gmsh.model.mesh.field

    # 파생 크기 (모두 위 섹션 1의 설정에서 계산)
    s_film = p.t_wse2 / N_LAYERS_FILM          # WSe2 안/근처 요소 크기 (2.275 nm)
    s_edge = s_film / EDGE_REFINE              # 접촉 모서리 요소 크기 (0.569 nm)

    def threshold(in_field, size_min, dist_min, slope):
        """size = size_min (거리 <= dist_min),  거리가 늘면 slope 비율로 증가,  S_MAX에서 멈춤."""
        t = F.add("Threshold")
        F.setNumber(t, "InField", in_field)
        F.setNumber(t, "SizeMin", size_min)
        F.setNumber(t, "SizeMax", S_MAX)
        F.setNumber(t, "DistMin", dist_min)
        F.setNumber(t, "DistMax", dist_min + (S_MAX - size_min) / slope)
        return t

    def distance_to(curves=None, pts=None, sampling=100):
        d = F.add("Distance")
        if curves:
            F.setNumbers(d, "CurvesList", curves)
        if pts:
            F.setNumbers(d, "PointsList", pts)
        F.setNumber(d, "Sampling", sampling)   # 선을 몇 개 점으로 잘라 거리를 잴지 (많을수록 정확)
        return d

    # --- 규칙 1: WSe2 박막 전체와 그 표면 근처 ---------------------------------------
    # 왜: (i) 박막 두께 방향 해상도, (ii) 유전율이 바뀌는 계면(WSe2/SiO2, WSe2/h-BN, WSe2/공기)에서
    #     전기장이 꺾이므로 계면 근처를 촘촘히, (iii) 접촉 아래 WSe2 윗면/아랫면(금속-WSe2 경계)도 같은 선이다.
    # 어떻게: WSe2 영역의 모든 경계선까지의 거리로 크기를 정한다. 박막 안쪽(경계에서 t/2 이내)은
    #     s_film으로 일정, 바깥쪽 SiO2/h-BN/공기 쪽으로는 GROWTH 비율로 커진다.
    film_curves = sorted({abs(t) for t in loops["WSe2"]})
    longest = 0.0
    for t in film_curves:
        for (a, b), tag in line_of.items():
            if tag == t:
                (xa, ya), (xb, yb) = points[a], points[b]
                longest = max(longest, math.hypot(xb - xa, yb - ya))
    # 가장 긴 선도 s_film/2 간격 이하로 쪼개서 거리를 재도록 표본 개수를 정한다.
    n_sampling = int(math.ceil(longest / (0.5 * s_film)))
    d_film = distance_to(curves=film_curves, sampling=n_sampling)
    t_film = threshold(d_film, s_film, p.t_wse2 / 2.0, GROWTH)

    # --- 규칙 2: 금속 모서리 4곳 ---------------------------------------------------------
    # 왜: 금속 직각 모서리에서는 전위가 급변하고 전기장이 발산하는 특이점이 있다.
    #   - src_edge_bot (0, t_wse2)      : source junction. 캐리어 주입(STEP 4 이후)이 일어나는 곳.
    #   - drn_corner   (L, t_drain)     : drain junction.  위와 같다.
    #   - src_edge_top (0, t_wse2+t_src): Source 금속의 위쪽 모서리. TG 전기장이 Source 금속을
    #                                     "돌아서" source junction 쪽으로 들어가는 길목이다.
    #   - dr_bl        (L, 0)           : Drain 금속의 아래쪽 모서리. BG 전기장이 Drain 금속을
    #                                     돌아서 공기 쐐기로 들어가는 길목이다.
    #   앞의 두 점이 가장 중요하지만, 차폐를 "돌아가는 전기장"으로 설명하려면 뒤의 두 점도 풀어야 한다.
    d_edge = distance_to(pts=[point_tag["src_edge_bot"], point_tag["drn_corner"],
                              point_tag["src_edge_top"], point_tag["dr_bl"]])
    t_edge = threshold(d_edge, s_edge, 0.0, GROWTH)

    # --- 규칙 3: 공기 쐐기 끝점 2곳 ------------------------------------------------------
    # 왜: 끝점에서 쐐기 높이가 0이라, 요소가 높이보다 크면 쐐기 안에 요소가 한 층도 안 들어간다.
    #     끝점에서 거리 d에서의 높이가 d*tan(각도)이므로 크기를 s_edge + tan(각도)/N * d 로 키운다.
    #   - AirBot 끝점 "apex" (0,0): 각도 = WSe2 경사각 theta
    #   - AirTop 끝점 "touch" (또는 l_step = L 이면 "slope_top_end"): 각도 = theta + h-BN 하강선 각도
    theta = math.atan2(p.t_drain, p.l_ramp)                       # WSe2 경사각 (경사 가로 길이 l_ramp 기준)
    y_src_top = p.t_wse2 + p.t_source
    desc = math.atan2(y_src_top - float(p.film_top(p.l_step)), p.l_step)
    top_apex = "touch" if "touch" in point_tag else "slope_top_end"
    slope_at_touch = theta if p.l_step > p.x_lift + 1e-9 else 0.0   # touch 가 평평 구간이면 박막 기울기 0
    t_apex_bot = threshold(distance_to(pts=[point_tag["apex"]]), s_edge, 0.0, math.tan(theta) / N_ACROSS_WEDGE)
    t_apex_top = threshold(distance_to(pts=[point_tag[top_apex]]), s_edge, 0.0, math.tan(slope_at_touch + desc) / N_ACROSS_WEDGE)

    # --- 규칙 4: Top Gate 양 끝 + TG 선의 꺾임점 ------------------------------------------
    # 왜: TG 가장자리에서 전기장이 휘어져 나온다(fringing). TG 선이 꺾이는 점(h-BN이 단차를 따라
    #     내려오는 곳)도 도체 표면의 모서리라 전기장이 집중된다. WSe2에서 30 nm 이상 떨어져 있어
    #     접촉 모서리만큼 촘촘할 필요는 없다.
    tg_pts = ["tg_l", "tg_r", "hbn_kink_src", "hbn_kink_drn"] + [n for n in ("hbn_kink_touch", "hbn_kink_lift") if n in point_tag]
    # lift_top(박막이 꺾이는 점)도 전기장이 집중되는 모서리 → 접촉 모서리와 같은 크기로
    if "lift_top" in point_tag:
        t_edge = threshold(distance_to(pts=[point_tag["src_edge_bot"], point_tag["drn_corner"], point_tag["src_edge_top"],
                                           point_tag["dr_bl"], point_tag["lift_top"]]), s_edge, 0.0, GROWTH)
    d_tg = distance_to(pts=[point_tag[n] for n in tg_pts])
    t_tg = threshold(d_tg, S_TG_EDGE, 0.0, GROWTH)

    # 위 규칙들 중 가장 작은 크기를 최종 mesh 크기로 쓴다.
    f_min = F.add("Min")
    F.setNumbers(f_min, "FieldsList", [t_film, t_edge, t_apex_bot, t_apex_top, t_tg])
    F.setAsBackgroundMesh(f_min)

    # 크기를 "필드"로만 정하도록 다른 크기 지정 방식은 끈다. (수치해석 설정)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeMax", S_MAX)
    # 2D 삼각형 알고리즘 6 = Frontal-Delaunay. Delaunay에 가까운 삼각형을 만들며,
    # DEVSIM의 유한체적(edge 기반) 방식에 잘 맞는다고 알려져 있다.
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    return {"s_film": s_film, "s_edge": s_edge, "wedge_angle_bot_deg": math.degrees(theta),
            "wedge_angle_top_deg": math.degrees(theta + desc), "n_sampling": n_sampling}


# ==============================================================================
# 섹션 5. 실행
# ==============================================================================
def build_config(config):
    """config 이름 하나에 대해 mesh 생성 + 검사. 통과하면 True."""
    import gmsh

    p = geo.CONFIGS[config]
    pts = geo.build_points(p)
    polys = geo.build_polygons(p)
    MSH_NM, MSH_CM = msh_names(config)
    ok, _ = geo.run_checks(pts, polys, p, verbose=False)
    if not ok:
        raise SystemExit(f"geometry 검사 실패({config}): 먼저 python rfet_geometry.py {config} 로 원인을 확인하세요.")

    gmsh.initialize()
    major, minor = (int(v) for v in gmsh.__version__.split(".")[:2])
    if (major, minor) < (4, 7):
        print(f"[주의] gmsh {gmsh.__version__}: 4.7 미만이면 옵션 이름이 달라 오류가 날 수 있습니다.")
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.model.add(f"rfet_{config}")

        point_tag, line_of, loops, surface = build_gmsh_geometry(pts, polys)
        add_physical_groups(polys, line_of, surface)
        info = add_size_fields(pts, point_tag, line_of, loops, p)
        print("mesh 크기 규칙 [nm]:", {k: round(v, 4) if isinstance(v, float) else v for k, v in info.items()})

        gmsh.model.mesh.generate(2)

        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)   # DEVSIM이 읽는 v2 ASCII 형식
        gmsh.option.setNumber("Mesh.SaveAll", 0)            # physical group에 든 요소만 저장
        gmsh.write(MSH_NM)
        if "-gui" in sys.argv:
            gmsh.fltk.run()
    finally:
        gmsh.finalize()

    # DEVSIM은 길이를 cm로 쓰는 것이 관례이므로, 좌표만 nm -> cm로 바꾼 파일을 하나 더 만든다.
    tools.rescale_msh2(MSH_NM, MSH_CM, NM_TO_CM)
    print(f"저장: {MSH_NM} (nm),  {MSH_CM} (cm)")

    # mesh가 geometry를 정확히 채우는지, 이름표가 올바른 선에 붙었는지, 삼각형 품질은 어떤지 확인
    return tools.mesh_report(MSH_NM, pts, polys, p)


def main():
    names = [a for a in sys.argv[1:] if not a.startswith("-")] or list(geo.CONFIGS)
    ok = all([build_config(n) for n in names])
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
