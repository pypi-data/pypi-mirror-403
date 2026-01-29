"""Chunked JPEG codec for RGB images in Zarr v3.

This codec handles RGB images in chunks of N slices (default: 4) with JPEG compression,
optimizing for spatial locality and efficient storage of photographic images.
"""

import io
import numpy as np
from typing import Any, Dict, Optional

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from numcodecs import Codec
    from numcodecs.registry import register_codec
except ImportError:
    # Fallback for Zarr v3 direct codec interface
    Codec = object
    register_codec = lambda *args, **kwargs: None


class ChunkedJPEGCodec(Codec):
    """Codec for RGB images using chunked JPEG compression.
    
    Encodes N×512×512×3 numpy arrays (RGB images) as JPEG-compressed bytes.
    Default chunk shape is (4, 512, 512, 3) but is configurable.
    
    Configuration:
        quality: JPEG quality (0-100, default: 85)
        chunk_shape: Tuple of (N, height, width, channels) or (N, height, width) for grayscale
                    Default: (4, 512, 512, 3) for RGB, (4, 512, 512) for grayscale
    """
    
    codec_id = "cft_zarr.chunked_jpeg"
    
    def __init__(
        self,
        quality: int = 85,
        chunk_shape: Optional[tuple] = None,
    ):
        """Initialize chunked JPEG codec.
        
        Args:
            quality: JPEG quality (0-100), default 85
            chunk_shape: Chunk shape tuple, default (4, 512, 512, 3) for RGB
        """
        self.quality = max(0, min(100, quality))
        self.chunk_shape = chunk_shape or (4, 512, 512, 3)
        
        # Validate chunk shape
        if len(self.chunk_shape) not in (3, 4):
            raise ValueError(f"chunk_shape must be 3D (grayscale) or 4D (RGB), got {len(self.chunk_shape)}D")
        
        self.is_rgb = len(self.chunk_shape) == 4
        if self.is_rgb:
            self.n_slices, self.height, self.width, self.channels = self.chunk_shape
        else:
            self.n_slices, self.height, self.width = self.chunk_shape
            self.channels = 1
    
    def encode(self, buf: np.ndarray) -> bytes:
        """Encode numpy array to JPEG-compressed bytes.
        
        Args:
            buf: Numpy array of shape (N, height, width, 3) or (N, height, width)
            
        Returns:
            Compressed bytes containing JPEG-encoded slices
        """
        if not CV2_AVAILABLE:
            raise ImportError("cv2 is required for chunked JPEG codec")
        
        if not isinstance(buf, np.ndarray):
            buf = np.asarray(buf)
        
        # Validate shape
        expected_shape = self.chunk_shape
        if buf.shape != expected_shape:
            # Handle partial chunks (last chunk may have fewer slices)
            if buf.shape[1:] == expected_shape[1:]:
                # Same spatial dimensions, just fewer slices
                pass
            else:
                raise ValueError(
                    f"Expected shape {expected_shape}, got {buf.shape}. "
                    "Partial chunks (fewer slices) are allowed, but spatial dimensions must match."
                )
        
        # Convert to uint8 if needed
        if buf.dtype != np.uint8:
            buf = buf.astype(np.uint8)
        
        # Encode each slice as JPEG using cv2
        jpeg_bytes_list = []
        n_slices = buf.shape[0]
        
        # JPEG encoding parameters for cv2
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality, cv2.IMWRITE_JPEG_OPTIMIZE, 1]
        
        for i in range(n_slices):
            slice_data = buf[i]
            
            # Handle RGB vs grayscale
            if self.is_rgb:
                # RGB: shape is (height, width, 3)
                if slice_data.shape != (self.height, self.width, 3):
                    # Resize if needed
                    slice_data = cv2.resize(slice_data, (self.width, self.height), interpolation=cv2.INTER_LANCZOS4)
                # cv2.imencode expects BGR for color images
                slice_data_bgr = cv2.cvtColor(slice_data, cv2.COLOR_RGB2BGR)
            else:
                # Grayscale: shape is (height, width)
                if slice_data.shape != (self.height, self.width):
                    slice_data = cv2.resize(slice_data, (self.width, self.height), interpolation=cv2.INTER_LANCZOS4)
                slice_data_bgr = slice_data
            
            # Encode as JPEG using cv2
            success, jpeg_bytes = cv2.imencode('.jpg', slice_data_bgr, encode_params)
            if not success:
                raise RuntimeError(f"Failed to encode slice {i} as JPEG")
            
            jpeg_bytes_list.append(jpeg_bytes.tobytes())
        
        # Combine all JPEG bytes with a simple format:
        # [n_slices (4 bytes)][slice_0_len (4 bytes)][slice_0_data][slice_1_len (4 bytes)][slice_1_data]...
        result = io.BytesIO()
        result.write(n_slices.to_bytes(4, byteorder='big'))
        for jpeg_bytes in jpeg_bytes_list:
            result.write(len(jpeg_bytes).to_bytes(4, byteorder='big'))
            result.write(jpeg_bytes)
        
        return result.getvalue()
    
    def decode(self, buf: bytes, out: Optional[np.ndarray] = None) -> np.ndarray:
        """Decode JPEG-compressed bytes to numpy array.
        
        Args:
            buf: Compressed bytes containing JPEG-encoded slices
            out: Optional output array (not used, but required by Codec interface)
            
        Returns:
            Numpy array of shape (N, height, width, 3) or (N, height, width)
        """
        if not CV2_AVAILABLE:
            raise ImportError("cv2 is required for chunked JPEG codec")
        
        buffer = io.BytesIO(buf)
        
        # Read number of slices
        n_slices_bytes = buffer.read(4)
        if len(n_slices_bytes) < 4:
            raise ValueError("Invalid chunked JPEG format: missing slice count")
        n_slices = int.from_bytes(n_slices_bytes, byteorder='big')
        
        # Decode each slice
        slices = []
        for i in range(n_slices):
            # Read slice length
            len_bytes = buffer.read(4)
            if len(len_bytes) < 4:
                raise ValueError(f"Invalid chunked JPEG format: missing length for slice {i}")
            slice_len = int.from_bytes(len_bytes, byteorder='big')
            
            # Read slice data
            slice_bytes = buffer.read(slice_len)
            if len(slice_bytes) < slice_len:
                raise ValueError(f"Invalid chunked JPEG format: incomplete data for slice {i}")
            
            # Decode JPEG using cv2
            slice_data = cv2.imdecode(np.frombuffer(slice_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if slice_data is None:
                raise RuntimeError(f"Failed to decode JPEG slice {i}")
            
            # Convert BGR to RGB if needed
            if self.is_rgb and slice_data.ndim == 3:
                slice_data = cv2.cvtColor(slice_data, cv2.COLOR_BGR2RGB)
            
            # Ensure correct shape
            if self.is_rgb:
                if slice_data.shape != (self.height, self.width, 3):
                    slice_data = cv2.resize(slice_data, (self.width, self.height), interpolation=cv2.INTER_LANCZOS4)
            else:
                if slice_data.shape != (self.height, self.width):
                    slice_data = cv2.resize(slice_data, (self.width, self.height), interpolation=cv2.INTER_LANCZOS4)
            
            slices.append(slice_data.astype(np.uint8))
        
        # Stack slices
        result = np.stack(slices, axis=0)
        
        # Pad to expected chunk shape if needed (for partial chunks)
        if result.shape[0] < self.n_slices:
            if self.is_rgb:
                padding_shape = (self.n_slices - result.shape[0], self.height, self.width, 3)
            else:
                padding_shape = (self.n_slices - result.shape[0], self.height, self.width)
            padding = np.zeros(padding_shape, dtype=np.uint8)
            result = np.concatenate([result, padding], axis=0)
        
        return result
    
    def get_config(self) -> Dict[str, Any]:
        """Get codec configuration."""
        return {
            "id": self.codec_id,
            "quality": self.quality,
            "chunk_shape": list(self.chunk_shape),
        }
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ChunkedJPEGCodec":
        """Create codec from configuration."""
        quality = config.get("quality", 85)
        chunk_shape = config.get("chunk_shape")
        if chunk_shape:
            chunk_shape = tuple(chunk_shape)
        return cls(quality=quality, chunk_shape=chunk_shape)


# Register codec with numcodecs (for Zarr v2 compatibility)
try:
    register_codec(ChunkedJPEGCodec)
except Exception:
    pass
