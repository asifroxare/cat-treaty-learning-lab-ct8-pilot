"""Tiny functions to prove CT8 process isolation without importing treaty code."""
import os
import time


def square(value):
    return value * value


def wait_forever(_value):
    time.sleep(30)
    return "must never return"


def crash(_value):
    os._exit(3)
