import math
import random
import time
import threading
import io
import urllib.request
import tkinter as tk
from tkinter import scrolledtext
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# ═══════════════════════════════════════════════════════
#  DONNÉES — coordonnées GPS (lat, lon)
#  Pour ajouter une ville : ajoutez simplement une entrée ici.
#  Les distances sont calculées automatiquement par Haversine.
# ═══════════════════════════════════════════════════════
COORDS = {
    "Paris":            (48.8566,  2.3522),
    "Marseille":        (43.2965,  5.3698),
    "Lyon":             (45.7640,  4.8357),
    "Toulouse":         (43.6047,  1.4442),
    "Nice":             (43.7102,  7.2620),
    "Nantes":           (47.2184, -1.5536),
    "Strasbourg":       (48.5734,  7.7521),
    "Montpellier":      (43.6119,  3.8772),
    "Bordeaux":         (44.8378, -0.5792),
    "Lille":            (50.6292,  3.0573),
    "Rennes":           (48.1173, -1.6778),
    "Reims":            (49.2583,  4.0317),
    "Le Havre":         (49.4938,  0.1077),
    "Dijon":            (47.3220,  5.0415),
    "Grenoble":         (45.1885,  5.7245),
    "Clermont-Ferrand": (45.7772,  3.0870),
    "Limoges":          (45.8336,  1.2611),
    "Toulon":           (43.1242,  5.9280),
    "Saint-Etienne":    (45.4397,  4.3872),
    "Perpignan":        (42.6887,  2.8948),
    "Bayonne":          (43.4929, -1.4748),
    # ── Pour ajouter une ville, décommentez ou copiez ce format : ──
    # "Brest":          (48.3904, -4.4861),
    # "Rouen":          (49.4432,  1.0993),
    # "Caen":           (49.1829, -0.3707),
    # "Metz":           (49.1193,  6.1727),
    # "Tours":          (47.3941,  0.6848),
    # "Orléans":        (47.9029,  1.9039),
    # "Angers":         (47.4784, -0.5632),
    # "Poitiers":       (46.5802,  0.3404),
    # "Nancy":          (48.6921,  6.1844),
    # "Amiens":         (49.8941,  2.2958),
}

# Emprise géographique de la carte affichée (lon_min, lon_max, lat_min, lat_max)
# Ajustez si vous ajoutez des villes hors de cette zone ou changez l'image de fond.
MAP_BOUNDS = (-5.2, 9.7, 41.3, 51.2)

villes_disponibles = sorted(COORDS.keys())

ANT_COLORS = [
    "#f38ba8", "#fab387", "#f9e2af", "#a6e3a1",
    "#89dceb", "#89b4fa", "#cba6f7", "#eba0ac",
    "#94e2d5", "#b4befe",
]


# ═══════════════════════════════════════════════════════
#  GÉOGRAPHIE
# ═══════════════════════════════════════════════════════
def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance en km entre deux points GPS."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a  = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def get_distance(v1: str, v2: str) -> float:
    """Distance haversine entre deux villes du catalogue COORDS."""
    for v in (v1, v2):
        if v not in COORDS:
            raise ValueError(f"Ville inconnue : '{v}' — ajoutez-la dans COORDS.")
    lat1, lon1 = COORDS[v1]
    lat2, lon2 = COORDS[v2]
    return haversine(lat1, lon1, lat2, lon2)


def build_pos(villes: list) -> dict:
    """
    Convertit les coordonnées GPS en positions [0,1]×[0,1] pour matplotlib,
    alignées sur l'emprise MAP_BOUNDS.
    """
    lon_min, lon_max, lat_min, lat_max = MAP_BOUNDS
    pos = {}
    for v in villes:
        lat, lon = COORDS[v]
        x = (lon - lon_min) / (lon_max - lon_min)
        y = (lat - lat_min) / (lat_max - lat_min)
        pos[v] = (x, y)
    return pos


