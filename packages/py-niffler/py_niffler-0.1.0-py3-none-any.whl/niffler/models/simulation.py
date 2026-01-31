from tortoise import fields

from ..enums import ComponentActivation, SelectionHandling, SimulationType
from .__proto__ import LocalModel
from .mixin import AlphaMarkingMixin, AlphaSettingsMixin


class Simulation(LocalModel, AlphaSettingsMixin, AlphaMarkingMixin):
    __hashkey__ = [
        "simulation_type",
        "expr",
        "combo",
        "selection",
        "instrument",
        "region",
        "universe",
        "decay",
        "delay",
        "neutralization",
        "truncation",
        "pasteurization",
        "unit_handling",
        "max_trade",
        "language",
        "nan_handling",
        "visualization",
    ]

    simulation_type = fields.CharEnumField(SimulationType, description="回测类型")
    alpha_id = fields.CharField(default=None, null=True, max_length=64)
    simid = fields.CharField(default=None, null=True, max_length=64)

    # expr
    expr = fields.TextField(description="因子表达式", null=True, default=None)  # regular
    combo = fields.TextField(description="因子表达式-组合", null=True, default=None)  # super
    selection = fields.TextField(description="因子表达式-选择", null=True, default=None)  # super

    # super-setting
    selection_limit = fields.IntField(description="选择限制", ge=10, default=10)
    selection_handling = fields.CharEnumField(
        SelectionHandling, description="选择处理", default=SelectionHandling.NON_NAN
    )
    component_activation = fields.CharEnumField(
        ComponentActivation, description="组件激活", default=ComponentActivation.IS
    )

    # description
    description = fields.TextField(description="描述", null=True, default=None)  # regular
    description_combo = fields.TextField(description="描述-组合", null=True, default=None)  # super
    description_selection = fields.TextField(description="描述-选择", null=True, default=None)  # super

    def to_payload(self) -> dict:
        if self.simulation_type == SimulationType.REGULAR:
            return {
                "type": "REGULAR",
                "settings": {
                    "instrumentType": self.instrument.value,
                    "language": self.language.value,
                    "region": self.region.value,
                    "universe": self.universe.value,
                    "delay": self.delay,
                    "decay": self.decay,
                    "visualization": self.visualization,
                    "neutralization": self.neutralization.value,
                    "truncation": self.truncation,
                    "pasteurization": self.pasteurization.value,
                    "unitHandling": self.unit_handling.value,
                    "nanHandling": self.nan_handling.value,
                    "maxTrade": self.max_trade.value,
                    "testPeriod": self.test_period,
                },
                "regular": self.expr,
            }
        else:
            return {
                "type": "SUPER",
                "settings": {
                    "instrumentType": self.instrument.value,
                    "language": self.language.value,
                    "region": self.region.value,
                    "universe": self.universe.value,
                    "delay": self.delay,
                    "decay": self.decay,
                    "visualization": self.visualization,
                    "neutralization": self.neutralization.value,
                    "truncation": self.truncation,
                    "pasteurization": self.pasteurization.value,
                    "unitHandling": self.unit_handling.value,
                    "nanHandling": self.nan_handling.value,
                    "maxTrade": self.max_trade.value,
                    "selectionLimit": self.selection_limit,
                    "selectionHandling": self.selection_handling.value,
                    "componentActivation": self.component_activation.value,
                    "testPeriod": self.test_period,
                },
                "combo": self.combo,
                "selection": self.selection,
            }
