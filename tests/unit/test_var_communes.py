from app.infrastructure.geocoding.var_communes import find_var_commune_coordinates


def test_find_var_commune_coordinates_normalizes_accents_and_case() -> None:
    coordinates = find_var_commune_coordinates("Collobrières")

    assert coordinates is not None
    assert coordinates.latitude == 43.2373
    assert coordinates.longitude == 6.3094


def test_find_var_commune_coordinates_normalizes_hyphenated_city() -> None:
    coordinates = find_var_commune_coordinates("Le Plan-de-la-Tour")

    assert coordinates is not None
    assert coordinates.latitude == 43.3396
    assert coordinates.longitude == 6.5489


def test_find_var_commune_coordinates_returns_none_for_unknown_city() -> None:
    assert find_var_commune_coordinates("Ville inconnue") is None
