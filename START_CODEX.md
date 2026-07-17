# Prompt de démarrage pour Codex

Copier le prompt ci-dessous dans Codex après avoir placé ce pack à la racine du nouveau dépôt.

---

Lis intégralement `AGENTS.md` puis tous les fichiers de `docs/`.

Commence uniquement par la phase 0 et la première tranche verticale du MVP :

1. initialise un projet Python 3.12 ;
2. ajoute la structure de dossiers décrite dans `docs/ARCHITECTURE.md` ;
3. configure `pyproject.toml`, Ruff, mypy et pytest ;
4. crée un `docker-compose.yml` avec PostgreSQL et PostGIS ;
5. ajoute `.env.example` ;
6. implémente le modèle minimal `Property` + `Listing` avec SQLAlchemy et Alembic ;
7. implémente une page Streamlit permettant :
   - de créer manuellement un bien ;
   - d'ajouter une annonce associée ;
   - d'afficher la liste enregistrée ;
8. ajoute les tests unitaires et d'intégration nécessaires ;
9. documente les commandes de lancement dans le README principal du dépôt.

Contraintes :

- n'implémente pas encore de LLM, n8n, LangGraph, géocodage ou scraping ;
- sépare l'interface, les services applicatifs, le domaine et les repositories ;
- utilise des valeurs monétaires en centimes d'euro ;
- conserve `source_url`, `first_seen_at` et `last_seen_at` pour chaque annonce ;
- ajoute toute décision non spécifiée dans `docs/DECISIONS.md`.

Avant de coder, présente un plan de fichiers concis. Puis exécute le plan sans demander de confirmation sauf blocage objectif.
