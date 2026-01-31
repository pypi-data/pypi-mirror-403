"""CLI: запуск бесконечного цикла движения мыши."""

import random
import time

import pyautogui

from datapipe.core import decomposition, MIN_DELAY, MAX_DELAY, MAX_OFFSET

pyautogui.FAILSAFE = True


def main(
    *,
    key: str = "shift",
    min_delay: int = MIN_DELAY,
    max_delay: int = MAX_DELAY,
    max_offset: int = MAX_OFFSET,
) -> None:
    """Data Pipeline Tool"""
    print("on air")
    while True:
        decomposition(max_offset=max_offset)
        delay = random.randint(min_delay, max_delay)
        print(f"decomposition point {delay} lbs")
        pyautogui.press(key)
        time.sleep(delay)
