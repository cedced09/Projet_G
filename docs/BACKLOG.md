# Backlog priorisé

## Phase 0 — Fondation

### P0.1 Initialiser le dépôt

- Python 3.12
- `pyproject.toml`
- Ruff
- mypy
- pytest
- structure des modules
- README de développement

**Acceptation :** les commandes qualité s'exécutent sur un projet vide.

### P0.2 Environnement Docker

- PostgreSQL + PostGIS
- variables d'environnement
- volume persistant
- healthcheck

**Acceptation :** la base démarre et accepte une connexion depuis l'application.

### P0.3 Migrations

- Alembic
- migration initiale
- commande documentée

**Acceptation :** une base vierge peut être migrée sans opération manuelle.

## Phase 1 — Première tranche verticale

### P1.1 Entités `Property` et `Listing`

- modèles de domaine ;
- modèles SQLAlchemy ;
- repositories ;
- services applicatifs.

### P1.2 Création manuelle

- formulaire Streamlit ;
- validation ;
- gestion des erreurs ;
- tests.

### P1.3 Liste des biens

- tableau ;
- tri ;
- filtres minimaux ;
- lien vers détail.

### P1.4 Fiche d'un bien

- données canoniques ;
- annonces ;
- dates d'observation ;
- modification simple.

## Phase 2 — Décisions utilisateur

### P2.1 Statut

- changement de statut ;
- historique.

### P2.2 Commentaires

- ajout ;
- historique ;
- raisons structurées.

### P2.3 Préférences

- page de consultation ;
- profil initial chargé depuis YAML ;
- versionnement.

## Phase 3 — Carte

### P3.1 Coordonnées manuelles

- champs latitude/longitude ;
- précision ;
- carte.

### P3.2 Géocodage

- adaptateur fournisseur ;
- cache ;
- validation humaine ;
- gestion des localisations approximatives.

## Phase 4 — Ingestion

### P4.1 Import CSV/JSON

- schéma documenté ;
- validation ;
- rapport d'erreurs ;
- idempotence.

### P4.2 Import d'alertes email

- boîte dédiée ;
- n8n ou worker Python ;
- adaptateurs par source ;
- conservation du message brut ou de sa référence ;
- historique de prix.

### P4.3 Cycle de vie d'une annonce

- active ;
- absente ;
- supprimée ;
- republiée.

## Phase 5 — Déduplication

### P5.1 Suggestions déterministes

- URL ;
- identifiant externe ;
- commune ;
- prix ;
- surfaces.

### P5.2 Similarité textuelle

- description ;
- agence ;
- caractéristiques.

### P5.3 Validation de fusion

- interface ;
- journal de fusion ;
- possibilité de corriger.

## Phase 6 — Scoring

### P6.1 Moteur de règles

- score par dimension ;
- confiance ;
- données manquantes ;
- explications.

### P6.2 Page de comparaison

- 2 à 5 biens ;
- différences ;
- principaux risques.

## Phase 7 — IA utile

### P7.1 Extraction structurée

- entrée texte ;
- sortie Pydantic ;
- provenance ;
- validation.

### P7.2 Synthèse

- points forts ;
- faiblesses ;
- questions à poser à l'agence.

### P7.3 Analyse du feedback

- raisons structurées ;
- proposition de préférence ;
- confirmation utilisateur.

## Phase 8 — Agent conversationnel

### P8.1 Outils métier

- rechercher ;
- lire ;
- comparer ;
- expliquer un score ;
- calculer un scénario économique.

### P8.2 Orchestration

- état persistant ;
- validation humaine ;
- journal des appels d'outils.

### P8.3 Requêtes naturelles

Exemples :

- nouveaux biens depuis sept jours ;
- biens dépassant légèrement le budget mais finançables ;
- rejets uniquement liés au prix ;
- meilleures opportunités avec données incomplètes.

## Phase 9 — Enrichissements publics

- Géorisques ;
- cadastre ;
- DVF ;
- temps routier ;
- documents d'urbanisme ;
- données touristiques.

## Règle de priorité

Une phase n'est pas commencée tant que le parcours principal de la phase précédente n'est pas utilisable et testé.
