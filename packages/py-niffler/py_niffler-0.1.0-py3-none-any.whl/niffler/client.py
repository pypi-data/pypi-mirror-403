import asyncio
import logging
import tomllib
from datetime import date, datetime, timedelta
from itertools import batched
from math import ceil
from pathlib import Path
from typing import Any, Self, TypeVar, overload
from zoneinfo import ZoneInfo

import httpx
import polars as pl
from pydantic import BaseModel, ConfigDict, field_validator
from tortoise import Tortoise
from tortoise.expressions import Q

from .config import NifflerConfig
from .enums import (
    AlphaType,
    Category,
    Color,
    FieldType,
    HTTPMethod,
    Instrument,
    OpScope,
    Region,
    ResponseStatus,
    Status,
    Universe,
)
from .models import AlphaSet, RegularAlpha, Simulation, SuperAlpha, User
from .models.__proto__ import ExternalModel
from .utils import parse_record

type JSONLike = dict | list

T = TypeVar("T", bound=ExternalModel)


class NifflerResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)

    status: ResponseStatus
    content: JSONLike
    raw: httpx.Response

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: str | ResponseStatus) -> ResponseStatus:
        if isinstance(v, str):
            return ResponseStatus(v)
        return v


class TokenExpiredError(Exception):
    pass


class BadRequestError(Exception):
    pass


