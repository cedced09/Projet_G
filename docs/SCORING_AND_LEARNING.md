# Scoring et apprentissage

## Objectif

Prioriser les biens sans masquer le raisonnement.

Le scoring initial est déterministe. L'apprentissage statistique vient ensuite.

## Profil initial

```yaml
financial:
  available_equity_eur: 3000000
  additional_debt_possible: true
  target_net_income_after_tax_eur_per_year: 70000

geography:
  preferred_department: "83"
  reference_city: "Toulon"
  maximum_target_drive_time_minutes: 45
  allow_outside_department: true

property:
  preferred_min_land_area_m2: 5000
  renovation_accepted: true
  planning_permission_risk_tolerance: low

operations:
  owner_occupied: true
  horse_activity_allowed: false
  wine_activity_preferred: false
  complementary_activities_welcome: true
  seasonal_downtime_preferred: true
```

## Dimensions initiales

| Dimension | Poids |
|---|---:|
| viabilité économique | 30 |
| localisation | 15 |
| potentiel d'hébergement | 15 |
| qualité de vie privée | 10 |
| terrain et dépendances | 10 |
| activité complémentaire | 10 |
| travaux et urbanisme | 5 |
| saisonnalité et charge | 5 |

Total : 100.

## Contraintes fortes

Une contrainte forte ne doit pas nécessairement supprimer le bien de l'affichage. Elle doit :

- produire un avertissement explicite ;
- réduire fortement le classement ;
- permettre à l'utilisateur de revoir manuellement la décision.

Contraintes initiales :

- activité équestre centrale ;
- modèle principalement viticole ;
- terrain très inférieur à 5 000 m² ;
- impossibilité manifeste d'habiter sur place ;
- risque urbanistique déterminant et non sécurisé.

## Structure d'un score

```json
{
  "total": 74,
  "model_version": "rules-v1",
  "dimensions": {
    "economic_viability": {
      "score": 20,
      "max": 30,
      "reasons": [
        "activité existante",
        "chiffre d'affaires non communiqué"
      ]
    }
  },
  "warnings": [
    "localisation approximative",
    "revenu net non démontré"
  ],
  "missing_information": [
    "EBE",
    "taxe foncière",
    "coût énergétique",
    "capacité réelle"
  ]
}
```

## Données inconnues

Une valeur inconnue ne doit pas être traitée comme mauvaise.

Séparer :

- pénalité liée à un mauvais critère ;
- réduction de confiance liée à une information manquante.

Afficher deux indicateurs :

- score d'adéquation ;
- niveau de confiance.

## Commentaires

Un LLM pourra ultérieurement transformer un commentaire libre en raisons structurées. Cette transformation reste une proposition.

Exemple :

```text
"Très beau, mais trop proche des voisins et aucune séparation avec les clients."
```

Proposition :

```json
{
  "decision": "rejected",
  "reasons": [
    {
      "category": "neighborhood",
      "sentiment": "negative",
      "importance": 4
    },
    {
      "category": "owner_privacy",
      "sentiment": "negative",
      "importance": 5
    }
  ],
  "preference_proposals": [
    {
      "key": "minimum_neighbor_distance",
      "action": "create_soft_preference"
    },
    {
      "key": "owner_area_separated",
      "action": "increase_weight"
    }
  ]
}
```

## Apprentissage progressif

### Étape 1 — Règles explicites

Calcul déterministe à partir du profil.

### Étape 2 — Ajustement confirmé des poids

Le système propose des modifications de préférence à partir des commentaires.

### Étape 3 — Comparaison par paires

L'utilisateur choisit entre deux biens. Ces choix constituent des données d'entraînement de meilleure qualité que les seules notes.

### Étape 4 — Modèle de ranking

Envisager seulement après un volume suffisant de décisions :

- régression logistique ;
- gradient boosting ;
- pairwise ranking.

Le modèle doit rester secondaire au score explicite.

## Mesures de qualité

Suivre :

- proportion des favoris dans le top 10 ;
- proportion des rejets évidents dans le top 10 ;
- nombre de biens utiles découverts ;
- taux de modification manuelle des extractions IA ;
- précision des propositions de doublons ;
- stabilité du classement entre versions.
