import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


VAR_COMMUNE_COORDINATES: dict[str, Coordinates] = {
    "AUPS": Coordinates(43.6289, 6.2242),
    "BANDOL": Coordinates(43.1364, 5.7533),
    "BORMES LES MIMOSAS": Coordinates(43.1500, 6.3410),
    "BRIGNOLES": Coordinates(43.4058, 6.0617),
    "CALLIAN": Coordinates(43.6226, 6.7522),
    "CARCES": Coordinates(43.4752, 6.1830),
    "CAVALAIRE SUR MER": Coordinates(43.1722, 6.5292),
    "COGOLIN": Coordinates(43.2528, 6.5303),
    "COLLOBRIERES": Coordinates(43.2373, 6.3094),
    "COTIGNAC": Coordinates(43.5285, 6.1495),
    "CUERS": Coordinates(43.2375, 6.0714),
    "DRAGUIGNAN": Coordinates(43.5360, 6.4645),
    "FAYENCE": Coordinates(43.6241, 6.6948),
    "FLAYOSC": Coordinates(43.5348, 6.3957),
    "FREJUS": Coordinates(43.4332, 6.7356),
    "GRIMAUD": Coordinates(43.2734, 6.5216),
    "HYERES": Coordinates(43.1204, 6.1286),
    "LA CRAU": Coordinates(43.1496, 6.0744),
    "LA GARDE": Coordinates(43.1247, 6.0104),
    "LA GARDE FREINET": Coordinates(43.3173, 6.4694),
    "LA SEYNE SUR MER": Coordinates(43.1030, 5.8783),
    "LA VALETTE DU VAR": Coordinates(43.1375, 5.9828),
    "LE LAVANDOU": Coordinates(43.1380, 6.3699),
    "LE LUC": Coordinates(43.3935, 6.3133),
    "LE PLAN DE LA TOUR": Coordinates(43.3396, 6.5489),
    "LE THORONET": Coordinates(43.4525, 6.3038),
    "LORGUES": Coordinates(43.4938, 6.3615),
    "OLLIOULES": Coordinates(43.1394, 5.8468),
    "PUGET SUR ARGENS": Coordinates(43.4554, 6.6856),
    "ROQUEBRUNE SUR ARGENS": Coordinates(43.4432, 6.6377),
    "SAINT RAPHAEL": Coordinates(43.4247, 6.7689),
    "SAINT TROPEZ": Coordinates(43.2677, 6.6407),
    "SAINTE MAXIME": Coordinates(43.3091, 6.6387),
    "SALERNES": Coordinates(43.5631, 6.2330),
    "SANARY SUR MER": Coordinates(43.1178, 5.8001),
    "SEILLANS": Coordinates(43.6368, 6.6432),
    "SIX FOURS LES PLAGES": Coordinates(43.0938, 5.8390),
    "SOLLIES PONT": Coordinates(43.1902, 6.0411),
    "TOULON": Coordinates(43.1242, 5.9280),
    "TOURTOUR": Coordinates(43.5903, 6.3026),
    "TRANS EN PROVENCE": Coordinates(43.5036, 6.4862),
    "VIDAUBAN": Coordinates(43.4277, 6.4325),
}


def find_var_commune_coordinates(value: str | None) -> Coordinates | None:
    if value is None:
        return None
    return VAR_COMMUNE_COORDINATES.get(normalize_commune_name(value))


def normalize_commune_name(value: str) -> str:
    without_accents = "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", without_accents).strip().upper()
    return re.sub(r"\s+", " ", normalized)
