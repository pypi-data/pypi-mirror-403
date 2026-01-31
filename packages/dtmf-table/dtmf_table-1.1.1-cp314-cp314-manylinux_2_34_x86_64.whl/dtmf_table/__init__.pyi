# Stubs for dtmf_table (generated from Rust bindings)
"""DTMF (Dual-Tone Multi-Frequency) frequency table for telephony applications.

This library provides efficient, const-first mappings between DTMF keys and their
canonical frequency pairs. Built with Rust for performance, it offers both exact
lookups and tolerance-based matching for real-world audio analysis.
"""

from typing import Any, Optional

__version__: str
__doc__: str

# DTMF frequency constants
LOWS: tuple[int, int, int, int]
"""Low-band DTMF frequencies in Hz: (697, 770, 852, 941)"""

HIGHS: tuple[int, int, int, int]
"""High-band DTMF frequencies in Hz: (1209, 1336, 1477, 1633)"""

class DtmfKey:
    """A DTMF (Dual-Tone Multi-Frequency) key representing telephony keypad buttons.

    Represents one of the 16 standard DTMF keys used in telephony systems:
    - Digits 0-9
    - Special characters * and #
    - Letters A-D (extended keypad)

    Each key corresponds to a unique pair of low and high frequency tones.
    """

    @staticmethod
    def from_char(c: str) -> "DtmfKey":
        """Create a DtmfKey from a character.

        # Arguments
        c: Single character representing the DTMF key ('0'-'9', '*', '#', 'A'-'D')

        # Returns
        The corresponding DTMF key

        # Errors
        ValueError: If the character is not a valid DTMF key
        """
        ...

    def to_char(self) -> str:
        """Convert the DtmfKey to its character representation.

        # Returns
        Single character representing the key
        """
        ...

    def freqs(self) -> tuple[int, int]:
        """Get the canonical frequencies for this DTMF key.

        # Returns
        Tuple of (low_frequency_hz, high_frequency_hz)
        """
        ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...

class DtmfTone:
    """A DTMF tone containing a key and its associated frequency pair.

    Represents the complete information for a DTMF signal:
    the key character and its corresponding low and high frequencies.
    This is useful for iterating over all possible tones or when you need
    both the key and frequency information together.
    """

    def __init__(self, key: DtmfKey, low_hz: int, high_hz: int) -> None:
        """Create a new DtmfTone.

        # Arguments
        key: The DTMF key
        low_hz: Low frequency in Hz
        high_hz: High frequency in Hz
        """
        ...

    @property
    def key(self) -> DtmfKey:
        """The DTMF key for this tone."""
        ...

    @property
    def low_hz(self) -> int:
        """Low frequency in Hz."""
        ...

    @property
    def high_hz(self) -> int:
        """High frequency in Hz."""
        ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: Any) -> bool: ...

class DtmfTable:
    """DTMF frequency lookup table for audio processing applications.

    Provides efficient bidirectional mapping between DTMF keys and their
    canonical frequency pairs. Supports exact lookups, tolerance-based matching
    for real-world audio analysis, and frequency snapping for noisy estimates.

    The table contains all 16 standard DTMF frequencies used in telephony:

              1209 Hz  1336 Hz  1477 Hz  1633 Hz
    697 Hz:      1        2        3        A
    770 Hz:      4        5        6        B
    852 Hz:      7        8        9        C
    941 Hz:      *        0        #        D
    """

    def __init__(self) -> None:
        """Create a new DTMF table instance."""
        ...

    @staticmethod
    def all_keys() -> list[DtmfKey]:
        """Get all DTMF keys in keypad order.

        # Returns
        List of all 16 DTMF keys
        """
        ...

    @staticmethod
    def all_tones() -> list[DtmfTone]:
        """Get all DTMF tones in keypad order.

        # Returns
        List of all 16 DTMF tones
        """
        ...

    @staticmethod
    def all_keys_matrix() -> list[list[DtmfKey]]:
        """Get all DTMF keys as a 4x4 matrix.

        # Returns
        4x4 matrix of DtmfKeys in keypad layout
        """
        ...

    @staticmethod
    def all_tones_matrix() -> list[list[DtmfTone]]:
        """Get all DTMF tones as a 4x4 matrix.

        # Returns
        4x4 matrix of DtmfTones in keypad layout
        """
        ...

    @staticmethod
    def lookup_key(key: DtmfKey) -> tuple[int, int]:
        """Look up frequencies for a given key.

        # Arguments
        key: The DTMF key to look up

        # Returns
        Tuple of (low_frequency_hz, high_frequency_hz)
        """
        ...

    @staticmethod
    def from_pair_exact(low: int, high: int) -> Optional[DtmfKey]:
        """Find DTMF key from exact frequency pair.

        # Arguments
        low: Low frequency in Hz
        high: High frequency in Hz

        # Returns
        The matching key, or None if no exact match
        """
        ...

    @staticmethod
    def from_pair_normalised(a: int, b: int) -> Optional[DtmfKey]:
        """Find DTMF key from frequency pair with automatic order normalization.

        # Arguments
        a: First frequency in Hz
        b: Second frequency in Hz

        # Returns
        The matching key, or None if no exact match
        """
        ...

    def from_pair_tol_u32(self, low: int, high: int, tol_hz: int) -> Optional[DtmfKey]:
        """Find DTMF key from frequency pair with tolerance (integer version).

        # Arguments
        low: Low frequency in Hz
        high: High frequency in Hz
        tol_hz: Tolerance in Hz

        # Returns
        The matching key within tolerance, or None
        """
        ...

    def from_pair_tol_f64(
        self, low: float, high: float, tol_hz: float
    ) -> Optional[DtmfKey]:
        """Find DTMF key from frequency pair with tolerance (float version).

        # Arguments
        low: Low frequency in Hz
        high: High frequency in Hz
        tol_hz: Tolerance in Hz

        # Returns
        The matching key within tolerance, or None
        """
        ...

    def nearest_u32(self, low: int, high: int) -> tuple[DtmfKey, int, int]:
        """Find the nearest DTMF key and snap frequencies to canonical values (integer version).

        # Arguments
        low: Low frequency estimate in Hz
        high: High frequency estimate in Hz

        # Returns
        Tuple of (key, snapped_low_hz, snapped_high_hz)
        """
        ...

    def nearest_f64(self, low: float, high: float) -> tuple[DtmfKey, int, int]:
        """Find the nearest DTMF key and snap frequencies to canonical values (float version).

        # Arguments
        low: Low frequency estimate in Hz
        high: High frequency estimate in Hz

        # Returns
        Tuple of (key, snapped_low_hz, snapped_high_hz)
        """
        ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
