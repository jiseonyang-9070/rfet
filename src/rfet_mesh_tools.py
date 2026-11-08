# -*- coding: utf-8 -*-
"""
rfet_mesh_tools.py
================================================================================
STEP 2-B (보조) : .msh 파일 읽기 / 좌표 단위 변환 / mesh 검사 리포트
gmsh도 DEVSIM도 필요 없다 (numpy만 사용). rfet_mesh_gmsh.py가 불러서 쓴다.

왜 따로 검사하는가
  gmsh가 에러 없이 끝났다고 해서 "내가 원한 mesh"인 것은 아니다. 아래를 숫자로 확인한다.
  (1) 영역별 삼각형 면적의 합 = geometry의 해석적 면적  -> mesh가 영역을 빈틈/겹침 없이 채웠는가
  (2) contact / interface 선의 총 길이 = geometry의 해당 선 길이
                                         -> 이름표(physical group)가 의도한 선에 붙었는가
  (3) 삼각형 품질 (참고용 진단): 최소/최대 각도, 둔각 삼각형 수, Delaunay 조건 위반 edge 수
      DEVSIM의 edge 기반 유한체적법은 Delaunay에 가까운 mesh일 때 가장 안정적이라고 알려져 있다.
      (1)(2)는 틀리면 FAIL(코드 문제), (3)은 FAIL이 아니라 "참고"이다. 어느 정도까지 허용할지는
      STEP 3에서 Poisson을 풀어 보며 정한다.
"""
import numpy as np

import rfet_geometry as geo


# ------------------------------------------------------------------------------
# .msh (gmsh MSH 2.2 ASCII) 읽기
# ------------------------------------------------------------------------------
def read_msh2(path):
    """반환 dict:
         names     : {(차원, physical tag): 이름}
         xy        : (N, 2) 노드 좌표 (파일 단위 그대로)
         tri       : (M, 3) 삼각형을 이루는 노드의 0-기반 index,   tri_phys : (M,) physical tag
         line      : (K, 2) 선 요소의 노드 index,                  line_phys: (K,)
    """
    with open(path, "r") as f:
        text = f.read().split("\n")

    names, ids, xy = {}, [], []
    tri, tri_phys, line, line_phys = [], [], [], []
    i = 0
    while i < len(text):
        s = text[i].strip()
        if s == "$MeshFormat":
            version = text[i + 1].split()[0]
            if not version.startswith("2"):
                raise ValueError(f"MSH 2.x 형식만 지원합니다 (파일은 {version})")
            i += 2
        elif s == "$PhysicalNames":
            n = int(text[i + 1])
            for j in range(n):
                dim, tag, name = text[i + 2 + j].split(None, 2)
                names[(int(dim), int(tag))] = name.strip().strip('"')
            i += 2 + n
        elif s == "$Nodes":
            n = int(text[i + 1])
            for j in range(n):
                t = text[i + 2 + j].split()
                ids.append(int(t[0]))
                xy.append((float(t[1]), float(t[2])))
            i += 2 + n
        elif s == "$Elements":
            n = int(text[i + 1])
            for j in range(n):
                t = text[i + 2 + j].split()
                etype, ntags = int(t[1]), int(t[2])
                phys = int(t[3]) if ntags >= 1 else 0        # 첫 번째 tag = physical group
                nodes = [int(v) for v in t[3 + ntags:]]
                if etype == 2:        # 3-node triangle
                    tri.append(nodes)
                    tri_phys.append(phys)
                elif etype == 1:      # 2-node line
                    line.append(nodes)
                    line_phys.append(phys)
            i += 2 + n
        else:
            i += 1

    lookup = np.full(max(ids) + 1, -1, dtype=np.int64)       # 파일의 노드 번호 -> 0..N-1
    lookup[np.array(ids)] = np.arange(len(ids))
    return {
        "names": names,
        "xy": np.array(xy, dtype=float),
        "tri": lookup[np.array(tri, dtype=np.int64)] if tri else np.zeros((0, 3), dtype=np.int64),
        "tri_phys": np.array(tri_phys, dtype=np.int64),
        "line": lookup[np.array(line, dtype=np.int64)] if line else np.zeros((0, 2), dtype=np.int64),
        "line_phys": np.array(line_phys, dtype=np.int64),
    }


