import json
import logging
import os
from collections.abc import Mapping
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
from livekit.plugins.turn_detector.multilingual import MultilingualModel

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
    "business_name": "Downtown Demo Barber Shop",
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

DEFAULT_AGENT_RUNTIME_NAME = "Jessica-voice-agent"


def _agent_identity_from_env(env: Mapping[str, str] | None = None) -> tuple[str, str]:
    source = env or os.environ
    runtime_name = source.get("AGENT_RUNTIME_NAME", DEFAULT_AGENT_RUNTIME_NAME).strip()
    assistant_name = (
        source.get("ASSISTANT_NAME") or source.get("AGENT_NAME") or "Jessica"
    ).strip()

    return runtime_name or DEFAULT_AGENT_RUNTIME_NAME, assistant_name or "Jessica"


AGENT_RUNTIME_NAME, ASSISTANT_NAME = _agent_identity_from_env()
_profile_timezone = BUSINESS_PROFILE.get("timezone")
TIMEZONE = str(os.getenv("TIMEZONE") or _profile_timezone or "America/New_York")


def _float_env(var_name: str, default: float) -> float:
    raw = os.getenv(var_name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid %s value '%s'. Using default %s.", var_name, raw, default)
        return default


def _int_env(var_name: str, default: int) -> int:
    raw = os.getenv(var_name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid %s value '%s'. Using default %s.", var_name, raw, default)
        return default


AGENT_LOAD_THRESHOLD = _float_env("AGENT_LOAD_THRESHOLD", 0.85)
AGENT_IDLE_PROCESSES = _int_env("AGENT_IDLE_PROCESSES", 1)
AGENT_INIT_TIMEOUT_SECONDS = _float_env("AGENT_INIT_TIMEOUT_SECONDS", 30.0)

logger.info(
    "Configured agent runtime '%s' with assistant name '%s'",
    AGENT_RUNTIME_NAME,
    ASSISTANT_NAME,
)


def build_reception_instructions() -> str:
    business_name = str(
        BUSINESS_PROFILE.get("business_name", "Downtown Demo Barber Shop")
    )
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
        "Sound like a real receptionist: use contractions, avoid stiff or robotic wording, and keep the tone warm but direct. "
        "Use natural conversational pacing and occasional brief acknowledgements like 'Sure' or 'Absolutely', "
        "but do not overuse fillers. "
        "\n\n"
        "Call flow rules:\n"
        f"1) First turn must be exactly: 'This is {business_name}, {ASSISTANT_NAME} speaking. How can I help?'\n"
        "2) Be helpful first: answer the caller's question directly before suggesting any next step.\n"
        "3) Do not pressure, upsell, or repeatedly circle back to appointments. Only mention booking when the caller asks to book or when it genuinely helps answer their question.\n"
        "4) If the caller interrupts, changes the subject, or asks a new question, stop the current response immediately in your next turn, answer the new request, and drop any unfinished booking script.\n"
        "5) If caller wants to book, collect these fields in this order: preferred appointment time, caller name, callback phone number. Ask for only one missing field at a time.\n"
        "6) If the caller gives a new appointment time or corrects another booking detail, treat the newest detail as authoritative and use it in your very next booking-related reply.\n"
        "7) Do not ask for a booking field again if the caller already gave it clearly. Instead, briefly confirm the latest time, name, and callback number you have on file and only ask for the one field that is still missing or unclear.\n"
        "8) As soon as the last missing or unclear booking field is clarified, your next reply must summarize the full booking using the latest requested appointment time before asking for confirmation once.\n"
        "9) If the caller is not ready to book, stay on their current question and do not keep nudging them back to scheduling.\n"
        "10) When answering business-hours questions, include the full grounded summary: weekdays until 6 PM, Saturday until 5 PM, and closed Sunday, unless the caller asks for only one specific day.\n"
        "11) If asked FAQ-style questions, answer from the knowledge base below and do not invent prices or hours.\n"
        "12) If you are unsure, use the fallback process and offer to take a callback message.\n"
        "13) If caller name is unclear after one attempt, ask them to say it slowly or spell it, then read it back for confirmation.\n"
        "14) For callback phone number capture, ask for digits slowly one group at a time. Repeat the full number back in 3-3-4 chunks and ask for a quick yes/no confirmation. If unclear, ask once more, then offer to continue with a callback message.\n"
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


ASSISTANT_INSTRUCTIONS = build_reception_instructions()


def build_turn_handling() -> dict[str, Any]:
    return {
        "turn_detection": MultilingualModel(),
        "endpointing": {
            "mode": "dynamic",
            "min_delay": 0.35,
            "max_delay": 2.5,
        },
        "interruption": {
            "mode": "adaptive",
            "min_duration": 0.25,
            "min_words": 0,
            "discard_audio_if_uninterruptible": True,
            "false_interruption_timeout": 1.5,
            "resume_false_interruption": True,
        },
    }


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=ASSISTANT_INSTRUCTIONS,
        )


server = AgentServer(
    load_threshold=AGENT_LOAD_THRESHOLD,
    num_idle_processes=AGENT_IDLE_PROCESSES,
    initialize_process_timeout=AGENT_INIT_TIMEOUT_SECONDS,
)


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
        turn_handling=build_turn_handling(),
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

    business_name = str(
        BUSINESS_PROFILE.get("business_name", "Downtown Demo Barber Shop")
    )
    await session.generate_reply(
        instructions=(
            f"Say exactly: 'This is {business_name}, {ASSISTANT_NAME} speaking. How can I help?' "
            "Then wait for the caller's request and let them lead the conversation."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
