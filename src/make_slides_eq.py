# -*- coding: utf-8 -*-
"""발표용 수식 이미지 (matplotlib mathtext, 투명 배경) -> eq/<name>.png + eq/index.json (가로세로비)"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/claude/rfet_ppt/eq"
os.makedirs(OUT, exist_ok=True)
plt.rcParams["mathtext.fontset"] = "cm"

EQ = {
    # 정전기
    "poisson":   r"$\nabla\cdot\left(\varepsilon\,\nabla\psi\right) = -\rho,\qquad \rho = q\,(p-n)$",
    "cap":       r"$C = \dfrac{\varepsilon_0\varepsilon_r}{d},\qquad Q = C\,V$",
    "superpos":  r"$\psi(\mathbf{r}) = V_{TG}\,\psi_{TG}(\mathbf{r}) + V_{BG}\,\psi_{BG}(\mathbf{r}) + V_S\,\psi_S(\mathbf{r}) + V_D\,\psi_D(\mathbf{r})$",
    "gauss":     r"$\sum_{\mathrm{edge}} \varepsilon\,\dfrac{\psi_{n0}-\psi_{n1}}{L_{\mathrm{edge}}}\,A_{\mathrm{edge}} = Q_{\mathrm{node}}$",
    # 밴드 · 쇼트키
    "band":      r"$E_c = -q\psi - \chi,\qquad E_v = E_c - E_g$",
    "schottky":  r"$\varphi_{Bn} = E_c - E_{F,m},\qquad \varphi_{Bp} = E_g - \varphi_{Bn}$",
    "contact":   r"$\psi_{\mathrm{contact}} = V - \dfrac{\varphi_{Bn}+\chi}{q},\qquad \psi_{\mathrm{gate}} = V_g - \dfrac{\Phi_m}{q}$",
    "thermionic":r"$I \propto \exp\left(-\dfrac{\varphi_B}{k_BT}\right),\qquad k_BT = 25.9\ \mathrm{meV}$",
    "wkb":       r"$T \approx \exp\left(-\dfrac{2}{\hbar}\int_0^{w}\sqrt{2m^*\left(\varphi(x)-E\right)}\,dx\right)$",
    # 캐리어
    "dos2d":     r"$g_{2D} = \dfrac{g_v\,m_d}{\pi\hbar^2},\qquad m_d=\sqrt{m_l m_t},\qquad N_{c,2D} = g_{2D}\,k_BT$",
    "fd":        r"$n = N_{c,2D}\,\ln\left(1+e^{\eta}\right),\qquad \eta = \dfrac{E_F - E_c}{k_BT}$",
    "fdlimits":  r"$\eta \ll 0:\ n \approx N_c e^{\eta}\ \ (\mathrm{Boltzmann}),\qquad \eta \gg 0:\ n \approx N_c\,\eta$",
    "nc14":      r"$N_c = 14\,N_{c,2D}\,/\,9.1\ \mathrm{nm}$",
    # 휨
    "beam":      r"$D\,\dfrac{d^4y}{dx^4} = 0 \;\Rightarrow\; y(x) = h\,(3u^2 - 2u^3),\quad u = x/\ell$",
    "bend":      r"$U_b = \dfrac{D}{2}\int_0^{\ell}\left(\dfrac{d^2y}{dx^2}\right)^{2}dx = \dfrac{6\,D\,h^2}{\ell^3},\qquad D = \dfrac{E\,t^3}{12(1-\nu^2)}$",
    "lstar":     r"$U(\ell) = \dfrac{6Dh^2}{\ell^3} + \Gamma\,\ell \;\Rightarrow\; \ell^* = \left(\dfrac{18\,D\,h^2}{\Gamma}\right)^{1/4} \approx 217\ \mathrm{nm}$",
    "strain":    r"$\epsilon_{\max} = \dfrac{t}{2R_{\min}},\qquad R_{\min} = \dfrac{\ell^2}{6h}\ \Rightarrow\ \epsilon_{\max} = 4.1\,\% < 7.3\,\%$",
    # 수송
    "dd":        r"$\mathbf{J}_n = q\mu_n n\,\mathbf{E} + qD_n\nabla n,\qquad \mathbf{J}_p = q\mu_p p\,\mathbf{E} - qD_p\nabla p$",
    "cont":      r"$\nabla\cdot\mathbf{J}_n = 0,\qquad \nabla\cdot\mathbf{J}_p = 0\quad(\mathrm{steady\;state})$",
    "einstein":  r"$D = \mu\,k_BT/q$",
}

index = {}
from PIL import Image
for name, tex in EQ.items():
    fig = plt.figure(figsize=(12, 2))
    fig.text(0.02, 0.5, tex, fontsize=26, color="#1A1A1A", va="center")
    path = os.path.join(OUT, f"{name}.png")
    fig.savefig(path, dpi=300, transparent=True, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    im = Image.open(path); index[name] = {"ratio": im.width / im.height, "h_in": im.height / 300}
json.dump(index, open(os.path.join(OUT, "index.json"), "w"))
print("ok", len(index))
