"""MP3 encoding for audio recordings."""

from __future__ import annotations

import re
import sys
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Try to import lameenc, provide helpful error if not available
try:
    import lameenc
    LAMEENC_AVAILABLE = True
except ImportError:
    LAMEENC_AVAILABLE = False
    lameenc = None


def _check_lameenc():
    """Check if lameenc is available, raise helpful error if not."""
    if not LAMEENC_AVAILABLE:
        print("\n" + "=" * 60, file=sys.stderr)
        print("ERROR: MP3 encoding requires the 'lame' library", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("\nTo fix this, run:", file=sys.stderr)
        print("\n    brew install lame", file=sys.stderr)
        print("\nThen reinstall meeting-noter:", file=sys.stderr)
        print("\n    pip install --force-reinstall meeting-noter", file=sys.stderr)
        print("\n" + "=" * 60 + "\n", file=sys.stderr)
        raise ImportError(
            "lameenc not available. Install LAME first: brew install lame"
        )


def _sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize a string for use as a filename.

    Args:
        name: The name to sanitize
        max_length: Maximum length for the sanitized name

    Returns:
        A safe filename string with spaces replaced by underscores
    """
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Remove any character that isn't alphanumeric, underscore, or hyphen
    name = re.sub(r"[^\w\-]", "", name)
    # Truncate to max length
    if len(name) > max_length:
        name = name[:max_length]
    # Remove trailing underscores/hyphens
    name = name.rstrip("_-")
    return name


def _is_timestamp_name(name: str) -> bool:
    """Check if name is a default timestamp pattern (DD_Mon_YYYY_HHMM)."""
    return bool(re.match(r"^\d{2}_[A-Z][a-z]{2}_\d{4}_\d{4}$", name))


class MP3Encoder:
    """Encodes audio data to MP3 format."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        bitrate: int = 128,
        quality: int = 2,
    ):
        _check_lameenc()
        self.sample_rate = sample_rate
        self.channels = channels
        self.encoder = lameenc.Encoder()
        self.encoder.set_bit_rate(bitrate)
        self.encoder.set_in_sample_rate(sample_rate)
        self.encoder.set_channels(channels)
        self.encoder.set_quality(quality)  # 2 = high quality
        self._buffer = bytearray()

    def encode_chunk(self, audio: np.ndarray) -> bytes:
        """Encode a chunk of audio data.

        Args:
            audio: Float32 audio data, values between -1 and 1

        Returns:
            MP3 encoded bytes
        """
        # Convert float32 to int16
        int_data = (audio * 32767).astype(np.int16)
        mp3_data = self.encoder.encode(int_data.tobytes())
        return mp3_data

    def finalize(self) -> bytes:
        """Finalize encoding and return remaining data."""
        return self.encoder.flush()


class RecordingSession:
    """Manages a single recording session (one meeting)."""

    def __init__(
        self,
        output_dir: Path,
        sample_rate: int = 16000,
        channels: int = 1,
        meeting_name: Optional[str] = None,
    ):
        self.output_dir = output_dir
        self.sample_rate = sample_rate
        self.channels = channels
        self.meeting_name = meeting_name
        self.encoder: Optional[MP3Encoder] = None
        self.file_handle = None
        self.filepath: Optional[Path] = None
        self.start_time: Optional[datetime] = None
        self.total_samples = 0

    def start(self) -> Path:
        """Start a new recording session."""
        self.start_time = datetime.now()

        if self.meeting_name:
            sanitized = _sanitize_filename(self.meeting_name)
            if _is_timestamp_name(self.meeting_name):
                # Default timestamp name - use as-is without extra prefix
                filename = f"{sanitized}.mp3"
            else:
                # Custom name - add timestamp prefix for uniqueness
                timestamp = self.start_time.strftime("%Y-%m-%d_%H%M%S")
                filename = f"{timestamp}_{sanitized}.mp3"
        else:
            timestamp = self.start_time.strftime("%Y-%m-%d_%H%M%S")
            filename = f"{timestamp}.mp3"
        self.filepath = self.output_dir / filename

        self.encoder = MP3Encoder(
            sample_rate=self.sample_rate,
            channels=self.channels,
        )
        self.file_handle = open(self.filepath, "wb")
        self.total_samples = 0

        return self.filepath

    def write(self, audio: np.ndarray):
        """Write audio data to the recording."""
        if self.encoder is None or self.file_handle is None:
            raise RuntimeError("Recording session not started")

        mp3_data = self.encoder.encode_chunk(audio)
        if mp3_data:
            self.file_handle.write(mp3_data)
        self.total_samples += len(audio)

    def stop(self) -> Tuple[Optional[Path], float]:
        """Stop the recording session.

        Returns:
            Tuple of (filepath, duration_seconds)
        """
        duration = 0.0
        filepath = self.filepath

        if self.encoder and self.file_handle:
            # Write final data
            final_data = self.encoder.finalize()
            if final_data:
                self.file_handle.write(final_data)
            self.file_handle.close()

            duration = self.total_samples / self.sample_rate

            # Delete if too short (less than 5 seconds)
            if duration < 5.0 and filepath and filepath.exists():
                filepath.unlink()
                filepath = None

        self.encoder = None
        self.file_handle = None
        self.filepath = None
        self.start_time = None
        self.total_samples = 0

        return filepath, duration

    @property
    def is_active(self) -> bool:
        """Check if a recording is in progress."""
        return self.encoder is not None

    @property
    def duration(self) -> float:
        """Get current recording duration in seconds."""
        if self.sample_rate > 0:
            return self.total_samples / self.sample_rate
        return 0.0
