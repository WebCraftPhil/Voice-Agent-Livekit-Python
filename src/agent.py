import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly and professional voice AI assistant serving the Manchester, New Hampshire area. You are speaking with local subscribers over the telephone.

            Your role is to:
            - Greet callers warmly and professionally
            - Provide information about local services and businesses in the Manchester, NH area
            - Answer questions about the area, including neighborhoods, attractions, and local amenities
            - Be knowledgeable about Manchester's history, culture, and community

            Communication style:
            - Keep responses concise and clear for telephone conversation
            - Speak naturally without complex formatting, emojis, asterisks, or other symbols
            - Be friendly, helpful, and patient
            - If you don't know something specific, be honest and offer to help with related questions

            Key information about Manchester, NH:
            - Largest city in New Hampshire
            - Located in Hillsborough County along the Merrimack River
            - Known for the historic Amoskeag Millyard
            - Home to the Manchester-Boston Regional Airport
            - Features attractions like the Currier Museum of Art and SNHU Arena
            - Vibrant downtown with local restaurants, shops, and entertainment""",
        )

    @function_tool
    async def get_local_info(self, context: RunContext, topic: str):
        """Use this tool to get information about local Manchester, NH services, attractions, or businesses.

        Args:
            topic: The topic or type of information requested (e.g., restaurants, parks, schools, healthcare, shopping)
        """

        logger.info(f"Looking up local information for: {topic}")

        # Provide helpful local information based on the topic
        topic_lower = topic.lower()

        if (
            "restaurant" in topic_lower
            or "food" in topic_lower
            or "dining" in topic_lower
        ):
            return """Manchester has a diverse dining scene. Popular areas include downtown Elm Street with restaurants like The Copper Door and Hanover Street Chop House. The Millyard district also features great options. For casual dining, Red Arrow Diner is a local favorite open 24/7."""

        elif (
            "park" in topic_lower
            or "outdoor" in topic_lower
            or "recreation" in topic_lower
        ):
            return """Manchester offers several parks including Livingston Park with its scenic trails, Derryfield Park for sports and picnicking, and Lake Massabesic for water activities. The Amoskeag Fishways has walking paths along the Merrimack River."""

        elif "school" in topic_lower or "education" in topic_lower:
            return """Manchester has a public school system with several elementary, middle, and high schools. The city is also home to Southern New Hampshire University (SNHU), Saint Anselm College, and Manchester Community College."""

        elif (
            "healthcare" in topic_lower
            or "hospital" in topic_lower
            or "medical" in topic_lower
        ):
            return """Catholic Medical Center and Elliot Hospital are the two main hospitals serving Manchester. Both offer comprehensive medical services and emergency care. There are also numerous urgent care facilities and medical practices throughout the city."""

        elif (
            "shopping" in topic_lower or "mall" in topic_lower or "store" in topic_lower
        ):
            return """The Mall of New Hampshire is a major shopping destination. Downtown Manchester on Elm Street has unique local shops and boutiques. The area also has various plazas and retail centers including the South Willow Street commercial district."""

        elif "airport" in topic_lower or "travel" in topic_lower:
            return """Manchester-Boston Regional Airport (MHT) is conveniently located just minutes from downtown. It serves several major airlines with direct flights to many U.S. destinations."""

        elif (
            "entertainment" in topic_lower
            or "event" in topic_lower
            or "arena" in topic_lower
        ):
            return """The SNHU Arena hosts concerts, sporting events, and shows. The historic Palace Theatre downtown presents plays, concerts, and performances. The Currier Museum of Art features impressive collections and exhibitions."""

        elif "history" in topic_lower or "museum" in topic_lower:
            return """Manchester's history is rooted in textile manufacturing at the Amoskeag Mills, once the largest cotton textile plant in the world. The Millyard Museum chronicles this history. The city has beautifully preserved historic architecture throughout downtown."""

        else:
            return f"""I can help with information about Manchester, NH. For specific details about {topic}, I recommend checking with local resources or asking about particular categories like restaurants, parks, schools, healthcare, shopping, or entertainment."""


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(model="assemblyai/universal-streaming", language="en"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
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

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
