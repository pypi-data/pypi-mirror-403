#!/usr/bin/env python3
"""
**Internal copy of `server.py`** packaged under `kamiwaza_mlx` so end-users can
simply run:

    python -m kamiwaza_mlx.server -m <model> [--port 1234]

The body of the file is identical to the original standalone script (save for
this prologue) to avoid any behavioural changes during the move.
"""

from __future__ import annotations

import argparse, base64, io, json, logging, math, re, time, uuid, asyncio, os, threading, fnmatch
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Optional

import requests, uvicorn, mlx.core as mx
from PIL import Image
from fastapi import FastAPI, Request
from fastapi import HTTPException
import shutil as _shutil
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, model_validator

try:  # pragma: no cover - allows running from source tree without package install
    from .distributed_runtime import setup_runtime
except ImportError:  # pragma: no cover - fallback when executed as a script
    from distributed_runtime import setup_runtime  # type: ignore

try:  # pragma: no cover - local package import
    from .lib.parsers.tool import get_tool_parser, list_tool_parsers
except ImportError:  # pragma: no cover - fallback when executed as script
    from lib.parsers.tool import get_tool_parser, list_tool_parsers  # type: ignore

# Import for prompt caching
from mlx_lm.models.cache import make_prompt_cache, save_prompt_cache, load_prompt_cache
from mlx_lm.models.cache import RotatingKVCache, QuantizedKVCache, KVCache
from mlx_lm.models.cache import can_trim_prompt_cache, trim_prompt_cache

# ────────────────────────── CLI & logging ──────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", default="mlx-community/Qwen2-VL-2B-Instruct-4bit")
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", type=int, default=18_000)
parser.add_argument("-V", "--vision", action="store_true", help="Force vision pipeline; otherwise auto-detect.")
parser.add_argument("--strip-thinking", action="store_true")
parser.add_argument(
    "--enable-auto-think-detection",
    type=lambda x: (str(x).lower() == 'true'),
    default=True,
    help="Enable auto-detection of chat templates that prepend <think> (default: True).",
)
parser.add_argument("--enable-prefix-caching", type=lambda x: (str(x).lower() == 'true'), default=True, help="Enable system message caching (default: True). Caches system messages for reuse across requests with the same system context.")
parser.add_argument("--prompt-cache-dir", type=str, default="./.cache/mlx_prompt_caches/", help="Directory to store/load system message cache files.")
parser.add_argument(
    "--tool-call-parser",
    type=str,
    default="auto",
    help="Tool call parser to use (auto, openai-json, minimax-m2, none).",
)
parser.add_argument(
    "--tool-call-parser-config",
    type=str,
    default="",
    help="Override JSON config for tool parser selection (used when --tool-call-parser=auto).",
)
parser.add_argument(
    "--kv-cache-max-tokens",
    type=int,
    default=0,
    help="Per-cache upper bound for KV cache tokens (0 = auto model context).",
)
parser.add_argument(
    "--kv-cache-global-max-tokens",
    type=int,
    default=0,
    help="Global KV cache budget across conversations in tokens (0 = auto model context).",
)
parser.add_argument(
    "--kv-cache-min-tokens",
    type=int,
    default=0,
    help="Lower bound for KV cache tokens when building caches.",
)
parser.add_argument("--kv-cache-keep", type=int, default=1, help="RotatingKVCache keep tokens when trimming.")
parser.add_argument("--prefix-cache-headroom", type=int, default=64, help="Extra tokens added to system-prefix cache size.")
parser.add_argument("--disable-kv-cache", action="store_true", help="Disable all KV caching (prefix + conversation)")
parser.add_argument("--enable-conversation-cache", type=lambda x: (str(x).lower() == 'true'), default=True, help="Enable conversation-scoped KV caching (default: True)")
parser.add_argument("--conversation-kv-max-tokens", type=int, default=0, help="Max tokens to retain per conversation KV cache (0 = auto model context)")
parser.add_argument("--conversation-max-convs", type=int, default=1, help="Max number of conversation caches to keep in memory")
parser.add_argument("--conversation-ttl-seconds", type=int, default=3600, help="Idle TTL for conversation caches (seconds)")
parser.add_argument("--conversation-snapshots", type=int, default=0, help="Snapshots to retain per conversation (default: 0)")
parser.add_argument("--conversation-auto-id", type=lambda x: (str(x).lower() == 'true'), default=True, help="Automatically bind requests without an explicit conversation id to a per-client conversation (default: True)")
parser.add_argument("--conversation-auto-fixed", type=str, default="_default", help="Fallback id to use if client address is unavailable and auto-id is enabled")
# Disk persistence (manual, via endpoints)
parser.add_argument("--conversation-disk-dir", type=str, default="/tmp/kamiwaza_mlx", help="Directory for conversation KV cache files (manual save/load endpoints)")
parser.add_argument("--conversation-disk-budget-mb", type=int, default=25, help="Approx total size budget (MB) for on-disk conversation caches (default: 25 MB)")
parser.add_argument("--conversation-disk-max-gb", type=int, default=200, help="Hard per-save limit for a single KV cache file (GiB)")
parser.add_argument("--trace-requests-path", type=str, default="", help="Write JSONL request/response traces for /v1/chat/completions (empty disables).")
parser.add_argument(
    "--trace-requests-include-prompt",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Include the built prompt text in trace logs (can be large).",
)
parser.add_argument(
    "--kv-cache-sizing",
    choices=["full", "efficient", "none", "never"],
    default="full",
    help=(
        "KV cache sizing policy: 'full' caps caches to the full context and enforces a global budget, "
        "'efficient' starts at --kv-cache-initial-tokens and grows by --kv-cache-grow-chunk, "
        "'none' allocates lazily with no pre-reserve, 'never' disables persistent KV caching."
    ),
)
parser.add_argument(
    "--kv-cache-initial-tokens",
    type=int,
    default=32768,
    help="Initial KV cache allocation (tokens) when using efficient sizing.",
)
parser.add_argument(
    "--kv-cache-grow-chunk",
    type=int,
    default=8192,
    help="Token chunk size used when growing KV caches under efficient sizing.",
)
parser.add_argument(
    "--kv-cache-grow-threshold",
    type=float,
    default=0.75,
    help="Utilisation ratio that triggers post-generation KV cache growth (efficient sizing).",
)
parser.add_argument(
    "--kv-cache-idle-release-seconds",
    type=int,
    default=0,
    help="Idle time before KV caches are released (0 disables release, default).",
)
parser.add_argument(
    "--mx-cache-clear-on-idle-seconds",
    type=int,
    default=5,
    help="Clear MX allocator cache after N seconds of inactivity (0 disables).",
)
parser.add_argument(
    "--kv-cache-hard-reserve",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Attempt to fully reserve KV cache memory up to the sizing target.",
)
parser.add_argument(
    "--retain-mx-cache",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Keep MX runtime memory allocations (disables internal mx.clear_cache calls).",
)
parser.add_argument(
    "--lazy-load",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Load model weights lazily on first request (default: False = load eagerly).",
)
parser.add_argument(
    "--kv-cache-warmup",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Run a warm-up forward pass at startup to materialize KV cache geometry and reserve memory.",
)
parser.add_argument(
    "--kv-cache-warmup-tokens",
    type=int,
    default=0,
    help="Number of tokens to use during the startup KV warm-up (0 = use full context target).",
)
parser.add_argument(
    "--distributed",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Enable multi-node inference via mlx.distributed (auto when PAIRED_HOST is set).",
)
parser.add_argument(
    "--distributed-rank",
    type=int,
    default=None,
    help="Rank of this process when running distributed inference.",
)
parser.add_argument(
    "--distributed-world-size",
    type=int,
    default=None,
    help="Total number of distributed participants (defaults to 2 when PAIRED_HOST is set).",
)
parser.add_argument(
    "--distributed-host",
    type=str,
    default=None,
    help="Hostname/IP used for the mlx.distributed rendezvous (defaults to $PAIRED_HOST).",
)
parser.add_argument(
    "--distributed-port",
    type=int,
    default=None,
    help="TCP port used for mlx.distributed rendezvous (defaults to 17863).",
)
parser.add_argument(
    "--distributed-timeout",
    type=float,
    default=None,
    help="Seconds to wait for distributed rendezvous/collectives (default: 120).",
)
parser.add_argument(
    "--distributed-env-file",
    type=str,
    default=None,
    help="Optional path to a .env file providing PAIRED_HOST / rank values.",
)
parser.add_argument(
    "--distributed-server-rank",
    type=int,
    default=0,
    help="Rank that should host the HTTP server when distributed is enabled.",
)
args = parser.parse_args()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

TRACE_REQUESTS_PATH = (args.trace_requests_path or "").strip()
TRACE_REQUESTS_INCLUDE_PROMPT = bool(args.trace_requests_include_prompt)
TRACE_REQUESTS_ENABLED = bool(TRACE_REQUESTS_PATH)
TRACE_REQUESTS_LOCK = threading.Lock()
if TRACE_REQUESTS_ENABLED:
    try:
        trace_path = Path(TRACE_REQUESTS_PATH).expanduser()
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        TRACE_REQUESTS_PATH = str(trace_path)
    except Exception:
        pass
    log.info("Request tracing enabled: %s", TRACE_REQUESTS_PATH)

if args.kv_cache_sizing == "never":
    args.disable_kv_cache = True
    args.enable_prefix_caching = False
    args.enable_conversation_cache = False
    args.kv_cache_warmup = False
    args.kv_cache_hard_reserve = False
elif args.kv_cache_sizing == "none":
    args.kv_cache_warmup = False
    args.kv_cache_hard_reserve = False

DISTRIBUTED = setup_runtime(args, log)

if args.disable_kv_cache and args.enable_prefix_caching:
    log.info("KV cache disabled; skipping prefix caching setup.")
    args.enable_prefix_caching = False

MX_CLEAR_CACHE_ORIG = getattr(mx, "clear_cache", None)
if args.retain_mx_cache and MX_CLEAR_CACHE_ORIG is not None:
    def _noop_mx_clear_cache() -> None:  # noqa: D401 - trivial noop
        return None

    mx.clear_cache = _noop_mx_clear_cache  # type: ignore[assignment]
    log.info("Retaining MX runtime allocations (mx.clear_cache disabled).")
# ───────────────────────── timers / tiny helpers ─────────────────────────

class _Timer:  # noqa: D101 – internal util
    __slots__ = ("start", "in_tok")

    def __init__(self, in_tok: int):
        self.start = time.perf_counter()
        self.in_tok = in_tok
        logging.info("Starting generation with %d input tokens", in_tok)

    def done(self, out_tok: int):
        dt = time.perf_counter() - self.start
        tps = 0.0 if dt == 0 else out_tok / dt
        logging.info(
            "Generation completed: %d output tokens in %.2fs (%.2f output tokens/sec)", out_tok, dt, tps
        )


# ───────────────────────── constants / regex ───────────────────────
MAX_TOKENS = -1
PATCH_LIMIT = 1536
PATCH_SIZE = 32
THINK_RE = re.compile(r"<think>(.*?)</think>", re.S | re.I)  # capture group!
AUTO_THINK_MIN_TOKENS = 50
AUTO_THINK_DETECTED = False
AUTO_THINK_SOURCE = ""
MODEL_PATH: Optional[Path] = None

# ──────────────────────────── helpers ──────────────────────────────

def _encode(txt: str):
    if hasattr(PROCESSOR, "encode"):
        return mx.array(PROCESSOR.encode(txt))
    if hasattr(PROCESSOR, "tokenizer"):
        return mx.array(PROCESSOR.tokenizer.encode(txt))
    return mx.array(txt.split())  # fallback

def _tok_len(text: str) -> int:
    # Add safety check for None/empty text
    if text is None:
        log.warning("_tok_len received None text")
        return 0
    if not isinstance(text, str):
        log.warning("_tok_len received non-string: %s = %r", type(text), text)
        text = str(text) if text is not None else ""
    
    if hasattr(PROCESSOR, "encode"):
        return len(PROCESSOR.encode(text))
    if hasattr(PROCESSOR, "tokenizer"):
        return len(PROCESSOR.tokenizer.encode(text))
    return len(text.split())  # hopeless fallback


def _trace_enabled() -> bool:
    return TRACE_REQUESTS_ENABLED


def _trace_headers(request: Request) -> Dict[str, str]:
    keys = ("x-conversation-id", "x-request-id", "x-forwarded-for", "user-agent")
    out: Dict[str, str] = {}
    for key in keys:
        val = request.headers.get(key)
        if val:
            out[key] = val
    return out


