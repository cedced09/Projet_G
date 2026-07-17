# Spécification du MVP

## Objectif

Fournir un cockpit personnel utilisable quotidiennement, avant toute automatisation avancée.

## Parcours principal

1. L'utilisateur ouvre l'application.
2. Il consulte les nouveaux biens et annonces.
3. Il filtre et visualise les résultats.
4. Il ouvre une fiche détaillée.
5. Il classe le bien et ajoute un commentaire.
6. Il peut retrouver l'historique de ses décisions.

## Fonctionnalités obligatoires

### 1. Création manuelle d'un bien

Champs minimaux :

- titre interne ;
- type de bien ;
- commune ou zone textuelle ;
- prix affiché ;
- surface habitable ;
- surface du terrain ;
- nombre de chambres ;
- nombre d'unités d'hébergement ;
- description libre ;
- source ;
- URL de l'annonce.

Les champs inconnus doivent pouvoir rester vides.

### 2. Liste des biens

Afficher au minimum :

- titre ;
- commune ;
- prix ;
- terrain ;
- surface habitable ;
- statut utilisateur ;
- score global lorsqu'il existe ;
- date de première observation ;
- date de dernière observation ;
- nombre d'annonces rattachées.

Filtres initiaux :

- texte ;
- statut ;
- fourchette de prix ;
- surface de terrain minimale ;
- source ;
- nouveau depuis une date.

### 3. Fiche détaillée

Afficher :

- données canoniques du bien ;
- annonces associées ;
- historique de prix ;
- commentaires ;
- décisions ;
- origine de chaque information ;
- avertissements sur les données incertaines.

### 4. Statuts utilisateur

Valeurs initiales :

- `new`
- `to_review`
- `interesting`
- `favorite`
- `rejected`
- `archived`

### 5. Commentaires et raisons

Un commentaire doit pouvoir être accompagné de raisons structurées :

- localisation ;
- voisinage ;
- qualité du logement privé ;
- potentiel d'exploitation ;
- terrain ;
- travaux ;
- urbanisme ;
- rentabilité ;
- saisonnalité ;
- autre.

### 6. Historique

Ne jamais écraser silencieusement :

- les anciens prix ;
- les anciens statuts ;
- les commentaires ;
- les modifications de critères ;
- les rapprochements de doublons.

## Fonctionnalités hors MVP initial

- scraping ;
- ingestion d'email ;
- LLM ;
- agent conversationnel ;
- géocodage automatique ;
- calcul d'itinéraire ;
- données cadastrales ;
- Géorisques ;
- DVF ;
- analyse d'images ;
- modèle prédictif de préférence.

Ces fonctions seront ajoutées par incréments.

## Critères d'acceptation du premier incrément

- L'application démarre avec Docker Compose.
- La base est créée par migration.
- Un bien peut être ajouté par l'interface.
- Une annonce peut être rattachée à ce bien.
- La liste des biens est persistante.
- Les champs facultatifs sont gérés proprement.
- Les montants sont stockés sans flottants.
- Les tests passent dans un environnement propre.
