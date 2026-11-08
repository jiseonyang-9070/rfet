# 참고 문헌 (전부 1차 문헌; 사용 위치 명시)

## 기준 논문
- **[Jiao 2026]** F. Jiao et al., "Reconfigurable WSe₂ transistors enabled by complementary electrostatic shielding of source and drain electrodes", *Appl. Phys. Lett.* **128**, 263504 (2026). DOI 10.1063/5.0338649. 본문 6쪽만 사용(Supplementary 미확보). → 두께·채널 길이·금속·전압 범위 (docs/01 1-A).

## 유전율
- **[Laturia 2018]** A. Laturia, M. L. Van de Put, W. G. Vandenberghe, "Dielectric properties of hexagonal boron nitride and transition metal dichalcogenides: from monolayer to bulk", *npj 2D Mater. Appl.* **2**, 6 (2018). DOI 10.1038/s41699-018-0050-x. Table 1 (h-BN), Table 2 (WSe₂), Table 3 (층 두께 6.52 Å). → `rfet_materials.py`. **원문 확인 2026-11-09** (par.nsf.gov 공개본).
- **[Sze & Ng 2007]** S. M. Sze, K. K. Ng, *Physics of Semiconductor Devices*, 3rd ed., Wiley (2007), Appendix "Properties of SiO₂ and Si₃N₄": ε_r = 3.9. (2차 문헌, 표준값) → `rfet_materials.py`.
- **[CODATA 2018]** NIST, ε₀, k_B, ħ, m₀, q. → `rfet_materials.py`, `rfet_semiconductor.py`.

## 밴드 구조·물성
- **[Wickramaratne 2014]** D. Wickramaratne, F. Zahid, R. K. Lake, "Electronic and thermoelectric properties of few-layer transition metal dichalcogenides", *J. Chem. Phys.* **140**, 124710 (2014). DOI 10.1063/1.4869142 (arXiv:1401.0502). Table II 유효질량(bulk WSe₂ CB Σ점 0.489/0.643, VB Γ점 0.997; 1L 은 K점 0.345/0.341), Table III 밴드갭 1.188 eV (PBE+SOC), Table I 실험 인용값 1.20 eV. → `rfet_semiconductor.py`. **원문 확인 2026-11-09** (arXiv 1401.0502).
- **[McDonnell 2014]** S. McDonnell et al., "Hole contacts on transition metal dichalcogenides: Interface chemistry and band alignments", *ACS Nano* **8**, 6265 (2014). DOI 10.1021/nn501728w. Table 3 (SKexp 행): IE = 5.19 ± 0.1 eV (Schlaf et al. 실험), E_g = 1.16 ± 0.03 eV (Kautek et al. 실험), χ = 4.03 ± 0.1 eV (= IE − E_g 유도; LDA 계산도 4.03). → `rfet_semiconductor.py`. **원문 확인 2026-11-09** (Berkeley 공개본).
- **[Smyth 2017]** C. M. Smyth et al., "WSe₂-contact metal interface chemistry and band alignment under high vacuum and ultra high vacuum deposition conditions", *2D Mater.* **4**, 025084 (2017). DOI 10.1088/2053-1583/aa6bea. 본문: UHV Au / bulk WSe₂ 전자 Schottky 장벽 0.53 eV ("measured in this work"; 표/그림 없음); E_g = 1.3 ± 0.1 eV (STS, ref.44 인용), IE 5.33 eV (ref.68 인용). → Drain 장벽. **원문 확인 2026-11-09**.

## 접점 장벽
- **[Jang 2022]** J. Jang et al., "Fermi-level pinning-free WSe₂ transistors via 2D van der Waals metal contacts and their circuits", *Adv. Mater.* **34**, 2109899 (2022). DOI 10.1002/adma.202109899. Fig. 3f: 증착 Ti/Au/Pd on 8–12 nm WSe₂ 전자 장벽 "≈190 to 250 meV" (금속 일함수에 거의 무관), pinning factor S = 0.03; 온도 의존 I–V(열전자, flat-band)로 추출. → Source 장벽 0.22 eV (범위 중앙값; Pd 개별값은 논문에 없음). **원문 확인 2026-11-09** (DNB 공개본).
- **[Prakash 2017]** A. Prakash, H. Ilatikhameneh, P. Wu, J. Appenzeller, "Understanding contact gating in Schottky barrier transistors from 2D channels", *Sci. Rep.* **7**, 12596 (2017). Ni/WSe₂ 0.4–0.5 eV. → 장벽 산포 참고.

## h-BN 역학 (단차 형상 추정)
- **[Falin 2017]** A. Falin et al., "Mechanical properties of atomically thin boron nitride and the role of interlayer interactions", *Nat. Commun.* **8**, 15815 (2017). DOI 10.1038/ncomms15815. E = 0.865 ± 0.073 (1L), 0.856 ± 0.003 TPa (9L), AFM 압입. → `sag_step_elastic`. **원문 확인 2026-11-09** (PMC 공개본).
- **[Koenig 2011]** S. P. Koenig, N. G. Boddeti, M. L. Dunn, J. S. Bunch, "Ultrastrong adhesion of graphene membranes", *Nat. Nanotechnol.* **6**, 543 (2011). DOI 10.1038/nnano.2011.123. Γ = 0.45 J/m² (단층 그래핀/SiO₂), 0.31 J/m² (2–5층). → **차용값**; h-BN/WSe₂ 값은 미확보. 같은 호 News & Views(R. Huang)로 수치 확인.

## 소프트웨어
- DEVSIM 2.11.2 — J. E. Sanchez, *DEVSIM: A TCAD semiconductor device simulator*, https://devsim.org (Apache 2.0).
- gmsh 4.15.2 — C. Geuzaine, J.-F. Remacle, "Gmsh: a three-dimensional finite element mesh generator with built-in pre- and post-processing facilities", *Int. J. Numer. Meth. Eng.* **79**, 1309 (2009).
- numpy, scipy, matplotlib.

## 참고만 한 코드 (따르지 않음)
- 팀 저장소 `eungoooooooo00/WSe2-RFET-scaling-with-DEVSIM`: 평면 구조, Boltzmann 통계, DD. 여기서 가져온 것은 "S/D 장벽 동일 대조군" 발상 하나 (docs/04 4-5).
