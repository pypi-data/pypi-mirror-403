# ============================================================
# Piecewise Moment–Curvature (M–kappa) for RC section
#
# Segment I   (State I, uncracked, linear-elastic):   0 .. kappa_cr
# Segment II  (State IIa, cracked, steel elastic):    kappa_cr .. kappa_y_first
# Segment III (State IIb, cracked, steel plastic):    kappa_y_first .. failure
#
# UNITS: m, MN, MN*m, MPa (= MN/m^2)
# SIGN:  eps>0 tension, eps<0 compression
# eps(z) = eps0 - kappa*z
# My = -∫ sigma * z dA  (sagging positive)
# ============================================================

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

# ----------------------------
# Data structures
# ----------------------------


@dataclass
class ConcreteMesh:
    y: np.ndarray  # [m]
    z: np.ndarray  # [m]
    A: np.ndarray  # [m^2]


@dataclass
class SteelBars:
    y: np.ndarray  # [m]
    z: np.ndarray  # [m]
    As: np.ndarray  # [m^2]


# ----------------------------
# Material laws (State II)
# ----------------------------


class ConcreteCrackedLinear:
    """Concrete: compression linear (eps<0), tension zero (eps>=0). Stress in MPa (neg. in compression)."""

    def __init__(self, Ec_MPa: float):
        self.Ec = float(Ec_MPa)

    def sigma(self, eps: np.ndarray) -> np.ndarray:
        return np.where(eps < 0.0, self.Ec * eps, 0.0)


class ConcreteEC2ParabolaRectangle:
    """
    EC2 parabola-rectangle stress-strain law for concrete (compression only).
    Stress in MPa (negative in compression). Tension = 0 (State II).
    """

    def __init__(self, fcd: float, eps_c2: float = 2.0e-3, eps_cu: float = 3.5e-3):
        self.fcd = float(fcd)
        self.eps_c2 = float(eps_c2)
        self.eps_cu = float(eps_cu)

    def sigma(self, eps: np.ndarray) -> np.ndarray:
        sig = np.zeros_like(eps, dtype=float)

        comp = eps < 0.0
        if not np.any(comp):
            return sig

        idx_comp = np.where(comp)[0]
        e = -eps[idx_comp]  # positive compression strain

        mask_p = e <= self.eps_c2
        sig[idx_comp[mask_p]] = -self.fcd * (1.0 - (1.0 - e[mask_p] / self.eps_c2) ** 2)

        mask_r = (e > self.eps_c2) & (e <= self.eps_cu)
        sig[idx_comp[mask_r]] = -self.fcd

        # beyond eps_cu: keep 0 here; failure handled outside
        return sig


class SteelElasticPerfectlyPlastic:
    """Steel: linear elastic up to yield, then perfectly plastic (stress capped at +/- fyd). Stress in MPa."""

    def __init__(self, Es_MPa: float, fyd_MPa: float):
        self.Es = float(Es_MPa)
        self.fyd = float(fyd_MPa)
        self.eps_y = self.fyd / self.Es

    def sigma(self, eps: np.ndarray) -> np.ndarray:
        return np.clip(self.Es * eps, -self.fyd, self.fyd)


# ----------------------------
# Simple section meshing
# ----------------------------


def mesh_rectangle(b: float, h: float, ny: int = 60, nz: int = 120) -> ConcreteMesh:
    y = np.linspace(-b / 2, b / 2, ny)
    z = np.linspace(-h / 2, h / 2, nz)
    dy, dz = y[1] - y[0], z[1] - z[0]
    Y, Z = np.meshgrid(y, z, indexing="ij")
    A = np.full(Y.size, dy * dz, dtype=float)
    return ConcreteMesh(Y.ravel(), Z.ravel(), A)


def mesh_circle(R, nr=40, ntheta=120):
    r = np.linspace(0, R, nr + 1)
    theta = np.linspace(0, 2 * np.pi, ntheta, endpoint=False)

    y, z, A = [], [], []

    for i in range(nr):
        r1, r2 = r[i], r[i + 1]
        for t in theta:
            rm = 0.5 * (r1 + r2)
            y.append(rm * np.cos(t))
            z.append(rm * np.sin(t))
            A.append(0.5 * (r2**2 - r1**2) * (2 * np.pi / ntheta))

    return ConcreteMesh(y=np.array(y), z=np.array(z), A=np.array(A))


