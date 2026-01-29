from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import imagecodecs as ic

from zarr.abc.codec import ArrayBytesCodec
from zarr.core.array_spec import ArraySpec
from zarr.core.buffer.cpu import Buffer as CPUBuffer


def _force_array(buf, spec: ArraySpec, *, want_dtype: np.dtype) -> np.ndarray:
    want_shape = tuple(spec.shape)
    if hasattr(buf, "as_numpy_array"):
        arr = np.asarray(buf.as_numpy_array())
    else:
        arr = np.asarray(buf)
    if arr.dtype != want_dtype:
        arr = arr.astype(want_dtype, copy=False)
    if tuple(arr.shape) != want_shape:
        arr = np.ascontiguousarray(arr).reshape(want_shape, order="C")
    return arr if arr.flags.c_contiguous else np.ascontiguousarray(arr)


class JPEGXLCodec(ArrayBytesCodec):
    """
    JPEG XL serializer for uint8/uint16 images (2D or 3D with channels 1 or 3).

    Parameters
    ----------
    distance: Optional[float]
        Butteraugli distance; lower is higher quality (lossy). None uses default.
    effort: Optional[int]
        Encoder effort/speed tradeoff (1..9); higher is slower/better.
    lossless: Optional[bool]
        If True, request lossless mode when supported.
    """

    codec_id = "cft_zarr.jpegxl"

    def __init__(self, *, distance: Optional[float] = None, effort: Optional[int] = None, lossless: Optional[bool] = None):
        if not hasattr(ic, "jpegxl_encode") or not hasattr(ic, "jpegxl_decode"):
            raise ImportError("imagecodecs missing JPEG XL support (jpegxl_encode/decode)")
        self.distance = float(distance) if distance is not None else None
        self.effort = int(effort) if effort is not None else None
        self.lossless = bool(lossless) if lossless is not None else None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JPEGXLCodec":
        cfg = (data.get("configuration") or {})
        return cls(**cfg)

    def validate(self, *, shape, dtype, chunk_grid) -> None:
        try:
            dt = np.dtype(dtype)
        except TypeError:
            s = str(dtype).lower()
            if 'uint8' in s:
                dt = np.uint8
            elif 'uint16' in s:
                dt = np.uint16
            else:
                raise TypeError(f"JPEGXLCodec supports uint8/uint16 only (got {dtype})")
        if dt not in (np.uint8, np.uint16):
            raise TypeError("JPEGXLCodec supports uint8/uint16 only")
        if len(shape) == 2:
            return
        if len(shape) == 3 and shape[-1] in (1, 3):
            return
        if len(shape) == 4 and shape[-1] in (1, 3):
            return
        raise TypeError(f"Unsupported shape for JPEGXLCodec: {shape}")

    def resolve_metadata(self, array_spec: ArraySpec) -> ArraySpec:
        return array_spec

    def to_dict(self) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        if self.distance is not None:
            cfg["distance"] = float(self.distance)
        if self.effort is not None:
            cfg["effort"] = int(self.effort)
        if self.lossless is not None:
            cfg["lossless"] = bool(self.lossless)
        # Use fully-qualified id for both id and name so reopen resolves by id
        return {"id": self.codec_id, "name": self.codec_id, "configuration": cfg}

    async def _encode_single(self, chunk, array_spec: ArraySpec):
        try:
            dt = np.dtype(array_spec.dtype)
        except TypeError:
            s = str(array_spec.dtype).lower()
            if 'uint8' in s:
                dt = np.uint8
            elif 'uint16' in s:
                dt = np.uint16
            else:
                raise
        arr = _force_array(chunk, array_spec, want_dtype=dt)
        # Collapse leading singleton Z if present for encoder
        if arr.ndim == 4 and arr.shape[0] == 1:
            arr = arr[0]
        kwargs: Dict[str, Any] = {}
        if self.distance is not None:
            kwargs["distance"] = self.distance
        if self.effort is not None:
            kwargs["effort"] = self.effort
        if self.lossless is not None:
            kwargs["lossless"] = self.lossless
        encoded = ic.jpegxl_encode(arr, **kwargs)
        return CPUBuffer.from_bytes(encoded)

    async def _decode_single(self, encoded, array_spec: ArraySpec):
        if hasattr(encoded, "to_bytes"):
            encoded = encoded.to_bytes()
        out = ic.jpegxl_decode(encoded)
        out = np.asarray(out)
        try:
            dt = np.dtype(array_spec.dtype)
        except TypeError:
            s = str(array_spec.dtype).lower()
            if 'uint8' in s:
                dt = np.uint8
            elif 'uint16' in s:
                dt = np.uint16
            else:
                raise
        if out.dtype != dt:
            out = out.astype(dt, copy=False)
        want = tuple(array_spec.shape)
        if len(want) == 4 and want[0] == 1 and out.ndim in (2, 3):
            out = np.ascontiguousarray(out)
            if out.ndim == 2:
                out = out[np.newaxis, :, :]
            else:
                out = out[np.newaxis, :, :, :]
        elif tuple(out.shape) != want:
            out = np.ascontiguousarray(out).reshape(want, order="C")
        return out


