from datetime import datetime
import time


def wacht_tot(tijdstip):
    while True:
        resterend = (
            tijdstip - datetime.now()
        ).total_seconds()

        if resterend <= 0:
            return

        if resterend > 0.1:
            time.sleep(
                min(
                    0.05,
                    resterend - 0.1,
                )
            )
        else:
            while datetime.now() < tijdstip:
                pass

            return
