"""Shared helper for calling Claude. Every project in this repo uses ask()."""
import os
import sys

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")


def ask(system: str, user: str, effort: str = "medium", max_tokens: int = 16000) -> str:
    """Send one prompt to Claude and return the text reply."""
    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": effort},
            # If the main model declines, the API retries on a suitable fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
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
    return text
