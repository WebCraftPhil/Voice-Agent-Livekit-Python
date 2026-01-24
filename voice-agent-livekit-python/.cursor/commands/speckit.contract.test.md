# /speckit.contract.test

## P0 tests
1. Imports and boot
- Import src.agent without side effects that crash without LiveKit credentials
- Ensure server exists and has rtc session handler

2. Env var validation
- If LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET missing, app must fail fast in run modes that require connecting

3. Scheduling tool contract
- Mock scheduler must satisfy interface
- Agent must not claim booking without confirmation

4. FAQ contract
- Mock FAQ source must return answer_text, source_id, confidence
- If confidence low, agent must not guess

## Smoke tests
- Optional local smoke test that starts console mode and completes one turn, gated behind an env var like RUN_SMOKE=1
5. Interruption handling
- Agent must respond to interruptions within 1 second
- Agent must not continue speaking after interruption
- Agent must acknowledge interruption and continue conversation