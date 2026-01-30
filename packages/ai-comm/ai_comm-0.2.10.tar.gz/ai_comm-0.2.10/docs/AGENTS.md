# ai-comm

## ai-comm for Cross-AI Collaboration

`ai-comm` enables communication with other AI CLIs (Claude, Codex, Gemini, Aider, etc.) running in separate Kitty windows. Always run `ai-comm --help` before first use in a session.

- **Initiator**: call `ai-comm`; for long responses, request file output.
- **Responder**: if input contains `[ai-comm:`, reply with plain text only—never call `ai-comm`. Sending to the sender’s window ID (shown in message header) causes deadlock.

Example uses:

- Request code review from Codex or Gemini
- Get second opinions on architecture decisions
- Delegate specialized analysis tasks
