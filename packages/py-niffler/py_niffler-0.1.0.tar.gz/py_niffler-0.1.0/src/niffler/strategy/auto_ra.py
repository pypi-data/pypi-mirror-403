"""顾问课策略模版 - 三阶段策略

阶段零: 数据预处理
  - winsorize(ts_backfill(field, 120), std=4)
阶段一: 单字段基础运算 Consultant101 STEP1
  - 横截面+时序
  - 因子反转
  - 增加 Decay
    - (0.7, ∞) -> x4
    - (0.6, 0.7] -> x3+3
    - (0.5, 0.6] -> x3
    - (0.4, 0.5] -> x2
    - (0.35, 0.4] -> +4
    - (0.3, 0.35] -> +2
阶段二: 组优化 Consultant101 STEP2
  - group_op(signal, group)
阶段三: 因子择时 Consultant101 STEP3
  - trade_when(open, signal, close)
"""

import random
from pathlib import Path
from typing import Literal, Self

from ..config import NifflerConfig
from ..enums import Neutralization, Region, SimulationType, Switch, Universe
from ..models import RegularAlpha, Simulation, SuperAlpha
from .__proto__ import NifflerStrategy


class Consultant101(NifflerStrategy):
    def __init__(
        self,
        name: str,
        config: NifflerConfig | str | Path | dict | None = None,
        batch_size: int = 10,
        slots: int = 8,
        priority_prob: float = 1,
        timeout: int = 5,
        verbose: int = 0,
        max_count: int | None = None,
    ) -> None:
        super().__init__(
            name=name,
            config=config,
            batch_size=batch_size,
            slots=slots,
            priority_prob=priority_prob,
            timeout=timeout,
            verbose=verbose,
            max_count=max_count,
        )
        self._sim_pool = []
        self._groups = []

    async def setup(
        self,
        region: Region | str,
        universe: Universe | str,
        delay: Literal[0, 1],
        dataset_id: str,
        backfill: int = 66,
        winsorize: int = 4,
        days: list[int] = [22],
        date_coverage: float = 1.0,
        universe_converage: float = 0.8,
        truncation: float = 0.08,
        decay: int = 6,
        neutralization: Neutralization | str = Neutralization.SUBINDUSTRY,
        max_trade: Switch | str = Switch.OFF,
        test_period: str = "P3Y6M",
    ) -> Self:
        await super().setup()

        self.days = days

        datafields = await self.client.get_datafields(
            region=region, universe=universe, delay=delay, dataset_id=dataset_id
        )

        vector_fields = list(filter(lambda x: x["type"] == "VECTOR", datafields))
        matrix_fields = list(filter(lambda x: x["type"] == "MATRIX", datafields))
        group_fields = list(filter(lambda x: x["type"] == "GROUP", datafields))

        self._logger.info(f"原始向量字段数: {len(vector_fields)}")
        self._logger.info(f"原始矩阵字段数: {len(matrix_fields)}")
        self._logger.info(f"原始组字段数: {len(group_fields)}")

        if len(group_fields) >= 5:
            self._logger.info("组字段超过 5 个, 只保留因子数最多的 5 个")
            group_fields = sorted(group_fields, key=lambda x: x["alphaCount"], reverse=True)[:5]

        vector_fields = list(
            filter(
                lambda x: (x["dateCoverage"] or 1.0) >= date_coverage
                and (x["coverage"] or 1.0) >= universe_converage,
                vector_fields,
            )
        )
        matrix_fields = list(
            filter(
                lambda x: (x["dateCoverage"] or 1.0) >= date_coverage
                and (x["coverage"] or 1.0) >= universe_converage,
                matrix_fields,
            )
        )
        self._logger.info(f"覆盖度过滤后向量字段数: {len(vector_fields)}")
        self._logger.info(f"覆盖度过滤后矩阵字段数: {len(group_fields)}")

        self._groups += [
            "market",
            "sector",
            "industry",
            "subindustry",
        ]

        if region in ["ASI", "GLB", "EUR"]:
            self._groups += ["country", "currency"]

        fields_all = list(map(lambda x: x["id"], matrix_fields)) + [
            f"{group_op}({field['id']})"
            for field in vector_fields
            for group_op in ["vec_max", "vec_avg", "vec_count", "vec_stddev", "vec_sum"]
        ]
        signals = [f"winsorize(ts_backfill({field}, {backfill}), std={winsorize})" for field in fields_all]
        self._logger.info(f"基础字段个数: {len(signals)}")

        operators = await self.client.get_operators()
        self.operators = [op["name"] for op in operators]

        signals += self.blind_transform(signals)
        random.shuffle(signals)
        self._logger.info(f"一阶拓展因子数: {len(signals)}")

        self._sim_pool += [
            Simulation(
                name=f"Consultant101-{dataset_id}",
                region=region,
                universe=universe,
                delay=delay,
                simulation_type=SimulationType.REGULAR,
                truncation=truncation,
                neutralization=neutralization,
                max_trade=max_trade,
                test_period=test_period,
                visualization=True,
                decay=decay,
                expr=e,
                tags=["Consultant101", "STEP1"],
            )
            for e in signals
        ]

        return self

    async def _produce(self) -> Simulation | None:
        if len(self._sim_pool) > 0:
            return self._sim_pool.pop(0)
        else:
            return None

    def blind_transform(self, fields: list[str]) -> list[str]:
        basic_ops = ["log", "rank", "zscore", "quantile"]
        ts_ops = [
            "ts_rank",
            "ts_zscore",
            "ts_delta",
            "ts_sum",
            "ts_product",
            "ts_ir",
            "ts_std_dev",
            "ts_mean",
            "ts_arg_min",
            "ts_arg_max",
            "ts_returns",
            "ts_scale",
            "ts_kurtosis",
            "ts_quantile",
        ]
        signals = []
        for field in fields:
            signals += [f"{op}({field})" for op in basic_ops]
            signals += [f"{op}({field}, {d})" for op in ts_ops for d in self.days]

        random.shuffle(signals)
        return signals

    async def _feedback(self, alpha: RegularAlpha | SuperAlpha) -> None:
        assert isinstance(alpha, RegularAlpha), "Consultant101 只支持 RegularAlpha"
        if alpha.is_longcnt < 100 or alpha.is_shortcnt < 100:
            return
        if alpha.is_sharpe < -0.8:
            reverse_sim = self._feedback_reverse(alpha)
            for sim in reverse_sim:
                await self.add_priority_simulation(sim, 99)
            return
        if alpha.is_sharpe < 0.8:
            self._logger.debug(f"{alpha} 跳过")
            return

        self._logger.debug(f"Feedback {alpha} Tags: {alpha.tags}")
        decay = alpha.decay
        # Decay
        if alpha.is_turnover > 0.7:
            decay *= 4
        elif alpha.is_turnover > 0.6:
            decay = decay * 3 + 3
        elif alpha.is_turnover > 0.5:
            decay *= 3
        elif alpha.is_turnover > 0.4:
            decay *= 2
        elif alpha.is_turnover > 0.35:
            decay += 4
        elif alpha.is_turnover > 0.3:
            decay += 2

        if "STEP1" in alpha.tags:
            group_sims = self._feedback_group(alpha, decay)
            for sim in group_sims:
                await self.add_priority_simulation(sim, 2)
        elif "STEP2" in alpha.tags and alpha.is_sharpe > 1.3 and alpha.is_fitness > 0.75:
            timing_sims = self._feedback_timing(alpha, decay)
            for sim in timing_sims:
                await self.add_priority_simulation(sim, 3)

    def _feedback_group(self, alpha: RegularAlpha, decay: int | None = None) -> list[Simulation]:
        group_op = ["group_neutralize", "group_rank", "group_scale", "group_zscore"]
        if decay is None:
            decay = alpha.decay

        expr_raw = alpha.expr
        sims = []
        for op in group_op:
            for g in self._groups:
                expr_lines = expr_raw.strip().split(";")
                expr_lines[-1] = f"{op}({expr_lines[-1].strip()}, {g})"
                expr = ";\n".join([line.strip() for line in expr_lines])
                sims += [
                    Simulation(
                        **{
                            **alpha.to_simulation(),
                            "expr": expr,
                            "decay": decay,
                            "tags": ["Consultant101", "STEP2"],
                        }
                    )
                ]
        return sims

    def _feedback_timing(self, alpha: RegularAlpha, decay: int | None = None) -> list[Simulation]:
        open_events = [
            "ts_arg_max(volume, 5) == 0",
            "ts_corr(close, volume, 20) < 0",
            "ts_corr(close, volume, 5) < 0",
            "ts_mean(volume,10)>ts_mean(volume,60)",
            "group_rank(ts_std_dev(returns,60), sector) > 0.7",
            "ts_zscore(returns,60) > 2",
        ]
        close_events = ["-1", "abs(returns) > 0.3"]
        if decay is None:
            decay = alpha.decay

        expr_raw = alpha.expr
        sims = []
        for open_e in open_events:
            for close_e in close_events:
                expr_lines = expr_raw.strip().split(";")
                expr_lines[-1] = f"trade_when({open_e}, {expr_lines[-1].strip()}, {close_e})"
                expr = ";\n".join([line.strip() for line in expr_lines])
                sims += [
                    Simulation(
                        **{
                            **alpha.to_simulation(),
                            "expr": expr,
                            "decay": decay,
                            "tags": ["Consultant101", "STEP3"],
                        }
                    )
                ]
        return sims
