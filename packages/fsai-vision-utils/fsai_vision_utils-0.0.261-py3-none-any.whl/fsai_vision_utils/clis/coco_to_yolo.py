"""
COCO to YOLO Format Converter

This script converts COCO format annotations to YOLO format and creates symlinks 
for images organized in the proper YOLO directory structure. It handles the 
complexities of the ultralytics convert_coco function which may create output 
in various subdirectories.

Key Features:
- Converts COCO JSON annotations to YOLO format using ultralytics
- Automatically detects where convert_coco places the output files
- Creates proper image symlinks organized by dataset splits (train/val/test)
- Includes background images (images without annotations) in the dataset
- Creates empty label files for background images to maintain YOLO format consistency
- Supports keypoint annotations and class mapping options
- Handles various output directory structures from different ultralytics versions

The tool will:
1. Run ultralytics convert_coco to generate YOLO format labels
2. Automatically detect the actual output location (handles 'data2', 'VOC_dataset', etc.)
3. Clean up any empty directories created during the process
4. Create symlinks from your flat image directory to the proper YOLO structure
5. Organize images into train/val/test subdirectories matching the labels
6. Include background images (without annotations) and create empty label files for them

Usage:
    poetry run coco-to-yolo \\
        --input-dir ./path/to/coco/annotations \\
        --output-dir ./path/to/yolo/output \\
        --images-dir ./path/to/flat/images \\
        --use-keypoints \\
        --cls91to80

Example with typical paths:
    poetry run coco-to-yolo \\
        --input-dir /data/coco/annotations \\
        --output-dir /data/yolo/dataset \\
        --images-dir /data/coco/images \\
        --use-keypoints
"""

import argparse
import json
from pathlib import Path

from ultralytics.data.converter import convert_coco


def parse_coco_annotations(input_dir: Path) -> dict:
    """
    Parse COCO annotation files to extract image information and identify background images.

    Args:
        input_dir: Directory containing COCO format annotations (JSON files)

    Returns:
        dict: Contains 'all_images' (set of all image filenames) and
              'background_images' (set of image filenames without annotations)
    """
    print("📖 Parsing COCO annotation files...")

    all_images = set()
    images_with_annotations = set()

    # Find all JSON files in the input directory
    json_files = list(input_dir.glob("*.json"))
    print(f"   Found {len(json_files)} JSON files")

    for json_file in json_files:
        print(f"   Processing: {json_file.name}")

        try:
            with open(json_file, "r") as f:
                coco_data = json.load(f)

            # Extract all images from this annotation file
            if "images" in coco_data:
                for image_info in coco_data["images"]:
                    image_filename = image_info["file_name"]
                    all_images.add(image_filename)

            # Extract images that have annotations
            if "annotations" in coco_data and "images" in coco_data:
                # Create mapping from image_id to filename
                image_id_to_filename = {
                    img["id"]: img["file_name"] for img in coco_data["images"]
                }

                # Find all image_ids that have annotations
                annotated_image_ids = set()
                for annotation in coco_data["annotations"]:
                    annotated_image_ids.add(annotation["image_id"])

                # Convert image_ids to filenames
                for image_id in annotated_image_ids:
                    if image_id in image_id_to_filename:
                        images_with_annotations.add(image_id_to_filename[image_id])

        except Exception as e:
            print(f"   ⚠️  Error parsing {json_file.name}: {e}")
            continue

    # Background images are those in the dataset but without annotations
    background_images = all_images - images_with_annotations

    print(f"   Total images in COCO dataset: {len(all_images)}")
    print(f"   Images with annotations: {len(images_with_annotations)}")
    print(f"   Background images (no annotations): {len(background_images)}")

    return {
        "all_images": all_images,
        "background_images": background_images,
        "images_with_annotations": images_with_annotations,
    }


