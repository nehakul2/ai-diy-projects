"""Shared helper for calling Claude. Every project in this repo uses ask()."""
import os
import sys

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

# Server-side web search: Claude searches the web itself, no extra code needed.
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}

MAX_CONTINUATIONS = 5


def ask(
    system: str,
    user: str,
    effort: str = "medium",
    max_tokens: int = 16000,
    tools: list | None = None,
) -> str:
    """Send one prompt to Claude and return the text reply.

    Pass tools=[WEB_SEARCH] to let Claude search the web while answering.
    """
    messages = [{"role": "user", "content": user}]
    extra = {"tools": tools} if tools else {}
    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        for _ in range(MAX_CONTINUATIONS + 1):
            response = client.beta.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                output_config={"effort": effort},
                # If the main model declines, the API retries on a suitable fallback model.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                **extra,
            )
            # Long web-search turns can pause; send the reply back and the server resumes.
            if response.stop_reason != "pause_turn":
                break
            messages = [messages[0], {"role": "assistant", "content": response.content}]
    except TypeError as e:
        if "authentication" not in str(e):
            raise
        sys.exit("No Claude API key found. Set ANTHROPIC_API_KEY (see README).")
    except anthropic.AuthenticationError:
        sys.exit("Claude API key missing or invalid. Set ANTHROPIC_API_KEY (see README).")
    except anthropic.RateLimitError:
        sys.exit("Hit the API rate limit. Wait a minute and try again.")
    except anthropic.APIStatusError as e:
        sys.exit(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("Couldn't reach the Claude API. Check your internet connection.")

    if response.stop_reason == "refusal":
        sys.exit("Claude declined this request.")
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if response.stop_reason == "max_tokens":
        text += "\n\n[Output was cut off because it hit the length limit.]"
    elif response.stop_reason == "pause_turn":
        text += "\n\n[Stopped early: the web search ran long. Try again or narrow the request.]"
    return text
