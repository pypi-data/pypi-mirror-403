# ============================================================
# Plotting.py (Final: Mit Schriftgrößen-Slider)
# ============================================================
from __future__ import annotations

import numpy as np
import matplotlib

# QtAgg für interaktive Fenster bevorzugen
try:
    matplotlib.use("QtAgg") 
except:
    pass 

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from matplotlib.widgets import Slider

class StructurePlotter:
    """
    Interaktiver 3D-Plotter für STABRAUM.
    Features: 
    - Schnittgrößen (Fläche + Kamm)
    - Interaktive Zahlenwerte (Anzahl & Schriftgröße)
    - Federn & Lasten
    - Korrekte Zugseiten-Darstellung
    """

    def __init__(self, res):
        self.res = res
        
        # --- 1. DATEN-ZUGRIFF ---
        if hasattr(res, "Inp"):
            self.inp = res.Inp
            self.nodes = res.Inp.nodes
            self.members = res.Inp.members
        elif hasattr(res, "nodes"):
            self.inp = None
            self.nodes = res.nodes
            self.members = getattr(res, "members", None)
        else:
            raise AttributeError("Plotter Error: Konnte 'nodes' nicht finden.")

        # --- 2. TRANSFORMATIONSMATRIZEN ---
        if hasattr(res, "TransMats"):
            self.T = res.TransMats
        elif hasattr(res, "element_T_matrices"):
            self.T = res.element_T_matrices
        else:
            self.T = []
        
        # Cache Koordinaten
        self.xyz = np.array([
            self.nodes["x[m]"], 
            self.nodes["y[m]"], 
            self.nodes["z[m]"]
        ]).T
        
        # Cache Connectivity (0-basiert)
        self.na = np.array(self.members["na"], dtype=int) - 1
        self.ne = np.array(self.members["ne"], dtype=int) - 1

    def _get_result_data(self, kind):
            """Map Strings auf Ergebnis-Arrays."""
            kind = kind.upper()
            mapping = {
                "MY": "MY_el_i_store",
                "MZ": "MZ_el_i_store",
                "MX": "MX_el_i_store",
                "MT": "MX_el_i_store",
                "N":  "N_el_i_store",
                "VY": "VY_el_i_store",
                "VZ": "VZ_el_i_store",
                "MW": "MW_el_i_store", # Wölbimoment
                "B":  "MW_el_i_store",
                
                # --- NEU HINZUFÜGEN ---
                "MTP": "MTP_el_i_store", # Primäre Torsion (St. Venant)
                "MTS": "MTS_el_i_store"  # Sekundäre Torsion (Wölbkrafttorsion)
                # ----------------------
            }
            
            attr_name = mapping.get(kind, None)
            if attr_name and hasattr(self.res, attr_name):
                return getattr(self.res, attr_name)
            else:
                print(f"Warnung: Ergebnis '{kind}' nicht gefunden (oder in 'res' noch nicht berechnet).")
                return np.zeros((len(self.na), 2, 1))


    def _get_local_axes(self, i_elem):
        """Extrahiert lokale Achsen (ex, ey, ez) aus der Matrix."""
        if len(self.T) <= i_elem:
            return np.array([1,0,0]), np.array([0,1,0]), np.array([0,0,1])

        Ti = self.T[i_elem]
        # Mapping: ux=0, uy=1, uz=3 (Spalte 3 ist ez)
        idx_global = [0, 1, 3] 
        
        ex = Ti[idx_global, 0]
        ey = Ti[idx_global, 1]
        ez = Ti[idx_global, 3] 
        
        def norm(v): 
            n = np.linalg.norm(v)
            return v if n < 1e-12 else v/n
            
        return norm(ex), norm(ey), norm(ez)

    def plot_diagram_interactive(self, kind="MY", scale_init=1.0, font_init=9, show_loads=True, flip_sign=False):
        """
        Hauptfunktion zum Plotten.
        Zeigt drei Slider: 'Skalierung', 'Werte' (Anzahl) und 'Schrift' (Größe).
        """
        kind = str(kind).upper()
        Q = self._get_result_data(kind)
        
        # Geometrie-Grenzen
        mins = self.xyz.min(axis=0)
        maxs = self.xyz.max(axis=0)
        span = max(maxs - mins) if len(mins) > 0 else 1.0
        margin = span * 0.1
        
        # Referenzwert
        vals = np.abs(Q[:, :, 0]).ravel()
        q_max = float(np.max(vals)) if vals.size > 0 else 1.0
        if q_max < 1e-12: q_max = 1.0

        fig = plt.figure(figsize=(12, 10)) # Etwas höher für mehr Slider
        ax = fig.add_subplot(projection="3d")
        
        # Platz für Slider unten schaffen
        plt.subplots_adjust(bottom=0.25) 

        # --- Statik (Struktur) ---
        lines_struct = []
        for i in range(len(self.na)):
            lines_struct.append([self.xyz[self.na[i]], self.xyz[self.ne[i]]])
            
        lc = Line3DCollection(lines_struct, colors='black', linewidths=0.8, alpha=0.5)
        ax.add_collection3d(lc)

        self._draw_springs(ax, span * 0.04)

        # --- Slider Setup ---
        # Positionen [left, bottom, width, height]
        ax_sl_scale  = plt.axes([0.25, 0.05, 0.5, 0.03])
        ax_sl_labels = plt.axes([0.25, 0.10, 0.5, 0.03])
        ax_sl_font   = plt.axes([0.25, 0.15, 0.5, 0.03])
        
        sl_scale  = Slider(ax_sl_scale, 'Skalierung', 0.0, 5.0, valinit=scale_init)
        sl_labels = Slider(ax_sl_labels, 'Werte', 0, 5, valinit=0, valstep=1) # 0=Aus, 1=Mitte...
        sl_font   = Slider(ax_sl_font, 'Schrift', 6, 20, valinit=font_init, valstep=1)

        # --- Dynamik ---
        actors = [] 

        def draw(val):
            # Alte Objekte entfernen
            for artist in actors:
                try: artist.remove()
                except: pass
            actors.clear()

            # Werte lesen
            current_scale = sl_scale.val
            n_labels = int(sl_labels.val)
            font_size = sl_font.val
            
            alpha = (current_scale * 0.15 * span) / q_max
            load_scale = current_scale * 0.15 * span
            
            # Globaler Flip (falls per Argument gesetzt)
            sign_factor = -1.0 if flip_sign else 1.0

            for i in range(len(self.na)):
                Pa = self.xyz[self.na[i]]
                Pe = self.xyz[self.ne[i]]
                
                ex, ey, ez = self._get_local_axes(i)
                
                # --- VORZEICHEN-LOGIK ---
                if kind == "MY":   w = ez 
                elif kind == "MZ": w = -ey   
                elif kind == "N":  w = ez   
                elif kind == "MW": w = ez  # NEU: Wölbimoment in lokale z-Richtung zeichnen
                elif kind == "B":  w = ez  # Alias für Bimoment
                else: w = ez
                
                w = w * sign_factor

                Mi = float(Q[i, 0, 0])
                Mj = float(Q[i, 1, 0])

                # 1. Diagramm
                for (P0, P1, m0, m1) in self._split(Pa, Pe, Mi, Mj):
                    p1, p2 = P0, P1 
                    p3 = P1 + w * (m1 * alpha) 
                    p4 = P0 + w * (m0 * alpha) 
                    
                    col = "blue" if (m0 + m1) >= 0 else "red"
                    
                    # Fläche
                    poly = Poly3DCollection([[p1, p2, p3, p4]], facecolor=col, alpha=0.3, edgecolor=None)
                    ax.add_collection3d(poly)
                    actors.append(poly)
                    
                    # Kontur
                    l, = ax.plot([p4[0], p3[0]], [p4[1], p3[1]], [p4[2], p3[2]], color=col, lw=1.5)
                    actors.append(l)

                    # Kamm-Stiche
                    dist = np.linalg.norm(P1 - P0)
                    if dist > 1e-9:
                        n_ticks = max(2, int(dist / span * 40)) 
                        for s in np.linspace(0, 1, n_ticks):
                            pt_base = P0 + s * (P1 - P0)
                            m_val = m0 + s * (m1 - m0)
                            pt_top = pt_base + w * (m_val * alpha)
                            lt, = ax.plot([pt_base[0], pt_top[0]], [pt_base[1], pt_top[1]], [pt_base[2], pt_top[2]], 
                                          color=col, lw=0.5, alpha=0.5)
                            actors.append(lt)

                # 2. Labels (Zahlenwerte)
                if n_labels > 0 and abs(Mi) + abs(Mj) > 1e-3:
                    if n_labels == 1:
                        steps = [0.5]
                    elif n_labels == 2:
                        steps = [0.0, 1.0]
                    elif n_labels == 3:
                        steps = [0.0, 0.5, 1.0]
                    else:
                        steps = np.linspace(0, 1, n_labels)
                    
                    for s in steps:
                        val_s = Mi + s * (Mj - Mi)
                        pos_base = Pa + s * (Pe - Pa)
                        pos_label = pos_base + w * (val_s * alpha * 1.1)
                        
                        if abs(val_s) > 1e-3:
                            # HIER WIRD DIE SCHRIFTGRÖSSE GESETZT
                            t = ax.text(pos_label[0], pos_label[1], pos_label[2], 
                                        f"{val_s:.2f}", fontsize=font_size, color='black', 
                                        ha='center', va='center', fontweight='bold')
                            actors.append(t)

            if show_loads:
                self._draw_loads(ax, actors, load_scale)

        # Slider Events
        sl_scale.on_changed(draw)
        sl_labels.on_changed(draw)
        sl_font.on_changed(draw)
        
        # Init
        draw(0) 
        
        ax.set_xlim(mins[0]-margin, maxs[0]+margin)
        ax.set_ylim(mins[1]-margin, maxs[1]+margin)
        ax.set_zlim(mins[2]-margin, maxs[2]+margin)
        try: ax.set_box_aspect((1, 1, 1))
        except: pass
        ax.set_axis_off()
        ax.set_title(f"Schnittgröße: {kind}")
        
        plt.show()
        # Slider zurückgeben, damit sie aktiv bleiben
        return sl_scale, sl_labels, sl_font

    def _split(self, P0, P1, m0, m1):
        if m0 * m1 >= 0 or abs(m0-m1) < 1e-12:
            return [(P0, P1, m0, m1)]
        s = -m0 / (m1 - m0)
        Pm = P0 + s * (P1 - P0)
        return [(P0, Pm, m0, 0.0), (Pm, P1, 0.0, m1)]

    def _draw_springs(self, ax, size):
        df = self.nodes
        def pick(*names):
            low = {c.lower(): c for c in df.columns}
            for n in names:
                if n.lower() in low: return low[n.lower()]
            return None

        col_kz = pick("kz", "kZ", "cz", "cZ", "Cp[MN/m]/[MNm/m]") 
        col_ky = pick("ky", "kY", "cy", "cY")
        col_kx = pick("kx", "kX", "cx", "cX")
        
        t = np.linspace(0, 1, 8)
        zigzag = np.zeros((8, 3))
        zigzag[:, 0] = np.sin(t * 4 * np.pi) * (size * 0.3)
        
        restraints = getattr(self.inp, "RestraintData", None)
        if restraints is not None:
            for _, row in restraints.iterrows():
                idx = int(row["Node"]) - 1
                dof = int(row["Dof"])
                cp = float(row["Cp[MN/m]/[MNm/m]"])
                pt = self.xyz[idx]
                
                if cp > 0:
                    pts = zigzag.copy()
                    if dof == 2 or dof == 3: # Z
                        pts[:, 2] = -t * size
                        pts = pts + pt
                        ax.plot(pts[:,0], pts[:,1], pts[:,2], color='orange', lw=1.5)
                    elif dof == 1: # Y
                        pts[:, 2] = pts[:, 0]
                        pts[:, 0] = 0
                        pts[:, 1] = -t * size
                        pts = pts + pt
                        ax.plot(pts[:,0], pts[:,1], pts[:,2], color='orange', lw=1.5)
                    elif dof == 0: # X
                        pts[:, 2] = pts[:, 0]
                        pts[:, 1] = 0
                        pts[:, 0] = -t * size
                        pts = pts + pt
                        ax.plot(pts[:,0], pts[:,1], pts[:,2], color='orange', lw=1.5)

    def _draw_loads(self, ax, actor_list, scale):
        if not self.inp or not hasattr(self.inp, "NodalForces"): return
        loads = self.inp.NodalForces
        base_len = max(scale, 1e-3)
        
        for _, row in loads.iterrows():
            node_idx = int(row["Node"]) - 1
            dof_str = str(row["Dof"]).strip().lower()
            val = float(row["Value[MN/MNm]"])
            if abs(val) < 1e-9: continue
            
            pt = self.xyz[node_idx]
            direction = np.zeros(3)
            is_moment = False
            
            if "fx" in dof_str: direction[0] = 1
            elif "fy" in dof_str: direction[1] = 1
            elif "fz" in dof_str: direction[2] = 1
            elif "mx" in dof_str: direction[0] = 1; is_moment = True
            elif "my" in dof_str: direction[1] = 1; is_moment = True
            elif "mz" in dof_str: direction[2] = 1; is_moment = True
            
            direction *= np.sign(val)
            
            if is_moment:
                p_start = pt
                p_end = pt + direction * base_len
                self._draw_arrow(ax, actor_list, p_start, p_end, color="magenta", style="double")
            else:
                p_end = pt
                p_start = pt - direction * base_len
                self._draw_arrow(ax, actor_list, p_start, p_end, color="green", style="simple")

    def _draw_arrow(self, ax, lst, p0, p1, color, style="simple"):
        vec = p1 - p0
        L = np.linalg.norm(vec)
        if L < 1e-9: return
        l, = ax.plot([p0[0], p1[0]], [p0[1], p1[1]], [p0[2], p1[2]], color=color, lw=2)
        lst.append(l)
        v = vec / L
        tmp = np.array([1,0,0]) if abs(v[0]) < 0.9 else np.array([0,1,0])
        n1 = np.cross(v, tmp); n1 /= np.linalg.norm(n1)
        n2 = np.cross(v, n1)
        head_L = L * 0.25; head_W = L * 0.1
        
        def draw_head(tip_pos):
            base = tip_pos - v * head_L
            corners = [base + n1*head_W, base - n1*head_W, base + n2*head_W, base - n2*head_W]
            for c in corners:
                ln, = ax.plot([tip_pos[0], c[0]], [tip_pos[1], c[1]], [tip_pos[2], c[2]], color=color, lw=1.5)
                lst.append(ln)

        if style == "simple": draw_head(p1)
        elif style == "double":
            draw_head(p1)
            draw_head(p1 - v * (head_L * 0.8))