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

## ADR-012 — Extraction structurée depuis les cartes HTML des alertes

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

Les alertes SeLoger contiennent une version texte avec de nombreux liens de tracking et une version
HTML structurée où chaque carte annonce porte des ancres nommées comme `adimage1_1`, `adprice1_1`,
`adtype1_1`, `adcriteria1_1` et `adlocation1_1`.

**Décision**

L'import email privilégie les cartes HTML structurées pour identifier l'URL et extraire les
caractéristiques principales visibles dans le mail. Aucune visite automatique de la page annonce
n'est effectuée.

**Conséquences**

L'extraction est plus précise pour SeLoger et reste conforme à l'approche sans scraping. Les champs
absents du mail restent inconnus jusqu'à saisie manuelle ou import autorisé plus riche.

## ADR-013 — Enrichissement par HTML fourni manuellement

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

Les pages annonce contiennent davantage d'informations que les emails, mais les CGU SeLoger
interdisent les dispositifs automatisés de consultation ou d'extraction du site.

**Décision**

L'application ne télécharge pas automatiquement les pages SeLoger. L'utilisateur peut ouvrir une
annonce dans son navigateur, enregistrer le HTML, puis fournir ce fichier à l'application pour un
parsing local.

**Conséquences**

L'enrichissement reste piloté par une action humaine explicite et évite l'accès automatisé au
portail. La qualité d'extraction dépendra du HTML fourni et pourra être améliorée source par source.

## ADR-014 — Fiche bien synchronisée depuis l'annonce validée

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

Une annonce importée puis enrichie depuis un HTML fourni manuellement contient parfois plus
d'informations exploitables que la fiche bien synthétique.

**Décision**

Lorsqu'une annonce est enregistrée comme bien ou enrichie alors qu'elle est déjà rattachée, les
champs descriptifs principaux sont copiés sur le bien : titre, commune, prix, pièces, surfaces,
chambres et piscine. Le titre de l'annonce et la source restent deux champs distincts.

**Conséquences**

La liste des biens affiche une fiche exploitable sans ouvrir chaque annonce. Si plusieurs annonces
sont rattachées au même bien, la dernière annonce enrichie peut remplacer ces champs de synthèse ;
une règle de fusion plus fine sera nécessaire lorsque la déduplication deviendra plus avancée.

## ADR-015 — Carte Leaflet avec localisation contrôlée

**Statut :** accepté

**Date :** 2026-07-20

**Contexte**

La carte doit être lisible et navigable comme une vraie carte. Le projet n'intègre toutefois pas
encore de fournisseur de géocodage et ne doit pas inventer de coordonnées.

**Décision**

La page cartographique utilise Leaflet et les tuiles OpenStreetMap chargées depuis Internet. Elle
utilise d'abord les coordonnées explicitement stockées sur les biens. À défaut, elle s'appuie sur un
petit référentiel local de communes du Var maintenu dans le code. Les annonces dont la commune n'est
pas reconnue sont affichées dans une liste séparée.

**Conséquences**

La carte est une vraie carte interactive avec zoom et déplacement, et des marqueurs cliquables par
ID d'annonce. Elle nécessite un accès Internet pour afficher le fond de carte. Le référentiel
communal devra être remplacé ou complété par un géocodage contrôlé lorsque cette fonctionnalité sera
priorisée.

## ADR-016 — Archivage local des HTML fournis manuellement

**Statut :** remplacé par ADR-017

**Date :** 2026-07-20

**Contexte**

Les HTML de pages annonce fournis manuellement peuvent servir à enrichir immédiatement les données,
mais aussi à revenir sur l'extraction ou à alimenter plus tard un traitement IA contrôlé.

**Décision**

Lorsqu'un HTML est analysé, l'application sauvegarde le fichier côté serveur dans
`HTML_STORAGE_DIR`, stocke le chemin, la date de sauvegarde et une empreinte SHA-256 sur l'annonce.
Le dossier `./data` est monté dans le conteneur Docker pour persister ces fichiers localement.

**Conséquences**

L'interface peut afficher un statut fiable `HTML enrichi` et permettre de récupérer le fichier. Les
fichiers HTML ne sont pas versionnés dans Git. Un futur traitement IA pourra consommer ces archives
sans revisiter automatiquement les portails.

## ADR-017 — Archivage PostgreSQL des HTML fournis manuellement

**Statut :** accepté

**Date :** 2026-07-22

**Contexte**

Les archives HTML doivent être accessibles à tous les utilisateurs de l'application, y compris si le
conteneur Docker est déployé sur une autre machine. Le stockage dans un dossier local du poste de
développement ne garantit pas cet accès partagé.

**Décision**

