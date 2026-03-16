import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero

logger = logging.getLogger("agent")

load_dotenv(".env.local")


def _load_json_file(env_var: str, default_path: str, fallback: Any) -> Any:
    path = Path(os.getenv(env_var, default_path))
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.warning("Config file not found for %s: %s", env_var, path)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON for %s (%s): %s", env_var, path, exc)
    return fallback


def _hours_summary(profile: dict[str, Any]) -> str:
    summary = profile.get("hours_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()

    hours = profile.get("hours")
    if isinstance(hours, str) and hours.strip():
        return hours.strip()
    if isinstance(hours, dict):
        ordered_days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        formatted = []
        for day in ordered_days:
            value = hours.get(day)
            if value:
                formatted.append(f"{day.title()}: {value}")
        if formatted:
            return "; ".join(formatted)
    return "Please ask and we can confirm current hours."


def _service_catalog(profile: dict[str, Any]) -> str:
    services = profile.get("services", [])
    if not isinstance(services, list) or not services:
        return "Service details are available by phone."

    lines = []
    for service in services:
        if not isinstance(service, dict):
            continue
        name = service.get("name", "Service")
        duration = service.get("duration_minutes")
        price = service.get("price")
        parts = [str(name)]
        if isinstance(duration, int):
            parts.append(f"{duration} min")
        if isinstance(price, int):
            parts.append(f"${price}")
        lines.append(" - ".join(parts))

    return "; ".join(lines) if lines else "Service details are available by phone."


def _faq_knowledge_block(faqs: list[dict[str, Any]]) -> str:
    if not faqs:
        return "No FAQ knowledge loaded."

    sorted_faqs = sorted(
        (item for item in faqs if isinstance(item, dict)),
        key=lambda item: (item.get("priority", 99), item.get("id", "")),
    )

    lines = []
    for item in sorted_faqs:
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if question and answer:
            lines.append(f"Q: {question} A: {answer}")
    return "\n".join(lines) if lines else "No FAQ knowledge loaded."


DEFAULT_BUSINESS_PROFILE = {
    "business_name": "Downtown Demo Barbershop",
    "address": "456 Demo Street",
    "city": "Nashua",
    "state": "NH",
    "timezone": "America/New_York",
    "hours_summary": "Monday to Friday 10 AM to 6 PM, Saturday 9 AM to 5 PM, closed Sunday.",
    "services": [
        {"name": "Haircut", "duration_minutes": 30, "price": 30},
        {"name": "Beard Trim", "duration_minutes": 20, "price": 15},
    ],
    "fallback": {
        "capture_message": "I can take your name and callback number and have someone call you back.",
        "callback_window": "within one business day",
    },
}

BUSINESS_PROFILE = _load_json_file(
    "BUSINESS_PROFILE_PATH", "config/business_profile.json", DEFAULT_BUSINESS_PROFILE
)
FAQS = _load_json_file("FAQ_SOURCE_PATH", "data/faqs.json", [])

AGENT_RUNTIME_NAME = os.getenv("AGENT_NAME", "Jessica-voice-agent")
_profile_timezone = BUSINESS_PROFILE.get("timezone")
TIMEZONE = str(os.getenv("TIMEZONE") or _profile_timezone or "America/New_York")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jessica")


def build_agent_instructions() -> str:
    business_name = str(BUSINESS_PROFILE.get("business_name", "Downtown Demo Barbershop"))
    address = str(BUSINESS_PROFILE.get("address", "456 Demo Street"))
    city = str(BUSINESS_PROFILE.get("city", "Nashua"))
    state = str(BUSINESS_PROFILE.get("state", "NH"))
    fallback = BUSINESS_PROFILE.get("fallback", {})
    fallback_message = str(
        fallback.get(
            "capture_message",
            "I can take your name and callback number and have someone call you back.",
        )
    )
    callback_window = str(fallback.get("callback_window", "within one business day"))

    return (
        f"You are {ASSISTANT_NAME}, the live phone receptionist for {business_name} in {city}, {state}. "
        "The caller is speaking over the phone, so every response must be concise, natural, and friendly. "
        "Use one or two short sentences unless the caller asks for more detail. "
        "\n\n"
        "Call flow rules:\n"
        f"1) First turn: greet the caller, introduce yourself as {ASSISTANT_NAME}, state the business name, and ask what time they want to set up an appointment for.\n"
        "2) If caller wants to book, collect these fields in this order: preferred appointment time, caller name, callback phone number.\n"
        "3) If the caller asks a new question at any point, answer it first, then politely continue booking only if they still want to book.\n"
        "4) After collecting all three fields, repeat details once and ask for confirmation once. If they decline or change details, update and continue without repeating the same confirmation prompt over and over.\n"
        "5) If caller name is unclear after one attempt, ask them to say it slowly or spell it, then read it back for confirmation.\n"
        "6) For callback phone number capture, ask for digits slowly one group at a time. Repeat the full number back in 3-3-4 chunks and ask for a quick yes/no confirmation. If unclear, ask once more, then offer to continue with a callback message.\n"
        "7) If asked FAQ-style questions, answer from the knowledge base below and do not invent prices or hours.\n"
        "8) If you are unsure, use the fallback process and offer to take a callback message.\n"
        "\n"
        f"Business: {business_name}\n"
        f"Location: {address}, {city}, {state}\n"
        f"Timezone: {TIMEZONE}\n"
        f"Hours: {_hours_summary(BUSINESS_PROFILE)}\n"
        f"Services: {_service_catalog(BUSINESS_PROFILE)}\n"
        f"Fallback: {fallback_message} Expected callback: {callback_window}.\n"
        "\n"
        "FAQ Knowledge Base:\n"
        f"{_faq_knowledge_block(FAQS)}"
    )


ASSISTANT_INSTRUCTIONS = build_agent_instructions()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=ASSISTANT_INSTRUCTIONS,
        )


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name=AGENT_RUNTIME_NAME)
async def agent_session(ctx: JobContext) -> None:
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect()

    session = AgentSession(
        stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions=(
            f"Greet the caller as {ASSISTANT_NAME} at "
            f"{BUSINESS_PROFILE.get('business_name', 'Downtown Demo Barbershop')} "
            "and immediately ask what time they want to set up their appointment for."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