def rescale_msh2(src, dst, factor):
    """노드 좌표(x, y, z)에 factor를 곱해서 새 .msh를 쓴다. (nm -> cm 이면 factor = 1e-7)
    요소 정보(어떤 노드가 삼각형을 이루는지)는 그대로이므로 mesh의 위상은 변하지 않는다."""
    with open(src, "r") as f:
        lines = f.read().split("\n")
    out, i = [], 0
    while i < len(lines):
        out.append(lines[i])
        if lines[i].strip() == "$Nodes":
            n = int(lines[i + 1])
            out.append(lines[i + 1])
            for j in range(n):
                t = lines[i + 2 + j].split()
                x, y, z = (float(v) * factor for v in t[1:4])
                out.append(f"{t[0]} {x:.12e} {y:.12e} {z:.12e}")
            i += 2 + n
        else:
            i += 1
    with open(dst, "w") as f:
        f.write("\n".join(out))


# ------------------------------------------------------------------------------
# 삼각형 품질 계산
# ------------------------------------------------------------------------------
def triangle_angles(xy, tri):
    """각 삼각형의 세 내각 [rad]. 열 k = 꼭짓점 k에서의 각."""
    a, b, c = xy[tri[:, 0]], xy[tri[:, 1]], xy[tri[:, 2]]

    def angle_at(p, q, r):
        u, v = q - p, r - p
        cosv = np.sum(u * v, axis=1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1))
        return np.arccos(np.clip(cosv, -1.0, 1.0))

    return np.column_stack([angle_at(a, b, c), angle_at(b, c, a), angle_at(c, a, b)])


def triangle_areas(xy, tri):
    a, b, c = xy[tri[:, 0]], xy[tri[:, 1]], xy[tri[:, 2]]
    return 0.5 * np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1]))


def edge_opposite_angles(tri, ang):
    """모든 edge에 대해 (그 edge를 쓰는 삼각형 수, 마주보는 각의 합, 마주보는 각 중 첫 번째 값).
    삼각형 수가 2면 영역 안쪽 edge(두 삼각형이 공유), 1이면 영역 경계 edge이다."""
    e = np.concatenate([tri[:, [1, 2]], tri[:, [2, 0]], tri[:, [0, 1]]])   # 꼭짓점 0,1,2의 맞은편 edge
    a = np.concatenate([ang[:, 0], ang[:, 1], ang[:, 2]])
    e = np.sort(e, axis=1)
    key = e[:, 0].astype(np.int64) * (int(e.max()) + 1) + e[:, 1]
    order = np.argsort(key, kind="stable")
    key, a = key[order], a[order]
    _, start, counts = np.unique(key, return_index=True, return_counts=True)
    return counts, np.add.reduceat(a, start), a[start]


