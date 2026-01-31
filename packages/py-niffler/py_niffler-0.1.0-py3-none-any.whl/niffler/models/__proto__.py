from datetime import date, datetime

from tortoise.models import Model

from ..enums import (
    Category,
    Color,
    Instrument,
    Language,
    Neutralization,
    Region,
    Stage,
    Status,
    Switch,
    UnitHandling,
    Universe,
)
from .mixin import (
    AlphaComputedMixin,
    AlphaMarkingMixin,
    AlphaPerformanceMixin,
    AlphaRawMixin,
    AlphaSettingsMixin,
    AlphaStatusMixin,
    ExternalIDMixin,
    HashcodeMixin,
    TimeStampMixin,
)


class ExternalModel(Model, TimeStampMixin, ExternalIDMixin):
    class Meta:
        abstract = True


class LocalModel(Model, TimeStampMixin, HashcodeMixin):
    class Meta:
        abstract = True

    def __str__(self) -> str:
        hashcode = self.hashing()
        return f"{self.__class__.__name__}({getattr(self, 'hashcode') or hashcode})"


class AlphaCore(
    ExternalModel,
    AlphaRawMixin,
    AlphaSettingsMixin,
    AlphaPerformanceMixin,
    AlphaStatusMixin,
    AlphaMarkingMixin,
    AlphaComputedMixin,
):
    class Meta:
        abstract = True

    @classmethod
    def get_kv_from_record(cls, record: dict) -> dict:
        return {
            # ExternalID
            "id": record["id"],
            # AlphaStatus
            "status": Status(record["status"]),
            "stage": Stage(record["stage"]),
            "date_created": datetime.fromisoformat(record["dateCreated"]),
            "date_modified": datetime.fromisoformat(record["dateModified"]),
            "date_submitted": datetime.fromisoformat(record["dateSubmitted"])
            if record["dateSubmitted"]
            else None,
            # Settings
            "instrument": Instrument(record["settings"]["instrumentType"]),
            "language": Language(record["settings"]["language"]),
            "region": Region(record["settings"]["region"]),
            "universe": Universe(record["settings"]["universe"]),
            "delay": record["settings"]["delay"],
            "decay": record["settings"]["decay"],
            "neutralization": Neutralization(record["settings"]["neutralization"]),
            "truncation": record["settings"]["truncation"],
            "pasteurization": Switch(record["settings"]["pasteurization"]),
            "unit_handling": UnitHandling(record["settings"]["unitHandling"]),
            "nan_handling": Switch(record["settings"]["nanHandling"]),
            "max_trade": Switch(record["settings"]["maxTrade"]),
            "visualization": record["settings"]["visualization"],
            "start_date": date.fromisoformat(record["settings"]["startDate"]),
            "end_date": date.fromisoformat(record["settings"]["endDate"]),
            "test_period": record["settings"].get("testPeriod"),
            # Marking
            "name": record["name"],
            "favorite": record["favorite"],
            "hidden": record["hidden"],
            "color": Color(record["color"]) if record["color"] else None,
            "category": Category(record["category"]) if record["category"] else None,
            "tags": record["tags"],
            "classifications": record["classifications"],
            "competitions": record["competitions"],
            "themes": record["themes"],
            "pyramids": record["pyramids"],
            "pyramid_themes": record["pyramidThemes"],
            "team": record["team"],
            # Performance
            "is_pnl": record["is"]["pnl"],
            "is_booksize": record["is"]["bookSize"],
            "is_longcnt": record["is"]["longCount"],
            "is_shortcnt": record["is"]["shortCount"],
            "is_turnover": record["is"]["turnover"],
            "is_returns": record["is"]["returns"],
            "is_drawdown": record["is"]["drawdown"],
            "is_margin": record["is"]["margin"],
            "is_sharpe": record["is"]["sharpe"],
            "is_fitness": record["is"]["fitness"] or 0,
            "is_startdate": date.fromisoformat(record["is"]["startDate"]),
            "is_others": {},  # FIXME
            "is_checks": {
                check_["name"]: {k: v for k, v in check_.items() if k != "name"}
                for check_ in record["is"]["checks"]
            },
            # RAW
            "raw": record,
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({getattr(self, 'id')}|{self.is_sharpe})"

    @property
    def checkable(self) -> bool:
        return not bool(list(filter(lambda x: x["result"] == "FAIL", self.is_checks.values())))
