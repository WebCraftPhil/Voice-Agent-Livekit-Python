# /speckit.contract
Repo level contract for LiveKit telephone customer service agent.

## 1. Entry Point Contract
The application entrypoint is:
- src/agent.py
- It must be runnable via LiveKit Agents CLI wrapper:
  python src/agent.py <subcommand>

The app must register an RTC session handler using:
- @server.rtc_session()

## 2. Runtime Contract
The agent must:
- Prewarm Silero VAD during process setup
- Create an AgentSession with:
  - STT configured
  - LLM configured
  - TTS configured
  - Turn detection configured
  - VAD configured
- Start session with room options that apply telephony noise cancellation when participant is SIP
- Connect to the room

## 3. Telephony Contract
If a participant is SIP:
- noise cancellation must use BVCTelephony
Else:
- noise cancellation must use BVC

## 4. Behavior Contract
The assistant must:
- Speak concisely, with minimal punctuation
- Ask clarifying questions when details are missing
- Never invent appointment bookings
- Never guess FAQ answers
- Confirm critical booking fields before finalizing:
  - date
  - time
  - timezone
  - name
  - callback number
  - purpose

## 5. Configuration Contract
Environment file:
- .env.local is loaded in development

Required env vars:
- LIVEKIT_URL
- LIVEKIT_API_KEY
- LIVEKIT_API_SECRET

Optional env vars:
- BUSINESS_PROFILE_PATH
- FAQ_SOURCE_PATH
- SCHEDULER_PROVIDER (default: mock)
- LOG_LEVEL (default: INFO)
- LOG_PII (default: false)

## 6. Tool Contracts
### 6.1 Scheduling Tool
A scheduler interface must exist with methods:
- get_availability(service, date_range, timezone) -> slots[]
- book_appointment(customer, service, slot, notes) -> confirmation
- cancel_appointment(confirmation_id) -> result

### 6.2 FAQ Retrieval
An FAQ retrieval interface must exist returning:
- answer_text
- source_id
- confidence (0 to 1)

If confidence < 0.65:
- agent must ask clarifying question or offer follow up capture

## 7. Observability Contract
Logs must include:
- call_id or room name
- event type
- provider names (stt, llm, tts)
PII logging off by default.
