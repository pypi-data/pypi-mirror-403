from __future__ import annotations
from zarr.core.buffer.cpu import Buffer as CPUBuffer
from typing import Any, Dict, Optional, Tuple
import numpy as np
import imagecodecs as ic

from zarr.abc.codec import ArrayBytesCodec
from zarr.core.array_spec import ArraySpec


def _lookup(names: Tuple[str, ...]):
    for n in names:
        fn = getattr(ic, n, None)
        if fn is not None:
            return fn
    return None

_JPEGLS_ENC = _lookup(("jpeg_ls_encode", "jpegls_encode"))
_JPEGLS_DEC = _lookup(("jpeg_ls_decode", "jpegls_decode"))


def _is_uint16_dtype(dt: Any) -> bool:
    try:
        return np.dtype(dt) == np.uint16
    except TypeError:
        pass
    bits = getattr(dt, "bits", None)
    signed = getattr(dt, "signed", None)
    if bits == 16 and signed is False:
        return True
    return "uint16" in str(dt).lower()


def _endianness_dtype(spec: ArraySpec) -> np.dtype:
    end = getattr(spec.dtype, "endianness", None)
    if end == "little":
        return np.dtype("<u2")
    if end == "big":
        return np.dtype(">u2")
    return np.dtype("u2")


def _force_uint16_array(buf, spec: ArraySpec) -> np.ndarray:
    """
    Coerce buf (ndarray/NDBuffer/bytes-like) to C-contiguous uint16 with shape == spec.shape.
    """
    want_shape = tuple(spec.shape)
    want_elems = int(np.prod(want_shape, dtype=np.int64))
    dt16 = _endianness_dtype(spec)

    # bytes-like → uint16 view + reshape
    if isinstance(buf, (bytes, bytearray, memoryview)):
        raw_u8 = np.frombuffer(buf, dtype=np.uint8)
        need_bytes = want_elems * 2
        if raw_u8.nbytes < need_bytes:
            raise ValueError(f"Insufficient bytes: have {raw_u8.nbytes}, need {need_bytes}")
        if raw_u8.nbytes != need_bytes:
            raw_u8 = raw_u8[:need_bytes]
        arr16 = raw_u8.view(dt16).reshape(want_shape, order="C")
        return arr16 if arr16.flags.c_contiguous else np.ascontiguousarray(arr16)

    # NDBuffer-like with .as_numpy_array(), else generic
    if hasattr(buf, "as_numpy_array"):
        arr = np.asarray(buf.as_numpy_array())
    else:
        arr = np.asarray(buf)

    # unwrap trivial object arrays
    if arr.dtype == object:
        try:
            inner = arr.item() if arr.ndim == 0 else next(iter(arr.flat))
            return _force_uint16_array(inner, spec)
        except Exception:
            pass

    # dtype normalize
    if arr.dtype == np.uint8:
        arr = arr.view(dt16)
    elif arr.dtype != np.uint16:
        arr = arr.astype(np.uint16, copy=False)

    # shape normalize
    if tuple(arr.shape) != want_shape:
        flat = arr.reshape(-1, order="C")
        if flat.size < want_elems:
            raise ValueError(f"Chunk elems mismatch: have {flat.size}, need {want_elems}")
        if flat.size > want_elems:
            flat = flat[:want_elems]
        arr = flat.reshape(want_shape, order="C")

    return arr if arr.flags.c_contiguous else np.ascontiguousarray(arr)


