#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from typing import List, Optional, Tuple

# =========================
# Config / constants
# =========================
VENV_PATH = os.environ.get("YTPDL_VENV", "/opt/yt-dlp-mullvad/venv")
YTDLP_BIN = os.path.join(VENV_PATH, "bin", "yt-dlp")

MULLVAD_LOCATION = os.environ.get("YTPDL_MULLVAD_LOCATION", "us")

MODERN_UA = os.environ.get(
    "YTPDL_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
)

FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"

# Only used if download_video() is called without out_dir.
DEFAULT_OUT_DIR = os.environ.get("YTPDL_DOWNLOAD_DIR", "/var/tmp/ytpdl_out")

# Subprocess timeouts (seconds)
# - Mullvad commands should never hang forever.
MULLVAD_CMD_TIMEOUT_S = int(os.environ.get("YTPDL_MULLVAD_CMD_TIMEOUT_S", "30"))
MULLVAD_CONNECT_WAIT_S = int(os.environ.get("YTPDL_MULLVAD_CONNECT_WAIT_S", "25"))

# - yt-dlp/ffmpeg can take a while for large downloads; do NOT set a max file size.
#   This is strictly a hung-process safety net.
YTDLP_TIMEOUT_S = int(os.environ.get("YTPDL_YTDLP_TIMEOUT_S", "7200"))  # 2 hours

# Keep error payloads readable (your web UI prints these).
_MAX_ERR_LINES = 80
_MAX_ERR_CHARS = 4000


# =========================
# Shell helpers
# =========================
def _run_argv_capture(argv: List[str], timeout_s: Optional[int] = None) -> Tuple[int, str]:
    try:
        res = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_s,
        )
        return res.returncode, (res.stdout or "")
    except subprocess.TimeoutExpired as e:
        out = e.stdout or b""
        if isinstance(out, bytes):
            try:
                out = out.decode("utf-8", errors="replace")
            except Exception:
                out = ""
        out = out or ""
        return 124, (out + f"\n[ytp-dl] Command timed out after {timeout_s}s\n")


def _run_argv(argv: List[str], check: bool = True, timeout_s: Optional[int] = None) -> str:
    rc, out = _run_argv_capture(argv, timeout_s=timeout_s)
    if check and rc != 0:
        cmd = " ".join(shlex.quote(p) for p in argv)
        raise RuntimeError(f"Command failed: {cmd}\n{out}")
    return out


def _tail(out: str) -> str:
    lines = (out or "").splitlines()
    tail_lines = lines[-_MAX_ERR_LINES:]
    txt = "\n".join(tail_lines)
    if len(txt) > _MAX_ERR_CHARS:
        txt = txt[-_MAX_ERR_CHARS:]
    return txt.strip()


# =========================
# Environment / Mullvad
# =========================
def validate_environment() -> None:
    if not os.path.exists(YTDLP_BIN):
        raise RuntimeError(f"yt-dlp not found at {YTDLP_BIN}")
    if shutil.which(FFMPEG_BIN) is None:
        raise RuntimeError("ffmpeg not found on PATH")


def _mullvad_present() -> bool:
    return shutil.which("mullvad") is not None


