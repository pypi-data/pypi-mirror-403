"""JPEG compressor for Zarr v3 (BytesBytesCodec).

This compressor works on bytes (after Zarr serializes the array) and supports
incremental chunk updates, unlike the ArrayBytesCodec serializer version.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import imagecodecs as ic
from imagecodecs import Jpeg8Error

from zarr.abc.codec import BytesBytesCodec
from zarr.core.array_spec import ArraySpec
from zarr.core.buffer.cpu import Buffer as CPUBuffer


class JPEGCompressor(BytesBytesCodec):
    """
    JPEG compressor for uint8 arrays (2D grayscale or 3-channel RGB).
    
    This is a BytesBytesCodec compressor that works on bytes, allowing
    incremental chunk updates (unlike ArrayBytesCodec serializers).
    
    - encode: bytes (serialized array) -> JPEG-compressed bytes
    - decode: JPEG-compressed bytes -> bytes (serialized array)
    
    Parameters
    ----------
    level: int
        JPEG quality (1-100). Default 85.
    subsampling: Optional[int]
        0 (4:4:4), 1 (4:2:2), 2 (4:2:0). Default None uses imagecodecs default.
    """
    
    codec_id = "cft_zarr.jpeg_compressor"
    
    def __init__(self, *, level: int = 85, subsampling: Optional[int] = None):
        if not hasattr(ic, "jpeg_encode") or not hasattr(ic, "jpeg_decode"):
            raise ImportError("imagecodecs missing JPEG support (jpeg_encode/decode)")
        self.level = int(level)
        self.subsampling = subsampling
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JPEGCompressor":
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
                raise TypeError(f"JPEGCompressor only supports uint8 arrays (got {dtype})")
        if dt != np.uint8:
            raise TypeError("JPEGCompressor only supports uint8 arrays")
        if len(shape) == 2:
            return
        if len(shape) == 3 and shape[-1] in (1, 3):
            return
        if len(shape) == 4 and shape[-1] in (1, 3):
            return
        raise TypeError(f"Unsupported shape for JPEGCompressor: {shape}")
    
    def resolve_metadata(self, array_spec: ArraySpec) -> ArraySpec:
        return array_spec
    
    def to_dict(self) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {"level": int(self.level)}
        if self.subsampling is not None:
            cfg["subsampling"] = int(self.subsampling)
        return {"id": self.codec_id, "name": self.codec_id, "configuration": cfg}
    
    async def _encode_single(self, chunk, array_spec: ArraySpec):
        """
        Encode bytes (serialized array) to JPEG-compressed bytes.
        
        Args:
            chunk: Bytes (from Zarr's default serialization of the array)
            array_spec: ArraySpec with shape and dtype information
        
        Returns:
            JPEG-compressed bytes
        """
        # Convert bytes to array using ArraySpec
        want_shape = tuple(array_spec.shape)
        # Zarr dtype objects need special handling - for JPEG we always expect uint8
        want_dtype = np.uint8
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
        
        # Ensure uint8
        if arr.dtype != np.uint8:
            arr = arr.astype(np.uint8, copy=False)
        
        # Handle 4D chunks (multiple slices) - encode each slice separately
        if arr.ndim == 4:
            n_slices = arr.shape[0]
            encoded_slices = []
            
            for slice_idx in range(n_slices):
                slice_data = arr[slice_idx]  # Get 3D slice (H, W, C)
                
                kwargs: Dict[str, Any] = {"level": self.level}
                if self.subsampling is not None:
                    kwargs["subsampling"] = int(self.subsampling)
                
                # Check if the slice is all zeros
                if np.all(slice_data == 0):
                    zero_img = np.zeros((1, 1, 3), dtype=np.uint8)
                    encoded = ic.jpeg_encode(zero_img, **kwargs)
                else:
                    encoded = ic.jpeg_encode(slice_data, **kwargs)
                
                encoded_slices.append(encoded)
            
            # Combine all encoded slices: [n_slices (4 bytes)][slice_0_len (4 bytes)][slice_0_data]...
            import io
            result = io.BytesIO()
            result.write(n_slices.to_bytes(4, byteorder='big'))
            for encoded in encoded_slices:
                result.write(len(encoded).to_bytes(4, byteorder='big'))
                result.write(encoded)
            
            return CPUBuffer.from_bytes(result.getvalue())
        
        # Handle 2D/3D (single slice or collapsed 4D)
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
        """
        Decode JPEG-compressed bytes back to bytes (serialized array).
        
        Args:
            encoded: JPEG-compressed bytes
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
        # Zarr dtype objects need special handling - for JPEG we always expect uint8
        want_dtype = np.uint8
        
        # Debug: log what we're trying to decode
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"JPEG decode: encoded_len={len(encoded)}, want_shape={want_shape}, encoded_header={encoded[:10].hex() if len(encoded) >= 10 else 'too_short'}")
        
        # Early check for zero-filled or invalid data
        try:
            if len(encoded) < 2:
                # Too small to be valid JPEG - return zeros
                arr = np.zeros(want_shape, dtype=want_dtype)
                return CPUBuffer.from_bytes(arr.tobytes())
            
            # Check if this is a multi-slice encoded chunk FIRST
            # Multi-slice format: [n_slices (4 bytes)][slice_0_len (4 bytes)][slice_0_data][slice_1_len (4 bytes)][slice_1_data]...
            # This check must come before the zero-filled check, because multi-slice format starts with n_slices (which could be 0x00000004 = \x00\x00\x00\x04)
            if len(encoded) >= 4:
                import struct
                try:
                    n_slices = struct.unpack('>I', encoded[:4])[0]
                    # Check if this looks like our multi-slice format
                    # n_slices should be reasonable (1-100) and the total size should make sense
                    if n_slices > 0 and n_slices <= 100:
                        # Verify it's our format by checking if we have enough bytes for headers
                        min_size = 4 + (n_slices * 4)  # header + all slice length headers
                        if len(encoded) >= min_size:
                            # This looks like our multi-slice format - process it
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.debug(f"JPEG decode: checking multi-slice format, n_slices={n_slices}, encoded_len={len(encoded)}")
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
                                    slice_decoded = ic.jpeg_decode(slice_encoded)
                                    slice_decoded = np.asarray(slice_decoded, dtype=np.uint8)
                                    
                                    # Ensure decoded slice matches expected shape
                                    # (zero-filled slices might be encoded as 1x1 JPEGs)
                                    if len(want_shape) == 4:
                                        expected_slice_shape = want_shape[1:]  # (H, W, C)
                                    else:
                                        expected_slice_shape = want_shape
                                    
                                    if tuple(slice_decoded.shape) != expected_slice_shape:
                                        # Resize to expected shape (e.g., 1x1 -> HxWxC for zero-filled slices)
                                        if slice_decoded.size == 1 or (slice_decoded.size == 3 and slice_decoded.ndim == 1):
                                            # Single pixel or minimal image - create zeros of expected shape
                                            slice_decoded = np.zeros(expected_slice_shape, dtype=np.uint8)
                                        elif slice_decoded.ndim == 3 and slice_decoded.shape[0] == 1 and slice_decoded.shape[1] == 1:
                                            # 1x1x3 image - expand to full size (all zeros)
                                            slice_decoded = np.zeros(expected_slice_shape, dtype=np.uint8)
                                        else:
                                            # Try to reshape (shouldn't happen normally)
                                            try:
                                                slice_decoded = np.ascontiguousarray(slice_decoded).reshape(expected_slice_shape, order="C")
                                            except ValueError:
                                                # Can't reshape - use zeros
                                                slice_decoded = np.zeros(expected_slice_shape, dtype=np.uint8)
                                    
                                    decoded_slices.append(slice_decoded)
                                except Exception as e:
                                    # On error, use zeros matching expected slice shape
                                    import logging
                                    logger = logging.getLogger(__name__)
                                    logger.debug(f"JPEG slice decode failed: {type(e).__name__}: {e}, slice_len={slice_len}, slice_header={slice_encoded[:10].hex() if len(slice_encoded) >= 10 else 'too_short'}")
                                    if len(want_shape) == 4:
                                        slice_shape = want_shape[1:]  # (H, W, C)
                                    else:
                                        slice_shape = want_shape
                                    decoded_slices.append(np.zeros(slice_shape, dtype=np.uint8))
                            
                            if len(decoded_slices) == n_slices:
                                # Stack slices back into 4D array
                                try:
                                    decoded = np.stack(decoded_slices, axis=0)
                                    import logging
                                    logger = logging.getLogger(__name__)
                                    logger.debug(f"JPEG multi-slice decode: stacked shape={decoded.shape}, want_shape={want_shape}, slice0_min/max={decoded[0].min()}/{decoded[0].max()}")
                                    if tuple(decoded.shape) != want_shape:
                                        decoded = np.ascontiguousarray(decoded).reshape(want_shape, order="C")
                                    # Convert back to bytes
                                    return CPUBuffer.from_bytes(decoded.tobytes())
                                except Exception as e:
                                    # Stacking failed - return zeros
                                    import logging
                                    logger = logging.getLogger(__name__)
                                    logger.debug(f"Failed to stack decoded slices: {type(e).__name__}: {e}, decoded_shapes={[s.shape for s in decoded_slices]}, want_shape={want_shape}")
                                    arr = np.zeros(want_shape, dtype=want_dtype)
                                    return CPUBuffer.from_bytes(arr.tobytes())
                            else:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.debug(f"JPEG multi-slice decode: only got {len(decoded_slices)}/{n_slices} slices, returning zeros")
                                arr = np.zeros(want_shape, dtype=want_dtype)
                                return CPUBuffer.from_bytes(arr.tobytes())
                except Exception as e:
                    # If multi-slice detection fails, fall through to single-slice decoding
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Multi-slice detection failed: {type(e).__name__}: {e}")
                    pass
            
            # Check for zero-filled data (starts with 0x00 0x00) - only if not multi-slice format
            if len(encoded) >= 2 and encoded[:2] == b'\x00\x00':
                arr = np.zeros(want_shape, dtype=want_dtype)
                return CPUBuffer.from_bytes(arr.tobytes())
            
            # Single-slice decoding
            # Check for valid JPEG header (starts with 0xFF 0xD8)
            if len(encoded) >= 2 and encoded[:2] == b'\xff\xd8':
                # Single JPEG - decode directly
                pass  # Continue to decode below
            else:
                # Not a valid JPEG and not multi-slice - return zeros
                arr = np.zeros(want_shape, dtype=want_dtype)
                return CPUBuffer.from_bytes(arr.tobytes())
                import struct
                try:
                    n_slices = struct.unpack('>I', encoded[:4])[0]
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"JPEG decode: checking multi-slice format, n_slices={n_slices}, encoded_len={len(encoded)}")
                    # Check if this looks like our multi-slice format
                    # n_slices should be reasonable (1-100) and the total size should make sense
                    if n_slices > 0 and n_slices <= 100:
                        # Verify it's our format by checking if we have enough bytes for headers
                        min_size = 4 + (n_slices * 4)  # header + all slice length headers
                        if len(encoded) >= min_size:
                            # Multi-slice chunk - decode each slice
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.debug(f"JPEG multi-slice decode: n_slices={n_slices}, want_shape={want_shape}, encoded_len={len(encoded)}")
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
                                    slice_decoded = ic.jpeg_decode(slice_encoded)
                                    slice_decoded = np.asarray(slice_decoded, dtype=np.uint8)
                                    
                                    # Ensure decoded slice matches expected shape
                                    # (zero-filled slices might be encoded as 1x1 JPEGs)
                                    if len(want_shape) == 4:
                                        expected_slice_shape = want_shape[1:]  # (H, W, C)
                                    else:
                                        expected_slice_shape = want_shape
                                    
                                    if tuple(slice_decoded.shape) != expected_slice_shape:
                                        # Resize to expected shape (e.g., 1x1 -> HxWxC for zero-filled slices)
                                        if slice_decoded.size == 1 or (slice_decoded.size == 3 and slice_decoded.ndim == 1):
                                            # Single pixel or minimal image - create zeros of expected shape
                                            slice_decoded = np.zeros(expected_slice_shape, dtype=np.uint8)
                                        elif slice_decoded.ndim == 3 and slice_decoded.shape[0] == 1 and slice_decoded.shape[1] == 1:
                                            # 1x1x3 image - expand to full size (all zeros)
                                            slice_decoded = np.zeros(expected_slice_shape, dtype=np.uint8)
                                        else:
                                            # Try to reshape (shouldn't happen normally)
                                            try:
                                                slice_decoded = np.ascontiguousarray(slice_decoded).reshape(expected_slice_shape, order="C")
                                            except ValueError:
                                                # Can't reshape - use zeros
                                                slice_decoded = np.zeros(expected_slice_shape, dtype=np.uint8)
                                    
                                    decoded_slices.append(slice_decoded)
                                except Exception as e:
                                    # On error, use zeros matching expected slice shape
                                    import logging
                                    logger = logging.getLogger(__name__)
                                    logger.debug(f"JPEG slice decode failed: {type(e).__name__}: {e}, slice_len={slice_len}, slice_header={slice_encoded[:10].hex() if len(slice_encoded) >= 10 else 'too_short'}")
                                    if len(want_shape) == 4:
                                        slice_shape = want_shape[1:]  # (H, W, C)
                                    else:
                                        slice_shape = want_shape
                                    decoded_slices.append(np.zeros(slice_shape, dtype=np.uint8))
                            
                            if len(decoded_slices) == n_slices:
                                # Stack slices back into 4D array
                                try:
                                    decoded = np.stack(decoded_slices, axis=0)
                                    import logging
                                    logger = logging.getLogger(__name__)
                                    logger.debug(f"JPEG multi-slice decode: stacked shape={decoded.shape}, want_shape={want_shape}, slice0_min/max={decoded[0].min()}/{decoded[0].max()}")
                                    if tuple(decoded.shape) != want_shape:
                                        decoded = np.ascontiguousarray(decoded).reshape(want_shape, order="C")
                                    # Convert back to bytes
                                    return CPUBuffer.from_bytes(decoded.tobytes())
                                except Exception as e:
                                    # Stacking failed - return zeros
                                    import logging
                                    logger = logging.getLogger(__name__)
                                    logger.debug(f"Failed to stack decoded slices: {type(e).__name__}: {e}, decoded_shapes={[s.shape for s in decoded_slices]}, want_shape={want_shape}")
                                    arr = np.zeros(want_shape, dtype=want_dtype)
                                    return CPUBuffer.from_bytes(arr.tobytes())
                            else:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.debug(f"JPEG multi-slice decode: only got {len(decoded_slices)}/{n_slices} slices, returning zeros")
                                arr = np.zeros(want_shape, dtype=want_dtype)
                                return CPUBuffer.from_bytes(arr.tobytes())
                except Exception as e:
                    # If multi-slice detection fails, fall through to single-slice decoding
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Multi-slice detection failed: {type(e).__name__}: {e}")
                    pass
            
            # Single-slice decoding
            # Check for valid JPEG header (starts with 0xFF 0xD8)
            if len(encoded) < 10 or encoded[:2] != b'\xff\xd8':
                # Not a valid JPEG - return zeros
                arr = np.zeros(want_shape, dtype=want_dtype)
                return CPUBuffer.from_bytes(arr.tobytes())
            
            # Decode JPEG
            try:
                decoded = ic.jpeg_decode(encoded)
            except (Jpeg8Error, Exception) as e:
                # Invalid JPEG or any error - return zeros
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"JPEG decode failed: {type(e).__name__}: {e}")
                arr = np.zeros(want_shape, dtype=want_dtype)
                return CPUBuffer.from_bytes(arr.tobytes())
            
            decoded = np.asarray(decoded)
            
            # Ensure correct shape and dtype
            # want_shape could be 2D, 3D, or 4D depending on the chunk
            if len(want_shape) == 4:
                # Expecting 4D: (N, H, W, C)
                if decoded.ndim == 3:
                    # Got 3D (H, W, C) - add Z dimension
                    decoded = decoded[np.newaxis, :, :, :]
                elif decoded.ndim == 2:
                    # Got 2D (H, W) - add Z and channel dimensions
                    decoded = decoded[np.newaxis, :, :, np.newaxis]
            elif len(want_shape) == 3:
                # Expecting 3D: (H, W, C)
                if decoded.ndim == 2:
                    # Got 2D (H, W) - add channel dimension
                    decoded = decoded[:, :, np.newaxis]
                elif decoded.ndim == 4 and decoded.shape[0] == 1:
                    # Got 4D with single slice - remove Z dimension
                    decoded = decoded[0]
            
            # Final shape check and reshape if needed
            if tuple(decoded.shape) != want_shape:
                try:
                    decoded = np.ascontiguousarray(decoded).reshape(want_shape, order="C")
                except ValueError:
                    # Shape mismatch - return zeros
                    arr = np.zeros(want_shape, dtype=want_dtype)
                    return CPUBuffer.from_bytes(arr.tobytes())
            
            if decoded.dtype != want_dtype:
                decoded = decoded.astype(want_dtype, copy=False)
            
            # Convert back to bytes (serialized array)
            return CPUBuffer.from_bytes(decoded.tobytes())
        
        except Exception as e:
            # On any error, return zeros
            arr = np.zeros(want_shape, dtype=want_dtype)
            return CPUBuffer.from_bytes(arr.tobytes())

