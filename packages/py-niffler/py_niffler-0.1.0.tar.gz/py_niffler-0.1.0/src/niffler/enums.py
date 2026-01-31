from __future__ import annotations

import enum


class AlphaType(enum.StrEnum):
    REGULAR = "REGULAR"
    SUPER = "SUPER"


class Status(enum.StrEnum):
    ACTIVE = "ACTIVE"
    UNSUBMITTED = "UNSUBMITTED"
    DECOMMISSIONED = "DECOMMISSIONED"


class Language(enum.StrEnum):
    FASTEXPR = "FASTEXPR"
    EXPR = "EXPR"
    PYTHON = "PYTHON"


class Instrument(enum.StrEnum):
    CRYPTO = "CRYPTO"
    EQUITY = "EQUITY"


class Region(enum.StrEnum):
    USA = "USA"
    GLB = "GLB"
    EUR = "EUR"
    ASI = "ASI"
    CHN = "CHN"
    IND = "IND"

    def universes(self) -> list[Universe]:
        match self:
            case Region.USA:
                return [
                    Universe.TOP3000,
                    Universe.TOP1000,
                    Universe.TOP500,
                    Universe.TOP200,
                    Universe.ILLIQUID_MINVOL1M,
                    Universe.TOPSP500,
                ]
            case Region.GLB:
                return [Universe.TOP3000, Universe.TOPDIV3000, Universe.MINVOL1M]
            case Region.EUR:
                return [
                    Universe.TOP2500,
                    Universe.TOP1200,
                    Universe.ILLIQUID_MINVOL1M,
                    Universe.TOP800,
                    Universe.TOP400,
                ]
            case Region.ASI:
                return [
                    Universe.ILLIQUID_MINVOL1M,
                    Universe.MINVOL1M,
                ]
            case Region.CHN:
                return [Universe.TOP2000U]
            case Region.IND:
                return [Universe.TOP500]
            case _:
                raise ValueError(f"Region {self} not supported")

    def neutralizations(self) -> list[Neutralization]:
        basic_neu = [
            Neutralization.NONE,
            Neutralization.MARKET,
            Neutralization.SECTOR,
            Neutralization.INDUSTRY,
            Neutralization.SUBINDUSTRY,
        ]
        stat_neu = [
            Neutralization.REVERSION_AND_MOMENTUM,
            Neutralization.CROWDING,
            Neutralization.FAST,
            Neutralization.SLOW,
            Neutralization.SLOW_AND_FAST,
        ]
        match self:
            case Region.USA:
                return [*basic_neu, *stat_neu, Neutralization.STATISTICAL]
            case Region.GLB | Region.EUR | Region.ASI:
                return [*basic_neu, *stat_neu, Neutralization.STATISTICAL, Neutralization.COUNTRY]
            case Region.CHN | Region.IND:
                return [*basic_neu, *stat_neu]
            case _:
                raise ValueError(f"Region {self} not supported")


class Universe(enum.StrEnum):
    TOP3000 = "TOP3000"
    TOPDIV3000 = "TOPDIV3000"
    TOP2500 = "TOP2500"
    TOP2000U = "TOP2000U"
    TOP1200 = "TOP1200"
    TOP1000 = "TOP1000"
    TOP800 = "TOP800"
    TOP500 = "TOP500"
    TOPSP500 = "TOPSP500"
    TOP400 = "TOP400"
    TOP200 = "TOP200"
    ILLIQUID_MINVOL1M = "ILLIQUID_MINVOL1M"
    MINVOL1M = "MINVOL1M"


class Category(enum.StrEnum):
    PRICE_REVERSION = "PRICE_REVERSION"
    PRICE_MOMENTUM = "PRICE_MOMENTUM"
    VOLUME = "VOLUME"
    FUNDAMENTAL = "FUNDAMENTAL"
    ANALYST = "ANALYST"
    PRICE_VOLUME = "PRICE_VOLUME"
    RELATION = "RELATION"
    SENTIMENT = "SENTIMENT"


class Neutralization(enum.StrEnum):
    NONE = "NONE"
    REVERSION_AND_MOMENTUM = "REVERSION_AND_MOMENTUM"
    STATISTICAL = "STATISTICAL"
    CROWDING = "CROWDING"
    FAST = "FAST"
    SLOW = "SLOW"
    MARKET = "MARKET"
    SECTOR = "SECTOR"
    INDUSTRY = "INDUSTRY"
    SUBINDUSTRY = "SUBINDUSTRY"
    SLOW_AND_FAST = "SLOW_AND_FAST"
    COUNTRY = "COUNTRY"


class Switch(enum.StrEnum):
    ON = "ON"
    OFF = "OFF"


class ComponentActivation(enum.StrEnum):
    IS = "IS"
    OS = "OS"


class UnitHandling(enum.StrEnum):
    VERIFY = "VERIFY"


class Color(enum.StrEnum):
    RED = "RED"
    YELLOW = "YELLOW"
    BLUE = "BLUE"
    GREEN = "GREEN"
    PURPLE = "PURPLE"


class Grade(enum.StrEnum):
    AVERAGE = "AVERAGE"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"
    SPECTACULAR = "SPECTACULAR"
    NEEDIMPROVMENT = "NEEDIMPROVMENT"


class Stage(enum.StrEnum):
    IS = "IS"
    OS = "OS"


class SelectionHandling(enum.StrEnum):
    POSITIVE = "POSITIVE"
    NON_ZERO = "NON_ZERO"
    NON_NAN = "NON_NAN"


class ResponseStatus(enum.StrEnum):
    SUCCESS = "SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    TRY_LATER = "TRY_LATER"
    BAD_REQUEST = "BAD_REQUEST"


class HTTPMethod(enum.StrEnum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    GET_LATER = "GET_LATER"


class FieldType(enum.StrEnum):
    GROUP = "GROUP"
    VECTOR = "VECTOR"
    MATRIX = "MATRIX"
    OTHER = "OTHER"


class OpScope(enum.StrEnum):
    REGULAR = "REGULAR"
    SELECTION = "SELECTION"
    COMBO = "COMBO"


class OpType(enum.StrEnum):
    ARITHMETIC = "ARITHMETIC"
    LOGICAL = "LOGICAL"
    TIMESERIES = "TIMESERIES"
    CROSS_SECTIONAL = "CROSS_SECTIONAL"
    VECTOR = "VECTOR"
    TRANSFORM = "TRANSFORM"
    GROUP = "GROUP"
    SELECTION = "SELECTION"
    COMBO = "COMBO"


class SimulationType(enum.StrEnum):
    REGULAR = "REGULAR"
    SUPER = "SUPER"
