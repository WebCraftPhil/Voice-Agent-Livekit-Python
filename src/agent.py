import logging
from pathlib import Path

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

PROMPT_PATH = (
    Path(__file__).resolve().parent / "prompts" / "stellar_styles_system_prompt.txt"
)
STELLAR_SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()
DEFAULT_OPENING = (
    "Hey there, welcome to Stellar Styles and More. "
    "I can help you find something meaningful or answer any questions you have. "
    "What are you looking for today?"
)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=STELLAR_SYSTEM_PROMPT,
        )


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="Steve-voice-agent")
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
        instructions=DEFAULT_OPENING
    )


if __name__ == "__main__":
    cli.run_app(server)
