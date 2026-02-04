import random
import math
import time
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# ============================================================================
# CONSTANTES
# ============================================================================


random.seed(42)

def haversine(a, b):
    lat1, lon1 = coords[a]
    lat2, lon2 = coords[b]
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return int(R * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x)))

VILLES_DISPONIBLES = [
    "Paris","Marseille","Lyon","Toulouse","Nice","Nantes","Strasbourg","Montpellier","Bordeaux","Lille",
    "Rennes","Reims","Le Havre","Dijon","Grenoble","Clermont-Ferrand","Limoges","Toulon","Saint-Étienne","Perpignan",
    "Bayonne","Amiens","Angers","Annecy","Avignon","Besançon","Biarritz","Brest","Caen","Chambéry",
    "Cherbourg","Colmar","Épinal","La Rochelle","Metz","Mulhouse","Nancy","Orléans","Pau","Poitiers",
    "Quimper","Saint-Malo","Tarbes","Tours","Troyes","Valence","Vannes","Vichy","Villeurbanne","Ajaccio",
    "Albi","Agen","Arles","Aurillac","Auxerre","Bagnères-de-Bigorre","Bar-le-Duc","Beauvais","Belfort","Bergerac",
    "Bernay","Blois","Brive-la-Gaillarde","Cahors","Calais","Cambrai","Carcassonne","Castres","Chalon-sur-Saône","Charleville-Mézières",
    "Châteauroux","Châtellerault","Chaumont","Cluses","Compiègne","Corte","Dax","Dieppe","Dole","Draguignan",
    "Dunkerque","Évreux","Figeac","Foix","Fontainebleau","Fréjus","Gap","Gex","Givet","Guéret",
    "Haguenau","Hyères","Issoire","La Ciotat","La Roche-sur-Yon","Langres","Lannion","Laval","Lectoure","Libourne",
    "Lons-le-Saunier","Lorient","Lourdes","Lunéville","Mâcon","Manosque","Marmande","Martigues","Mayenne","Millau",
    "Moissac","Mont-de-Marsan","Montargis","Montbéliard","Morlaix","Moulins","Narbonne","Nevers","Nîmes","Niort",
    "Orange","Oyonnax","Pamiers","Périgueux","Pontarlier","Prades","Riom","Rodez","Romorantin-Lanthenay","Roanne",
    "Saint-Brieuc","Saint-Dié-des-Vosges","Saint-Flour","Saint-Gaudens","Saint-Junien","Saint-Lô","Saint-Nazaire","Saint-Omer","Sarlat-la-Canéda","Saverne",
    "Sélestat","Sens","Sète","Soissons","Tarascon","Thionville","Thonon-les-Bains","Tulle","Ussel","Verdun",
    "Vesoul","Vienne","Vierzon","Villeneuve-sur-Lot","Vire","Wissembourg","Yssingeaux","Abbeville","Albert","Alençon",
    "Ambert","Annonay","Arcachon","Argentan","Auch","Autun","Barcelonnette","Bastia","Bellegarde-sur-Valserine","Berck",
    "Béthune","Bollène","Briançon","Bourg-en-Bresse","Bourgoin-Jallieu","Carpentras","Châteaulin","Chinon","Cognac","Concarneau",
    "Cosne-Cours-sur-Loire","Coulommiers","Crest","Decazeville","Douai","Elbeuf","Fécamp","Forbach","Gray","Hendaye",
    "Issoudun","Jonzac","Landerneau","Le Creusot","Les Sables-d’Olonne","Longwy","Louhans","Maubeuge","Menton","Mirande",
    "Monistrol-sur-Loire","Nogent-le-Rotrou","Oloron-Sainte-Marie","Pontivy","Redon","Remiremont","Rethel","Saint-Amand-Montrond","Saint-Claude","Saint-Girons",
    "Saint-Priest","Sainte-Foy-la-Grande","Sarrebourg","Sarreguemines","Segré","Sisteron","Tournon-sur-Rhône","Uzès","Valenciennes","Vendôme"
]

