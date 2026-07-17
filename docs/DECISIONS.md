# Journal des décisions d'architecture

Utiliser le format suivant pour toute décision structurante.

## ADR-XXX — Titre

**Statut :** proposé / accepté / remplacé

**Date :** YYYY-MM-DD

**Contexte**

Décrire le problème.

**Décision**

Décrire le choix.

**Conséquences**

Décrire les avantages, limites et travaux futurs.

---

## ADR-001 — Ingestion initiale sans scraping

**Statut :** accepté

**Date :** 2026-07-17

**Contexte**

Les portails immobiliers ont des interfaces, CGU et protections susceptibles de rendre le scraping fragile ou interdit. Le projet doit être maintenable et ne pas dépendre d'un contournement technique.

**Décision**

Le MVP utilise la création manuelle. Les phases suivantes privilégient les alertes email officielles, les API publiques et les imports autorisés.

**Conséquences**

L'exhaustivité initiale est moindre, mais le système reste robuste et juridiquement plus défendable.

## ADR-002 — Monolithe modulaire

**Statut :** accepté

**Date :** 2026-07-17

**Contexte**

Le produit est utilisé par une personne et doit d'abord servir de support d'apprentissage.

**Décision**

Construire un monolithe Python modulaire avec Streamlit et PostgreSQL.

**Conséquences**

Déploiement simple, faible charge opérationnelle et possibilité d'extraire ultérieurement certains services.

## ADR-003 — PostgreSQL et PostGIS dès le départ

**Statut :** accepté

**Date :** 2026-07-17

**Contexte**

La carte, les distances et les rapprochements géographiques sont centraux.

**Décision**

Utiliser PostgreSQL avec l'extension PostGIS, même si le premier incrément n'exploite pas toutes les capacités spatiales.

**Conséquences**

Le développement initial est légèrement plus lourd qu'avec SQLite, mais évite une migration structurante ultérieure.

## ADR-004 — Pas de framework d'agent dans le MVP

**Statut :** accepté

**Date :** 2026-07-17

**Contexte**

La valeur initiale provient de la centralisation, de l'historisation et du scoring explicable.

**Décision**

LangGraph n'est ajouté qu'après l'existence d'outils métier déterministes et testés.

**Conséquences**

Le projet permet de distinguer clairement automatisation, LLM et agent.

## ADR-005 — Tests de repositories sur SQLite en mémoire

**Statut :** accepté

**Date :** 2026-07-17

**Contexte**

Le premier incrément doit rester rapide à exécuter localement tout en validant les services,
repositories et modèles SQLAlchemy.

**Décision**

Les tests d'intégration automatisés utilisent SQLite en mémoire pour vérifier le flux métier
minimal. L'environnement applicatif réel reste PostgreSQL/PostGIS via Docker Compose et Alembic.

**Conséquences**

Les tests sont rapides et sans dépendance Docker. Les comportements spécifiques PostgreSQL/PostGIS
devront recevoir des tests dédiés lorsqu'ils seront utilisés par le domaine.

## ADR-006 — Unicité initiale des annonces par URL source

**Statut :** accepté

**Date :** 2026-07-17

**Contexte**

Les annonces créées manuellement peuvent ne pas fournir d'identifiant externe stable.

**Décision**

La première tranche impose l'unicité de `source_url`. Une contrainte partielle unique sur
`(source, external_id)` est aussi créée lorsque `external_id` existe.

**Conséquences**

La création manuelle reste simple et évite les doublons évidents. Une normalisation plus avancée
des URL pourra être ajoutée avec l'ingestion.
