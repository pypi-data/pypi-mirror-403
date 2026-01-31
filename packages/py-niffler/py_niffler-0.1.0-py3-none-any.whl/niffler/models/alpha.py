from typing import Self

from tortoise import fields

from ..enums import ComponentActivation, SelectionHandling, SimulationType
from .__proto__ import AlphaCore


class RegularAlpha(AlphaCore):
    user = fields.ForeignKeyField("niffler.User", related_name="regular_alphas")
    expr = fields.TextField(description="因子表达式")
    description = fields.TextField(description="因子描述", null=True)
    operator_count = fields.IntField(description="操作符数", null=True)

    @classmethod
    def from_record(cls, record: dict) -> Self:
        assert record["type"] == "REGULAR", "因子类型错误"
        kv = cls.get_kv_from_record(record)
        kv = {
            **kv,
            **{
                "user_id": record["author"],
                "expr": record["regular"]["code"],
                "description": record["regular"]["description"],
                "operator_count": record["regular"]["operatorCount"],
            },
        }
        return cls(**kv)

    @classmethod
    def get_keys_from_record(cls, record: dict) -> list[str]:
        return list(cls.get_kv_from_record(record).keys()) + ["expr", "description", "user_id", "operator_count"]

    def to_description(self) -> dict:
        return {
            "category": self.category.value if self.category is not None else None,
            "regular": {"description": self.description},
            "color": self.color.value if self.color is not None else None,
            "name": self.name,
            "tags": self.tags,
            "hidden": self.hidden,
            "favorite": self.favorite,
        }

    def to_simulation(self) -> dict:
        return {
            "simulation_type": SimulationType.REGULAR,
            "region": self.region,
            "universe": self.universe,
            "delay": self.delay,
            "decay": self.decay,
            "truncation": self.truncation,
            "pasteurization": self.pasteurization,
            "max_trade": self.max_trade,
            "nan_handling": self.nan_handling,
            "visualization": self.visualization,
            "test_period": self.test_period,
            "neutralization": self.neutralization,
            "name": self.name,
            "tags": self.tags,
            "expr": self.expr,
            "description": self.description,
        }


class SuperAlpha(AlphaCore):
    user = fields.ForeignKeyField("niffler.User", related_name="super_alphas")
    combo = fields.TextField(description="因子表达式-组合")
    selection = fields.TextField(description="因子表达式-选择")

    selection_limit = fields.IntField(description="选择限制", ge=10)
    selection_handling = fields.CharEnumField(SelectionHandling, description="选择处理")
    component_activation = fields.CharEnumField(
        ComponentActivation, description="组件激活", default=ComponentActivation.IS
    )

    description_combo = fields.TextField(description="描述-组合", null=True)
    description_selection = fields.TextField(description="描述-选择", null=True)
    operator_count_combo = fields.IntField(description="操作符数-组合", null=True)
    operator_count_selection = fields.IntField(description="操作符数-选择", null=True)

    @classmethod
    def from_record(cls, record: dict) -> Self:
        assert record["type"] == "SUPER", "因子类型错误"
        kv = cls.get_kv_from_record(record)
        kv = {
            **kv,
            **{
                "user_id": record["author"],
                "combo": record["combo"]["code"],
                "selection": record["selection"]["code"],
                "selection_handling": SelectionHandling(record["settings"]["selectionHandling"]),
                "selection_limit": record["settings"]["selectionLimit"],
                "component_activation": ComponentActivation(record["settings"]["componentActivation"]),
                "description_combo": record["combo"]["description"],
                "description_selection": record["selection"]["description"],
                "operator_count_combo": record["combo"]["operatorCount"],
                "operator_count_selection": record["selection"]["operatorCount"],
            },
        }
        return cls(**kv)

    @classmethod
    def get_keys_from_record(cls, record: dict) -> list[str]:
        return list(cls.get_kv_from_record(record).keys()) + [
            "combo",
            "selection",
            "user_id",
            "selection_handling",
            "selection_limit",
            "component_activation",
            "description_combo",
            "description_selection",
            "operator_count_combo",
            "operator_count_selection",
        ]

    def to_description(self) -> dict:
        payload = {
            "name": self.name,
            "color": self.color.value if self.color is not None else None,
            "tags": self.tags,
            "category": self.category.value if self.category is not None else None,
            "regular": {"description": None},
            "favorite": self.favorite,
        }
        if self.description_combo is not None:
            payload["combo"] = {"description": self.description_combo}
        if self.description_selection is not None:
            payload["selection"] = {"description": self.description_selection}
        return payload

    def to_simulation(self) -> dict:
        return {
            "simulation_type": SimulationType.SUPER,
            "region": self.region,
            "universe": self.universe,
            "delay": self.delay,
            "decay": self.decay,
            "truncation": self.truncation,
            "pasteurization": self.pasteurization,
            "max_trade": self.max_trade,
            "nan_handling": self.nan_handling,
            "visualization": self.visualization,
            "test_period": self.test_period,
            "neutralization": self.neutralization,
            "name": self.name,
            "tags": self.tags,
            "combo": self.combo,
            "selection": self.selection,
            "description": self.description,
            "selection_limit": self.selection_limit,
            "selection_handling": self.selection_handling,
            "component_activation": self.component_activation,
            "description_combo": self.description_combo,
            "description_selection": self.description_selection,
        }
