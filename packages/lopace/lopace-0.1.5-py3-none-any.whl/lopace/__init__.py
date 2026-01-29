"""
LoPace - Lossless Optimized Prompt Accurate Compression Engine

A professional Python package for compressing and decompressing prompts
using multiple techniques: Zstd, Token-based (BPE), and Hybrid methods.
"""

from .compressor import PromptCompressor, CompressionMethod

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0.dev0+unknown"

__all__ = ["PromptCompressor", "CompressionMethod"]