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

Le MVP ne scrape pas automatiquement les portails immobiliers. Le flux opérationnel actuel privilégie
les alertes email officielles, puis la validation manuelle des annonces importées. Les formulaires de
création manuelle de biens et d'ajout manuel d'annonces ont été retirés de l'interface pour garder le
cockpit concentré sur le parcours réellement utilisé.

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

La navigation latérale contient trois pages :

- `Tableau de bord` pour importer, enrichir et consulter les annonces ;
- `Carte du Var` pour afficher les annonces localisées sur une carte Leaflet/OpenStreetMap avec
  un lien cliquable par ID `ANN-0001` ;
- `Nettoyage` pour supprimer des entrées de test.

La carte charge les tuiles OpenStreetMap depuis Internet. Elle utilise les coordonnées déjà stockées
sur le bien quand elles existent. Sinon elle tente une localisation par commune à partir d'un
référentiel local limité aux communes du Var déjà connues de l'application. Les annonces sans
commune reconnue restent listées comme non localisées.

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
`Enregistrer comme bien`, présent sur chaque ligne d'annonce, crée un bien canonique depuis
l'annonce sélectionnée et la rattache à ce bien.

Pour les alertes SeLoger, l'import exploite la structure HTML de la carte annonce et extrait quand
ils sont présents : prix, nombre de pièces, surface habitable, surface de terrain, ville, nombre de
chambres et présence d'une piscine. Le lien affiché dans l'interface est cliquable. L'application ne
visite pas la page de l'annonce.

Pour enrichir une annonce depuis sa page web sans téléchargement automatique :

1. ouvrir le lien de l'annonce dans le navigateur ;
2. enregistrer la page en `Page web complète` depuis Chrome ;
3. laisser le fichier `.html` et le dossier associé au même endroit ;
4. dans Streamlit, ouvrir le menu `HTML` de l'annonce ;
5. cliquer sur `Choisir et importer le HTML` ;
6. sélectionner le fichier `.html` dans la boîte de dialogue.

L'application lit automatiquement le dossier voisin créé par Chrome, par exemple `annonce_fichiers`
ou `annonce_files`, et archive ses fichiers avec le HTML.

`HTML_IMPORT_DIRECTORIES` sert uniquement à proposer un dossier de départ à la boîte de dialogue.
En local Windows, `~/Downloads` est inclus par défaut. Si l'application tourne dans Docker sans
interface graphique, cette boîte de dialogue peut ne pas être disponible ; il faudra alors exécuter
l'app localement ou ajouter un autre flux d'import adapté au serveur.

Le HTML importé est sauvegardé dans PostgreSQL, dans une table dédiée. Ainsi, tous les utilisateurs
qui accèdent à la même application et à la même base voient les mêmes archives HTML, même depuis un
autre poste. L'interface affiche un badge `HTML enrichi` lorsque le contenu a été sauvegardé et
analysé.

L'archive conserve le document HTML fourni ou téléchargé. Lors d'un import local, le répertoire
associé créé par le navigateur est récupéré automatiquement : images, CSS, JavaScript et autres
fichiers liés sont alors stockés dans PostgreSQL avec l'archive HTML. À l'affichage, l'application
tente de réintégrer ces fichiers dans le HTML archivé.

Dans la liste des biens enregistrés, deux boutons sont disponibles :

- `Site web` ouvre l'annonce originale ;
- `Sauvegarde` ouvre dans le navigateur une prévisualisation locale générée depuis le HTML et les
  fichiers associés stockés en base.

Le bouton `Télécharger depuis la source` est disponible dans le menu `HTML`, mais il ne fonctionne
que pour les domaines explicitement autorisés dans `.env` :

```env
HTML_AUTO_DOWNLOAD_ALLOWED_DOMAINS=source-autorisee.example
```

Laisser cette valeur vide désactive le téléchargement automatique et conserve le flux manuel par
upload HTML.

### Nettoyage des données de test

La navigation Streamlit contient une page `Nettoyage`. Elle permet de supprimer :

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

Le parcours principal permet d'importer des alertes email, d'enrichir une annonce par HTML sauvegardé,
de créer un bien depuis une annonce validée, puis d'afficher la liste persistée.