def create_image_symlinks(
    labels_root: Path,
    images_root: Path,
    target_root: Path,
    background_images: set = None,
):
    """
    Create symlinks for images based on the YOLO label structure.
    Includes both images with annotations and background images (without annotations).

    Args:
        labels_root: Path to the directory containing YOLO label subdirectories (train, val, etc.)
        images_root: Path to the flat directory containing all source images
        target_root: Path to the target directory where image symlinks will be created
        background_images: Set of background image filenames from COCO parsing (optional)

    Returns:
        dict: Statistics about symlink creation
    """
    print("🔗 Creating image symlinks...")
    print(f"   Labels directory: {labels_root}")
    print(f"   Source images: {images_root}")
    print(f"   Target directory: {target_root}")

    stats = {
        "subdirs_found": 0,
        "symlinks_created": 0,
        "symlinks_existed": 0,
        "images_not_found": 0,
        "background_images_added": 0,
        "empty_labels_created": 0,
        "errors": 0,
    }

    # Track which images have been processed to identify background images later
    processed_images = set()

    found_label_subdirs = False
    for label_subdir in labels_root.glob("*"):
        if not label_subdir.is_dir():
            continue
        found_label_subdirs = True
        stats["subdirs_found"] += 1
        print(f"📁 Processing split: {label_subdir.name}")

        # Create matching subdir in target images dir (train, val, etc.)
        image_subdir = target_root / label_subdir.name
        image_subdir.mkdir(parents=True, exist_ok=True)

        label_files = list(label_subdir.glob("*.txt"))
        print(f"   Found {len(label_files)} label files")

        # Process images that have corresponding label files
        for label_file in label_files:
            # Try multiple image extensions
            image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
            source_image_path = None

            for ext in image_extensions:
                potential_path = images_root / (label_file.stem + ext)
                if potential_path.exists():
                    source_image_path = potential_path
                    break

            if source_image_path is None:
                stats["images_not_found"] += 1
                continue

            # Track that this image has been processed
            processed_images.add(source_image_path.name)

            symlink_path = image_subdir / source_image_path.name

            if source_image_path.exists():
                if not symlink_path.exists():
                    try:
                        symlink_path.symlink_to(source_image_path)
                        stats["symlinks_created"] += 1
                    except Exception as e:
                        print(
                            f"❌ Error creating symlink {symlink_path} -> {source_image_path}: {e}"
                        )
                        stats["errors"] += 1
                else:
                    stats["symlinks_existed"] += 1

    if not found_label_subdirs:
        print(f"⚠️  No label subdirectories found in {labels_root}")
        print("   Expected subdirectories like 'train', 'val', 'test'")
        return stats

    # Now process background images (images without annotations)
    print("🖼️  Processing background images (images without annotations)...")

    if background_images is None:
        # Fallback to old behavior if no COCO data provided
        print(
            "   No COCO background image data provided, falling back to directory scanning..."
        )
        image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        all_images = []
        for ext in image_extensions:
            all_images.extend(images_root.glob(f"*{ext}"))
            all_images.extend(images_root.glob(f"*{ext.upper()}"))

        background_image_files = [
            img for img in all_images if img.name not in processed_images
        ]
    else:
        # Use COCO-derived background images
        print(
            f"   Using COCO-derived background images: {len(background_images)} images"
        )
        background_image_files = []

        # Find the actual image files for the background images
        image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        for bg_filename in background_images:
            # Try to find the image file with various extensions
            found_image = None

            # First try the filename as-is
            potential_path = images_root / bg_filename
            if potential_path.exists():
                found_image = potential_path
            else:
                # Try different extensions if the original doesn't exist
                base_name = Path(bg_filename).stem
                for ext in image_extensions:
                    potential_path = images_root / (base_name + ext)
                    if potential_path.exists():
                        found_image = potential_path
                        break
                    potential_path = images_root / (base_name + ext.upper())
                    if potential_path.exists():
                        found_image = potential_path
                        break

            if found_image:
                background_image_files.append(found_image)
            else:
                print(
                    f"   ⚠️  Background image not found in images directory: {bg_filename}"
                )

    print(f"   Found {len(background_image_files)} background images")

    if background_image_files:
        # Distribute background images across existing splits
        # Use the first split directory found, or create a 'train' directory if none exist
        split_dirs = [d for d in labels_root.glob("*") if d.is_dir()]
        if not split_dirs:
            # Create a train directory if no splits exist
            train_labels_dir = labels_root / "train"
            train_labels_dir.mkdir(parents=True, exist_ok=True)
            train_images_dir = target_root / "train"
            train_images_dir.mkdir(parents=True, exist_ok=True)
            split_dirs = [train_labels_dir]

        # For simplicity, add all background images to the first split
        # In a more sophisticated implementation, you might want to distribute them proportionally
        target_split = split_dirs[0]
        target_labels_dir = target_split
        target_images_dir = target_root / target_split.name

        print(f"   Adding background images to '{target_split.name}' split")

        for bg_image in background_image_files:
            # Create symlink for the background image
            symlink_path = target_images_dir / bg_image.name

            if not symlink_path.exists():
                try:
                    symlink_path.symlink_to(bg_image)
                    stats["symlinks_created"] += 1
                    stats["background_images_added"] += 1
                except Exception as e:
                    print(
                        f"❌ Error creating symlink for background image {symlink_path} -> {bg_image}: {e}"
                    )
                    stats["errors"] += 1
            else:
                stats["symlinks_existed"] += 1

            # Create empty label file for the background image
            label_path = target_labels_dir / (bg_image.stem + ".txt")
            if not label_path.exists():
                try:
                    label_path.touch()  # Create empty file
                    stats["empty_labels_created"] += 1
                except Exception as e:
                    print(f"❌ Error creating empty label file {label_path}: {e}")
                    stats["errors"] += 1

    return stats


