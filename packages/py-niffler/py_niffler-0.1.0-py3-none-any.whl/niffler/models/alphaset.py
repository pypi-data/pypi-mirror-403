from typing import Any, Self
from zoneinfo import ZoneInfo

from tortoise import fields

from ..enums import AlphaType, Category, Color, Region, Status, Universe
from .__proto__ import LocalModel


class AlphaSet(LocalModel):
    __hashkey__ = [
        "user_id",
        "alpha_type",
        "region",
        "universe",
        "delay",
        "date_from",
        "date_to",
        "sharpe_from",
        "sharpe_to",
        "fitness_from",
        "fitness_to",
        "status",
        "tag",
        "name",
        "category",
        "color",
        "hidden",
    ]

    user = fields.ForeignKeyField("niffler.User", related_name="alphasets")
    alpha_ids = fields.JSONField(description="因子集", default=list)
    n_regular = fields.IntField(description="因子集大小(Regular)", default=0)
    n_super = fields.IntField(description="因子集大小(Super)", default=0)

    # 固定集
    alpha_type = fields.CharEnumField(AlphaType, description="因子类型", null=True, default=None)
    region = fields.CharEnumField(Region, description="地区", null=True, default=None)
    universe = fields.CharEnumField(Universe, description=" Universe", null=True, default=None)
    delay = fields.IntField(description="延迟", null=True, default=None, ge=0, le=1)
    date_from = fields.DatetimeField(description="开始时间", null=True, default=None)
    date_to = fields.DatetimeField(description="结束时间", null=True, default=None)
    sharpe_from = fields.FloatField(description="最低夏普率", null=True, default=None)
    sharpe_to = fields.FloatField(description="最高夏普率", null=True, default=None)
    fitness_from = fields.FloatField(description="最低稳健性", null=True, default=None)
    fitness_to = fields.FloatField(description="最高稳健性", null=True, default=None)

    # 浮动项
    status = fields.CharEnumField(Status, description="状态", null=True, default=None)
    tag = fields.CharField(description="检索标签", null=True, default=None, max_length=256)
    name = fields.CharField(description="检索名称", null=True, default=None, max_length=256)
    category = fields.CharEnumField(Category, description="因子类别", null=True, default=None)
    color = fields.CharEnumField(Color, description="因子颜色", null=True, default=None)
    hidden = fields.BooleanField(description="隐藏因子", null=True, default=None)

    def to_params(self) -> dict:
        params: dict[str, Any] = {"order": "-is.fitness"}
        if self.alpha_type is not None:
            params["type"] = self.alpha_type.value
        if self.date_from is not None:
            params["dateCreated>"] = self.date_from.astimezone(ZoneInfo("America/New_York")).isoformat()
        if self.date_to is not None:
            params["dateCreated<"] = self.date_to.astimezone(ZoneInfo("America/New_York")).isoformat()
        if self.status is not None:
            params["status"] = self.status.value
        if self.delay is not None:
            params["delay"] = self.delay

        # settings
        for setting, setting_s in zip(
            [self.region, self.universe],
            ["region", "universe"],
        ):
            if setting is not None:
                params[f"settings.{setting_s}"] = setting.value

        # is
        for is_value, is_value_s in zip(
            [self.sharpe_from, self.sharpe_to, self.fitness_from, self.fitness_to],
            ["sharpe>", "sharpe<", "fitness>", "fitness<"],
        ):
            if is_value is not None:
                params[f"is.{is_value_s}"] = is_value

        # info
        for info, info_s in zip([self.tag, self.name], ["tag", "name"]):
            if info is not None:
                params[info_s] = info

        # info-enum
        for info, info_s in zip([self.color, self.category], ["color", "category"]):
            if info is not None:
                params[info_s] = info.value

        return params

    @property
    def is_frozen(self) -> bool:
        info = [self.status, self.tag, self.name, self.category, self.color, self.hidden]
        if len([i for i in info if i is not None]) > 0:
            # 动态条件非空
            return False
        elif self.date_to is None or self.updated_at is None or self.updated_at < self.date_to:
            # 未设截止日期, 未落库, 或截止日期超过落库日期, 取最新因子集
            return False
        else:
            return True

    def update_from_record(self, record: list) -> Self:
        ra_ids = [rcd["id"] for rcd in record if rcd["type"] == "REGULAR"]
        sa_ids = [rcd["id"] for rcd in record if rcd["type"] == "SUPER"]
        self.alpha_ids = ra_ids + sa_ids
        self.n_regular = len(ra_ids)
        self.n_super = len(sa_ids)
        return self
