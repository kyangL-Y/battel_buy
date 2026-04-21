from __future__ import annotations

from typing import Callable

from utils.logger import setup_logger

logger = setup_logger()


def run_interval(job: Callable[[], None], interval_seconds: int) -> None:
    """使用 APScheduler 按固定间隔执行任务（BlockingScheduler，阻塞当前进程）。

    优先使用 APScheduler；若未安装则降级为简单 time.sleep 循环。
    """
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: PLC0415

        scheduler = BlockingScheduler(timezone="Asia/Shanghai")
        scheduler.add_job(
            job,
            trigger="interval",
            seconds=interval_seconds,
            max_instances=1,
            coalesce=True,
        )
        logger.info("APScheduler 启动，间隔 %s 秒执行抓取任务", interval_seconds)
        # 立即执行一次，再按间隔调度
        try:
            job()
        except Exception as exc:  # noqa: BLE001
            logger.exception("首次执行失败: %s", exc)

        scheduler.start()

    except ImportError:
        import time

        logger.warning("APScheduler 未安装，降级为 time.sleep 循环。建议执行: pip install apscheduler")
        logger.info("简单定时循环启动，间隔 %s 秒", interval_seconds)
        while True:
            try:
                job()
            except Exception as exc:  # noqa: BLE001
                logger.exception("定时任务执行失败: %s", exc)
            time.sleep(interval_seconds)
