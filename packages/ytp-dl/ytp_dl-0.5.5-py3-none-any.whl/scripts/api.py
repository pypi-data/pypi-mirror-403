#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import tempfile
import time
from typing import Iterator

from flask import Flask, Response, jsonify, request, stream_with_context
from gevent.lock import Semaphore

from .downloader import download_video, validate_environment

app = Flask(__name__)

# Job workspace parent directory.
# IMPORTANT: prefer a temp-friendly path; avoid /root by default.
BASE_DOWNLOAD_DIR = os.environ.get("YTPDL_JOB_BASE_DIR", "/var/tmp/ytpdl_jobs")
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

MAX_CONCURRENT = int(os.environ.get("YTPDL_MAX_CONCURRENT", "1"))
_sem = Semaphore(MAX_CONCURRENT)

# Failsafe: delete abandoned job dirs older than this many seconds.
STALE_JOB_TTL_S = int(os.environ.get("YTPDL_STALE_JOB_TTL_S", "21600"))  # 6 hours


def _cleanup_stale_jobs() -> None:
    """Best-effort cleanup of old job directories."""
    now = time.time()
    try:
        for name in os.listdir(BASE_DOWNLOAD_DIR):
            p = os.path.join(BASE_DOWNLOAD_DIR, name)
            if not os.path.isdir(p):
                continue
            try:
                age = now - os.path.getmtime(p)
            except Exception:
                continue
            if age > STALE_JOB_TTL_S:
                shutil.rmtree(p, ignore_errors=True)
    except Exception:
        # Never break request handling due to cleanup.
        pass


def _stream_file_and_cleanup(path: str, job_dir: str, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    """
    Stream the file in chunks and ALWAYS remove the job_dir afterwards.

    Why not send_file(...).call_on_close(...):
      - In some WSGI / gevent edge cases, call_on_close may not fire reliably,
        especially on client disconnects/timeouts.
      - A generator with a finally block is reliably closed when the response ends.
    """
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    finally:
        try:
            shutil.rmtree(job_dir, ignore_errors=True)
        except Exception:
            pass


@app.route("/api/download", methods=["POST"])
def handle_download():
    _cleanup_stale_jobs()

    if not _sem.acquire(blocking=False):
        return jsonify(error="Server busy, try again later"), 503

    job_dir: str | None = None
    released = False

    def _release_once() -> None:
        nonlocal released
        if not released:
            released = True
            _sem.release()

    try:
        data = request.get_json(force=True)
        url = (data.get("url") or "").strip()
        resolution = data.get("resolution")
        extension = data.get("extension")

        if not url:
            _release_once()
            return jsonify(error="Missing 'url'"), 400

        job_dir = tempfile.mkdtemp(prefix="ytpdl_", dir=BASE_DOWNLOAD_DIR)

        # yt-dlp work (guarded by semaphore)
        filename = download_video(
            url=url,
            resolution=resolution,
            extension=extension,
            out_dir=job_dir,
        )

        if not (filename and os.path.exists(filename)):
            raise RuntimeError("Download failed")

        # Release semaphore as soon as yt-dlp is done.
        # Streaming the file should not block the next download job.
        _release_once()

        basename = os.path.basename(filename) or "download"
        headers = {
            "Content-Disposition": f'attachment; filename="{basename}"',
        }

        return Response(
            stream_with_context(_stream_file_and_cleanup(filename, job_dir)),
            mimetype="application/octet-stream",
            headers=headers,
        )

    except RuntimeError as e:
        if job_dir:
            shutil.rmtree(job_dir, ignore_errors=True)
        _release_once()

        msg = str(e)
        if "Mullvad not logged in" in msg:
            return jsonify(error=msg), 503
        return jsonify(error=f"Download failed: {msg}"), 500

    except Exception as e:
        if job_dir:
            shutil.rmtree(job_dir, ignore_errors=True)
        _release_once()
        return jsonify(error=f"Download failed: {str(e)}"), 500


@app.route("/healthz", methods=["GET"])
def healthz():
    # gevent Semaphore exposes .counter (current available permits)
    return jsonify(ok=True, in_use=(MAX_CONCURRENT - _sem.counter), capacity=MAX_CONCURRENT), 200


def main():
    validate_environment()
    print("Starting ytp-dl API server...")
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
