import os, json
from google import genai
from google.genai import types
from pathlib import Path
from typing import Any
from storage import JsonFile

def _load_dotenv() -> None:
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]

    for env_path in env_paths:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        break


_load_dotenv()

_PROMPTS: dict[str, str] = {}
for key, filename in {
    "generate_scenes": "outliner.txt",
    "generate_approach": "approacher.txt",
    "generate_storyboard": "storyboarder.txt",
    "generate_raw_html": "html_generator.txt",
    "generate_styles": "html_styler.txt",
    "generate_animations": "html_animator.txt",
    "generate_transcript": "transcripter.txt",
}.items():
    prompt_path = Path(__file__).resolve().parent / "Prompts" / filename
    _PROMPTS[key] = prompt_path.read_text(encoding="utf-8")

def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)

    project = os.getenv("GEMINI_PROJECT")
    location = os.getenv("GEMINI_LOCATION")
    if project and location:
        return genai.Client(vertexai=True, project=project, location=location)

    raise RuntimeError(
        "Missing Gemini credentials. Set GEMINI_API_KEY or GEMINI_PROJECT and GEMINI_LOCATION."
    )

_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def _chat_complete(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> str:
    system_lines: list[str] = []
    parts: list[str] = []

    for m in messages:
        if m["role"] == "system":
            system_lines.append(m["content"])
        else:
            parts.append(f"{m['role'].upper()}:\n{m['content']}")

    config = types.GenerateContentConfig(
        system_instruction="\n".join(system_lines) if system_lines else None,
        temperature=temperature,
    )
    if max_tokens is not None:
        config.max_output_tokens = max_tokens

    client = _get_client()
    response = client.models.generate_content(
        model=_MODEL,
        config=config,
        contents="\n\n".join(parts),
    )

    return response.text.strip()

def _extract_json(text: str) -> Any:
    text = text.strip()
    if not text:
        raise ValueError("Empty response received from the LLM")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for open_char, close_char in (("{", "}"), ("[", "]")):
        start = text.find(open_char)
        end = text.rfind(close_char)
        if start == -1 or end == -1 or end <= start:
            continue
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError("Could not parse JSON from the LLM response")


def _format_list(items: list[Any]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _format_json(obj: Any) -> str:
    return json.dumps(obj.data if isinstance(obj, JsonFile) else obj, indent=2, ensure_ascii=False)

def generate_scenes(
    prompt: str,
) -> list[dict]:
    if not prompt.strip(): raise ValueError("Prompt is required!")
    messages = [
        {"role": "system", "content": _PROMPTS["generate_scenes"]},
        {"role": "user", "content": prompt},
    ]
    content = _chat_complete(messages, max_tokens=10000)
    result = _extract_json(content)
    if isinstance(result, dict) and "scenes" in result:
        scenes = result["scenes"]
    else:
        raise Exception("Cannot find scenes!")

    if not isinstance(scenes, list):
        raise ValueError("Expected a list of scene objects from generate_scenes")
    return [{**i, 'status': False} for i in scenes]


def generate_approach(
    meta: JsonFile,
    previous_titles: list[str],
    next_titles: list[str],
    previous_approaches: list[str],
    previous_storyboardss: list[str],
    assets: str,
) -> str:
    message = [
        "Scene metadata:",
        _format_json(meta.data),
        "Scene title:",
        meta['title'],
        "Previous scene titles:",
        _format_list(previous_titles) if previous_titles else "(none)",
        "Next scene titles:",
        _format_list(next_titles) if next_titles else "(none)",
        "Assets:",
        assets,
        "Some of previous approaches:",
        _format_list(previous_approaches) if previous_approaches else "(none)",
        "Some of previous storyboard specifications:",
        "\n\n".join(previous_storyboardss) if previous_storyboardss else "(none)",
    ]
    messages = [
        {"role": "system", "content": _PROMPTS["generate_approach"]},
        {"role": "user", "content": "\n\n".join(message)},
    ]
    return _chat_complete(messages, max_tokens=12000)

def generate_storyboard(
    meta: dict,
    approach: str,
    transcript: str,
    assets: str,
    previous_storyboards: str | None = None,
) -> str:
    message = [
        "Scene metadata:",
        _format_json(meta),
        "Educational approach:",
        approach,
        "Transcript of Current Scene:",
        transcript,
        "Assets:",
        assets,
    ]
    if previous_storyboards:
        message.extend(["Previous storyboard history:", previous_storyboards])
    messages = [
        {"role": "system", "content": _PROMPTS["generate_storyboard"]},
        {"role": "user", "content": "\n\n".join(message)},
    ]
    return _chat_complete(messages, max_tokens=14000)


def generate_raw_html(
    meta: dict,
    html_scene: str,
    assets: str,
) -> str:
    messages = [
        {"role": "system", "content": _PROMPTS["generate_raw_html"]},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    "Scene metadata:",
                    _format_json(meta),
                    "Storyboard specification:",
                    html_scene,
                    "Assets:",
                    assets,
                ]
            ),
        },
    ]
    return _chat_complete(messages, max_tokens=14000)


def generate_styles(
    meta: dict,
    html_scene: str,
    raw_html: str,
) -> str:
    messages = [
        {"role": "system", "content": _PROMPTS["generate_styles"]},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    "Scene metadata:",
                    _format_json(meta),
                    "Storyboard specification:",
                    html_scene,
                    "Raw HTML:",
                    raw_html,
                ]
            ),
        },
    ]
    return _chat_complete(messages, max_tokens=12000)


def generate_animations(
    meta: dict,
    html_scene: str,
    styled_html: str,
) -> str:
    messages = [
        {"role": "system", "content": _PROMPTS["generate_animations"]},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    "Scene metadata:",
                    _format_json(meta),
                    "Storyboard specification:",
                    html_scene,
                    "Styled HTML:",
                    styled_html,
                ]
            ),
        },
    ]
    return _chat_complete(messages, max_tokens=12000)


def generate_transcript(
    meta: dict,
    approach: str,
) -> str:
    messages = [
        {"role": "system", "content": _PROMPTS["generate_transcript"]},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    "Scene metadata:",
                    _format_json(meta),
                    "Educational approach:",
                    approach,
                ]
            ),
        },
    ]
    return _chat_complete(messages, max_tokens=12000)


def _extract_audio_bytes(response: types.GenerateContentResponse) -> bytes:
    if getattr(response, "candidates", None):
        for candidate in response.candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", None) or []
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data is not None:
                    data = getattr(inline_data, "data", None)
                    if isinstance(data, (bytes, bytearray)):
                        return bytes(data)
                    if isinstance(data, str):
                        return data.encode("utf-8")
    raise ValueError("Could not extract audio bytes from Gemini audio response")


def generate_audio(
    meta: dict,
    transcript: str,
) -> bytes:
    client = _get_client()
    response = client.models.generate_content(
        model=os.getenv(
            "GEMINI_TTS_MODEL",
            "gemini-2.5-flash-preview-tts",
        ),
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=os.getenv("GEMINI_VOICE", "Kore")
                    )
                )
            ),
        ),
        contents=transcript,
    )

    return _extract_audio_bytes(response)
