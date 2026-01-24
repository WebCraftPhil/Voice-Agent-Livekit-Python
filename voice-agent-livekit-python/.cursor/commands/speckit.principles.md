# /speckit.principles
Design axioms derived from the Constitution for this repo.

## P0: Phone Call Reality
- The agent must be understandable over a phone line.
- Prefer short sentences, minimal punctuation, no complex formatting.
- Confirm critical details by repeating them back.

## P1: Latency Budget
- Target time to first response: <= 1.5s after user finishes speaking (best effort).
- If processing will take longer than 2.5s, the agent must say a short filler line:
  - "One second while I check that."
  - "Let me pull that up."

## P2: Barge-in and Interruptions
- If the user interrupts, stop speaking within 300ms if possible.
- The user always wins the floor. Do not talk over them.

## P3: Never Invent Business Facts
- If the agent does not know, it must say so and offer next steps:
  - ask a clarifying question
  - offer to transfer, take a message, or follow up

## P4: Appointment Setting Safety
- The agent may only schedule using the Scheduling Tool API.
- If tool fails, do not pretend the appointment is booked.
- Always confirm: date, time, timezone, name, phone, and purpose.

## P5: FAQ Grounding
- All FAQ answers must come from an approved FAQ source.
- If the FAQ source has no match, the agent must not guess.
- The agent may offer to capture the question for follow-up.

## P6: Call Outcome First
Every call should end with one of these outcomes:
- Appointment booked
- Appointment request captured for follow-up
- FAQ answered with a cited source entry (internal citation ID)
- Escalated to a human or voicemail workflow
- Polite termination if abusive or out of scope

## P7: PII and Logging
- Do not log raw phone numbers, emails, or full names.
- Logs must include a call_id and event types, not sensitive content by default.
- Debug mode can log more, but must be opt-in via env var.

## P8: Config Over Code
- Providers (LLM, STT, TTS) selected by config.
- Business behavior configured by a "business profile" file or env-driven config.

## P9: Agent-Friendly Repo
- Clear entrypoints, stable interfaces, and contract tests.
- Every tool has a schema and example payloads.
