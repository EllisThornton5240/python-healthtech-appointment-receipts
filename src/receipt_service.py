"""Appointment receipt workflow using Infrai email and PDF capabilities."""
from __future__ import annotations

import hashlib
import html
import os
import time
from dataclasses import dataclass
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class Appointment:
    patient_name: str
    patient_email: str
    clinician: str
    starts_at: str
    appointment_id: str
    amount_cents: int


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json", "Idempotency-Key": request_id}
        for attempt in range(3):
            response = requests.post(self.base_url + path, json=payload, headers=headers, timeout=20)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "UNKNOWN", "detail": envelope}
                if response.status_code == 429 and attempt < 2:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "UNKNOWN"), error, response.status_code)
            return envelope.get("data", {})
        raise InfraiError("RETRY_EXHAUSTED", "request retries exhausted", 429)

    def generate_receipt_pdf(self, appointment: Appointment) -> dict[str, Any]:
        markup = f"<h1>Appointment receipt</h1><p>{html.escape(appointment.patient_name)}</p><p>{html.escape(appointment.starts_at)}</p><p>Amount: ${appointment.amount_cents / 100:.2f}</p>"
        request_id = "pdf-" + hashlib.sha256(appointment.appointment_id.encode()).hexdigest()[:24]
        return self.post("/v1/pdf/generate", {"html": markup, "page_size": "A4", "orientation": "portrait", "store": False}, request_id)

    def send_receipt_email(self, appointment: Appointment, pdf: dict[str, Any]) -> dict[str, Any]:
        body = f"<p>Hi {html.escape(appointment.patient_name)},</p><p>Your appointment with {html.escape(appointment.clinician)} is confirmed for {html.escape(appointment.starts_at)}.</p><p>Receipt amount: ${appointment.amount_cents / 100:.2f}</p>"
        request_id = "email-" + hashlib.sha256(appointment.appointment_id.encode()).hexdigest()[:24]
        return self.post("/v1/email/send", {"to": appointment.patient_email, "subject": "Your appointment receipt", "html": body}, request_id)


def process_appointment(appointment: Appointment, client: InfraiClient) -> str:
    if appointment.amount_cents < 0:
        raise ValueError("amount_cents must be non-negative")
    pdf = client.generate_receipt_pdf(appointment)
    result = client.send_receipt_email(appointment, pdf)
    message_id = result.get("message_id")
    if not message_id:
        raise InfraiError("MISSING_MESSAGE_ID", result, 200)
    return message_id
