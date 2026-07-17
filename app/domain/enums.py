from enum import StrEnum


class PropertyType(StrEnum):
    HOUSE = "house"
    ESTATE = "estate"
    BASTIDE = "bastide"
    MAS = "mas"
    CASTLE = "castle"
    HOTEL = "hotel"
    GUEST_HOUSE = "guest_house"
    GITE_BUSINESS = "gite_business"
    BUSINESS_ASSETS = "business_assets"
    LAND = "land"
    OTHER = "other"


class PropertyStatus(StrEnum):
    NEW = "new"
    TO_REVIEW = "to_review"
    INTERESTING = "interesting"
    FAVORITE = "favorite"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class LocationPrecision(StrEnum):
    EXACT_ADDRESS = "exact_address"
    STREET = "street"
    LOCALITY = "locality"
    MUNICIPALITY = "municipality"
    POSTAL_CODE = "postal_code"
    AREA = "area"
    DEPARTMENT = "department"
    UNKNOWN = "unknown"
