"""
Add Background Images to YOLO Dataset

This script adds background images (images without annotations) to an existing YOLO 
dataset structure. It's designed to work with datasets that have already been 
converted from COCO to YOLO format but are missing background images.

Key Features:
- Identifies background images by comparing source images with existing dataset
- Creates symlinks for background images in the YOLO dataset structure
- Creates empty label files for background images to maintain format consistency
- Distributes background images across existing dataset splits (train/val/test)
- Provides detailed statistics about the background images added

Usage:
    poetry run add-background-images \\
        --yolo-dataset-dir ./path/to/yolo/dataset \\
        --source-images-dir ./path/to/all/images

Example:
    poetry run add-background-images \\
        --yolo-dataset-dir /data/yolo/dataset \\
        --source-images-dir /data/coco/images
"""

import argparse
from pathlib import Path
from typing import Dict, List, Set


def get_existing_images(yolo_dataset_dir: Path) -> Set[str]:
    """
    Get the set of image filenames that already exist in the YOLO dataset.

    Args:
        yolo_dataset_dir: Path to the YOLO dataset directory

    Returns:
        Set of image filenames (without path) that already exist
    """
    existing_images = set()

    # Look for images directory
    images_dir = yolo_dataset_dir / "images"
    if not images_dir.exists():
        print(f"⚠️  Images directory not found: {images_dir}")
        return existing_images

    # Scan all subdirectories (train, val, test, etc.)
    for split_dir in images_dir.glob("*"):
        if not split_dir.is_dir():
            continue

        # Get all image files in this split
        image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff"]
        for ext in image_extensions:
            for img_file in split_dir.glob(ext):
                existing_images.add(img_file.name)
            # Also check uppercase extensions
            for img_file in split_dir.glob(ext.upper()):
                existing_images.add(img_file.name)

    return existing_images


def get_dataset_splits(yolo_dataset_dir: Path) -> List[Path]:
    """
    Get the list of dataset splits (train, val, test, etc.) in the YOLO dataset.

    Args:
        yolo_dataset_dir: Path to the YOLO dataset directory

    Returns:
        List of paths to split directories
    """
    splits = []

    # Check both labels and images directories for splits
    for subdir_name in ["labels", "images"]:
        subdir = yolo_dataset_dir / subdir_name
        if subdir.exists():
            for split_dir in subdir.glob("*"):
                if split_dir.is_dir():
                    splits.append(split_dir.name)
            break  # Use the first one we find

    # Remove duplicates and return as paths
    unique_splits = list(set(splits))
    return [yolo_dataset_dir / "labels" / split for split in unique_splits]


def distribute_background_images(
    background_images: List[Path], splits: List[Path]
) -> Dict[str, List[Path]]:
    """
    Distribute background images across dataset splits proportionally.

    Args:
        background_images: List of background image paths
        splits: List of split directory paths

    Returns:
        Dictionary mapping split names to lists of background images
    """
    if not splits:
        return {}

    # For simplicity, distribute evenly across splits
    # In a more sophisticated version, you could distribute proportionally
    # based on existing image counts in each split

    distribution = {split.name: [] for split in splits}
    split_names = list(distribution.keys())

    for i, bg_image in enumerate(background_images):
        split_name = split_names[i % len(split_names)]
        distribution[split_name].append(bg_image)

    return distribution


