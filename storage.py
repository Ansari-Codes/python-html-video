import json
from pathlib import Path
from typing import Any, Literal

class JsonFile:
    def __init__(self, file_name: str | Path, initial: dict[str, Any] | None = None) -> None:
        self.fn = Path(file_name)
        self.fn.parent.mkdir(parents=True, exist_ok=True)
        if self.fn.exists():
            self.data = json.loads(self.fn.read_text("utf-8"))
        else:
            self.data = initial or {}
            self.fn.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def save(self) -> None:self.fn.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
    def __getitem__(self, key: Any) -> Any: return self.data[key]
    def __setitem__(self, key: Any, value: Any) -> None:
        self.data[key] = value
        self.save()
    def get(self, key: Any, default: Any = None) -> Any:return self.data.get(key, default)
    def setdefault(self, key: Any, default: Any = None) -> Any:
        value = self.data.setdefault(key, default)
        self.save()
        return value
    def to_dict(self) -> dict[str, Any]: return self.data
    def __iter__(self): return iter(self.data)
    def __str__(self) -> str:
        return json.dumps(self.data, indent=4)

_STAGE_KEYS = [
    "approach_done",
    "storyboard_done",
    "raw_html_done",
    "styling_done",
    "animation_done",
    "transcript_done",
    "audio_done",
    "render_done",
]
class STAGES:
    approach = "approach_done"
    storyboard = "storyboard_done"
    html = "raw_html_done"
    styling = "styling_done"
    animation = "animation_done"
    transcription = "transcript_done"
    audio = "audio_done"
    render = "render_done"


def _to_path(pdir: str | Path) -> Path: return Path(pdir)
def _project_meta_path(pdir: str | Path) -> Path: return _to_path(pdir) / "meta.json"
def _scene_directory(pdir: str | Path, s_no: int) -> Path: return _to_path(pdir) / f"scene_{s_no:03d}"
def _scene_meta_path(pdir: str | Path, s_no: int) -> Path: return _scene_directory(pdir, s_no) / "meta.json"
def _scene_status_path(pdir: str | Path, s_no: int) -> Path: return _scene_directory(pdir, s_no) / "status.json"
def _scene_file_path(pdir: str | Path, s_no: int, filename: str) -> Path: return _scene_directory(pdir, s_no) / filename
def _write_file(path: Path, content: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):path.write_bytes(content)
    else:path.write_text(str(content), encoding="utf-8")
    return path
def write_file(pdir: str | Path, s_no: int, name: str, content: str | bytes) -> Path:
    return _write_file(_scene_file_path(pdir, s_no, name), content)


def load_assets(pdir: str | Path) -> dict[str, Any]:
    assets_path = _to_path(pdir) / "Assets" / "assets.json"
    if not assets_path.exists():
        return {}
    return json.loads(assets_path.read_text("utf-8"))


def format_assets(assets: dict[str, Any]) -> str:
    if not assets:
        return "(no assets)"
    lines: list[str] = []
    for name, item in assets.items():
        kind = item.get("type", "file")
        if kind == "emoji":
            lines.append(f"{name}: {item.get('emoji')} - {item.get('description', '')}")
        else:
            path = item.get("path", "")
            desc = item.get("description", "")
            lines.append(f"{name}: {path} - {desc}")
    return "\n".join(lines)


# --------------------------------------------------------------------
# Project
# --------------------------------------------------------------------

def initialize_project(pdir: str | Path, title: str, prompt: str, scenes: list) -> JsonFile:
    pdir = _to_path(pdir)
    pdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "title": title,
        "prompt": prompt,
        "scenes": scenes
    }
    return JsonFile(_project_meta_path(pdir), initial=meta)


def load_project_meta(pdir: str | Path) -> dict[str, Any]:return JsonFile(_project_meta_path(pdir)).to_dict()
def save_project_meta(pdir: str | Path, meta: dict[str, Any]) -> None:
    jf = JsonFile(_project_meta_path(pdir))
    jf.data = meta
    jf.save()


