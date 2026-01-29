from __future__ import annotations

import io
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Dict, Iterable, Iterator, Optional, Union

from ._exceptions import BadArchiveError, PylhasaError, UnsafePathError
from ._paths import NormalizedPath, normalize_path

try:
    from . import _pylhasa
except ImportError as exc:  # pragma: no cover - import error shown at runtime
    raise ImportError("pylhasa native extension is not built") from exc


@dataclass(frozen=True)
class Entry:
    """Metadata for a single archive entry."""
    raw_path: str
    raw_path_bytes: bytes
    safe_path: Optional[str]
    size: int
    compressed_size: int
    method: str
    crc: Optional[int]
    timestamp: Optional[int]
    is_dir: bool
    is_symlink: bool
    _index: int
    _archive: "Archive"

    def open(self) -> io.BufferedReader:
        """Open the entry for streaming reads."""
        return self._archive._open_entry(self)


class _EntryRawIO(io.RawIOBase):
    def __init__(self, reader: "_pylhasa.EntryReader") -> None:
        self._reader = reader

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        return self._reader.read(size)

    def readinto(self, b: bytearray) -> int:
        return self._reader.readinto(b)

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
            self._reader = None
        super().close()


class Archive(Iterable[Entry]):
    """High-level archive wrapper that provides iteration and extraction."""
    def __init__(self, backend: "_pylhasa.Archive", temp_path: Optional[Path] = None) -> None:
        self._backend = backend
        self._temp_path = temp_path
        self._closed = False
        self._entries = self._load_entries()
        self._entries_by_raw: Dict[str, Entry] = {entry.raw_path: entry for entry in self._entries}

    def _load_entries(self) -> list[Entry]:
        entries = []
        for idx, meta in enumerate(self._backend.entries()):
            raw_bytes = meta["raw_path_bytes"]
            if not isinstance(raw_bytes, (bytes, bytearray)):
                raw_bytes = bytes(raw_bytes)
            norm = normalize_path(bytes(raw_bytes))
            entry = Entry(
                raw_path=norm.raw_path,
                raw_path_bytes=norm.raw_path_bytes,
                safe_path=norm.safe_path,
                size=int(meta["size"]),
                compressed_size=int(meta["compressed_size"]),
                method=str(meta["method"]),
                crc=None if meta["crc"] is None else int(meta["crc"]),
                timestamp=None if meta["timestamp"] is None else int(meta["timestamp"]),
                is_dir=bool(meta["is_dir"]),
                is_symlink=bool(meta.get("is_symlink", False)),
                _index=idx,
                _archive=self,
            )
            entries.append(entry)
        return entries

    def __iter__(self) -> Iterator[Entry]:
        return iter(self._entries)

    def __enter__(self) -> "Archive":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def close(self) -> None:
        if self._closed:
            return
        self._backend.close()
        self._closed = True
        if self._temp_path is not None:
            try:
                self._temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _open_entry(self, entry: Entry) -> io.BufferedReader:
        reader = self._backend.open_entry(entry._index)
        raw = _EntryRawIO(reader)
        return io.BufferedReader(raw)

    def read(self, name_or_entry: Union[str, Entry]) -> bytes:
        entry = self._resolve_entry(name_or_entry)
        if entry.is_dir or entry.is_symlink:
            return b""
        with entry.open() as fp:
            return fp.read()

    def extract(self, name_or_entry: Union[str, Entry], dest_dir: Union[str, Path], safe: bool = True, allow_symlinks: bool = False) -> Path:
        entry = self._resolve_entry(name_or_entry)
        return self._extract_entry(entry, Path(dest_dir), safe=safe, allow_symlinks=allow_symlinks)

    def extractall(self, dest_dir: Union[str, Path], safe: bool = True, allow_symlinks: bool = False) -> list[Path]:
        dest = Path(dest_dir)
        extracted: list[Path] = []
        for entry in self._entries:
            extracted.append(self._extract_entry(entry, dest, safe=safe, allow_symlinks=allow_symlinks))
        return extracted

    def _resolve_entry(self, name_or_entry: Union[str, Entry]) -> Entry:
        if isinstance(name_or_entry, Entry):
            return name_or_entry
        if not isinstance(name_or_entry, str):
            raise TypeError("expected entry name or Entry")
        if name_or_entry in self._entries_by_raw:
            return self._entries_by_raw[name_or_entry]
        for entry in self._entries:
            if entry.safe_path == name_or_entry:
                return entry
        raise KeyError(f"entry not found: {name_or_entry}")

    def _extract_entry(self, entry: Entry, dest_dir: Path, safe: bool, allow_symlinks: bool) -> Path:
        if safe:
            if entry.safe_path is None:
                raise UnsafePathError(f"unsafe entry path: {entry.raw_path}")
            rel_path = Path(entry.safe_path)
        else:
            rel_path = Path(entry.raw_path)

        if entry.is_symlink and not allow_symlinks:
            raise UnsafePathError(f"symlink entry blocked: {entry.raw_path}")

        dest_dir = dest_dir.resolve()
        target = (dest_dir / rel_path).resolve()

        if safe:
            try:
                common = os.path.commonpath([str(dest_dir), str(target)])
            except ValueError:
                raise UnsafePathError(f"unsafe entry path: {entry.raw_path}")
            if common != str(dest_dir):
                raise UnsafePathError(f"unsafe entry path: {entry.raw_path}")

        if entry.is_dir:
            target.mkdir(parents=True, exist_ok=True)
            return target

        target.parent.mkdir(parents=True, exist_ok=True)
        with entry.open() as src, target.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        return target


def _open_from_path(path: Union[str, Path]) -> Archive:
    backend = _pylhasa.open_path(os.fspath(path))
    return Archive(backend)


def _open_from_bytes(data: bytes) -> Archive:
    backend = _pylhasa.open_bytes(data)
    return Archive(backend)


def _open_from_fileobj(fileobj: io.BufferedIOBase, buffering: int) -> Archive:
    if buffering <= 0:
        raise ValueError("buffering must be positive")
    # Spool to a temp file so liblhasa can stream without loading all bytes.
    temp = tempfile.NamedTemporaryFile(prefix="pylhasa_", suffix=".lha", delete=False)
    temp_path = Path(temp.name)
    try:
        shutil.copyfileobj(fileobj, temp, length=buffering)
    finally:
        temp.close()
    backend = _pylhasa.open_path(os.fspath(temp_path))
    return Archive(backend, temp_path=temp_path)


def open(path: Union[str, Path]) -> Archive:
    """Open an LHA/LZH archive from a file path."""
    return _open_from_path(path)


def open_bytes(data: bytes) -> Archive:
    """Open an LHA/LZH archive from bytes in memory."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    return _open_from_bytes(bytes(data))


def open_fileobj(fileobj: io.BufferedIOBase, buffering: int = 131072) -> Archive:
    """Open an LHA/LZH archive from a file-like object."""
    if not hasattr(fileobj, "read"):
        raise TypeError("fileobj must be file-like")
    return _open_from_fileobj(fileobj, buffering)
