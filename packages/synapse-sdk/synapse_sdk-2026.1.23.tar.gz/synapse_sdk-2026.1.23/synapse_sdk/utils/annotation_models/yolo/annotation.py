"""YOLO annotation model.

Supports standard YOLO detection format with normalized coordinates.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class YOLOAnnotation(BaseModel):
    """Single YOLO annotation line.

    YOLO format uses normalized center coordinates:
    `class_id cx cy w h`

    All coordinates are normalized to [0, 1] range.

    Attributes:
        class_id: Class index (0-based).
        cx: Normalized center x coordinate.
        cy: Normalized center y coordinate.
        w: Normalized width.
        h: Normalized height.
    """

    class_id: int = Field(ge=0)
    cx: float = Field(ge=0, le=1)
    cy: float = Field(ge=0, le=1)
    w: float = Field(ge=0, le=1)
    h: float = Field(ge=0, le=1)

    def to_line(self) -> str:
        """Convert to YOLO label line format.

        Returns:
            String in format: `class_id cx cy w h`
        """
        return f'{self.class_id} {self.cx:.6f} {self.cy:.6f} {self.w:.6f} {self.h:.6f}'

    @classmethod
    def from_line(cls, line: str) -> YOLOAnnotation:
        """Parse from YOLO label line.

        Args:
            line: String in format: `class_id cx cy w h`

        Returns:
            YOLOAnnotation instance.
        """
        parts = line.strip().split()
        return cls(
            class_id=int(parts[0]),
            cx=float(parts[1]),
            cy=float(parts[2]),
            w=float(parts[3]),
            h=float(parts[4]),
        )

    def to_absolute(self, width: int, height: int) -> tuple[float, float, float, float]:
        """Convert to absolute pixel coordinates.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Tuple of (x, y, w, h) in absolute coordinates.
        """
        abs_w = self.w * width
        abs_h = self.h * height
        abs_x = (self.cx * width) - (abs_w / 2)
        abs_y = (self.cy * height) - (abs_h / 2)
        return abs_x, abs_y, abs_w, abs_h

    @classmethod
    def from_absolute(
        cls,
        class_id: int,
        x: float,
        y: float,
        w: float,
        h: float,
        img_width: int,
        img_height: int,
    ) -> YOLOAnnotation:
        """Create from absolute pixel coordinates.

        Args:
            class_id: Class index.
            x: Top-left x coordinate.
            y: Top-left y coordinate.
            w: Box width.
            h: Box height.
            img_width: Image width in pixels.
            img_height: Image height in pixels.

        Returns:
            YOLOAnnotation with normalized coordinates.
        """
        cx = (x + w / 2) / img_width
        cy = (y + h / 2) / img_height
        nw = w / img_width
        nh = h / img_height
        return cls(class_id=class_id, cx=cx, cy=cy, w=nw, h=nh)


__all__ = ['YOLOAnnotation']
