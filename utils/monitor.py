"""测试过程监测

通过 pytest 钩子收集用例执行状态，实时打印进度并最终汇总为 summary.json。
设计为单例 Monitor，在 conftest.py 中注入：
    monitor.on_start(nodeid)
    monitor.on_finish(nodeid, status, duration)
    monitor.write_summary()
"""
import json
import os
import time

from utils.log_utils import get_logger

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Monitor:
    """测试执行过程监测器（单例）。"""

    def __init__(self, summary_file: str = None, realtime_print: bool = True):
        self.summary_file = summary_file or os.path.join(BASE_DIR, "reports", "summary.json")
        self.realtime_print = realtime_print
        self.records = []          # 每条用例记录
        self.counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "rerun": 0}
        self.start_time = time.time()

    # ---------- 记录接口 ----------
    def on_start(self, nodeid: str) -> None:
        self.records.append({"nodeid": nodeid, "status": "running", "start": time.time()})
        if self.realtime_print:
            logger.info(f"[开始] {nodeid}")

    def on_finish(self, nodeid: str, status: str, duration: float, error: str = "") -> None:
        # 更新最后一条匹配记录
        for rec in reversed(self.records):
            if rec["nodeid"] == nodeid and rec["status"] == "running":
                rec["status"] = status
                rec["duration"] = round(duration, 3)
                rec["error"] = error
                break
        if status in self.counts:
            self.counts[status] += 1
        if self.realtime_print:
            tag = {"passed": "通过", "failed": "失败", "skipped": "跳过", "error": "错误"}.get(status, status)
            logger.info(f"[{tag}] {nodeid}  耗时={duration:.2f}s")

    # ---------- 汇总 ----------
    def write_summary(self) -> str:
        os.makedirs(os.path.dirname(self.summary_file), exist_ok=True)
        total = len(self.records)
        duration = round(time.time() - self.start_time, 2)
        summary = {
            "total": total,
            "counts": self.counts,
            "duration_seconds": duration,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
            "records": self.records,
        }
        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(
            "测试汇总: 共 {total} 条 | 通过 {p} | 失败 {f} | 跳过 {s} | 耗时 {d}s -> {path}".format(
                total=total,
                p=self.counts["passed"],
                f=self.counts["failed"],
                s=self.counts["skipped"],
                d=duration,
                path=self.summary_file,
            )
        )
        return self.summary_file

    def print_progress(self) -> None:
        """实时打印当前进度（可在长用例间隔调用）。"""
        done = sum(self.counts.values())
        logger.info(f"进度: 已完成 {done} 条 | 通过 {self.counts['passed']} 失败 {self.counts['failed']}")


# 全局单例（在 conftest 中按需重置）
monitor = Monitor()


def get_monitor() -> Monitor:
    return monitor


def reset_monitor(summary_file: str = None, realtime_print: bool = True) -> Monitor:
    """每轮测试开始时重置 Monitor。"""
    global monitor
    monitor = Monitor(summary_file=summary_file, realtime_print=realtime_print)
    return monitor
