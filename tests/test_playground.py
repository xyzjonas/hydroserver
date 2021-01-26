from croniter import croniter
from datetime import datetime


def test_cron():
    iter = croniter("0 */16 * * *")
    c = iter.get_next(datetime)
    z = iter.all_next(datetime)
    for i in range(20):
        x = next(z)
    u = 1


if __name__ == "__main__":
    from datetime import timedelta
    test_cron()
