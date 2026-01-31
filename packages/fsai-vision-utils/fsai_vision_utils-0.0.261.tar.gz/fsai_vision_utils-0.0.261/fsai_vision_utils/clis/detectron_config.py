"""
Detectron2 Config Generator

This script generates Detectron2 configuration files from the model zoo templates.
It's useful for creating baseline configs that can be customized for your specific
training requirements.

Key Features:
- Loads any config from the Detectron2 model zoo
- Exports the full resolved configuration to YAML format
- Creates output directories automatically
- Supports all model architectures (detection, segmentation, keypoints)

The tool will:
1. Load a model zoo configuration template
2. Resolve all config inheritance and defaults
3. Export the complete configuration to a YAML file
4. Create the output directory if it doesn't exist

Usage:
    poetry run detectron-config \\
        --config-file COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml \\
        --output-path ./configs

Available Config Files (examples):
    - COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml
    - COCO-Detection/retinanet_R_50_FPN_3x.yaml
    - COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml
    - COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml
    - COCO-Keypoints/keypoint_rcnn_R_101_FPN_3x.yaml

Prerequisites:
    - Detectron2 must be installed
"""

import argparse
import os

from detectron2 import model_zoo
from detectron2.config import get_cfg


def main():
    parser = argparse.ArgumentParser(description="Generate Detectron2 config file")
    parser.add_argument(
        "--config-file",
        type=str,
        default="COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml",
        help="Config file name from model zoo (e.g., 'COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml')",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="./tmp/output_configs",
        help="Output directory path for the generated config file",
    )

    args = parser.parse_args()

    config_file = args.config_file
    output_dir = args.output_path

    config_file_base_name = config_file.split("/")[-1].split(".")[0]

    # Load and modify config
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(config_file))

    # Write to YAML file
    output_yaml_path = os.path.join(output_dir, f"{config_file_base_name}.yaml")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_yaml_path, "w") as f:
        f.write(cfg.dump())  # `dump()` returns a string in YAML format

    print(f"Config file generated: {output_yaml_path}")


if __name__ == "__main__":
    main()
