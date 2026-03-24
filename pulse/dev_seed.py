"""Development demo data for Pulse."""

from datetime import date as date_class, timedelta


def seed_demo_data(database) -> None:
    today = date_class.today()
    for index, offset in enumerate(range(6, -1, -1)):
        current_date = (today - timedelta(days=offset)).isoformat()
        base = 5.0 + (index % 3)
        samples = []
        for hour in range(8, 24):
            level = max(1.0, min(10.0, base + ((hour % 4) - 1.5)))
            samples.append(_Sample(hour=hour, level=round(level, 1)))
        database.save_evening_input(
            date=current_date,
            hourly_samples=samples,
            sleep_hours=6.5 + (index % 3) * 0.5,
            physical_activity=("no", "some", "yes")[index % 3],
            stress_level=("low", "medium", "high")[index % 3],
            free_note="Demo day {}".format(index + 1),
        )
    database.save_ritual("shutdown", "Shutdown", "18:30", True)
    database.save_ritual("walk", "Walk outside", "15:00", True)
    database.save_ritual("stretch", "Stretch break", "11:30", False)
    database.save_mbi_checkin(today.isoformat(), 2, 1, 3)


class _Sample(object):
    def __init__(self, hour: int, level: float) -> None:
        self.hour = hour
        self.level = level
