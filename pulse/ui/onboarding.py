"""Onboarding helpers for Pulse."""


DEFAULT_REMINDER_TIME = "20:00"
EARLIEST_REMINDER_HOUR = 18
LATEST_REMINDER_HOUR = 22


def normalize_reminder_time(reminder_time):
    text = str(reminder_time).strip()
    if not text:
        return DEFAULT_REMINDER_TIME
    if ":" not in text:
        return DEFAULT_REMINDER_TIME
    hour_text, minute_text = text.split(":", 1)
    try:
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError:
        return DEFAULT_REMINDER_TIME
    if hour < EARLIEST_REMINDER_HOUR or hour > LATEST_REMINDER_HOUR:
        return DEFAULT_REMINDER_TIME
    if hour == LATEST_REMINDER_HOUR and minute > 0:
        return DEFAULT_REMINDER_TIME
    if minute < 0 or minute > 59:
        return DEFAULT_REMINDER_TIME
    return "{:02d}:{:02d}".format(hour, minute)
