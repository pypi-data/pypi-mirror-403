import os
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, Field, SecretStr
from pydantic_extra_types.timezone_name import TimeZoneName
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource


class DatabaseConfig(BaseModel):
    connection: str = Field(default="sqlite:///:memory:", description="本地因子库")
    models: list[str] = Field(default=["niffler.models"], description="模型组")
    use_tz: bool = Field(default=True, description="统一时区")

    sql_batchsize: int = 50


class PlatformConfig(BaseModel):
    """平台配置类"""

    base_url: str = Field(default="https://api.worldquantbrain.com", description="根路径")
    auth_url: str = Field(default="/authentication", description="登陆")
    dataset_url: str = Field(default="/data-sets/{dataset_id}", description="获取数据集")
    datafield_url: str = Field(default="/data-fields", description="获取数据字段")
    operators_url: str = Field(default="/operators", description="获取运算符")
    alphaset_url: str = Field(default="/users/self/alphas", description="获取因子集")
    simulation_url: str = Field(default="/simulations", description="因子回测")
    genius_url: str = Field(default="/consultant/boards/genius", description="获取顾问排行")

    alpha_info: str = Field(default="/alphas/{alpha_id}", description="获取因子信息")
    alpha_yearly_stats: str = Field(
        default="https://api.worldquantbrain.com/alphas/{alpha_id}/recordsets/yearly-stats",
        description="获取因子年化统计",
    )
    alpha_pnl: str = Field(default="/alphas/{alpha_id}/recordsets/pnl", description="获取因子 PNL")
    alpha_check: str = Field(default="/alphas/{alpha_id}/check", description="检查因子")
    alpha_corr: str = Field(default="/alphas/{alpha_id}/correlations/prod", description="获取因子生产相关性")
    alpha_perf: str = Field(
        default="/users/self/alphas/{alpha_id}/before-and-after-performance", description="获取因子绩效"
    )
    alpha_submit: str = Field(default="/alphas/{alpha_id}/submit", description="提交因子")


class NotifierConfig(BaseModel):
    url: str = Field(default="https://api.day.app/{token}", description="推送地址")


class NifflerConfig(BaseSettings):
    username: str = Field(default=...)
    password: SecretStr = Field(default=...)

    notifier_url: str = Field(default="https://api.day.app/{token}", description="推送地址")
    notifier_token: SecretStr = Field(default=...)

    timezone: TimeZoneName = TimeZoneName("Asia/Shanghai")
    begin_date: datetime = Field(default=datetime(2025, 1, 1), description="因子开始时间")

    database: DatabaseConfig = DatabaseConfig()
    platform: PlatformConfig = PlatformConfig()
    notifier: NotifierConfig = NotifierConfig()

    expire_redun: timedelta = Field(default=timedelta(hours=0.5), description="缓存容错")
    retry_delay: float = Field(default=10, description="重试间隔秒", gt=0)
    max_retry: int = Field(default=10, description="最大重试次数", ge=1)
    concurrency: int = Field(default=5, description="请求最大并发数", ge=1)

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="NIFFLER_",
        env_nested_delimiter="__",
        toml_file=[
            os.path.expanduser("~/.config/niffler/config.toml"),
            os.path.join(Path.cwd(), "niffler_config.toml"),
        ],
        extra="allow",
        validate_by_name=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, TomlConfigSettingsSource(settings_cls))
