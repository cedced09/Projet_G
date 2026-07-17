# Modèle de données

## Entités principales

## `properties`

Représente un bien canonique.

Champs recommandés :

| Champ | Type | Remarque |
|---|---|---|
| id | UUID | clé primaire |
| internal_title | text | titre choisi ou généré |
| property_type | enum | domaine, maison, hôtel, fonds, etc. |
| status | enum | statut utilisateur |
| description | text nullable | synthèse canonique |
| price_cents | bigint nullable | prix de référence |
| living_area_m2 | numeric nullable | |
| land_area_m2 | numeric nullable | |
| bedroom_count | integer nullable | |
| accommodation_unit_count | integer nullable | |
| owner_area_separated | boolean nullable | |
| municipality | text nullable | |
| postal_code | text nullable | |
| department_code | text nullable | |
| latitude | double nullable | |
| longitude | double nullable | |
| location_precision | enum nullable | |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| archived_at | timestamptz nullable | |

## `listings`

Représente une annonce source.

| Champ | Type | Remarque |
|---|---|---|
| id | UUID | |
| property_id | UUID nullable | absent avant déduplication |
| source | enum/text | |
| external_id | text nullable | identifiant source |
| source_url | text | normalisée |
| title | text | |
| raw_location | text nullable | |
| description | text nullable | |
| current_price_cents | bigint nullable | |
| published_at | timestamptz nullable | |
| first_seen_at | timestamptz | |
| last_seen_at | timestamptz | |
| removed_at | timestamptz nullable | |
| raw_payload | jsonb nullable | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Contraintes :

- unicité recommandée sur `(source, external_id)` lorsque `external_id` existe ;
- sinon unicité sur l'URL normalisée avec stratégie documentée.

## `listing_price_history`

| Champ | Type |
|---|---|
| id | UUID |
| listing_id | UUID |
| price_cents | bigint |
| observed_at | timestamptz |
| source | text |

## `property_feedback`

| Champ | Type |
|---|---|
| id | UUID |
| property_id | UUID |
| decision | enum nullable |
| comment | text nullable |
| created_at | timestamptz |
| supersedes_feedback_id | UUID nullable |

## `feedback_reasons`

Raisons structurées rattachées à un feedback.

| Champ | Type |
|---|---|
| id | UUID |
| feedback_id | UUID |
| category | enum |
| sentiment | enum |
| importance | integer |
| note | text nullable |

`sentiment` :

- `positive`
- `negative`
- `neutral`
- `unknown`

## `preferences`

Préférences actives et explicites.

| Champ | Type |
|---|---|
| id | UUID |
| key | text |
| value | jsonb |
| weight | numeric nullable |
| hard_constraint | boolean |
| active | boolean |
| source | enum |
| created_at | timestamptz |
| updated_at | timestamptz |

## `preference_change_proposals`

Proposition générée à partir d'un feedback.

| Champ | Type |
|---|---|
| id | UUID |
| feedback_id | UUID |
| preference_key | text |
| proposed_value | jsonb |
| proposed_weight_delta | numeric nullable |
| rationale | text |
| status | enum |
| created_at | timestamptz |
| reviewed_at | timestamptz nullable |

Statuts :

- `pending`
- `accepted`
- `rejected`
- `modified`

## `property_scores`

Conserver les résultats de score pour audit.

| Champ | Type |
|---|---|
| id | UUID |
| property_id | UUID |
| total_score | numeric |
| model_version | text |
| details | jsonb |
| calculated_at | timestamptz |

## `ingestion_runs`

| Champ | Type |
|---|---|
| id | UUID |
| source | text |
| started_at | timestamptz |
| finished_at | timestamptz nullable |
| status | enum |
| items_seen | integer |
| items_created | integer |
| items_updated | integer |
| error_count | integer |
| error_details | jsonb nullable |

## `property_merge_events`

Trace les décisions de fusion de doublons.

| Champ | Type |
|---|---|
| id | UUID |
| surviving_property_id | UUID |
| merged_property_id | UUID |
| confidence | numeric nullable |
| reason | text |
| decided_by | enum |
| created_at | timestamptz |

## Enums initiaux

### `property_type`

- `house`
- `estate`
- `bastide`
- `mas`
- `castle`
- `hotel`
- `guest_house`
- `gite_business`
- `business_assets`
- `land`
- `other`

### `location_precision`

- `exact_address`
- `street`
- `locality`
- `municipality`
- `postal_code`
- `area`
- `department`
- `unknown`

### `data_origin`

- `listing`
- `user`
- `public_data`
- `ai_inference`
- `derived`

## Identité et doublons

Ne jamais considérer deux annonces comme identiques sur la seule base du titre.

La fusion automatique est interdite dans les premières versions. Le système propose, l'utilisateur confirme.
