import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.receipt_service import Appointment, InfraiClient, process_appointment


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise SystemExit("Set DEMO_EMAIL_TO before running the demo")
    appointment = Appointment("Mina", recipient, "Dr Lee", "2026-09-14 09:00", "apt-demo-1", 4200)
    message_id = process_appointment(appointment, InfraiClient())
    print(f"receipt email sent: {message_id}")


if __name__ == "__main__":
    main()