coords = {}
for i, c in enumerate(VILLES_DISPONIBLES):
    lat = 42.0 + (i % 90) * (9.0 / 89)
    lon = -5.0 + (i // 90) * (13.0 / 3)
    coords[c] = (lat, lon)

DISTANCES = {}
for i in range(len(VILLES_DISPONIBLES)):
    for j in range(i + 1, len(VILLES_DISPONIBLES)):
        a, b = VILLES_DISPONIBLES[i], VILLES_DISPONIBLES[j]
        DISTANCES[(a, b)] = haversine(a, b)


# ============================================================================
# CLASSE FOURMI
# ============================================================================

class Fourmi:
    def __init__(self, position: str):
        self.position = position
        self.visite = [position]
        self.distance = 0
        
    def get_position(self):
        return self.position

    def deplacement(self, new_pos: str, distance: float):
        self.position = new_pos
        self.visite.append(new_pos)
        self.distance += distance


# ============================================================================
# FONCTIONS ANT SYSTEM (identiques à la version console)
# ============================================================================

def ajouter_aretes(G, villes):
    """Ajoute les arêtes au graphe avec distances et phéromones."""
    for i in range(len(villes)):
        for j in range(i + 1, len(villes)):
            v1, v2 = villes[i], villes[j]
            d = DISTANCES.get((v1, v2)) or DISTANCES.get((v2, v1))
            if d is None:
                raise ValueError(f"Distance inconnue entre {v1} et {v2}")
            G.add_edge(v1, v2, distance=d, pheromone=pheromone_initiale(d))


def pheromone_initiale(distance: float, C: float = 100) -> float:
    return C / distance


def calculer_probabilites(G, fourmi, alpha: float = 1, beta: float = 2):
    position = fourmi.position
    voisins = []
    poids = []
    
    for v in G.neighbors(position):
        if v not in fourmi.visite:
            pheromone = G[position][v]["pheromone"]
            distance = G[position][v]["distance"]
            visibilite = 1 / distance
            valeur = (pheromone ** alpha) * (visibilite ** beta)
            voisins.append(v)
            poids.append(valeur)
    
    return voisins, poids


def deplacement_fourmi(G, fourmi, alpha: float = 1, beta: float = 2) -> bool:
    voisins, poids = calculer_probabilites(G, fourmi, alpha, beta)
    
    if not voisins:
        return False
    
    destination = random.choices(voisins, weights=poids, k=1)[0]
    distance = G[fourmi.position][destination]["distance"]
    fourmi.deplacement(destination, distance)
    return True


def mise_a_jour_pheromones(G, fourmis, rho: float = 0.5, Q: float = 100):
    for u, v in G.edges():
        G[u][v]["pheromone"] *= (1 - rho)
    
    for fourmi in fourmis:
        contribution = Q / fourmi.distance
        for i in range(len(fourmi.visite) - 1):
            u = fourmi.visite[i]
            v = fourmi.visite[i + 1]
            G[u][v]["pheromone"] += contribution


# ============================================================================
# INTERFACE GRAPHIQUE
# ============================================================================

class AntSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ant System - Optimisation par Colonie de Fourmis")
        self.root.geometry("1200x800")
        
        # Variables
        self.G = None
        self.villes = []
        self.pos = None
        self.meilleur_chemin = None
        self.meilleure_distance = float('inf')
        self.simulation_en_cours = False
        
        # Créer l'interface
        self.creer_interface()
        
    def creer_interface(self):
        # ===== PANNEAU GAUCHE : PARAMETRES =====
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        titre = ttk.Label(left_frame, text="ANT SYSTEM", font=("Arial", 16, "bold"))
        titre.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Sélection des villes
        ttk.Label(left_frame, text="Nombre de villes:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.nb_villes_var = tk.IntVar(value=6)
        ttk.Spinbox(left_frame, from_=4, to=300, textvariable=self.nb_villes_var, width=10).grid(row=1, column=1, pady=5)
        
        # Nombre de fourmis
        ttk.Label(left_frame, text="Nombre de fourmis:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.nb_fourmis_var = tk.IntVar(value=10)
        ttk.Spinbox(left_frame, from_=1, to=50, textvariable=self.nb_fourmis_var, width=10).grid(row=2, column=1, pady=5)
        
        # Nombre d'itérations
        ttk.Label(left_frame, text="Nombre d'iterations:", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.nb_iterations_var = tk.IntVar(value=20)
        ttk.Spinbox(left_frame, from_=1, to=100, textvariable=self.nb_iterations_var, width=10).grid(row=3, column=1, pady=5)
        
        # Animation
        self.animer_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_frame, text="Animer les deplacements", variable=self.animer_var).grid(row=4, column=0, columnspan=2, pady=10)
        
        # Boutons
        ttk.Button(left_frame, text="Generer Graphe Aleatoire", command=self.generer_graphe).grid(row=5, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(left_frame, text="Lancer Simulation", command=self.lancer_simulation, style="Accent.TButton").grid(row=6, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(left_frame, text="Arreter Simulation", command=self.arreter_simulation).grid(row=7, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Zone de résultats
        ttk.Label(left_frame, text="Resultats:", font=("Arial", 12, "bold")).grid(row=8, column=0, columnspan=2, pady=(20,5))
        
        self.resultats_text = tk.Text(left_frame, height=15, width=40, font=("Courier", 9))
        self.resultats_text.grid(row=9, column=0, columnspan=2, pady=5)
        
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.resultats_text.yview)
        scrollbar.grid(row=9, column=2, sticky=(tk.N, tk.S))
        self.resultats_text.configure(yscrollcommand=scrollbar.set)
        
        # Barre de progression
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=10, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(left_frame, text="Pret", font=("Arial", 9))
        self.status_label.grid(row=11, column=0, columnspan=2)
        
        # ===== PANNEAU DROIT : GRAPHIQUE =====
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Figure matplotlib
        self.fig, self.ax = plt.subplots(figsize=(9, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configuration grille
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Message initial
        self.ax.text(0.5, 0.5, "Cliquez sur 'Generer Graphe Aleatoire'\npour commencer", 
                    ha='center', va='center', fontsize=14, transform=self.ax.transAxes)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def generer_graphe(self):
        """Génère un graphe aléatoire."""
        nb = self.nb_villes_var.get()
        nb = max(4, min(nb, len(VILLES_DISPONIBLES)))
        
        self.villes = random.sample(VILLES_DISPONIBLES, nb)
        self.G = nx.Graph()
        
        for ville in self.villes:
            self.G.add_node(ville)
        
        ajouter_aretes(self.G, self.villes)
        
        # Calculer layout
        try:
            self.pos = nx.kamada_kawai_layout(self.G)
        except:
            self.pos = nx.spring_layout(self.G, seed=42, k=1.5, iterations=50)
        
        # Afficher le graphe
        self.afficher_graphe_initial()
        
        # Mettre à jour les résultats
        self.resultats_text.delete(1.0, tk.END)
        self.resultats_text.insert(tk.END, f"Graphe genere !\n\n")
        self.resultats_text.insert(tk.END, f"Villes selectionnees:\n")
        for ville in self.villes:
            self.resultats_text.insert(tk.END, f"  - {ville}\n")
        
        self.status_label.config(text="Graphe pret - Cliquez sur 'Lancer Simulation'")
    
    def afficher_graphe_initial(self):
        """Affiche le graphe initial."""
        self.ax.clear()
        
        nx.draw(
            self.G,
            self.pos,
            ax=self.ax,
            with_labels=True,
            node_color="lightgreen",
            node_size=700,
            edge_color="lightgray",
            width=1,
            font_size=9
        )
        
        labels = nx.get_edge_attributes(self.G, "distance")
        nx.draw_networkx_edge_labels(self.G, self.pos, edge_labels=labels, font_size=7, ax=self.ax)
        
        self.ax.set_title("Graphe des villes", fontsize=12, fontweight='bold')
        self.canvas.draw()
    
    def lancer_simulation(self):
        """Lance la simulation dans un thread séparé."""
        if self.G is None:
            messagebox.showwarning("Attention", "Veuillez d'abord generer un graphe !")
            return
        
        if self.simulation_en_cours:
            messagebox.showinfo("Info", "Une simulation est deja en cours !")
            return
        
        self.simulation_en_cours = True
        self.meilleure_distance = float('inf')
        self.meilleur_chemin = None
        
        # Lancer dans un thread pour ne pas bloquer l'interface
        thread = threading.Thread(target=self.executer_simulation)
        thread.daemon = True
        thread.start()
    
    def arreter_simulation(self):
        """Arrête la simulation."""
        self.simulation_en_cours = False
        self.status_label.config(text="Simulation arretee")
    
    def executer_simulation(self):
        """Exécute la simulation Ant System."""
        nb_fourmis = self.nb_fourmis_var.get()
        iterations = self.nb_iterations_var.get()
        animer = self.animer_var.get()
        
        self.resultats_text.delete(1.0, tk.END)
        self.resultats_text.insert(tk.END, "=== SIMULATION EN COURS ===\n\n")
        
        for it in range(iterations):
            if not self.simulation_en_cours:
                break
            
            # Mise à jour statut
            self.status_label.config(text=f"Iteration {it+1}/{iterations}")
            self.progress_var.set((it / iterations) * 100)
            
            self.resultats_text.insert(tk.END, f"\n--- Iteration {it+1}/{iterations} ---\n")
            
            fourmis = []
            aretes_visitees = set()
            
            for i in range(nb_fourmis):
                if not self.simulation_en_cours:
                    break
                
                depart = random.choice(list(self.G.nodes))
                f = Fourmi(depart)
                
                # Déplacer la fourmi
                for _ in range(len(self.G.nodes) - 1):
                    ancienne_position = f.position
                    succes = deplacement_fourmi(self.G, f)
                    
                    if succes and animer:
                        edge = tuple(sorted([ancienne_position, f.position]))
                        aretes_visitees.add(edge)
                        self.root.after(0, self.afficher_animation, aretes_visitees)
                        time.sleep(0.05)
                
                # Retour au départ
                ancienne_position = f.position
                ville_depart = f.visite[0]
                distance_retour = self.G[f.position][ville_depart]["distance"]
                f.deplacement(ville_depart, distance_retour)
                
                if animer:
                    edge = tuple(sorted([ancienne_position, ville_depart]))
                    aretes_visitees.add(edge)
                    self.root.after(0, self.afficher_animation, aretes_visitees)
                    time.sleep(0.05)
                
                fourmis.append(f)
                
                # Afficher résultat fourmi
                self.resultats_text.insert(tk.END, f"Fourmi {i+1}: {round(f.distance, 2)} km\n")
                self.resultats_text.see(tk.END)
                
                # Mettre à jour meilleur
                if f.distance < self.meilleure_distance:
                    self.meilleure_distance = f.distance
                    self.meilleur_chemin = f.visite[:]
            
            # Mise à jour phéromones
            mise_a_jour_pheromones(self.G, fourmis)
        
        # Fin simulation
        self.simulation_en_cours = False
        self.progress_var.set(100)
        self.status_label.config(text="Simulation terminee !")
        
        # Afficher résultat final
        self.resultats_text.insert(tk.END, f"\n{'='*40}\n")
        self.resultats_text.insert(tk.END, f"MEILLEUR CHEMIN TROUVE:\n")
        self.resultats_text.insert(tk.END, f"{' -> '.join(self.meilleur_chemin)}\n")
        self.resultats_text.insert(tk.END, f"\nDistance totale: {round(self.meilleure_distance, 2)} km\n")
        self.resultats_text.insert(tk.END, f"{'='*40}\n")
        self.resultats_text.see(tk.END)
        
        # Afficher graphe final
        self.root.after(0, self.afficher_graphe_final)
    
    def afficher_animation(self, aretes_visitees):
        """Affiche l'animation pendant la simulation."""
        self.ax.clear()
        
        # Graphe de base
        nx.draw(
            self.G,
            self.pos,
            ax=self.ax,
            with_labels=True,
            node_color="lightgreen",
            node_size=700,
            edge_color="lightgray",
            width=1,
            font_size=9
        )
        
        # Arêtes visitées en rouge
        edges_to_draw = [(u, v) for u, v in self.G.edges() 
                         if tuple(sorted([u, v])) in aretes_visitees]
        nx.draw_networkx_edges(
            self.G, 
            self.pos, 
            edgelist=edges_to_draw, 
            edge_color="red", 
            width=3,
            alpha=0.7,
            ax=self.ax
        )
        
        self.ax.set_title("Simulation en cours...", fontsize=12, fontweight='bold')
        self.canvas.draw()
    
    def afficher_graphe_final(self):
        """Affiche le graphe avec le meilleur chemin."""
        self.ax.clear()
        
        # Phéromones pour épaisseur
        pheromones = [self.G[u][v]["pheromone"] for u, v in self.G.edges()]
        max_phero = max(pheromones) if pheromones else 1
        widths = [0.8 + 3 * (p / max_phero) for p in pheromones]
        
        # Graphe de base
        nx.draw(
            self.G,
            self.pos,
            ax=self.ax,
            with_labels=True,
            node_size=700,
            node_color="lightgreen",
            font_size=9,
            width=widths,
            edge_color="gray"
        )
        
        # Meilleur chemin en rouge
        if self.meilleur_chemin:
            D = nx.DiGraph()
            for i in range(len(self.meilleur_chemin) - 1):
                D.add_edge(self.meilleur_chemin[i], self.meilleur_chemin[i + 1])
            
            nx.draw_networkx_edges(
                D,
                self.pos,
                edge_color="red",
                width=4,
                arrows=True,
                arrowstyle="-|>",
                arrowsize=20,
                ax=self.ax
            )
        
        self.ax.set_title(f"Meilleur chemin : {round(self.meilleure_distance, 2)} km", 
                         fontsize=12, fontweight='bold')
        self.canvas.draw()


# ============================================================================
# LANCEMENT
# ============================================================================

def main():
    root = tk.Tk()
    app = AntSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
