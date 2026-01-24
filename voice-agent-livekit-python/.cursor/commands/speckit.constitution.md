description: Create or amend the Voice Agent Constitution for this repository, enforcing telephone-first behavior, tool-gated truth, privacy guarantees, and agent-safe development rules. All dependent specification templates must be kept in sync.
handoffs:
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification in strict compliance with the updated Voice Agent Constitution. Do not invent behavior, tools, or guarantees not explicitly allowed by the constitution.
    send: true 
    

# Voice Agent Constitution

## Core Principles

### I. Phone First
This agent is built for telephone conversations. Responses must be short, clear, and easy to understand over a phone line. No complex formatting, symbols, or special punctuation.

### II. Tool Gated Truth
The agent must not claim an appointment is booked unless the Scheduling tool returns a success confirmation. The agent must not answer FAQs unless the answer is retrieved from an approved FAQ source.

### III. Test First Non Negotiable
Any change to behavior ships with tests and eval scenarios first. If behavior changes, evals must be updated intentionally.

### IV. Failure Safe UX
If any component fails (STT, LLM, TTS, scheduling, FAQ retrieval), the agent must degrade gracefully: apologize, ask to repeat, capture details for follow up, or escalate.

### V. Privacy by Default
Do not log raw PII by default. No raw phone numbers, emails, or full names in logs. PII logging is explicit opt-in.

## Development Workflow
- Spec before code for new capabilities
- Contract tests and evals must pass before merge
- Changes that impact callers require updated evals

## Governance
- Constitution overrides all other docs
- Amendments require: rationale, migration plan, updated tests and evals

**Version**: 0.1.0 | **Ratified**: 2026-01-22 | **Last Amended**: 2026-01-22