def _trace_write(entry: Dict[str, Any]) -> None:
    if not TRACE_REQUESTS_ENABLED or not TRACE_REQUESTS_PATH:
        return
    try:
        payload = json.dumps(entry, ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Trace serialization failed: {exc}")
        return
    try:
        with TRACE_REQUESTS_LOCK:
            with open(TRACE_REQUESTS_PATH, "a", encoding="utf-8") as handle:
                handle.write(payload + "\n")
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Trace write failed: {exc}")


def _trace_begin(req: "ChatReq", request: Request, prompt_str: str) -> Optional[Dict[str, Any]]:
    if not TRACE_REQUESTS_ENABLED:
        return None
    try:
        req_payload = req.model_dump()
    except Exception:
        req_payload = {"model": req.model}
    entry: Dict[str, Any] = {
        "ts": time.time(),
        "path": str(request.url.path),
        "client": request.client.host if request.client else None,
        "headers": _trace_headers(request),
        "request": req_payload,
    }
    if TRACE_REQUESTS_INCLUDE_PROMPT:
        entry["prompt"] = prompt_str
    req.__dict__["_trace_entry"] = entry
    if getattr(req, "stream", False):
        req.__dict__["_trace_raw_parts"] = []
        req.__dict__["_trace_parts"] = []
    return entry


def _trace_append(req: "ChatReq", *, raw_piece: Optional[str] = None, out_piece: Optional[str] = None) -> None:
    if not TRACE_REQUESTS_ENABLED:
        return
    raw_parts = req.__dict__.get("_trace_raw_parts")
    if raw_parts is not None and raw_piece:
        raw_parts.append(raw_piece)
    out_parts = req.__dict__.get("_trace_parts")
    if out_parts is not None and out_piece:
        out_parts.append(out_piece)


def _trace_finalize(
    req: "ChatReq",
    *,
    raw_text: Optional[str] = None,
    text: Optional[str] = None,
    finish_reason: Optional[str] = None,
    tool_calls: Optional[Any] = None,
    usage: Optional[Dict[str, Any]] = None,
) -> None:
    if not TRACE_REQUESTS_ENABLED:
        return
    entry = req.__dict__.get("_trace_entry")
    if not isinstance(entry, dict):
        return
    if raw_text is None:
        raw_text = "".join(req.__dict__.get("_trace_raw_parts", []))
    if text is None:
        text = "".join(req.__dict__.get("_trace_parts", []))
    response: Dict[str, Any] = {
        "content": text,
        "raw_content": raw_text,
    }
    reasoning_content = req.__dict__.get("_reasoning_content")
    if reasoning_content:
        response["reasoning_content"] = reasoning_content
    if tool_calls is not None:
        response["tool_calls"] = tool_calls
    if finish_reason:
        response["finish_reason"] = finish_reason
    if usage is not None:
        response["usage"] = usage
    entry["response"] = response
    _trace_write(entry)
    req.__dict__.pop("_trace_entry", None)
    req.__dict__.pop("_trace_raw_parts", None)
    req.__dict__.pop("_trace_parts", None)


def _model_cfg(model) -> Dict[str, Any]:
    cfg = getattr(model, "config", {})
    return cfg if isinstance(cfg, dict) else cfg.__dict__


def _model_ctx_len(model) -> Optional[int]:
    """Best-effort detection of model context length from config."""
    cfg = _model_cfg(model)
    for k in (
        "max_position_embeddings",
        "max_sequence_length",
        "max_seq_len",
        "seq_len",
        "n_ctx",
        "context_length",
    ):
        v = cfg.get(k)
        if isinstance(v, int) and v > 0:
            return int(v)
    # Fallback: check model directory config.json if available
    try:
        mdl_path = Path(args.model)
        if mdl_path.exists():
            cfg_json = json.loads((mdl_path / "config.json").read_text())
            for k in (
                "max_position_embeddings",
                "max_sequence_length",
                "max_seq_len",
                "seq_len",
                "n_ctx",
                "context_length",
            ):
                v = cfg_json.get(k)
                if isinstance(v, int) and v > 0:
                    log.info("Context length %d detected from config.json.", v)
                    return int(v)
    except Exception:
        pass
    return None


def _resolve_model_path(repo: str) -> Path:
    """Best-effort path resolution across mlx_lm versions."""
    from mlx_lm import utils as lm_utils

    if hasattr(lm_utils, "get_model_path"):
        return lm_utils.get_model_path(repo)
    try:
        from mlx_lm import get_model_path as _get_model_path
    except Exception:
        _get_model_path = None
    if _get_model_path is not None:
        return _get_model_path(repo)
    model_path = Path(repo)
    if model_path.exists():
        return model_path
    try:
        from huggingface_hub import snapshot_download
    except Exception:
        return model_path
    try:
        return Path(
            snapshot_download(
                repo,
                allow_patterns=[
                    "*.json",
                    "*.safetensors",
                    "*.py",
                    "tokenizer.model",
                    "*.tiktoken",
                    "tiktoken.model",
                    "*.txt",
                    "*.jsonl",
                ],
            )
        )
    except Exception:
        return model_path


def _load_model_config(model_path: Path) -> Dict[str, Any]:
    try:
        from mlx_lm import utils as lm_utils

        if hasattr(lm_utils, "load_config"):
            return lm_utils.load_config(model_path)
    except Exception:
        pass
    try:
        return json.loads((model_path / "config.json").read_text())
    except Exception:
        return {}


def strip_thoughts(text: str, flag: bool) -> str:
    return THINK_RE.sub("", text) if flag else text


def _set_auto_think_detected(source: str) -> None:
    global AUTO_THINK_DETECTED, AUTO_THINK_SOURCE
    if not args.enable_auto_think_detection:
        return
    if AUTO_THINK_DETECTED:
        return
    AUTO_THINK_DETECTED = True
    AUTO_THINK_SOURCE = source
    log.info("Auto-think detected (%s).", source)


def _has_unclosed_think_tag(text: str) -> bool:
    lower = text.lower()
    last_open = lower.rfind("<think>")
    if last_open == -1:
        return False
    last_close = lower.rfind("</think>")
    return last_close == -1 or last_open > last_close


def _template_suggests_auto_think(template: str) -> bool:
    lower = template.lower()
    if "<think>" not in lower:
        return False
    marker = lower.rfind("add_generation_prompt")
    tail = lower[marker:] if marker != -1 else lower
    last_open = tail.rfind("<think>")
    if last_open == -1:
        return False
    last_close = tail.rfind("</think>")
    return last_close == -1 or last_open > last_close


def _iter_chat_template_sources(model_path: Optional[Path], processor: Any) -> List[Tuple[str, str]]:
    sources: List[Tuple[str, str]] = []
    if model_path and model_path.exists():
        jinja_path = model_path / "chat_template.jinja"
        if jinja_path.exists():
            try:
                sources.append(("chat_template.jinja", jinja_path.read_text(encoding="utf-8")))
            except Exception:
                pass
        for cfg_name in ("tokenizer_config.json", "config.json"):
            cfg_path = model_path / cfg_name
            if not cfg_path.exists():
                continue
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            tpl = cfg.get("chat_template")
            if isinstance(tpl, str):
                sources.append((f"{cfg_name}:chat_template", tpl))
    tpl = getattr(processor, "chat_template", None)
    if isinstance(tpl, str):
        sources.append(("processor.chat_template", tpl))
    return sources


def _detect_auto_think_template(processor: Any, model_path: Optional[Path]) -> bool:
    if not args.enable_auto_think_detection:
        return False
    if hasattr(processor, "apply_chat_template"):
        try:
            probe = processor.apply_chat_template(
                [{"role": "user", "content": "Hello"}],
                tokenize=False,
                add_generation_prompt=True,
            )
            if isinstance(probe, str) and _has_unclosed_think_tag(probe):
                _set_auto_think_detected("rendered chat template")
                return True
        except Exception as e:
            log.debug("Auto-think detection render failed: %s", e)
    for source, template in _iter_chat_template_sources(model_path, processor):
        if _template_suggests_auto_think(template):
            _set_auto_think_detected(source)
            return True
    return False


def _supports_chat_template_tools(processor: Any) -> bool:
    if not hasattr(processor, "apply_chat_template"):
        return False
    try:
        processor.apply_chat_template(
            [{"role": "user", "content": "tool_probe"}],
            tokenize=False,
            add_generation_prompt=False,
            tools=[],
        )
        return True
    except TypeError:
        return False
    except Exception:
        return False


def _load_tool_parser_config(path: str) -> Dict[str, Any]:
    default_path = Path(__file__).resolve().parent / "config" / "tool_parsers.json"
    cfg_path = Path(path) if path else default_path
    try:
        if cfg_path.exists():
            return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Tool parser config load failed (%s): %s", cfg_path, exc)
    return {}


def _select_tool_parser_name(model_name: str, cfg: Dict[str, Any]) -> str:
    name = (model_name or "").lower()
    patterns = cfg.get("patterns") or []
    for rule in patterns:
        pattern = str(rule.get("pattern", "")).lower()
        parser_name = str(rule.get("parser", "")).strip()
        match_type = str(rule.get("match", "glob")).lower()
        if not pattern or not parser_name:
            continue
        try:
            if match_type == "regex":
                if re.search(pattern, name):
                    return parser_name
            else:
                if fnmatch.fnmatch(name, pattern):
                    return parser_name
        except Exception:
            continue
    default_parser = cfg.get("default") or "openai-json"
    return str(default_parser)


def _normalize_tools(tools: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for t in tools or []:
        if hasattr(t, "model_dump"):
            out.append(t.model_dump(exclude_none=True))
        elif isinstance(t, dict):
            out.append(t)
    return out


def _split_reasoning_content(text: str) -> Tuple[str, str]:
    if not text:
        return text, ""
    lower = text.lower()
    open_idx = lower.find("<think>")
    close_idx = lower.find("</think>")
    reasoning_parts = THINK_RE.findall(text)
    if open_idx != -1 and close_idx == -1:
        reasoning_tail = text[open_idx + len("<think>") :]
        if reasoning_tail:
            reasoning_parts.append(reasoning_tail)
        content = text[:open_idx]
    else:
        content = THINK_RE.sub("", text)
    reasoning = "\n\n".join(part.strip() for part in reasoning_parts if part is not None).strip()
    return content, reasoning


def _postprocess_thinking(text: str, strip: bool) -> Tuple[str, str]:
    if not text:
        return "", ""
    lower = text.lower()
    close_idx = lower.find("</think>")
    open_idx = lower.find("<think>")

    if close_idx != -1 and (open_idx == -1 or close_idx < open_idx):
        if args.enable_auto_think_detection:
            _set_auto_think_detected("output saw </think> without <think>")
        reasoning_raw = text[:close_idx]
        reasoning = reasoning_raw.strip()
        content = text[close_idx + len("</think>") :]
        if strip:
            content = content.lstrip("\n")
        return content.lstrip("\n"), reasoning

    if not strip:
        if args.enable_auto_think_detection and close_idx != -1 and open_idx == -1:
            _set_auto_think_detected("output saw </think> without <think>")
        return _split_reasoning_content(text)

    if not args.enable_auto_think_detection:
        return _split_reasoning_content(strip_thoughts(text, True))

    if AUTO_THINK_DETECTED and open_idx == -1 and close_idx == -1:
        if _tok_len(text) > AUTO_THINK_MIN_TOKENS:
            return text, ""
        return "", ""

    return _split_reasoning_content(strip_thoughts(text, True))


def _cap_image(img: Image.Image) -> Image.Image:
    w, h = img.size
    patches = math.ceil(w / PATCH_SIZE) * math.ceil(h / PATCH_SIZE)
    if patches <= PATCH_LIMIT:
        return img
    scale = math.sqrt(PATCH_LIMIT / patches)
    return img.resize((int(w * scale), int(h * scale)), Image.BICUBIC)


def load_image(ref: str) -> Image.Image:
    if ref.startswith("data:image/"):
        img = Image.open(io.BytesIO(base64.b64decode(ref.split(",", 1)[1])))
    elif ref.startswith("http"):
        img = Image.open(io.BytesIO(requests.get(ref, timeout=15).content))
    else:
        img = Image.open(ref)
    return _cap_image(img.convert("RGB"))


def _hash_tokens(toks: mx.array) -> str:
    """Return SHA256 hash of token id array (1-D view)."""
    import hashlib, numpy as _np
    # Ensure toks is an mx.array, convert to numpy, flatten, and hash
    # The .astype('uint32') is important for consistent hashing across platforms/setups
    # if the token IDs are, for instance, int64 by default from the tokenizer.
    flat_numpy_array = _np.array(toks, copy=False).astype('uint32').ravel()
    return hashlib.sha256(flat_numpy_array.tobytes()).hexdigest()


def _mx_length(arr) -> int:
    """Return total element count for an mx.array-like object."""
    if hasattr(arr, "size"):
        try:
            return int(arr.size)
        except Exception:
            pass
    if hasattr(arr, "shape"):
        try:
            return int(arr.shape[-1])
        except Exception:
            pass
    try:
        return int(len(arr))
    except Exception:
        return 0


def _iter_cache_nodes(cache_obj: Any):
    if isinstance(cache_obj, (list, tuple)):
        for item in cache_obj:
            yield from _iter_cache_nodes(item)
    elif hasattr(cache_obj, "caches"):
        try:
            for item in getattr(cache_obj, "caches"):
                yield from _iter_cache_nodes(item)
        except Exception:
            yield cache_obj
    else:
        yield cache_obj


def _cache_token_count(cache_obj: Any) -> int:
    """Best-effort cache length in tokens (includes generated tokens)."""
    counts: List[int] = []
    for node in _iter_cache_nodes(cache_obj):
        offset = getattr(node, "offset", None)
        if offset is None:
            continue
        try:
            counts.append(int(offset))
        except Exception:
            continue
    return max(counts) if counts else 0


def _cache_capacity_tokens(cache_obj: Any) -> int:
    """Best-effort allocated cache capacity in tokens."""
    max_tokens = 0
    for node in _iter_cache_nodes(cache_obj):
        keys = getattr(node, "keys", None)
        if keys is None:
            continue
        if isinstance(keys, (list, tuple)) and keys:
            keys = keys[0]
        try:
            max_tokens = max(max_tokens, int(keys.shape[2]))
        except Exception:
            continue
    return max_tokens


def _array_nbytes(arr: Any) -> int:
    if arr is None:
        return 0
    if isinstance(arr, (list, tuple)):
        return sum(_array_nbytes(item) for item in arr)
    try:
        return int(arr.nbytes)
    except Exception:
        try:
            return int(arr.size) * int(arr.dtype.size)  # type: ignore[attr-defined]
        except Exception:
            return 0


def _shape_repr(arr: Any) -> Any:
    if arr is None:
        return None
    if isinstance(arr, (list, tuple)):
        return [_shape_repr(item) for item in arr]
    try:
        return list(arr.shape)
    except Exception:
        return None


def _dtype_repr(arr: Any) -> Any:
    if arr is None:
        return None
    if isinstance(arr, (list, tuple)):
        return [_dtype_repr(item) for item in arr]
    try:
        return str(arr.dtype)
    except Exception:
        return None


def _kv_token_capacity_from_keys(keys: Any) -> int:
    if keys is None:
        return 0
    if isinstance(keys, (list, tuple)) and keys:
        keys = keys[0]
    if keys is None:
        return 0
    try:
        return int(keys.shape[2])
    except Exception:
        return 0


def _cache_node_summary(node: Any) -> Dict[str, Any]:
    keys = getattr(node, "keys", None)
    values = getattr(node, "values", None)
    return {
        "type": node.__class__.__name__,
        "offset": int(getattr(node, "offset", 0) or 0),
        "max_size": int(getattr(node, "max_size", 0) or 0) or None,
        "keep": int(getattr(node, "keep", 0) or 0) or None,
        "capacity_tokens": _kv_token_capacity_from_keys(keys),
        "keys_shape": _shape_repr(keys),
        "values_shape": _shape_repr(values),
        "keys_dtype": _dtype_repr(keys),
        "values_dtype": _dtype_repr(values),
        "bytes": _array_nbytes(keys) + _array_nbytes(values),
    }


def _cache_summary(cache_obj: Any, *, verbose: bool) -> Optional[Dict[str, Any]]:
    if cache_obj is None:
        return None
    nodes = []
    total_bytes = 0
    capacity_tokens = 0
    types: set[str] = set()
    for node in _iter_cache_nodes(cache_obj):
        summary = _cache_node_summary(node)
        nodes.append(summary)
        total_bytes += int(summary.get("bytes") or 0)
        capacity_tokens = max(capacity_tokens, int(summary.get("capacity_tokens") or 0))
        types.add(summary.get("type") or "")
    payload = {
        "total_bytes": int(total_bytes),
        "capacity_tokens": int(capacity_tokens),
        "used_tokens": int(_cache_token_count(cache_obj)),
        "node_count": int(len(nodes)),
        "types": sorted(t for t in types if t),
    }
    if verbose:
        payload["nodes"] = nodes
    return payload


def _trim_cache_to(cache_obj: Any, target_tokens: int) -> int:
    """Trim cache to a target prefix length, if possible."""
    if cache_obj is None:
        return 0
    target = max(int(target_tokens), 0)
    current = _cache_token_count(cache_obj)
    if current <= target:
        return 0
    if not can_trim_prompt_cache(cache_obj):
        return 0
    return trim_prompt_cache(cache_obj, int(current - target))


def _kv_cache_limit(cli_cap: Optional[int]) -> Optional[int]:
    """Return the hard upper bound for KV caches given CLI cap and model context."""
    cap = _positive_or_none(cli_cap)
    try:
        ctx = _model_ctx_len(MODEL)
    except NameError:
        ctx = None
    if ctx is not None and isinstance(ctx, int) and ctx > 0:
        cap = ctx if cap is None else min(cap, int(ctx))
    return cap


def _infer_layer_geometries(model) -> List[Optional[Dict[str, Any]]]:
    """Best-effort extraction of per-layer KV geometry (kv heads, dims, dtypes)."""
    geoms: List[Optional[Dict[str, Any]]] = []
    layers = getattr(model, "layers", [])
    for layer in layers:
        attn = None
        for attr in ("self_attn", "attention", "attn", "mha", "transformer", "block"):
            attn = getattr(layer, attr, None)
            if attn is not None:
                break
        if attn is None:
            geoms.append(None)
            continue

        kv_heads = (
            getattr(attn, "n_kv_heads", None)
            or getattr(attn, "num_key_value_heads", None)
            or getattr(attn, "num_kv_heads", None)
            or getattr(attn, "num_attention_heads", None)
            or getattr(attn, "n_heads", None)
        )
        head_dim = getattr(attn, "head_dim", None)
        try:
            if head_dim is None:
                # Try to infer from k_proj output size (most reliable for GQA models)
                k_proj = getattr(attn, "k_proj", None)
                if k_proj is not None and hasattr(k_proj, "weight"):
                    k_out_features = k_proj.weight.shape[0]
                    if kv_heads and k_out_features:
                        head_dim = int(k_out_features) // int(kv_heads)

                # Fallback to hidden_size calculation (may be incorrect for GQA)
                if head_dim is None:
                    hidden_size = getattr(attn, "hidden_size", None) or getattr(layer, "hidden_size", None)
                    attn_heads = getattr(attn, "num_attention_heads", None) or getattr(attn, "n_heads", None)
                    if hidden_size and attn_heads:
                        head_dim = int(hidden_size) // int(attn_heads)
        except Exception:
            head_dim = None

        k_proj = getattr(attn, "k_proj", None)
        v_proj = getattr(attn, "v_proj", None)
        dtype_k = getattr(getattr(k_proj, "weight", None), "dtype", None)
        dtype_v = getattr(getattr(v_proj, "weight", None), "dtype", dtype_k)

        if not kv_heads or not head_dim:
            geoms.append(None)
            continue
        try:
            geoms.append(
                {
                    "kv_heads": int(kv_heads),
                    "head_dim": int(head_dim),
                    "dtype_k": dtype_k,
                    "dtype_v": dtype_v or dtype_k,
                }
            )
        except Exception:
            geoms.append(None)
    return geoms


def _ensure_cache_container(cache_obj: Any) -> List[Any]:
    if cache_obj is None:
        return []
    if isinstance(cache_obj, list):
        return cache_obj
    if isinstance(cache_obj, tuple):
        return list(cache_obj)
    return [cache_obj]


KV_CACHE_REGISTRY: Dict[int, Dict[str, Any]] = {}


def _update_layer_geometries_from_cache(cache_obj: Any) -> None:
    layers = _ensure_cache_container(cache_obj)
    if not layers:
        return
    global KV_LAYER_GEOMS
    if not isinstance(KV_LAYER_GEOMS, list):
        KV_LAYER_GEOMS = []
    if len(KV_LAYER_GEOMS) < len(layers):
        KV_LAYER_GEOMS.extend([None] * (len(layers) - len(KV_LAYER_GEOMS)))
    for idx, layer in enumerate(layers):
        if isinstance(layer, RotatingKVCache) and layer.keys is not None:
            try:
                _, heads, _, dim = layer.keys.shape
                dtype_k = layer.keys.dtype
                dtype_v = layer.values.dtype if layer.values is not None else dtype_k
                KV_LAYER_GEOMS[idx] = {
                    "kv_heads": int(heads),
                    "head_dim": int(dim),
                    "dtype_k": dtype_k,
                    "dtype_v": dtype_v,
                }
            except Exception:
                continue


def _warm_cache_with_dummy_tokens(cache_obj: Any, tokens: int) -> None:
    if cache_obj is None or tokens <= 0 or IS_VISION:
        return
    try:
        tok_arr = _encode(" warmup ")
    except Exception:
        tok_arr = mx.array([0], dtype=mx.int32)
    if getattr(tok_arr, "ndim", 1) != 1:
        tok_arr = tok_arr.ravel()
    if tok_arr.size == 0:
        tok_arr = mx.array([0], dtype=mx.int32)
    try:
        tok_arr = tok_arr.astype(mx.int32)
    except Exception:
        pass
    import math as _math

    if int(tok_arr.size) < int(tokens):
        reps = max(int(_math.ceil(tokens / max(int(tok_arr.size), 1))), 1)
        try:
            tok_arr = mx.tile(tok_arr, reps)
        except Exception:
            tok_arr = mx.array(
                list(tok_arr.tolist()) * reps, dtype=tok_arr.dtype  # type: ignore[attr-defined]
            )
    tok_arr = tok_arr[: tokens]
    try:
        tok_arr = mx.expand_dims(tok_arr, 0)
    except Exception:
        tok_arr = tok_arr.reshape((1, -1))

    try:
        MODEL(tok_arr, cache=cache_obj)
    except Exception as exc:
        log.debug(f"Warmup forward failed: {exc}")
        return
    try:
        mx.eval(tok_arr)
    except Exception:
        pass
    _update_layer_geometries_from_cache(cache_obj)
    for node in _iter_cache_nodes(cache_obj):
        if isinstance(node, RotatingKVCache):
            node.offset = 0
            if hasattr(node, "_idx"):
                node._idx = 0


def _cache_register(cache_obj: Any, *, target_tokens: Optional[int], upper_limit: Optional[int], reason: str) -> None:
    if cache_obj is None:
        return
    meta = {
        "target": int(target_tokens) if target_tokens and target_tokens > 0 else None,
        "upper": int(upper_limit) if upper_limit and upper_limit > 0 else None,
        "reason": reason,
        "needs_reserve": bool(args.kv_cache_hard_reserve) and bool(target_tokens),
    }
    KV_CACHE_REGISTRY[id(cache_obj)] = meta

    # Ensure Rotating caches respect the upper limit if provided
    for node in _iter_cache_nodes(cache_obj):
        if isinstance(node, RotatingKVCache) and meta["upper"] is not None:
            try:
                node.max_size = min(int(meta["upper"]), int(node.max_size or meta["upper"]))
            except Exception:
                pass


def _cache_meta(cache_obj: Any) -> Dict[str, Any]:
    return KV_CACHE_REGISTRY.get(id(cache_obj), {})


def _reserve_rotating_layer(
    layer_cache: RotatingKVCache,
    target_tokens: int,
    geom: Optional[Dict[str, Any]],
    *,
    layer_index: int | None = None,
) -> bool:
    try:
        if target_tokens <= 0:
            return True
        if layer_cache.max_size is not None and target_tokens > layer_cache.max_size:
            layer_cache.max_size = int(target_tokens)
        limit = int(layer_cache.max_size) if layer_cache.max_size is not None else int(target_tokens)
        target = min(int(target_tokens), limit)
        if layer_cache.keys is not None and layer_cache.keys.shape[2] >= target:
            return True

        old_keys = layer_cache.keys
        old_vals = layer_cache.values

        if old_keys is not None:
            B, heads, _, dim = old_keys.shape
            dtype_k = old_keys.dtype
        else:
            if not geom or not geom.get("kv_heads") or not geom.get("head_dim"):
                layer_label = f"layer {layer_index}" if layer_index is not None else "layer"
                log.debug(
                    "Skipping KV hard reserve for %s (geometry unknown before first use).",
                    layer_label,
                )
                return False
            B = 1
            heads = int(geom.get("kv_heads"))
            dim = int(geom.get("head_dim"))
            dtype_k = geom.get("dtype_k") if geom and geom.get("dtype_k") is not None else mx.float16

        if old_vals is not None:
            _, _, _, v_dim = old_vals.shape
            dtype_v = old_vals.dtype
        else:
            v_dim = dim
            dtype_v = geom.get("dtype_v") if geom and geom.get("dtype_v") is not None else dtype_k

        new_len = int(target)
        if new_len <= 0:
            return True
        new_keys = mx.zeros((B, heads, new_len, dim), dtype=dtype_k)
        new_vals = mx.zeros((B, heads, new_len, v_dim), dtype=dtype_v)

        if old_keys is not None:
            copy_len = min(old_keys.shape[2], new_len)
            if copy_len > 0:
                new_keys[..., :copy_len, :] = old_keys[..., :copy_len, :]
        if old_vals is not None:
            copy_len = min(old_vals.shape[2], new_len)
            if copy_len > 0:
                new_vals[..., :copy_len, :] = old_vals[..., :copy_len, :]

        layer_cache.keys = new_keys
        layer_cache.values = new_vals
        layer_cache.offset = min(int(layer_cache.offset), new_len)
        if hasattr(layer_cache, "_idx"):
            layer_cache._idx = min(int(layer_cache._idx), new_len)
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning(f"KV cache reservation failed: {exc}")
        return False


def _hard_reserve_cache(cache_obj: Any) -> None:
    if not args.kv_cache_hard_reserve:
        return
    meta = _cache_meta(cache_obj)
    target = meta.get("target")
    if not target:
        return
    layers = _ensure_cache_container(cache_obj)
    all_ok = True
    for idx, layer in enumerate(layers):
        if isinstance(layer, RotatingKVCache):
            geom = None
            if "KV_LAYER_GEOMS" in globals():
                geoms = globals().get("KV_LAYER_GEOMS", [])
                if idx < len(geoms):
                    geom = geoms[idx]
            ok = _reserve_rotating_layer(layer, int(target), geom, layer_index=idx)
            if not ok:
                all_ok = False
        elif isinstance(layer, KVCache):
            # KVCache has no size metadata; nothing to do.
            continue
    meta["needs_reserve"] = not all_ok


def _ensure_cache_ready(cache_obj: Any) -> None:
    if cache_obj is None:
        return
    meta = _cache_meta(cache_obj)
    if meta.get("needs_reserve"):
        _hard_reserve_cache(cache_obj)


def _release_cache_memory(cache_obj: Any) -> None:
    if cache_obj is None:
        return
    for node in _iter_cache_nodes(cache_obj):
        if isinstance(node, RotatingKVCache):
            node.keys = None
            node.values = None
            node.offset = 0
            if hasattr(node, "_idx"):
                node._idx = 0
        elif isinstance(node, KVCache):
            node.state = None
    meta = _cache_meta(cache_obj)
    if meta:
        meta["needs_reserve"] = bool(args.kv_cache_hard_reserve) and bool(meta.get("target"))


def _reset_cache_offsets(cache_obj: Any) -> None:
    if cache_obj is None:
        return
    for node in _iter_cache_nodes(cache_obj):
        if hasattr(node, "offset"):
            try:
                node.offset = 0
            except Exception:
                pass
        if hasattr(node, "_idx"):
            try:
                node._idx = 0
            except Exception:
                pass
        if hasattr(node, "start_position"):
            try:
                node.start_position = 0
            except Exception:
                pass


def _maybe_expand_cache(cache_obj: Any, usage_tokens: int) -> None:
    meta = _cache_meta(cache_obj)
    if not meta:
        return
    target = meta.get("target")
    upper = meta.get("upper")
    if not target or not upper:
        return
    if args.kv_cache_sizing != "efficient":
        return
    if usage_tokens <= 0:
        return
    threshold = float(args.kv_cache_grow_threshold or 0.75)
    if target >= upper:
        return
    chunk = max(int(args.kv_cache_grow_chunk or 1), 1)
    new_target = int(target)
    grew = False
    while new_target < int(upper) and usage_tokens >= threshold * new_target:
        next_target = min(int(upper), new_target + chunk)
        if next_target <= new_target:
            break
        new_target = next_target
        grew = True
    if not grew:
        return
    layers = _ensure_cache_container(cache_obj)
    all_ok = True
    for idx, layer in enumerate(layers):
        if isinstance(layer, RotatingKVCache):
            geom = None
            if "KV_LAYER_GEOMS" in globals():
                geoms = globals().get("KV_LAYER_GEOMS", [])
                if idx < len(geoms):
                    geom = geoms[idx]
            ok = _reserve_rotating_layer(layer, new_target, geom, layer_index=idx)
            if ok:
                layer.max_size = int(new_target)
            else:
                all_ok = False
    meta["target"] = new_target
    meta["needs_reserve"] = not all_ok


def _maybe_clear_mx_cache(reason: str) -> None:
    if MX_CLEAR_CACHE_ORIG is None:
        return
    try:
        MX_CLEAR_CACHE_ORIG()
        log.info("MX allocator cache cleared (%s).", reason)
    except Exception as exc:  # noqa: BLE001
        log.warning("MX allocator cache clear failed: %s", exc)


def _cache_idle_release() -> None:
    idle_kv = int(getattr(args, "kv_cache_idle_release_seconds", 0) or 0)
    idle_mx = int(getattr(args, "mx_cache_clear_on_idle_seconds", 0) or 0)
    if idle_kv <= 0 and idle_mx <= 0:
        return
    now = time.time()
    last_activity = globals().get("KV_CACHE_LAST_ACTIVITY", now)
    idle_for = now - last_activity
    did_any = False

    if idle_kv > 0:
        last_release = globals().get("KV_CACHE_LAST_RELEASE", 0.0)
        if idle_for >= idle_kv and (now - last_release) >= idle_kv:
            if globals().get("GLOBAL_PROMPT_CACHE") is not None:
                _release_cache_memory(globals()["GLOBAL_PROMPT_CACHE"])
            warm = globals().get("GLOBAL_WARMUP_CACHE")
            if warm is not None:
                _release_cache_memory(warm)
            try:
                for rec in list(CONV_KV._map.values()):  # noqa: SLF001
                    _release_cache_memory(rec.cache)
            except Exception:
                pass
            globals()["KV_CACHE_LAST_RELEASE"] = now
            did_any = True

    if idle_mx > 0:
        last_clear = globals().get("MX_CACHE_LAST_CLEAR", 0.0)
        if idle_for >= idle_mx and (now - last_clear) >= idle_mx:
            _maybe_clear_mx_cache(f"idle {idle_for:.1f}s")
            globals()["MX_CACHE_LAST_CLEAR"] = now
            did_any = True

    if did_any:
        globals()["KV_CACHE_LAST_ACTIVITY"] = now


def _set_rotating_keep(cache_obj: Any, keep: int) -> None:
    keep = int(keep)
    for node in _iter_cache_nodes(cache_obj):
        if isinstance(node, RotatingKVCache):
            node.keep = keep


def _positive_or_none(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    try:
        value = int(value)
    except Exception:
        return None
    return value if value > 0 else None


def _global_kv_budget_tokens() -> Optional[int]:
    budget = _positive_or_none(getattr(args, "kv_cache_global_max_tokens", None))
    if budget:
        return int(budget)
    return _kv_cache_limit(args.kv_cache_max_tokens)


def _resolve_cache_size(
    *, ensure: int = 0, cli_cap: Optional[int] = None, prefer_ensure: bool = False
) -> Tuple[Optional[int], Optional[int]]:
    """Determine (initial_size, upper_limit) for KV cache allocations."""

    ensure = max(int(ensure), 0)
    min_tokens = max(int(args.kv_cache_min_tokens), 0)
    lower_bound = max(ensure, min_tokens)

    limit = _kv_cache_limit(cli_cap)

    if limit is None:
        if args.kv_cache_sizing != "efficient":
            return (lower_bound if lower_bound > 0 else None, None)
        init = max(int(args.kv_cache_initial_tokens), 0)
        if init <= 0:
            init = lower_bound
        if init <= 0 and lower_bound <= 0:
            return (None, None)
        chosen = max(init, lower_bound)
        return (chosen, None)

    if lower_bound > limit:
        log.debug(
            "Requested cache lower bound %d exceeds limit %d; using limit.",
            lower_bound,
            limit,
        )
        return (limit, limit)

    if args.kv_cache_sizing != "efficient":
        if prefer_ensure and lower_bound > 0:
            cap = min(lower_bound, limit)
            return (cap, cap)
        return (limit, limit)

    init = max(int(args.kv_cache_initial_tokens), 0)
    if init <= 0:
        init = lower_bound
    if init <= 0:
        init = limit
    chosen = max(init, lower_bound)
    chosen = min(chosen, limit)
    return (chosen, limit)


def _legacy_prompt_cache(max_tokens: Optional[int], keep: int) -> List[Any]:
    try:
        num_layers = len(MODEL.layers)
    except Exception:
        cfg = _model_cfg(MODEL)
        num_layers = int(cfg.get("num_hidden_layers", 32))

    if max_tokens is None:
        log.info("Falling back to unbounded KVCache instances (legacy path).")
        return [KVCache() for _ in range(num_layers)]

    max_tokens = max(int(max_tokens), 1)
    log.info(
        "Falling back to RotatingKVCache instances (legacy path) max_size=%d keep=%d.",
        max_tokens,
        keep,
    )
    return [RotatingKVCache(max_size=max_tokens, keep=int(keep)) for _ in range(num_layers)]


def _allocate_prompt_cache(
    max_tokens: Optional[int],
    *,
    keep: int,
    reason: str,
    upper_limit: Optional[int],
) -> List[Any]:
    try:
        prompt_cache = make_prompt_cache(MODEL, max_kv_size=max_tokens)
    except Exception as exc:  # noqa: BLE001 – one-off fallback
        log.warning(
            "make_prompt_cache failed for %s (%s); using legacy allocation.",
            reason,
            exc,
        )
        prompt_cache = _legacy_prompt_cache(max_tokens, keep)
        _cache_register(prompt_cache, target_tokens=max_tokens, upper_limit=upper_limit, reason=reason)
        _hard_reserve_cache(prompt_cache)
        return prompt_cache

    desc = "unbounded" if max_tokens is None else str(int(max_tokens))
    log.info("Allocating prompt cache (%s): max_size=%s, keep=%d", reason, desc, keep)
    _set_rotating_keep(prompt_cache, keep)
    _cache_register(prompt_cache, target_tokens=max_tokens, upper_limit=upper_limit, reason=reason)
    _hard_reserve_cache(prompt_cache)
    return prompt_cache


def _claim_warmup_cache_for_conversation(
    *,
    max_tokens: Optional[int],
    upper_limit: Optional[int],
    reason: str,
) -> Optional[List[Any]]:
    warm = globals().get("GLOBAL_WARMUP_CACHE")
    if warm is None:
        return None
    if warm is globals().get("GLOBAL_PROMPT_CACHE"):
        return None
    if args.disable_kv_cache or not args.enable_conversation_cache:
        return None
    meta = _cache_meta(warm)
    target = meta.get("target")
    if max_tokens is not None and target is not None and int(target) > int(max_tokens):
        log.info(
            "Releasing warmup cache (target %d > desired %d).",
            int(target),
            int(max_tokens),
        )
        _release_cache_memory(warm)
        globals()["GLOBAL_WARMUP_CACHE"] = None
        return None

    desc = "unbounded" if max_tokens is None else str(int(max_tokens))
    _cache_register(warm, target_tokens=max_tokens, upper_limit=upper_limit, reason=reason)
    _reset_cache_offsets(warm)
    _hard_reserve_cache(warm)
    globals()["GLOBAL_WARMUP_CACHE"] = None
    log.info("Reusing warmup cache for %s (max_size=%s).", reason, desc)
    return warm


def _prepare_cache_for_system_only(
    req: ChatReq,
    global_prompt_cache: Optional[List[Any]],
    cached_prefix_len: int,
    cache_prefix_hash: str,
    is_vision_model: bool,
    enable_prefix_caching_arg: bool,
    func_name_for_log: str
) -> Tuple[Optional[List[Any]], int, mx.array]:
    """Prepare cache and suffix for system-only caching approach."""
    
    if is_vision_model or not enable_prefix_caching_arg:
        # No caching for vision models
        prompt_str = build_prompt(req, 0)
        prompt_ids = _encode(prompt_str)
        return None, 0, prompt_ids
    
    # Check if we have system messages
    system_prompt_str = build_system_prompt(req)
    if not system_prompt_str:
        # No system messages, can't use cache
        prompt_str = build_prompt(req, 0)
        prompt_ids = _encode(prompt_str)
        return None, 0, prompt_ids

    # Build full prompt once to ensure cache suffix alignment.
    full_prompt_str = build_prompt(req, 0)
    
    # Check if cache is valid for current system prompt
    system_ids = _encode(system_prompt_str)
    system_hash = _hash_tokens(system_ids)
    
    cache_to_use = None
    actual_cached_len = 0
    
    if (global_prompt_cache is not None and 
        cached_prefix_len > 0 and 
        cache_prefix_hash == system_hash):
        # Cache is valid for this system prompt
        _ensure_cache_ready(global_prompt_cache)
        cache_to_use = global_prompt_cache
        actual_cached_len = cached_prefix_len
        log.info(f"✅ Using cached system prompt ({actual_cached_len} tokens) in {func_name_for_log}")
        
        # Slice the full prompt so suffix tokens exactly follow the cached prefix.
        if full_prompt_str.startswith(system_prompt_str):
            suffix_text = full_prompt_str[len(system_prompt_str):]
            suffix_ids = _encode(suffix_text)
        else:
            log.warning(
                "System prompt cache prefix mismatch in %s; falling back to full prompt.",
                func_name_for_log,
            )
            cache_to_use = None
            actual_cached_len = 0
            suffix_ids = _encode(full_prompt_str)
    else:
        # Cache doesn't match or doesn't exist
        if global_prompt_cache is not None:
            log.info(f"❌ System prompt hash mismatch in {func_name_for_log}, not using cache")
        
        # Use full prompt
        suffix_ids = _encode(full_prompt_str)
    
    # Ensure suffix is not empty
    if suffix_ids.ndim == 1 and len(suffix_ids) == 0:
        # This shouldn't happen with properly formed prompts, but just in case
        log.warning(f"Empty suffix in {func_name_for_log}, using full prompt")
        prompt_str = build_prompt(req, 0)
        suffix_ids = _encode(prompt_str)
        cache_to_use = None
        actual_cached_len = 0

    req.__dict__["_prefix_cache_used"] = (cache_to_use is not None and cache_to_use is global_prompt_cache)
    
    return cache_to_use, actual_cached_len, suffix_ids


def _usage_dict(in_tok: int, out_tok: int, dur: float, reasoning_tok: int, cached_tok: int) -> Dict[str, Any]:
    """Return an OpenAI-style `usage` dict including optional reasoning tokens."""

    return {
        "input_tokens": in_tok,
        "input_tokens_details": {"cached_tokens": int(cached_tok)},
        "output_tokens": out_tok,
        "output_tokens_details": {"reasoning_tokens": reasoning_tok},
        "total_tokens": in_tok + out_tok,
        "tokens_per_second": (in_tok + out_tok) / max(dur, 1e-6),  # never ÷0
    }


def load_model(repo: str) -> Tuple[Any, Any, bool]:
    global MODEL_PATH
    if MODEL_PATH is None:
        path_hint = Path(repo)
        if path_hint.exists():
            MODEL_PATH = path_hint
    want_vl = args.vision or "vl" in Path(repo).name.lower()
    if want_vl:
        try:
            from mlx_vlm import load as vlm_load
            # // Do NOT pass HF config dict into mlx_vlm.load(); it reads the repo itself.
            model, proc = vlm_load(repo)
            log.info("🖼️  vision model loaded via mlx-vlm")
            return model, proc, True
        except Exception as e:  # noqa: BLE001 – blanket log here is fine
            msg = str(e)
            if "AutoVideoProcessor requires the Torchvision" in msg:
                log.error("GLM-V video preprocessor present but torchvision missing.")
                log.error("Either install torchvision (to keep video) or remove "
                          "video_preprocessor_config.json (image-only).")
                raise  # don't drop to LM for glm4v_moe
            log.warning("vision load failed (%s) – falling back to LM", e)

    from mlx_lm import utils as lm_utils

    model_path = _resolve_model_path(repo)
    MODEL_PATH = model_path
    config_override: Dict[str, Any] = {}
    config = _load_model_config(model_path)
    if config.get("model_type") == "minimax_m2":
        config_override["model_type"] = "minimax"
        log.info("Aliasing model_type minimax_m2 -> minimax for MLX compatibility.")

    # Use lazy=True to avoid materializing parameters immediately; reduces peak mem at startup
    load_kwargs = {"lazy": args.lazy_load}
    if config_override:
        load_kwargs["model_config"] = config_override
    try:
        model, config = lm_utils.load_model(model_path, **load_kwargs)
    except TypeError:
        load_kwargs.pop("model_config", None)
        if config_override:
            log.warning(
                "mlx_lm.load_model does not accept model_config; minimax_m2 alias may be ignored."
            )
        model, config = lm_utils.load_model(model_path, **load_kwargs)
    try:
        tok = lm_utils.load_tokenizer(model_path, eos_token_ids=config.get("eos_token_id", None))
    except TypeError:
        tok = lm_utils.load_tokenizer(model_path)
    log.info("💬  language model loaded via mlx-lm")
    return model, tok, False


MODEL, PROCESSOR, IS_VISION = load_model(args.model)
MODEL_NAME = Path(args.model).name
MODEL_CREATED = int(time.time())
CHAT_TEMPLATE_SUPPORTS_TOOLS = _supports_chat_template_tools(PROCESSOR)
TOOL_PARSER_CONFIG = _load_tool_parser_config(args.tool_call_parser_config)
TOOL_PARSER_NAME = ""
TOOL_PARSER = None
try:
    _detect_auto_think_template(PROCESSOR, MODEL_PATH)
except Exception as e:
    log.warning("Auto-think detection failed: %s", e)
KV_LAYER_GEOMS = _infer_layer_geometries(MODEL)
KV_CACHE_LAST_ACTIVITY = time.time()
KV_CACHE_LAST_RELEASE = 0.0
MX_CACHE_LAST_CLEAR = 0.0
GLOBAL_WARMUP_CACHE = None
CTX_HINT = _model_ctx_len(MODEL)
if CTX_HINT:
    log.info("Detected model context length: %d tokens.", CTX_HINT)
else:
    log.warning(
        "Could not detect model context length from config; KV warmup will rely on CLI overrides."
    )

DISTRIBUTED.after_model_load(MODEL)

def _server_warmup_after_load() -> None:
    global GLOBAL_WARMUP_CACHE, KV_LAYER_GEOMS
    if args.disable_kv_cache or IS_VISION or not args.kv_cache_warmup:
        return

    cfg_tokens = int(args.kv_cache_warmup_tokens)
    ensure_hint = max(cfg_tokens, 0)
    warmup_cap = _positive_or_none(args.conversation_kv_max_tokens)
    if warmup_cap is None:
        warmup_cap = _positive_or_none(args.kv_cache_max_tokens)
    max_size, upper_limit = _resolve_cache_size(
        ensure=ensure_hint,
        cli_cap=warmup_cap,
    )

    target_tokens = cfg_tokens if cfg_tokens > 0 else (upper_limit or max_size or CTX_HINT)
    if target_tokens is None or target_tokens <= 0:
        log.info("Skipping KV warmup (no target tokens resolved).")
        return

    warm_cache = _allocate_prompt_cache(
        target_tokens,
        keep=args.kv_cache_keep,
        reason="warmup",
        upper_limit=upper_limit,
    )
    _warm_cache_with_dummy_tokens(warm_cache, int(target_tokens))
    _update_layer_geometries_from_cache(warm_cache)
    _hard_reserve_cache(warm_cache)
    GLOBAL_WARMUP_CACHE = warm_cache
    KV_LAYER_GEOMS = KV_LAYER_GEOMS or _infer_layer_geometries(MODEL)
    desc = "unbounded" if target_tokens is None else str(int(target_tokens))
    log.info(
        "🔥 KV warmup complete (%s tokens, hard_reserve=%s).",
        desc,
        args.kv_cache_hard_reserve,
    )

# Perform warmup after model load if requested
try:
    _server_warmup_after_load()
except Exception as warm_exc:
    log.warning(f"KV warmup skipped due to error: {warm_exc}")

# Global variables for system message caching
GLOBAL_PROMPT_CACHE = None
GLOBAL_CACHE_FILE_PATH: str | None = None
CACHE_PRIMED_THIS_SESSION = False
CACHED_PREFIX_LEN = 0
CACHE_PREFIX_HASH = ""
SYSTEM_PROMPT_CACHE_FAILS = 0
SYSTEM_PROMPT_CACHE_SUCCESSES = 0
SYSTEM_PROMPT_CACHE_DISABLED = False
SYSTEM_PROMPT_CACHE_FAIL_LIMIT = 2

if args.enable_prefix_caching and not IS_VISION:
    try:
        # Sanitize model name for use as a filename
        sanitized_model_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', MODEL_NAME)
        cache_dir = Path(args.prompt_cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        GLOBAL_CACHE_FILE_PATH = str(cache_dir / f"{sanitized_model_name}.safetensors")
        log.info(f"System message cache path set to: {GLOBAL_CACHE_FILE_PATH}")

        if os.path.exists(GLOBAL_CACHE_FILE_PATH):
            log.info(f"Attempting to load system message cache from {GLOBAL_CACHE_FILE_PATH}...")
            GLOBAL_PROMPT_CACHE = load_prompt_cache(GLOBAL_CACHE_FILE_PATH) 
            log.info("System message cache loaded successfully.")
            CACHE_PRIMED_THIS_SESSION = True # If loaded, it's already primed
            SYSTEM_PROMPT_CACHE_SUCCESSES += 1
            # load len
            len_path = GLOBAL_CACHE_FILE_PATH + ".len"
            if os.path.exists(len_path):
                try:
                    CACHED_PREFIX_LEN = int(Path(len_path).read_text())
                except Exception:
                    CACHED_PREFIX_LEN = 0
            # load hash
            hash_path = GLOBAL_CACHE_FILE_PATH + ".hash"
            if os.path.exists(hash_path):
                try:
                    CACHE_PREFIX_HASH = Path(hash_path).read_text().strip()
                except Exception:
                    CACHE_PREFIX_HASH = ""
            ensure_len = int(CACHED_PREFIX_LEN or 0) + int(args.prefix_cache_headroom)
            max_size, upper_limit = _resolve_cache_size(
                ensure=ensure_len,
                cli_cap=args.kv_cache_max_tokens,
                prefer_ensure=True,
            )
            _cache_register(GLOBAL_PROMPT_CACHE, target_tokens=max_size, upper_limit=upper_limit, reason="prefix-load")
            _hard_reserve_cache(GLOBAL_PROMPT_CACHE)
            if GLOBAL_WARMUP_CACHE is not None and GLOBAL_WARMUP_CACHE is not GLOBAL_PROMPT_CACHE:
                if args.disable_kv_cache or not args.enable_conversation_cache:
                    _release_cache_memory(GLOBAL_WARMUP_CACHE)
                    GLOBAL_WARMUP_CACHE = GLOBAL_PROMPT_CACHE
                else:
                    log.info("Retaining warmup cache for conversation reuse.")
        else:
            log.info(f"System message cache file not found at {GLOBAL_CACHE_FILE_PATH}. Will be created on first request with a system message.")
    except Exception as e:
        log.error(f"Error during system message cache setup: {e}. Caching might not work.")

# ─────────────────── Pydantic request / schema ────────────────────

class MsgPart(BaseModel):
    type: str
    text: str | None = None
    image_url: Dict[str, str] | None = None


class ToolFunctionSpec(BaseModel):
    name: str
    description: str | None = None
    parameters: Dict[str, Any] | None = None


class ToolSpec(BaseModel):
    type: str  # Only 'function' is supported
    function: ToolFunctionSpec


class ToolCallFunction(BaseModel):
    name: str
    # OpenAI returns arguments as a JSON string; accept dict and stringify later
    arguments: Union[str, Dict[str, Any]]


class ToolCall(BaseModel):
    id: str | None = None
    type: str = "function"
    function: ToolCallFunction


class ChatMsg(BaseModel):
    role: str
    # Allow None when assistant emits tool_calls
    content: Union[str, List[MsgPart], None]
    # Optional OpenAI-compatible tool fields
    tool_calls: List[ToolCall] | None = None
    name: str | None = None          # for role=='tool'
    tool_call_id: str | None = None  # for role=='tool'


class ChatReq(BaseModel):
    model: str = MODEL_NAME
    messages: List[ChatMsg]
    images: List[str] | None = None
    max_tokens: int = MAX_TOKENS
    temperature: float = 1.0
    top_p: float = 1.0
    stream: bool = False
    strip_thinking: bool | None = None
    # Tool-calling (OpenAI-compatible) inputs
    tools: List[ToolSpec] | None = None
    tool_choice: Union[str, Dict[str, Any], None] = None
    parallel_tool_calls: bool | None = True
    # Conversation KV caching
    conversation: str | None = None
    conversation_id: str | None = None
    reset_conversation: bool | None = None

    @model_validator(mode="after")
    def _flatten(self):  # noqa: D401
        imgs, flat = list(self.images or []), []
        for m in self.messages:
            if isinstance(m.content, list):
                buf = []
                for p in m.content:
                    if p.type == "text" and p.text:
                        buf.append(p.text)
                    elif p.type == "image_url" and p.image_url:
                        imgs.append(p.image_url["url"])
                m.content = "\n".join(buf)
            # Normalize None content
            if m.content is None:
                m.content = ""
            # Map tool messages into user-visible text for models that don't know 'tool' role
            if m.role == "tool":
                tool_name = m.name or "tool"
                tool_id = m.tool_call_id or ""
                wrapped = f"<tool_result name=\"{tool_name}\" id=\"{tool_id}\">\n{m.content}\n</tool_result>"
                flat.append({"role": "user", "content": wrapped})
                continue
            # If assistant message has tool_calls, serialize as text markers so the model sees them in-context
            if m.role == "assistant" and m.tool_calls:
                chunks = []
                for i, call in enumerate(m.tool_calls):
                    cid = call.id or f"call_{i+1}"
                    args = call.function.arguments
                    if not isinstance(args, str):
                        try:
                            args = json.dumps(args, ensure_ascii=False)
                        except Exception:
                            args = str(args)
                    chunks.append(
                        f"<tool_call id=\"{cid}\" name=\"{call.function.name}\">\n{args}\n</tool_call>"
                    )
                # Preserve any free-form assistant content around tool calls (rare)
                if m.content:
                    chunks.append(str(m.content))
                flat.append({"role": "assistant", "content": "\n".join(chunks)})
                continue
            flat.append({"role": m.role, "content": m.content})
        self.__dict__["flat"] = flat
        self.__dict__["all_images"] = imgs
        return self


class _ThinkFilter:  # noqa: D401 – simple state machine
    def __init__(self, start_in_think: bool = False):
        self.state = "IN" if start_in_think else "NORMAL"
        self.buf = ""
        self.pending = ""
        self.saw_close_without_open = False
        self.saw_close = False

    def feed(self, s: str) -> str | None:  # noqa: C901 – tiny FSM, keep inline
        self.buf += s
        out = ""
        while True:
            if self.state == "NORMAL":
                buf_lower = self.buf.lower()
                i = buf_lower.find("<think>")
                j = buf_lower.find("</think>")
                if i == -1 and j == -1:
                    out, self.buf = out + self.buf, ""
                    return out
                if j != -1 and (i == -1 or j < i):
                    # Closing tag without a prior <think>; drop it but mark for detection.
                    self.saw_close_without_open = True
                    out += self.buf[:j]
                    self.buf = self.buf[j + 8 :]
                    self.saw_close = True
                    self.state = "STRIP_NL"
                    continue
                out += self.buf[:i]
                self.pending += self.buf[i : i + 7]
                self.buf = self.buf[i + 7 :]
                self.state = "IN"
            elif self.state == "IN":
                buf_lower = self.buf.lower()
                j = buf_lower.find("</think>")
                if j == -1:
                    self.pending += self.buf
                    self.buf = ""
                    return None
                self.pending += self.buf[:j]
                self.buf = self.buf[j + 8 :]
                self.saw_close = True
                self.pending = ""
                self.state = "STRIP_NL"
            elif self.state == "STRIP_NL":
                self.buf = self.buf.lstrip("\n")
                self.state = "NORMAL"

    def flush_fallback(self, min_tokens: int) -> str | None:
        if self.state != "IN" or self.saw_close:
            return None
        pending = self.pending + self.buf
        if not pending:
            return None
        if _tok_len(pending) <= min_tokens:
            return None
        self.pending = ""
        self.buf = ""
        self.state = "NORMAL"
        return pending


def build_prompt(req: ChatReq, n_imgs: int) -> str:
    tools = req.__dict__.get("_tool_template_tools")
    if IS_VISION:
        from mlx_vlm import apply_chat_template

        return apply_chat_template(PROCESSOR, config=_model_cfg(MODEL), prompt=req.flat, num_images=n_imgs)
    if getattr(PROCESSOR, "chat_template", None):
        if tools:
            try:
                return PROCESSOR.apply_chat_template(req.flat, tokenize=False, add_generation_prompt=True, tools=tools)
            except TypeError:
                pass
        return PROCESSOR.apply_chat_template(req.flat, tokenize=False, add_generation_prompt=True)
    chunks = [f"<|{m['role']}|>\n{m['content']}</s>" for m in req.flat]
    chunks.append("<|assistant|>\n")
    return "\n".join(chunks)


def _non_ephemeral(flat_msgs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [m for m in flat_msgs if (not m.get("_ephemeral")) or m.get("_tool_prompt")]


def build_system_prompt(req: ChatReq) -> str:
    """Build prompt containing only system message(s) for caching."""
    tools = req.__dict__.get("_tool_template_tools")
    # Extract only system messages
    system_messages = [m for m in _non_ephemeral(req.flat) if m['role'] == 'system']
    
    if not system_messages:
        return ""
    
    if IS_VISION:
        # For vision models, we can't easily separate system from user in the template
        # So we'll return empty string and not cache for vision models
        return ""
    
    if getattr(PROCESSOR, "chat_template", None):
        # Apply chat template to system messages only
        # Don't add generation prompt since we're not generating yet
        if tools:
            try:
                return PROCESSOR.apply_chat_template(system_messages, tokenize=False, add_generation_prompt=False, tools=tools)
            except TypeError:
                pass
        return PROCESSOR.apply_chat_template(system_messages, tokenize=False, add_generation_prompt=False)
    
    # Manual template formatting for system messages only
    chunks = [f"<|{m['role']}|>\n{m['content']}</s>" for m in system_messages]
    return "\n".join(chunks)


def build_user_and_assistant_prompt(req: ChatReq, n_imgs: int) -> str:
    """Build prompt containing everything after system messages."""
    tools = req.__dict__.get("_tool_template_tools")
    # Extract non-system messages
    non_system_messages = [m for m in _non_ephemeral(req.flat) if m['role'] != 'system']
    
    if not non_system_messages:
        # If only system messages, return just the assistant prompt
        if getattr(PROCESSOR, "chat_template", None):
            return PROCESSOR.apply_chat_template([], tokenize=False, add_generation_prompt=True)
        return "<|assistant|>\n"
    
    if IS_VISION:
        from mlx_vlm import apply_chat_template
        # For vision, we need to include all messages
        return apply_chat_template(PROCESSOR, config=_model_cfg(MODEL), prompt=req.flat, num_images=n_imgs)
    
    if getattr(PROCESSOR, "chat_template", None):
        # Apply chat template to non-system messages and add generation prompt
        if tools:
            try:
                return PROCESSOR.apply_chat_template(non_system_messages, tokenize=False, add_generation_prompt=True, tools=tools)
            except TypeError:
                pass
        return PROCESSOR.apply_chat_template(non_system_messages, tokenize=False, add_generation_prompt=True)
    
    # Manual template formatting
    chunks = [f"<|{m['role']}|>\n{m['content']}</s>" for m in non_system_messages]
    chunks.append("<|assistant|>\n")
    return "\n".join(chunks)


def build_base_prompt(req: ChatReq, n_imgs: int) -> str:
    """Build prompt without the generation prompt (assistant header).
    Used to compute stable string prefixes for incremental tokenization.
    """
    tools = req.__dict__.get("_tool_template_tools")
    flat_msgs = _non_ephemeral(req.flat)
    if IS_VISION:
        # Vision path does not currently support base vs full separation.
        from mlx_vlm import apply_chat_template
        return apply_chat_template(PROCESSOR, config=_model_cfg(MODEL), prompt=flat_msgs, num_images=n_imgs)
    if getattr(PROCESSOR, "chat_template", None):
        if tools:
            try:
                return PROCESSOR.apply_chat_template(flat_msgs, tokenize=False, add_generation_prompt=False, tools=tools)
            except TypeError:
                pass
        return PROCESSOR.apply_chat_template(flat_msgs, tokenize=False, add_generation_prompt=False)
    # Manual template formatting without the trailing assistant cue
    chunks = [f"<|{m['role']}|>\n{m['content']}</s>" for m in flat_msgs]
    return "\n".join(chunks)


def build_base_prompt_for_flat(flat_msgs: List[Dict[str, str]], n_imgs: int, tools: Optional[List[Dict[str, Any]]] = None) -> str:
    """Build base prompt (no generation prompt) for a provided flat message list."""
    flat_msgs = _non_ephemeral(flat_msgs)
    if IS_VISION:
        from mlx_vlm import apply_chat_template
        return apply_chat_template(PROCESSOR, config=_model_cfg(MODEL), prompt=flat_msgs, num_images=n_imgs)
    if getattr(PROCESSOR, "chat_template", None):
        if tools:
            try:
                return PROCESSOR.apply_chat_template(flat_msgs, tokenize=False, add_generation_prompt=False, tools=tools)
            except TypeError:
                pass
        return PROCESSOR.apply_chat_template(flat_msgs, tokenize=False, add_generation_prompt=False)
    chunks = [f"<|{m['role']}|>\n{m['content']}</s>" for m in flat_msgs]
    return "\n".join(chunks)


def _msg_hash(role: str, content: str) -> str:
    import hashlib, re

    text = content or ""
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = (role + "\n" + text).encode("utf-8", errors="ignore")
    return hashlib.sha1(s).hexdigest()[:16]


def _boundary_offsets_for_flat(
    flat_msgs: List[Dict[str, str]],
    n_imgs: int,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> List[int]:
    """Compute cumulative token offsets at the end of each message in flat_msgs.
    Uses incremental delta tokenization of the base prompt to avoid re-encoding
    the entire prefix multiple times.
    """
    offsets: List[int] = []
    prev_base = ""
    total = 0
    filtered = _non_ephemeral(flat_msgs)
    for i in range(len(filtered)):
        base_i = build_base_prompt_for_flat(filtered[: i + 1], n_imgs, tools=tools)
        delta = base_i[len(prev_base):]
        ids = _encode(delta)
        dn = int(ids.shape[-1] if getattr(ids, 'ndim', 1) != 1 else len(ids))
        total += dn
        offsets.append(total)
        prev_base = base_i
    return offsets


# ─────────────────── generation (vision / language) ───────────────

# ─────────────── tool support helpers (prompt + parsing) ───────────────

def _resolve_tool_parser() -> Optional[Any]:
    global TOOL_PARSER, TOOL_PARSER_NAME
    if args.tool_call_parser.strip().lower() == "none":
        TOOL_PARSER_NAME = "none"
        TOOL_PARSER = None
        return None
    if TOOL_PARSER is not None:
        return TOOL_PARSER
    parser_name = args.tool_call_parser.strip().lower()
    if parser_name == "auto" or not parser_name:
        parser_name = _select_tool_parser_name(MODEL_NAME, TOOL_PARSER_CONFIG)
    parser = get_tool_parser(parser_name)
    if parser is None:
        log.warning(
            "Unknown tool parser '%s' (available: %s). Falling back to openai-json.",
            parser_name,
            ", ".join(list_tool_parsers()),
        )
        parser = get_tool_parser("openai-json")
    TOOL_PARSER = parser
    TOOL_PARSER_NAME = parser.name if parser else "none"
    if parser is not None:
        log.info(
            "Tool call parser selected: %s (chat_template_tools=%s)",
            parser.name,
            parser.uses_chat_template_tools,
        )
    return parser


def _get_forced_tool_name(tool_choice: Union[str, Dict[str, Any], None]) -> Optional[str]:
    if isinstance(tool_choice, dict):
        fn = tool_choice.get("function") or {}
        name = fn.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


def _maybe_parse_arguments_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract a top-level JSON object from text and return it as a dict."""
    s = text.strip()
    m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", s, re.IGNORECASE)
    if m:
        s = m.group(1)
    # Trim to first '{'
    if "{" in s and not s.lstrip().startswith("{"):
        s = s[s.find("{"):]
    # Try full-string parse first
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # Attempt to find the first balanced JSON object
    # Simple brace matching ignoring braces inside quotes
    in_str = False
    esc = False
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    candidate = s[start : i + 1]
                    try:
                        obj = json.loads(candidate)
                        if isinstance(obj, dict):
                            return obj
                    except Exception:
                        pass
    return None

if IS_VISION:  # ──────────── VISION PATH ────────────
    # mlx-vlm API compatibility: generate/stream_generate moved from utils → generate in newer versions
    try:
        from mlx_vlm.utils import generate as vlm_gen, stream_generate as vlm_stream  # older mlx-vlm
    except Exception:  # ImportError or missing attributes
        try:
            from mlx_vlm.generate import generate as vlm_gen, stream_generate as vlm_stream  # newer mlx-vlm
        except Exception:
            # Last-resort granular fallbacks to handle mixed versions
            from mlx_vlm.generate import generate as vlm_gen  # type: ignore
            try:
                from mlx_vlm.generate import stream_generate as vlm_stream  # type: ignore
            except Exception:
                from mlx_vlm.utils import stream_generate as vlm_stream  # type: ignore

    def sync_gen(prompt: str, imgs, req: ChatReq) -> str:  # noqa: D401
        timer = _Timer(len(prompt))
        result = vlm_gen(
            MODEL,
            PROCESSOR,
            prompt,
            image=imgs,
            max_tokens=req.max_tokens,
            temp=req.temperature,
            top_p=req.top_p,
            verbose=False,
        )
        # Normalize return across mlx-vlm versions: GenerationResult | (text, stats) | str
        if hasattr(result, "text"):
            txt = result.text
        elif isinstance(result, tuple):
            txt = result[0]
        else:
            txt = str(result)
        timer.done(_tok_len(txt))
        return txt

    def stream_chunks(prompt: str, imgs, req: ChatReq):  # noqa: C901 – ported as-is
        rid, created, first = f"chatcmpl-{uuid.uuid4()}", int(time.time()), False
        should_strip = args.strip_thinking if req.strip_thinking is None else req.strip_thinking
        timer = _Timer(len(prompt))
        out_tok = 0

        def _emit(chunk: str):
            nonlocal first, out_tok
            if not chunk:
                return
            out_tok += _tok_len(chunk)
            delta = {"content": chunk}
            if not first:
                delta["role"] = "assistant"  # ← add the value!
                first = True
            _trace_append(req, out_piece=chunk)
            return _sse_chunk(rid, created, delta)

        if not should_strip:
            for r in vlm_stream(
                MODEL,
                PROCESSOR,
                prompt,
                image=imgs,
                max_tokens=req.max_tokens,
                temp=req.temperature,
                top_p=req.top_p,
            ):
                if r.text:
                    _trace_append(req, raw_piece=r.text)
                    yield _emit(r.text)
            yield "data: [DONE]\n\n"
            final = {
                "id": rid,
                "object": "chat.completion.chunk",
                "created": created,
                "model": MODEL_NAME,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(final)}\n\n"
            timer.done(out_tok)
            yield "data: [DONE]\n\n"

        state, buf = "NORMAL", ""
        for r in vlm_stream(
            MODEL,
            PROCESSOR,
            prompt,
            image=imgs,
            max_tokens=req.max_tokens,
            temp=req.temperature,
            top_p=req.top_p,
        ):
            if not r.text:
                continue
            _trace_append(req, raw_piece=r.text)
            buf += r.text
            while True:
                if state == "NORMAL":
                    k = buf.find("<think>")
                    if k == -1:
                        chunk, buf = buf, ""
                    else:
                        chunk, buf, state = buf[:k], buf[k + 7 :], "IN_THINK"
                    if chunk:
                        yield _emit(chunk)
                    if k == -1:
                        break
                elif state == "IN_THINK":
                    k = buf.find("</think>")
                    if k == -1:
                        buf = ""
                        break
                    buf, state = buf[k + 8 :], "STRIP"
                elif state == "STRIP":
                    buf = buf.lstrip("\n")
                    state = "NORMAL"
        if buf:
            yield _emit(buf)
        final = {
            "id": rid,
            "object": "chat.completion.chunk",
            "created": created,
            "model": MODEL_NAME,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(final)}\n\n"
        timer.done(out_tok)
        yield "data: [DONE]\n\n"

else:  # ──────────── TEXT-ONLY PATH ────────────
    from mlx_lm.generate import stream_generate as lm_stream
    from mlx_lm.sample_utils import make_sampler

    def _sampler(req: ChatReq):
        return make_sampler(temp=req.temperature, top_p=req.top_p, min_p=0.0, min_tokens_to_keep=1)

    def sync_gen(prompt: str, _imgs, req: ChatReq) -> str:  # noqa: C901, D401
        global GLOBAL_PROMPT_CACHE, CACHED_PREFIX_LEN, CACHE_PREFIX_HASH
        sampler = _sampler(req)
        
        pre = req.__dict__.get("_precomputed_cache")
        if pre is not None:
            cache_to_use, actual_cached_len, suffix_ids_val = pre[0], pre[1], pre[2]
            _ensure_cache_ready(cache_to_use)
        else:
            cache_to_use, actual_cached_len, suffix_ids_val = _prepare_cache_for_system_only(
                req,
                GLOBAL_PROMPT_CACHE,
                CACHED_PREFIX_LEN,
                CACHE_PREFIX_HASH,
                IS_VISION,
                (args.enable_prefix_caching and not args.disable_kv_cache),
                "sync_gen"
            )
        req.__dict__["_prefix_cache_used"] = bool(cache_to_use is GLOBAL_PROMPT_CACHE)
        # Fallback: ensure a bounded KV cache exists to cap memory
        if cache_to_use is None and not IS_VISION and not args.disable_kv_cache:
            suffix_len = _mx_length(suffix_ids_val)
            required = suffix_len + int(args.prefix_cache_headroom)
            max_size, upper_limit = _resolve_cache_size(
                ensure=required,
                cli_cap=args.kv_cache_max_tokens,
            )
            cache_to_use = _allocate_prompt_cache(
                max_size,
                keep=args.kv_cache_keep,
                reason="generation",
                upper_limit=upper_limit,
            )
        
        # Calculate total prompt length for reporting
        full_prompt_len = len(_encode(prompt))
        suffix_len = len(suffix_ids_val) if suffix_ids_val.ndim == 1 else suffix_ids_val.shape[-1]
        
        log.info("🪟 Using cache? %s | full prompt %d tokens | processing %d tokens (cached system: %d)", 
                 cache_to_use is not None, full_prompt_len, suffix_len, actual_cached_len)

        timer = _Timer(suffix_len)
        out, comp_tok, think_tok_count_if_stripped = [], 0, 0
        t0 = time.perf_counter()

        first_iter = True
        for r in lm_stream(
            model=MODEL,
            tokenizer=PROCESSOR,
            prompt=suffix_ids_val,
            max_tokens=req.max_tokens,
            sampler=sampler,
            prompt_cache=cache_to_use
        ):
            if first_iter:
                start_pos = getattr(r, "pos", getattr(r, "position", -1))
                log.debug("🔍 First step model start_pos = %s", start_pos)
                first_iter = False
            if r.token == PROCESSOR.eos_token_id:
                break
            out.append(r.text)
            comp_tok += 1
            # This counts tokens inside <think> tags if they were to be stripped.
            # The actual reasoning_tok for usage depends on whether stripping happens.
            if "<think>" in r.text:
                 think_tok_count_if_stripped += len(PROCESSOR.encode("".join(THINK_RE.findall(r.text))))
        dt = time.perf_counter() - t0

        full = "".join(out)
        # Calculate actual reasoning tokens based on the final full string and stripping choice
        final_reasoning_tok = 0
        if not (req.strip_thinking or args.strip_thinking):
            inner_thoughts = THINK_RE.findall(full)
            final_reasoning_tok = sum(len(PROCESSOR.encode(seg)) for seg in inner_thoughts)
        
        total_input = suffix_len + int(actual_cached_len)
        req.__dict__["_usage"] = _usage_dict(total_input, comp_tok, dt, final_reasoning_tok, int(actual_cached_len))
        prefix_cache_used = bool(req.__dict__.get("_prefix_cache_used")) or (cache_to_use is GLOBAL_PROMPT_CACHE)
        appended_tokens = suffix_len + comp_tok
        if cache_to_use is not None:
            if prefix_cache_used and appended_tokens > 0:
                try:
                    if can_trim_prompt_cache(cache_to_use):
                        trim_prompt_cache(cache_to_use, appended_tokens)
                except Exception as e:
                    log.warning(f"Prefix cache trim failed: {e}")
            if prefix_cache_used:
                req.__dict__["_prefix_cache_used"] = False
            _maybe_expand_cache(cache_to_use, total_input)

        timer.done(comp_tok)

        return full

    def stream_chunks(prompt: str, _imgs, req: ChatReq):  # noqa: C901
        global GLOBAL_PROMPT_CACHE, CACHED_PREFIX_LEN, CACHE_PREFIX_HASH
        rid, created, sent_role = f"chatcmpl-{uuid.uuid4()}", int(time.time()), False
        sampler = _sampler(req)

        pre = req.__dict__.get("_precomputed_cache")
        if pre is not None:
            cache_to_use, actual_cached_len, suffix_ids_val = pre[0], pre[1], pre[2]
            _ensure_cache_ready(cache_to_use)
        else:
            cache_to_use, actual_cached_len, suffix_ids_val = _prepare_cache_for_system_only(
                req,
                GLOBAL_PROMPT_CACHE,
                CACHED_PREFIX_LEN,
                CACHE_PREFIX_HASH,
                IS_VISION,
                (args.enable_prefix_caching and not args.disable_kv_cache),
                "stream_chunks"
            )
        req.__dict__["_prefix_cache_used"] = bool(cache_to_use is GLOBAL_PROMPT_CACHE)
        # Fallback: ensure a bounded KV cache exists to cap memory
        if cache_to_use is None and not IS_VISION and not args.disable_kv_cache:
            suffix_len = _mx_length(suffix_ids_val)
            required = suffix_len + int(args.prefix_cache_headroom)
            max_size, upper_limit = _resolve_cache_size(
                ensure=required,
                cli_cap=args.kv_cache_max_tokens,
            )
            cache_to_use = _allocate_prompt_cache(
                max_size,
                keep=args.kv_cache_keep,
                reason="generation-stream",
                upper_limit=upper_limit,
            )
        
        # Calculate total prompt length for reporting
        full_prompt_len = len(_encode(prompt))
        suffix_len = len(suffix_ids_val) if suffix_ids_val.ndim == 1 else suffix_ids_val.shape[-1]
        
        log.info("🪟 Using cache? %s | full prompt %d tokens | processing %d tokens (cached system: %d) (stream)", 
                 cache_to_use is not None, full_prompt_len, suffix_len, actual_cached_len)

        timer = _Timer(suffix_len)
        # reasoning_tok for streaming is harder to calculate accurately upfront if stripping thoughts.
        # The _ThinkFilter handles stripping, and final usage might not be easily available here.
        # For simplicity, we'll set it to 0 here or acknowledge it's an approximation for streaming.

        strip_it = args.strip_thinking if req.strip_thinking is None else req.strip_thinking
        think = _ThinkFilter(start_in_think=(args.enable_auto_think_detection and AUTO_THINK_DETECTED)) if strip_it else None
        SYNC_EVERY, tok_ctr, out_tok = 16, 0, 0
        def _emit_piece(piece: str, raw_text: str | None = None) -> str | None:
            nonlocal sent_role, out_tok
            if piece == "" and raw_text:
                piece = "\n"
            elif piece == "":
                return None
            delta = {"content": piece}
            if not sent_role:
                delta["role"] = "assistant"
                sent_role = True
            out_tok += 1
            _trace_append(req, out_piece=piece)
            return _sse_chunk(rid, created, delta)

        first_iter = True
        for r in lm_stream(
            model=MODEL,
            tokenizer=PROCESSOR,
            prompt=suffix_ids_val,
            max_tokens=req.max_tokens,
            sampler=sampler,
            prompt_cache=cache_to_use
        ):
            if first_iter:
                start_pos = getattr(r, "pos", getattr(r, "position", -1))
                log.debug("🔍 First step model start_pos = %s (stream)", start_pos)
                first_iter = False
            if r.token == PROCESSOR.eos_token_id:
                break
            piece = r.text
            _trace_append(req, raw_piece=piece)
            if strip_it and think is not None:
                stripped_piece = think.feed(piece)
                if think.saw_close_without_open:
                    _set_auto_think_detected("stream saw </think> without <think>")
                if stripped_piece is None:
                    tok_ctr += 1
                    if tok_ctr % SYNC_EVERY == 0:
                        mx.synchronize()
                    continue
                piece = stripped_piece

            chunk = _emit_piece(piece, r.text)
            if chunk:
                yield chunk
            tok_ctr += 1
            if tok_ctr % SYNC_EVERY == 0:
                mx.synchronize()

        if strip_it and args.enable_auto_think_detection and think is not None:
            fallback = think.flush_fallback(AUTO_THINK_MIN_TOKENS)
            if fallback:
                chunk = _emit_piece(fallback, fallback)
                if chunk:
                    yield chunk

        if cache_to_use is not None:
            prefix_cache_used = bool(req.__dict__.get("_prefix_cache_used")) or (cache_to_use is GLOBAL_PROMPT_CACHE)
            appended_tokens = suffix_len + out_tok
            if prefix_cache_used and appended_tokens > 0:
                try:
                    if can_trim_prompt_cache(cache_to_use):
                        trim_prompt_cache(cache_to_use, appended_tokens)
                except Exception as e:
                    log.warning(f"Prefix cache trim (stream) failed: {e}")
            if prefix_cache_used:
                req.__dict__["_prefix_cache_used"] = False
            _maybe_expand_cache(cache_to_use, suffix_len + int(actual_cached_len))
        timer.done(out_tok)
        final = {
            "id": rid,
            "object": "chat.completion.chunk",
            "created": created,
            "model": MODEL_NAME,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(final)}\n\n"
        yield "data: [DONE]\n\n"


# ───────────────────────── SSE helper ─────────────────────────────

def _sse_chunk(rid: str, created: int, delta: Dict[str, str]) -> str:
    payload = {
        "id": rid,
        "object": "chat.completion.chunk",
        "created": created,
        "model": MODEL_NAME,
        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
    }
    return f"data: {json.dumps(payload)}\n\n"


# ─────────────────────────── FastAPI app ─────────────────────────
app = FastAPI()

# ─────────────────── Conversation KV manager ───────────────────
import time as _time
from collections import OrderedDict


class _ConvRec:
    __slots__ = ("cache", "tokens", "text", "base_text", "boundary_offsets", "message_hashes", "messages", "ts", "snapshots")

    def __init__(self, cache: Any, tokens, text: str = "", base_text: str = ""):
        self.cache = cache
        self.tokens = tokens  # numpy array (uint32) 1-D
        self.text = text      # full prompt string corresponding to tokens
        self.base_text = base_text  # prompt without generation prompt
        self.boundary_offsets: List[int] | None = None  # token offsets after each message
        self.message_hashes: List[str] | None = None    # hash per message
        self.messages: List[Dict[str, str]] | None = None  # flat messages used for this cache
        self.ts = _time.time()
        # snapshots: recent prior states for rollback/prefix match
        # elements: {"tokens": np.ndarray, "text": str, "cache": Any}
        self.snapshots: List[Dict[str, Any]] = []


class ConversationKV:
    def __init__(self, max_convs: int, ttl: int):
        self.max_convs = max_convs
        self.ttl = ttl
        self._map: "OrderedDict[str, _ConvRec]" = OrderedDict()

    def _evict(self):
        # Evict LRU beyond capacity or stale by TTL
        now = _time.time()
        # Drop expired
        keys_to_drop = [k for k, rec in self._map.items() if self.ttl > 0 and (now - rec.ts) > self.ttl]
        for k in keys_to_drop:
            rec = self._map.pop(k, None)
            if rec is not None:
                try:
                    _release_cache_memory(rec.cache)
                except Exception:
                    pass
        # Enforce max size
        while len(self._map) > self.max_convs:
            _, rec = self._map.popitem(last=False)
            try:
                _release_cache_memory(rec.cache)
            except Exception:
                pass

    def _enforce_budget(self, budget_tokens: Optional[int]):
        if budget_tokens is None or budget_tokens <= 0:
            return
        total = 0
        for rec in self._map.values():
            total += _cache_capacity_tokens(rec.cache)
        if total <= budget_tokens:
            return
        while len(self._map) > 1 and total > budget_tokens:
            cid, rec = self._map.popitem(last=False)
            released = _cache_capacity_tokens(rec.cache)
            try:
                _release_cache_memory(rec.cache)
            except Exception:
                pass
            total -= released
            log.info(
                "Evicted conversation KV '%s' to honor global budget (%d/%d tokens).",
                cid,
                max(total, 0),
                budget_tokens,
            )
        if total > budget_tokens:
            log.warning(
                "Global KV budget exceeded: %d tokens used with budget %d (unable to evict further).",
                total,
                budget_tokens,
            )

    def get(self, cid: str) -> Optional[_ConvRec]:
        rec = self._map.get(cid)
        if rec is None:
            return None
        # touch LRU
        rec.ts = _time.time()
        self._map.move_to_end(cid, last=True)
        return rec

    def put(self, cid: str, cache: Any, tokens, text: str = "", base_text: str = ""):
        rec = _ConvRec(cache, tokens, text, base_text)
        self._map[cid] = rec
        self._map.move_to_end(cid, last=True)
        self._evict()
        self._enforce_budget(_global_kv_budget_tokens())

# ─────────────────── Disk persistence for conversation KV (manual) ───────────────────
def _sanitize_id(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", s or "")


def _ensure_disk_dir() -> Path:
    d = Path(args.conversation_disk_dir)
    try:
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o700)
    except Exception:
        pass
    return d


def _conv_disk_paths(conv_id: str) -> Dict[str, Path]:
    base = _sanitize_id(MODEL_NAME) + "__" + _sanitize_id(conv_id)
    d = _ensure_disk_dir()
    return {
        "cache": d / f"{base}.safetensors",
        "meta": d / f"{base}.meta.json",
    }


def _conv_disk_save(conv_id: str, rec: _ConvRec, *, title: Optional[str] = None, override_limit: bool = False) -> Dict[str, Any]:
    import numpy as _np
    info = {"written_bytes": 0, "meta_bytes": 0, "path": "", "error": None}
    paths = _conv_disk_paths(conv_id)
    try:
        d = paths["cache"].parent
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o700)
        tmp_cache = d / (paths["cache"].name + ".tmp")
        tmp_meta = d / (paths["meta"].name + ".tmp")
        # Write cache to tmp
        if tmp_cache.exists():
            tmp_cache.unlink()
        save_prompt_cache(str(tmp_cache), rec.cache)
        size = int(tmp_cache.stat().st_size)
        # Check per-save max size (GiB)
        max_bytes = int(args.conversation_disk_max_gb) * (1024**3)
        if size > max_bytes and not override_limit:
            tmp_cache.unlink(missing_ok=True)
            info["error"] = f"cache size {size} exceeds max {max_bytes}"
            return info
        # Check disk occupancy threshold (90%) before committing
        usage = _shutil.disk_usage(str(d))
        after_used = usage.used + size
        if after_used / usage.total > 0.90:
            tmp_cache.unlink(missing_ok=True)
            info["error"] = "disk occupancy would exceed 90%"
            return info
        # Write meta tmp
        meta = {
            "v": 2,
            "model": MODEL_NAME,
            "conversation_id": conv_id,
            "ts": int(time.time()),
            "title": title or "",
            "tokens": list(map(int, _np.array(rec.tokens, copy=False).astype('uint32').ravel())) if rec.tokens is not None else [],
            "boundary_offsets": list(map(int, rec.boundary_offsets or [])) if getattr(rec, 'boundary_offsets', None) else None,
            "message_hashes": list(rec.message_hashes or []),
            "messages": list(rec.messages or []),
            "prefix": (rec.base_text or rec.text or "")[:500],
            "path": str(paths["cache"]),
        }
        tmp_meta.write_text(json.dumps(meta), encoding="utf-8")
        # Move into place atomically
        if paths["cache"].exists():
            paths["cache"].unlink()
        tmp_cache.rename(paths["cache"])
        if paths["meta"].exists():
            paths["meta"].unlink()
        tmp_meta.rename(paths["meta"])
        # Permissions
        try:
            paths["cache"].chmod(0o600)
            paths["meta"].chmod(0o600)
        except Exception:
            pass
        info["written_bytes"] = size
        info["meta_bytes"] = int(paths["meta"].stat().st_size)
        info["path"] = str(paths["cache"])
        return info
    except Exception as e:
        log.warning(f"Conversation disk save failed for '{conv_id}': {e}")
        try:
            tmp_cache.unlink(missing_ok=True)
            tmp_meta.unlink(missing_ok=True)
        except Exception:
            pass
        info["error"] = str(e)
        return info


def _conv_disk_load(conv_id: str) -> Tuple[Any, Optional[List[int]], Optional[List[int]], Optional[List[str]]]:
    import numpy as _np
    paths = _conv_disk_paths(conv_id)
    if not (paths["cache"].exists() and paths["meta"].exists()):
        return None, None, None, None
    try:
        cache = load_prompt_cache(str(paths["cache"]))
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        toks = meta.get("tokens") or []
        offs = meta.get("boundary_offsets") or None
        hashes = meta.get("message_hashes") or None
        ensure_len = len(toks)
        conv_cap = _positive_or_none(args.conversation_kv_max_tokens)
        if conv_cap is None:
            conv_cap = _positive_or_none(args.kv_cache_max_tokens)
        max_size, upper_limit = _resolve_cache_size(ensure=ensure_len, cli_cap=conv_cap)
        _cache_register(cache, target_tokens=max_size, upper_limit=upper_limit, reason=f"conversation:{conv_id}:disk")
        _hard_reserve_cache(cache)
        return cache, toks, offs, hashes
    except Exception as e:
        log.warning(f"Conversation disk load failed for '{conv_id}': {e}")
        return None, None, None, None


def _conv_disk_enforce_budget() -> None:
    budget = int(args.conversation_disk_budget_mb) * 1024 * 1024
    d = _ensure_disk_dir()
    try:
        entries = []
        total = 0
        prefix = _sanitize_id(MODEL_NAME) + "__"
        for meta_p in d.glob(f"{prefix}*.meta.json"):
            try:
                cache_p = Path(str(meta_p).replace('.meta.json', '.safetensors'))
                size = (meta_p.stat().st_size if meta_p.exists() else 0) + (cache_p.stat().st_size if cache_p.exists() else 0)
                ts = 0
                try:
                    m = json.loads(meta_p.read_text(encoding='utf-8'))
                    ts = int(m.get('ts') or 0)
                except Exception:
                    pass
                entries.append((ts, size, meta_p, cache_p))
                total += size
            except Exception:
                continue
        if total <= budget:
            return
        entries.sort(key=lambda x: x[0])
        for ts, size, meta_p, cache_p in entries:
            try:
                if cache_p.exists():
                    cache_p.unlink()
                if meta_p.exists():
                    meta_p.unlink()
            except Exception:
                pass
            total -= size
            if total <= budget:
                break
    except Exception as e:
        log.warning(f"Disk budget enforcement failed: {e}")


# ──────────────────────────── Save/Load Endpoints ───────────────────────────

class _ConvIOReq(BaseModel):
    conversation: Optional[str] = None
    conversation_id: Optional[str] = None
    budget_mb: Optional[int] = None
    title: Optional[str] = None
    override_limit: Optional[bool] = None


@app.post("/v1/conv_kv/save")
async def save_conversation(body: _ConvIOReq):
    cid = (body.conversation or body.conversation_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="conversation or conversation_id required")
    rec = CONV_KV.get(cid)
    if rec is None or rec.cache is None:
        raise HTTPException(status_code=404, detail="conversation not found or no cache in memory")
    # Ensure boundary metadata is present
    if rec.boundary_offsets is None and not IS_VISION:
        try:
            # We cannot reconstruct message list here; leave None if unknown
            pass
        except Exception:
            pass
    info = _conv_disk_save(cid, rec, title=body.title, override_limit=bool(body.override_limit))
    if info.get("error"):
        raise HTTPException(status_code=413, detail=info["error"])  # 413 Payload Too Large / over limit
    if body.budget_mb is not None:
        try:
            old = args.conversation_disk_budget_mb
            args.conversation_disk_budget_mb = int(body.budget_mb)
            _conv_disk_enforce_budget()
            args.conversation_disk_budget_mb = old
        except Exception:
            _conv_disk_enforce_budget()
    else:
        _conv_disk_enforce_budget()
    return {
        "status": "saved",
        "id": cid,
        "path": info.get("path"),
        "bytes": info.get("written_bytes", 0),
        "meta_bytes": info.get("meta_bytes", 0),
        "tokens": int(len(rec.tokens) if rec.tokens is not None else 0),
    }


@app.post("/v1/conv_kv/load")
async def load_conversation(body: _ConvIOReq):
    import numpy as _np
    cid = (body.conversation or body.conversation_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="conversation or conversation_id required")
    cache, toks, offs, hashes = _conv_disk_load(cid)
    if cache is None:
        raise HTTPException(status_code=404, detail="conversation cache not found on disk")
    # Install or update record
    toks_np = _np.array(toks or [], dtype='uint32')
    rec = CONV_KV.get(cid)
    if rec is not None:
        rec.cache = cache
        rec.tokens = toks_np
        rec.boundary_offsets = list(map(int, offs or [])) if offs else None
        rec.message_hashes = list(hashes or []) if hashes else None
    else:
        CONV_KV.put(cid, cache, toks_np, text="", base_text="")
        rec2 = CONV_KV.get(cid)
        if rec2 is not None:
            rec2.boundary_offsets = list(map(int, offs or [])) if offs else None
            rec2.message_hashes = list(hashes or []) if hashes else None
    return {
        "status": "loaded",
        "id": cid,
        "tokens": int(len(toks or [])),
        "has_boundary": bool(offs),
        "has_hashes": bool(hashes),
    }


@app.get("/v1/conv_kv/stats")
async def list_conversation_stats():
    d = _ensure_disk_dir()
    prefix = _sanitize_id(MODEL_NAME) + "__"
    items = []
    try:
        for meta_p in d.glob(f"{prefix}*.meta.json"):
            try:
                cache_p = Path(str(meta_p).replace('.meta.json', '.safetensors'))
                meta = json.loads(meta_p.read_text(encoding='utf-8'))
                size = (meta_p.stat().st_size if meta_p.exists() else 0) + (cache_p.stat().st_size if cache_p.exists() else 0)
                items.append({
                    "id": meta.get("conversation_id") or meta_p.stem.split("__",1)[-1].replace('.meta',''),
                    "title": meta.get("title") or "",
                    "tokens": len(meta.get("tokens") or []),
                    "ts": meta.get("ts") or 0,
                    "size_bytes": int(size),
                    "path": str(cache_p),
                    "prefix": meta.get("prefix") or "",
                })
            except Exception:
                continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"items": items}


@app.delete("/v1/conv_kv/{cid}")
async def delete_conversation(cid: str):
    paths = _conv_disk_paths(cid)
    deleted = False
    try:
        if paths["cache"].exists():
            paths["cache"].unlink()
            deleted = True
        if paths["meta"].exists():
            paths["meta"].unlink()
            deleted = True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "deleted" if deleted else "not_found", "id": cid}


CONV_KV = ConversationKV(max_convs=int(args.conversation_max_convs), ttl=int(args.conversation_ttl_seconds))

@app.get("/v1/models")
async def list_models() -> dict:
    """Return the single loaded model in OpenAI's `/v1/models` schema."""

    model_info = {
        "id": MODEL_NAME,
        "object": "model",
        "created": MODEL_CREATED,
        "owned_by": "kamiwaza",
    }
    return {"object": "list", "data": [model_info]}


@app.get("/v1/allocator/stats")
async def allocator_stats() -> Dict[str, Any]:
    """Return lightweight allocator telemetry for debugging."""
    try:
        active = getattr(mx, "get_active_memory", lambda: 0)()
        cached = getattr(mx, "get_cache_memory", lambda: 0)()
        info = getattr(mx.metal, "device_info", lambda: {})
        return {
            "active_bytes": int(active),
            "cache_bytes": int(cached),
            "device_info": info() if callable(info) else info,
        }
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/v1/kv_cache/stats")
async def kv_cache_stats(verbose: bool = False) -> Dict[str, Any]:
    convs = []
    total_bytes = 0
    for cid, rec in list(CONV_KV._map.items()):  # noqa: SLF001
        summary = _cache_summary(rec.cache, verbose=verbose)
        if summary:
            total_bytes += int(summary.get("total_bytes") or 0)
        convs.append(
            {
                "id": cid,
                "tokens": int(len(rec.tokens) if rec.tokens is not None else 0),
                "ts": float(rec.ts),
                "cache": summary,
            }
        )
    warm = _cache_summary(GLOBAL_WARMUP_CACHE, verbose=verbose)
    prompt = _cache_summary(GLOBAL_PROMPT_CACHE, verbose=verbose)
    for item in (warm, prompt):
        if item:
            total_bytes += int(item.get("total_bytes") or 0)
    return {
        "config": {
            "kv_cache_sizing": args.kv_cache_sizing,
            "kv_cache_max_tokens": int(args.kv_cache_max_tokens),
            "kv_cache_global_max_tokens": int(args.kv_cache_global_max_tokens),
            "conversation_kv_max_tokens": int(args.conversation_kv_max_tokens),
            "conversation_max_convs": int(args.conversation_max_convs),
            "kv_cache_hard_reserve": bool(args.kv_cache_hard_reserve),
            "retain_mx_cache": bool(args.retain_mx_cache),
        },
        "totals": {"kv_bytes": int(total_bytes)},
        "warmup": warm,
        "prompt": prompt,
        "conversations": convs,
    }


@app.post("/v1/chat/completions")
async def completions(req: ChatReq, request: Request):  # noqa: C901 – same as original
    from fastapi import Request as _Request  # local import to avoid circulars
    # access headers by creating a dummy Request param via dependency not available here; instead FastAPI can inject if we include param
    if req.model != MODEL_NAME:
        log.warning("Requested model '%s' ≠ loaded '%s'", req.model, MODEL_NAME)
    _cache_idle_release()
    globals()["KV_CACHE_LAST_ACTIVITY"] = time.time()

    # Prepare canonical vs prompt views of the conversation
    base_flat = [dict(m) for m in req.flat]
    tools_payload = _normalize_tools(req.tools or [])
    tool_parser = _resolve_tool_parser() if tools_payload else None
    tools_enabled = bool(tool_parser and tools_payload)
    forced_name = _get_forced_tool_name(getattr(req, "tool_choice", None)) if tools_enabled else None
    if tools_payload:
        parser_name = tool_parser.name if tool_parser else "none"
        log.info(
            "Tool request: %d tools (parser=%s, template_tools=%s)",
            len(tools_payload),
            parser_name,
            bool(tool_parser and tool_parser.uses_chat_template_tools),
        )

    flat_prompt = base_flat
    tools_template: Optional[List[Dict[str, Any]]] = None
    tool_prompt_inserted = False
    use_template_tools = False
    if tools_enabled:
        use_template_tools = bool(tool_parser.uses_chat_template_tools and CHAT_TEMPLATE_SUPPORTS_TOOLS)
        if use_template_tools:
            tools_template = tool_parser.format_tools_for_template(tools_payload)
            req.__dict__["_tool_template_tools"] = tools_template
        else:
            tool_prompt = None
            try:
                if forced_name:
                    tool_prompt = tool_parser.build_forced_prompt(tools_payload, forced_name)
                else:
                    tool_prompt = tool_parser.build_tool_prompt(
                        tools_payload,
                        req.tool_choice,
                        req.parallel_tool_calls,
                    )
            except Exception as e:
                log.warning("Failed to prepare tool instructions: %s", e)
            if tool_prompt:
                tool_prompt = dict(tool_prompt)
                tool_prompt.setdefault("_ephemeral", True)
                tool_prompt["_tool_prompt"] = True
                if base_flat and base_flat[0].get("role") == "system":
                    merged = dict(base_flat[0])
                    merged_content = str(merged.get("content") or "")
                    merged["content"] = (merged_content + "\n\n" + tool_prompt["content"]).strip()
                    flat_prompt = [merged] + base_flat[1:]
                else:
                    flat_prompt = [tool_prompt] + base_flat
                tool_prompt_inserted = True

    if tools_payload:
        log.info(
            "Tool template decision: enabled=%s use_template_tools=%s template_len=%d supports_tools=%s",
            tools_enabled,
            use_template_tools,
            len(tools_template or []),
            CHAT_TEMPLATE_SUPPORTS_TOOLS,
        )
    req.__dict__["flat"] = flat_prompt
    req.__dict__["_flat_conv"] = flat_prompt

    imgs = [load_image(u) for u in req.all_images] if IS_VISION else []
    prompt_str = build_prompt(req, len(imgs))
    if tools_enabled and tool_parser and tool_parser.uses_chat_template_tools and tools_template:
        if tool_parser.name == "minimax-m2":
            expected_tools = len(tools_payload)
            tool_tag_count = prompt_str.count("<tool>")
            if tool_tag_count < expected_tools:
                if tool_prompt_inserted:
                    log.warning(
                        "Tool prompt inserted but tool tags still missing (%d/%d) from rendered prompt (parser=%s).",
                        tool_tag_count,
                        expected_tools,
                        tool_parser.name,
                    )
                else:
                    tool_prompt = None
                    try:
                        if forced_name:
                            tool_prompt = tool_parser.build_forced_prompt(tools_payload, forced_name)
                        else:
                            tool_prompt = tool_parser.build_tool_prompt(
                                tools_payload,
                                req.tool_choice,
                                req.parallel_tool_calls,
                            )
                    except Exception as e:
                        log.warning("Failed to prepare tool instructions: %s", e)
                    if tool_prompt:
                        log.warning(
                            "Chat template tools missing (<tool> tags %d/%d); falling back to explicit tool prompt (parser=%s).",
                            tool_tag_count,
                            expected_tools,
                            tool_parser.name,
                        )
                        req.__dict__.pop("_tool_template_tools", None)
                        tools_template = None
                        tool_prompt = dict(tool_prompt)
                        tool_prompt.setdefault("_ephemeral", True)
                        tool_prompt["_tool_prompt"] = True
                        if base_flat and base_flat[0].get("role") == "system":
                            merged = dict(base_flat[0])
                            merged_content = str(merged.get("content") or "")
                            merged["content"] = (merged_content + "\n\n" + tool_prompt["content"]).strip()
                            flat_prompt = [merged] + base_flat[1:]
                        else:
                            flat_prompt = [tool_prompt] + base_flat
                        req.__dict__["flat"] = flat_prompt
                        req.__dict__["_flat_conv"] = flat_prompt
                        prompt_str = build_prompt(req, len(imgs))
    if tools_enabled and tool_parser and tool_parser.name == "minimax-m2":
        tool_tag_count = prompt_str.count("<tool>")
        log.info(
            "Tool prompt tags: %d/%d",
            tool_tag_count,
            len(tools_payload),
        )
    flat_conv = req.__dict__.get("_flat_conv", base_flat)
    try:
        act_mem = getattr(mx, "get_active_memory", lambda: 0)()
        cache_mem = getattr(mx, "get_cache_memory", lambda: 0)()
        log.info(
            "MX memory → active=%.2f GiB cache=%.2f GiB",
            act_mem / (1 << 30),
            cache_mem / (1 << 30),
        )
    except Exception:
        pass

    # ───────── Conversation KV preparation ─────────
    conv_id = None
    if not args.disable_kv_cache and args.enable_conversation_cache:
        # precedence: body.conversation -> body.conversation_id -> header X-Conversation-Id
        conv_id = (req.conversation or req.conversation_id or request.headers.get("X-Conversation-Id"))
        if conv_id is not None:
            conv_id = conv_id.strip() or None
        # Auto-bind to a per-client conversation if enabled and none provided
        if conv_id is None and args.conversation_auto_id:
            client_id = None
            try:
                if request.client and request.client.host:
                    client_id = f"client:{request.client.host}"
            except Exception:
                client_id = None
            conv_id = client_id or str(args.conversation_auto_fixed)

    trace_entry = _trace_begin(req, request, prompt_str)
    if trace_entry is not None:
        trace_entry["conversation_id"] = conv_id or ""

    full_ids_for_conv = None
    conv_diag = {"id": conv_id or "", "mode": "disabled" if (args.disable_kv_cache or not args.enable_conversation_cache) else ("none" if not conv_id else "unknown"), "cached": 0, "processing": 0}
    if conv_id and not req.reset_conversation:
        try:
            full_ids_for_conv = _encode(prompt_str)
            # flatten to 1-D if needed
            if getattr(full_ids_for_conv, 'ndim', 1) != 1:
                full_ids_for_conv = full_ids_for_conv.ravel()
        except Exception as e:
            log.warning(f"Conversation encode failed: {e}")
            full_ids_for_conv = None

    precomp_cache = None
    if conv_id and not req.reset_conversation:
        import numpy as _np
        # Try incremental tokenization: if new prompt_str starts with stored text,
        # only encode the tail and concatenate tokens.
        cand = None
        CONV_KV.max_convs = int(args.conversation_max_convs)
        CONV_KV.ttl = int(args.conversation_ttl_seconds)
        rec = CONV_KV.get(conv_id)
        if rec is not None:
            _ensure_cache_ready(rec.cache)
            try:
                prev = _np.array(rec.tokens, copy=False).astype('uint32').ravel()

                # Prefer boundary-aware matching by message hashes and token offsets
                text = prompt_str
                prev = _np.array(rec.tokens, copy=False).astype('uint32').ravel()
                prev_hashes = list(rec.message_hashes or [])
                new_hashes = [_msg_hash(m.get('role',''), m.get('content','') or '') for m in flat_conv]
                base_prev = rec.base_text or ""
                k = 0
                max_k = min(len(prev_hashes), len(new_hashes))
                while k < max_k and prev_hashes[k] == new_hashes[k]:
                    k += 1
                if rec.boundary_offsets and k > 0:
                    off = list(rec.boundary_offsets or [])
                    k = min(k, len(off))
                    base_prev_tok = int(off[k-1]) if k > 0 else 0
                    base_str_k = build_base_prompt_for_flat(flat_conv[:k], len(imgs), tools=tools_template)
                    if not text.startswith(base_str_k):
                        log.warning("Conversation KV boundary prefix mismatch; falling back to full prompt.")
                    else:
                        # Build incremental tails per added message
                        tail_arrays = []
                        boundary_offsets_new = off[:k]
                        cur_tok = base_prev_tok
                        prev_base = base_str_k
                        boundary_ok = True
                        for i in range(k, len(flat_conv)):
                            base_i = build_base_prompt_for_flat(flat_conv[: i + 1], len(imgs), tools=tools_template)
                            if not base_i.startswith(prev_base):
                                log.warning("Conversation KV boundary delta mismatch; falling back to full prompt.")
                                boundary_ok = False
                                break
                            delta = base_i[len(prev_base):]
                            delta_ids = _encode(delta)
                            delta_ids = delta_ids if getattr(delta_ids, 'ndim', 1) == 1 else delta_ids.ravel()
                            dn = _np.array(delta_ids, copy=False).astype('uint32').ravel()
                            if len(dn) > 0:
                                tail_arrays.append(dn)
                            cur_tok += int(len(dn))
                            boundary_offsets_new.append(cur_tok)
                            prev_base = base_i
                        if boundary_ok:
                            # Append generation prompt for new full prompt
                            gen_str = text[len(prev_base):]
                            gen_ids = _encode(gen_str)
                            gen_ids = gen_ids if getattr(gen_ids, 'ndim', 1) == 1 else gen_ids.ravel()
                            gen_np = _np.array(gen_ids, copy=False).astype('uint32').ravel()
                            suffix_cat = gen_np if len(tail_arrays) == 0 else _np.concatenate(tail_arrays + [gen_np])
                            suffix_ids = mx.array(suffix_cat)
                            # Trim cache back to boundary once we know we can reuse it safely
                            if base_prev_tok >= 0:
                                try:
                                    _trim_cache_to(rec.cache, base_prev_tok)
                                except Exception as e:
                                    log.warning(f"KV trim failed (boundary LCP): {e}")
                            prev_trimmed = prev[:base_prev_tok] if base_prev_tok > 0 else prev[:0]
                            precomp_cache = (rec.cache, base_prev_tok, suffix_ids)
                            cand = prev_trimmed if len(suffix_cat) == 0 else _np.concatenate([prev_trimmed, suffix_cat])
                            conv_diag.update({"mode": "hit", "cached": base_prev_tok, "processing": int(len(suffix_cat))})
                            # Stash for commit
                            req.__dict__["_boundary_offsets_new"] = boundary_offsets_new
                            req.__dict__["_message_hashes_new"] = new_hashes
                if precomp_cache is None:
                    if base_prev and text.startswith(base_prev):
                        base_new = build_base_prompt(req, len(imgs))
                        if not text.startswith(base_new):
                            # rebuild prompt to ensure consistency
                            base_new = build_base_prompt(req, len(imgs))
                        # Compute trailer tokens to trim existing cache back to base_prev
                        trailer_prev_str = (rec.text or "")[len(base_prev):]
                        trailer_prev_ids = _encode(trailer_prev_str)
                        trailer_prev_tok = int(trailer_prev_ids.shape[-1] if getattr(trailer_prev_ids, 'ndim', 1) != 1 else len(trailer_prev_ids))
                        base_prev_tok = int(len(prev) - trailer_prev_tok)
                        if base_prev_tok >= 0:
                            try:
                                _trim_cache_to(rec.cache, base_prev_tok)
                            except Exception as e:
                                log.warning(f"KV trim failed: {e}")
                        # Tail between base_prev and base_new
                        tail = base_new[len(base_prev):]
                        tail_ids = _encode(tail)
                        tail_ids = tail_ids if getattr(tail_ids, 'ndim', 1) == 1 else tail_ids.ravel()
                        # Append generation prompt for new full prompt
                        gen_str = text[len(base_new):]
                        gen_ids = _encode(gen_str)
                        gen_ids = gen_ids if getattr(gen_ids, 'ndim', 1) == 1 else gen_ids.ravel()
                        suffix_ids = mx.array(_np.concatenate([
                            _np.array(tail_ids, copy=False).astype('uint32').ravel(),
                            _np.array(gen_ids, copy=False).astype('uint32').ravel(),
                        ]))
                        precomp_cache = (rec.cache, base_prev_tok, suffix_ids)
                        # Build candidate tokens for commit without full re-encode
                        tail_np = _np.array(tail_ids, copy=False).astype('uint32').ravel()
                        gen_np = _np.array(gen_ids, copy=False).astype('uint32').ravel()
                        cand = _np.concatenate([prev[:base_prev_tok], tail_np, gen_np])
                        conv_diag.update({"mode": "hit", "cached": base_prev_tok, "processing": int(len(tail_np) + len(gen_np))})
                        log.info(f"🧵 Conversation KV hit (base/string) for '{conv_id}' (cached_prefix={base_prev_tok} tokens, processing={len(tail_np)+len(gen_np)})")
                    else:
                        # Try snapshots by string
                        hit = False
                        for snap in reversed(rec.snapshots):
                            if "cache" not in snap:
                                continue
                            sbase = snap.get("base_text") or ""
                            stxt = snap.get("text") or ""
                            if sbase and text.startswith(sbase):
                                stoks = _np.array(snap["tokens"], copy=False).astype('uint32').ravel()
                                # Trim snapshot cache back to its base
                                trailer_snap_str = stxt[len(sbase):]
                                trailer_snap_ids = _encode(trailer_snap_str)
                                trailer_snap_tok = int(trailer_snap_ids.shape[-1] if getattr(trailer_snap_ids, 'ndim', 1) != 1 else len(trailer_snap_ids))
                                scache = snap["cache"]
                                base_snap_tok = int(len(stoks) - trailer_snap_tok)
                                if base_snap_tok >= 0:
                                    try:
                                        _trim_cache_to(scache, base_snap_tok)
                                    except Exception as e:
                                        log.warning(f"KV trim failed (snapshot): {e}")
                                base_new = build_base_prompt(req, len(imgs))
                                tail = base_new[len(sbase):]
                                tail_ids = _encode(tail)
                                tail_ids = tail_ids if getattr(tail_ids, 'ndim', 1) == 1 else tail_ids.ravel()
                                gen_str = text[len(base_new):]
                                gen_ids = _encode(gen_str)
                                gen_ids = gen_ids if getattr(gen_ids, 'ndim', 1) == 1 else gen_ids.ravel()
                                suffix_ids = mx.array(_np.concatenate([
                                    _np.array(tail_ids, copy=False).astype('uint32').ravel(),
                                    _np.array(gen_ids, copy=False).astype('uint32').ravel(),
                                ]))
                                precomp_cache = (scache, base_snap_tok, suffix_ids)
                                tail_np = _np.array(tail_ids, copy=False).astype('uint32').ravel()
                                gen_np = _np.array(gen_ids, copy=False).astype('uint32').ravel()
                                cand = _np.concatenate([stoks[:base_snap_tok], tail_np, gen_np])
                                conv_diag.update({"mode": "snapshot", "cached": base_snap_tok, "processing": int(len(tail_np)+len(gen_np))})
                                log.info(f"🧵 Conversation snapshot hit (base/string) for '{conv_id}' (cached_prefix={base_snap_tok} tokens, processing={len(tail_np)+len(gen_np)})")
                                hit = True
                                break
                        if not hit:
                            # Fallback to token-based comparison if we already encoded full prompt
                            if full_ids_for_conv is None:
                                full_ids_for_conv = _encode(prompt_str)
                                if getattr(full_ids_for_conv, 'ndim', 1) != 1:
                                    full_ids_for_conv = full_ids_for_conv.ravel()
                            cand = _np.array(full_ids_for_conv, copy=False).astype('uint32').ravel()
                            if len(prev) <= len(cand) and _np.array_equal(prev, cand[: len(prev)]):
                                match_len = int(len(prev))
                                try:
                                    _trim_cache_to(rec.cache, match_len)
                                except Exception as e:
                                    log.warning(f"KV trim failed (token prefix): {e}")
                                suffix_ids = mx.array(cand[match_len:])
                                precomp_cache = (rec.cache, match_len, suffix_ids)
                                conv_diag.update({"mode": "hit", "cached": match_len, "processing": int(len(cand) - match_len)})
                                log.info(f"🧵 Conversation KV hit for '{conv_id}' (cached_prefix={match_len} tokens, processing={len(cand)-match_len})")
                            else:
                                # Token-based snapshots
                                token_hit = False
                                for snap in reversed(rec.snapshots):
                                    if "cache" not in snap:
                                        continue
                                    stoks = _np.array(snap["tokens"], copy=False).astype('uint32').ravel()
                                    if len(stoks) <= len(cand) and _np.array_equal(stoks, cand[: len(stoks)]):
                                        match_len = int(len(stoks))
                                        try:
                                            _trim_cache_to(snap["cache"], match_len)
                                        except Exception as e:
                                            log.warning(f"KV trim failed (token snapshot): {e}")
                                        suffix_ids = mx.array(cand[match_len:])
                                        precomp_cache = (snap["cache"], match_len, suffix_ids)
                                        conv_diag.update({"mode": "snapshot", "cached": match_len, "processing": int(len(cand) - match_len)})
                                        log.info(f"🧵 Conversation snapshot hit for '{conv_id}' (cached_prefix={match_len} tokens, processing={len(cand)-match_len})")
                                        token_hit = True
                                        break
                                if not token_hit:
                                    log.info(f"🧵 Conversation KV miss for '{conv_id}' (prefix mismatch)")
            except Exception as e:
                log.warning(f"Conversation KV compare failed: {e}")
        if precomp_cache is not None:
            _ensure_cache_ready(precomp_cache[0])
        if precomp_cache is None:
            # no existing record or mismatch → allocate fresh cache for this conversation
            ensure_len = 0
            if full_ids_for_conv is not None:
                ensure_len = _mx_length(full_ids_for_conv)
            conv_cap = _positive_or_none(args.conversation_kv_max_tokens)
            if conv_cap is None:
                conv_cap = _positive_or_none(args.kv_cache_max_tokens)
            max_size, upper_limit = _resolve_cache_size(ensure=ensure_len, cli_cap=conv_cap)
            conv_cache = None
            reused = False
            if rec is not None and rec.cache is not None:
                conv_cache = rec.cache
                reused = True
                _reset_cache_offsets(conv_cache)
                _ensure_cache_ready(conv_cache)
            if conv_cache is None:
                conv_cache = _claim_warmup_cache_for_conversation(
                    max_tokens=max_size,
                    upper_limit=upper_limit,
                    reason=f"conversation:{conv_id}",
                )
            if conv_cache is None:
                conv_cache = _allocate_prompt_cache(
                    max_size,
                    keep=args.kv_cache_keep,
                    reason=f"conversation:{conv_id}",
                    upper_limit=upper_limit,
                )
            # If we already computed cand (full or partial), use it; else encode now
            if cand is None:
                if full_ids_for_conv is None:
                    full_ids_for_conv = _encode(prompt_str)
                if getattr(full_ids_for_conv, 'ndim', 1) != 1:
                    full_ids_for_conv = full_ids_for_conv.ravel()
                cand = _np.array(full_ids_for_conv, copy=False).astype('uint32').ravel()
            precomp_cache = (conv_cache, 0, mx.array(cand))
            conv_diag.update({"mode": "reset" if reused else "fresh", "cached": 0, "processing": int(len(cand))})
            if reused:
                log.info(f"🧵 Conversation KV reset for '{conv_id}' (reused cache)")
            else:
                desc = "unbounded" if max_size is None else str(int(max_size))
                log.info(f"🧵 Conversation KV allocate for '{conv_id}' (max_size={desc})")
        # pass precomputed cache + suffix to generators via req
        req.__dict__["_precomputed_cache"] = precomp_cache
        # stash conv commit info for after generation
        req.__dict__["_conv_commit"] = {"id": conv_id, "tokens": cand}
    req.__dict__["_conv_diag"] = conv_diag
    
    # Extract system prompt for caching
    system_prompt_str = build_system_prompt(req) if not IS_VISION else ""

    global GLOBAL_PROMPT_CACHE, GLOBAL_WARMUP_CACHE, CACHE_PRIMED_THIS_SESSION, CACHED_PREFIX_LEN, CACHE_PREFIX_HASH  # Ensure globals are modifiable
    global SYSTEM_PROMPT_CACHE_FAILS, SYSTEM_PROMPT_CACHE_SUCCESSES, SYSTEM_PROMPT_CACHE_DISABLED

    # ----- determine if existing cache should be discarded -----
    should_discard_cache = False
    if args.enable_prefix_caching and not IS_VISION and GLOBAL_PROMPT_CACHE is not None and system_prompt_str:
        # A cache exists and we have a system prompt. Check if the system prompt has changed.
        current_system_ids = _encode(system_prompt_str)
        current_system_hash = _hash_tokens(current_system_ids)
        
        if current_system_hash != CACHE_PREFIX_HASH:
            # System prompt has changed. Cache is not usable and should be replaced.
            log.info(
                "🔄 System prompt has changed. Discarding old cache."
            )
            should_discard_cache = True
        # else: system prompt matches -> keep cache

    if should_discard_cache:
        log.info("Executing cache discard operation.")
        GLOBAL_PROMPT_CACHE = None
        CACHED_PREFIX_LEN = 0
        CACHE_PREFIX_HASH = ""
        CACHE_PRIMED_THIS_SESSION = False
        try:
            if GLOBAL_CACHE_FILE_PATH:
                len_path = GLOBAL_CACHE_FILE_PATH + ".len"
                hash_path = GLOBAL_CACHE_FILE_PATH + ".hash"
                if os.path.exists(GLOBAL_CACHE_FILE_PATH):
                    os.remove(GLOBAL_CACHE_FILE_PATH)
                    log.info(f"Deleted cache file: {GLOBAL_CACHE_FILE_PATH}")
                if os.path.exists(len_path):
                    os.remove(len_path)
                    log.info(f"Deleted cache length file: {len_path}")
                if os.path.exists(hash_path):
                    os.remove(hash_path)
                    log.info(f"Deleted cache hash file: {hash_path}")
        except Exception as e:
            log.warning(f"Could not delete old cache files: {e}")
    # -----------------------------------------------------------------------

    # Create cache if needed and we have a system prompt (with bounded size)
    if (
        args.enable_prefix_caching
        and not args.disable_kv_cache
        and not IS_VISION
        and GLOBAL_PROMPT_CACHE is None
        and not CACHE_PRIMED_THIS_SESSION
        and not SYSTEM_PROMPT_CACHE_DISABLED
        and GLOBAL_CACHE_FILE_PATH is not None
        and system_prompt_str
    ):
        log.info(f"Creating system message cache from current request, saving to {GLOBAL_CACHE_FILE_PATH}...")
        cache_creation_start_time = time.perf_counter()
        try:
            system_ids = _encode(system_prompt_str)
            if system_ids.ndim == 1:
                system_ids = system_ids[None, :]
            
            # Build a bounded KV cache to cap memory (prefix length + headroom, within [min,max])
            sys_len = int(system_ids.shape[-1])
            ensure_len = sys_len + int(args.prefix_cache_headroom)
            max_size, upper_limit = _resolve_cache_size(
                ensure=ensure_len,
                cli_cap=args.kv_cache_max_tokens,
                prefer_ensure=True,
            )
            temp_cache = _allocate_prompt_cache(
                max_size,
                keep=args.kv_cache_keep,
                reason="prefix",
                upper_limit=upper_limit,
            )
            MODEL(system_ids, cache=temp_cache)  # Prime the cache with system prompt only

            CACHED_PREFIX_LEN = int(system_ids.shape[-1])
            CACHE_PREFIX_HASH = _hash_tokens(system_ids)
            try:
                Path(GLOBAL_CACHE_FILE_PATH + ".len").write_text(str(CACHED_PREFIX_LEN))
                Path(GLOBAL_CACHE_FILE_PATH + ".hash").write_text(CACHE_PREFIX_HASH)
            except Exception:
                pass

            GLOBAL_PROMPT_CACHE = temp_cache
            if GLOBAL_WARMUP_CACHE is not None and GLOBAL_WARMUP_CACHE is not GLOBAL_PROMPT_CACHE:
                if args.disable_kv_cache or not args.enable_conversation_cache:
                    _release_cache_memory(GLOBAL_WARMUP_CACHE)
                    GLOBAL_WARMUP_CACHE = GLOBAL_PROMPT_CACHE
                else:
                    log.info("Retaining warmup cache for conversation reuse.")
            try:
                save_prompt_cache(GLOBAL_CACHE_FILE_PATH, GLOBAL_PROMPT_CACHE)
            except Exception as e:
                log.warning(f"Could not save prompt cache: {e}")
            CACHE_PRIMED_THIS_SESSION = True
            SYSTEM_PROMPT_CACHE_SUCCESSES += 1
            cache_creation_duration = time.perf_counter() - cache_creation_start_time
            desc = "unbounded" if max_size is None else str(int(max_size))
            log.info(
                "System message cache created and saved (%d tokens, max_size=%s) in %.2f seconds.",
                CACHED_PREFIX_LEN,
                desc,
                cache_creation_duration,
            )
        except Exception:
            SYSTEM_PROMPT_CACHE_FAILS += 1
            log.exception("Error creating/priming system message cache")
            if SYSTEM_PROMPT_CACHE_SUCCESSES == 0 and SYSTEM_PROMPT_CACHE_FAILS >= SYSTEM_PROMPT_CACHE_FAIL_LIMIT:
                SYSTEM_PROMPT_CACHE_DISABLED = True
                log.warning(
                    "Disabling system prompt caching after %d failures with no successes.",
                    SYSTEM_PROMPT_CACHE_FAILS,
                )

    # The generation functions (sync_gen, stream_chunks) will use GLOBAL_PROMPT_CACHE if set

    # Prepare diagnostic headers
    diag = req.__dict__.get("_conv_diag", {}) or {}
    headers = {
        "X-Conv-Id": str(diag.get("id", "")),
        "X-Conv-KV": str(diag.get("mode", "none")),
        "X-Conv-Cached-Tokens": str(diag.get("cached", 0)),
        "X-Conv-Processing-Tokens": str(diag.get("processing", 0)),
    }

    if not req.stream:
        txt_raw = sync_gen(prompt_str, imgs, req)
        txt, reasoning_content = _postprocess_thinking(txt_raw, req.strip_thinking or args.strip_thinking)
        if reasoning_content:
            req.__dict__["_reasoning_content"] = reasoning_content

        tool_calls = None
        if tools_enabled and tool_parser:
            if forced_name and tool_parser.name == "openai-json":
                args_obj = _maybe_parse_arguments_json(txt)
                if isinstance(args_obj, dict):
                    try:
                        arg_str = json.dumps(args_obj, ensure_ascii=False)
                    except Exception:
                        arg_str = str(args_obj)
                    tool_calls = [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": forced_name, "arguments": arg_str},
                    }]
            if tool_calls is None:
                tool_calls = tool_parser.parse_tool_calls(txt, tools_payload)

        if IS_VISION:
            usage = _usage_dict(len(prompt_str), _tok_len(txt), 0.0, 0, 0)
        else:
            usage = req.__dict__.get("_usage")
            if not isinstance(usage, dict):
                p_tok, c_tok, dur = (len(prompt_str), len(txt), 0.0)
                usage = _usage_dict(p_tok, c_tok, dur, 0, 0)

        message: Dict[str, Any] = {"role": "assistant"}
        finish_reason = "stop"
        if tool_calls:
            message["content"] = None
            message["tool_calls"] = tool_calls
            finish_reason = "tool_calls"
        else:
            message["content"] = txt
        reasoning_content = req.__dict__.get("_reasoning_content")
        if reasoning_content:
            message["reasoning_content"] = reasoning_content

        # Commit conversation KV (if any)
        conv_meta = req.__dict__.get("_conv_commit")
        if conv_meta and not req.reset_conversation and not args.disable_kv_cache and args.enable_conversation_cache:
            try:
                cid = conv_meta.get("id")
                tokens = conv_meta.get("tokens")
                # Use the cache object we passed to generator (updated in-place)
                cached = req.__dict__.get("_precomputed_cache")[0]
                # Update existing record if present to retain snapshots
                rec = CONV_KV.get(cid)
                if rec is not None:
                    rec.cache = cached
                    rec.tokens = tokens
                    rec.text = prompt_str
                    if not IS_VISION:
                        try:
                            rec.base_text = build_base_prompt(req, len(imgs))
                        except Exception:
                            pass
                    # Persist boundary metadata and messages snapshot
                    try:
                        offsets_new = req.__dict__.get("_boundary_offsets_new")
                        if offsets_new is None and not IS_VISION:
                            offsets_new = _boundary_offsets_for_flat(flat_conv, len(imgs), tools=tools_template)
                        rec.boundary_offsets = offsets_new
                        rec.message_hashes = [_msg_hash(m.get('role',''), m.get('content','') or '') for m in flat_conv]
                        # messages snapshot
                        rec.messages = [dict(role=m.get('role',''), content=m.get('content','') or '') for m in flat_conv]
                    except Exception as e:
                        log.warning(f"Persist boundary metadata failed: {e}")
                else:
                    base_txt = ""
                    if not IS_VISION:
                        try:
                            base_txt = build_base_prompt(req, len(imgs))
                        except Exception:
                            base_txt = ""
                    CONV_KV.put(cid, cached, tokens, text=prompt_str, base_text=base_txt)
                    # Set metadata on the new record
                    try:
                        rec2 = CONV_KV.get(cid)
                        if rec2 is not None:
                            offsets_new = req.__dict__.get("_boundary_offsets_new")
                            if offsets_new is None and not IS_VISION:
                                offsets_new = _boundary_offsets_for_flat(flat_conv, len(imgs), tools=tools_template)
                            rec2.boundary_offsets = offsets_new
                            rec2.message_hashes = [_msg_hash(m.get('role',''), m.get('content','') or '') for m in flat_conv]
                            rec2.messages = [dict(role=m.get('role',''), content=m.get('content','') or '') for m in flat_conv]
                    except Exception as e:
                        log.warning(f"Persist boundary metadata (new rec) failed: {e}")
                CONV_KV._enforce_budget(_global_kv_budget_tokens())
                log.info(f"🧵 Conversation KV stored for '{cid}' (tokens={len(tokens)})")
            except Exception as e:
                log.warning(f"Conversation KV store failed: {e}")
        payload = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": finish_reason,
                }
            ],
            "usage": usage,
        }
        try:
            payload["metadata"] = {"conversation_id": headers.get("X-Conv-Id", "")}
        except Exception:
            payload["metadata"] = {"conversation_id": ""}
        _trace_finalize(
            req,
            raw_text=txt_raw,
            text=txt,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            usage=usage,
        )
        return JSONResponse(content=payload, headers=headers)

    async def event_stream():
        # If tools are enabled, run a one-shot generation and stream a structured tool_calls delta
        if tools_enabled:
            rid, created = f"chatcmpl-{uuid.uuid4()}", int(time.time())
            txt_raw = sync_gen(prompt_str, imgs, req)
            txt, reasoning_content = _postprocess_thinking(txt_raw, req.strip_thinking or args.strip_thinking)
            if reasoning_content:
                req.__dict__["_reasoning_content"] = reasoning_content
            calls = []
            if tools_enabled and tool_parser:
                if forced_name and tool_parser.name == "openai-json":
                    args_obj = _maybe_parse_arguments_json(txt)
                    if isinstance(args_obj, dict):
                        try:
                            arg_str = json.dumps(args_obj, ensure_ascii=False)
                        except Exception:
                            arg_str = str(args_obj)
                        calls = [{"id": "call_1", "type": "function", "function": {"name": forced_name, "arguments": arg_str}}]
                if not calls:
                    calls = tool_parser.parse_tool_calls(txt, tools_payload) or []
            usage = req.__dict__.get("_usage")
            _trace_finalize(
                req,
                raw_text=txt_raw,
                text=txt,
                finish_reason="tool_calls" if calls else "stop",
                tool_calls=calls if calls else None,
                usage=usage if isinstance(usage, dict) else None,
            )
            # Emit role first
            yield _sse_chunk(rid, created, {"role": "assistant"})
            if reasoning_content:
                yield _sse_chunk(rid, created, {"reasoning_content": reasoning_content})
            if calls:
                # Emit each call in two chunks: name, then arguments
                for idx, call in enumerate(calls):
                    # Name (and id/type)
                    delta1 = {
                        "tool_calls": [
                            {
                                "index": idx,
                                "id": call.get("id"),
                                "type": "function",
                                "function": {"name": call["function"]["name"]},
                            }
                        ]
                    }
                    yield _sse_chunk(rid, created, delta1)
                    # Arguments (as a single string chunk)
                    delta2 = {
                        "tool_calls": [
                            {
                                "index": idx,
                                "function": {"arguments": call["function"]["arguments"]},
                            }
                        ]
                    }
                    yield _sse_chunk(rid, created, delta2)
                # Final chunk indicating finish by tool_calls
                final = {
                    "id": rid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": MODEL_NAME,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
                }
                yield f"data: {json.dumps(final)}\n\n"
                yield "data: [DONE]\n\n"
            else:
                # No tool_calls detected; stream a single content chunk and stop
                yield _sse_chunk(rid, created, {"content": txt})
                final = {
                    "id": rid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": MODEL_NAME,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(final)}\n\n"
                # Commit conversation KV (if any)
                conv_meta = req.__dict__.get("_conv_commit")
                if conv_meta and not req.reset_conversation and not args.disable_kv_cache and args.enable_conversation_cache:
                    try:
                        cid = conv_meta.get("id")
                        tokens = conv_meta.get("tokens")
                        cached = req.__dict__.get("_precomputed_cache")[0]
                        rec = CONV_KV.get(cid)
                        if rec is not None:
                            rec.cache = cached
                            rec.tokens = tokens
                            rec.text = prompt_str
                            if not IS_VISION:
                                try:
                                    rec.base_text = build_base_prompt(req, len(imgs))
                                except Exception:
                                    pass
                            try:
                                offsets_new = req.__dict__.get("_boundary_offsets_new")
                                if offsets_new is None and not IS_VISION:
                                    offsets_new = _boundary_offsets_for_flat(flat_conv, len(imgs), tools=tools_template)
                                rec.boundary_offsets = offsets_new
                                rec.message_hashes = [_msg_hash(m.get('role',''), m.get('content','') or '') for m in flat_conv]
                            except Exception as e:
                                log.warning(f"Persist boundary metadata failed: {e}")
                        else:
                            base_txt = ""
                            if not IS_VISION:
                                try:
                                    base_txt = build_base_prompt(req, len(imgs))
                                except Exception:
                                    base_txt = ""
                            CONV_KV.put(cid, cached, tokens, text=prompt_str, base_text=base_txt)
                            try:
                                rec2 = CONV_KV.get(cid)
                                if rec2 is not None:
                                    offsets_new = req.__dict__.get("_boundary_offsets_new")
                                    if offsets_new is None and not IS_VISION:
                                        offsets_new = _boundary_offsets_for_flat(flat_conv, len(imgs), tools=tools_template)
                                    rec2.boundary_offsets = offsets_new
                                    rec2.message_hashes = [_msg_hash(m.get('role',''), m.get('content','') or '') for m in flat_conv]
                            except Exception as e:
                                log.warning(f"Persist boundary metadata (new rec) failed: {e}")
                        CONV_KV._enforce_budget(_global_kv_budget_tokens())
                        log.info(f"🧵 Conversation KV stored for '{cid}' (tokens={len(tokens)})")
                    except Exception as e:
                        log.warning(f"Conversation KV store failed: {e}")
                yield "data: [DONE]\n\n"
                return
        # Default: passthrough token streaming
        for chunk in stream_chunks(prompt_str, imgs, req):
            yield chunk
            await asyncio.sleep(0)
        # Commit after streaming completes
        conv_meta = req.__dict__.get("_conv_commit")
        if conv_meta and not req.reset_conversation and not args.disable_kv_cache and args.enable_conversation_cache:
            try:
                cid = conv_meta.get("id")
                tokens = conv_meta.get("tokens")
                cached = req.__dict__.get("_precomputed_cache")[0]
                rec = CONV_KV.get(cid)
                if rec is not None:
                    rec.cache = cached
                    rec.tokens = tokens
                    rec.text = prompt_str
                    if not IS_VISION:
                        try:
                            rec.base_text = build_base_prompt(req, len(imgs))
                        except Exception:
                            pass
                    try:
                        offsets_new = req.__dict__.get("_boundary_offsets_new")
                        if offsets_new is None and not IS_VISION:
                            offsets_new = _boundary_offsets_for_flat(flat_conv, len(imgs), tools=tools_template)
                        rec.boundary_offsets = offsets_new
                        rec.message_hashes = [_msg_hash(m.get('role',''), m.get('content','') or '') for m in flat_conv]
                    except Exception as e:
                        log.warning(f"Persist boundary metadata failed: {e}")
                else:
                    base_txt = ""
                    if not IS_VISION:
                        try:
                            base_txt = build_base_prompt(req, len(imgs))
                        except Exception:
                            base_txt = ""
                    CONV_KV.put(cid, cached, tokens, text=prompt_str, base_text=base_txt)
                    try:
                        rec2 = CONV_KV.get(cid)
                        if rec2 is not None:
                            offsets_new = req.__dict__.get("_boundary_offsets_new")
                            if offsets_new is None and not IS_VISION:
                                offsets_new = _boundary_offsets_for_flat(flat_conv, len(imgs), tools=tools_template)
                            rec2.boundary_offsets = offsets_new
                            rec2.message_hashes = [_msg_hash(m.get('role',''), m.get('content','') or '') for m in flat_conv]
                    except Exception as e:
                        log.warning(f"Persist boundary metadata (new rec) failed: {e}")
                CONV_KV._enforce_budget(_global_kv_budget_tokens())
                log.info(f"🧵 Conversation KV stored for '{cid}' (tokens={len(tokens)})")
            except Exception as e:
                log.warning(f"Conversation KV store failed: {e}")

    if req.stream:
        return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)
    else:
        if IS_VISION:
            usage = _usage_dict(len(prompt_str), _tok_len(txt), 0.0, 0, 0)
        else:
            usage = req.__dict__.get("_usage")
            if not isinstance(usage, dict):
                p_tok, c_tok, dur = (len(prompt_str), len(txt), 0.0)
                usage = _usage_dict(p_tok, c_tok, dur, 0, 0)
        payload2 = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": txt,
                        **(
                            {"reasoning_content": req.__dict__.get("_reasoning_content")}
                            if req.__dict__.get("_reasoning_content")
                            else {}
                        ),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": usage,
        }
        try:
            meta = {"conversation_id": headers.get("X-Conv-Id", "")}
            reasoning_ctx = req.__dict__.get("_reasoning_context")
            if reasoning_ctx:
                meta["reasoning_context"] = reasoning_ctx
            payload2["metadata"] = meta
        except Exception:
            payload2["metadata"] = {"conversation_id": ""}
        return JSONResponse(content=payload2, headers=headers)

def _serve_or_wait() -> None:
    if DISTRIBUTED.is_active:
        DISTRIBUTED.barrier("pre-server-dispatch")
    if DISTRIBUTED.should_host_server():
        extra = ""
        if DISTRIBUTED.is_active:
            extra = f" [rank {DISTRIBUTED.rank}/{DISTRIBUTED.world_size}]"
        log.info(
            "Serving %s on %s:%d  (vision=%s)%s",
            MODEL_NAME,
            args.host,
            args.port,
            IS_VISION,
            extra,
        )
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        log.info(
            "Rank %d waiting as distributed worker (server rank=%d).",
            DISTRIBUTED.rank,
            DISTRIBUTED.server_rank,
        )
        DISTRIBUTED.worker_forever()


def main_entry() -> None:
    _serve_or_wait()


# ─────────────────────────── main ────────────────────────────────
if __name__ == "__main__":
    _serve_or_wait()
