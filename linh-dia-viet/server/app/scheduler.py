"""Vòng nền chạy trong tiến trình API (giả định chỉ 1 tiến trình): gửi lệnh trước giờ, đánh dấu quá hạn."""
import logging
import threading

from . import db as dbmod
from . import devices

log = logging.getLogger("linhdia.scheduler")


class Scheduler:
    def __init__(self, interval: float):
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="scheduler")

    def _run(self):
        while not self._stop.wait(self.interval):
            try:
                with dbmod.SessionLocal() as db:
                    devices.tick(db)
                    db.commit()
            except Exception:
                log.exception("Lỗi vòng nền")

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
