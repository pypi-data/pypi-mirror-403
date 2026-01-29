"""
rustpdf-compress - A fast PDF compression library written in Rust.

Usage:
    >>> import rustpdf_compress
    >>>
    >>> # Compress from bytes
    >>> with open("input.pdf", "rb") as f:
    ...     data = f.read()
    >>> compressed = rustpdf_compress.compress(data, level="recommended")
    >>> with open("output.pdf", "wb") as f:
    ...     f.write(compressed)
    >>>
    >>> # Or compress file directly
    >>> original_size, compressed_size, reduction = rustpdf_compress.compress_file(
    ...     "input.pdf", "output.pdf", level="recommended"
    ... )
    >>> print(f"Reduced by {reduction:.1f}%")

Compression levels:
    - "extreme": Maximum compression (30% image quality, 50% scale)
    - "recommended": Balanced compression (60% image quality, 75% scale)
    - "low": High quality (85% image quality, no scaling)
"""

from .rustpdf_compress import compress, compress_file, __version__

__all__ = ["compress", "compress_file", "__version__"]
