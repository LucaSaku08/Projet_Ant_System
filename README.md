# 🐜 Ant System – Visualisation TSP sur carte de France

Simulation interactive de l'algorithme **Ant System** (colonie de fourmis) appliqué au problème du voyageur de commerce (TSP), avec visualisation géographique sur carte de France.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Tkinter](https://img.shields.io/badge/UI-Tkinter-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Aperçu

L'algorithme Ant System simule le comportement de fourmis qui déposent des phéromones sur leurs trajets. Au fil des itérations, les meilleures routes accumulent plus de phéromones et sont davantage empruntées — faisant émerger progressivement le chemin le plus court entre les villes sélectionnées.

Les villes sont positionnées selon leurs **vraies coordonnées GPS**, les distances calculées par la **formule de Haversine**, et le tout est affiché sur une carte de France en arrière-plan.

---

## Fonctionnalités

- **Deux modes de sélection des villes** : aléatoire ou manuel via une liste cliquable (multi-sélection)
- **21 villes françaises** pré-configurées, extensible à volonté
- **Ajout de ville à la volée** : recherche automatique des coordonnées via Nominatim (OpenStreetMap)
- **Animation des fourmis** en temps réel (optionnelle)
- **Carte de fond** : chargement automatique de `france_map.png` ou téléchargement OSM en fallback
- **Console intégrée** avec logs de simulation (meilleure distance, convergence…)
- **Barre de progression** par itération

---

## Installation

### Prérequis

- Python 3.9 ou supérieur
- pip

### Dépendances

```bash
pip install networkx matplotlib
```

> `tkinter` est inclus dans la bibliothèque standard Python. Si absent (Linux) :
> ```bash
> sudo apt install python3-tk
> ```

---

## Lancement

```bash
python antsystem_geo.py
```

