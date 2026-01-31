from .pyavif_ext import Decoder, BatchDecoder, DecoderCodec

try:
    from .pyavif_ext import Encoder, EncoderCodec
except ImportError:
    Encoder = None
    EncoderCodec = None

try:
    from .pyavif_ext import EncoderOptions, Range, PixelFormat, HeaderFormat
except ImportError:
    EncoderOptions = None
    Range = None
    PixelFormat = None
    HeaderFormat = None


try:
    from .pyavif_ext import BatchEncoder
except ImportError:
    BatchEncoder = None

__all__ = ["Decoder", "BatchDecoder", "DecoderCodec", "to_torch"]
if Encoder is not None:
    __all__.append("Encoder")
if EncoderCodec is not None:
    __all__.append("EncoderCodec")
if EncoderOptions is not None:
    __all__.append("EncoderOptions")
if BatchEncoder is not None:
    __all__.append("BatchEncoder")
if Range is not None:
    __all__.append("Range")
if PixelFormat is not None:
    __all__.append("PixelFormat")
if HeaderFormat is not None:
    __all__.append("HeaderFormat")

def to_torch(array, *, layout: str = "channels_last", pin_memory: bool = False):
    """
    Zero-copy convert a NumPy array (HxWxC, uint8/uint16) to a CPU torch.Tensor.

    layout:
      - "channels_last" (default): returns a tensor with shape HxWxC.
      - "chw": returns a tensor with shape CxHxW (uses a view with permuted strides; may be non-contiguous).

    pin_memory:
      - If True, pin the CPU tensor's memory (this creates a pinned copy).
    """
    import torch
    t = torch.from_numpy(array)  # zero-copy view (CPU)
    if layout == "chw":
        # This creates a view with permuted strides (no copy).
        t = t.permute(2, 0, 1)
    elif layout != "channels_last":
        raise ValueError("layout must be 'channels_last' or 'chw'")
    if pin_memory:
        t = t.pin_memory()  # this will allocate pinned memory (copy)
    return t
