from dataclasses import dataclass, field
from typing import Iterator, Tuple

import av
from PIL import Image, ImageDraw

from openframe.element import FrameElement
from openframe.util import ContentMode, _resize_image


@dataclass(kw_only=True)
class VideoClip(FrameElement):
    """Render a series of video frames as a frame element.

    Looping can be enabled so the clip repeats whenever the requested duration exceeds the source length.
    Use playback_rate below 1.0 to play in slow motion.
    """

    path: str
    source_start: float = 0.0
    source_end: float | None = None
    content_mode: ContentMode = ContentMode.NONE
    loop_enable: bool = False
    playback_rate: float = 1.0
    _visible_duration: float = field(init=False)
    _source_duration: float = field(init=False)
    _current_frame: Image.Image | None = field(init=False, default=None)
    _current_time: float | None = field(init=False, default=None)
    _container: av.container.input.InputContainer = field(init=False)
    _stream: av.video.stream.VideoStream = field(init=False)
    _frame_iter: Iterator[av.VideoFrame] | None = field(init=False, default=None)
    _time_base: float = field(init=False)
    _source_start_time: float = field(init=False)
    _source_end_time: float = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the decoder and timing for sequential playback.

        Returns:
            None
        """

        if self.playback_rate <= 0:
            raise ValueError("playback_rate must be greater than 0.")

        self._container = av.open(self.path)
        self._stream = self._container.streams.video[0]
        if self._stream.time_base is None:
            raise ValueError("Video stream does not provide a time base.")

        if self._stream.duration is None:
            raise ValueError("Video stream does not provide a duration.")

        self._time_base = float(self._stream.time_base)
        stream_duration = float(self._stream.duration * self._time_base)
        self._source_start_time = max(0.0, self.source_start)
        self._source_end_time = stream_duration if self.source_end is None else self.source_end

        if self._source_end_time <= self._source_start_time:
            raise ValueError("No frames available within the requested source range.")

        if self._source_end_time > stream_duration:
            raise ValueError("Requested source range exceeds video duration.")

        self._source_duration = self._source_end_time - self._source_start_time
        if self.loop_enable:
            self._visible_duration = self.duration
        else:
            self._visible_duration = min(self.duration, self._source_duration / self.playback_rate)

        self._reset_decoder(self._source_start_time)

    def is_visible(self, t: float) -> bool:
        """Report whether the clip should still draw its frames.

        Args:
            t: Current timeline time in seconds.

        Returns:
            bool: True while the source has remaining frames.
        """

        if not super().is_visible(t):
            return False

        return t < self.start_time + self._visible_duration

    def render(self, canvas: Image.Image, t: float) -> None:
        """Select the correct frame before delegating to the base renderer.

        Args:
            canvas: Frame canvas to render onto.
            t: Timeline time in seconds.

        Returns:
            None
        """

        self._current_frame = self._frame_for_time(t)
        try:
            super().render(canvas, t)
        finally:
            self._current_frame = None

    def _frame_for_time(self, t: float) -> Image.Image:
        """Pick the frame that most closely matches the requested timeline.

        Args:
            t: Timeline time in seconds.

        Returns:
            Image.Image: Frame that should be drawn.
        """

        elapsed_base = max(0.0, t - self.start_time)
        if self.loop_enable and self._source_duration > 0:
            elapsed = (elapsed_base * self.playback_rate) % self._source_duration
        else:
            elapsed = min(elapsed_base, self._visible_duration) * self.playback_rate

        target_time = self._source_start_time + elapsed
        return self._ensure_frame_for_time(target_time)

    def _render_content(self, canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        """Paint the current frame onto the overlay canvas.

        Args:
            canvas: Overlay canvas matching the clip bounds.
            draw: Drawing helper (unused).

        Returns:
            None
        """

        if self._current_frame is None:
            return
        canvas.paste(self._current_frame, (0, 0), self._current_frame)

    def _ensure_frame_for_time(self, target_time: float) -> Image.Image:
        """Decode frames until the desired timestamp is reached.

        Args:
            target_time: Timestamp in seconds relative to the source.

        Returns:
            Image.Image: Decoded frame closest to the target time.
        """

        if self._current_time is None or target_time < self._current_time:
            self._reset_decoder(self._source_start_time)

        if self._current_time is not None and target_time <= self._current_time:
            return self._current_frame

        self._advance_to_time(target_time)
        if self._current_frame is None:
            raise ValueError("Failed to decode a frame at the requested time.")
        return self._current_frame

    def _advance_to_time(self, target_time: float) -> None:
        """Advance the decoder until reaching the requested time.

        Args:
            target_time: Timestamp in seconds relative to the source.

        Returns:
            None
        """

        for frame in self._frame_iter:
            frame_time = self._frame_time(frame)

            if frame_time < self._source_start_time:
                continue
            if frame_time > self._source_end_time:
                break

            if frame_time < target_time:
                continue

            self._current_time = frame_time
            self._current_frame = self._process_frame(frame)
            return

    def _frame_time(self, frame: av.VideoFrame) -> float:
        """Return the presentation timestamp in seconds for a video frame.

        Args:
            frame: Video frame from PyAV.

        Returns:
            float: Frame timestamp in seconds.
        """

        if frame.pts is not None:
            return float(frame.pts * self._time_base)
        if frame.time is not None:
            return float(frame.time)
        raise ValueError("Decoded frame does not provide timing information.")

    def _process_frame(self, frame: av.VideoFrame) -> Image.Image:
        """Convert and resize a decoded frame for rendering.

        Args:
            frame: Video frame from PyAV.

        Returns:
            Image.Image: Processed RGBA frame.
        """

        image = frame.to_image().convert('RGBA')
        if self.size is None or self.content_mode == ContentMode.NONE:
            return image
        return _resize_image(image, self.size, self.content_mode)

    def _reset_decoder(self, seek_time: float) -> None:
        """Seek and prepare decoding from the requested time.

        Args:
            seek_time: Target time in seconds for the seek.

        Returns:
            None
        """

        pts = int(seek_time / self._time_base)
        self._container.seek(pts, stream=self._stream, any_frame=False, backward=True)
        self._frame_iter = self._container.decode(self._stream)
        self._current_time = None
        self._current_frame = None

    @property
    def bounding_box_size(self) -> Tuple[int, int]:
        """Return the size that will be used when creating overlays.

        Returns:
            Tuple[int, int]: Width and height of the clip.
        """

        if self.size is not None:
            return (max(1, self.size[0]), max(1, self.size[1]))

        frame = self._ensure_frame_for_time(self._source_start_time)
        return frame.size