def circle_rebar(n_bars, r_s, As_bar):
    theta = np.linspace(0, 2 * np.pi, n_bars, endpoint=False)

    y = r_s * np.cos(theta)
    z = r_s * np.sin(theta)
    As = np.full(n_bars, As_bar)

    return SteelBars(y=y, z=z, As=As)


def mesh_T(bf, tf, bw, h, ny=40, nz=80):
    meshes = []

    # Flansch
    meshes.append(mesh_rectangle(b=bf, h=tf, ny=ny, nz=int(nz * tf / h)))

    # Steg
    web = mesh_rectangle(
        b=bw, h=h - tf, ny=int(ny * bw / bf), nz=int(nz * (h - tf) / h)
    )
    web.z += -(tf / 2)  # Verschiebung nach unten
    meshes.append(web)

    y = np.concatenate([m.y for m in meshes])
    z = np.concatenate([m.z for m in meshes])
    A = np.concatenate([m.A for m in meshes])

    return ConcreteMesh(y=y, z=z, A=A)


# ----------------------------
# Section properties + cracking (State I)
# ----------------------------


def section_properties_from_mesh(
    conc: ConcreteMesh,
) -> Tuple[float, float, float, float]:
    """
    About y-axis bending:
      A  = ∫ dA
      Iy = ∫ z^2 dA
    Returns: A, Iy, z_top, z_bot
    """
    A = float(np.sum(conc.A))
    Iy = float(np.sum(conc.A * conc.z**2))
    z_top = float(np.max(conc.z))
    z_bot = float(np.min(conc.z))
    return A, Iy, z_top, z_bot


def cracking_M_with_N(
    A: float, Iy: float, z_t: float, N_Ed: float, fctm: float
) -> float:
    """
    State I, uncracked, linear stress distribution:
      sigma(z) = N/A - (M/Iy)*z
    cracking at tension edge z=z_t:
      N/A - (Mcr/Iy)*z_t = fctm
      => Mcr = (N/A - fctm) * Iy / z_t

    Conventions:
      N_Ed > 0 tension, < 0 compression
      z_t  = coordinate of tension edge (for sagging usually bottom => z_t < 0)
      fctm > 0
    """
    if (N_Ed / A) >= fctm:
        return 0.0  # already cracked by axial tension alone
    return float((N_Ed / A - fctm) * (Iy / z_t))


def cracking_kappa_with_N(
    A: float, Iy: float, z_t: float, N_Ed: float, fctm: float, Ec: float
) -> Tuple[float, float]:
    Mcr = cracking_M_with_N(A, Iy, z_t, N_Ed, fctm)
    kcr = float(Mcr / (Ec * Iy)) if Iy > 0 else 0.0
    return kcr, Mcr


# ----------------------------
# Interpolation utilities
# ----------------------------


def M_at_kappa(res: Dict[str, Any], kappa_target: float) -> float:
    return float(np.interp(kappa_target, res["kappa_total"], res["My_total"]))


def kappa_at_M(res: Dict[str, Any], M_target: float) -> float:
    return float(np.interp(M_target, res["My_total"], res["kappa_total"]))


# ----------------------------
# M-kappa solver (State II, 1D bending about y)
# ----------------------------


