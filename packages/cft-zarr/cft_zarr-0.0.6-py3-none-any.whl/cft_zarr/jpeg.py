from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
import imagecodecs as ic
from imagecodecs import Jpeg8Error

from zarr.abc.codec import ArrayBytesCodec
from zarr.core.array_spec import ArraySpec
from zarr.core.buffer.cpu import Buffer as CPUBuffer


def _force_uint8_array(buf, spec: ArraySpec) -> np.ndarray:
    """Coerce input to C-contiguous uint8 with shape == spec.shape."""
    want_shape = tuple(spec.shape)
    if isinstance(buf, (bytes, bytearray, memoryview)):
        arr = np.frombuffer(buf, dtype=np.uint8)
        want_elems = int(np.prod(want_shape, dtype=np.int64))
        if arr.size < want_elems:
            raise ValueError(f"Insufficient bytes: have {arr.size}, need {want_elems}")
        if arr.size != want_elems:
            arr = arr[:want_elems]
        arr = arr.reshape(want_shape, order="C")
        return arr if arr.flags.c_contiguous else np.ascontiguousarray(arr)

    if hasattr(buf, "as_numpy_array"):
        arr = np.asarray(buf.as_numpy_array())
    else:
        arr = np.asarray(buf)

    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8, copy=False)
    if tuple(arr.shape) != want_shape:
        arr = np.ascontiguousarray(arr).reshape(want_shape, order="C")
    return arr if arr.flags.c_contiguous else np.ascontiguousarray(arr)


