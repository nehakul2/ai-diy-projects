"""Read text aloud, or save it as audio, with the computer's built-in voice. No extra installs.

macOS uses `say`, Windows uses the built-in System.Speech voice, Linux uses espeak-ng or espeak
(install with your package manager, e.g. `sudo apt install espeak-ng`).
"""
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path


def _engine() -> str:
    system = platform.system()
    if system == "Darwin" and shutil.which("say"):
        return "say"
    if system == "Windows" and shutil.which("powershell"):
        return "powershell"
    for name in ("espeak-ng", "espeak"):
        if shutil.which(name):
            return name
    raise ValueError("No text-to-speech voice found. On Linux, install espeak-ng; on Mac and Windows it's built in.")


def audio_suffix() -> str:
    """File type this computer can write: .m4a on Mac, .wav elsewhere."""
    return ".m4a" if _engine() == "say" else ".wav"


def speak(text: str, out: Path | None = None, rate: int = 175) -> Path | None:
    """Read `text` aloud, or save it to `out` (Mac: .m4a or .aiff; others: .wav)."""
    engine = _engine()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text)
        script = f.name
    try:
        if engine == "say":
            cmd = ["say", "-r", str(rate), "-f", script]
            if out:
                cmd += ["-o", str(out)] + (["--data-format=aac"] if out.suffix == ".m4a" else [])
        elif engine == "powershell":
            target = f"$s.SetOutputToWaveFile('{out}');" if out else ""
            ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                  f"{target} $s.Speak([IO.File]::ReadAllText('{script}')); $s.Dispose()")
            cmd = ["powershell", "-NoProfile", "-Command", ps]
        else:
            cmd = [engine, "-s", str(rate), "-f", script] + (["-w", str(out)] if out else [])
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise ValueError(f"The speech voice failed: {e.stderr.decode(errors='replace').strip() or e}") from None
    finally:
        Path(script).unlink(missing_ok=True)
    return out
