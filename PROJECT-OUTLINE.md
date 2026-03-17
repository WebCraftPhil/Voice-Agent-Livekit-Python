# Project Outline: Voice AI Assistant

This document outlines the development plan for a voice AI assistant built with LiveKit Agents.

## 1. Project Goal

*   Define the primary purpose and scope of the voice AI assistant.
*   Identify the target audience and key use cases.
*   Example: A customer service agent for an e-commerce website, capable of answering questions about products and order status.

## 2. Core Features

*   **Intent Recognition:** What are the key intents the agent should understand?
    *   e.g., `greet`, `get_product_info`, `get_order_status`, `transfer_to_human`.
*   **Conversation Flow:** How will the conversation be structured?
    *   Design conversation flows for each intent.
    *   Consider edge cases and error handling.
*   **Tool Usage:** What tools will the agent need to fulfill user requests?
    *   e.g., API calls to a product database, order management system, etc.
*   **Voice and Personality:** Define the agent's voice and personality.
    *   Choose a text-to-speech (TTS) voice.
    *   Define the agent's tone and style (e.g., friendly, professional, concise).

## 3. Technical Implementation

*   **Agent Logic (`src/agent.py`):**
    *   Implement the main agent logic, including intent handling and conversation management.
    *   Define the agent's instruction prompt.
    *   Integrate necessary tools (functions the agent can call).
*   **STT/TTS Integration:**
    *   Configure the speech-to-text (STT) and text-to-speech (TTS) services.
    *   The starter project uses AssemblyAI and Cartesia by default, but this can be changed.
*   **LLM Integration:**
    *   Configure the language model (LLM).
    *   The starter project uses OpenAI by default.
*   **Testing (`tests/`):**
    *   Write unit and integration tests for the agent's behavior.
    *   Use the LiveKit Agents testing framework to create evals for conversation quality.

## 4. Frontend/Telephony Integration

*   Choose an integration method:
    *   **Web:** Use a frontend framework like React (e.g., `livekit-examples/agent-starter-react`).
    *   **Mobile:** Use native frameworks (Swift, Kotlin) or cross-platform frameworks (Flutter, React Native).
    *   **Telephony:** Integrate with a SIP trunk for phone calls.

## 5. Deployment

*   **Environment Configuration:**
    *   Set up `.env.local` with API keys and LiveKit credentials.
*   **Production Deployment:**
    *   Use the provided `Dockerfile` to containerize the agent.
    *   Deploy to LiveKit Cloud or another container hosting service.

## 6. Working LiveKit Config Snapshot (2026-03-17)

*   **LiveKit project:** `first-voice-agent` (subdomain: `first-voice-agent-pr105f3f`)
*   **Agent ID:** `CA_uzBzoBc3QsCG`
*   **Agent name (dispatch target):** `Jessica-voice-agent`
*   **Current deployed version:** `v20260317164604` (`Available`)
*   **Agent runtime status:** `Running` in `us-east`
*   **Phone number (ACTIVE):** `+16033469332` (`PN_PPN_D2FVXyocpzJR`)
*   **Inbound SIP trunk:** `ST_AUaNowuPWqij` (`Voice-agent inbound`)
    *   Numbers: `+16033469332`
    *   Allowed addresses: `0.0.0.0/0`
    *   Allowed numbers: empty
*   **SIP dispatch rule:** `SDR_jRojEp6SyqhZ` (`Inbound-Missed-Call`)
    *   Type: `Individual (Caller)`
    *   Room pattern: `call-_<caller>_<random>`
    *   Agent target: `Jessica-voice-agent`
    *   SIP trunk binding: `PN_PPN_D2FVXyocpzJR`
*   **Cleanup completed:** removed extra conflicting trunk `ST_H2ncNt9whi8X`
