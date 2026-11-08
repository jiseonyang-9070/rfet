# -*- coding: utf-8 -*-
"""
rfet_devsim_load.py
================================================================================
STEP 2-C : rfet_cm.msh 를 DEVSIM에 불러오고, DEVSIM 안에서 "내가 의도한 구조"가 되었는지 확인한다.

준비:  pip install devsim         (그리고 먼저 python rfet_mesh_gmsh.py 로 rfet_<config>_cm.msh 를 만들어 둔다)
실행:  python rfet_devsim_load.py bridge      (config 이름: rfet_geometry.CONFIGS 의 키)

이 파일이 하는 일
  1) .msh 안의 이름표(physical group)를 DEVSIM의 region / contact / interface 이름에 연결한다.
  2) DEVSIM이 실제로 만든 region, contact, interface 목록과 좌표 범위를 geometry와 비교한다.
  3) mesh를 파일(tecplot/vtk)로 내보내서 눈으로 볼 수 있게 한다.

이 파일이 아직 하지 않는 일  (STEP 3에서 한다)
  - 재료 물성(유전율 등), Poisson 방정식, 전위 경계조건(전압), 전하밀도, 해 구하기
  -> 지금 만든 device는 "모양과 이름표만 있는 빈 틀"이다.

DEVSIM 개념 세 가지 (교수님께 설명할 때)
  - region    : 재료가 같은 연속 영역. 방정식은 region마다 따로 정의한다. (여기서는 4개)
  - contact   : region의 경계 중 전극(금속)과 닿는 선. 나중에 전압(Dirichlet 경계조건)을 건다.
                DEVSIM의 contact는 "하나의 region"에만 속한다. 그래서 Source가 WSe2와 h-BN에
                모두 닿는 이 구조에서는 Source_WSe2, Source_hBN 두 contact를 만들고,
                STEP 3에서 두 contact에 같은 전압을 걸어 준다.
  - interface : 서로 다른 두 region이 맞닿는 선. 나중에 "전위는 연속, 전속밀도 D의 수직성분은 연속"
                조건(전하 없는 계면)을 여기서 걸어 준다.
"""
import sys

import devsim

import rfet_geometry as geo

# ==============================================================================
# 섹션 1. 설정
# ==============================================================================
CONFIG = (sys.argv[1] if len(sys.argv) > 1 else "bridge")   # rfet_geometry.CONFIGS 의 키
MSH_FILE = f"rfet_{CONFIG}_cm.msh"   # [수치해석 설정] rfet_mesh_gmsh.py 가 만든 cm 단위 mesh
MESH_NAME = f"rfet_mesh_{CONFIG}"    # DEVSIM 안에서 mesh를 부르는 이름
DEVICE_NAME = f"rfet_{CONFIG}"       # DEVSIM 안에서 device를 부르는 이름
P = geo.CONFIGS[CONFIG]
POLYGONS = geo.build_polygons(P)
CM_TO_NM = 1.0e7              # DEVSIM 내부 길이는 cm. 사람이 읽기 쉽게 nm로 바꿔 출력할 때 쓴다.


# ==============================================================================
# 섹션 2. mesh 불러오기: gmsh 이름표 -> DEVSIM 이름
# ==============================================================================
def load_mesh(msh_file):
    # (a) .msh 파일을 읽는다. 아직 region/contact는 없다.
    devsim.create_gmsh_mesh(mesh=MESH_NAME, file=msh_file)

    # (b) 면(2D) 이름표 -> region.  material은 이름표일 뿐, 물성값은 STEP 3에서 넣는다.
    for r in geo.REGIONS:
        devsim.add_gmsh_region(mesh=MESH_NAME, gmsh_name=geo.gmsh_region_name(r),
                               region=r, material=geo.REGION_MATERIAL[r])

    # (c) 선(1D) 이름표 -> contact / interface. 어느 이름이 있어야 하는지는 geometry가 정한다.
    contacts, interfaces, _ = geo.classify_edges(POLYGONS)
    for (metal, region) in sorted(contacts):
        devsim.add_gmsh_contact(mesh=MESH_NAME, gmsh_name=geo.gmsh_contact_name(metal, region),
                                region=region, name=geo.contact_name(metal, region), material="metal")
    for (r0, r1) in sorted(interfaces):
        devsim.add_gmsh_interface(mesh=MESH_NAME, gmsh_name=geo.gmsh_interface_name(r0, r1),
                                  region0=r0, region1=r1, name=geo.interface_name(r0, r1))

    # (d) mesh를 확정하고 device를 만든다. 이 뒤에는 region/contact를 더 추가할 수 없다.
    devsim.finalize_mesh(mesh=MESH_NAME)
    devsim.create_device(mesh=MESH_NAME, device=DEVICE_NAME)


