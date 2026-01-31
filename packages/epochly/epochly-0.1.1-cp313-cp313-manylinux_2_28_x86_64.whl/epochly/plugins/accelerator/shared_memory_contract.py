"""
Shared Memory Contract (SPEC2 Task 16).

Defines shared memory layout for cross-language plugins.
"""

import struct
import logging
from typing import Optional, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class DataType(Enum):
    """Supported data types for shared memory."""
    INT32 = "i"
    INT64 = "q"
    FLOAT32 = "f"
    FLOAT64 = "d"
    BYTES = "bytes"  # Special handling required


@dataclass
class BufferLayout:
    """
    Shared memory buffer layout descriptor.

    Defines the structure of data in shared memory.
    """
    data_type: DataType
    element_count: int
    byte_offset: int = 0

    @property
    def element_size(self) -> int:
        """Get size of single element in bytes."""
        if self.data_type == DataType.BYTES:
            return 1  # Bytes are counted individually
        return struct.calcsize(self.data_type.value)

    @property
    def total_size(self) -> int:
        """Get total size in bytes."""
        return self.element_size * self.element_count

    def validate_size(self, buffer_size: int) -> bool:
        """
        Validate buffer size is sufficient.

        Args:
            buffer_size: Size of buffer in bytes

        Returns:
            True if buffer is large enough
        """
        required_size = self.byte_offset + self.total_size
        return buffer_size >= required_size


class SharedMemoryContract:
    """
    Shared memory contract for cross-language plugins.

    Enforces ABI compatibility and provides safe read/write.
    """

    HEADER_SIZE = 64  # Bytes reserved for header
    MAGIC_NUMBER = 0x45504F43  # "EPOC" in hex
    VERSION = 1

    def __init__(self, buffer_size: int):
        """
        Initialize shared memory contract.

        Args:
            buffer_size: Total buffer size in bytes
        """
        self.buffer_size = buffer_size
        self._layouts: dict = {}
        self._validated = False

    def add_layout(self, name: str, layout: BufferLayout) -> None:
        """
        Add a buffer layout definition.

        Args:
            name: Layout identifier
            layout: BufferLayout instance
        """
        if not layout.validate_size(self.buffer_size):
            raise ValueError(
                f"Layout '{name}' requires {layout.total_size} bytes "
                f"but buffer only has {self.buffer_size}"
            )

        self._layouts[name] = layout

    def write_header(self, buffer: memoryview) -> None:
        """
        Write contract header to buffer.

        Header format:
        - Magic number (4 bytes)
        - Version (4 bytes)
        - Layout count (4 bytes)
        - Reserved (52 bytes)

        Args:
            buffer: Memory buffer to write to
        """
        if len(buffer) < self.HEADER_SIZE:
            raise ValueError("Buffer too small for header")

        # Pack header
        header_data = struct.pack(
            '<III52x',  # Little-endian, 3 ints, 52 bytes padding
            self.MAGIC_NUMBER,
            self.VERSION,
            len(self._layouts)
        )

        buffer[:self.HEADER_SIZE] = header_data

    def validate_header(self, buffer: memoryview) -> bool:
        """
        Validate contract header.

        Args:
            buffer: Memory buffer to validate

        Returns:
            True if header is valid
        """
        if len(buffer) < self.HEADER_SIZE:
            logger.error("Buffer too small for header")
            return False

        # Unpack header
        try:
            magic, version, layout_count = struct.unpack('<III', buffer[:12])

            if magic != self.MAGIC_NUMBER:
                logger.error(f"Invalid magic number: {magic:08x} != {self.MAGIC_NUMBER:08x}")
                return False

            if version != self.VERSION:
                logger.error(f"Version mismatch: {version} != {self.VERSION}")
                return False

            if layout_count != len(self._layouts):
                logger.error(f"Layout count mismatch: {layout_count} != {len(self._layouts)}")
                return False

            self._validated = True
            return True

        except struct.error as e:
            logger.error(f"Header parsing error: {e}")
            return False

    def write_data(self, buffer: memoryview, layout_name: str, data: Any) -> bool:
        """
        Write data to buffer according to layout.

        Args:
            buffer: Memory buffer
            layout_name: Name of layout to use
            data: Data to write (list, single value, or bytes for BYTES type)

        Returns:
            True if write successful
        """
        if layout_name not in self._layouts:
            raise ValueError(f"Unknown layout: {layout_name}")

        layout = self._layouts[layout_name]
        start_offset = self.HEADER_SIZE + layout.byte_offset

        # Special handling for BYTES
        if layout.data_type == DataType.BYTES:
            if not isinstance(data, (bytes, bytearray, memoryview)):
                raise TypeError(f"BYTES layout requires bytes, got {type(data)}")

            if len(data) > layout.element_count:
                raise ValueError(
                    f"Data length {len(data)} exceeds layout capacity {layout.element_count}"
                )

            # Pack as fixed-size bytes with padding
            format_str = f'<{layout.element_count}s'
            padded_data = bytes(data).ljust(layout.element_count, b'\x00')
            packed_data = struct.pack(format_str, padded_data)

            end_offset = start_offset + len(packed_data)
            buffer[start_offset:end_offset] = packed_data
            return True

        # Convert single value to list for numeric types
        if not isinstance(data, (list, tuple)):
            data = [data]

        if len(data) > layout.element_count:
            raise ValueError(
                f"Data length {len(data)} exceeds layout capacity {layout.element_count}"
            )

        # Pack data
        try:
            format_str = '<' + (layout.data_type.value * len(data))
            packed_data = struct.pack(format_str, *data)

            end_offset = start_offset + len(packed_data)
            buffer[start_offset:end_offset] = packed_data

            return True

        except struct.error as e:
            logger.error(f"Data packing error: {e}")
            return False

    def read_data(self, buffer: memoryview, layout_name: str) -> Optional[Any]:
        """
        Read data from buffer according to layout.

        Args:
            buffer: Memory buffer
            layout_name: Name of layout to use

        Returns:
            Unpacked data or None on error
        """
        if layout_name not in self._layouts:
            raise ValueError(f"Unknown layout: {layout_name}")

        layout = self._layouts[layout_name]
        start_offset = self.HEADER_SIZE + layout.byte_offset
        end_offset = start_offset + layout.total_size

        # Special handling for BYTES
        if layout.data_type == DataType.BYTES:
            try:
                format_str = f'<{layout.element_count}s'
                raw = struct.unpack(format_str, buffer[start_offset:end_offset])[0]
                # Strip null padding
                return raw.rstrip(b'\x00')
            except struct.error as e:
                logger.error(f"BYTES unpacking error: {e}")
                return None

        # Unpack data
        try:
            format_str = '<' + (layout.data_type.value * layout.element_count)
            data = struct.unpack(format_str, buffer[start_offset:end_offset])

            # Return single value if only one element
            if len(data) == 1:
                return data[0]

            return list(data)

        except struct.error as e:
            logger.error(f"Data unpacking error: {e}")
            return None
