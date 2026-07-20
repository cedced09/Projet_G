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

## ADR-007 — Python 3.14 pour le développement local

**Statut :** accepté

**Date :** 2026-07-17

**Contexte**

Le poste de développement disponible fournit Python 3.14, tandis que Python 3.12 n'est pas
installé.

**Décision**

Le projet cible désormais Python 3.14 dans la configuration, la documentation et l'image Docker.

**Conséquences**

Le développement local est aligné avec l'environnement réel. Si un déploiement impose une version
plus ancienne, il faudra vérifier explicitement la compatibilité avant de revenir en arrière.

## ADR-008 — Ingestion email sans visite automatique des portails

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

Les alertes email officielles sont une source autorisée et stable pour détecter de nouvelles
annonces. Les règles du projet interdisent en revanche de scraper un portail immobilier sans preuve
documentée que cette automatisation est autorisée.

**Décision**

L'ingestion email se limite à lire la boîte IMAP configurée, extraire les URL contenues dans les
messages, et créer ou mettre à jour des `Listing` non rattachés. L'application ne visite pas les URL
extraites et ne tente pas d'extraire le contenu des portails.

**Conséquences**

Le système peut détecter les nouvelles alertes et les historiser sans dépendre des portails. Les
données détaillées de chaque annonce restent à saisir manuellement ou à importer ultérieurement via
une source explicitement autorisée.

## ADR-009 — Annonces orphelines avant déduplication

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

Une alerte email peut contenir une URL de nouvelle annonce sans que le bien canonique associé soit
encore connu ou validé.

**Décision**

`listings.property_id` devient nullable. Les annonces importées par email sont créées sans bien
rattaché, puis affichées séparément dans l'interface.

**Conséquences**

L'ingestion reste fidèle au modèle cible et évite de créer automatiquement des biens canoniques
incertains. Une future tranche devra ajouter le rattachement manuel ou les suggestions de
déduplication.

## ADR-010 — Identifiants d'annonces séquentiels

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

Les UUID sont fiables techniquement mais peu lisibles dans l'interface, surtout lorsque plusieurs
annonces ont le même titre.

**Décision**

Chaque annonce reçoit un identifiant public séquentiel `ANN-0001`, `ANN-0002`, etc. L'UUID reste la
clé primaire technique.

**Conséquences**

L'interface est plus lisible pendant les tests et l'usage quotidien. La génération est suffisante
pour un utilisateur unique, mais devra être renforcée si plusieurs imports concurrents sont ajoutés.

## ADR-011 — Limitation des liens email par nombre annoncé

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

Les alertes email peuvent contenir de nombreux liens de tracking, même lorsqu'elles annoncent un
seul bien.

**Décision**

Lorsque le sujet indique un nombre d'annonces, l'import conserve au maximum ce nombre de liens
autorisés. Sinon il applique `EMAIL_MAX_LISTINGS_PER_MESSAGE`.

**Conséquences**

Les faux positifs diminuent sans visiter les portails immobiliers. Cette heuristique reste simple et
devra être spécialisée par source si les alertes fournissent une structure exploitable.
