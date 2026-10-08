from src.receipt_service import Appointment, process_appointment


class FakeClient:
    def __init__(self):
        self.calls = []

    def generate_receipt_pdf(self, appointment):
        self.calls.append("pdf")
        return {"pdf": "inline"}

    def send_receipt_email(self, appointment, pdf):
        self.calls.append(("email", pdf))
        return {"message_id": "msg-123"}


def test_paid_appointment_generates_receipt_before_email():
    client = FakeClient()
    appointment = Appointment("Mina", "mina@example.com", "Dr Lee", "2026-09-14 09:00", "apt-7", 4200)
    assert process_appointment(appointment, client) == "msg-123"
    assert client.calls == ["pdf", ("email", {"pdf": "inline"})]