Placez `france_map.png` dans le même dossier que le script pour afficher la carte en fond (voir section [Carte de fond](#carte-de-fond)).

---

## Utilisation

### Mode aléatoire

1. Sélectionnez **Aléatoire**
2. Indiquez le nombre de villes souhaité
3. Ajustez les paramètres et cliquez **▶ Lancer**

### Mode manuel

1. Sélectionnez **Manuel**
2. Cliquez sur les villes souhaitées dans la liste (`Ctrl+clic` pour sélection multiple, `Shift+clic` pour une plage)
3. Mettez le champ *Nombre de villes* en accord avec votre sélection
4. Cliquez **▶ Lancer**

### Ajouter une nouvelle ville

Cliquez sur **＋ Nouvelle ville** (mode manuel) ou **＋ Ajouter une ville au catalogue** (mode aléatoire), saisissez le nom et lancez la recherche — les coordonnées sont récupérées automatiquement via OpenStreetMap.

---

## Paramètres de simulation

| Paramètre | Description | Valeur par défaut |
|---|---|---|
| Nombre de villes | Villes incluses dans le TSP | 6 |
| Nombre de fourmis | Fourmis par itération | 10 |
| Nombre d'itérations | Durée de la simulation | 20 |
| Animation | Affiche les fourmis en mouvement | Non |
| Fourmis simultanées | Fourmis visibles en même temps (si animation) | 3 |

---

## Carte de fond

Le programme cherche `france_map.png` dans cet ordre :
1. Dossier du script
2. Dossier courant (`os.getcwd()`)
3. Téléchargement automatique depuis OpenStreetMap (nécessite internet)

**Format attendu :** PNG, emprise `lon -5.2 → 9.7 / lat 41.3 → 51.2`, ~900×600 px.

Pour générer une carte compatible, utilisez cette URL dans votre navigateur :
```
https://render.openstreetmap.org/cgi-bin/export?bbox=-5.2,41.3,9.7,51.2&scale=3000000&format=png
```

---

## Ajouter une ville manuellement dans le code

Dans `COORDS`, ajoutez une ligne au format `"Nom": (latitude, longitude)` :

```python
COORDS = {
    ...
    "Brest": (48.3904, -4.4861),
}
```

Aucune autre modification nécessaire — distances et positions sont recalculées automatiquement.

Si la ville est hors de l'emprise France, ajustez `MAP_BOUNDS` :

```python
MAP_BOUNDS = (-5.2, 9.7, 41.3, 51.2)  # (lon_min, lon_max, lat_min, lat_max)
```

---

## Structure du projet

```
antsystem_geo.py   ← script principal
france_map.png     ← carte de fond (optionnelle, à placer ici)
README.md
```

---

## Algorithme

L'Ant System (Dorigo, 1992) repose sur trois mécanismes :

- **Construction de solution** : chaque fourmi choisit sa prochaine ville selon une probabilité dépendant des phéromones (exploitation) et de l'inverse de la distance (heuristique).
- **Évaporation** : les phéromones diminuent à chaque itération (`ρ = 0.5`).
- **Dépôt** : après chaque tour complet, chaque fourmi dépose des phéromones proportionnellement à la qualité de son trajet (`Q / distance`).

La **meilleure solution globale** est conservée et affichée en surbrillance à chaque itération.

---

## Concepts du cours utilisés

Ce projet s'appuie directement sur les notions abordées dans le cours *Les graphes en Python* (C. Guyeux).

### Type de graphe — graphe non orienté pondéré simple

Le graphe modélisant les villes est un **graphe non orienté simple pondéré** (cours p. 3, 14, 24) : pas d'arcs multiples, pas de boucles, et chaque arête porte un poids (la distance en km entre deux villes).

```python
G = nx.Graph()                          # graphe non orienté (cours p. 22)
G.add_node(v)                           # ajout de sommets (cours p. 22)
G.add_edge(v1, v2, distance=d,          # arêtes pondérées (cours p. 24)
           pheromone=pheromone_initiale(d))
```

### Construction du graphe avec NetworkX

Utilisation de `nx.Graph()`, `add_node()`, `add_edge()` et parcours des voisins via `G.neighbors()`, conformément aux exemples du cours (p. 22–25) :

```python
for v in G.neighbors(fourmi.position):   # voisins d'un sommet (cours p. 25)
    ph  = G[fourmi.position][v]["pheromone"]
    vis = 1 / G[fourmi.position][v]["distance"]
```

### Parcours hamiltonien — problème du voyageur de commerce

Le cœur du projet est la recherche d'un **circuit hamiltonien de coût minimal** (cours p. 105) : chaque fourmi construit un parcours passant **exactement une fois par chaque sommet**, ce qui est la définition exacte d'un parcours hamiltonien.

> *"Un parcours est hamiltonien s'il passe exactement une fois par tout sommet du graphe. Problème voisin : le voyageur de commerce (circuit hamiltonien de coût optimal)."* — cours p. 105

```python
# Chaque fourmi visite chaque ville exactement une fois
if v not in fourmi.visite:   # on ne repasse pas par un sommet déjà visité
    voisins.append(v)
```

### Graphe pondéré et matrice de phéromones

Les **poids des arêtes** (cours p. 24) sont utilisés doublement : pour la distance (`distance`) et pour les phéromones (`pheromone`), deux attributs stockés sur chaque arête du graphe NetworkX.

```python
G.add_edge(v1, v2, distance=d, pheromone=pheromone_initiale(d))
# Lecture du poids : G[u][v]["distance"], G[u][v]["pheromone"]
```

### Visualisation avec NetworkX et Matplotlib

Affichage du graphe avec les fonctions de dessin de NetworkX (cours p. 23, 48–53) :

```python
nx.draw_networkx_nodes(G, pos, ax=ax, ...)     # cours p. 63
nx.draw_networkx_edges(G, pos, ax=ax, ...)     # cours p. 63
nx.draw_networkx_labels(G, pos, ax=ax, ...)    # cours p. 63
nx.draw_networkx_edge_labels(G, pos, ...)      # cours p. 51
```

Utilisation d'un **layout personnalisé** (cours p. 49) : au lieu d'un layout automatique (`spring_layout`, `circular_layout`…), les positions des nœuds sont calculées à partir des **vraies coordonnées GPS**, converties en coordonnées normalisées [0,1]×[0,1] alignées sur l'emprise de la carte.

```python
# Équivalent d'un layout manuel (cours p. 49)
pos = build_pos(list(G.nodes))  # pos = {ville: (x, y)} en coords normalisées
```

### Degré des sommets et structure du graphe complet

Le graphe créé est **complet** : toutes les paires de villes sont reliées (cours p. 74–75). Pour `n` villes, il possède `n(n-1)/2` arêtes. Chaque sommet a un degré de `n-1`.

```python
# Construction du graphe complet : toutes les paires (i, j) avec i < j
for i in range(len(villes)):
    for j in range(i + 1, len(villes)):
        G.add_edge(villes[i], villes[j], ...)
```

### Connexité

Le graphe est **connexe** par construction (cours p. 91) : puisqu'il est complet, il existe une arête entre toute paire de sommets. Cela garantit que chaque fourmi peut toujours compléter son tour.

---

## Licence

MIT — libre d'utilisation, modification et distribution.