def mullvad_logged_in() -> bool:
    if not _mullvad_present():
        return False
    try:
        res = subprocess.run(
            ["mullvad", "account", "get"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=MULLVAD_CMD_TIMEOUT_S,
        )
        return "not logged in" not in (res.stdout or "").lower()
    except subprocess.TimeoutExpired:
        return False


def require_mullvad_login() -> None:
    if _mullvad_present() and not mullvad_logged_in():
        raise RuntimeError("Mullvad not logged in. Run: mullvad account login <ACCOUNT>")


def mullvad_wait_connected(timeout: int = MULLVAD_CONNECT_WAIT_S) -> bool:
    """
    Poll until Mullvad reports Connected.
    """
    if not _mullvad_present():
        return True
    for _ in range(max(1, int(timeout))):
        try:
            res = subprocess.run(
                ["mullvad", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=MULLVAD_CMD_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            time.sleep(1)
            continue
        if "Connected" in (res.stdout or ""):
            return True
        time.sleep(1)
    return False


def mullvad_rotate_ip(location: Optional[str] = None) -> None:
    """
    Rotate to a fresh Mullvad connection *without* leaving the machine disconnected.

    Why:
      - Disconnecting can trigger Mullvad's "block when disconnected" firewall behavior,
        making your API unreachable (port 5000 looks down).
      - `mullvad reconnect` rotates relays (fresh IP) while keeping the VPN up.

    Strategy:
      1) Optionally pin relay location (country/city) each job.
      2) Prefer `mullvad reconnect` (new relay / new IP).
      3) Fall back to `mullvad connect` if reconnect isn't available.
      4) Wait for Connected.
    """
    if not _mullvad_present():
        return

    loc = (location or MULLVAD_LOCATION).strip()

    # Best-effort location pinning.
    if loc:
        _run_argv(["mullvad", "relay", "set", "location", loc], check=False, timeout_s=MULLVAD_CMD_TIMEOUT_S)

    # Prefer reconnect (keeps VPN up, rotates relay).
    rc, out = _run_argv_capture(["mullvad", "reconnect"], timeout_s=MULLVAD_CMD_TIMEOUT_S)
    if rc != 0:
        # Older CLI versions may not have reconnect; try connect.
        _run_argv(["mullvad", "connect"], check=False, timeout_s=MULLVAD_CMD_TIMEOUT_S)

    if not mullvad_wait_connected(timeout=MULLVAD_CONNECT_WAIT_S):
        raise RuntimeError("Mullvad connection failed (did not reach Connected state)")


# =========================
# yt-dlp helpers
# =========================
def _common_flags() -> List[str]:
    # --no-playlist prevents accidental channel/playlist pulls (and disk blowups)
    return [
        "--no-playlist",
        "--retries", "10",
        "--fragment-retries", "10",
        "--retry-sleep", "exp=1:30",
        "--user-agent", MODERN_UA,
        "--no-cache-dir",
        "--ignore-config",
        "--embed-metadata",
        "--sleep-interval", "1",
    ]


def _extract_final_path(stdout: str, out_dir: str) -> Optional[str]:
    """
    Robustly derive the final output file path from yt-dlp output.

    Priority:
      1) --print after_move:filepath lines (absolute paths)
      2) [Merger] Merging formats into "..."
      3) Any Destination: lines that still exist
      4) Newest non-temp file in out_dir
    """
    candidates: List[str] = []
    out_dir = os.path.abspath(out_dir)

    for raw in (stdout or "").splitlines():
        line = (raw or "").strip()
        if not line:
            continue

        # 1) --print after_move:filepath (usually an absolute path)
        if os.path.isabs(line) and line.startswith(out_dir):
            candidates.append(line.strip("'\""))
            continue

        # 2) Merger line: ... into "path"
        if "Merging formats into" in line and "\"" in line:
            try:
                merged = line.split("Merging formats into", 1)[1].strip()
                if merged.startswith("\"") and merged.endswith("\""):
                    merged = merged[1:-1]
                else:
                    # handle: ... into "file"
                    if merged.startswith("\""):
                        merged = merged.split("\"", 2)[1]
                if merged:
                    if not os.path.isabs(merged):
                        merged = os.path.join(out_dir, merged)
                    candidates.append(merged.strip("'\""))
            except Exception:
                pass
            continue

        # 3) Destination lines (download/extractaudio)
        if "Destination:" in line:
            try:
                p = line.split("Destination:", 1)[1].strip().strip("'\"")
                if p and not os.path.isabs(p):
                    p = os.path.join(out_dir, p)
                if p:
                    candidates.append(p)
            except Exception:
                pass
            continue

        # already downloaded
        if "] " in line and " has already been downloaded" in line:
            try:
                p = (
                    line.split("] ", 1)[1]
                    .split(" has already been downloaded", 1)[0]
                    .strip()
                    .strip("'\"")
                )
                if p and not os.path.isabs(p):
                    p = os.path.join(out_dir, p)
                if p:
                    candidates.append(p)
            except Exception:
                pass

    # Prefer existing, newest candidate (reverse traversal)
    for p in reversed(candidates):
        if p and os.path.exists(p):
            return p

    # 4) Fallback: newest non-temp file in out_dir
    try:
        best_path = None
        best_mtime = -1.0
        for name in os.listdir(out_dir):
            if name.endswith((".part", ".ytdl", ".tmp")):
                continue
            full = os.path.join(out_dir, name)
            if not os.path.isfile(full):
                continue
            mt = os.path.getmtime(full)
            if mt > best_mtime:
                best_mtime = mt
                best_path = full
        if best_path:
            return best_path
    except Exception:
        pass

    return None


def _download_with_format(url: str, out_dir: str, fmt: str, merge_mp4: bool) -> str:
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    out_tpl = os.path.join(out_dir, "%(title)s.%(ext)s")

    argv = [
        YTDLP_BIN,
        "-f", fmt,
        *(_common_flags()),
        "--output", out_tpl,
        # Ensure we can reliably pick the final output path.
        "--print", "after_move:filepath",
    ]
    if merge_mp4:
        argv.extend(["--merge-output-format", "mp4"])

    argv.append(url)

    rc, out = _run_argv_capture(argv, timeout_s=YTDLP_TIMEOUT_S)
    path = _extract_final_path(out, out_dir)

    if path and os.path.exists(path):
        return os.path.abspath(path)

    tail = _tail(out)
    if rc == 124:
        raise RuntimeError(f"yt-dlp timed out after {YTDLP_TIMEOUT_S}s (format: {fmt})\n{tail}")
    if rc != 0:
        raise RuntimeError(f"yt-dlp failed (format: {fmt})\n{tail}")
    raise RuntimeError(f"Download completed but output file not found (format: {fmt})\n{tail}")


# =========================
# Public API
# =========================
def download_video(
    url: str,
    resolution: int | None = 1080,
    extension: Optional[str] = None,
    out_dir: str = DEFAULT_OUT_DIR,
) -> str:
    if not url:
        raise RuntimeError("Missing URL")

    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    validate_environment()
    require_mullvad_login()

    # Rotate VPN connection per job (fresh IP) without ever leaving the host disconnected.
    mullvad_rotate_ip(MULLVAD_LOCATION)

    ext = (extension or "").lower().strip()
    if ext == "mp3":
        # bestaudio -> ffmpeg -> mp3 (handled by yt-dlp)
        return _download_with_format(
            url=url,
            out_dir=out_dir,
            fmt="bestaudio",
            merge_mp4=False,
        )

    cap = int(resolution or 1080)

    # Prefer exact cap H.264/AAC MP4 when available (more compatible).
    fmt1 = (
        f"bv*[height={cap}][vcodec~='^(avc1|h264)'][ext=mp4]"
        f"+ba[acodec~='^mp4a'][ext=m4a]"
        f"/b[height={cap}][vcodec~='^(avc1|h264)'][ext=mp4]"
    )
    try:
        return _download_with_format(url, out_dir, fmt1, merge_mp4=True)
    except Exception:
        pass

    # Fallback: best available up to cap
    fmt2 = f"bv*[height<={cap}]+ba/b[height<={cap}]"
    return _download_with_format(url, out_dir, fmt2, merge_mp4=True)