def charger_carte_france():
    """
    Charge la carte de fond.
    Cherche france_map.png dans plusieurs emplacements, puis tente OSM.
    Format recommandé : PNG, emprise lon -5.2→9.7 / lat 41.3→51.2, ~900×600 px.
    """
    import os

    # Cherche france_map.png dans plusieurs endroits possibles
    candidats = []
    try:
        candidats.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "france_map.png"))
    except Exception:
        pass
    candidats.append(os.path.join(os.getcwd(), "france_map.png"))
    candidats.append("france_map.png")

    for chemin in candidats:
        if os.path.exists(chemin):
            try:
                img = mpimg.imread(chemin)
                return img
            except Exception:
                pass

    # Fallback : téléchargement OSM
    try:
        url = (
            "https://render.openstreetmap.org/cgi-bin/export"
            "?bbox=-5.2,41.3,9.7,51.2&scale=3000000&format=png"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "AntSystemApp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return mpimg.imread(io.BytesIO(r.read()))
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════
#  LOGIQUE ANT SYSTEM  (inchangée)
# ═══════════════════════════════════════════════════════
class Fourmi:
    def __init__(self, position: str):
        self.position = position
        self.visite   = [position]
        self.distance = 0

    def deplacement(self, new_pos: str, distance: float):
        self.position = new_pos
        self.visite.append(new_pos)
        self.distance += distance


def pheromone_initiale(distance: float, C: float = 100) -> float:
    return C / distance


def creer_graphe_manuel(villes):
    G = nx.Graph()
    for v in villes:
        G.add_node(v)
    for i in range(len(villes)):
        for j in range(i + 1, len(villes)):
            d = get_distance(villes[i], villes[j])
            G.add_edge(villes[i], villes[j], distance=d, pheromone=pheromone_initiale(d))
    return G


def creer_graphe_rand(nb):
    villes = random.sample(villes_disponibles, nb)
    G = nx.Graph()
    for v in villes:
        G.add_node(v)
    for i in range(nb):
        for j in range(i + 1, nb):
            d = get_distance(villes[i], villes[j])
            G.add_edge(villes[i], villes[j], distance=d, pheromone=pheromone_initiale(d))
    return G, villes


def calculer_probabilites(G, fourmi, alpha=1, beta=2):
    voisins, poids = [], []
    for v in G.neighbors(fourmi.position):
        if v not in fourmi.visite:
            ph  = G[fourmi.position][v]["pheromone"]
            vis = 1 / G[fourmi.position][v]["distance"]
            voisins.append(v)
            poids.append((ph ** alpha) * (vis ** beta))
    return voisins, poids


def deplacement_fourmi(G, fourmi, alpha=1, beta=2):
    voisins, poids = calculer_probabilites(G, fourmi, alpha, beta)
    if not voisins:
        return False
    dest = random.choices(voisins, weights=poids, k=1)[0]
    fourmi.deplacement(dest, G[fourmi.position][dest]["distance"])
    return True


def mise_a_jour_pheromones(G, fourmis, rho=0.5, Q=100):
    for u, v in G.edges():
        G[u][v]["pheromone"] *= (1 - rho)
    for f in fourmis:
        if f.distance > 0:
            contrib = Q / f.distance
            for k in range(len(f.visite) - 1):
                G[f.visite[k]][f.visite[k + 1]]["pheromone"] += contrib


# ═══════════════════════════════════════════════════════
#  APPLICATION TKINTER
# ═══════════════════════════════════════════════════════
class AntSystemApp:

    BG     = "#1e1e2e"
    BG2    = "#181825"
    BG3    = "#13131f"
    FG     = "#cdd6f4"
    ACCENT = "#cba6f7"
    MUTED  = "#a6adc8"
    ENTRY  = "#313244"
    GREEN  = "#a6e3a1"
    RED    = "#f38ba8"

    def __init__(self, root):
        self.root = root
        self.root.title("Ant System – Simulation")
        self.root.configure(bg=self.BG)
        self.root.geometry("1350x820")
        self.root.resizable(True, True)

        self.mode   = tk.StringVar(value="aleatoire")
        self.animer = tk.BooleanVar(value=False)

        self.simulation_running = False
        self._stop_event        = threading.Event()

        self.G   = None
        self.pos = None

        self._ants_state = {}
        self._ants_lock  = threading.Lock()

        self._bar_pct_val = 0.0

        # Chargement de la carte en arrière-plan (ne bloque pas l'UI)
        self._carte_france = None
        threading.Thread(target=self._preload_map, daemon=True).start()

        self._build_ui()

    def _preload_map(self):
        self._carte_france = charger_carte_france()
        if self._carte_france is not None:
            self._log("🗺 Carte de France chargée.")
        else:
            self._log("⚠ Carte non trouvée — placez france_map.png dans le même dossier que le script.")

    # ════════════════════════════════════════
    #  CONSTRUCTION UI
    # ════════════════════════════════════════
    def _build_ui(self):
        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main, bg=self.BG, width=400)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        self._build_left(left)

        right = tk.Frame(main, bg=self.BG3)
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    # ── Panneau gauche ───────────────────────
    def _build_left(self, p):
        def sep(label):
            f = tk.Frame(p, bg=self.BG)
            f.pack(fill="x", pady=(12, 2))
            tk.Label(f, text=label, bg=self.BG, fg=self.ACCENT,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Frame(p, bg=self.ACCENT, height=1).pack(fill="x", pady=(0, 6))

        def entry_row(parent, label, default):
            f = tk.Frame(parent, bg=self.BG)
            f.pack(fill="x", pady=2)
            tk.Label(f, text=label, bg=self.BG, fg=self.FG,
                     font=("Segoe UI", 9), width=26, anchor="w").pack(side="left")
            e = tk.Entry(f, bg=self.ENTRY, fg=self.FG, insertbackground=self.FG,
                         font=("Segoe UI", 9), relief="flat", bd=4)
            e.insert(0, default)
            e.pack(side="left", fill="x", expand=True)
            return e

        # Titre
        tk.Label(p, text="🐜  Ant System", bg=self.BG, fg=self.ACCENT,
                 font=("Segoe UI", 14, "bold")).pack(pady=(4, 10))

        # ── Mode graphe ──
        sep("Mode de création du graphe")
        mf = tk.Frame(p, bg=self.BG)
        mf.pack(fill="x", pady=4)
        for val, txt in [("aleatoire", "Aléatoire"), ("manuel", "Manuel")]:
            tk.Radiobutton(mf, text=txt, variable=self.mode, value=val,
                           bg=self.BG, fg=self.FG, selectcolor=self.ENTRY,
                           activebackground=self.BG, activeforeground=self.ACCENT,
                           font=("Segoe UI", 9),
                           command=self._on_mode_change).pack(side="left", padx=8)

        self.nb_villes_entry = entry_row(p, "Nombre de villes :", "6")

        # ── Bloc mode aléatoire : bouton ajout ville ──
        self.aleatoire_frame = tk.Frame(p, bg=self.BG)
        self.aleatoire_frame.pack(fill="x")
        tk.Button(
            self.aleatoire_frame, text="＋  Ajouter une ville au catalogue",
            bg=self.ENTRY, fg=self.FG, font=("Segoe UI", 8), relief="flat",
            bd=0, pady=4, cursor="hand2", command=self._ouvrir_ajout_ville,
        ).pack(fill="x", pady=(4, 0))

        # ── Bloc mode manuel : Listbox multi-sélection ──
        self.manuel_frame = tk.Frame(p, bg=self.BG)
        self.manuel_frame.pack(fill="x")

        # En-tête avec compteur
        hdr = tk.Frame(self.manuel_frame, bg=self.BG)
        hdr.pack(fill="x", pady=(4, 2))
        tk.Label(hdr, text="Cliquez pour sélectionner les villes :",
                 bg=self.BG, fg=self.FG, font=("Segoe UI", 8)).pack(side="left")
        self._selection_label = tk.Label(hdr, text="(0 sélectionnées)",
                                         bg=self.BG, fg=self.MUTED,
                                         font=("Segoe UI", 7, "italic"))
        self._selection_label.pack(side="right")

        # Listbox + scrollbar
        lb_frame = tk.Frame(self.manuel_frame, bg=self.BG2)
        lb_frame.pack(fill="x", pady=2)
        sb_lb = tk.Scrollbar(lb_frame, orient="vertical")
        self._listbox = tk.Listbox(
            lb_frame, selectmode="multiple", height=8,
            bg=self.BG2, fg=self.FG, selectbackground=self.ACCENT,
            selectforeground=self.BG, font=("Segoe UI", 9),
            relief="flat", bd=0, highlightthickness=0,
            activestyle="none", yscrollcommand=sb_lb.set,
        )
        sb_lb.config(command=self._listbox.yview)
        sb_lb.pack(side="right", fill="y")
        self._listbox.pack(side="left", fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", lambda _e: self._maj_compteur())
        # Molette souris
        self._listbox.bind("<MouseWheel>",
            lambda e: self._listbox.yview_scroll(-1 * (e.delta // 120), "units"))
        self._rebuild_listbox()

        # Boutons Tout / Rien + Nouvelle ville
        btn_row = tk.Frame(self.manuel_frame, bg=self.BG)
        btn_row.pack(fill="x", pady=(3, 0))
        tk.Button(btn_row, text="✔ Tout", bg=self.ENTRY, fg=self.FG,
                  font=("Segoe UI", 7), relief="flat", bd=0, padx=6, pady=3,
                  cursor="hand2",
                  command=lambda: self._tout_selectionner(True)).pack(side="left", padx=(0, 3))
        tk.Button(btn_row, text="✘ Rien", bg=self.ENTRY, fg=self.FG,
                  font=("Segoe UI", 7), relief="flat", bd=0, padx=6, pady=3,
                  cursor="hand2",
                  command=lambda: self._tout_selectionner(False)).pack(side="left")
        tk.Button(btn_row, text="＋ Nouvelle ville", bg=self.ENTRY, fg=self.ACCENT,
                  font=("Segoe UI", 7, "bold"), relief="flat", bd=0, padx=6, pady=3,
                  cursor="hand2",
                  command=self._ouvrir_ajout_ville).pack(side="right")

        # ── Paramètres ──
        sep("Paramètres de simulation")
        self.nb_fourmis_entry = entry_row(p, "Nombre de fourmis :", "10")
        self.nb_iter_entry    = entry_row(p, "Nombre d'itérations :", "20")

        # ── Options ──
        sep("Options")
        tk.Checkbutton(p, text="Afficher l'animation des fourmis\n(plus lent – consomme plus de mémoire)",
                       variable=self.animer, bg=self.BG, fg=self.FG,
                       selectcolor=self.ENTRY, activebackground=self.BG,
                       activeforeground=self.ACCENT, font=("Segoe UI", 9),
                       justify="left", command=self._on_anim_change).pack(anchor="w", pady=(4, 2))

        self._anim_sub = tk.Frame(p, bg=self.BG)
        self._anim_sub.pack(fill="x")
        self.nb_simultane_entry = entry_row(self._anim_sub, "Fourmis simultanées :", "3")
        tk.Label(self._anim_sub, text="⚠ Plus il y en a, plus c'est lent",
                 bg=self.BG, fg=self.RED, font=("Segoe UI", 7, "italic")).pack(anchor="w")

        # ── Boutons ──
        tk.Frame(p, bg=self.BG, height=8).pack()

        self.btn_lancer = tk.Button(
            p, text="▶  Lancer la simulation",
            bg=self.ACCENT, fg=self.BG,
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
            padx=12, pady=8, cursor="hand2", command=self._lancer)
        self.btn_lancer.pack(fill="x", pady=(4, 2))

        self.btn_stop = tk.Button(
            p, text="⏹  Arrêter la simulation",
            bg="#45475a", fg=self.FG,
            font=("Segoe UI", 9), relief="flat", bd=0,
            padx=12, pady=6, cursor="hand2",
            state="disabled", command=self._stop)
        self.btn_stop.pack(fill="x", pady=2)

        self.btn_reset = tk.Button(
            p, text="↺  Réinitialiser",
            bg=self.ENTRY, fg=self.FG,
            font=("Segoe UI", 9), relief="flat", bd=0,
            padx=12, pady=6, cursor="hand2", command=self._reset)
        self.btn_reset.pack(fill="x", pady=2)

        # ── Console ──
        sep("Console")
        self.console = scrolledtext.ScrolledText(
            p, bg=self.BG2, fg=self.GREEN,
            font=("Courier New", 8), state="disabled",
            relief="flat", wrap="word")
        self.console.pack(fill="both", expand=True, pady=(0, 4))

        self._on_mode_change()
        self._on_anim_change()

    # ── Listbox : construction et utilitaires ──
    def _rebuild_listbox(self, select_new: str = None):
        """Reconstruit la Listbox depuis COORDS, en conservant la sélection."""
        old_sel = self._get_villes_selectionnees()
        self._listbox.delete(0, "end")
        for ville in sorted(COORDS.keys()):
            self._listbox.insert("end", ville)
        # Restaurer la sélection + sélectionner la nouvelle ville si fournie
        villes = sorted(COORDS.keys())
        for i, v in enumerate(villes):
            if v in old_sel or v == select_new:
                self._listbox.selection_set(i)
        self._maj_compteur()

    def _maj_compteur(self):
        n = len(self._listbox.curselection())
        self._selection_label.config(text=f"({n} sélectionnée{'s' if n > 1 else ''})")

    def _tout_selectionner(self, etat: bool):
        if etat:
            self._listbox.selection_set(0, "end")
        else:
            self._listbox.selection_clear(0, "end")
        self._maj_compteur()

    def _get_villes_selectionnees(self) -> list:
        villes = sorted(COORDS.keys())
        return [villes[i] for i in self._listbox.curselection()]

    # ── Fenêtre d'ajout de ville (recherche Nominatim) ──
    def _ouvrir_ajout_ville(self):
        win = tk.Toplevel(self.root)
        win.title("Ajouter une ville")
        win.configure(bg=self.BG)
        win.resizable(False, False)
        win.grab_set()

        pad = {"padx": 16, "pady": 5}

        tk.Label(win, text="➕  Nouvelle ville", bg=self.BG, fg=self.ACCENT,
                 font=("Segoe UI", 12, "bold")).pack(padx=16, pady=(14, 6))

        # Champ de recherche
        search_f = tk.Frame(win, bg=self.BG)
        search_f.pack(fill="x", **pad)
        tk.Label(search_f, text="Rechercher :", bg=self.BG, fg=self.FG,
                 font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")
        e_search = tk.Entry(search_f, bg=self.ENTRY, fg=self.FG,
                            insertbackground=self.FG,
                            font=("Segoe UI", 9), relief="flat", bd=4, width=22)
        e_search.pack(side="left", fill="x", expand=True)
        e_search.focus_set()

        btn_search = tk.Button(search_f, text="🔍", bg=self.ENTRY, fg=self.ACCENT,
                               font=("Segoe UI", 9), relief="flat", bd=0,
                               padx=6, cursor="hand2")
        btn_search.pack(side="left", padx=(4, 0))

        # Zone de résultats
        tk.Label(win, text="Résultats :", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 8, "italic")).pack(anchor="w", padx=16, pady=(4, 0))

        res_frame = tk.Frame(win, bg=self.BG2)
        res_frame.pack(fill="x", padx=16, pady=(2, 0))
        sb_res = tk.Scrollbar(res_frame, orient="vertical")
        lb_res = tk.Listbox(res_frame, height=5, bg=self.BG2, fg=self.FG,
                            selectbackground=self.ACCENT, selectforeground=self.BG,
                            font=("Segoe UI", 8), relief="flat", bd=0,
                            highlightthickness=0, activestyle="none",
                            yscrollcommand=sb_res.set)
        sb_res.config(command=lb_res.yview)
        sb_res.pack(side="right", fill="y")
        lb_res.pack(side="left", fill="both", expand=True)

        # Label infos du résultat sélectionné
        info_var = tk.StringVar(value="")
        tk.Label(win, textvariable=info_var, bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 7, "italic"), wraplength=300,
                 justify="left").pack(anchor="w", padx=16, pady=(2, 0))

        msg = tk.Label(win, text="", bg=self.BG, fg=self.RED,
                       font=("Segoe UI", 8, "italic"))
        msg.pack(padx=16, pady=(4, 0))

        # Stockage des résultats Nominatim {display_name: (lat, lon, nom_court)}
        _resultats = {}

        def _afficher_info(_e=None):
            sel = lb_res.curselection()
            if not sel:
                info_var.set("")
                return
            key = lb_res.get(sel[0])
            if key in _resultats:
                lat, lon, _ = _resultats[key]
                info_var.set(f"lat {lat:.5f}  /  lon {lon:.5f}")

        lb_res.bind("<<ListboxSelect>>", _afficher_info)

        def _rechercher(_e=None):
            query = e_search.get().strip()
            if not query:
                return
            msg.config(text="Recherche en cours…", fg=self.MUTED)
            win.update_idletasks()
            lb_res.delete(0, "end")
            _resultats.clear()
            info_var.set("")

            try:
                url = (
                    "https://nominatim.openstreetmap.org/search"
                    f"?q={urllib.request.quote(query)}&format=json&limit=8&addressdetails=1"
                )
                req = urllib.request.Request(
                    url, headers={"User-Agent": "AntSystemApp/1.0"})
                with urllib.request.urlopen(req, timeout=6) as r:
                    import json
                    data = json.loads(r.read().decode())

                if not data:
                    msg.config(text="Aucun résultat trouvé.", fg=self.RED)
                    return

                for item in data:
                    lat  = float(item["lat"])
                    lon  = float(item["lon"])
                    # Nom court : ville ou municipality ou county
                    addr = item.get("address", {})
                    nom_court = (addr.get("city") or addr.get("town") or
                                 addr.get("village") or addr.get("municipality") or
                                 addr.get("county") or query.title())
                    display = item.get("display_name", nom_court)[:60]
                    _resultats[display] = (lat, lon, nom_court)
                    lb_res.insert("end", display)

                msg.config(text=f"{len(data)} résultat(s) trouvé(s).", fg=self.GREEN)

            except Exception as ex:
                msg.config(text=f"Erreur réseau : {ex}", fg=self.RED)

        btn_search.config(command=_rechercher)
        e_search.bind("<Return>", _rechercher)

        def _valider():
            sel = lb_res.curselection()
            if not sel:
                msg.config(text="⚠ Sélectionnez un résultat.", fg=self.RED)
                return
            key  = lb_res.get(sel[0])
            lat, lon, nom_court = _resultats[key]

            # Utiliser nom_court comme nom de ville, mais laisser l'utilisateur le modifier
            nom = nom_court.strip()
            if nom in COORDS:
                msg.config(text=f"⚠ '{nom}' est déjà dans le catalogue.", fg=self.RED)
                return

            COORDS[nom] = (lat, lon)
            villes_disponibles.append(nom)
            villes_disponibles.sort()
            self._rebuild_listbox(select_new=nom)
            self._log(f"✔ Ville ajoutée : {nom}  ({lat:.5f}, {lon:.5f})")
            win.destroy()

        tk.Button(win, text="✔  Ajouter la ville sélectionnée",
                  bg=self.ACCENT, fg=self.BG,
                  font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                  padx=12, pady=6, cursor="hand2",
                  command=_valider).pack(fill="x", padx=16, pady=(8, 4))
        tk.Button(win, text="Annuler",
                  bg=self.ENTRY, fg=self.FG,
                  font=("Segoe UI", 8), relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  command=win.destroy).pack(fill="x", padx=16, pady=(0, 14))

        win.bind("<Escape>", lambda e: win.destroy())

    # ── Panneau droit ────────────────────────
    def _build_right(self, p):
        tk.Label(p, text="Visualisation du graphe", bg=self.BG3, fg=self.ACCENT,
                 font=("Segoe UI", 11, "bold")).pack(pady=(8, 2))

        # ── Barre de progression ──────────────
        prog = tk.Frame(p, bg=self.BG3)
        prog.pack(fill="x", padx=14, pady=(0, 6))

        top = tk.Frame(prog, bg=self.BG3)
        top.pack(fill="x")
        self._prog_label = tk.Label(top, text="En attente…",
                                    bg=self.BG3, fg=self.MUTED,
                                    font=("Segoe UI", 8))
        self._prog_label.pack(side="left")
        self._prog_pct = tk.Label(top, text="",
                                  bg=self.BG3, fg=self.ACCENT,
                                  font=("Segoe UI", 8, "bold"))
        self._prog_pct.pack(side="right")

        self._bar_canvas = tk.Canvas(prog, height=14, bg=self.ENTRY,
                                     highlightthickness=0, relief="flat")
        self._bar_canvas.pack(fill="x", pady=(3, 0))
        self._bar_canvas.bind("<Configure>", lambda e: self._redraw_bar(self._bar_pct_val))

        # ── Canvas matplotlib ──────────────────
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.fig.patch.set_facecolor(self.BG3)
        self.ax.set_facecolor(self.BG3)
        self.ax.axis("off")
        self.canvas = FigureCanvasTkAgg(self.fig, master=p)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._draw_placeholder()

    # ════════════════════════════════════════
    #  CALLBACKS
    # ════════════════════════════════════════
    def _on_mode_change(self):
        if self.mode.get() == "manuel":
            self.manuel_frame.pack(fill="x")
            self.aleatoire_frame.pack_forget()
        else:
            self.manuel_frame.pack_forget()
            self.aleatoire_frame.pack(fill="x")

    def _on_anim_change(self):
        if self.animer.get():
            self._anim_sub.pack(fill="x", pady=(0, 4))
        else:
            self._anim_sub.pack_forget()

    # ════════════════════════════════════════
    #  BARRE DE PROGRESSION
    # ════════════════════════════════════════
    def _redraw_bar(self, pct):
        c = self._bar_canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w <= 1:
            return
        c.delete("all")
        c.create_rectangle(0, 0, w, h, fill=self.ENTRY, outline="")
        fw = int(w * pct)
        if fw > 0:
            c.create_rectangle(0, 0, fw, h, fill=self.ACCENT, outline="")
            c.create_rectangle(0, 0, fw, h // 3, fill="#d4b7ff", outline="")

    def _set_progress(self, current, total, label=""):
        pct = current / total if total > 0 else 0
        self._bar_pct_val = pct
        def _do():
            self._prog_label.config(text=label)
            self._prog_pct.config(text=f"{int(pct * 100)} %")
            self._redraw_bar(pct)
        self.root.after(0, _do)

    def _reset_progress(self, msg="En attente…"):
        self._bar_pct_val = 0.0
        def _do():
            self._prog_label.config(text=msg)
            self._prog_pct.config(text="")
            self._redraw_bar(0.0)
        self.root.after(0, _do)

    # ════════════════════════════════════════
    #  CONSOLE
    # ════════════════════════════════════════
    def _log(self, text):
        def _do():
            self.console.config(state="normal")
            self.console.insert("end", text + "\n")
            self.console.see("end")
            self.console.config(state="disabled")
        self.root.after(0, _do)

    # ════════════════════════════════════════
    #  DESSIN DU GRAPHE
    # ════════════════════════════════════════
    def _draw_placeholder(self):
        self.ax.clear()
        self.ax.set_facecolor(self.BG3)
        self.ax.text(0.5, 0.5, "Le graphe s'affichera ici",
                     ha="center", va="center", color="#585b70",
                     fontsize=13, transform=self.ax.transAxes)
        self.ax.axis("off")
        self.canvas.draw()

    def _base_draw(self, G, pos, chemin=None, ants_snap=None, final=False):
        self.ax.clear()
        self.ax.set_facecolor(self.BG3)
        self.fig.patch.set_facecolor(self.BG3)

        # ── Carte de France en arrière-plan ──
        if self._carte_france is not None:
            try:
                self.ax.imshow(
                    self._carte_france,
                    extent=[0, 1, 0, 1],
                    aspect="auto",
                    alpha=0.45,
                )
            except Exception:
                pass
        self.ax.set_xlim(-0.02, 1.02)
        self.ax.set_ylim(-0.02, 1.02)

        pheromones = [G[u][v]["pheromone"] for u, v in G.edges()]
        max_ph = max(pheromones) if pheromones else 1
        widths = [0.5 + 3.5 * (p / max_ph) for p in pheromones]

        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color="#89b4fa", node_size=2800)
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_color=self.BG,
                                font_size=7, font_weight="bold")
        nx.draw_networkx_edges(G, pos, ax=self.ax, width=widths,
                               edge_color="#45475a", alpha=0.7)
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=nx.get_edge_attributes(G, "distance"),
            ax=self.ax, font_size=6, font_color=self.MUTED, bbox=dict(alpha=0))

        # ── Meilleur chemin ──
        if chemin and len(chemin) > 1:
            complet    = chemin + [chemin[0]]
            path_edges = [(complet[i], complet[i + 1]) for i in range(len(complet) - 1)]
            if final:
                D = nx.DiGraph()
                D.add_nodes_from(G.nodes)
                D.add_edges_from(path_edges)
                nx.draw_networkx_edges(
                    D, pos, ax=self.ax, edgelist=path_edges,
                    edge_color=self.RED, width=3, alpha=0.95,
                    arrows=True, arrowstyle="-|>", arrowsize=22,
                    connectionstyle="arc3,rad=0.08",
                    min_source_margin=18, min_target_margin=18)
                depart = chemin[0]
                nx.draw_networkx_nodes(G, pos, ax=self.ax, nodelist=[depart],
                                       node_color=self.GREEN, node_size=2800)
                nx.draw_networkx_labels(G, pos, ax=self.ax,
                                        labels={depart: depart},
                                        font_color=self.BG, font_size=7,
                                        font_weight="bold")
            else:
                nx.draw_networkx_edges(G, pos, edgelist=path_edges[:-1],
                                       ax=self.ax, edge_color=self.RED,
                                       width=3, style="solid", alpha=0.85)

        # ── Fourmis animées ──
        if ants_snap:
            for idx, state in ants_snap.items():
                color = state["color"]
                for (u, v) in state["trail"]:
                    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)],
                                           ax=self.ax, edge_color=color,
                                           width=2, alpha=0.55)
                self.ax.scatter(state["x"], state["y"],
                                c=color, s=240, zorder=10,
                                edgecolors=self.BG, linewidths=1.5)

        title = ("Meilleur chemin trouvé ✔ " if final else "Simulation en cours…")
        self.ax.set_title(title, color=self.ACCENT, fontsize=11,
                          fontweight="bold", pad=8)
        self.ax.axis("off")
        self.canvas.draw()

    def _draw_graph(self, G, pos, chemin=None, ants=None, final=False):
        """Planifie un redessin thread-safe."""
        snap = {}
        if ants is not None:
            with self._ants_lock:
                for k, v in ants.items():
                    snap[k] = {**v, "trail": list(v["trail"])}
        self.root.after(0, lambda: self._base_draw(G, pos, chemin, snap or None, final))

    # ════════════════════════════════════════
    #  CONTRÔLES
    # ════════════════════════════════════════
    def _reset(self):
        if self.simulation_running:
            return
        self.G = self.pos = None
        self._draw_placeholder()
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")
        self._reset_progress()
        self.btn_lancer.config(state="normal")
        self.btn_stop.config(state="disabled")

    def _stop(self):
        if self.simulation_running:
            self._stop_event.set()
            self._log("⏹ Arrêt demandé, fin de l'itération en cours…")
            self.btn_stop.config(state="disabled")

    def _lancer(self):
        if self.simulation_running:
            return
        try:
            nb_villes  = int(self.nb_villes_entry.get())
            nb_fourmis = int(self.nb_fourmis_entry.get())
            nb_iter    = int(self.nb_iter_entry.get())
        except ValueError:
            self._log("⚠ Les paramètres doivent être des entiers.")
            return

        if nb_villes < 4:
            self._log("⚠ Il est conseillé de mettre au minimum 4 villes.")
            return

        nb_simultane = 1
        if self.animer.get():
            try:
                nb_simultane = max(1, int(self.nb_simultane_entry.get()))
            except ValueError:
                nb_simultane = 1

        if self.mode.get() == "manuel":
            villes = self._get_villes_selectionnees()
            if len(villes) < 4:
                self._log("⚠ Sélectionnez au moins 4 villes en mode manuel.")
                return
            if len(villes) != nb_villes:
                self._log(f"⚠ {nb_villes} villes attendues, {len(villes)} sélectionnées.")
                return
        else:
            if nb_villes > len(villes_disponibles):
                self._log(f"⚠ Maximum {len(villes_disponibles)} villes disponibles.")
                return
            villes = None

        self._stop_event.clear()
        self.simulation_running = True
        self.btn_lancer.config(state="disabled")
        self.btn_stop.config(state="normal")

        threading.Thread(
            target=self._run_simulation,
            args=(nb_villes, nb_fourmis, nb_iter, villes, nb_simultane),
            daemon=True,
        ).start()

    # ════════════════════════════════════════
    #  SIMULATION (thread secondaire)
    # ════════════════════════════════════════
    def _run_simulation(self, nb_villes, nb_fourmis, nb_iter, villes_manuel, nb_simultane):
        animer = self.animer.get()
        try:
            # ── Création du graphe ──
            if villes_manuel:
                self._log("--- Création manuelle du graphe ---")
                G      = creer_graphe_manuel(villes_manuel)
                villes = villes_manuel
                self._log("Graphe créé avec succès !")
            else:
                self._log("--- Création aléatoire du graphe ---")
                G, villes = creer_graphe_rand(nb_villes)
                self._log("Villes sélectionnées : " + " → ".join(villes))

            self.G   = G
            # Positions géographiques réelles (remplace spring_layout)
            self.pos = build_pos(list(G.nodes))
            self._draw_graph(G, self.pos)
            self._log("\nLancement de la simulation…\n")

            meilleure_distance = float("inf")
            meilleur_chemin    = None
            total_steps        = nb_iter * nb_fourmis
            step               = 0
            NB_FRAMES          = 8

            for it in range(nb_iter):
                if self._stop_event.is_set():
                    self._log("⏹ Simulation interrompue.")
                    break

                self._log(f"=== Itération {it + 1}/{nb_iter} ===")
                self._set_progress(step, total_steps, f"Itération {it + 1} / {nb_iter}")

                fourmis = []

                if animer:
                    # ── Lots de fourmis animées simultanément ──
                    for batch_start in range(0, nb_fourmis, nb_simultane):
                        if self._stop_event.is_set():
                            break

                        batch = []
                        for bi in range(nb_simultane):
                            idx = batch_start + bi
                            if idx >= nb_fourmis:
                                break
                            depart = random.choice(list(G.nodes))
                            f      = Fourmi(depart)
                            color  = ANT_COLORS[idx % len(ANT_COLORS)]
                            x0, y0 = self.pos[depart]
                            with self._ants_lock:
                                self._ants_state[idx] = {
                                    "x": x0, "y": y0,
                                    "trail": [], "color": color,
                                }
                            batch.append((idx, f, color))

                        for _ in range(len(G.nodes) - 1):
                            if self._stop_event.is_set():
                                break

                            moves = []
                            for idx, f, color in batch:
                                anc = f.position
                                if deplacement_fourmi(G, f):
                                    moves.append((idx, f, color, anc, f.position))

                            if not moves:
                                break

                            p1 = {idx: self.pos[anc] for idx, _, _, anc, _ in moves}
                            p2 = {idx: self.pos[nv]  for idx, _, _, _, nv  in moves}

                            for frame in range(NB_FRAMES + 1):
                                if self._stop_event.is_set():
                                    break
                                t = frame / NB_FRAMES
                                with self._ants_lock:
                                    for idx, f, color, anc, nv in moves:
                                        xi = p1[idx][0] + t * (p2[idx][0] - p1[idx][0])
                                        yi = p1[idx][1] + t * (p2[idx][1] - p1[idx][1])
                                        self._ants_state[idx]["x"] = xi
                                        self._ants_state[idx]["y"] = yi
                                        if frame == NB_FRAMES:
                                            self._ants_state[idx]["trail"].append((anc, nv))
                                self._draw_graph(G, self.pos,
                                                 chemin=meilleur_chemin,
                                                 ants=self._ants_state)
                                time.sleep(0.025)

                        for idx, f, color in batch:
                            fourmis.append(f)
                            self._log(f"  Fourmi {idx+1} | {' → '.join(f.visite)} | {round(f.distance, 2)} km")
                            if f.distance < meilleure_distance:
                                meilleure_distance = f.distance
                                meilleur_chemin    = f.visite[:]
                            with self._ants_lock:
                                self._ants_state.pop(idx, None)

                else:
                    # ── Sans animation ──
                    for i in range(nb_fourmis):
                        if self._stop_event.is_set():
                            break
                        depart = random.choice(list(G.nodes))
                        f      = Fourmi(depart)
                        for _ in range(len(G.nodes) - 1):
                            deplacement_fourmi(G, f)
                        fourmis.append(f)
                        self._log(f"  Fourmi {i+1} | {' → '.join(f.visite)} | {round(f.distance, 2)} km")
                        if f.distance < meilleure_distance:
                            meilleure_distance = f.distance
                            meilleur_chemin    = f.visite[:]

                mise_a_jour_pheromones(G, fourmis)
                step += nb_fourmis
                self._set_progress(step, total_steps, f"Itération {it + 1} / {nb_iter}")
                self._draw_graph(G, self.pos, chemin=meilleur_chemin)

            # ── Résultat final ──
            if meilleur_chemin:
                self._log("\n" + "=" * 42)
                self._log("=== RÉSULTAT FINAL ===")
                self._log("=" * 42)
                self._log("Meilleur chemin : " + " → ".join(meilleur_chemin + [meilleur_chemin[0]]))
                self._log(f"Distance totale : {round(meilleure_distance, 2)} km")
                self._log("=" * 42)
                self._set_progress(total_steps, total_steps, "Simulation terminée ✔")
                self._draw_graph(G, self.pos, chemin=meilleur_chemin, final=True)
            else:
                self._log("Aucun chemin complet trouvé.")
                self._reset_progress("Simulation arrêtée.")

        except Exception as e:
            import traceback
            self._log(f"⚠ Erreur : {e}\n{traceback.format_exc()}")
        finally:
            with self._ants_lock:
                self._ants_state.clear()
            self.simulation_running = False
            self.root.after(0, lambda: (
                self.btn_lancer.config(state="normal"),
                self.btn_stop.config(state="disabled"),
            ))


# ═══════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    AntSystemApp(root)
    root.mainloop()