class Shift12JLSCodec(ArrayBytesCodec):
    """
    Serializer that:
      - encode: (uint16 >> 4) -> JPEG-LS bytes
      - decode: JPEG-LS -> (uint16 << 4)

    Use as serializer={"name": "cft_zarr.shift12jls"} (and set compressors=[]).
    """
    # Use package-qualified codec id for clarity and consistency
    codec_id = "cft_zarr.shift12jls"

    def __init__(self, *, near_lossless: Optional[int] = None):
        if _JPEGLS_ENC is None or _JPEGLS_DEC is None:
            raise ImportError(
                "imagecodecs JPEG-LS functions not found. "
                "Install imagecodecs with JPEG-LS enabled."
            )
        self.near_lossless = near_lossless

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Shift12JLSCodec":
        cfg = (data.get("configuration") or {})
        return cls(**cfg)

    def validate(self, *, shape, dtype, chunk_grid) -> None:
        if not _is_uint16_dtype(dtype):
            raise TypeError("Shift12JLSCodec only supports uint16 arrays")
        # Accept 2D (H,W) or 3D (Z,H,W) (any Z; codec runs per-chunk)
        if len(shape) == 2:
            return
        if len(shape) == 3:
            return
        raise TypeError(f"Unsupported shape for Shift12JLSCodec: {shape}")

    def resolve_metadata(self, array_spec: ArraySpec) -> ArraySpec:
        return array_spec

    # Ensure Zarr can persist this codec in zarr.json
    def to_dict(self) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        if self.near_lossless is not None:
            cfg["near_lossless"] = int(self.near_lossless)
        # Use fully-qualified id for both id and name so reopen resolves by id
        return {"id": self.codec_id, "name": self.codec_id, "configuration": cfg}

    async def _encode_single(self, chunk, array_spec: ArraySpec):
        # array -> bytes (Buffer)
        a16 = _force_uint16_array(chunk, array_spec)
        
        # Handle 3D chunks by encoding each slice separately
        if a16.ndim == 3 and a16.shape[0] > 1:
            # Multiple slices in chunk - encode each slice separately
            import io
            n_slices = a16.shape[0]
            encoded_slices = []
            
            for i in range(n_slices):
                slice_2d = a16[i]
                shifted = (slice_2d >> 4).astype(np.uint8, copy=False)
                
                # Ensure contiguous array
                if not shifted.flags.c_contiguous:
                    shifted = np.ascontiguousarray(shifted)
                
                # Pre-allocate output buffer
                out_buffer = np.empty(shifted.size, dtype=np.uint8)
                
                if self.near_lossless is not None:
                    encoded = None
                    for key in ("near_lossless", "near"):
                        try:
                            encoded = _JPEGLS_ENC(shifted, out=out_buffer, **{key: int(self.near_lossless)})  # type: ignore[misc]
                            break
                        except (TypeError, ValueError):
                            encoded = None
                    if encoded is None:
                        try:
                            encoded = _JPEGLS_ENC(shifted, out=out_buffer)  # type: ignore[misc]
                        except (TypeError, ValueError):
                            encoded = _JPEGLS_ENC(shifted)  # type: ignore[misc]
                else:
                    try:
                        encoded = _JPEGLS_ENC(shifted, out=out_buffer)  # type: ignore[misc]
                    except (TypeError, ValueError):
                        encoded = _JPEGLS_ENC(shifted)  # type: ignore[misc]
                
                encoded_slices.append(encoded)
            
            # Combine all encoded slices: [n_slices (4 bytes)][slice_0_len (4 bytes)][slice_0_data]...
            result = io.BytesIO()
            result.write(n_slices.to_bytes(4, byteorder='big'))
            for encoded in encoded_slices:
                result.write(len(encoded).to_bytes(4, byteorder='big'))
                result.write(encoded)
            
            return CPUBuffer.from_bytes(result.getvalue())
        
        # Handle 2D or 3D with shape[0] == 1
        if a16.ndim == 3 and a16.shape[0] == 1:
            a16 = a16[0]
        
        # Shift 12-bit data to 8-bit range for JPEG-LS
        shifted = (a16 >> 4).astype(np.uint8, copy=False)
        
        # Ensure contiguous array
        if not shifted.flags.c_contiguous:
            shifted = np.ascontiguousarray(shifted)

        # Pre-allocate output buffer (JPEG-LS encoder needs this for larger images)
        out_buffer = np.empty(shifted.size, dtype=np.uint8)

        if self.near_lossless is not None:
            encoded = None
            for key in ("near_lossless", "near"):
                try:
                    encoded = _JPEGLS_ENC(shifted, out=out_buffer, **{key: int(self.near_lossless)})  # type: ignore[misc]
                    break
                except (TypeError, ValueError):
                    encoded = None
            if encoded is None:
                try:
                    encoded = _JPEGLS_ENC(shifted, out=out_buffer)  # type: ignore[misc]
                except (TypeError, ValueError):
                    encoded = _JPEGLS_ENC(shifted)  # type: ignore[misc]
        else:
            try:
                encoded = _JPEGLS_ENC(shifted, out=out_buffer)  # type: ignore[misc]
            except (TypeError, ValueError):
                encoded = _JPEGLS_ENC(shifted)  # type: ignore[misc]

        # Wrap as Buffer using the array's buffer prototype
        return CPUBuffer.from_bytes(encoded)

    async def _decode_single(self, encoded, array_spec: ArraySpec):
        # bytes (Buffer) -> array
        if hasattr(encoded, "to_bytes"):  # Buffer
            encoded = encoded.to_bytes()
        
        want_shape = tuple(array_spec.shape)
        
        # Check if this is a multi-slice encoded chunk (has n_slices header)
        if len(encoded) >= 4 and len(want_shape) == 3 and want_shape[0] > 1:
            try:
                import struct
                n_slices = struct.unpack('>I', encoded[:4])[0]
                if n_slices == want_shape[0]:
                    # Multi-slice format: decode each slice
                    offset = 4
                    decoded_slices = []
                    for i in range(n_slices):
                        if offset + 4 > len(encoded):
                            break
                        slice_len = struct.unpack('>I', encoded[offset:offset+4])[0]
                        offset += 4
                        if offset + slice_len > len(encoded):
                            break
                        slice_encoded = encoded[offset:offset+slice_len]
                        offset += slice_len
                        
                        slice_decoded = _JPEGLS_DEC(slice_encoded)
                        if slice_decoded.dtype != np.uint8:
                            slice_decoded = slice_decoded.astype(np.uint8, copy=False)
                        slice_16bit = (slice_decoded.astype(np.uint16) << 4).astype(np.uint16, copy=False)
                        decoded_slices.append(slice_16bit)
                    
                    if len(decoded_slices) == n_slices:
                        # Stack slices back into 3D array
                        out = np.stack(decoded_slices, axis=0)
                        if tuple(out.shape) != want_shape:
                            out = np.ascontiguousarray(out).reshape(want_shape, order="C")
                        return out
            except Exception:
                # Fall through to single-slice decoding
                pass
        
        # Single-slice decoding
        out = _JPEGLS_DEC(encoded)
        if out.dtype != np.uint8:
            out = out.astype(np.uint8, copy=False)
        out = (out.astype(np.uint16) << 4).astype(np.uint16, copy=False)

        # Ensure shape matches spec (re-add leading singleton if needed)
        if len(want_shape) == 3 and want_shape[0] == 1 and out.ndim == 2:
            out = out.reshape(want_shape[1:], order="C")
            out = out[np.newaxis, :, :]
        elif tuple(out.shape) != want_shape:
            out = np.ascontiguousarray(out).reshape(want_shape, order="C")
        return out
