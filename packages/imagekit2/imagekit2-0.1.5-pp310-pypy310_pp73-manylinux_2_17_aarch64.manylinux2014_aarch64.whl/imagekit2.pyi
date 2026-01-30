from typing import Optional, List

class Watermarker:
    """
    ImageKit2 Watermark Processor.
    """

    def __init__(self, font_paths: Optional[List[str]] = None) -> None:
        """
        Initialize the Watermarker.

        Args:
            font_paths: A list of paths to custom font files or directories containing fonts.
                        If None, the built-in default font is used.
        """
        ...

    def process(
        self,
        image_bytes: bytes,
        text: str,
        position: str = "br",
        x: Optional[int] = None,
        y: Optional[int] = None,
        padding: int = 10,
        opacity: float = 0.8,
        size: float = 24.0,
        color: str = "#FFFFFF",
        angle: float = 0.0,
        stroke_width: int = 0,
        stroke_color: str = "#000000",
        shadow_x: int = 0,
        shadow_y: int = 0,
        shadow_color: str = "#000000",
        align: str = "left",
        output_format: str = "png",
        quality: int = 80,
        image_scale: float = 1.0,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
    ) -> bytes:
        """
        Add a text watermark to an image.

        Args:
            image_bytes: The binary data of the source image.
            text: The watermark text content (supports multiline).
            position: Position of the watermark ('tl', 'tr', 'bl', 'br', 'center', 'tile'). Defaults to 'br'.
            x: Manually specify the X coordinate (pixels). Overrides 'position' if set.
            y: Manually specify the Y coordinate (pixels). Overrides 'position' if set.
            padding: Padding from edges or spacing for tiling. Defaults to 10.
            opacity: Opacity level (0.0 - 1.0). Defaults to 0.8.
            size: Font size. Defaults to 24.0.
            color: Text color (Hex, e.g., '#FF0000' or '#FF000080') or 'auto' (smart contrast).
            angle: Rotation angle in degrees. Defaults to 0.0.
            stroke_width: Width of the text stroke (pixels). 0 means no stroke.
            stroke_color: Color of the stroke.
            shadow_x: Horizontal offset of the drop shadow. Defaults to 0.
            shadow_y: Vertical offset of the drop shadow. Defaults to 0.
            shadow_color: Color of the drop shadow. Defaults to "#000000".
            align: Text alignment for multiline text ('left', 'center', 'right').
            output_format: Output image format ('jpeg', 'png', 'webp', 'avif'...).
            quality: Output quality for JPEG (1-100). Defaults to 80.
            image_scale: Scale factor for the source image (e.g., 0.5 to shrink by half). Defaults to 1.0.
            resize_width: Limit the output image width. Defaults to None (keep original).
            resize_height: Limit the output image height. Defaults to None (keep original).

        Returns:
            The binary data of the processed image.
        """
        ...

    def process_image(
        self,
        image_bytes: bytes,
        logo_bytes: bytes,
        position: str = "br",
        x: Optional[int] = None,
        y: Optional[int] = None,
        padding: int = 10,
        opacity: float = 0.8,
        scale: float = 0.2,
        angle: float = 0.0,
        output_format: str = "png",
        quality: int = 80,
        image_scale: float = 1.0,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
    ) -> bytes:
        """
        Add an image (Logo) watermark to an image.

        Args:
            image_bytes: The binary data of the source image.
            logo_bytes: The binary data of the logo image.
            position: Position of the watermark ('tl', 'tr', 'bl', 'br', 'center', 'tile').
            x: Manually specify the X coordinate.
            y: Manually specify the Y coordinate.
            padding: Padding from edges or spacing for tiling.
            opacity: Opacity level (0.0 - 1.0).
            scale: Logo scale factor (percentage of the source image width). 0 means original logo size.
            angle: Rotation angle in degrees.
            output_format: Output image format.
            quality: Output quality for JPEG (1-100).
            image_scale: Scale factor for the source image.
            resize_width: Limit the output image width. Defaults to None.
            resize_height: Limit the output image height. Defaults to None.

        Returns:
            The binary data of the processed image.
        """
        ...
