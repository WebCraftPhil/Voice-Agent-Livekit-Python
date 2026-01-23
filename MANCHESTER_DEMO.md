# Manchester, NH Telephone Agent Demo

This voice AI agent is specifically configured for demonstrating to local subscribers around Manchester, New Hampshire. It provides a professional telephone experience with local knowledge and information.

## Features

### Manchester-Specific Knowledge
The agent is pre-configured with information about:
- Local geography and landmarks (Merrimack River, Amoskeag Millyard)
- Major attractions (Currier Museum of Art, SNHU Arena, Palace Theatre)
- Manchester-Boston Regional Airport
- Historic context and local culture

### Local Information Tool
The agent includes a `get_local_info` tool that provides detailed information about:
- **Restaurants & Dining**: Local favorites like Red Arrow Diner, Copper Door, Hanover Street Chop House
- **Parks & Recreation**: Livingston Park, Derryfield Park, Lake Massabesic, Amoskeag Fishways
- **Education**: Public schools, SNHU, Saint Anselm College, Manchester Community College
- **Healthcare**: Catholic Medical Center, Elliot Hospital, urgent care facilities
- **Shopping**: Mall of New Hampshire, downtown Elm Street shops, South Willow Street
- **Entertainment**: SNHU Arena, Palace Theatre, local events
- **History & Culture**: Amoskeag Mills history, Millyard Museum, historic architecture

### Telephone-Optimized Experience
The agent is designed for phone calls with:
- Professional, warm greeting suitable for telephone interaction
- Clear, concise responses optimized for voice-only communication
- No emojis, asterisks, or text formatting
- SIP/telephony noise cancellation enabled

## Setup

### Prerequisites
1. LiveKit Cloud account with API credentials
2. Environment variables configured in `.env.local`:
   ```
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   ```

### Installation
```bash
# Install dependencies
uv sync

# Download required models
uv run python src/agent.py download-files
```

## Running the Agent

### For Console Testing
```bash
uv run python src/agent.py console
```

### For Development (with Frontend or Telephony)
```bash
uv run python src/agent.py dev
```

### For Production
```bash
uv run python src/agent.py start
```

## Telephony Integration

To connect this agent to a phone number for your Manchester, NH demo:

1. Follow the [LiveKit Telephony Documentation](https://docs.livekit.io/agents/start/telephony/)
2. Configure a SIP trunk using the LiveKit CLI:
   ```bash
   lk sip trunk create
   ```
3. Set up inbound or outbound calling as needed for your demo

The agent automatically applies telephony-optimized noise cancellation when connected via SIP.

## Testing

Run the test suite to validate Manchester-specific functionality:
```bash
uv run pytest
```

Tests include:
- Manchester location awareness
- Local information tool functionality
- Professional telephone greeting
- Standard agent behavior (grounding, safety)

## Example Interactions

**Greeting:**
- Caller: "Hello, can you help me?"
- Agent: *Provides warm, professional greeting and offers assistance*

**Local Information:**
- Caller: "What restaurants do you recommend?"
- Agent: *Uses get_local_info tool to provide Manchester dining options*

**Area Questions:**
- Caller: "Tell me about your city"
- Agent: *Shares information about Manchester, NH's history, location, and attractions*

## Customization

To adjust the agent for your specific demo needs:

1. **Update Instructions**: Edit the `instructions` parameter in `src/agent.py`
2. **Add Local Info**: Extend the `get_local_info` tool with more categories
3. **Adjust Voice/Model**: Modify the TTS voice or LLM model in the session setup

## Demo Tips

For the best demo experience:
- Use a quality microphone and quiet environment
- Speak clearly and naturally
- Try asking about different Manchester topics (restaurants, parks, schools)
- Demonstrate the agent's professional telephone demeanor
- Show how it handles local knowledge vs. general questions

## Support

For issues or questions about LiveKit Agents, see:
- [LiveKit Documentation](https://docs.livekit.io/)
- [LiveKit Agents Python SDK](https://github.com/livekit/agents)
- [LiveKit Community](https://livekit.io/community)