class MomentCurvatureSolver:
    def __init__(
        self,
        conc: ConcreteMesh,
        steel: SteelBars,
        conc_law,
        steel_law: SteelElasticPerfectlyPlastic,
        eps_cu: float = 3.5e-3,
        eps_su: float = 25e-3,
    ):
        self.conc = conc
        self.steel = steel
        self.conc_law = conc_law
        self.steel_law = steel_law

        self.eps_cu = float(eps_cu)
        self.eps_su = float(eps_su)
        self.eps_y = float(self.steel_law.eps_y)

        self.z_top = float(np.max(conc.z))
        self.z_bot = float(np.min(conc.z))

    @staticmethod
    def strains(eps0: float, kappa: float, z: np.ndarray) -> np.ndarray:
        return eps0 - kappa * z

    def resultants(self, eps0: float, kappa: float) -> Tuple[float, float]:
        eps_c = self.strains(eps0, kappa, self.conc.z)
        sig_c = self.conc_law.sigma(eps_c)  # MPa

        if self.steel.z.size:
            eps_s = self.strains(eps0, kappa, self.steel.z)
            sig_s = self.steel_law.sigma(eps_s)  # MPa
        else:
            sig_s = np.array([], dtype=float)

        N = float(np.sum(sig_c * self.conc.A) + np.sum(sig_s * self.steel.As))  # MN
        My = float(
            -np.sum(sig_c * self.conc.A * self.conc.z)
            - np.sum(sig_s * self.steel.As * self.steel.z)
        )  # MNm
        return N, My

    def solve_eps0_for_N(
        self,
        kappa: float,
        N_Ed: float,
        eps0_min: float = -0.05,
        eps0_max: float = +0.05,
        n_scan: int = 300,
        tol_N: float = 1e-8,
        max_iter: int = 80,
    ) -> Optional[float]:
        eps0_grid = np.linspace(eps0_min, eps0_max, n_scan)
        g = np.empty_like(eps0_grid)

        for i, e0 in enumerate(eps0_grid):
            N, _ = self.resultants(float(e0), kappa)
            g[i] = N - N_Ed

        idx = np.where(np.sign(g[:-1]) * np.sign(g[1:]) <= 0)[0]
        if idx.size == 0:
            return None

        i0 = int(idx[0])
        a, b = float(eps0_grid[i0]), float(eps0_grid[i0 + 1])
        fa, fb = float(g[i0]), float(g[i0 + 1])

        for _ in range(max_iter):
            m = 0.5 * (a + b)
            Nm, _ = self.resultants(m, kappa)
            fm = float(Nm - N_Ed)

            if abs(fm) < tol_N:
                return m

            if np.sign(fa) * np.sign(fm) <= 0:
                b, fb = m, fm
            else:
                a, fa = m, fm

        return 0.5 * (a + b)

    def moment_curvature_stateII(
        self,
        N_Ed: float = 0.0,
        kappa_start: float = 0.0,
        kappa_max: float = 0.30,
        dkappa: float = 5e-4,
        tol_N: float = 1e-8,
    ) -> Dict[str, Any]:

        kappas, Mys, eps0s = [], [], []
        epsc_min_list, epss_max_list, epss_min_list = [], [], []

        Nc_list = []
        Ns_t_list = []
        Ns_c_list = []

        kappa_y_tens = None
        kappa_y_comp = None
        kappa_fail = None
        fail_mode = None

        z_s = self.steel.z
        if z_s.size:
            z_top_s = np.max(z_s)
            z_bot_s = np.min(z_s)
            comp_ids = np.where(np.isclose(z_s, z_top_s, rtol=0, atol=1e-12))[0]
            tens_ids = np.where(np.isclose(z_s, z_bot_s, rtol=0, atol=1e-12))[0]
        else:
            comp_ids = np.array([], dtype=int)
            tens_ids = np.array([], dtype=int)

        k = float(kappa_start)
        while k <= kappa_max + 1e-15:
            eps0 = self.solve_eps0_for_N(kappa=k, N_Ed=N_Ed, tol_N=tol_N)
            if eps0 is None:
                break

            N, My = self.resultants(eps0, k)

            eps_c = self.strains(eps0, k, self.conc.z)
            eps_s = self.strains(eps0, k, z_s) if z_s.size else np.array([0.0])

            eps_c_min = float(np.min(eps_c))
            eps_s_max = float(np.max(eps_s))
            eps_s_min = float(np.min(eps_s))

            # failure
            if eps_c_min <= -self.eps_cu:
                kappa_fail = k
                fail_mode = "concrete_crush (eps_c_min <= -eps_cu)"
                break

            if abs(eps_s_max) >= self.eps_su or abs(eps_s_min) >= self.eps_su:
                kappa_fail = k
                fail_mode = "steel_ultimate (|eps_s| >= eps_su)"
                break

            kappas.append(k)
            Mys.append(My)
            eps0s.append(eps0)
            epsc_min_list.append(eps_c_min)
            epss_max_list.append(eps_s_max)
            epss_min_list.append(eps_s_min)

            # yield events
            if kappa_y_comp is None and comp_ids.size:
                eps_comp = float(np.min(eps_s[comp_ids]))
                if eps_comp <= -self.eps_y:
                    kappa_y_comp = k

            if kappa_y_tens is None and tens_ids.size:
                eps_tens = float(np.max(eps_s[tens_ids]))
                if eps_tens >= self.eps_y:
                    kappa_y_tens = k

            # split forces
            forces = self.resultants_split(eps0, k)

            Nc_list.append(forces["Nc"])
            Ns_t_list.append(forces["Ns_t"])
            Ns_c_list.append(forces["Ns_c"])

            k += dkappa

        return {
            "kappa": np.array(kappas),
            "My": np.array(Mys),
            "eps0": np.array(eps0s),
            "eps_c_min": np.array(epsc_min_list),
            "eps_s_max": np.array(epss_max_list),
            "eps_s_min": np.array(epss_min_list),
            "kappa_y_tens": kappa_y_tens,
            "kappa_y_comp": kappa_y_comp,
            "kappa_fail": kappa_fail,
            "fail_mode": fail_mode,
            "eps_y": self.eps_y,
            "Nc": np.array(Nc_list),
            "Ns_t": np.array(Ns_t_list),
            "Ns_c": np.array(Ns_c_list),
        }

    @staticmethod
    def _first_yield(
        kappa_y_tens: Optional[float], kappa_y_comp: Optional[float]
    ) -> Optional[float]:
        vals = [v for v in [kappa_y_tens, kappa_y_comp] if v is not None]
        return min(vals) if vals else None

    def moment_curvature_piecewise(
        self,
        Ec: float,
        fctm: float,
        N_Ed: float = 0.0,
        kappa_max: float = 0.30,
        dkappa: float = 5e-4,
        tol_N: float = 1e-8,
        n_I: int = 30,
        start_eps: float = 1e-12,
    ) -> Dict[str, Any]:
        """
        Builds a piecewise curve + explicit segment arrays:

          Segment I   (State I):    analytic from 0..kappa_cr
          Segment II  (State IIa):  kappa_cr..kappa_y_first (steel elastic)
          Segment III (State IIb):  kappa_y_first..kappa_fail (steel plastic)

        NOTE: Segment I stiffness is Ec*Iy of concrete mesh (as requested).
        """

        # --- cracking point (State I) ---
        A, Iy, z_top, z_bot = section_properties_from_mesh(self.conc)
        z_t = z_bot  # sagging -> bottom in tension
        kappa_cr, M_cr = cracking_kappa_with_N(
            A=A, Iy=Iy, z_t=z_t, N_Ed=N_Ed, fctm=fctm, Ec=Ec
        )

        # --- Segment I: straight line ---
        if kappa_cr <= 0.0 or M_cr <= 0.0:
            kappa_I = np.array([0.0])
            M_I = np.array([0.0])
            kappa_start = 0.0
        else:
            kappa_I = np.linspace(0.0, kappa_cr, max(2, int(n_I)))
            M_I = Ec * Iy * kappa_I
            kappa_start = kappa_cr + max(start_eps, 0.2 * dkappa)

        # --- State II curve ---
        resII = self.moment_curvature_stateII(
            N_Ed=N_Ed,
            kappa_start=kappa_start,
            kappa_max=kappa_max,
            dkappa=dkappa,
            tol_N=tol_N,
        )

        # --- force continuity at cracking ---
        if resII["kappa"].size:
            M_at_cr_num = np.interp(kappa_cr, resII["kappa"], resII["My"])
            delta_M = M_cr - M_at_cr_num
            resII["My"] = resII["My"] #+ delta_M

        # --- determine first yield and split II / III ---
        ky_first = self._first_yield(
            resII.get("kappa_y_tens"), resII.get("kappa_y_comp")
        )

        kII = resII["kappa"].copy()
        MII = resII["My"].copy()

        if kII.size == 0:
            # no State II data (rare: solver couldn't bracket eps0)
            kappa_II = np.array([])
            M_II = np.array([])
            kappa_III = np.array([])
            M_III = np.array([])
        else:
            if ky_first is None:
                # never yielded before failure/max -> everything is Segment II
                kappa_II = kII
                M_II = MII
                kappa_III = np.array([])
                M_III = np.array([])
            else:
                # index where kappa >= ky_first (first plastic point belongs to Segment III)
                i_split = int(np.searchsorted(kII, ky_first, side="left"))
                kappa_II = kII[:i_split]
                M_II = MII[:i_split]
                kappa_III = kII[i_split:]
                M_III = MII[i_split:]

                # ensure that ky_first point exists on the curve (nice for plotting/continuity)
                # If ky_first is between grid points, insert interpolated point at boundary
                if kII[0] < ky_first < kII[-1]:
                    My_ky = float(np.interp(ky_first, kII, MII))
                    # add to end of II and start of III if not already exactly present
                    if (
                        not np.isclose(kappa_II[-1], ky_first, atol=0.0, rtol=0.0)
                        if kappa_II.size
                        else True
                    ):
                        kappa_II = np.concatenate([kappa_II, [ky_first]])
                        M_II = np.concatenate([M_II, [My_ky]])
                    if (
                        not np.isclose(kappa_III[0], ky_first, atol=0.0, rtol=0.0)
                        if kappa_III.size
                        else False
                    ):
                        kappa_III = np.concatenate([[ky_first], kappa_III])
                        M_III = np.concatenate([[My_ky], M_III])

        # --- merge full curve (for interpolation helpers) ---
        kappa_total = np.concatenate([kappa_I, kII]) if kII.size else kappa_I.copy()
        My_total = np.concatenate([M_I, MII]) if MII.size else M_I.copy()

        out = dict(resII)
        out.update(
            {
                "A": A,
                "Iy": Iy,
                "z_top": z_top,
                "z_bot": z_bot,
                "kappa_cr": kappa_cr,
                "M_cr": M_cr,
                # first yield (for segmentation)
                "kappa_y_first": ky_first,
                # explicit segments
                "kappa_I": kappa_I,
                "M_I": M_I,
                "kappa_II": kappa_II,
                "M_II": M_II,
                "kappa_III": kappa_III,
                "M_III": M_III,
                # full
                "kappa_total": kappa_total,
                "My_total": My_total,
            }
        )
        return out

    def plot_M_kappa_piecewise(
        self, res: Dict[str, Any], title: str = "M-κ (piecewise)"
    ) -> None:
        import matplotlib.pyplot as plt

        plt.figure()

        # plot explicit segments (default matplotlib colors)
        if res["kappa_I"].size:
            plt.plot(res["kappa_I"], res["M_I"], lw=2, label="Segment I (uncracked)")

        if res["kappa_II"].size:
            plt.plot(
                res["kappa_II"],
                res["M_II"],
                lw=2,
                label="Segment II (cracked, steel elastic)",
            )

        if res["kappa_III"].size:
            plt.plot(
                res["kappa_III"],
                res["M_III"],
                lw=2,
                label="Segment III (cracked, steel plastic)",
            )

        # markers
        if res.get("kappa_cr") is not None and res.get("M_cr") is not None:
            plt.scatter(
                [res["kappa_cr"]], [res["M_cr"]], marker="s", zorder=5, label="cracking"
            )

        if res.get("kappa_y_first") is not None:
            ky = res["kappa_y_first"]
            Myy = float(np.interp(ky, res["kappa_total"], res["My_total"]))
            plt.scatter([ky], [Myy], marker="o", zorder=6, label="first yield")
            plt.text(ky, Myy, "  first yield", va="bottom")

        if res.get("kappa_fail") is not None:
            kf = res["kappa_fail"]
            Myf = float(np.interp(kf, res["kappa_total"], res["My_total"]))
            plt.scatter([kf], [Myf], marker="x", zorder=6, label="failure")
            plt.text(kf, Myf, f"  fail: {res.get('fail_mode')}", va="bottom")

        plt.xlabel(r"$\kappa$ [1/m]")
        plt.ylabel(r"$M_y$ [MN·m]")
        plt.title(title)
        plt.grid(True)
        plt.legend()
        plt.show()

    def resultants_split(self, eps0: float, kappa: float) -> Dict[str, float]:
        """
        Returns separated axial forces:
        Nc  : concrete compression force (<=0)
        Ns_t: steel tension force (>=0)
        Ns_c: steel compression force (<=0)
        All forces in MN.
        """

        # --- concrete ---
        eps_c = self.strains(eps0, kappa, self.conc.z)
        sig_c = self.conc_law.sigma(eps_c)

        Nc = float(np.sum(sig_c * self.conc.A))  # already only compression

        # --- steel ---
        if self.steel.z.size:
            eps_s = self.strains(eps0, kappa, self.steel.z)
            sig_s = self.steel_law.sigma(eps_s)

            Ns_t = float(np.sum(sig_s[eps_s > 0.0] * self.steel.As[eps_s > 0.0]))
            Ns_c = float(np.sum(sig_s[eps_s < 0.0] * self.steel.As[eps_s < 0.0]))
        else:
            Ns_t = 0.0
            Ns_c = 0.0

        return {"Nc": Nc, "Ns_t": Ns_t, "Ns_c": Ns_c, "N_total": Nc + Ns_t + Ns_c}

    def plot_section_with_resultants(
        self,
        eps0: float,
        kappa: float,
        scale_force: float = 0.15,
        title: str = "Section stresses & resultants",
    ):
        import matplotlib.pyplot as plt
        import numpy as np
        from scipy.spatial import ConvexHull


        # --- strains & stresses ---
        eps_c = self.strains(eps0, kappa, self.conc.z)
        sig_c = self.conc_law.sigma(eps_c)

        eps_s = self.strains(eps0, kappa, self.steel.z)
        sig_s = self.steel_law.sigma(eps_s)

        # --- concrete resultant ---
        mask_c = sig_c < 0
        Nc = np.sum(sig_c[mask_c] * self.conc.A[mask_c])
        zc = np.sum(sig_c[mask_c] * self.conc.A[mask_c] * self.conc.z[mask_c]) / Nc

        # --- steel resultants ---
        mask_t = eps_s > 0
        mask_c_s = eps_s < 0

        Ns_t = np.sum(sig_s[mask_t] * self.steel.As[mask_t])
        Ns_c = np.sum(sig_s[mask_c_s] * self.steel.As[mask_c_s])

        zs_t = (
            np.sum(sig_s[mask_t] * self.steel.As[mask_t] * self.steel.z[mask_t]) / Ns_t
            if abs(Ns_t) > 0
            else 0.0
        )
        zs_c = (
            np.sum(sig_s[mask_c_s] * self.steel.As[mask_c_s] * self.steel.z[mask_c_s]) / Ns_c
            if abs(Ns_c) > 0
            else 0.0
        )




        # --- plotting ---
        fig, ax = plt.subplots(figsize=(6, 6))

        # --- outer section contour (convex hull) ---
        pts = np.column_stack([self.conc.y, self.conc.z])
        hull = ConvexHull(pts)

        hull_pts = pts[hull.vertices]
        hull_pts = np.vstack([hull_pts, hull_pts[0]])  # schließen

        ax.plot(
            hull_pts[:, 0],
            hull_pts[:, 1],
            color="black",
            lw=2.0,
            label="Section contour",
        )

        # concrete (compression only)
        sc = ax.scatter(
            self.conc.y[mask_c],
            self.conc.z[mask_c],
            c=-sig_c[mask_c],
            cmap="Reds",
            s=8,
        )
        plt.colorbar(sc, ax=ax, label=r"$|\sigma_c|$ [MPa]")

        # reinforcement
        ax.scatter(
            self.steel.y,
            self.steel.z,
            s=self.steel.As / self.steel.As.max() * 600,
            c='black',
            edgecolors="black",
            zorder=5,
        )

        # --- horizontal resultants ---
        ax.arrow(
            0,
            zc,
            -Nc * scale_force,
            0,
            width=0.003,
            color="blue",
            length_includes_head=True,
            label=r"$N_c$",
        )

        ax.arrow(
            0,
            zs_t,
            Ns_t * scale_force,
            0,
            width=0.003,
            color="red",
            length_includes_head=True,
            label=r"$N_{s,t}$",
        )

        ax.arrow(
            0,
            zs_c,
            -Ns_c * scale_force,
            0,
            width=0.003,
            color="green",
            length_includes_head=True,
            label=r"$N_{s,c}$",
        )

        # neutral axis
        if abs(kappa) > 1e-12:
            y = np.array([self.conc.y.min(), self.conc.y.max()])
            z = eps0 / kappa * np.ones_like(y)
            ax.plot(y, z, "k--", lw=2, label="Neutral axis")

        ax.set_aspect("equal")
        ax.set_xlabel("y [m]")
        ax.set_ylabel("z [m]")
        ax.set_title(title)
        ax.grid(True)
        ax.legend()

        plt.show()



