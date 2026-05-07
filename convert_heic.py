from pathlib import Path
import argparse

from PIL import Image


def register_heic_support() -> None:
    import pillow_heif

    pillow_heif.register_heif_opener()


DEFAULT_INPUT_DIR = Path("inputs/jordan")
DEFAULT_OUTPUT_DIR = Path("inputs/jordan_converted")
DEFAULT_LONGEST_SIDE = 2000
JPEG_QUALITY = 95


def resize_to_longest_side(image: Image.Image, longest_side: int) -> Image.Image:
    """Downscale image so its longest side is at most longest_side."""
    if longest_side <= 0:
        raise ValueError("longest_side must be greater than 0")

    width, height = image.size
    current_longest_side = max(width, height)
    if current_longest_side <= longest_side:
        return image

    scale = longest_side / current_longest_side
    resized_size = (round(width * scale), round(height * scale))
    return image.resize(resized_size, Image.Resampling.LANCZOS)


def convert_heic_directory(
    input_dir: Path,
    output_dir: Path,
    longest_side: int = DEFAULT_LONGEST_SIDE,
) -> None:
    register_heic_support()
    output_dir.mkdir(parents=True, exist_ok=True)

    for heic_path in sorted(input_dir.glob("*.heic")):
        with Image.open(heic_path) as img:
            img = img.convert("RGB")
            img = resize_to_longest_side(img, longest_side)

            out_path = output_dir / f"{heic_path.stem}.jpg"
            img.save(out_path, "JPEG", quality=JPEG_QUALITY)

        print("Converted:", out_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert HEIC images to JPEG and resize their longest side."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory containing .heic files. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for converted .jpg files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--longest-side",
        type=int,
        default=DEFAULT_LONGEST_SIDE,
        help=(
            "Maximum output longest side in pixels. "
            f"Default: {DEFAULT_LONGEST_SIDE}"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    convert_heic_directory(args.input_dir, args.output_dir, args.longest_side)


if __name__ == "__main__":
    main()
