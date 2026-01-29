"""
mini-arcade native backend package.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

# --- 1) Make sure Windows can find SDL2.dll when using vcpkg ------------------

if sys.platform == "win32":
    # a) If running as a frozen PyInstaller exe (e.g. DejaBounce.exe),
    #    SDL2.dll will live next to the executable. Add that dir.
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        try:
            os.add_dll_directory(str(exe_dir))
        except (FileNotFoundError, OSError):
            # If this somehow fails, we still try other fallbacks.
            pass

    # b) Dev / vcpkg fallback: use VCPKG_ROOT if available.
    vcpkg_root = os.environ.get("VCPKG_ROOT")
    if vcpkg_root:
        # Typical vcpkg layout: <VCPKG_ROOT>/installed/x64-windows/bin/SDL2.dll
        sdl_bin = os.path.join(vcpkg_root, "installed", "x64-windows", "bin")
        if os.path.isdir(sdl_bin):
            try:
                os.add_dll_directory(sdl_bin)
            except (FileNotFoundError, OSError):
                pass

# --- 2) Now import native extension and core types ----------------------------

# Justification: Need to import core after setting DLL path on Windows
# pylint: disable=wrong-import-position
# Justification: When mini-arcade-core is installed in editable mode, import-error
# false positive can occur.
# pylint: disable=import-error
from mini_arcade_core.backend import (  # pyright: ignore[reportMissingImports]
    Backend,
    WindowSettings,
)
from mini_arcade_core.backend.events import (  # pyright: ignore[reportMissingImports]
    Event,
    EventType,
)
from mini_arcade_core.backend.sdl_map import (  # pyright: ignore[reportMissingImports]
    SDL_KEYCODE_TO_KEY,
)

# Justification: Importing the native extension module
# pylint: disable=import-self,no-name-in-module
from . import _native as native

# pylint: enable=import-error


# --- 2) Now import core + define NativeBackend as before ---


__all__ = ["NativeBackend", "native"]

Alpha = Union[float, int]

_NATIVE_TO_CORE = {
    native.EventType.Unknown: EventType.UNKNOWN,
    native.EventType.Quit: EventType.QUIT,
    native.EventType.KeyDown: EventType.KEYDOWN,
    native.EventType.KeyUp: EventType.KEYUP,
    native.EventType.MouseMotion: EventType.MOUSEMOTION,
    native.EventType.MouseButtonDown: EventType.MOUSEBUTTONDOWN,
    native.EventType.MouseButtonUp: EventType.MOUSEBUTTONUP,
    native.EventType.MouseWheel: EventType.MOUSEWHEEL,
    native.EventType.WindowResized: EventType.WINDOWRESIZED,
    native.EventType.TextInput: EventType.TEXTINPUT,
}


@dataclass
class BackendSettings:
    """
    Settings for the NativeBackend.

    :ivar font_path (Optional[str]): Optional path to a TTF font file to load.
    :ivar font_size (int): Font size in points to use when loading the font.
    :ivar sounds (Optional[dict[str, str]]): Optional dictionary mapping sound IDs to file paths.
    """

    font_path: Optional[str] = None
    font_size: int = 24
    sounds: Optional[dict[str, str]] = None  # sound_id -> path


# TODO: Refactor backend interface into smaller protocols?
# Justification: Many public methods needed for backend interface
# pylint: disable=too-many-public-methods,too-many-instance-attributes
class NativeBackend(Backend):
    """Adapter that makes the C++ Engine usable as a mini-arcade backend."""

    def __init__(self, backend_settings: BackendSettings | None = None):
        """
        :param backend_settings: Optional settings for the backend.
        :type backend_settings: BackendSettings | None
        """
        self._engine = native.Engine()

        self._font_path = (
            backend_settings.font_path if backend_settings else None
        )
        self._font_size = (
            backend_settings.font_size if backend_settings else 24
        )
        self._default_font_id: int | None = None
        self._fonts_by_size: dict[int, int] = {}

        self._sounds = backend_settings.sounds if backend_settings else None

        self._vp_offset_x = 0
        self._vp_offset_y = 0
        self._vp_scale = 1.0

    def _get_font_id(self, font_size: int | None) -> int:
        # No font loaded -> keep current “no-op” behavior
        if self._font_path is None:
            return -1

        # Default font
        if font_size is None:
            return (
                self._default_font_id
                if self._default_font_id is not None
                else -1
            )

        if font_size <= 0:
            raise ValueError(f"font_size must be > 0, got {font_size}")

        # Cached
        cached = self._fonts_by_size.get(font_size)
        if cached is not None:
            return cached

        # Lazily load and cache
        font_id = self._engine.load_font(self._font_path, int(font_size))
        self._fonts_by_size[font_size] = font_id
        return font_id

    def init(self, window_settings: WindowSettings):
        """
        Initialize the backend with a window of given width, height, and title.

        :param window_settings: Settings for the backend window.
        :type window_settings: WindowSettings
        """
        title = ""
        self._engine.init(window_settings.width, window_settings.height, title)

        # Load font if provided
        if self._font_path is not None:
            self._default_font_id = self._engine.load_font(
                self._font_path, self._font_size
            )
            self._fonts_by_size[self._font_size] = self._default_font_id

        # Load sounds if provided
        if self._sounds is not None:
            for sound_id, path in self._sounds.items():
                self.load_sound(sound_id, path)

    def set_window_title(self, title: str):
        """
        Set the window title.

        :param title: Title of the window.
        :type title: str
        """
        self._engine.set_window_title(title)

    def set_clear_color(self, r: int, g: int, b: int):
        """
        Set the background/clear color used by begin_frame.

        :param r: Red component (0-255).
        :type r: int

        :param g: Green component (0-255).
        :type g: int

        :param b: Blue component (0-255).
        :type b: int
        """
        self._engine.set_clear_color(int(r), int(g), int(b))

    # Justification: Many local variables needed for event mapping
    # pylint: disable=too-many-locals
    def poll_events(self) -> list[Event]:
        """
        Poll for events from the backend and return them as a list of Event objects.

        :return: List of Event objects representing the polled events.
        :rtype: list[Event]
        """
        out: list[Event] = []
        for ev in self._engine.poll_events():
            etype = _NATIVE_TO_CORE.get(ev.type, EventType.UNKNOWN)

            key = None
            key_code = None
            scancode = None
            mod = None
            repeat = None

            x = y = dx = dy = None
            button = None
            wheel = None
            size = None
            text = None

            if etype in (EventType.KEYDOWN, EventType.KEYUP):
                raw_key = int(getattr(ev, "key", 0) or 0)
                key_code = raw_key if raw_key != 0 else None
                key = SDL_KEYCODE_TO_KEY.get(raw_key) if raw_key != 0 else None

                scancode = (
                    int(ev.scancode) if getattr(ev, "scancode", 0) else None
                )
                mod = int(ev.mod) if getattr(ev, "mod", 0) else None

                rep = int(getattr(ev, "repeat", 0) or 0)
                repeat = bool(rep) if etype == EventType.KEYDOWN else None

            elif etype == EventType.MOUSEMOTION:
                x = int(ev.x)
                y = int(ev.y)
                dx = int(ev.dx)
                dy = int(ev.dy)

            elif etype in (EventType.MOUSEBUTTONDOWN, EventType.MOUSEBUTTONUP):
                button = int(ev.button) if ev.button else None
                x = int(ev.x)
                y = int(ev.y)

            elif etype == EventType.MOUSEWHEEL:
                wx = int(ev.wheel_x)
                wy = int(ev.wheel_y)
                wheel = (wx, wy) if (wx or wy) else None

            elif etype == EventType.WINDOWRESIZED:
                w = int(ev.width)
                h = int(ev.height)
                size = (w, h) if (w and h) else None

            elif etype == EventType.TEXTINPUT:
                t = getattr(ev, "text", "")
                text = t if t else None

            out.append(
                Event(
                    type=etype,
                    key=key,
                    key_code=key_code,
                    scancode=scancode,
                    mod=mod,
                    repeat=repeat,
                    x=x,
                    y=y,
                    dx=dx,
                    dy=dy,
                    button=button,
                    wheel=wheel,
                    size=size,
                    text=text,
                )
            )
        return out

    # pylint: enable=too-many-locals

    def begin_frame(self):
        """Begin a new frame for rendering."""
        self._engine.begin_frame()

    def end_frame(self):
        """End the current frame for rendering."""
        self._engine.end_frame()

    @staticmethod
    def _alpha_to_u8(alpha: Alpha | None) -> int:
        """Convert CSS-like alpha (0..1) to uint8 (0..255)."""
        if alpha is None:
            return 255

        # disallow booleans (since bool is a subclass of int)
        if isinstance(alpha, bool):
            raise TypeError("alpha must be a float in [0,1], not bool")

        a = float(alpha)

        # Enforce “percentage only”
        if a < 0.0 or a > 1.0:
            raise ValueError(f"alpha must be in [0, 1], got {alpha!r}")

        return int(round(a * 255))

    @staticmethod
    def _get_color_values(color: tuple[int, ...]) -> int:
        """
        Extract alpha value from color tuple (r,g,b) or (r,g,b,a).
        If missing, returns default.
        """
        if len(color) == 3:
            r, g, b = color
            a_u8 = 255
        elif len(color) == 4:
            r, g, b, a = color
            a_u8 = NativeBackend._alpha_to_u8(a)
        else:
            raise ValueError(
                f"Color must be (r,g,b) or (r,g,b,a), got {color!r}"
            )

        return (int(r), int(g), int(b), a_u8)

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def draw_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: tuple[int, ...] = (255, 255, 255),
    ):
        """
        Draw a rectangle at the specified position with given width and height.

        :param x: X coordinate of the rectangle's top-left corner.
        :type x: int

        :param y: Y coordinate of the rectangle's top-left corner.
        :type y: int

        :param w: Width of the rectangle.
        :type w: int

        :param h: Height of the rectangle.
        :type h: int

        :param color: Color of the rectangle as (r, g, b) or (r, g, b, a).
        :type color: tuple[int, ...]
        """
        r, g, b, a = self._get_color_values(color)
        sx = int(round(self._vp_offset_x + x * self._vp_scale))  # top-left x
        sy = int(round(self._vp_offset_y + y * self._vp_scale))  # top-left y
        sw = int(round(w * self._vp_scale))  # width
        sh = int(round(h * self._vp_scale))  # height
        self._engine.draw_rect(sx, sy, sw, sh, r, g, b, a)
        # self._engine.draw_rect(x, y, w, h, r, g, b, a)

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: tuple[int, int, int] = (255, 255, 255),
        font_size: int | None = None,
    ):
        """
        Draw text at the given position using the loaded font.
        If no font is loaded, this is a no-op.

        :param x: X coordinate for the text position.
        :type x: int

        :param y: Y coordinate for the text position.
        :type y: int

        :param text: The text string to draw.
        :type text: str

        :param color: Color of the text as (r, g, b).
        :type color: tuple[int, int, int]
        """
        r, g, b, a = self._get_color_values(color)
        font_id = self._get_font_id(font_size)
        sx = int(round(self._vp_offset_x + x * self._vp_scale))
        sy = int(round(self._vp_offset_y + y * self._vp_scale))

        # optional but recommended: scale font size too
        if font_size is not None:
            scaled = max(8, int(round(font_size * self._vp_scale)))
        else:
            scaled = None

        font_id = self._get_font_id(scaled)
        self._engine.draw_text(
            text, sx, sy, int(r), int(g), int(b), int(a), font_id
        )
        # self._engine.draw_text(
        #     text, x, y, int(r), int(g), int(b), int(a), font_id
        # )

    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def capture_frame(self, path: str | None = None) -> bool:
        """
        Capture the current frame.

        :param path: Optional file path to save the captured frame (e.g., PNG).
        :type path: str | None

        :return: True if the frame was successfully captured (and saved if path provided),
            False otherwise.
        :rtype: bool
        """
        if path is None:
            raise ValueError("Path must be provided to capture frame.")
        return self._engine.capture_frame(path)

    def measure_text(
        self, text: str, font_size: int | None = None
    ) -> tuple[int, int]:
        """
        Measure text size (width, height) in pixels for the active font.

        Returns (0,0) if no font is loaded (matches draw_text no-op behavior).
        """
        font_id = self._get_font_id(font_size)
        w, h = self._engine.measure_text(text, font_id)
        return int(w), int(h)

    def init_audio(
        self, frequency: int = 44100, channels: int = 2, chunk_size: int = 2048
    ):
        """Initialize SDL_mixer audio."""
        self._engine.init_audio(int(frequency), int(channels), int(chunk_size))

    def shutdown_audio(self):
        """Shutdown SDL_mixer audio and free loaded sounds."""
        self._engine.shutdown_audio()

    def load_sound(self, sound_id: str, path: str):
        """
        Load a WAV sound and store it by ID.
        Example: backend.load_sound("hit", "assets/sfx/hit.wav")
        """
        if not sound_id:
            raise ValueError("sound_id cannot be empty")

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Sound file not found: {p}")

        self._engine.load_sound(sound_id, str(p))

    def play_sound(self, sound_id: str, loops: int = 0):
        """
        Play a loaded sound.
        loops=0 => play once
        loops=-1 => infinite loop
        loops=1 => play twice (SDL convention)
        """
        self._engine.play_sound(sound_id, int(loops))

    def set_master_volume(self, volume: int):
        """
        Master volume: 0..128
        """
        self._engine.set_master_volume(int(volume))

    def set_sound_volume(self, sound_id: str, volume: int):
        """
        Per-sound volume: 0..128
        """
        self._engine.set_sound_volume(sound_id, int(volume))

    def stop_all_sounds(self):
        """Stop all channels."""
        self._engine.stop_all_sounds()

    def set_viewport_transform(
        self, offset_x: int, offset_y: int, scale: float
    ) -> None:
        self._vp_offset_x = int(offset_x)
        self._vp_offset_y = int(offset_y)
        self._vp_scale = float(scale)

    def clear_viewport_transform(self) -> None:
        self._vp_offset_x = 0
        self._vp_offset_y = 0
        self._vp_scale = 1.0

    def resize_window(self, width: int, height: int) -> None:
        self._engine.resize_window(int(width), int(height))

    def set_clip_rect(self, x: int, y: int, w: int, h: int) -> None:
        self._engine.set_clip_rect(int(x), int(y), int(w), int(h))

    def clear_clip_rect(self) -> None:
        self._engine.clear_clip_rect()