# ==============================================================================
# 섹션 3. DEVSIM 안의 구조가 geometry와 같은지 확인
# ==============================================================================
def check_device(p: geo.Params):
    pts = geo.build_points(p)
    ok = True

    def report(name, passed, detail=""):
        nonlocal ok
        ok = ok and bool(passed)
        print(f"  [{'OK  ' if passed else 'FAIL'}] {name}  {detail}")

    contacts, interfaces, _ = geo.classify_edges(POLYGONS)
    exp_regions = set(geo.REGIONS)
    exp_contacts = {geo.contact_name(m, r) for (m, r) in contacts}
    exp_interfaces = {geo.interface_name(a, b) for (a, b) in interfaces}

    got_regions = set(devsim.get_region_list(device=DEVICE_NAME))
    got_contacts = set(devsim.get_contact_list(device=DEVICE_NAME))
    got_interfaces = set(devsim.get_interface_list(device=DEVICE_NAME))
    report("region 목록 일치", got_regions == exp_regions, f"차이: {got_regions ^ exp_regions}")
    report("contact 목록 일치", got_contacts == exp_contacts, f"차이: {got_contacts ^ exp_contacts}")
    report("interface 목록 일치", got_interfaces == exp_interfaces, f"차이: {got_interfaces ^ exp_interfaces}")

    # contact가 의도한 region에 붙었는지
    for (metal, region) in sorted(contacts):
        name = geo.contact_name(metal, region)
        try:
            regs = list(devsim.get_region_list(device=DEVICE_NAME, contact=name))
            report(f"contact {name} 는 region {region} 에 속함", regs == [region], f"(실제 {regs})")
        except Exception as e:      # 이 호출이 버전에 따라 없을 수 있으므로 실패해도 중단하지 않는다
            print(f"  [생략] contact {name} 의 region 조회 실패: {e}")

    # region별 노드 수와 좌표 범위 (DEVSIM 좌표는 cm -> nm로 환산해서 geometry와 비교)
    print("\n  region   노드수   x범위[nm]              y범위[nm]")
    for r in geo.REGIONS:
        xs = devsim.get_node_model_values(device=DEVICE_NAME, region=r, name="x")
        ys = devsim.get_node_model_values(device=DEVICE_NAME, region=r, name="y")
        x0, x1 = min(xs) * CM_TO_NM, max(xs) * CM_TO_NM
        y0, y1 = min(ys) * CM_TO_NM, max(ys) * CM_TO_NM
        poly = geo.polygon_xy(pts, POLYGONS[r])
        ex0, ex1, ey0, ey1 = poly[:, 0].min(), poly[:, 0].max(), poly[:, 1].min(), poly[:, 1].max()
        print(f"  {r:7s} {len(xs):6d}   [{x0:9.3f}, {x1:9.3f}]   [{y0:8.3f}, {y1:8.3f}]")
        same = max(abs(x0 - ex0), abs(x1 - ex1), abs(y0 - ey0), abs(y1 - ey1)) < 1e-4
        report(f"{r} 좌표 범위 = geometry", same, f"(기대 x[{ex0:.1f},{ex1:.1f}] y[{ey0:.1f},{ey1:.1f}])")
    return ok


# ==============================================================================
# 섹션 4. 실행
# ==============================================================================
def main():
    load_mesh(MSH_FILE)
    print("=== DEVSIM에 불러온 구조 확인 ===")
    ok = check_device(P)

    # mesh를 파일로 저장해서 Paraview 등으로 볼 수 있게 한다. (지원 형식은 DEVSIM 버전마다 다르다)
    for kind in ("vtk", "tecplot"):
        try:
            devsim.write_devices(file=f"rfet_{CONFIG}_mesh_check", type=kind)
            print(f"mesh 저장 ({kind}): rfet_{CONFIG}_mesh_check*")
            break
        except Exception as e:
            print(f"  [생략] {kind} 저장 실패: {e}")

    print("\n전체 판정:", "모두 통과" if ok else "FAIL이 있음 - 위 로그를 확인")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
