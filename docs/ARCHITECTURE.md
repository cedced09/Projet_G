# Architecture technique

## Vue d'ensemble cible

```text
Alertes officielles / import manuel
                │
                ▼
        Ingestion adapters
                │
                ▼
     Normalization and validation
                │
                ▼
 Application services and domain
                │
                ▼
      PostgreSQL + PostGIS
                │
        ┌───────┴─────────┐
        ▼                 ▼
 Streamlit UI       AI services
                         │
                         ▼
                  Agent orchestration
```

## Architecture du dépôt cible

```text
gite-agent/
├── app/
│   ├── main.py
│   ├── ui/
│   │   ├── pages/
│   │   └── components/
│   ├── application/
│   │   ├── property_service.py
│   │   ├── listing_service.py
│   │   ├── feedback_service.py
│   │   └── search_service.py
│   ├── domain/
│   │   ├── entities.py
│   │   ├── enums.py
│   │   ├── value_objects.py
│   │   ├── scoring.py
│   │   └── deduplication.py
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   │   └── repositories/
│   │   ├── ingestion/
│   │   ├── geocoding/
│   │   └── ai/
│   └── settings.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
├── docs/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

## Principes

### Bien canonique et annonce

Un `Property` représente le bien immobilier réel.

Un `Listing` représente une annonce publiée sur une source donnée.

Un bien peut avoir plusieurs annonces.

### Provenance

Chaque donnée importante doit porter une provenance :

- `listing`
- `user`
- `public_data`
- `ai_inference`
- `derived`

Une donnée inférée par IA ne doit jamais remplacer silencieusement une donnée explicite.

### Argent

Stocker les valeurs monétaires en centimes d'euro avec un entier.

Exemple :

```text
3 000 000,00 € → 300000000
```

### Dates

Utiliser des timestamps UTC en base.

Champs essentiels d'une annonce :

- `published_at` : date publiée par la source, potentiellement absente ;
- `first_seen_at` : première observation par le système ;
- `last_seen_at` : dernière observation ;
- `removed_at` : date de disparition connue, potentiellement absente.

### Cartographie

PostGIS est prévu dès le départ, mais les coordonnées peuvent rester absentes.

Prévoir :

- longitude ;
- latitude ;
- niveau de précision ;
- texte d'origine ;
- fournisseur de géocodage ;
- date du géocodage.

### Ingestion

Une ingestion doit être idempotente :

- réimporter la même annonce ne crée pas de doublon ;
- `last_seen_at` est mis à jour ;
- un changement de prix crée une entrée d'historique.

### IA

Les services IA sont des adaptateurs remplaçables.

Le domaine ne dépend pas d'un fournisseur de modèle particulier.

Toute sortie IA utilisée par l'application doit être validée par un schéma Pydantic.

## Déploiement initial

Docker Compose avec :

- `app`
- `db`

Services ultérieurs :

- `n8n`
- worker asynchrone ;
- reverse proxy ;
- stockage objet si des images sont conservées.

## Observabilité minimale

Dès le MVP :

- logs structurés ;
- journal des erreurs d'ingestion ;
- identifiant de corrélation pour une exécution d'import ;
- état des migrations ;
- page simple de santé.