def find_actual_output_directory(base_output_dir: Path) -> Path:
    """
    Find the actual directory where convert_coco placed the labels.

    ultralytics convert_coco can create output in various locations depending on version:
    - Directly in the specified directory
    - In a 'VOC_dataset' subdirectory
    - In a parallel 'data2' directory

    Args:
        base_output_dir: The directory passed to convert_coco

    Returns:
        Path to the actual output directory containing 'labels' subdirectory

    Raises:
        FileNotFoundError: If no labels directory can be found
    """
    print("🔍 Searching for actual output directory...")

    # List of potential locations to check
    candidates = [
        base_output_dir,  # Direct output
        base_output_dir / "VOC_dataset",  # Common ultralytics pattern
        base_output_dir.parent / "data2",  # Alternative pattern
        base_output_dir.parent / (base_output_dir.name + "2"),  # Generic pattern
    ]

    actual_output = None
    for candidate in candidates:
        labels_dir = candidate / "labels"
        if labels_dir.exists() and labels_dir.is_dir():
            print(f"✅ Found labels directory at: {candidate}")
            actual_output = candidate
            break

    if actual_output is None:
        # If not found, list what's actually in the base directory for debugging
        print("❌ Could not find 'labels' directory in any expected location.")
        print(f"Contents of {base_output_dir}:")
        if base_output_dir.exists():
            for item in base_output_dir.iterdir():
                print(f"   {item.name} ({'dir' if item.is_dir() else 'file'})")
        else:
            print("   Directory does not exist!")

        raise FileNotFoundError(
            f"Could not find 'labels' directory. Checked: {[str(c) for c in candidates]}"
        )

    # Clean up empty directories that may have been created
    cleanup_empty_directories(base_output_dir, actual_output)

    return actual_output


def cleanup_empty_directories(base_output_dir: Path, actual_output_dir: Path):
    """
    Clean up empty directories that were created but not used by ultralytics.

    Args:
        base_output_dir: The originally requested output directory
        actual_output_dir: The directory actually used by ultralytics
    """
    if base_output_dir != actual_output_dir:
        # Check if the base directory is empty and remove it if so
        try:
            if base_output_dir.exists() and base_output_dir.is_dir():
                # Check if directory is empty (no files or subdirectories)
                contents = list(base_output_dir.iterdir())
                if not contents:
                    print(f"🧹 Removing empty directory: {base_output_dir}")
                    base_output_dir.rmdir()
                else:
                    print(f"ℹ️  Keeping non-empty directory: {base_output_dir}")
        except Exception as e:
            print(f"⚠️  Could not remove empty directory {base_output_dir}: {e}")


