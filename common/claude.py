"""Shared helper for calling Claude. Every project in this repo uses ask()."""
import os
import sys

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

# Server-side web search: Claude searches the web itself, no extra code needed.
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}

MAX_CONTINUATIONS = 5


def _clean_key() -> str | None:
    """Read ANTHROPIC_API_KEY, dropping stray spaces, newlines or quotes from copy-paste."""
    raw = os.environ.get("ANTHROPIC_API_KEY")
    if raw is None:
        return None
    return raw.strip().strip("'\"").strip() or None


def _api_message(e: anthropic.APIStatusError) -> str:
    """The API's own error text, e.g. 'invalid x-api-key'."""
    body = e.body if isinstance(e.body, dict) else {}
    return body.get("error", {}).get("message") or e.message


def _key_hint(key: str | None) -> str:
    """Describe the key without revealing it, to help spot paste mistakes."""
    if not key:
        return "ANTHROPIC_API_KEY is not set in this Terminal window."
    problems = []
    if not key.startswith("sk-ant-"):
        problems.append("it doesn't start with sk-ant-")
    if any(c.isspace() for c in key):
        problems.append("it contains a space or line break")
    hint = f"Key in use: {key[:10]}...{key[-4:]} ({len(key)} characters)"
    return hint + (f"; looks wrong because {' and '.join(problems)}." if problems else ".")


def ask(
    system: str,
    user: str,
    effort: str = "medium",
    max_tokens: int = 16000,
    tools: list | None = None,
    schema: dict | None = None,
) -> str:
    """Send one prompt to Claude and return the text reply.

    Pass tools=[WEB_SEARCH] to let Claude search the web while answering.
    Pass schema={...} (a JSON Schema) to get back JSON text that matches it.
    """
    output_config = {"effort": effort}
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    messages = [{"role": "user", "content": user}]
    extra = {"tools": tools} if tools else {}
    try:
        key = _clean_key()
        client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()
        for _ in range(MAX_CONTINUATIONS + 1):
            response = client.beta.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                output_config=output_config,
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
    except anthropic.AuthenticationError as e:
        sys.exit(
            f"The API rejected the key (401: {_api_message(e)}).\n{_key_hint(key)}\n"
            "Check the key is active at console.anthropic.com > API Keys, then run "
            "export ANTHROPIC_API_KEY=... again in this same window."
        )
    except anthropic.PermissionDeniedError as e:
        sys.exit(f"The key works but isn't allowed to do this (403): {_api_message(e)}")
    except anthropic.RateLimitError:
        sys.exit("Hit the API rate limit. Wait a minute and try again.")
    except anthropic.APIStatusError as e:
        sys.exit(f"Claude API error {e.status_code}: {_api_message(e)}")
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
