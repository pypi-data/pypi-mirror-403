import hashlib
from typing import Any

from tortoise import fields, signals
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


class TimeStampMixin:
    """本地时间戳 Mixin

    包含创建日期和更新日期的时间戳, 根据本地落库时间自动创建和更新.
    """

    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")


class ExternalIDMixin:
    """外部主键 Mixin

    基于外部系统的主键, 需要从接口获取, 需要该主键的模型必须提供主键才能测试.
    """

    id = fields.CharField(max_length=16, primary_key=True)


class HashcodeMixin:
    """自动哈希 Mixin

    指定 HashKey 并实现哈希函数, HashKey 决定了模型对象的唯一性, 主要用于一些可能重复,
    但是实际含义具有唯一性的对象.
    """

    __hashkey__: list[str] = []
    hashcode = fields.CharField(max_length=512, index=True)

    def hashing(self) -> str:
        keys = getattr(self.__class__, "__hashkey__", [])
        fields = [
            str(getattr(self, k, "|")).lower()
            if isinstance(getattr(self, k, "|"), bool)
            else str(getattr(self, k, "|"))
            for k in keys
        ]
        encode = "".join(fields)
        return hashlib.md5(encode.encode("utf-8")).hexdigest()

    def __init_subclass__(cls, **kwargs):
        """自动注册 Pre-Save

        Save 时自动更新 hashcode
        """
        super().__init_subclass__(**kwargs)

        async def _pre_save(
            sender: type[Model],
            instance: Model,
            using_db: Any,
            update_fields: list[str],
        ) -> None:
            if not isinstance(instance, cls):
                return
            instance.hashcode = instance.hashing()

        signals.pre_save(cls)(_pre_save)


class AlphaStatusMixin:
    """因子状态 Mixin"""

    status = fields.CharEnumField(Status, description="因子状态")
    stage = fields.CharEnumField(Stage, description="因子阶段")
    date_created = fields.DatetimeField(description="创建日期")
    date_modified = fields.DatetimeField(description="修改日期")
    date_submitted = fields.DatetimeField(description="提交日期", null=True)
    deprecated = fields.BooleanField(description="是否弃用", default=False)

    classifications = fields.JSONField(description="分类", default=list)
    competitions = fields.JSONField(description="比赛", null=True)
    themes = fields.JSONField(description="主题", null=True)
    pyramids = fields.JSONField(description="金字塔", null=True)
    pyramid_themes = fields.JSONField(description="金字塔主题", null=True)
    team = fields.JSONField(description="团队", null=True)

    start_date = fields.DateField(description="开始日期")
    end_date = fields.DateField(description="结束日期")


class AlphaSettingsMixin:
    """回测设置 Mixin"""

    instrument = fields.CharEnumField(Instrument, description="投资工具", default=Instrument.EQUITY)
    language = fields.CharEnumField(Language, description="因子语言", default=Language.FASTEXPR)
    region = fields.CharEnumField(Region, description="投资区域")
    universe = fields.CharEnumField(Universe, description="投资范围")
    delay = fields.IntField(description="Delay", ge=0, le=1)
    decay = fields.IntField(description="Decay", ge=0)
    neutralization = fields.CharEnumField(Neutralization, description="中性化策略")
    truncation = fields.FloatField(description="权重截断", gt=0, le=1)
    pasteurization = fields.CharEnumField(Switch, description="池化", default=Switch.ON)
    unit_handling = fields.CharEnumField(UnitHandling, description="单位验证", default=UnitHandling.VERIFY)
    max_trade = fields.CharEnumField(Switch, description="流动性控制", default=Switch.OFF)
    nan_handling = fields.CharEnumField(Switch, description="空值处理", default=Switch.ON)
    visualization = fields.BooleanField(description="高级可视化", default=False)
    test_period = fields.CharField(description="测试期结构", max_length=64, default="P2Y6M", null=True)


class AlphaMarkingMixin:
    """因子标记 Mixin"""

    name = fields.CharField(description="名称", max_length=255, null=True, default=None)
    favorite = fields.BooleanField(description="标星", default=False)
    hidden = fields.BooleanField(description="隐藏", default=False)
    color = fields.CharEnumField(Color, description="颜色", null=True)
    category = fields.CharEnumField(Category, description="类别", null=True)
    tags = fields.JSONField(description="标签", default=list)


class AlphaPerformanceMixin:
    """因子表现 Mixin"""

    is_pnl = fields.IntField(description="盈亏曲线")
    is_booksize = fields.IntField(description="交易规模")
    is_longcnt = fields.IntField(description="多头数量")
    is_shortcnt = fields.IntField(description="空头数量")
    is_turnover = fields.FloatField(description="成交额")
    is_returns = fields.FloatField(description="收益")
    is_drawdown = fields.FloatField(description="回撤")
    is_margin = fields.FloatField(description="利润")
    is_sharpe = fields.FloatField(description="夏普率")
    is_fitness = fields.FloatField(description="因子评分")
    is_startdate = fields.DateField(description="开始日期")
    is_others = fields.JSONField(description="中性化表现", default=list)
    is_checks = fields.JSONField(description="提交检查器", default=list)


class AlphaRawMixin:
    """因子原始内容 Mixin

    其中 raw 不可为空, 创建因子时必然能获取, 其他按需获取.
    """

    raw = fields.JSONField(description="因子明细原始数据", null=False, default=None)
    pnl_raw = fields.JSONField(description="盈亏明细", null=True, default=None)
    self_corr_raw = fields.JSONField(description="自相关", null=True, default=None)
    prod_corr_raw = fields.JSONField(description="生产相关性", null=True, default=None)
    combine_perf_raw = fields.JSONField(description="提交前后表现", null=True, default=None)
    yearly_stats_raw = fields.JSONField(description="年度统计", null=True, default=None)


class AlphaComputedMixin:
    """因子计算属性"""

    self_corr = fields.FloatField(description="本地自相关性", null=True, default=None)
    prod_corr = fields.FloatField(description="生产相关性", null=True, default=None)
