"""FastAPI static file serving with zstd compression and SPA support."""

import mimetypes
import os
import time
from base64 import urlsafe_b64encode
from pathlib import Path, PurePath, PurePosixPath
from wsgiref.handlers import format_date_time

from blake3 import blake3
from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException
from zstandard import ZstdCompressor

# Dev mode: index files but don't load content, return error responses
_DEVMODE = os.getenv("FASTAPI_VUE_FRONTEND_URL")


class Frontend:
    """Static file server with automatic zstd compression and caching.

    Features:
    - Automatic zstd compression for compressible files
    - ETag-based caching with configurable cache headers
    - SPA (Single Page Application) support
    - Favicon handling from hashed assets
    - Dev mode: indexes files but returns error directing to Vite server

    Args:
        directory: Path to the directory containing static files
        index: Name of the index file (default: "index.html")
        spa: Enable SPA mode - serve index.html for unknown routes (default: False)
        cached: Path prefixes that should have immutable cache headers
        zstdlevel: Zstd compression level (default: 18)
        favicon: Path to favicon for automatic /favicon.ico handling
    """

    def __init__(
        self,
        directory: Path | str,
        *,
        index: str = "index.html",
        spa: bool = False,
        cached: str | list[str] | None = None,
        zstdlevel: int = 18,
        favicon: str | None = None,
    ) -> None:
        self.www: dict[str, tuple[bytes, bytes | None, dict]] = {}
        self.base: Path = Path(directory)
        self.index = index
        self.spa = spa
        if cached is None:
            self.cached_paths = []
        elif isinstance(cached, str):
            self.cached_paths = [cached]
        else:
            self.cached_paths = cached
        self.zstdlevel = zstdlevel
        self.favicon = favicon
        self.devmode = bool(_DEVMODE)

    def _index_only(self) -> set[str]:
        """Index file paths without loading content (for dev mode)."""
        paths: set[str] = set()
        if not self.base.exists():
            return paths
        queue = [PurePath()]
        while queue:
            current = self.base / queue.pop(0)
            for p in current.iterdir():
                rel = p.relative_to(self.base)
                if p.is_dir():
                    queue.append(rel)
                    continue
                name = "/" + rel.as_posix()
                name = name.removesuffix(self.index)
                paths.add(name)
        if self.favicon:
            p = PurePosixPath(self.favicon)
            base = str(p.with_suffix(""))
            ext = p.suffix
            if any(path.startswith(base) and path.endswith(ext) for path in paths):
                paths.add("/favicon.ico")
        return paths

    def _load(self, existing: dict):
        """Load static files from disk with compression."""
        new: dict[str, tuple[bytes, bytes | None, dict]] = {}
        if not self.base.exists():
            raise ValueError(f"Frontend folder {self.base} not found (try uv build)")
        paths = [PurePath()]
        while paths:
            current = self.base / paths.pop(0)
            for p in current.iterdir():
                rel = p.relative_to(self.base)
                if p.is_dir():
                    paths.append(rel)
                    continue
                # Read file
                name = "/" + rel.as_posix()
                mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
                name = name.removesuffix(self.index)
                data = p.read_bytes()
                etag = urlsafe_b64encode(blake3(data).digest(9)).decode()
                # Keep existing identical files as they are
                if name in existing and existing[name][2]["etag"] == etag:
                    new[name] = existing[name]
                    continue
                if mime.startswith("text/"):
                    mime += "; charset=UTF-8"
                mtime = p.stat().st_mtime
                cached = any(name.startswith(prefix) for prefix in self.cached_paths)
                headers = {
                    "etag": f'"{etag}"',
                    "last-modified": format_date_time(mtime),
                    "cache-control": (
                        "max-age=31536000, immutable" if cached else "no-cache"
                    ),
                    "content-type": mime,
                }
                zstd = ZstdCompressor(self.zstdlevel).compress(data)
                if len(zstd) >= len(data):
                    zstd = None
                new[name] = data, zstd, headers
        if self.favicon:
            p = PurePosixPath(self.favicon)
            base = str(p.with_suffix(""))
            ext = p.suffix
            hashed_path = next(
                (path for path in new if path.startswith(base) and path.endswith(ext)),
                None,
            )
            if hashed_path:
                new["/favicon.ico"] = new[hashed_path]
        if not new:
            msg = "Frontend files missing, check your installation.\n"
            new["/"] = (
                msg.encode(),
                None,
                {
                    "etag": "error",
                    "content-type": "text/plain",
                    "cache-control": "no-store",
                },
            )
        return new

    async def load(self, *, log=True):
        """Load or reload static files from disk.

        In dev mode (FASTAPI_VUE_FRONTEND_URL set), only indexes paths without loading content.
        """
        start = time.perf_counter()
        if self.devmode:
            # Dev mode: just index paths, no content loading
            paths = await run_in_threadpool(self._index_only)
            self._devmode_paths = paths
            duration = time.perf_counter() - start
            if log and paths:
                print(
                    f"{self.base.name}: indexed {len(paths)} paths in {1000 * duration:.1f} ms (dev mode)"
                )
            return

        self.www = await run_in_threadpool(self._load, self.www)
        duration = time.perf_counter() - start
        if not log:
            return
        compfiles = [(len(d), len(z)) for d, z, _ in self.www.values() if z]
        raw = sum(v[0] for v in compfiles)
        comp = sum(v[1] for v in compfiles)
        ratio = comp / raw * 100 if raw else 100.0
        print(
            f"{self.base.name}: {len(self.www)} files in {1000 * duration:.1f} ms | "
            f"zstd {len(compfiles)} files {1e-6 * raw:.2f}->{1e-6 * comp:.2f} MB ({ratio:.0f} %)"
        )

    def route(self, app: FastAPI, mount_path="/", *, name="frontend"):
        """Register this frontend handler with a FastAPI app.

        Args:
            app: FastAPI application instance
            mount_path: Path where the frontend should be mounted (default: "/")
            name: Route name for the handler
        """
        path = mount_path.rstrip("/") + "{path:path}"
        app.api_route(path, methods=["GET", "HEAD"], name=name)(self.handle)

    def handle(self, request: Request, path: str):
        """Static file handler. Takes path already stripped of mount_path prefix."""
        name = path.removesuffix(self.index)

        # Dev mode: return error directing to Vite server
        if self.devmode:
            paths = getattr(self, "_devmode_paths", set())
            if name not in paths:
                if name and f"{name}/" in paths:
                    return RedirectResponse(request.url.path + "/")
                if self.spa and "text/html" in request.headers.get("accept", ""):
                    name = "/"
                if name not in paths:
                    raise HTTPException(status_code=404)
            return JSONResponse(
                status_code=409,
                content={
                    "detail": f"Frontend assets served by Vite in dev mode. Connect via {_DEVMODE} instead."
                },
            )

        if name not in self.www:
            # Friendly redirect for directories missing trailing slash
            if name and f"{name}/" in self.www:
                return RedirectResponse(request.url.path + "/")
            # SPA support: serve / for unknown paths if the browser wants HTML
            if self.spa and "text/html" in request.headers.get("accept", ""):
                name = "/"
            # 404 for everything else
            if name not in self.www:
                raise HTTPException(status_code=404)
        # File found, give the appropriate response
        data, zstd, headers = self.www[name]
        if request.headers.get("if-none-match") == headers["etag"]:
            return Response(status_code=304, headers=headers)
        if zstd and "zstd" in request.headers.get("accept-encoding", ""):
            headers["content-encoding"] = "zstd"
            data = zstd
        return Response(content=data, headers=headers)
