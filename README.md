# Gîte Agent — Context Pack

Ce dépôt contient le contexte de départ pour construire, avec Codex dans VS Code, une application personnelle de veille et d'aide à la décision pour l'achat d'un gîte ou domaine touristique.

## Finalité

L'application doit centraliser les biens provenant de plusieurs sources, les afficher sur une carte, conserver l'historique des annonces, permettre leur évaluation manuelle et apprendre progressivement des retours de l'utilisateur.

Le projet est aussi un support d'apprentissage pratique de :

- Python applicatif ;
- PostgreSQL/PostGIS ;
- Streamlit ;
- ingestion automatisée ;
- sorties structurées de LLM ;
- systèmes de scoring explicables ;
- orchestration d'agents IA ;
- tests et déploiement Docker.

## Ordre de lecture

1. `AGENTS.md`
2. `docs/PRODUCT_CONTEXT.md`
3. `docs/MVP_SPEC.md`
4. `docs/ARCHITECTURE.md`
5. `docs/DATA_MODEL.md`
6. `docs/SCORING_AND_LEARNING.md`
7. `docs/BACKLOG.md`
8. `START_CODEX.md`

## Périmètre initial

Le MVP ne scrape pas automatiquement les portails immobiliers. Les annonces entrent par :

1. saisie manuelle ;
2. import d'URL avec métadonnées saisies ou autorisées ;
3. alertes email officielles, dans une phase suivante.

## Stack cible

- Python 3.14
- Streamlit
- PostgreSQL 16
- PostGIS
- SQLAlchemy 2
- Alembic
- Pydantic 2
- psycopg 3
- pytest
- Ruff
- mypy
- Docker Compose

n8n et LangGraph seront introduits après validation du cœur métier.

## Principe directeur

Construire d'abord un outil déterministe et utile. Ajouter l'IA uniquement là où elle apporte une valeur mesurable : extraction de texte, synthèse, classement assisté, détection de doublons et interprétation des commentaires.

## Développement local

### Prérequis

- Python 3.14
- Docker Compose

### Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
copy .env.example .env
```

### Base PostgreSQL/PostGIS

```bash
docker compose up -d db
alembic upgrade head
```

Si Docker n'est pas disponible sur le PC, installer PostgreSQL 16 et PostGIS localement,
créer une base `gite_agent`, puis adapter `DATABASE_URL` dans `.env` avant de lancer
`alembic upgrade head`.

### Application Streamlit

```bash
streamlit run app/main.py
```

Ou avec Docker Compose :

```bash
docker compose up --build app
```

### Ingestion des alertes email

Créer une adresse email dédiée aux alertes immobilières, puis configurer les paramètres IMAP dans
`.env` :

```env
EMAIL_IMAP_HOST=imap.example.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USERNAME=alertes@example.com
EMAIL_IMAP_PASSWORD=mot-de-passe-ou-mot-de-passe-application
EMAIL_IMAP_FOLDER=INBOX
EMAIL_IMAP_SEARCH=UNSEEN
EMAIL_IMPORT_LIMIT=25
EMAIL_MAX_LISTINGS_PER_MESSAGE=5
EMAIL_ALLOWED_SENDER_DOMAINS=
EMAIL_ALLOWED_URL_DOMAINS=seloger.com,bellesdemeures.com,espaces-atypiques.com,cessionpme.com
```

Ensuite :

```bash
alembic upgrade head
streamlit run app/main.py
```

Dans l'application, cliquer sur `Importer les nouvelles alertes email`.

L'import lit les emails correspondant à `EMAIL_IMAP_SEARCH`, extrait les URL présentes dans le
message, puis crée des annonces non rattachées à un bien canonique. Il ne visite pas les portails
immobiliers et ne contourne aucune restriction de site. Une URL déjà connue n'est pas dupliquée :
sa date de dernière observation est mise à jour.

Les emails ne créent une annonce que si au moins une URL extraite passe le filtre
`EMAIL_ALLOWED_URL_DOMAINS`. Laisser ce filtre vide importe toutes les URL trouvées, y compris les
liens techniques ou de sécurité. Pour éviter les faux positifs, renseigner les domaines des portails
autorisés.

Quand le sujet de l'email indique explicitement un nombre d'annonces, par exemple
`1 nouvelle annonce`, l'import limite le nombre de liens conservés à ce nombre. Cela évite de créer
une annonce pour chaque lien de tracking présent dans le message.

Les annonces importées restent d'abord non rattachées. Le bouton
`Enregistrer cette annonce comme bien` crée un bien canonique depuis l'annonce sélectionnée et la
rattache à ce bien.

### Nettoyage des données de test

La page Streamlit contient une section `Nettoyage de la base`. Elle permet de supprimer :

- une annonce email non rattachée ;
- un bien complet avec ses annonces rattachées.

Chaque suppression demande de saisir `SUPPRIMER`.

### Qualité et tests

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

Le premier incrément permet de créer manuellement un bien, de rattacher une annonce avec
`source_url`, `first_seen_at` et `last_seen_at`, puis d'afficher la liste persistée.
