# /speckit.threat-model
Threat model for telephone customer service agent.

## Assets to protect
- LiveKit credentials
- Provider API keys
- Customer PII (names, phone numbers, emails)
- Appointment details

## Primary threats
1. Secret leakage in logs or commits
2. PII exposure in logs, metrics, or third-party vendors
3. Prompt injection via caller attempting to override policy
4. Hallucinated confirmations (agent claims booking without booking)
5. Abuse and harassment calls

## Controls
- Secrets only via env vars, never committed
- LOG_PII default false
- Redaction function for any user identifiers
- Tool-gated confirmations: booking only if tool returns confirmation
- Policy layer for unsafe or abusive content
- Rate limiting and call duration caps where feasible

## Data retention
- Store minimal call metadata by default
- No audio recording unless explicitly enabled and disclosed
- If transcripts are stored, redact phone and email patterns

## Vendor considerations
- Document which vendors receive audio or text
- Provide a config to swap providers without code rewrites

## Incident response
- Documented process for handling security incidents
- Contact points for reporting vulnerabilities
- Steps for revoking compromised credentials
- Plan for isolating affected components