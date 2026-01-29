"""Execute song-schema JSON files in Ableton Live with proper timing."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from abletonosc_client import AbletonOSCClient, Song, Scene


@dataclass
class SectionTiming:
    """Timing information for a song section."""
    name: str
    scene_index: int
    start_beat: float
    duration_beats: float
    bars: int


class SongExecutor:
    """Execute a song-schema JSON file in Ableton Live.

    Reads structure.sections from a song.json and fires scenes
    with proper timing to record into arrangement view.
    """

    def __init__(
        self,
        song_path: str,
        client: Optional[AbletonOSCClient] = None,
        receive_port: int = 11001
    ):
        """Initialize with a song JSON file.

        Args:
            song_path: Path to the song.json file
            client: Optional AbletonOSCClient instance (creates one if not provided)
            receive_port: OSC receive port (default 11001, use different if MCP is running)
        """
        self.song_path = Path(song_path)
        self._client = client
        self._receive_port = receive_port
        self._song_data = None
        self._timings: list[SectionTiming] = []

    @property
    def client(self) -> AbletonOSCClient:
        """Lazy-load the OSC client."""
        if self._client is None:
            self._client = AbletonOSCClient(receive_port=self._receive_port)
        return self._client

    @property
    def song(self) -> Song:
        """Get Song controller for Ableton."""
        return Song(self.client)

    @property
    def scene(self) -> Scene:
        """Get Scene controller for Ableton."""
        return Scene(self.client)

    def load(self) -> dict:
        """Load the song JSON file."""
        with open(self.song_path) as f:
            self._song_data = json.load(f)
        self._calculate_timings()
        return self._song_data

    @property
    def tempo(self) -> float:
        """Get the song tempo in BPM."""
        return self._song_data.get("metadata", {}).get("tempo", 120)

    @property
    def time_signature(self) -> tuple[int, int]:
        """Get the time signature as (numerator, denominator)."""
        ts = self._song_data.get("metadata", {}).get("time_signature", {})
        return (ts.get("numerator", 4), ts.get("denominator", 4))

    @property
    def beats_per_bar(self) -> int:
        """Calculate beats per bar from time signature."""
        num, denom = self.time_signature
        # Standard beats per bar calculation
        # 4/4 = 4 beats, 3/4 = 3 beats, 6/8 = 6 beats
        return num

    @property
    def sections(self) -> list[dict]:
        """Get the structure sections."""
        return self._song_data.get("structure", {}).get("sections", [])

    @property
    def total_bars(self) -> int:
        """Calculate total bars in the song."""
        return sum(s.get("bars", 4) for s in self.sections)

    @property
    def total_beats(self) -> float:
        """Calculate total beats in the song."""
        return self.total_bars * self.beats_per_bar

    @property
    def total_duration_seconds(self) -> float:
        """Calculate total duration in seconds."""
        return self.total_beats * (60.0 / self.tempo)

    def _calculate_timings(self) -> None:
        """Calculate timing for each section."""
        self._timings = []
        current_beat = 0.0

        for i, section in enumerate(self.sections):
            bars = section.get("bars", 4)
            duration_beats = bars * self.beats_per_bar

            timing = SectionTiming(
                name=section.get("name", f"section_{i}"),
                scene_index=i,
                start_beat=current_beat,
                duration_beats=duration_beats,
                bars=bars
            )
            self._timings.append(timing)
            current_beat += duration_beats

    def beat_to_seconds(self, beat: float) -> float:
        """Convert beats to seconds at current tempo."""
        return beat * (60.0 / self.tempo)

    def get_timing(self, scene_index: int) -> Optional[SectionTiming]:
        """Get timing for a specific scene."""
        if 0 <= scene_index < len(self._timings):
            return self._timings[scene_index]
        return None

    def print_structure(self) -> None:
        """Print the song structure with timing information."""
        print(f"\n{'='*60}")
        print(f"Song: {self.song_path.name}")
        print(f"Tempo: {self.tempo} BPM")
        print(f"Time Signature: {self.time_signature[0]}/{self.time_signature[1]}")
        print(f"Total: {self.total_bars} bars = {self.total_beats} beats = {self.total_duration_seconds:.1f} seconds")
        print(f"{'='*60}\n")

        print(f"{'Scene':<8} {'Section':<15} {'Bars':<6} {'Beats':<8} {'Start (s)':<10} {'Duration (s)':<12}")
        print("-" * 60)

        for timing in self._timings:
            start_sec = self.beat_to_seconds(timing.start_beat)
            dur_sec = self.beat_to_seconds(timing.duration_beats)
            print(f"{timing.scene_index:<8} {timing.name:<15} {timing.bars:<6} {timing.duration_beats:<8.0f} {start_sec:<10.1f} {dur_sec:<12.1f}")

        print()

    def execute(self, record: bool = True, dry_run: bool = False) -> None:
        """Execute the song by firing scenes with proper timing.

        Args:
            record: Whether to enable recording to arrangement view
            dry_run: If True, just print what would happen without executing
        """
        if not self._song_data:
            self.load()

        self.print_structure()

        if dry_run:
            print("[DRY RUN] Would execute the following:")
            for timing in self._timings:
                wait_time = self.beat_to_seconds(timing.duration_beats)
                print(f"  - Fire scene {timing.scene_index} ({timing.name}), wait {wait_time:.1f}s")
            print(f"  - Stop playback")
            return

        # Set tempo and time signature
        print(f"Setting tempo to {self.tempo} BPM...")
        self.song.set_tempo(self.tempo)

        ts_num, ts_denom = self.time_signature
        print(f"Setting time signature to {ts_num}/{ts_denom}...")
        self.song.set_signature_numerator(ts_num)
        self.song.set_signature_denominator(ts_denom)

        # Position at start
        print("Positioning at beat 0...")
        self.song.set_current_song_time(0)

        # Enable recording if requested
        if record:
            print("Enabling arrangement recording...")
            self.song.set_record_mode(True)

        # Execute each section
        print("\nStarting playback...")
        for i, timing in enumerate(self._timings):
            wait_time = self.beat_to_seconds(timing.duration_beats)

            print(f"  [{i+1}/{len(self._timings)}] Firing scene {timing.scene_index} ({timing.name})...")
            self.scene.fire(timing.scene_index)

            # Start playback on first scene
            if i == 0:
                time.sleep(0.1)  # Small delay for scene to register
                self.song.start_playing()

            print(f"      Waiting {wait_time:.1f}s ({timing.bars} bars)...")
            time.sleep(wait_time)

        # Stop playback
        print("\nStopping playback...")
        self.song.stop_playing()

        if record:
            print("Disabling record mode...")
            self.song.set_record_mode(False)

        print(f"\nExecution complete! Total duration: {self.total_duration_seconds:.1f}s")

    def execute_section(self, section_name: str) -> None:
        """Execute a single section by name.

        Args:
            section_name: Name of the section to execute
        """
        if not self._song_data:
            self.load()

        timing = None
        for t in self._timings:
            if t.name == section_name:
                timing = t
                break

        if not timing:
            available = [t.name for t in self._timings]
            raise ValueError(f"Section '{section_name}' not found. Available: {available}")

        wait_time = self.beat_to_seconds(timing.duration_beats)

        print(f"Firing scene {timing.scene_index} ({timing.name})...")
        self.scene.fire(timing.scene_index)
        self.song.start_playing()

        print(f"Playing for {wait_time:.1f}s ({timing.bars} bars)...")
        time.sleep(wait_time)

        self.song.stop_playing()
        print("Done.")
