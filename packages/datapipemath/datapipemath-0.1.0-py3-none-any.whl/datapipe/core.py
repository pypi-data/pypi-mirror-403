"""Ядро datapipe: движение мыши и константы."""

import random
import time
from typing import Optional

import pyautogui

pyautogui.FAILSAFE = True

MIN_DELAY = 50
MAX_DELAY = 250
MAX_OFFSET = 75


def decomposition(
    *,
    max_offset: Optional[int] = None,
    duration: Optional[float] = None,
) -> None:
    """
    Одно плавное перемещение мыши на случайное смещение.
    """
    offset = max_offset if max_offset is not None else MAX_OFFSET
    dx = random.randint(-offset, offset)
    dy = random.randint(-offset, offset)

    t = duration if duration is not None else random.uniform(0.2, 0.6)
    pyautogui.moveRel(dx, dy, duration=t)

    time.sleep(random.uniform(0.2, 0.5))
