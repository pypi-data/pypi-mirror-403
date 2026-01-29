"""cft_zarr package - runtime registration of custom Zarr v3 codecs.

This module registers available codecs so Zarr can resolve them by name:
  - cft_zarr.shift12jls (ArrayBytesCodec serializer - no incremental updates)
  - cft_zarr.jpeg (ArrayBytesCodec serializer - no incremental updates)
  - cft_zarr.shift12jls_compressor (BytesBytesCodec compressor - supports incremental updates)
  - cft_zarr.jpeg_compressor (BytesBytesCodec compressor - supports incremental updates)
  - cft_zarr.jpegxl

Registration is attempted against the Zarr v3 registry API. If unavailable,
we try a legacy-style register function as a best effort.
"""

from typing import Any

__all__ = [
    "Shift12JLSCodec",
    "JPEGCodec",
    "Shift12JLSCompressor",
    "JPEGCompressor",
]

# Import codecs if available
Shift12JLSCodec: Any = None
JPEGCodec: Any = None
Shift12JLSCompressor: Any = None
JPEGCompressor: Any = None
JPEGXLCodec: Any = None

try:
    from .shift12jls import Shift12JLSCodec as _Shift12JLSCodec
    Shift12JLSCodec = _Shift12JLSCodec
except Exception:
    Shift12JLSCodec = None

try:
    from .jpeg import JPEGCodec as _JPEGCodec
    JPEGCodec = _JPEGCodec
except Exception:
    JPEGCodec = None

try:
    from .shift12jls_compressor import Shift12JLSCompressor as _Shift12JLSCompressor
    Shift12JLSCompressor = _Shift12JLSCompressor
except Exception:
    Shift12JLSCompressor = None

try:
    from .jpeg_compressor import JPEGCompressor as _JPEGCompressor
    JPEGCompressor = _JPEGCompressor
except Exception:
    JPEGCompressor = None

try:
    from .jpegxl import JPEGXLCodec as _JPEGXLCodec
    JPEGXLCodec = _JPEGXLCodec
except Exception:
    JPEGXLCodec = None


def _register_if_possible(cls: Any) -> None:
    if cls is None:
        return
    # Use Zarr v3 registry API (zarr.registry.register_codec)
    # Signature: register_codec(key: str, codec_cls: type[Codec])
    try:
        from zarr import registry as zregistry  # type: ignore
        codec_id = getattr(cls, 'codec_id', None)
        if codec_id:
            zregistry.register_codec(codec_id, cls)  # type: ignore[attr-defined]
    except Exception as e:
        # Log error for debugging but don't fail
        import warnings
        warnings.warn(f"Failed to register codec {cls}: {e}", UserWarning)


def _force_map(cls: Any) -> None:
    """Best-effort: insert codec class into known registry maps for immediate availability."""
    if cls is None:
        return
    cid = getattr(cls, 'codec_id', None)
    cname = getattr(cls, '__name__', None)
    if not cid and not cname:
        return
    # zarr.registry private maps - try all possible registry attribute names
    try:
        from zarr import registry as zregistry  # type: ignore
        for attr_name in ('_CODECS', 'CODECS', '_codecs', 'codecs', '_registry', 'registry'):
            reg = getattr(zregistry, attr_name, None)
            if isinstance(reg, dict):
                if cid:
                    reg[cid] = cls
                if cname:
                    reg[cname] = cls
                # Also try name lookup (Zarr might look up by class name)
                if cname and cname != cid:
                    reg[cname] = cls
    except Exception:
        pass
    # zarr.codecs.registry private maps
    try:
        from zarr.codecs import registry as cregistry  # type: ignore
        for attr_name in ('_CODECS', 'CODECS', '_codecs', 'codecs', '_registry', 'registry'):
            reg = getattr(cregistry, attr_name, None)
            if isinstance(reg, dict):
                if cid:
                    reg[cid] = cls
                if cname:
                    reg[cname] = cls
                # Also try name lookup
                if cname and cname != cid:
                    reg[cname] = cls
    except Exception:
        pass
    # Try registering via get_codec if it exists (Zarr v3 resolver)
    try:
        from zarr.codecs import get_codec  # type: ignore
        # This might register it
    except Exception:
        pass
    # Force register with any resolver functions we can find
    try:
        from zarr import registry as zregistry  # type: ignore
        # Try to find and call a resolver or register function
        for attr_name in ('resolve_codec', 'get_codec', 'register', 'add'):
            resolver = getattr(zregistry, attr_name, None)
            if callable(resolver):
                try:
                    if cid:
                        resolver(cid, cls)  # type: ignore
                except Exception:
                    try:
                        resolver(cls)  # type: ignore
                    except Exception:
                        pass
    except Exception:
        pass


# Runtime registration
_register_if_possible(Shift12JLSCodec)
_register_if_possible(JPEGCodec)
_register_if_possible(Shift12JLSCompressor)
_register_if_possible(JPEGCompressor)
_register_if_possible(JPEGXLCodec)

# Force-map as a last resort so reopened arrays can resolve codecs immediately
_force_map(Shift12JLSCodec)
_force_map(JPEGCodec)
_force_map(Shift12JLSCompressor)
_force_map(JPEGCompressor)
_force_map(JPEGXLCodec)

from .shift12jls import Shift12JLSCodec
from .jpeg import JPEGCodec
from .shift12jls_compressor import Shift12JLSCompressor
from .jpeg_compressor import JPEGCompressor

__all__ = ["Shift12JLSCodec", "JPEGCodec", "Shift12JLSCompressor", "JPEGCompressor"]


def _register_for_napari():
    """
    Napari plugin hook - ensures codecs are registered when napari starts.
    
    This function is called by napari when the plugin is loaded, ensuring
    that custom Zarr codecs are registered before any Zarr files are opened.
    
    The codecs are already registered during module import (see above),
    but this function provides an explicit hook for napari.
    """
    # Re-register in case napari loads us before any other import side effects.
    _register_if_possible(Shift12JLSCodec)
    _register_if_possible(JPEGCodec)
    _register_if_possible(Shift12JLSCompressor)
    _register_if_possible(JPEGCompressor)
    _register_if_possible(JPEGXLCodec)

    # Force-map as a last resort so reopened arrays can resolve codecs immediately
    _force_map(Shift12JLSCodec)
    _force_map(JPEGCodec)
    _force_map(Shift12JLSCompressor)
    _force_map(JPEGCompressor)
    _force_map(JPEGXLCodec)