class NifflerClient:
    """平台接口交互工具

    Notes
    -----
    - ._cache : dict[str, Any]
          [REGION]_active_pnls - 活跃 Alpha PnL, 用于计算 Self-Correlation
    """

    def __init__(self, config: NifflerConfig | str | Path | dict | None = None) -> None:
        if config is None:
            cfg = NifflerConfig()
        elif isinstance(config, (str, Path)):
            cfg = NifflerConfig(**tomllib.load(open(Path(config), "rb")))
        elif isinstance(config, dict):
            cfg = NifflerConfig(**config)
        elif isinstance(config, NifflerConfig):
            cfg = config
        else:
            raise ValueError(f"配置无效: {config}")

        self._config = cfg
        self._logger = logging.getLogger(__name__)
        self._user: User | None = None
        self._cache: dict[str, Any] = {}

        self._sem = asyncio.Semaphore(self._config.concurrency)

    async def setup(self) -> Self:
        await Tortoise.init(
            config={
                "connections": {"default": self._config.database.connection},
                "apps": {
                    "niffler": {
                        "models": [*self._config.database.models, "aerich.models"],
                        "default_connection": "default",
                    }
                },
                "use_tz": self._config.database.use_tz,
                "timezone": self._config.timezone,
            }
        )
        await Tortoise.generate_schemas(safe=True)
        _ = await self.get_user()
        self._logger.debug("数据库链接初始化完成")
        return self

    async def close(self) -> None:
        await Tortoise.close_connections()

    async def get_user(self, force: bool = False) -> User:
        if (
            (self._user is not None)  # 已完成初始化
            and (self._user.cookie is not None)  # Cookie 不为空
            and (
                datetime.now(ZoneInfo(self._config.timezone)) - self._user.updated_at
                < timedelta(seconds=self._user.expiry) - self._config.expire_redun
            )  # Cookie 未过期
            and not force
        ):
            # self._logger.debug("获取权鉴缓存")
            return self._user
        else:
            user = await User.get_or_none(username=self._config.username)
            if (
                (user is not None)
                and (user.cookie is not None)
                and (
                    datetime.now(ZoneInfo(self._config.timezone)) - user.updated_at
                    < timedelta(seconds=user.expiry) - self._config.expire_redun
                )
            ):
                # self._logger.debug("读取本地权鉴")
                self._user = user
                return user
            else:
                # self._logger.debug("重新登录")
                return await self.login()

    async def login(self) -> User:
        """登录"""
        async with httpx.AsyncClient(
            auth=httpx.BasicAuth(self._config.username, self._config.password.get_secret_value()),
            base_url=self._config.platform.base_url,
        ) as client:
            response = await self.send_request(client, HTTPMethod.POST, self._config.platform.auth_url)
            if response.status != ResponseStatus.SUCCESS or not isinstance(response.content, dict):
                raise ValueError("登陆失败")

        self._user, _ = await User.update_or_create(
            id=response.raw.json()["user"]["id"],
            defaults=dict(
                username=self._config.username,
                password=self._config.password,
                permissions=response.raw.json().get("permissions"),
                cookie=response.raw.cookies.get("t"),
                expiry=response.raw.json()["token"]["expiry"],
            ),
        )
        # self._logger.debug(f"登陆成功: {response.raw.json()['user']['id']}")
        return self._user

    async def send_request(
        self,
        client: httpx.AsyncClient,
        method: HTTPMethod,
        url: str,
        params: dict | None = None,
        payload: JSONLike | None = None,
        max_retry: int | None = None,
    ) -> NifflerResponse:
        """通用请求发送器

        NifflerClient 核心交互方法, 向平台发送请求, 支持 Get/Get-Later/Post/Patch, 实现了自动重试和超限休眠.
        返回结果抽象为 NifflerResponse, 既包含结果内容, 也包含原始返回内容.
        """

        if max_retry is None:
            max_retry = self._config.max_retry

        match HTTPMethod(method):
            case HTTPMethod.GET | HTTPMethod.GET_LATER:
                method_core: str = "GET"
            case _:
                method_core: str = method.value

        ntry = 0
        while max_retry - ntry > 0:
            try:
                res = await client.request(
                    method=method_core,
                    url=url,
                    timeout=None,
                    params=params,
                    json=payload,
                )
                if res.status_code in [401, 429]:
                    # Re-Send
                    self._user = await self.get_user()
                    client.cookies.set("t", self._user.cookie)
                    res = await client.request(
                        method=method_core,
                        url=url,
                        timeout=None,
                        params=params,
                        json=payload,
                    )
                match res.status_code:
                    case 401:  # 登陆失败
                        return NifflerResponse(
                            status=ResponseStatus.LOGIN_FAILED,
                            content={"message": "登陆失败"},
                            raw=res,
                        )
                    case 429:  # 触发频率限制
                        return NifflerResponse(
                            status=ResponseStatus.TRY_LATER,
                            content={"message": "触发频率限制"},
                            raw=res,
                        )
                    case 404 | 400:  # 请求异常
                        try:
                            message = res.json()
                        except Exception:
                            message = "请求异常"
                        return NifflerResponse(
                            status=ResponseStatus.BAD_REQUEST,
                            content={"message": message},
                            raw=res,
                        )
                    case success if 200 <= success <= 299:
                        pass
                    case error:  # 服务器异常
                        return NifflerResponse(
                            status=ResponseStatus.TRY_LATER,
                            content={"message": f"服务器异常({error})"},
                            raw=res,
                        )

                match method:
                    case HTTPMethod.GET | HTTPMethod.PATCH:
                        if res.content is None:
                            ntry += 1
                            await asyncio.sleep(self._config.retry_delay)
                            continue
                        else:
                            content = res.json()
                    case HTTPMethod.GET_LATER:
                        retry_after = float(res.headers.get("Retry-After", 0))
                        if retry_after:
                            await asyncio.sleep(retry_after + self._config.retry_delay)
                            continue
                        content = res.json()
                    case _:
                        content = {}

                return NifflerResponse(status=ResponseStatus.SUCCESS, content=content, raw=res)

            except Exception as e:
                ntry += 1
                self._logger.error(f"Error with {url} ({method}) {e}")
                await asyncio.sleep(self._config.retry_delay)

        _err = f"{method_core} {url} 超过最大重试次数, 请求失败"
        self._logger.error(_err, exc_info=True)
        raise ValueError(_err)

    async def get(self, url: str, params: dict | None = None, later: bool = False) -> JSONLike:
        async with httpx.AsyncClient(
            cookies=httpx.Cookies({"t": (await self.get_user()).cookie}),
            base_url=self._config.platform.base_url,
        ) as client:
            res = await self.send_request(
                client,
                HTTPMethod.GET_LATER if later else HTTPMethod.GET,
                url,
                params=params,
            )

        match res.status:
            case ResponseStatus.SUCCESS:
                return res.content
            case ResponseStatus.BAD_REQUEST:
                raise BadRequestError(res.content)
            case ResponseStatus.LOGIN_FAILED:
                raise TokenExpiredError("登陆已过期")
            case ResponseStatus.TRY_LATER:
                await asyncio.sleep(self._config.retry_delay * 12)
                return await self.get(url, params)
            case _:
                return res.content

    async def post(self, url: str, payload: Any) -> NifflerResponse:
        async with httpx.AsyncClient(
            cookies=httpx.Cookies({"t": (await self.get_user()).cookie}),
            base_url=self._config.platform.base_url,
        ) as client:
            res = await self.send_request(client, HTTPMethod.POST, url, payload=payload)
            return res

    async def patch(self, url: str, payload: Any) -> JSONLike:
        async with httpx.AsyncClient(
            cookies=httpx.Cookies({"t": (await self.get_user()).cookie}),
            base_url=self._config.platform.base_url,
        ) as client:
            res = await self.send_request(client, HTTPMethod.PATCH, url, payload=payload)

        match res.status:
            case ResponseStatus.SUCCESS:
                return res.content
            case ResponseStatus.BAD_REQUEST:
                raise BadRequestError(res.content)
            case ResponseStatus.LOGIN_FAILED:
                raise TokenExpiredError("登陆已过期")
            case ResponseStatus.TRY_LATER:
                await asyncio.sleep(self._config.retry_delay)
                return await self.patch(url, payload)
            case _:
                return res.content

    async def get_all(
        self,
        url: str,
        page_size: int,
        params: dict | None = None,
        count_key: str = "count",
        result_key: str = "results",
    ) -> list[dict]:
        result = []
        r0 = await self.get(
            url,
            params={**(params or {}), "offset": 0, "limit": page_size},
        )

        if not isinstance(r0, dict):
            raise ValueError("GET-ALL 0 应该返回字典")
        total = r0[count_key]
        result += r0[result_key]
        offsets = list(range(page_size, total, page_size))
        if len(offsets) == 0:
            return result

        progress = len(result)
        lock = asyncio.Lock()  # Progress 加锁
        self._logger.debug(f"分页加载进度: [{progress}/{total}]")

        async def _fetch(offset: int) -> list[dict]:
            async with self._sem:
                ri = await self.get(
                    url,
                    params={**(params or {}), "offset": offset, "limit": page_size},
                )
                assert isinstance(ri, dict), "GET-ALL 0 应该返回字典"
                async with lock:
                    nonlocal progress
                    progress += len(ri[result_key])
                    self._logger.debug(f"分页加载进度: [{progress}/{total}]")
                return ri[result_key]

        pages = await asyncio.gather(*(_fetch(offset) for offset in offsets), return_exceptions=True)
        for p in pages:
            if isinstance(p, BaseException):
                self._logger.error(f"分页加载失败: {p}")
            else:
                result.extend(p)
        return result

    async def notify(self, message: str, title: str | None = None, group: str | None = None) -> None:
        payload = {"body": message, "isArchive": 1}
        if group is not None:
            payload["group"] = group
        if title is not None:
            payload["title"] = title

        async with httpx.AsyncClient(
            base_url=self._config.notifier_url.format(token=self._config.notifier_token.get_secret_value())
        ) as client:
            _ = await self.send_request(client, HTTPMethod.POST, "/", payload=payload)

    async def batch_update_or_create(
        self, instances: list[T], model: type[T], fields: list[str] | None = None
    ) -> list[T]:
        """批量创建或更新外部模型

        外部模型具有唯一性, 包含唯一外部 ID, 该方法实现了外部模型的批量落表.

        Parameters
        ----------
        instances : list[T] 更新对象, 必须包含 id 否则无法更新
        model : type[T] 目标模型 (数据库表)
        fields : list[str] 要更新的字段 (默认为除了 id 和 created_at 之外的全部字段)
        """

        if fields is None:
            fields = [p for p in model._meta.fields_map.keys() if p not in ["id", "created_at"]]

        ids_all = [i.id for i in instances if i.id is not None]
        ids_update = await model.filter(id__in=ids_all).values_list("id", flat=True)
        ids_create = [i for i in ids_all if i not in ids_update]

        to_update = [ins for ins in instances if ins.id in ids_update]
        to_create = [ins for ins in instances if ins.id in ids_create]

        if to_update:
            await model.bulk_update(to_update, fields=fields, batch_size=self._config.database.sql_batchsize)

        if to_create:
            await model.bulk_create(to_create, batch_size=self._config.database.sql_batchsize)

        return await model.filter(id__in=ids_all).all()

    async def get_operators(self, op_scope: OpScope | str | None = None) -> list[dict]:
        """获取运算符"""
        ops = await self.get(url=self._config.platform.operators_url)
        assert isinstance(ops, list), "运算符获取异常"
        if op_scope is not None:
            ops = list(filter(lambda x: op_scope in x["scope"], ops))
        return ops

    async def get_datafields(
        self,
        region: Region | str,
        universe: Universe | str,
        delay: int,
        dataset_id: str | None = None,
        field_type: FieldType | str | None = None,
        instrument_type: Instrument | str | None = None,
    ) -> list[dict]:
        """获取数据字段

        数据字段与 region / universe / delay 关联, 可通过 dataset_id 和 field_type 进行筛选,
        另外保留了 instrument_type 用于未来其他类型使用.
        """

        params = {
            "instrumentType": instrument_type or Instrument.EQUITY,
            "region": region,
            "universe": universe,
            "delay": delay,
        }
        if dataset_id is not None:
            params["dataset.id"] = dataset_id
        if field_type is not None:
            params["type"] = field_type

        return await self.get_all(url=self._config.platform.datafield_url, page_size=50, params=params)

    async def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        """获取数据集"""
        ds = await self.get(self._config.platform.dataset_url.format(dataset_id=dataset_id))
        assert isinstance(ds, dict), "数据集获取异常"
        return ds

    async def get_alpha(self, alpha_id: str, force: bool = False) -> RegularAlpha | SuperAlpha:
        if not force:
            ra = await RegularAlpha.get_or_none(id=alpha_id)
            sa = await SuperAlpha.get_or_none(id=alpha_id)
            if ra is not None:
                # self._logger.debug(f"读取本地 RA: {ra}")
                return ra
            if sa is not None:
                # self._logger.debug(f"读取本地 SA: {sa}")
                return sa
        rcd = await self.get(url=self._config.platform.alpha_info.format(alpha_id=alpha_id))
        assert isinstance(rcd, dict), "获取因子失败"
        if rcd["type"] == "SUPER":
            alpha = SuperAlpha.from_record(rcd)
            keys = SuperAlpha.get_keys_from_record(rcd)
            alpha_batch = await self.batch_update_or_create(
                [alpha], SuperAlpha, [k for k in keys if k not in ["id"]]
            )
        elif rcd["type"] == "REGULAR":
            alpha = RegularAlpha.from_record(rcd)
            keys = RegularAlpha.get_keys_from_record(rcd)
            alpha_batch = await self.batch_update_or_create(
                [alpha], RegularAlpha, [k for k in keys if k not in ["id"]]
            )
        else:
            raise ValueError(f"alpha type {rcd['type']} not supported")
        alpha_get = alpha_batch[0]
        self._logger.debug(f"在线加载因子: {alpha_get}")
        return alpha_get

    async def get_alphaset(
        self,
        region: Region | str | None = None,
        universe: Universe | str | None = None,
        delay: int | None = None,
        date_from: str | datetime | None = None,
        date_to: str | datetime | None = None,
        alpha_type: AlphaType | str | None = None,
        sharpe_from: float | None = None,
        sharpe_to: float | None = None,
        fitness_from: float | None = None,
        fitness_to: float | None = None,
        status: Status | str | None = None,
        tag: str | None = None,
        name: str | None = None,
        category: Category | str | None = None,
        color: Color | str | None = None,
        hidden: bool | None = None,
        force: bool = False,
        date_split: int | timedelta | None = None,
    ) -> AlphaSet:
        """获取因子集

        根据检索条件自动获取全量因子集, 自动读取全部分页, 单次因子集获取最大为 10000 条,
        为实现全量因子获取, 提供了按时间拆分任务的能力.

        同时基于检索条件和因子集属性, 自动从缓存中拉取已经冻结的因子集, 避免重复获取.

        Parameters
        ----------
        force : bool, default False
            强制更新
        date_split : int | timedelta | None, optional
            自动拆分, int 表示按天拆分, timedelta 表示按时间间隔拆分
        """
        dt_from = datetime.fromisoformat(date_from) if isinstance(date_from, str) else date_from
        dt_to = datetime.fromisoformat(date_to) if isinstance(date_to, str) else date_to

        if dt_from is not None and dt_from.tzinfo is None:
            dt_from = dt_from.replace(tzinfo=ZoneInfo(self._config.timezone))

        if dt_to is not None and dt_to.tzinfo is None:
            dt_to = dt_to.replace(tzinfo=ZoneInfo(self._config.timezone))

        alphaset = AlphaSet(
            region=region,
            universe=universe,
            delay=delay,
            date_from=dt_from,
            date_to=dt_to,
            alpha_type=alpha_type,
            sharpe_from=sharpe_from,
            sharpe_to=sharpe_to,
            fitness_from=fitness_from,
            fitness_to=fitness_to,
            status=status,
            tag=tag,
            name=name,
            category=category,
            color=color,
            hidden=hidden,
            user_id=(await self.get_user()).id,
        )

        hashcode = alphaset.hashing()
        alphaset_get = await AlphaSet.get_or_none(hashcode=hashcode)

        if alphaset_get is not None and alphaset_get.is_frozen and not force:
            self._logger.debug(f"获取存量因子集: {hashcode}, 共 {len(alphaset_get.alpha_ids)} 个因子")
            return alphaset_get

        alphaset.alpha_ids = []
        alphaset.n_regular = 0
        alphaset.n_super = 0

        # TimeSplit
        match date_split:
            case float() | int() as i if i > 0:
                dt_split = timedelta(days=i)
            case timedelta():
                dt_split = date_split
            case _:
                dt_split = None

        if dt_split is not None:
            dt_current = dt_from or self._config.begin_date
            while dt_current <= (dt_to or datetime.now(ZoneInfo(self._config.timezone))):
                alphaset_split = await self.get_alphaset(
                    alpha_type=alpha_type,
                    region=region,
                    universe=universe,
                    delay=delay,
                    status=status,
                    date_from=dt_current,
                    date_to=dt_current + dt_split,
                    sharpe_from=sharpe_from,
                    sharpe_to=sharpe_to,
                    fitness_from=fitness_from,
                    fitness_to=fitness_to,
                    tag=tag,
                    name=name,
                    category=category,
                    color=color,
                    date_split=None,
                    force=force,
                )
                alphaset.alpha_ids += alphaset_split.alpha_ids
                alphaset.n_regular += alphaset_split.n_regular
                alphaset.n_super += alphaset_split.n_super
                dt_current += dt_split
        else:
            self._logger.debug(f"在线加载因子集: From {date_from or 'Begin'} To {date_to or 'End'} ")
            records = await self.get_all(
                url=self._config.platform.alphaset_url,
                page_size=100,
                params=alphaset.to_params(),
            )
            alphaset = alphaset.update_from_record(records)

            # 顺便更新 RegularAlpha 和 SuperAlpha
            regular_records = [rcd for rcd in records if rcd["type"] == "REGULAR"]
            if len(regular_records) > 0:
                alpha_from_records = [RegularAlpha.from_record(rcd) for rcd in regular_records]
                alpha_ids_from_records = list(set([a.id for a in alpha_from_records]))
                _ = await self.batch_update_or_create(
                    [a for a in alpha_from_records if a.id in alpha_ids_from_records],
                    RegularAlpha,
                    fields=[
                        k for k in RegularAlpha.get_keys_from_record(regular_records[0]) if k not in ["id"]
                    ],
                )

            super_records = [rcd for rcd in records if rcd["type"] == "SUPER"]
            if len(super_records) > 0:
                alpha_from_records = [SuperAlpha.from_record(rcd) for rcd in super_records]
                alpha_ids_from_records = list(set([a.id for a in alpha_from_records]))
                _ = await self.batch_update_or_create(
                    [a for a in alpha_from_records if a.id in alpha_ids_from_records],
                    SuperAlpha,
                    fields=[k for k in SuperAlpha.get_keys_from_record(super_records[0]) if k not in ["id"]],
                )

        self._logger.debug(f"保存在线因子集, 共 {len(alphaset.alpha_ids)} 个因子")

        if alphaset_get is not None:
            alphaset_get.alpha_ids = alphaset.alpha_ids
            alphaset_get.n_regular = alphaset.n_regular
            alphaset_get.n_super = alphaset.n_super
            await alphaset_get.save()
        else:
            await alphaset.save()
        return alphaset

    async def get_pnl(self, alpha: str | SuperAlpha | RegularAlpha, force: bool = False) -> dict:
        """获取单个因子的 PNL 曲线"""
        if isinstance(alpha, str):
            alpha_ = await self.get_alpha(alpha)
            aid_ = alpha
        else:
            alpha_ = await self.get_alpha(alpha.id)
            aid_ = alpha.id

        if alpha_ is None:
            raise ValueError(f"因子不存在: {aid_}")

        if alpha_.pnl_raw is not None and not force:
            self._logger.debug(f"返回缓存 PNL: {alpha_.id}")
            return alpha_.pnl_raw

        self._logger.debug(f"加载在线 PNL: {alpha_.id}")
        pnl_records = await self.get(
            url=self._config.platform.alpha_pnl.format(alpha_id=alpha_.id), later=True
        )
        assert isinstance(pnl_records, dict)
        alpha_.pnl_raw = pnl_records
        await alpha_.save(update_fields=["pnl_raw"])
        return pnl_records

    async def get_pnls(self, alpha_ids: list[str], force: bool = False) -> dict[str, dict]:
        """并发获取多个因子的 PNL 曲线"""
        if len(alpha_ids) == 0:
            return {}

        if not force:
            cached_ra = {
                row["id"]: row["pnl_raw"]
                for row in await RegularAlpha.filter(Q(id__in=alpha_ids) & ~Q(pnl_raw=None)).values(
                    "id", "pnl_raw"
                )
            }
            cached_sa = {
                row["id"]: row["pnl_raw"]
                for row in await SuperAlpha.filter(Q(id__in=alpha_ids) & ~Q(pnl_raw=None)).values(
                    "id", "pnl_raw"
                )
            }
        else:
            cached_ra = {}
            cached_sa = {}

        online_alpha_ids = [aid for aid in alpha_ids if aid not in cached_ra and aid not in cached_sa]

        fetched_pnls = {}

        idx = 0
        total = len(online_alpha_ids)
        progress_lock = asyncio.Lock()

        async def _fetch(aid: str) -> None:
            async with self._sem:
                fetched_pnls[aid] = await self.get_pnl(aid, force=force)
                async with progress_lock:
                    nonlocal idx
                    idx += 1
                    self._logger.debug(f"盈亏数据获取进度: [{idx}/{total}]")

        if online_alpha_ids:
            self._logger.debug(f"在线加载 {len(online_alpha_ids)} 个 PNL")
            results = await asyncio.gather(*(_fetch(aid) for aid in online_alpha_ids), return_exceptions=True)
            for aid, res in zip(online_alpha_ids, results):
                if isinstance(res, Exception):
                    self._logger.warning(f"因子 {aid} 获取 PNL 失败: {res}")

        return {**cached_ra, **cached_sa, **fetched_pnls}

    async def get_stat(self, alpha: str | SuperAlpha | RegularAlpha, force: bool = False) -> dict:
        """获取单个因子的年化统计"""
        if isinstance(alpha, str):
            alpha_ = await self.get_alpha(alpha)
            aid_ = alpha
        else:
            alpha_ = await self.get_alpha(alpha.id)
            aid_ = alpha.id

        if alpha_ is None:
            raise ValueError(f"因子不存在: {aid_}")

        if alpha_.yearly_stats_raw is not None and not force:
            self._logger.debug(f"加载缓存年化统计: {aid_}")
            return alpha_.yearly_stats_raw

        self._logger.debug(f"在线获取年化统计: {aid_}")
        yearly_records = await self.get(
            url=self._config.platform.alpha_yearly_stats.format(alpha_id=alpha_.id),
            later=True,
        )
        assert isinstance(yearly_records, dict)
        alpha_.yearly_stats_raw = yearly_records
        await alpha_.save(update_fields=["yearly_stats_raw"])
        return alpha_.yearly_stats_raw

    async def get_stats(self, alpha_ids: list[str], force: bool = False) -> dict[str, dict]:
        """批量获取多个因子的年化统计"""
        if len(alpha_ids) == 0:
            return {}

        if not force:
            cached_ra = {
                row["id"]: row["yearly_stats_raw"]
                for row in await RegularAlpha.filter(Q(id__in=alpha_ids) & ~Q(yearly_stats_raw=None)).values(
                    "id", "yearly_stats_raw"
                )
            }
            cached_sa = {
                row["id"]: row["yearly_stats_raw"]
                for row in await SuperAlpha.filter(Q(id__in=alpha_ids) & ~Q(yearly_stats_raw=None)).values(
                    "id", "yearly_stats_raw"
                )
            }
        else:
            cached_ra = {}
            cached_sa = {}

        online_alpha_ids = [aid for aid in alpha_ids if aid not in cached_ra and aid not in cached_sa]

        fetched_stats = {}

        idx = 0
        total = len(online_alpha_ids)
        progress_lock = asyncio.Lock()

        async def _fetch(aid: str) -> None:
            async with self._sem:
                fetched_stats[aid] = await self.get_stat(aid, force=force)
                async with progress_lock:
                    nonlocal idx
                    idx += 1
                    self._logger.debug(f"年化统计数据获取进度: [{idx}/{total}]")

        if online_alpha_ids:
            self._logger.debug(f"在线加载 {len(online_alpha_ids)} 个年化统计数据")
            results = await asyncio.gather(*(_fetch(aid) for aid in online_alpha_ids), return_exceptions=True)
            for aid, res in zip(online_alpha_ids, results):
                if isinstance(res, Exception):
                    self._logger.warning(f"因子 {aid} 获取年化统计值失败: {res}")

        return {**cached_ra, **cached_sa, **fetched_stats}

    async def get_perf(self, alpha: str | SuperAlpha | RegularAlpha, force: bool = False) -> dict:
        """获取单个因子的提交前后表现"""
        if isinstance(alpha, str):
            alpha_ = await self.get_alpha(alpha)
            aid_ = alpha
        else:
            alpha_ = await self.get_alpha(alpha.id)
            aid_ = alpha.id

        if alpha_ is None:
            raise ValueError(f"因子不存在: {aid_}")

        if alpha_.combine_perf_raw is not None and not force:
            self._logger.debug(f"加载缓存表现: {aid_}")
            return alpha_.combine_perf_raw

        self._logger.debug(f"在线获取提交前后表现: {aid_}")
        combine_perf = await self.get(
            url=self._config.platform.alpha_perf.format(alpha_id=alpha_.id), later=True
        )
        assert isinstance(combine_perf, dict)
        alpha_.combine_perf_raw = combine_perf
        await alpha_.save(update_fields=["combine_perf_raw"])
        return alpha_.combine_perf_raw

    async def get_perfs(self, alpha_ids: list[str], force: bool = False) -> dict[str, dict]:
        """批量获取多个因子的提交前后表现

        该接口消耗服务端资源, 不会进行并发检索, 并且强制执行限速检查, 如果碰到限速会休眠.
        并且该数据与存量因子相关, 一般需要重新获取.
        """
        if len(alpha_ids) == 0:
            return {}

        if not force:
            cached_ra = {
                row["id"]: row["combine_perf_raw"]
                for row in await RegularAlpha.filter(Q(id__in=alpha_ids) & ~Q(combine_perf_raw=None)).values(
                    "id", "combine_perf_raw"
                )
            }
            cached_sa = {
                row["id"]: row["combine_perf_raw"]
                for row in await SuperAlpha.filter(Q(id__in=alpha_ids) & ~Q(combine_perf_raw=None)).values(
                    "id", "combine_perf_raw"
                )
            }
        else:
            cached_ra = {}
            cached_sa = {}

        online_alpha_ids = [aid for aid in alpha_ids if aid not in cached_ra and aid not in cached_sa]

        fetched_perfs = {}

        if len(online_alpha_ids) > 0:
            self._logger.debug(f"在线加载 {len(online_alpha_ids)} 个提交前后表现数据")

        async with httpx.AsyncClient(
            cookies=httpx.Cookies({"t": getattr(self._user, "cookie") or ""}),
            base_url=self._config.platform.base_url,
        ) as client:
            for idx, aid in enumerate(online_alpha_ids):
                res = await self.send_request(
                    client,
                    HTTPMethod.GET_LATER,
                    self._config.platform.alpha_perf.format(alpha_id=aid),
                )
                assert isinstance(res.content, dict)

                alpha_ = await self.get_alpha(aid)
                alpha_.combine_perf_raw = res.content
                await alpha_.save(update_fields=["combine_perf_raw"])
                fetched_perfs[aid] = res.content

                self._logger.debug(f"提交前后表现数据获取进度: [{idx + 1}/{len(online_alpha_ids)}]")

                ratelimit_remaining = res.raw.headers.get("ratelimit-remaining")
                ratelimit_reset = res.raw.headers.get("ratelimit-reset")

                if ratelimit_remaining is not None and ratelimit_reset is not None:
                    self._logger.debug(
                        f"获取 Combine Perf 剩余次数: {ratelimit_remaining}, 重置时间: {ratelimit_reset}"
                    )
                    if int(ratelimit_remaining) <= self._config.concurrency:
                        self._logger.info(f"获取 Combine Perf 剩余次数不足, 暂停等待重置: {ratelimit_reset}s")
                        await asyncio.sleep(int(ratelimit_reset))
        return {**cached_ra, **cached_sa, **fetched_perfs}

    async def get_prod_corr(self, alpha: str | SuperAlpha | RegularAlpha, force: bool = False) -> float:
        """获取单个因子的生产相关性"""
        if isinstance(alpha, str):
            alpha_ = await self.get_alpha(alpha)
            aid_ = alpha
        else:
            alpha_ = await self.get_alpha(alpha.id)
            aid_ = alpha.id

        if alpha_ is None:
            raise ValueError(f"因子不存在: {aid_}")

        if alpha_.prod_corr is not None and not force:
            self._logger.debug(f"加载缓存生产相关性: {aid_}")
            return alpha_.prod_corr

        self._logger.debug(f"在线获取生产相关性: {aid_}")
        prod_corr_record = await self.get(
            url=self._config.platform.alpha_corr.format(alpha_id=alpha_.id), later=True
        )
        assert isinstance(prod_corr_record, dict)
        alpha_.prod_corr_raw = prod_corr_record
        alpha_.prod_corr = prod_corr_record["max"]
        await alpha_.save(update_fields=["prod_corr_raw", "prod_corr"])
        return alpha_.prod_corr

    async def get_prods(
        self, alpha_ids: list[str], force: bool = False, threshold: float = 0.7
    ) -> dict[str, dict]:
        """批量获取多个因子的生产相关性

        该接口消耗服务端资源, 不会进行并发检索, 并且强制执行限速检查, 如果碰到限速会休眠.
        并且该数据与存量因子相关, 一般需要重新获取.
        """
        if len(alpha_ids) == 0:
            return {}

        if not force:
            cached_ra = {
                row["id"]: row["prod_corr"]
                for row in await RegularAlpha.filter(Q(id__in=alpha_ids) & ~Q(prod_corr=None)).values(
                    "id", "prod_corr"
                )
            }
            cached_sa = {
                row["id"]: row["prod_corr"]
                for row in await SuperAlpha.filter(Q(id__in=alpha_ids) & ~Q(prod_corr=None)).values(
                    "id", "prod_corr"
                )
            }
        else:
            cached_ra = {}
            cached_sa = {}

        online_alpha_ids = [aid for aid in alpha_ids if aid not in cached_ra and aid not in cached_sa]

        fetched_perfs = {}

        if len(online_alpha_ids) > 0:
            self._logger.debug(f"在线加载 {len(online_alpha_ids)} 个生产相关性")

        async with httpx.AsyncClient(
            cookies=httpx.Cookies({"t": getattr(self._user, "cookie") or ""}),
            base_url=self._config.platform.base_url,
        ) as client:
            for idx, aid in enumerate(online_alpha_ids):
                alpha_ = await self.get_alpha(aid)
                if alpha_ is not None and alpha_.prod_corr > threshold:
                    self._logger.debug(f"{alpha_} 生产相关性超过 {threshold}, 跳过更新")
                    fetched_perfs[aid] = alpha_.prod_corr
                    continue

                res = await self.send_request(
                    client,
                    HTTPMethod.GET_LATER,
                    self._config.platform.alpha_corr.format(alpha_id=aid),
                )
                assert isinstance(res.content, dict)

                alpha_ = await self.get_alpha(aid)
                alpha_.prod_corr_raw = res.content
                alpha_.prod_corr = res.content["max"]
                await alpha_.save(update_fields=["prod_corr_raw", "prod_corr"])
                fetched_perfs[aid] = res.content["max"]

                self._logger.debug(f"生产相关性获取进度: [{idx + 1}/{len(online_alpha_ids)}]")

                ratelimit_remaining = res.raw.headers.get("ratelimit-remaining")
                ratelimit_reset = res.raw.headers.get("ratelimit-reset")

                if ratelimit_remaining is not None and ratelimit_reset is not None:
                    self._logger.debug(
                        f"获取 Prod-Corr 剩余次数: {ratelimit_remaining}, 重置时间: {ratelimit_reset}"
                    )
                    if int(ratelimit_remaining) <= self._config.concurrency:
                        self._logger.info(f"获取 Prod-Corr 剩余次数不足, 暂停等待重置: {ratelimit_reset}s")
                        await asyncio.sleep(int(ratelimit_reset))
        return {**cached_ra, **cached_sa, **fetched_perfs}

    async def update_alpha(
        self,
        alpha: str | SuperAlpha | RegularAlpha,
        name: str | None = None,
        category: Category | None = None,
        description: str | None = None,
        description_combo: str | None = None,
        description_selection: str | None = None,
        color: Color | None = None,
        tags: list[str] | str | None = None,
        hidden: bool | None = None,
        favorite: bool | None = None,
        force: bool = False,
    ) -> RegularAlpha | SuperAlpha:
        if isinstance(alpha, str):
            alpha_ = await self.get_alpha(alpha)
            aid_ = alpha
        else:
            alpha_ = await self.get_alpha(alpha.id)
            aid_ = alpha.id

        if alpha_ is None:
            raise ValueError(f"因子不存在: {aid_}")

        if favorite is None:
            favorite = alpha_.favorite

        if isinstance(alpha_, RegularAlpha):
            prop_field = [
                "name",
                "category",
                "description",
                "color",
                "hidden",
                "favorite",
            ]
            prop = [name, category, description, color, hidden, favorite]
        elif isinstance(alpha_, SuperAlpha):
            prop_field = [
                "name",
                "category",
                "description_combo",
                "description_selection",
                "color",
                "hidden",
                "favorite",
            ]
            prop = [
                name,
                category,
                description_combo,
                description_selection,
                color,
                hidden,
                favorite,
            ]
        else:
            raise TypeError(f"未知的 Alpha 类型: {type(alpha_)}")

        _send = False
        for pf, p in zip(prop_field, prop):
            alpha_p = getattr(alpha_, pf)
            _rule_1 = (p is None) and (alpha_p is not None) and force  # 使用空值覆盖
            _rule_2 = (p is not None) and (alpha_p != p)  # 使用 p 填充
            if _rule_1 or _rule_2:
                _send = True
                setattr(alpha_, pf, p)

        if tags is None and force:
            if len(alpha_.tags) > 0:
                alpha_.tags = []
                _send = True
        elif isinstance(tags, str):
            if tags not in alpha_.tags and not force:
                alpha_.tags.append(tags)
                _send = True
            elif force:
                alpha_.tags = [tags]
                _send = True
        elif isinstance(tags, list) and set(tags) != set(alpha_.tags):
            _send = True
            if force:
                alpha_.tags = tags
            else:
                alpha_.tags = list(set(alpha_.tags) | set(tags))

        if _send:
            _ = await self.patch(
                url=self._config.platform.alpha_info.format(alpha_id=aid_),
                payload=alpha_.to_description(),
            )
            await alpha_.save(update_fields=prop_field)

        return alpha_

    async def _sim_and_get_result(self, payload: JSONLike) -> JSONLike | None:
        """提交回测&获取结果"""

        if isinstance(payload, list) and len(payload) == 1:
            resp = await self.post(url=self._config.platform.simulation_url, payload=payload[0])
        else:
            resp = await self.post(url=self._config.platform.simulation_url, payload=payload)
        if resp.raw.headers.get("location") is None:
            self._logger.error(f"回测启动失败: {resp.content}")
            return None

        simid = resp.raw.headers.get("location").split("/")[-1]
        self._logger.debug(f"回测已启动: {simid}")

        progress = 0.0
        while True:
            sim_result = await self.get(f"{self._config.platform.simulation_url}/{simid}")
            assert isinstance(sim_result, dict)
            if (_progress := sim_result.get("progress")) is not None:
                if _progress != progress:
                    progress = _progress
                    self._logger.debug(f"Simulation({simid}) 进度: {progress:.0%}")
                await asyncio.sleep(self._config.retry_delay)
            else:
                break

        ratelimit_remaining = resp.raw.headers.get("x-ratelimit-remaining")
        ratelimit_reset = resp.raw.headers.get("x-ratelimit-reset")
        if ratelimit_remaining is not None and ratelimit_reset is not None:
            self._logger.debug(
                f"回测剩余次数: {ratelimit_remaining}, 重置时间: {int(ratelimit_reset) / 3600:.2f} Hours"
            )
            if int(ratelimit_remaining) < 20:
                await self.notify(message="回测剩余次数不足10次, 系统休眠", title="Niffler Warning")
                self._logger.info("回测剩余次数不足10次, 系统休眠")
                await asyncio.sleep(int(ratelimit_reset) + self._config.retry_delay)

        if "children" in sim_result:
            # multi-sim regular alpha
            sim_result_all = [
                await self.get(f"{self._config.platform.simulation_url}/{sid}")
                for sid in sim_result["children"]
            ]

            if sim_result["status"] != "COMPLETE":
                error_sims = filter(
                    lambda x: x is not None and isinstance(x, dict) and x["status"] == "ERROR",
                    sim_result_all,
                )
                for es in error_sims:
                    if es is not None and isinstance(es, dict):
                        self._logger.error(f"回测 {es['id']} 失败: {es['message']}")
                return None
            return sim_result_all
        else:
            if sim_result["status"] != "COMPLETE":
                self._logger.error(f"Simulation({simid}) 失败: {sim_result['message']}")
                return None
            return sim_result

    async def _sim_post_process(self, simulation_result: list[Simulation] | Simulation) -> None:
        """回测后处理"""
        if not isinstance(simulation_result, list):
            simulation_result = [simulation_result]

        for sim_rst in simulation_result:
            if sim_rst.alpha_id is None:
                self._logger.warning(f"回测未完成, 无法更新 Alpha 信息: {sim_rst}")
                continue
            try:
                _ = await self.update_alpha(
                    alpha=sim_rst.alpha_id,
                    name=sim_rst.name,
                    category=sim_rst.category,
                    description=sim_rst.description,
                    description_combo=sim_rst.description_combo,
                    description_selection=sim_rst.description_selection,
                    color=sim_rst.color,
                    tags=sim_rst.tags,
                    hidden=sim_rst.hidden,
                    favorite=sim_rst.favorite,
                )
            except Exception:
                self._logger.exception(f"更新 Alpha({sim_rst.alpha_id}) 失败")

    @overload
    async def simulate(self, simulation: Simulation) -> Simulation: ...
    @overload
    async def simulate(self, simulation: list[Simulation], batch_size: int = 10) -> list[Simulation]: ...
    async def simulate(
        self, simulation: Simulation | list[Simulation], batch_size: int = 10
    ) -> Simulation | list[Simulation]:
        """完整回测接口

        支持单回测和批量回测, 批量回测可以配置批大小, 全部回测完成后返回.
        根据回测的哈希值自动召回回测, 防止重复计算, 不提供 force 参数, 回测不需要强制重复.
        支持 RA 和 SA, 但是需要满足平台要求:
        - RA 批量回测时 Region / Universe / delay 必须一致
        - SA 不支持批量回测, batch_size 必须为 1
        接口不处理回测不满足平台要求的情况, 服务器会返回报错信息.
        """
        if isinstance(simulation, list):
            sim_all = simulation
            is_batch = True
        else:
            sim_all = [simulation]
            is_batch = False

        sim_cache = []
        sim_new = []
        for sim in sim_all:
            simhash = sim.hashing()
            sim_get = await Simulation.get_or_none(hashcode=simhash)
            if sim_get is None:
                sim_new.append(sim)
            else:
                sim_cache.append(sim_get)

        if len(sim_new) > 0:
            self._logger.debug(f"新增回测 {len(sim_new)} 个, 存量回测 {len(sim_cache)} 个")
        else:
            self._logger.debug(f"存量回测 {len(sim_cache)} 个")
            return sim_cache if is_batch else sim_cache[0]

        nbatch = ceil(len(sim_new) / batch_size)
        sim_result_all = []
        for batch_id, sim_batch in enumerate(batched(sim_new, batch_size)):
            sim_result = []
            self._logger.debug(f"[{batch_id + 1}/{nbatch}] - 开始执行 {len(sim_batch)} 个回测")
            payload = [sim.to_payload() for sim in sim_batch]
            sim_rst_batch = await self._sim_and_get_result(payload)
            if sim_rst_batch is None:
                continue
            elif isinstance(sim_rst_batch, list):
                for sim, rst in zip(sim_batch, sim_rst_batch):
                    sim_add, _ = await Simulation.update_or_create(
                        hashcode=sim.hashing(),
                        defaults={
                            "simid": rst["id"],
                            "alpha_id": rst["alpha"],
                            **{
                                f: getattr(sim, f)
                                for f in sim._meta.fields
                                if f
                                not in [
                                    "simid",
                                    "alpha_id",
                                    "hashcode",
                                    "created_at",
                                    "updated_at",
                                    "id",
                                ]
                                # FIXME: 丧失了拓展性, 下次迭代 Simulation 对象时修改这块内容
                            },
                        },
                    )
                    sim_result.append(sim_add)
            else:
                sim = sim_batch[0]
                sim_add, _ = await Simulation.update_or_create(
                    hashcode=sim.hashing(),
                    defaults={
                        "simid": sim_rst_batch["id"],
                        "alpha_id": sim_rst_batch["alpha"],
                        **{
                            f: getattr(sim, f)
                            for f in sim._meta.fields
                            if f
                            not in [
                                "simid",
                                "alpha_id",
                                "hashcode",
                                "created_at",
                                "updated_at",
                                "id",
                            ]
                        },
                    },
                )
                sim_result.append(sim_add)
            sim_result_all.extend(sim_result)
            self._logger.debug(
                f"[{batch_id + 1}/{nbatch}] - 回测完成, 成功执行 {len(sim_result)} 个回测, 开始进行因子更新"
            )
            await self._sim_post_process(sim_result)

        if is_batch:
            return sim_result_all
        elif not is_batch and len(sim_result_all) == 1:
            return sim_result_all[0]
        else:
            raise ValueError("回测结果错误")

    async def _get_active_pnls(self, region: Region | str, force: bool = False) -> dict:
        cache_key = f"{Region(region).value}_active_pnls"

        if self._cache.get(cache_key) is not None and not force:
            return self._cache[cache_key]

        activate_alphaset = await self.get_alphaset(region=region, status=Status.ACTIVE)
        pnls = await self.get_pnls(alpha_ids=activate_alphaset.alpha_ids)

        self._cache[cache_key] = pnls
        return self._cache[cache_key]

    async def get_self_corr(self, alpha: str | SuperAlpha | RegularAlpha, force: bool = False) -> float:
        """获取单个因子的自相关性"""
        if isinstance(alpha, str):
            alpha_ = await self.get_alpha(alpha)
            aid_ = alpha
        else:
            alpha_ = await self.get_alpha(alpha.id)
            aid_ = alpha.id

        if alpha_ is None:
            raise ValueError(f"因子不存在: {aid_}")

        if alpha_.self_corr is not None and not force:
            return alpha_.self_corr

        self._logger.debug(f"重新计算自相关性: {aid_}")
        activate_pnls = await self._get_active_pnls(alpha_.region)
        alpha_pnl = await self.get_pnl(alpha=aid_)

        pnls_all = parse_record(alpha_pnl).select(["date", "pnl"]).rename({"pnl": aid_})

        for aid, a_pnl in activate_pnls.items():
            pnls_all = pnls_all.join(
                parse_record(a_pnl).select(["date", "pnl"]).rename({"pnl": aid}),
                how="left",
                on=["date"],
            ).select(pl.selectors.exclude(["date_right"]))

        max_date = pnls_all["date"].max()
        assert isinstance(max_date, date)
        begin_date = pl.date(year=max_date.year - 4, month=max_date.month, day=max_date.day)

        pnls_all = pnls_all.with_columns(
            *[
                pl.col(p) - pl.col(p).fill_null(strategy="forward").shift(1)
                for p in pnls_all.columns
                if p != "date"
            ],
        ).filter(pl.col("date") > begin_date)

        self_corr = (
            pnls_all.select(pl.selectors.exclude(["date"]))
            .fill_null(0)
            .corr()
            .with_columns(alpha=pl.Series(pnls_all.select(pl.selectors.exclude(["date"])).columns))
            .select(["alpha", aid_])
            .sort(aid_, descending=True)
            .filter(pl.col("alpha") != aid_)
        )
        self_corr_raw = dict(zip(*self_corr))
        alpha_.self_corr_raw = self_corr_raw
        alpha_.self_corr = self_corr[aid_][0]
        await alpha_.save(update_fields=["self_corr_raw", "self_corr"])
        return alpha_.self_corr
