# -*- coding: utf-8 -*-
"""
rfet_poisson_devsim.py
================================================================================
STEP 3-C : DEVSIM 으로 Poisson 방정식을 풀어 단위 응답 ψ_S, ψ_D, ψ_TG, ψ_BG 를 구하고 .npz 로 저장한다.
          (후처리는 rfet_post.py, 독립 참조해는 rfet_fem_reference.py)

준비:  python rfet_mesh_gmsh.py <config>   ->  rfet_<config>_cm.msh
실행:  python rfet_poisson_devsim.py bridge [perp|para]
출력:  rfet_devsim_<config>_<variant>.npz   (rfet_post.py 가 읽는 공통 형식)

--------------------------------------------------------------------------------
물리 모델 (이 파일이 DEVSIM 에게 시키는 것)
--------------------------------------------------------------------------------
  영역마다   ∇·(ε ∇ψ) = 0            (ρ = 0: rfet_materials 섹션 5)
  접점에서   ψ = V_금속               (Dirichlet. 금속은 이상 등전위체)
  계면에서   ψ 연속, (ε∇ψ)·n 연속     (전하 없는 유전체 계면)
  그 외 외곽 (ε∇ψ)·n = 0              (DEVSIM 의 자연 경계조건: 아무것도 지정하지 않으면 이것이 된다)

DEVSIM 이 이것을 어떻게 이산화하는가 (수치 방법)
  유한체적(box) 방법. 각 노드 주위의 제어체적에서 전속 밀도 D = -ε∇ψ 의 유출 합 = 0 을 세운다.
  D 는 "edge 모델"로, 두 노드를 잇는 edge 방향 성분만 사용한다:  D_edge = ε (ψ_n0 - ψ_n1) / L_edge.
  -> 이 때문에 ε 는 영역별 스칼라여야 한다 (원칙 8 의 "스칼라 단순화"가 생기는 지점).
     텐서 ε 는 요소(element) 모델로 넣어야 하는데 STEP 3 에서는 구현하지 않고,
     스칼라 단순화의 오차는 rfet_fem_reference.py 의 텐서 계산으로 잰다.
  선형 문제이므로 Newton 반복 1~2회에 수렴해야 한다 (수렴 안 하면 설정 오류).

이름 규칙: 모든 영역에서 방정식 이름을 "PotentialEquation" 으로 같게 둔다.
  DEVSIM 의 interface_equation(type="continuous") 는 같은 이름의 방정식을 두 영역에서 찾아 묶기 때문이다.
"""
import sys

import numpy as np
import devsim

import rfet_geometry as geo
import rfet_materials as mat
import rfet_devsim_load as loader

CM_TO_NM = 1.0e7


# ==============================================================================
# 섹션 1. 영역별 Poisson 설정
# ==============================================================================
def setup_region_poisson(device, region, eps_rel):
    """한 영역에 Poisson 방정식을 정의한다. eps_rel: 상대 유전율(스칼라)."""
    # [문헌값/모델] 유전율 ε = ε_r ε0 [F/cm]. 값의 출처는 rfet_materials.py 참조.
    devsim.set_parameter(device=device, region=region, name="Permittivity", value=eps_rel * mat.EPS0_F_PER_CM)

    # 미지수: 노드마다 전위 ψ [V]
    devsim.node_solution(device=device, region=region, name="Potential")
    # edge 의 양 끝 노드 값 Potential@n0, Potential@n1 을 쓸 수 있게 한다
    devsim.edge_from_node_model(device=device, region=region, node_model="Potential")

    # edge 방향 전기장 E_edge = (ψ_n0 - ψ_n1) / L_edge  [V/cm]   (EdgeInverseLength 는 DEVSIM 내장 모델 1/L_edge)
    devsim.edge_model(device=device, region=region, name="ElectricField",
                      equation="(Potential@n0 - Potential@n1)*EdgeInverseLength")
    devsim.edge_model(device=device, region=region, name="ElectricField:Potential@n0", equation="EdgeInverseLength")
    devsim.edge_model(device=device, region=region, name="ElectricField:Potential@n1", equation="-EdgeInverseLength")

    # edge 전속밀도 D_edge = ε E_edge  [C/cm^2].  이것이 유한체적 식의 "flux" 가 된다.
    devsim.edge_model(device=device, region=region, name="PotentialEdgeFlux", equation="Permittivity*ElectricField")
    devsim.edge_model(device=device, region=region, name="PotentialEdgeFlux:Potential@n0",
                      equation="Permittivity*ElectricField:Potential@n0")
    devsim.edge_model(device=device, region=region, name="PotentialEdgeFlux:Potential@n1",
                      equation="Permittivity*ElectricField:Potential@n1")

    # 방정식: Σ_edge D_edge · (제어체적 면) = 전하(=0).  node_model 을 비워 두면 우변 전하가 0 이다 (ρ = 0 가정).
    devsim.equation(device=device, region=region, name="PotentialEquation", variable_name="Potential",
                    edge_model="PotentialEdgeFlux", variable_update="default")


# ==============================================================================
# 섹션 2. 접점(Dirichlet)과 계면(연속) 조건
# ==============================================================================
def setup_contact(device, contact, region, metal):
    """접점 노드에서 ψ = V_금속. 전압은 parameter '<금속>_bias' 로 두고 나중에 바꾼다.
    한 금속이 여러 영역에 닿으면(Source: WSe2, AirTop, hBN) 접점이 여러 개지만 bias parameter 는 금속 하나당 하나다."""
    bias = f"{metal}_bias"
    if bias not in devsim.get_parameter_list(device=device):
        devsim.set_parameter(device=device, name=bias, value=0.0)
    bc = f"{contact}_bc"
    devsim.contact_node_model(device=device, contact=contact, name=bc, equation=f"Potential - {bias}")
    devsim.contact_node_model(device=device, contact=contact, name=f"{bc}:Potential", equation="1")
    # edge_charge_model 을 주면 접점에 유도된 전하(= 전속 적분)를 나중에 읽을 수 있다 (게이트 용량 검증용)
    devsim.contact_equation(device=device, contact=contact, name="PotentialEquation",
                            node_model=bc, edge_charge_model="PotentialEdgeFlux")