def convert_coco_to_yolo(
    input_dir: str,
    output_dir: str,
    images_dir: str,
    use_keypoints: bool = False,
    cls91to80: bool = False,
) -> dict:
    """
    Convert COCO format annotations to YOLO format and create image symlinks.

    Note: The actual output directory may differ from the requested output_dir
    due to ultralytics behavior. The function will automatically detect the
    correct location and clean up any unused directories.

    Args:
        input_dir: Directory containing COCO format annotations (JSON files)
        output_dir: Requested directory to save YOLO format annotations
        images_dir: Flat directory containing all source images
        use_keypoints: Whether to process keypoint annotations
        cls91to80: Whether to convert 91 classes to 80 classes (COCO format)

    Returns:
        dict: Statistics about the conversion process including actual output location
    """
    print("🚀 Starting COCO to YOLO conversion...")
    print(f"   Input annotations: {input_dir}")
    print(f"   Output directory: {output_dir}")
    print(f"   Source images: {images_dir}")
    print(f"   Use keypoints: {use_keypoints}")
    print(f"   Convert 91->80 classes: {cls91to80}")

    # Validate input paths
    input_path = Path(input_dir)
    images_path = Path(images_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not images_path.exists():
        raise FileNotFoundError(f"Images directory does not exist: {images_dir}")

    # Parse COCO annotations to identify background images
    coco_data = parse_coco_annotations(input_path)
    background_images = coco_data["background_images"]

    # Don't create the output directory yet - let ultralytics handle it
    # This prevents creating an empty directory that might not be used
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent exists

    # Run ultralytics conversion
    print("⚙️  Running ultralytics convert_coco...")
    try:
        convert_coco(
            labels_dir=str(input_path),
            save_dir=str(output_path),
            use_keypoints=use_keypoints,
            cls91to80=cls91to80,
        )
        print("✅ convert_coco completed successfully")
    except Exception as e:
        raise RuntimeError(f"convert_coco failed: {e}")

    # Find the actual output directory
    try:
        actual_output_root = find_actual_output_directory(output_path)
    except FileNotFoundError as e:
        raise RuntimeError(f"Could not locate converted labels: {e}")

    # Set up paths for symlink creation
    labels_root = actual_output_root / "labels"
    target_images_root = actual_output_root / "images"

    # Ensure target images directory exists
    target_images_root.mkdir(parents=True, exist_ok=True)

    # Create image symlinks
    symlink_stats = create_image_symlinks(
        labels_root, images_path, target_images_root, background_images
    )

    # Collect overall statistics
    stats = {
        "conversion_successful": True,
        "actual_output_directory": str(actual_output_root),
        "labels_directory": str(labels_root),
        "images_directory": str(target_images_root),
        "symlink_stats": symlink_stats,
    }

    return stats


def parse_args():
    """Parse command line arguments for the COCO to YOLO converter."""
    parser = argparse.ArgumentParser(
        description="Convert COCO format annotations to YOLO format and create image symlinks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  %(prog)s --input-dir ./coco/annotations --output-dir ./yolo/data --images-dir ./coco/images
  
  # With keypoints and class conversion
  %(prog)s --input-dir ./coco/annotations --output-dir ./yolo/data --images-dir ./coco/images --use-keypoints --cls91to80
        """,
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing COCO format annotations (JSON files)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save YOLO format annotations and images",
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        required=True,
        help="Flat directory containing all source images (supports .jpg, .jpeg, .png, .bmp, .tiff)",
    )
    parser.add_argument(
        "--use-keypoints",
        action="store_true",
        help="Process keypoint annotations (default: False)",
    )
    parser.add_argument(
        "--cls91to80",
        action="store_true",
        help="Convert COCO 91 classes to 80 classes (default: False)",
    )
    return parser.parse_args()


def main():
    """Main entry point for the COCO to YOLO converter."""
    try:
        args = parse_args()

        stats = convert_coco_to_yolo(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            images_dir=args.images_dir,
            use_keypoints=args.use_keypoints,
            cls91to80=args.cls91to80,
        )

        # Print summary statistics
        print("\n✅ Conversion completed successfully!")
        print("📊 Summary:")
        print(f"   Output directory: {stats['actual_output_directory']}")
        print(f"   Labels: {stats['labels_directory']}")
        print(f"   Images: {stats['images_directory']}")

        symlink_stats = stats["symlink_stats"]
        print(f"   Dataset splits found: {symlink_stats['subdirs_found']}")
        print(f"   Symlinks created: {symlink_stats['symlinks_created']}")
        print(f"   Symlinks already existed: {symlink_stats['symlinks_existed']}")
        print(f"   Background images added: {symlink_stats['background_images_added']}")
        print(f"   Empty label files created: {symlink_stats['empty_labels_created']}")

        if symlink_stats["images_not_found"] > 0:
            print(f"   ⚠️  Images not found: {symlink_stats['images_not_found']}")
        if symlink_stats["errors"] > 0:
            print(f"   ❌ Symlink errors: {symlink_stats['errors']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()
