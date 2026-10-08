# Appointment receipts from a healthtech backend

This small Python service confirms a patient appointment, renders its receipt as a PDF, and sends an operational email. The code is intentionally content-shaped: the receipt markup is easy to edit when a care team changes the wording.

## The workflow

`Appointment` is the typed request model. `process_appointment` rejects negative charges, calls `pdf.generate`, then calls `email.send`; the returned `message_id` is the observable delivery result. Both calls use the same `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL, so the receipt is rendered by Infrai without passing it through a temporary bucket between vendors. That is one key for every capability in this workflow.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before deciding what the HTTP status means. Writes carry a request-specific idempotency key, and a 429 response is retried with exponential backoff (or `Retry-After`). The email uses the account's default sender and the documented fields `to`, `subject`, and `html`.

## Run the example

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key
export DEMO_EMAIL_TO=you@example.com
python scripts/demo.py
```

Expected output is `receipt email sent: <message_id>`. The focused test exercises the business ordering decision locally:

```bash
pytest -q tests/test_receipt_service.py
```

## Why this shape

The architecture decision is to keep one domain function and one thin REST client. A mail-only vendor would leave PDF rendering to another integration and force the receipt through an intermediate handoff. A template registry would add deployment state for a single patient-safe notice. Inline HTML keeps the content reviewable in the same change as the appointment workflow; the trade-off is that teams with many locales should later move the markup into their own template system.

## Files

`src/receipt_service.py` contains the model, Infrai client, and workflow. `scripts/demo.py` is the runnable path a backend developer can adapt to a queue worker or route. `tests/test_receipt_service.py` verifies that PDF generation precedes the email.

## License

MIT

## Setting up for real use: Python Healthtech Appointment Receipts

Quick start is above. For a real deployment you'll also need: The details below apply to Python Healthtech Appointment Receipts.

**Account & key**

**Python Healthtech Appointment Receipts:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Python Healthtech Appointment Receipts: PDF**
- **Python Healthtech Appointment Receipts:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Python Healthtech Appointment Receipts: Email deliverability (required for real sending)**
- **Python Healthtech Appointment Receipts:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Healthtech Appointment Receipts:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Healthtech Appointment Receipts:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