class JPEGCodec(ArrayBytesCodec):
    """
    JPEG serializer for uint8 arrays (2D grayscale or 3-channel RGB).

    - encode: ndarray -> JPEG bytes
    - decode: JPEG bytes -> ndarray

    Parameters
    ----------
    level: int
        JPEG quality (1-100). Default 85.
    subsampling: Optional[int]
        0 (4:4:4), 1 (4:2:2), 2 (4:2:0). Default None uses imagecodecs default.
    """

    codec_id = "cft_zarr.jpeg"

    def __init__(self, *, level: int = 85, subsampling: Optional[int] = None):
        if not hasattr(ic, "jpeg_encode") or not hasattr(ic, "jpeg_decode"):
            raise ImportError("imagecodecs missing JPEG support (jpeg_encode/decode)")
        self.level = int(level)
        self.subsampling = subsampling

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JPEGCodec":
        cfg = (data.get("configuration") or {})
        return cls(**cfg)

    def validate(self, *, shape, dtype, chunk_grid) -> None:
        # Accept uint8 grayscale or RGB; allow Z dimension (any length)
        try:
            dt = np.dtype(dtype)
        except TypeError:
            s = str(dtype).lower()
            if 'uint8' in s:
                dt = np.uint8
            else:
                raise TypeError(f"JPEGCodec only supports uint8 arrays (got {dtype})")
        if dt != np.uint8:
            raise TypeError("JPEGCodec only supports uint8 arrays")
        if len(shape) == 2:
            return
        if len(shape) == 3 and shape[-1] in (1, 3):
            return
        if len(shape) == 4 and shape[-1] in (1, 3):
            return
        raise TypeError(f"Unsupported shape for JPEGCodec: {shape}")

    def resolve_metadata(self, array_spec: ArraySpec) -> ArraySpec:
        return array_spec

    # Ensure Zarr can persist this codec in zarr.json
    def to_dict(self) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {"level": int(self.level)}
        if self.subsampling is not None:
            cfg["subsampling"] = int(self.subsampling)
        # Use fully-qualified id for both id and name so reopen resolves by id
        return {"id": self.codec_id, "name": self.codec_id, "configuration": cfg}

    async def _encode_single(self, chunk, array_spec: ArraySpec):
        arr = _force_uint8_array(chunk, array_spec)
        
        # Handle 4D chunks by encoding each slice separately
        if arr.ndim == 4 and arr.shape[0] > 1:
            # Multiple slices in chunk - encode each slice separately
            import io
            n_slices = arr.shape[0]
            encoded_slices = []
            
            kwargs: Dict[str, Any] = {"level": self.level}
            if self.subsampling is not None:
                kwargs["subsampling"] = int(self.subsampling)
            
            for i in range(n_slices):
                slice_3d = arr[i]  # Shape: (height, width, channels)
                
                # Check if slice is all zeros (fill_value)
                if np.all(slice_3d == 0):
                    # Zero-filled slice - encode as minimal JPEG for zero slices
                    zero_img = np.zeros((1, 1, 3), dtype=np.uint8)
                    encoded = ic.jpeg_encode(zero_img, **kwargs)
                    encoded_slices.append(encoded)
                else:
                    try:
                        encoded = ic.jpeg_encode(slice_3d, **kwargs)
                        encoded_slices.append(encoded)
                    except Exception as e:
                        # Encoding failed, try with minimal JPEG
                        import warnings
                        warnings.warn(f"JPEG encoding failed for slice {i}: {e}")
                        zero_img = np.zeros((1, 1, 3), dtype=np.uint8)
                        encoded = ic.jpeg_encode(zero_img, **kwargs)
                        encoded_slices.append(encoded)
            
            # Combine all encoded slices: [n_slices (4 bytes)][slice_0_len (4 bytes)][slice_0_data]...
            result = io.BytesIO()
            result.write(n_slices.to_bytes(4, byteorder='big'))
            for encoded in encoded_slices:
                result.write(len(encoded).to_bytes(4, byteorder='big'))
                result.write(encoded)
            
            return CPUBuffer.from_bytes(result.getvalue())
        
        # Handle 2D/3D or 4D with shape[0] == 1
        if arr.ndim == 4 and arr.shape[0] == 1:
            arr = arr[0]
        
        kwargs: Dict[str, Any] = {"level": self.level}
        if self.subsampling is not None:
            kwargs["subsampling"] = int(self.subsampling)
        
        # Check if the single slice is all zeros
        if np.all(arr == 0):
            zero_img = np.zeros((1, 1, 3), dtype=np.uint8)
            encoded = ic.jpeg_encode(zero_img, **kwargs)
        else:
            encoded = ic.jpeg_encode(arr, **kwargs)
        return CPUBuffer.from_bytes(encoded)

    async def _decode_single(self, encoded, array_spec: ArraySpec):
        if hasattr(encoded, "to_bytes"):
            encoded = encoded.to_bytes()
        
        want = tuple(array_spec.shape)
        
        # Early check for zero-filled or invalid data - catch before any processing
        try:
            if len(encoded) < 2:
                # Too small to be valid JPEG
                if len(want) == 4:
                    return np.zeros(want, dtype=np.uint8)
                elif len(want) == 3:
                    return np.zeros(want, dtype=np.uint8)
                else:
                    return np.zeros(want, dtype=np.uint8)
            
            # Check for zero-filled data (starts with 0x00 0x00)
            if encoded[:2] == b'\x00\x00':
                # Zero-filled data - return zeros
                if len(want) == 4:
                    return np.zeros(want, dtype=np.uint8)
                elif len(want) == 3:
                    return np.zeros(want, dtype=np.uint8)
                else:
                    return np.zeros(want, dtype=np.uint8)
            
            # Check for valid JPEG header (starts with 0xFF 0xD8)
            if len(encoded) < 10 or encoded[:2] != b'\xff\xd8':
                # Not a valid JPEG - might be corrupted
                # Return zeros matching expected shape
                if len(want) == 4:
                    return np.zeros(want, dtype=np.uint8)
                elif len(want) == 3:
                    return np.zeros(want, dtype=np.uint8)
                else:
                    return np.zeros(want, dtype=np.uint8)
        except Exception as early_e:
            # If any check fails, return zeros
            if len(want) == 4:
                return np.zeros(want, dtype=np.uint8)
            elif len(want) == 3:
                return np.zeros(want, dtype=np.uint8)
            else:
                return np.zeros(want, dtype=np.uint8)
        
        # Check if this is a multi-slice encoded chunk (has n_slices header)
        # Try multi-slice format if:
        # 1. We have at least 4 bytes (for n_slices header)
        # 2. Array shape is 4D with multiple slices
        # 3. The first 4 bytes represent a reasonable slice count
        if len(encoded) >= 4 and len(want) == 4 and want[0] > 1:
            try:
                import struct
                n_slices = struct.unpack('>I', encoded[:4])[0]
                # Validate: n_slices should match want[0] and be reasonable (1-1000)
                if n_slices == want[0] and 1 <= n_slices <= 1000:
                    # Multi-slice format: decode each slice
                    offset = 4
                    decoded_slices = []
                    for i in range(n_slices):
                        if offset + 4 > len(encoded):
                            # Missing length header, create zero-filled slice
                            h, w, c = want[1], want[2], want[3]
                            decoded_slices.append(np.zeros((h, w, c), dtype=np.uint8))
                            break
                        slice_len = struct.unpack('>I', encoded[offset:offset+4])[0]
                        offset += 4
                        
                        if slice_len == 0:
                            # Zero-length slice (all zeros), create zero-filled slice
                            h, w, c = want[1], want[2], want[3]
                            decoded_slices.append(np.zeros((h, w, c), dtype=np.uint8))
                            continue
                        
                        if offset + slice_len > len(encoded):
                            # Incomplete data, create zero-filled slice
                            h, w, c = want[1], want[2], want[3]
                            decoded_slices.append(np.zeros((h, w, c), dtype=np.uint8))
                            break
                        
                        slice_encoded = encoded[offset:offset+slice_len]
                        offset += slice_len
                        
                        # Check if slice is all zeros or invalid JPEG header
                        # Valid JPEG starts with 0xFF 0xD8 and has minimum size
                        # Also check for zero-filled data (0x00 0x00) or very small data
                        is_valid_jpeg = (
                            len(slice_encoded) >= 10 and  # Minimum JPEG size
                            len(slice_encoded) >= 2 and 
                            slice_encoded[:2] == b'\xff\xd8' and
                            slice_encoded[:2] != b'\x00\x00'  # Not zero-filled
                        )
                        
                        if not is_valid_jpeg:
                            # Not a valid JPEG (likely zero-filled or corrupted), create zero-filled slice
                            h, w, c = want[1], want[2], want[3]
                            decoded_slices.append(np.zeros((h, w, c), dtype=np.uint8))
                            continue
                        
                        try:
                            slice_decoded = ic.jpeg_decode(slice_encoded)
                            slice_decoded = np.asarray(slice_decoded)
                            if slice_decoded.dtype != np.uint8:
                                slice_decoded = slice_decoded.astype(np.uint8, copy=False)
                            
                            # Ensure shape matches expected
                            expected_shape = (want[1], want[2], want[3])
                            if slice_decoded.shape != expected_shape:
                                # Reshape if needed
                                if slice_decoded.size == np.prod(expected_shape):
                                    slice_decoded = slice_decoded.reshape(expected_shape, order='C')
                                else:
                                    # Size mismatch, create zero-filled slice
                                    decoded_slices.append(np.zeros(expected_shape, dtype=np.uint8))
                                    continue
                            
                            decoded_slices.append(slice_decoded)
                        except (Jpeg8Error, ValueError, Exception) as e:
                            # Decode failed (e.g., "Not a JPEG file: starts with 0x00 0x00")
                            # Create zero-filled slice instead
                            import warnings
                            warnings.warn(f"JPEG decode failed for slice {i} in multi-slice chunk: {e}. Using zero-filled slice.")
                            h, w, c = want[1], want[2], want[3]
                            decoded_slices.append(np.zeros((h, w, c), dtype=np.uint8))
                    
                    if len(decoded_slices) == n_slices:
                        # Stack slices back into 4D array
                        out = np.stack(decoded_slices, axis=0)
                        if tuple(out.shape) != want:
                            out = np.ascontiguousarray(out).reshape(want, order="C")
                        return out
            except Exception as e:
                # Multi-slice decode failed, try single-slice decoding
                # But first check if this might be multi-slice format that failed
                if len(encoded) >= 4:
                    import struct
                    try:
                        n_slices = struct.unpack('>I', encoded[:4])[0]
                        # If it looks like multi-slice format but decode failed,
                        # this chunk might be corrupted - return zeros
                        if 1 <= n_slices <= 1000 and len(want) == 4:
                            h, w, c = want[1], want[2], want[3]
                            return np.zeros((n_slices, h, w, c), dtype=np.uint8)
                    except Exception:
                        pass
                # Fall through to single-slice decoding
                pass
        
        # Single-slice decoding
        # Check if this looks like invalid/corrupted/zero-filled data
        # Valid JPEG starts with 0xFF 0xD8, zero-filled data starts with 0x00 0x00
        if len(encoded) < 2:
            # Too small to be valid JPEG
            if len(want) == 4:
                return np.zeros(want, dtype=np.uint8)
            elif len(want) == 3:
                return np.zeros(want, dtype=np.uint8)
            else:
                return np.zeros(want, dtype=np.uint8)
        
        # Check for zero-filled data (starts with 0x00 0x00)
        if encoded[:2] == b'\x00\x00':
            # Zero-filled data - return zeros
            if len(want) == 4:
                return np.zeros(want, dtype=np.uint8)
            elif len(want) == 3:
                return np.zeros(want, dtype=np.uint8)
            else:
                return np.zeros(want, dtype=np.uint8)
        
        # Check for valid JPEG header (starts with 0xFF 0xD8)
        if len(encoded) < 10 or encoded[:2] != b'\xff\xd8':
            # Not a valid JPEG - might be corrupted
            # Return zeros matching expected shape
            if len(want) == 4:
                return np.zeros(want, dtype=np.uint8)
            elif len(want) == 3:
                return np.zeros(want, dtype=np.uint8)
            else:
                return np.zeros(want, dtype=np.uint8)
        
        try:
            out = ic.jpeg_decode(encoded)
            out = np.asarray(out)
            if out.dtype != np.uint8:
                out = out.astype(np.uint8, copy=False)
        except (Jpeg8Error, ValueError, Exception) as e:
            # Decode failed (e.g., "Not a JPEG file: starts with 0x00 0x00")
            # Return zeros matching expected shape
            import warnings
            warnings.warn(f"JPEG decode failed in single-slice path: {e}. Using zero-filled array.")
            if len(want) == 4:
                return np.zeros(want, dtype=np.uint8)
            elif len(want) == 3:
                return np.zeros(want, dtype=np.uint8)
            else:
                return np.zeros(want, dtype=np.uint8)
        
        if len(want) == 4 and want[0] == 1 and out.ndim in (2, 3):
            # Expand back to (1,H,W[,C])
            out = np.ascontiguousarray(out)
            if out.ndim == 2:
                out = out[np.newaxis, :, :]
            else:
                out = out[np.newaxis, :, :, :]
        elif tuple(out.shape) != want:
            out = np.ascontiguousarray(out).reshape(want, order="C")
        return out