def add_background_images_to_yolo(
    yolo_dataset_dir: str, source_images_dir: str
) -> Dict:
    """
    Add background images to an existing YOLO dataset.

    Args:
        yolo_dataset_dir: Path to the existing YOLO dataset directory
        source_images_dir: Path to the directory containing all source images

    Returns:
        Dictionary with statistics about the operation
    """
    print("🖼️  Adding background images to YOLO dataset...")
    print(f"   YOLO dataset: {yolo_dataset_dir}")
    print(f"   Source images: {source_images_dir}")

    # Validate paths
    yolo_path = Path(yolo_dataset_dir)
    source_path = Path(source_images_dir)

    if not yolo_path.exists():
        raise FileNotFoundError(
            f"YOLO dataset directory does not exist: {yolo_dataset_dir}"
        )
    if not source_path.exists():
        raise FileNotFoundError(
            f"Source images directory does not exist: {source_images_dir}"
        )

    # Get existing images in the YOLO dataset
    print("🔍 Scanning existing YOLO dataset...")
    existing_images = get_existing_images(yolo_path)
    print(f"   Found {len(existing_images)} existing images in dataset")

    # Get all source images
    print("📁 Scanning source images directory...")
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    all_source_images = []
    for ext in image_extensions:
        all_source_images.extend(source_path.glob(f"*{ext}"))
        all_source_images.extend(source_path.glob(f"*{ext.upper()}"))

    print(f"   Found {len(all_source_images)} total source images")

    # Identify background images (not in existing dataset)
    background_images = [
        img for img in all_source_images if img.name not in existing_images
    ]
    print(f"   Identified {len(background_images)} background images")

    if not background_images:
        print("✅ No background images to add!")
        return {
            "background_images_found": 0,
            "background_images_added": 0,
            "empty_labels_created": 0,
            "splits_updated": 0,
            "errors": 0,
        }

    # Get dataset splits
    splits = get_dataset_splits(yolo_path)
    if not splits:
        print("⚠️  No dataset splits found. Creating 'train' split...")
        train_labels = yolo_path / "labels" / "train"
        train_images = yolo_path / "images" / "train"
        train_labels.mkdir(parents=True, exist_ok=True)
        train_images.mkdir(parents=True, exist_ok=True)
        splits = [train_labels]

    print(f"   Found {len(splits)} dataset splits: {[s.name for s in splits]}")

    # Distribute background images across splits
    distribution = distribute_background_images(background_images, splits)

    # Statistics
    stats = {
        "background_images_found": len(background_images),
        "background_images_added": 0,
        "empty_labels_created": 0,
        "splits_updated": 0,
        "errors": 0,
    }

    # Process each split
    for split_name, split_bg_images in distribution.items():
        if not split_bg_images:
            continue

        print(
            f"📂 Processing '{split_name}' split ({len(split_bg_images)} background images)..."
        )

        labels_dir = yolo_path / "labels" / split_name
        images_dir = yolo_path / "images" / split_name

        # Ensure directories exist
        labels_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        split_added = 0
        split_labels = 0

        for bg_image in split_bg_images:
            # Create image symlink
            symlink_path = images_dir / bg_image.name

            if not symlink_path.exists():
                try:
                    symlink_path.symlink_to(bg_image)
                    split_added += 1
                except Exception as e:
                    print(
                        f"❌ Error creating symlink {symlink_path} -> {bg_image}: {e}"
                    )
                    stats["errors"] += 1
                    continue

            # Create empty label file
            label_path = labels_dir / (bg_image.stem + ".txt")
            if not label_path.exists():
                try:
                    label_path.touch()  # Create empty file
                    split_labels += 1
                except Exception as e:
                    print(f"❌ Error creating empty label file {label_path}: {e}")
                    stats["errors"] += 1

        if split_added > 0:
            stats["splits_updated"] += 1
            print(
                f"   ✅ Added {split_added} images and {split_labels} empty labels to '{split_name}'"
            )

        stats["background_images_added"] += split_added
        stats["empty_labels_created"] += split_labels

    return stats


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Add background images to an existing YOLO dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add background images to YOLO dataset
  %(prog)s --yolo-dataset-dir ./yolo/data --source-images-dir ./coco/images
  
  # With absolute paths
  %(prog)s --yolo-dataset-dir /data/yolo/dataset --source-images-dir /data/coco/images
        """,
    )
    parser.add_argument(
        "--yolo-dataset-dir",
        type=str,
        required=True,
        help="Directory containing the existing YOLO dataset (with labels/ and images/ subdirs)",
    )
    parser.add_argument(
        "--source-images-dir",
        type=str,
        required=True,
        help="Directory containing all source images (flat structure)",
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    try:
        args = parse_args()

        stats = add_background_images_to_yolo(
            yolo_dataset_dir=args.yolo_dataset_dir,
            source_images_dir=args.source_images_dir,
        )

        # Print summary
        print("\n✅ Background image processing completed!")
        print("📊 Summary:")
        print(f"   Background images found: {stats['background_images_found']}")
        print(f"   Background images added: {stats['background_images_added']}")
        print(f"   Empty label files created: {stats['empty_labels_created']}")
        print(f"   Dataset splits updated: {stats['splits_updated']}")

        if stats["errors"] > 0:
            print(f"   ❌ Errors encountered: {stats['errors']}")
            return 1

        if stats["background_images_added"] == 0:
            print("   ℹ️  No new background images were added")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
