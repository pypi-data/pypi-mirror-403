import asyncio
import logging
import math
import random
import signal
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Self

from ..client import NifflerClient
from ..config import NifflerConfig
from ..models import RegularAlpha, Simulation, SuperAlpha


class NifflerStrategy(metaclass=ABCMeta):
    """策略抽象类

    主要实现了策略的执行能力, 策略具体内容需要在继承类中实现.

    Notes
    -----
    生产者: 生成任务并推送到 task_queue
    消费者: 消费 task_queue 中的任务, 并将结果推送至 result_queue
    分解者: 从 result_queue 中获取任务, 并执行收尾工作
    """

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
        self._logger = logging.getLogger(__name__)

        self.name = name
        self.slots = slots
        self.batch_size = batch_size
        self.priority_prob = priority_prob
        self.timeout = timeout
        self.client = NifflerClient(config)
        self.verbose = verbose
        self._verbose_pin = verbose if verbose > 0 else math.inf
        self.max_count = max_count or math.inf

        self._task_queue: asyncio.Queue[Simulation] = asyncio.Queue(maxsize=self.slots * self.batch_size * 2)
        self._result_queue: asyncio.Queue[Simulation] = asyncio.Queue()
        self._priority_queue: asyncio.PriorityQueue[tuple[int, Simulation]] = asyncio.PriorityQueue()

        self._terminated_e = asyncio.Event()  # 任务终止
        self._hang_e = [asyncio.Event() for _ in range(self.slots)]
        self._count = [0 for _ in range(self.slots)]  # 每个执行器完成数量
        self._result = []

    async def setup(self) -> Self:
        await self.client.setup()
        return self

    async def close(self) -> None:
        await self.client.close()

    @property
    def finished(self) -> bool:
        for e in self._hang_e:
            if not e.is_set():
                return False
        return True

    def terminate(self) -> None:
        self._logger.info("任务终止流程启动")
        self._terminated_e.set()
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def producer(self) -> None:
        """生产者"""
        self._logger.info("生产者初始化")

        while not self._terminated_e.is_set():
            if (not self._priority_queue.empty()) and (random.random() <= self.priority_prob):
                _, task = self._priority_queue.get_nowait()
            else:
                task = await self._produce()

            if task is None:
                await asyncio.sleep(self.timeout)
                continue
            # self._logger.debug(f"已获取新任务, 开始检查任务缓存: {task}")
            sim_hashget = await Simulation.get_or_none(hashcode=task.hashing())
            if sim_hashget is not None:
                # self._logger.debug(f"跳过已回测的任务: {task}")
                task.simid = sim_hashget.simid
                task.alpha_id = sim_hashget.alpha_id
                # await self.feedback(sim_hashget) feedback 放在 consumer 中
                await self._result_queue.put(task)
                continue
            else:
                self._logger.debug(f"创建新任务: {task}")
                await self._task_queue.put(task)

        self._logger.info("生产者终止")

    async def consumer(self, consumer_idx: int = 0) -> None:
        """消费者"""
        self._logger.info(f"消费者[{consumer_idx}]初始化")

        batch: list[Simulation] = []
        consumer_count = 0
        while not self._terminated_e.is_set():
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=self.timeout)
                batch_encode = [t.hashing() for t in batch]
                if task.hashing() in batch_encode:
                    self._logger.debug(f"跳过重复的任务: {task}")
                    continue
                batch.append(task)
                self._hang_e[consumer_idx % self.slots].clear()  # 取消挂起状态
                if len(batch) < self.batch_size:
                    continue
            except asyncio.TimeoutError:
                if len(batch) == 0:
                    self._hang_e[consumer_idx % self.slots].set()  # 无任务可执行, 直接挂起
                    self._logger.debug(f"执行器[{consumer_idx}]已挂起")
                    await asyncio.sleep(self.timeout)
                    continue

            self._logger.debug(f"消费者[{consumer_idx}]开始执行回测")
            try:
                payload = [t.to_payload() for t in batch]
                sim_result = await self.client._sim_and_get_result(payload)
                if sim_result is None:
                    self._logger.error(f"回测失败: {payload}")
                    raise ValueError("回测失败")
                consumer_count += len(batch)
                self._count[consumer_idx % self.slots] = consumer_count
                self._logger.info(f"消费者[{consumer_idx}]完成任务: {consumer_count}")
                if isinstance(sim_result, list):
                    for sim, rst in zip(batch, sim_result):
                        sim_add, _ = await Simulation.update_or_create(
                            hashcode=sim.hashing(),
                            defaults={"simid": rst["id"], "alpha_id": rst["alpha"]},
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
                        )
                        # await self.feedback(sim_add)
                        await self._result_queue.put(sim_add)
                else:
                    sim = batch[0]
                    sim_add, _ = await Simulation.update_or_create(
                        hashcode=sim.hashing(),
                        defaults={
                            "simid": sim_result["id"],
                            "alpha_id": sim_result["alpha"],
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
                    # await self.feedback(sim_add)
                    await self._result_queue.put(sim_add)
                batch = []
                if sum(self._count) >= self.max_count:
                    self._logger.info(
                        f"当前回测量 {sum(self._count)} 已达到最大回测量 {self.max_count} 系统提前终止"
                    )
                    self.terminate()
                    break
            except Exception:
                self._logger.exception(f"消费者[{consumer_idx}]任务失败")
                batch = []

        self._hang_e[consumer_idx % self.slots].set()
        self._logger.info(f"消费者[{consumer_idx}]终止")

    async def decomposer(self) -> None:
        """分解者"""
        self._logger.info("分解者初始化")
        while True:
            if sum(self._count) > self._verbose_pin:
                _message = f"已完成任务 {sum(self._count)} 个"
                self._logger.info(_message)
                await self.client.notify(message=_message, title=f"Strategy {self.name}", group="Simulation")
                self._verbose_pin = (sum(self._count) // self.verbose + 1) * self.verbose
            try:
                sim_rst = await asyncio.wait_for(self._result_queue.get(), timeout=self.timeout)
                _ = await self.client._sim_post_process(sim_rst)
                await self.feedback(sim_rst)
            except asyncio.TimeoutError:
                if self.finished:
                    # 所有消费者都已挂起
                    self._logger.info("任务已结束")
                    self.terminate()
                    break
                else:
                    await asyncio.sleep(self.timeout)
            except Exception:
                self._logger.exception("分解者异常")
        self._logger.info("分解者终止")

    async def run(self) -> None:
        self._logger.info(f"开始执行策略: {self.name}")
        loop = asyncio.get_running_loop()

        def _on_sigint():
            self._logger.warning("强制终止任务, 正在清理资源...")
            loop.remove_signal_handler(signal.SIGINT)
            loop.remove_signal_handler(signal.SIGTERM)
            self.terminate()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _on_sigint)

        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(self.producer(), name="producer")
            for i in range(self.slots):
                task_group.create_task(self.consumer(i), name=f"consumer-{i}")
            task_group.create_task(self.decomposer(), name="finisher")

        message = f"策略执行完成, 任务总计 {sum(self._count)} 个"
        self._logger.info(message)
        await self.client.notify(message=message, title=f"Strategy {self.name}", group="Simulation")
        await self.close()

    async def briefing(self) -> str:
        raise NotImplementedError("回测简报")  # TODO

    @abstractmethod
    async def _produce(self) -> Simulation | None: ...

    async def feedback(self, simulation: Simulation | None = None) -> None:
        if simulation is not None and simulation.alpha_id is not None:
            alpha = await self.client.get_alpha(simulation.alpha_id, force=True)
            self._result.append(alpha)
            await self._feedback(alpha)
        else:
            self._logger.warning("回测结果异常")

    @abstractmethod
    async def _feedback(self, alpha: RegularAlpha | SuperAlpha) -> None: ...

    def _feedback_reverse(self, alpha: RegularAlpha) -> list[Simulation]:
        expr = alpha.expr

        expr_lines = expr.strip().split(";")
        expr_lines[-1] = f"-({expr_lines[-1].strip()})"
        expr = ";\n".join([line.strip() for line in expr_lines])

        sim = Simulation(**{**alpha.to_simulation(), "expr": expr})
        return [sim]

    async def add_priority_simulation(self, simulation: Simulation, priority: int = 0) -> None:
        await self._priority_queue.put((priority, simulation))
        self._logger.debug(f"新增优先任务(Lv.{priority}) {simulation}")
