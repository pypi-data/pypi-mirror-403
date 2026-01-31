from dataclasses import dataclass, field
from typing import Optional, Tuple
from PIL import Image, ImageDraw

from openframe.element import FrameElement

RGBA = Tuple[int, int, int, int]


@dataclass
class ShapeClip(FrameElement):
    """Base class for shape elements that pre-render into an RGBA image.

    Attributes:
        fill: RGBA color used to fill the shape.
        stroke: RGBA color used to outline the shape.
        stroke_width: Outline width in pixels.
    """

    fill: Optional[RGBA] = (255, 255, 255, 255)
    stroke: Optional[RGBA] = None
    stroke_width: int = 0
    image: Image.Image = field(init=False)
    _bbox_size: Tuple[int, int] = field(init=False)

    def __post_init__(self) -> None:
        """Render the shape once into an RGBA image for fast compositing."""

        if self.size is None:
            raise ValueError("size must be provided for shapes.")

        if self.stroke_width < 0:
            raise ValueError("stroke_width must be 0 or greater.")

        width = max(1, self.size[0])
        height = max(1, self.size[1])
        self._bbox_size = (width, height)

        self.image = Image.new('RGBA', self._bbox_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.image)
        self._draw_shape(draw, self._bbox_size)

    def _draw_shape(self, draw: ImageDraw.ImageDraw, size: Tuple[int, int]) -> None:
        """Draw the specific shape into the given drawing context.

        Args:
            draw: Drawing context to paint the shape.
            size: Size of the shape bounding box.
        """

        raise NotImplementedError("ShapeClip._draw_shape should be implemented by subclasses.")

    def _render_content(self, canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        """Paste the cached shape image onto the overlay canvas.

        Args:
            canvas: Overlay canvas matching the target frame size.
            draw: Drawing helper (unused).
        """

        canvas.paste(self.image, (0, 0), self.image)

    @property
    def bounding_box_size(self) -> Tuple[int, int]:
        """Return the size of the cached shape image."""

        return self._bbox_size


@dataclass
class Rectangle(ShapeClip):
    """Rectangle shape element."""

    def _draw_shape(self, draw: ImageDraw.ImageDraw, size: Tuple[int, int]) -> None:
        """Draw a rectangle into the shape canvas.

        Args:
            draw: Drawing context to paint the shape.
            size: Size of the shape bounding box.
        """

        width, height = size
        outline = self.stroke
        stroke_width = self.stroke_width if outline is not None else 0
        draw.rectangle(
            (0, 0, width - 1, height - 1),
            fill=self.fill,
            outline=outline,
            width=stroke_width,
        )


@dataclass
class Circle(ShapeClip):
    """Circle shape element."""

    def _draw_shape(self, draw: ImageDraw.ImageDraw, size: Tuple[int, int]) -> None:
        """Draw a circle into the shape canvas.

        Args:
            draw: Drawing context to paint the shape.
            size: Size of the shape bounding box.
        """

        width, height = size
        outline = self.stroke
        stroke_width = self.stroke_width if outline is not None else 0
        draw.ellipse(
            (0, 0, width - 1, height - 1),
            fill=self.fill,
            outline=outline,
            width=stroke_width,
        )


@dataclass
class Triangle(ShapeClip):
    """Triangle shape element."""

    def _draw_shape(self, draw: ImageDraw.ImageDraw, size: Tuple[int, int]) -> None:
        """Draw an isosceles triangle into the shape canvas.

        Args:
            draw: Drawing context to paint the shape.
            size: Size of the shape bounding box.
        """

        width, height = size
        points = (
            (width // 2, 0),
            (0, height - 1),
            (width - 1, height - 1),
        )
        outline = self.stroke
        stroke_width = self.stroke_width if outline is not None else 0
        draw.polygon(
            points,
            fill=self.fill,
            outline=outline,
            width=stroke_width,
        )