def setup_interface(device, interface):
    """계면: 두 영역의 ψ 가 같다 (type='continuous' 가 두 영역의 flux 식도 합쳐 D 법선 연속을 만든다)."""
    devsim.interface_model(device=device, interface=interface, name="continuousPotential",
                           equation="Potential@r0 - Potential@r1")
    devsim.interface_model(device=device, interface=interface, name="continuousPotential:Potential@r0", equation="1")
    devsim.interface_model(device=device, interface=interface, name="continuousPotential:Potential@r1", equation="-1")
    devsim.interface_equation(device=device, interface=interface, name="PotentialEquation",
                              interface_model="continuousPotential", type="continuous")


# ==============================================================================
# 섹션 3. 전체 조립과 풀이
# ==============================================================================
def build(config, variant):
    loader.CONFIG = config
    device = f"rfet_{config}"
    # rfet_devsim_load.load_mesh 는 모듈 상수(MESH_NAME 등)를 쓰므로 config 에 맞게 다시 계산한다
    loader.MESH_NAME, loader.DEVICE_NAME = f"rfet_mesh_{config}", device
    loader.P = geo.CONFIGS[config]
    loader.POLYGONS = geo.build_polygons(loader.P)
    loader.load_mesh(f"rfet_{config}_cm.msh")

    eps = mat.scalar_eps(variant)
    for r in geo.REGIONS:
        setup_region_poisson(device, r, eps[r])
    contacts, interfaces, _ = geo.classify_edges(loader.POLYGONS)
    for (metal, region) in sorted(contacts):
        setup_contact(device, geo.contact_name(metal, region), region, metal)
    for (r0, r1) in sorted(interfaces):
        setup_interface(device, geo.interface_name(r0, r1))
    return device


def solve_unit_cases(device):
    results = {}
    for metal in geo.METALS:
        for m in geo.METALS:
            devsim.set_parameter(device=device, name=f"{m}_bias", value=1.0 if m == metal else 0.0)
        # [수치해석 설정] 선형 문제라 1~2 회 반복에 수렴해야 한다. 허용오차는 전위 1e-10 V 수준.
        devsim.solve(type="dc", absolute_error=1e-10, relative_error=1e-12, maximum_iterations=10)
        results[metal] = gather_nodes(device)
        print(f"  unit case {metal:6s}: psi 범위 [{results[metal]['psi'].min():+.4f}, {results[metal]['psi'].max():+.4f}] V")
    return results


def gather_nodes(device):
    """모든 영역의 노드 좌표(nm)와 ψ 를 하나의 배열로 모은다. 계면 노드는 두 영역에 중복되므로 좌표로 합친다."""
    xs, ys, ps = [], [], []
    for r in geo.REGIONS:
        xs += list(devsim.get_node_model_values(device=device, region=r, name="x"))
        ys += list(devsim.get_node_model_values(device=device, region=r, name="y"))
        ps += list(devsim.get_node_model_values(device=device, region=r, name="Potential"))
    return {"x": np.array(xs) * CM_TO_NM, "y": np.array(ys) * CM_TO_NM, "psi": np.array(ps)}


def export_npz(config, variant, results):
    """rfet_post.py 공통 형식으로 저장. 삼각형 연결 정보는 nm mesh 파일에서 가져오고,
    DEVSIM 노드(영역별, 계면 중복)의 ψ 를 좌표 일치로 mesh 노드에 옮긴다."""
    import rfet_mesh_tools as tools
    m = tools.read_msh2(f"rfet_{config}_nm.msh")
    xy, tri = m["xy"], m["tri"]
    tri_names = {t: nm for (d, t), nm in m["names"].items() if d == 2}
    tri_region = np.array([tri_names[t][2:] for t in m["tri_phys"]])
    from scipy.spatial import cKDTree
    tree = cKDTree(xy)
    out = {}
    for metal, res in results.items():
        d, idx = tree.query(np.column_stack([res["x"], res["y"]]))
        if d.max() > 1e-4:
            raise RuntimeError(f"DEVSIM 노드와 mesh 노드가 일치하지 않는다 (최대 거리 {d.max():.3e} nm)")
        psi = np.full(len(xy), np.nan)
        psi[idx] = res["psi"]            # 계면 중복 노드는 같은 값이어야 한다 (ψ 연속) -> 마지막 값으로 덮어써도 무방
        if np.isnan(psi).any():
            raise RuntimeError("ψ 가 채워지지 않은 mesh 노드가 있다")
        out[f"psi_{metal}"] = psi
    path = f"rfet_devsim_{config}_{variant}.npz"
    np.savez(path, xy=xy, tri=tri, tri_region=tri_region, solver="devsim", config=config, variant=variant, **out)
    print("  저장:", path)
    return path


def main():
    config = sys.argv[1] if len(sys.argv) > 1 else "bridge"
    variant = sys.argv[2] if len(sys.argv) > 2 else "perp"
    print(f"=== DEVSIM Poisson: config={config}, ε variant={variant} (스칼라) ===")
    device = build(config, variant)
    results = solve_unit_cases(device)
    export_npz(config, variant, results)


if __name__ == "__main__":
    main()
