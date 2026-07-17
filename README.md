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

- Python 3.12
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

- Python 3.12
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

### Application Streamlit

```bash
streamlit run app/main.py
```

Ou avec Docker Compose :

```bash
docker compose up --build app
```

### Qualité et tests

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

Le premier incrément permet de créer manuellement un bien, de rattacher une annonce avec
`source_url`, `first_seen_at` et `last_seen_at`, puis d'afficher la liste persistée.
