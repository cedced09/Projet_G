# Instructions pour Codex

## Mission

Construire progressivement l'application `gite-agent` décrite dans les documents du répertoire `docs/`.

Le logiciel est destiné à un utilisateur unique recherchant un domaine dans le Var ou autour de Toulon afin d'y vivre et d'exploiter une activité de gîte rentable.

## Règles de travail

1. Lire tous les documents de contexte avant toute modification importante.
2. Ne pas extrapoler silencieusement les exigences métier. Lorsqu'un choix est nécessaire, adopter l'hypothèse la plus simple et la documenter dans `docs/DECISIONS.md`.
3. Travailler par incréments petits et testables.
4. Ne jamais introduire un framework d'agent avant que le besoin ne soit couvert par des fonctions métier explicites.
5. Ne pas implémenter de scraping d'un portail immobilier sans preuve documentée que cette automatisation est autorisée.
6. Préférer les imports manuels, alertes email officielles, API publiques et sources ouvertes.
7. Ne jamais exposer de secret dans le dépôt. Utiliser `.env` et fournir `.env.example`.
8. Ajouter ou mettre à jour les tests à chaque fonctionnalité.
9. Les décisions de scoring doivent être explicables et traçables.
10. Les modifications automatiques du profil utilisateur doivent toujours nécessiter une confirmation humaine.

## Conventions

### Langue

- Documentation fonctionnelle : français.
- Code, identifiants, noms de tables et commentaires techniques : anglais.
- Texte de l'interface : français.

### Python

- Python 3.14.
- Typage strict sur le code métier.
- Pydantic pour les objets entrants/sortants.
- SQLAlchemy 2 en style moderne.
- Fonctions courtes, responsabilités explicites.
- Pas de logique métier directement dans les pages Streamlit.
- Pas de requêtes SQL construites par concaténation.

### Qualité

Les commandes suivantes doivent réussir :

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

### Architecture

Respecter les couches suivantes :

```text
UI Streamlit
    ↓
Application services
    ↓
Domain logic
    ↓
Repositories
    ↓
PostgreSQL/PostGIS
```

Les dépendances vont vers le domaine, jamais l'inverse.

## Sécurité et conformité

- Ne pas automatiser une authentification destinée à un humain sans autorisation.
- Conserver uniquement les données nécessaires au projet.
- Prévoir la suppression et l'export des données.
- Ne pas considérer un résumé LLM comme une donnée certaine.
- Marquer l'origine de chaque valeur : annonce, saisie utilisateur, source publique ou inférence IA.

## Définition de terminé

Une tâche est terminée lorsque :

- son comportement est couvert par des tests ;
- les migrations de base sont incluses si nécessaire ;
- les erreurs sont gérées ;
- la documentation utile est mise à jour ;
- le scénario nominal est vérifiable localement ;
- aucune donnée de démonstration n'est codée en dur dans le cœur métier.
