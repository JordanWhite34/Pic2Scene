from pathlib import Path
import argparse

from PIL import Image


def register_heic_support() -> None:
    import pillow_heif

    pillow_heif.register_heif_opener()


DEFAULT_INPUT_DIR = Path("inputs/water_tower")
DEFAULT_OUTPUT_DIR = Path("inputs/water_tower_converted")
DEFAULT_LONGEST_SIDE = 2000
JPEG_QUALITY = 95
HEIC_EXTENSIONS = {".heic", ".heif"}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
SUPPORTED_INPUT_EXTENSIONS = HEIC_EXTENSIONS | JPEG_EXTENSIONS


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


def find_image_inputs(input_dir: Path) -> list[Path]:
    """Return supported image files in stable processing order."""
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS
    )


def output_path_for(input_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{input_path.stem}.jpg"


def validate_output_paths(input_paths: list[Path], output_dir: Path) -> None:
    """Avoid silently overwriting two same-stem inputs in one run."""
    seen: dict[str, Path] = {}
    for input_path in input_paths:
        output_path = output_path_for(input_path, output_dir)
        output_key = output_path.name.lower()
        if output_key in seen:
            first_input = seen[output_key]
            raise ValueError(
                "Multiple inputs would write to the same output file "
                f"{output_path}: {first_input.name}, {input_path.name}"
            )
        seen[output_key] = input_path


def convert_image_directory(
    input_dir: Path,
    output_dir: Path,
    longest_side: int = DEFAULT_LONGEST_SIDE,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    input_paths = find_image_inputs(input_dir)
    validate_output_paths(input_paths, output_dir)

    if any(path.suffix.lower() in HEIC_EXTENSIONS for path in input_paths):
        register_heic_support()

    for input_path in input_paths:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            img = resize_to_longest_side(img, longest_side)

            out_path = output_path_for(input_path, output_dir)
            img.save(out_path, "JPEG", quality=JPEG_QUALITY)

        print("Wrote:", out_path)


def convert_heic_directory(
    input_dir: Path,
    output_dir: Path,
    longest_side: int = DEFAULT_LONGEST_SIDE,
) -> None:
    """Backward-compatible name for existing callers."""
    convert_image_directory(input_dir, output_dir, longest_side)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert HEIC/JPEG images to JPEG and resize their longest side."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=(
            "Directory containing .heic, .heif, .jpg, or .jpeg files. "
            f"Default: {DEFAULT_INPUT_DIR}"
        ),
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
    convert_image_directory(args.input_dir, args.output_dir, args.longest_side)


if __name__ == "__main__":
    main()