Les HTML fournis manuellement sont stockés dans PostgreSQL dans la table
`listing_html_archives`, liée à `listings`. Les fichiers associés au HTML, par exemple images, CSS
ou JavaScript issus du dossier créé par le navigateur, sont stockés dans
`listing_html_archive_assets`. L'annonce conserve la date de sauvegarde et l'empreinte SHA-256 pour
afficher le statut et tracer le contenu archivé. Le contenu HTML est lu depuis la base pour
l'affichage et le téléchargement dans l'interface.

**Conséquences**

La sauvegarde et la restauration de la base couvrent aussi les HTML et leurs fichiers associés. Tous
les utilisateurs connectés à la même base accèdent aux mêmes contenus. Cette solution reste simple
pour le volume attendu ; un stockage objet pourra être introduit plus tard si les archives deviennent
volumineuses.

## ADR-018 — Filtrage des emails promotionnels sans caractéristiques d'annonce

**Statut :** accepté

**Date :** 2026-07-22

**Contexte**

Certaines communications SeLoger utilisent une structure HTML proche des alertes, mais correspondent
à des contenus promotionnels ou éditoriaux plutôt qu'à des annonces immobilières réelles.

**Décision**

L'ingestion ne crée une annonce que si la carte email contient au moins une caractéristique
immobilière structurée : prix, nombre de pièces, surface habitable, surface de terrain ou nombre de
chambres. Les liens sans ces caractéristiques sont ignorés, même si leur domaine est autorisé.

**Conséquences**

Les publicités et contenus génériques ne polluent plus la base. Une annonce réelle très pauvre en
métadonnées pourrait être ignorée ; ce compromis est accepté pour conserver une base propre.

## ADR-019 — Téléchargement HTML direct limité aux domaines autorisés

**Statut :** accepté

**Date :** 2026-07-22

**Contexte**

Le téléchargement direct d'une page source est plus ergonomique que l'upload manuel, mais il peut
constituer une automatisation d'accès à un portail immobilier.

**Décision**

Le bouton de téléchargement direct est présent dans l'interface, mais il n'est actif que pour les
domaines explicitement listés dans `HTML_AUTO_DOWNLOAD_ALLOWED_DOMAINS`. Par défaut, cette liste est
vide. Pour les autres domaines, l'utilisateur conserve le flux manuel d'upload HTML.

**Conséquences**

Les sources autorisées peuvent être archivées en un clic dans PostgreSQL. Les portails non autorisés
ne sont pas téléchargés automatiquement, ce qui préserve le cadre de conformité du projet.

## ADR-020 — Import local des exports Chrome complets

**Statut :** accepté

**Date :** 2026-07-22

**Contexte**

Lorsqu'une page est enregistrée manuellement depuis Chrome en mode page complète, le navigateur crée
un fichier HTML et un répertoire voisin contenant les ressources associées. L'upload web classique
ne fournit pas à Streamlit le chemin local complet du fichier sélectionné, donc l'application ne peut
pas deviner automatiquement le répertoire frère depuis un simple upload navigateur.

**Décision**

L'interface propose un seul bouton `Choisir et importer le HTML`, qui ouvre une boîte de dialogue
fichier native sur la machine qui exécute Streamlit. L'utilisateur sélectionne le fichier HTML
principal. Comme le chemin réel du fichier est alors connu côté serveur, l'application lit
automatiquement les répertoires frères usuels, comme `nom_fichiers` ou `nom_files`, puis archive le
HTML et les ressources en PostgreSQL. `HTML_IMPORT_DIRECTORIES` sert seulement à proposer un dossier
initial à la boîte de dialogue.

**Conséquences**

L'enrichissement manuel devient beaucoup plus rapide lorsque l'application tourne sur le poste qui
contient l'export Chrome. En Docker sans interface graphique ou sur un serveur distant, cette boîte
de dialogue peut ne pas être disponible et un flux d'import dédié devra être ajouté. Un simple upload
navigateur du fichier HTML ne suffit pas pour découvrir automatiquement le dossier frère, car le
navigateur ne transmet pas ce chemin à Streamlit. Ce choix ne visite pas automatiquement le portail
immobilier et reste compatible avec l'approche d'archivage manuel.

## ADR-021 — Retrait des formulaires de création manuelle

**Statut :** accepté

**Date :** 2026-07-22

**Contexte**

Le parcours réellement utilisé consiste à importer des annonces depuis les alertes email, enrichir
les annonces pertinentes avec le HTML sauvegardé, puis créer un bien canonique depuis une annonce
validée. Les formulaires de création manuelle d'un bien et d'ajout manuel d'une annonce à un bien
alourdissent le tableau de bord sans être utilisés.

**Décision**

Retirer ces deux formulaires de l'interface Streamlit. Les services applicatifs et repositories
conservent les méthodes de création, car elles restent nécessaires au flux `Créer bien` depuis une
annonce importée et aux tests métier.

**Conséquences**

Le tableau de bord devient plus direct et centré sur le flux quotidien. Si un besoin ponctuel de
saisie manuelle revient, il sera traité comme un flux dédié plutôt que comme un formulaire permanent
sur la page principale.
