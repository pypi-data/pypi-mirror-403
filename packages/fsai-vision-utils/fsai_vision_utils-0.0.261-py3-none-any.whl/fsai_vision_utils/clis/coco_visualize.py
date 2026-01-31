"""
COCO Dataset Visualizer using FiftyOne

This script provides an interactive visualization interface for COCO format datasets
using FiftyOne. It allows you to browse images, view annotations, and inspect your
dataset before training or after inference.

Key Features:
- Interactive web-based visualization interface
- Browse images with bounding box and segmentation overlays
- Filter and search annotations by category
- Zoom and pan on images to inspect details
- Named datasets for easy organization and comparison

The tool will:
1. Load a COCO dataset from the specified image directory and annotation file
2. Launch the FiftyOne web application in your browser
3. Wait for you to finish browsing before exiting

Usage:
    poetry run coco-visualize \\
        --image-dir ./images \\
        --input-coco-json ./annotations/coco.json

Example with custom dataset name:
    poetry run coco-visualize \\
        --image-dir ./images \\
        --input-coco-json ./annotations/coco.json \\
        --dataset-name my_training_data

Prerequisites:
    - FiftyOne must be installed (included in dependencies)
    - A modern web browser for the visualization interface
"""

import argparse

import fiftyone as fo


def visualize_coco_dataset(data_path, labels_path, name="coco_dataset"):
    dataset = fo.Dataset.from_dir(
        dataset_type=fo.types.COCODetectionDataset,
        data_path=data_path,
        labels_path=labels_path,
        name=name,
    )
    session = fo.launch_app(dataset)
    session.wait()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize a COCO dataset using FiftyOne"
    )
    parser.add_argument(
        "--image-dir", required=True, help="Path to the image directory"
    )
    parser.add_argument(
        "--input-coco-json", required=True, help="Path to the COCO JSON annotation file"
    )
    parser.add_argument(
        "--dataset-name",
        default="coco_dataset",
        help="Optional name for the FiftyOne dataset",
    )

    args = parser.parse_args()
    visualize_coco_dataset(args.image_dir, args.input_coco_json, args.dataset_name)


if __name__ == "__main__":
    main()