import matplotlib.pyplot as plt

if __name__ == "__main__":

    # ----------------------------
    # Kreisquerschnitt
    # ----------------------------
    R = 0.20      # Radius [m] → Ø 40 cm
    conc = mesh_circle(R=R, nr=50, ntheta=120)

    # ----------------------------
    # Bewehrung
    # ----------------------------
    n_bars = 10
    phi = 14e-3
    As_bar = np.pi * (phi/2)**2
    r_s = R - 0.04   

    steel = circle_rebar(
        n_bars=n_bars,
        r_s=r_s,
        As_bar=As_bar
    )

    # ----------------------------
    # Materialien
    # ----------------------------
    Ec = 34077.0   # MPa
    Es = 200000.0  # MPa
    fyd = 435.0    # MPa

    fck = 30.0
    fctm = 0.30 * fck**(2/3)

    conc_law = ConcreteEC2ParabolaRectangle(
        fcd=0.85 * fck / 1.5,
        eps_c2=2.0e-3,
        eps_cu=3.5e-3
    )

    steel_law = SteelElasticPerfectlyPlastic(
        Es_MPa=Es,
        fyd_MPa=fyd
    )

    # ----------------------------
    # Solver
    # ----------------------------
    solver = MomentCurvatureSolver(
        conc=conc,
        steel=steel,
        conc_law=conc_law,
        steel_law=steel_law
    )

    # ----------------------------
    # Berechnung
    # ----------------------------
    N_Ed = -0.60  # MN

    res = solver.moment_curvature_piecewise(
        Ec=Ec,
        fctm=fctm,
        N_Ed=N_Ed,
        kappa_max=0.15,
        dkappa=5e-4
    )

    solver.plot_M_kappa_piecewise(
        res,
        title="Moment–Krümmung Kreisquerschnitt"
    )

    print("A      =", res["A"])
    print("Iy     =", res["Iy"])
    print("k_cr   =", res["kappa_cr"])
    print("M_cr   =", res["M_cr"])
    print("k_y    =", res["kappa_y_first"])
    print("M_fail = ", np.max(res["My_total"]))
    print("k_fail =", res["kappa_fail"])
    print(sum(solver.steel.As)*100**2)


    plt.plot(res["kappa"], res["Nc"], label="Nc (Beton)")
    plt.plot(res["kappa"], res["Ns_c"], label="Ns,c (Stahl Druck)")
    plt.plot(res["kappa"], res["Ns_t"], label="Ns,t (Stahl Zug)")
    plt.legend(); plt.grid(); plt.show()


    i = -1  # letzter Punkt (nahe Versagen)
    eps0 = res["eps0"][i]
    kappa = res["kappa"][i]

    solver.plot_section_with_resultants(
        eps0=eps0,
        kappa=kappa,
        scale_force=0.3,
        title="Resultierende Kräfte im Querschnitt"
    )


print(res["Nc"][-1])
print(res["Ns_c"][-1])
print(res["Ns_t"][-1])
