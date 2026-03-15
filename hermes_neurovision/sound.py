"""Sound system for hermes-neurovision.

Tier 1 (everywhere): curses.beep(), curses.flash()
Tier 2 (macOS only): afplay, say via subprocess

Zero external dependencies.
"""
from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SoundCue:
    """A sound that can be triggered by events."""
    name: str
    type: str        # 'bell', 'flash', 'say', 'file'
    value: str = ''  # text for say, path for file
    volume: float = 0.5  # 0.0-1.0
    priority: int = 0    # higher = override lower sounds


class SoundEngine:
    """Manages sound output. Pure stdlib + optional macOS."""
    
    def __init__(self, enabled: bool = True, volume: float = 0.5) -> None:
        self._enabled = enabled
        self._is_macos = sys.platform == 'darwin'
        self._volume = max(0.0, min(1.0, volume))
        self._last_played: Dict[str, float] = {}  # cooldowns
        self._min_interval = 0.5  # minimum seconds between same sound
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
    
    @property
    def volume(self) -> float:
        return self._volume
    
    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))
    
    def play(self, cue: SoundCue) -> bool:
        """Play a sound cue. Returns True if played, False if skipped."""
        if not self._enabled:
            return False
        
        # Cooldown check
        now = time.time()
        last = self._last_played.get(cue.name, 0.0)
        if now - last < self._min_interval:
            return False
        self._last_played[cue.name] = now
        
        try:
            if cue.type == 'bell':
                self._play_bell()
            elif cue.type == 'flash':
                self._play_flash()
            elif cue.type == 'say' and self._is_macos:
                self._play_say(cue.value)
            elif cue.type == 'file' and self._is_macos:
                self._play_file(cue.value, cue.volume)
            else:
                return False
            return True
        except Exception:
            return False
    
    def _play_bell(self) -> None:
        import curses
        try:
            curses.beep()
        except curses.error:
            # Fallback: raw BEL character
            sys.stdout.write('\a')
            sys.stdout.flush()
    
    def _play_flash(self) -> None:
        import curses
        try:
            curses.flash()
        except curses.error:
            pass
    
    def _play_say(self, text: str) -> None:
        """macOS text-to-speech (fire-and-forget)."""
        if not text:
            return
        subprocess.Popen(
            ['say', '-v', 'Whisper', text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    
    def _play_file(self, path: str, volume: float = 0.5) -> None:
        """macOS audio file playback (fire-and-forget)."""
        if not path:
            return
        final_vol = volume * self._volume
        subprocess.Popen(
            ['afplay', '-v', str(final_vol), path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    
    def play_for_event(self, event_kind: str, sound_cues: Dict[str, SoundCue]) -> bool:
        """Look up and play a sound cue for an event kind."""
        cue = sound_cues.get(event_kind)
        if cue is None:
            return False
        return self.play(cue)