# ------------------------------------------------------------------------------
# mesh 검사 리포트
# ------------------------------------------------------------------------------
def mesh_report(msh_path, points, polygons, p: geo.Params, rel_tol=1e-6):
    """검사 결과를 출력하고, (1)(2)가 모두 통과하면 True를 반환한다. 파일 단위는 nm여야 한다."""
    m = read_msh2(msh_path)
    xy, tri = m["xy"], m["tri"]
    ang = triangle_angles(xy, tri)
    area = triangle_areas(xy, tri)
    all_ok = True

    def fail(msg):
        nonlocal all_ok
        all_ok = False
        print("  [FAIL]", msg)

    print(f"\n=== mesh 리포트: {msh_path} ===")
    print(f"노드 {len(xy)}개, 삼각형 {len(tri)}개, 선 요소 {len(m['line'])}개")
    if area.min() <= 0:
        fail(f"면적이 0 이하인 삼각형이 있다 (최소 면적 {area.min():.3e})")
    if np.any(m["tri_phys"] == 0):
        fail("이름표(physical group)가 없는 삼각형이 있다")

    tri_names = {tag: nm for (dim, tag), nm in m["names"].items() if dim == 2}
    line_names = {tag: nm for (dim, tag), nm in m["names"].items() if dim == 1}
    analytic = geo.analytic_areas(p)

    # (1) 영역별 면적 + (3) 영역별 삼각형 품질
    print("\n[영역별]  삼각형수  면적[nm^2]   해석면적     상대오차  | 최소각  최대각  둔각수  "
          "Delaunay위반edge  경계둔각edge")
    for r in geo.REGIONS:
        tag = next((t for t, nm in tri_names.items() if nm == geo.gmsh_region_name(r)), None)
        if tag is None:
            fail(f"physical group {geo.gmsh_region_name(r)} 가 파일에 없다")
            continue
        sel = m["tri_phys"] == tag
        a_sum = float(area[sel].sum())
        rel = abs(a_sum - analytic[r]) / analytic[r]
        degs = np.degrees(ang[sel])
        counts, sums, first = edge_opposite_angles(tri[sel], ang[sel])
        n_del = int(np.sum((counts == 2) & (sums > np.pi + 1e-9)))       # 안쪽 edge: 마주보는 각 합 > 180도
        n_bnd = int(np.sum((counts == 1) & (first > 0.5 * np.pi + 1e-9)))  # 경계 edge: 마주보는 각 > 90도
        if np.any(counts > 2):
            fail(f"{r}: 3개 이상의 삼각형이 공유하는 edge가 있다 (비정상 mesh)")
        print(f"  {r:7s} {sel.sum():8d}  {a_sum:11.2f}  {analytic[r]:11.2f}  {rel:9.2e} | "
              f"{degs.min():6.2f}  {degs.max():6.2f}  {int(np.sum(degs.max(axis=1) > 90 + 1e-9)):6d}  "
              f"{n_del:14d}  {n_bnd:12d}")
        if rel > rel_tol:
            fail(f"{r}: mesh 면적이 geometry와 다르다 (상대오차 {rel:.2e})")

    # (2) contact / interface: 선 요소의 총 길이
    contacts, interfaces, _ = geo.classify_edges(polygons)
    expected = {}
    for (metal, region), keys in contacts.items():
        expected[geo.gmsh_contact_name(metal, region)] = keys
    for (r1, r2), keys in interfaces.items():
        expected[geo.gmsh_interface_name(r1, r2)] = keys
    print("\n[contact / interface 선]  요소수   총길이[nm]   기대길이[nm]")
    for name in sorted(expected):
        exp_len = sum(np.linalg.norm(np.array(points[a]) - np.array(points[b])) for a, b in expected[name])
        tag = next((t for t, nm in line_names.items() if nm == name), None)
        if tag is None:
            fail(f"physical group {name} 가 파일에 없다")
            continue
        seg = m["line"][m["line_phys"] == tag]
        length = float(np.linalg.norm(xy[seg[:, 0]] - xy[seg[:, 1]], axis=1).sum())
        print(f"  {name:20s} {len(seg):7d}  {length:11.3f}  {exp_len:11.3f}")
        if abs(length - exp_len) > rel_tol * exp_len:
            fail(f"{name}: 선 길이가 geometry와 다르다")
    extra = set(line_names.values()) - set(expected)
    if extra:
        fail(f"의도하지 않은 선 이름표가 있다: {sorted(extra)}")

    # 전체 요약 (참고)
    all_edges = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    el = np.linalg.norm(xy[all_edges[:, 0]] - xy[all_edges[:, 1]], axis=1)
    print(f"\n[참고] edge 길이: 최소 {el.min():.3f} nm, 최대 {el.max():.2f} nm;  "
          f"전체 최소각 {np.degrees(ang.min()):.2f} deg, 전체 최대각 {np.degrees(ang.max()):.2f} deg")
    print("[참고] 'Delaunay위반edge'와 '경계둔각edge'는 FAIL이 아니라 진단 값입니다 "
          "(허용 범위는 STEP 3에서 Poisson 결과의 mesh 의존성을 보며 정합니다).")
    print("\n판정:", "(1)(2) 모두 통과" if all_ok else "FAIL이 있음 - 위 로그를 확인")
    return all_ok