# --------------------------------------------------------------------
# Scene
# --------------------------------------------------------------------
SCENE_FILES = ['approach.md', 'scene.html', 'transcript.txt', 'storyboard.md']
def create_scene(pdir: str | Path, s_no: int, title: str, duration: int) -> tuple[JsonFile, JsonFile]:
    scene_dir = _scene_directory(pdir, s_no)
    scene_dir.mkdir(parents=True, exist_ok=True)
    meta = {"number": s_no, "title": title, "duration": duration}
    status = {key: False for key in _STAGE_KEYS}
    for s in SCENE_FILES:
        if not (scene_dir/s).exists(): (scene_dir/s).touch()
    return JsonFile(_scene_meta_path(pdir, s_no), initial=meta), JsonFile(_scene_status_path(pdir, s_no), initial=status)


def load_scene_meta(pdir: str | Path, s_no: int):return JsonFile(_scene_meta_path(pdir, s_no))
def save_scene_meta(pdir: str | Path, s_no: int, meta: dict[str, Any]) -> None:
    jf = JsonFile(_scene_meta_path(pdir, s_no))
    jf.data = meta
    jf.save()


# --------------------------------------------------------------------
# Status
# --------------------------------------------------------------------

def load_status(pdir: str | Path, s_no: int):return JsonFile(_scene_status_path(pdir, s_no))
def save_status(pdir: str | Path, s_no: int, status: dict[str, Any]) -> None:
    jf = JsonFile(_scene_status_path(pdir, s_no))
    jf.data = status
    jf.save()

def mark_completed(pdir: str | Path, s_no: int, stage: Literal[
        "approach_done",
        "storyboard_done",
        "raw_html_done",
        "styling_done",
        "animation_done",
        "transcript_done",
        "audio_done",
        "render_done",
    ]) -> None:
    if stage not in _STAGE_KEYS:
        raise ValueError(f"Unknown stage: {stage}")
    jf = JsonFile(_scene_status_path(pdir, s_no))
    jf.data[stage] = True
    jf.save()

# --------------------------------------------------------------------
# Approach
# --------------------------------------------------------------------

def save_approach(pdir: str | Path, s_no: int, text: str) -> Path:return write_file(pdir, s_no, "approach.md", text)
def load_approach(pdir: str | Path, s_no: int) -> str:return _scene_file_path(pdir, s_no, "approach.md").read_text("utf-8")

# --------------------------------------------------------------------
# Storyboard
# --------------------------------------------------------------------

def save_storyboard(pdir: str | Path, s_no: int, text: str) -> Path:return write_file(pdir, s_no, "storyboard.md", text)
def load_storyboard(pdir: str | Path, s_no: int) -> str:return _scene_file_path(pdir, s_no, "storyboard.md").read_text("utf-8")


# --------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------

def save_html(pdir: str | Path, s_no: int, html: str) -> Path:return write_file(pdir, s_no, "scene.html", html)
def load_html(pdir: str | Path, s_no: int) -> str:return _scene_file_path(pdir, s_no, "scene.html").read_text("utf-8")

# --------------------------------------------------------------------
# Transcript
# --------------------------------------------------------------------

def save_transcript(pdir: str | Path, s_no: int, transcript: str) -> Path:return write_file(pdir, s_no, "transcript.txt", transcript)
def load_transcript(pdir: str | Path, s_no: int) -> str:return _scene_file_path(pdir, s_no, "transcript.txt").read_text("utf-8")


# --------------------------------------------------------------------
# Audio
# --------------------------------------------------------------------

def save_audio(pdir: str | Path, s_no: int, audio: bytes, extension: str = "wav") -> Path:return write_file(pdir, s_no, f"narration.{extension}", audio)
def load_audio(pdir: str | Path, s_no: int) -> bytes:return _scene_file_path(pdir, s_no, "narration.wav").read_bytes()


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def scene_path(pdir: str | Path, s_no: int) -> Path: return _scene_directory(pdir, s_no)
def scene_exists(pdir: str | Path, s_no: int) -> bool: return _scene_directory(pdir, s_no).is_dir()
def list_scenes(pdir: str | Path) -> list[int]:
    root = _to_path(pdir)
    if not root.exists():return []
    scene_numbers: list[int] = []
    for child in root.iterdir():
        if not child.is_dir() or not child.name.startswith("scene_"):continue
        suffix = child.name[len("scene_"):]
        if not suffix.isdigit():continue
        scene_numbers.append(int(suffix))
    return sorted(scene_numbers)
