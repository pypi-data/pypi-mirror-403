"""Shift12JLS compressor for Zarr v3 (BytesBytesCodec).

This compressor works on bytes (after Zarr serializes the array) and supports
incremental chunk updates, unlike the ArrayBytesCodec serializer version.
"""

from __future__ import annotations
from zarr.core.buffer.cpu import Buffer as CPUBuffer
from typing import Any, Dict, Optional, Tuple
import numpy as np
import imagecodecs as ic

from zarr.abc.codec import BytesBytesCodec
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


class Shift12JLSCompressor(BytesBytesCodec):
    """
    Shift12JLS compressor for uint16 arrays (12-bit fluorescent data).
    
    This is a BytesBytesCodec compressor that works on bytes, allowing
    incremental chunk updates (unlike ArrayBytesCodec serializers).
    
    - encode: bytes (serialized array) -> JPEG-LS-compressed bytes
    - decode: JPEG-LS-compressed bytes -> bytes (serialized array)
    
    The codec encodes 12-bit data shifted up to 16-bit using JPEG-LS:
    - encode: Extract 12-bit values (uint16 >> 4) and encode as uint16 with JPEG-LS
    - decode: Decode JPEG-LS to uint16, then shift back up (uint16 << 4)
    
    JPEG-LS supports 16-bit data directly, so we can encode the full 12-bit range (0-4095)
    without needing to split into bytes or convert to uint8.
    
    Parameters
    ----------
    near_lossless: Optional[int]
        Near-lossless parameter for JPEG-LS (0-255). None uses default.
    """
    
    codec_id = "cft_zarr.shift12jls_compressor"
    
    def __init__(self, *, near_lossless: Optional[int] = None):
        if _JPEGLS_ENC is None or _JPEGLS_DEC is None:
            raise ImportError(
                "imagecodecs JPEG-LS functions not found. "
                "Install imagecodecs with JPEG-LS enabled."
            )
        self.near_lossless = near_lossless
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Shift12JLSCompressor":
        cfg = (data.get("configuration") or {})
        return cls(**cfg)
    
    def validate(self, *, shape, dtype, chunk_grid) -> None:
        if not _is_uint16_dtype(dtype):
            raise TypeError("Shift12JLSCompressor only supports uint16 arrays")
        # Accept 2D (H,W) or 3D (Z,H,W) (any Z; codec runs per-chunk)
        if len(shape) == 2:
            return
        if len(shape) == 3:
            return
        raise TypeError(f"Unsupported shape for Shift12JLSCompressor: {shape}")
    
    def resolve_metadata(self, array_spec: ArraySpec) -> ArraySpec:
        return array_spec
    
    def to_dict(self) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        if self.near_lossless is not None:
            cfg["near_lossless"] = int(self.near_lossless)
        return {"id": self.codec_id, "name": self.codec_id, "configuration": cfg}
    
    async def _encode_single(self, chunk, array_spec: ArraySpec):
        """
        Encode bytes (serialized array) to JPEG-LS-compressed bytes.
        
        Args:
            chunk: Bytes (from Zarr's default serialization of the array)
            array_spec: ArraySpec with shape and dtype information
        
        Returns:
            JPEG-LS-compressed bytes
        """
        # Convert bytes to array using ArraySpec
        want_shape = tuple(array_spec.shape)
        # Zarr dtype objects need special handling - for Shift12JLS we always expect uint16
        want_dtype = np.uint16
        want_elems = int(np.prod(want_shape, dtype=np.int64))
        
        if hasattr(chunk, "to_bytes"):
            chunk_bytes = chunk.to_bytes()
        elif isinstance(chunk, (bytes, bytearray, memoryview)):
            chunk_bytes = bytes(chunk)
        else:
            chunk_bytes = bytes(chunk)
        
        # Reshape bytes into array
        arr = np.frombuffer(chunk_bytes, dtype=want_dtype)
        if arr.size < want_elems:
            raise ValueError(f"Insufficient bytes: have {arr.size}, need {want_elems}")
        if arr.size != want_elems:
            arr = arr[:want_elems]
        arr = arr.reshape(want_shape, order="C")
        
        # Ensure uint16
        if arr.dtype != np.uint16:
            arr = arr.astype(np.uint16, copy=False)
        
        # Handle 3D chunks - encode each slice separately
        if arr.ndim == 3:
            n_slices = arr.shape[0]
            encoded_slices = []
            
            for slice_idx in range(n_slices):
                slice_data = arr[slice_idx]
                
                # Extract 12-bit values from 16-bit data (shift down by 4 bits)
                # This gives us 0-4095 range, which fits in uint16
                values_12bit = (slice_data >> 4).astype(np.uint16, copy=False)
                
                # Ensure contiguous
                if not values_12bit.flags.c_contiguous:
                    values_12bit = np.ascontiguousarray(values_12bit)
                
                # Pre-allocate output buffer - JPEG-LS can expand data
                # Use uint8 buffer for encoded output (JPEG-LS outputs bytes)
                out_buffer = np.empty(values_12bit.size * 4, dtype=np.uint8)
                
                # Encode with JPEG-LS (supports uint16 directly)
                if self.near_lossless is not None:
                    encoded = None
                    for key in ("near_lossless", "near"):
                        try:
                            encoded = _JPEGLS_ENC(values_12bit, out=out_buffer, **{key: int(self.near_lossless)})
                            break
                        except (TypeError, ValueError):
                            encoded = None
                    if encoded is None:
                        try:
                            encoded = _JPEGLS_ENC(values_12bit, out=out_buffer)
                        except (TypeError, ValueError):
                            # If buffer is still too small, try without buffer (let it allocate)
                            encoded = _JPEGLS_ENC(values_12bit)
                else:
                    try:
                        encoded = _JPEGLS_ENC(values_12bit, out=out_buffer)
                    except (TypeError, ValueError):
                        # If buffer is still too small, try without buffer (let it allocate)
                        encoded = _JPEGLS_ENC(values_12bit)
                
                encoded_slices.append(encoded)
            
            # Combine all encoded slices: [n_slices (4 bytes)][slice_0_len (4 bytes)][slice_0_data]...
            import io
            result = io.BytesIO()
            result.write(n_slices.to_bytes(4, byteorder='big'))
            for encoded in encoded_slices:
                result.write(len(encoded).to_bytes(4, byteorder='big'))
                result.write(encoded)
            
            return CPUBuffer.from_bytes(result.getvalue())
        
        # Handle 2D or 3D with shape[0] == 1
        if arr.ndim == 3 and arr.shape[0] == 1:
            arr = arr[0]
        
        # Extract 12-bit values from 16-bit data (shift down by 4 bits)
        # This gives us 0-4095 range, which fits in uint16
        values_12bit = (arr >> 4).astype(np.uint16, copy=False)
        
        # Ensure contiguous
        if not values_12bit.flags.c_contiguous:
            values_12bit = np.ascontiguousarray(values_12bit)
        
        # Pre-allocate output buffer - JPEG-LS can expand data
        # Use uint8 buffer for encoded output (JPEG-LS outputs bytes)
        out_buffer = np.empty(values_12bit.size * 4, dtype=np.uint8)
        
        # Encode with JPEG-LS (supports uint16 directly)
        if self.near_lossless is not None:
            encoded = None
            for key in ("near_lossless", "near"):
                try:
                    encoded = _JPEGLS_ENC(values_12bit, out=out_buffer, **{key: int(self.near_lossless)})
                    break
                except (TypeError, ValueError):
                    encoded = None
            if encoded is None:
                try:
                    encoded = _JPEGLS_ENC(values_12bit, out=out_buffer)
                except (TypeError, ValueError):
                    # If buffer is still too small, try without buffer (let it allocate)
                    encoded = _JPEGLS_ENC(values_12bit)
        else:
            try:
                encoded = _JPEGLS_ENC(values_12bit, out=out_buffer)
            except (TypeError, ValueError):
                # If buffer is still too small, try without buffer (let it allocate)
                encoded = _JPEGLS_ENC(values_12bit)
        
        return CPUBuffer.from_bytes(encoded)
    
    async def _decode_single(self, encoded, array_spec: ArraySpec):
        """
        Decode JPEG-LS-compressed bytes back to bytes (serialized array).
        
        Args:
            encoded: JPEG-LS-compressed bytes
            array_spec: ArraySpec with shape and dtype information
        
        Returns:
            Bytes (serialized array) for Zarr to deserialize
        """
        if hasattr(encoded, "to_bytes"):
            encoded = encoded.to_bytes()
        elif isinstance(encoded, (bytes, bytearray, memoryview)):
            encoded = bytes(encoded)
        else:
            encoded = bytes(encoded)
        
        want_shape = tuple(array_spec.shape)
        # Zarr dtype objects need special handling - for Shift12JLS we always expect uint16
        want_dtype = np.uint16
        
        # Check if this is a multi-slice encoded chunk FIRST
        # Multi-slice format: [n_slices (4 bytes)][slice_0_len (4 bytes)][slice_0_data][slice_1_len (4 bytes)][slice_1_data]...
        # This check must come before any zero-filled checks, because multi-slice format starts with n_slices
        if len(encoded) >= 4:
            import struct
            try:
                n_slices = struct.unpack('>I', encoded[:4])[0]
                if n_slices > 0 and n_slices <= 100:  # Reasonable limit
                    # Multi-slice chunk - decode each slice
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
                        
                        try:
                            slice_decoded = _JPEGLS_DEC(slice_encoded)
                            slice_decoded = np.asarray(slice_decoded, dtype=np.uint16)
                            
                            # Shift back up to 16-bit range (12-bit value << 4)
                            slice_decoded = slice_decoded << 4
                            
                            decoded_slices.append(slice_decoded)
                        except Exception:
                            # On error, use zeros
                            decoded_slices.append(np.zeros(want_shape[1:], dtype=np.uint16))
                    
                    if len(decoded_slices) == n_slices:
                        # Stack slices back into 3D array
                        decoded = np.stack(decoded_slices, axis=0)
                        if tuple(decoded.shape) != want_shape:
                            decoded = np.ascontiguousarray(decoded).reshape(want_shape, order="C")
                        # Convert back to bytes
                        return CPUBuffer.from_bytes(decoded.tobytes())
            except Exception:
                pass  # Fall through to single-slice decoding
        
        # Single-slice decoding
        try:
            decoded = _JPEGLS_DEC(encoded)
            decoded = np.asarray(decoded, dtype=np.uint16)
            
            # Shift back up to 16-bit range (12-bit value << 4)
            decoded = decoded << 4
            
            # Ensure correct shape
            if decoded.ndim == 2 and len(want_shape) == 3:
                # 2D -> add Z dimension
                decoded = decoded[np.newaxis, :, :]
            
            if tuple(decoded.shape) != want_shape:
                decoded = np.ascontiguousarray(decoded).reshape(want_shape, order="C")
            
            if decoded.dtype != want_dtype:
                decoded = decoded.astype(want_dtype, copy=False)
            
            # Convert back to bytes
            return CPUBuffer.from_bytes(decoded.tobytes())
        
        except Exception:
            # On any error, return zeros
            arr = np.zeros(want_shape, dtype=want_dtype)
            return CPUBuffer.from_bytes(arr.tobytes())

