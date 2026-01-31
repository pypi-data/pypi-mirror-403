"""
COCO Category ID Remapper

This script remaps COCO category IDs to be contiguous starting from a specified ID.
It's useful for preparing datasets for frameworks that expect zero-indexed or
one-indexed contiguous category IDs.

Key Features:
- Remaps non-contiguous category IDs to contiguous values
- Configurable starting ID (0 or 1) for different framework requirements
- Updates both category definitions and annotation references
- Preserves all other category and annotation metadata
- Creates output directory if it doesn't exist

Common Use Cases:
- Preparing datasets for YOLO (expects 0-indexed categories)
- Preparing datasets for Detectron2 (expects contiguous IDs)
- Fixing datasets after category deletion or filtering
- Standardizing category IDs after merging datasets

The tool will:
1. Load the input COCO JSON file
2. Create a mapping from old category IDs to new contiguous IDs
3. Update all category definitions with new IDs
4. Update all annotation category_id references
5. Save the remapped COCO JSON

Usage:
    poetry run coco-remap \\
        --input-coco-json ./annotations/coco.json \\
        --output-coco-json ./annotations/coco_remapped.json \\
        --start-id 0

Example with 1-indexed categories:
    poetry run coco-remap \\
        -i ./annotations/coco.json \\
        -o ./annotations/coco_remapped.json \\
        -s 1
"""

import argparse
import json
from pathlib import Path


def remap_coco_category_ids(input_json_path, output_json_path, start_id=0):
    """Remap COCO category IDs to contiguous values starting from start_id."""
    
    # Load the original COCO JSON
    with open(input_json_path, "r") as f:
        coco = json.load(f)

    # Create a mapping from old category IDs to new contiguous ones
    original_categories = coco["categories"]
    id_mapping = {
        cat["id"]: new_id + start_id
        for new_id, cat in enumerate(original_categories)
    }

    # Update the categories with new IDs
    new_categories = []
    for new_id, cat in enumerate(original_categories):
        new_cat = cat.copy()
        new_cat["id"] = new_id + start_id
        new_categories.append(new_cat)
    coco["categories"] = new_categories

    # Update all annotations with the new category IDs
    for ann in coco["annotations"]:
        old_id = ann["category_id"]
        ann["category_id"] = id_mapping[old_id]

    # Save the updated COCO JSON
    with open(output_json_path, "w") as f:
        json.dump(coco, f, indent=2)

    print(f"✅ Category IDs remapped and saved to: {output_json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Remap COCO category IDs to be contiguous."
    )
    parser.add_argument(
        "--input-coco-json",
        "-i",
        default="coco.json",
        help="Path to input COCO JSON file",
    )
    parser.add_argument(
        "--output-coco-json",
        "-o",
        default="coco_remapped.json",
        help="Path to output COCO JSON file",
    )
    parser.add_argument(
        "--start-id",
        "-s",
        type=int,
        choices=[0, 1],
        default=1,
        help="Starting ID for category mapping (0 or 1)",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    Path(args.output_coco_json).parent.mkdir(parents=True, exist_ok=True)

    # Run the remapping
    remap_coco_category_ids(
        args.input_coco_json, args.output_coco_json, args.start_id
    )


if __name__ == "__main__":
    main()
