"""
COCO Prediction Generator using SAHI

This script runs SAHI (Slicing Aided Hyper Inference) predictions on images and
generates COCO-format results JSON compatible with pycocotools evaluation.

Key Features:
- Uses SAHI for sliced inference on high-resolution images
- Supports keypoint detection models (e.g., YOLOv11 pose)
- Parallel processing with multiple workers for faster inference
- Generates COCO-format results JSON for evaluation with pycocotools
- Configurable slice size, overlap, and post-processing parameters

The tool will:
1. Load a COCO ground truth annotation file to get image IDs
2. Run SAHI sliced inference on each image in the specified directory
3. Convert detections (including keypoints) to COCO format
4. Save results JSON compatible with COCOeval

Usage:
    poetry run coco-predict \\
        --model-path ./weights/best.pt \\
        --image-dir ./images/test \\
        --coco-gt ./annotations/test.json \\
        --output ./results.json \\
        --num-workers 8

Example with all options:
    poetry run coco-predict \\
        --model-path ./weights/best.pt \\
        --image-dir ./images/test \\
        --coco-gt ./annotations/test.json \\
        --output ./results.json \\
        --max-images 50 \\
        --num-workers 4 \\
        --device cuda:0 \\
        --confidence-threshold 0.25 \\
        --slice-size 2048 \\
        --overlap-ratio 0.2
"""

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from pathlib import Path

import numpy as np
from pycocotools.coco import COCO
from tqdm import tqdm

from fsai_vision_utils.libs.sahi.models.ultralytics import UltralyticsDetectionModel
from fsai_vision_utils.libs.sahi.predict import get_sliced_prediction

# ============================================================
# LAZY GLOBALS (PER PROCESS)
# ============================================================

_model = None
_file_to_image_id = None
_config = None


def init_worker(config: dict):
    """
    Initialize worker process with configuration.

    Args:
        config: Dictionary containing model_path, coco_gt_ann, device, and confidence_threshold
    """
    global _config
    _config = config


def get_model():
    """
    Lazily create one UltralyticsDetectionModel per process.
    This avoids sharing the model across processes/threads.

    Returns:
        UltralyticsDetectionModel: The initialized detection model
    """
    global _model
    if _model is None:
        _model = UltralyticsDetectionModel(
            model_path=_config["model_path"],
            confidence_threshold=_config["confidence_threshold"],
            device=_config["device"],
        )
    return _model


def get_file_to_image_id():
    """
    Lazily load COCO GT and build filename → image_id mapping per process.

    Returns:
        dict: Mapping from image filename to COCO image ID
    """
    global _file_to_image_id
    if _file_to_image_id is None:
        coco_gt = COCO(_config["coco_gt_ann"])
        _file_to_image_id = {
            img["file_name"]: img["id"] for img in coco_gt.dataset["images"]
        }
    return _file_to_image_id


# ============================================================
# KEYPOINT CONVERSION TO COCO FORMAT
# ============================================================


def convert_keypoints(keypoints_obj, vis_thresh: float = 0.2) -> tuple[list, int]:
    """
    Convert custom Keypoints/Keypoint objects to COCO keypoints format.

    COCO keypoints format: [x1, y1, v1, x2, y2, v2, ...]
    where v: 0 = not labeled, 1 = labeled but not visible, 2 = visible

    Args:
        keypoints_obj: Keypoints object from detection model (various formats supported)
        vis_thresh: Visibility threshold - keypoints with score > vis_thresh are marked visible

    Returns:
        tuple: (flat_keypoints_list, visible_count)
            - flat_keypoints_list: COCO format [x1, y1, v1, x2, y2, v2, ...]
            - visible_count: Number of visible keypoints
    """
    if keypoints_obj is None:
        return [], 0

    # 1. Try to unwrap common container attributes: .keypoints / .points / .data / .tensor
    raw = keypoints_obj
    for attr in ("keypoints", "points", "data", "tensor"):
        if hasattr(raw, attr):
            candidate = getattr(raw, attr)
            try:
                len(candidate)
                raw = candidate
                break
            except TypeError:
                pass

    flat = []
    visible_count = 0

    try:
        iterator = iter(raw)
    except TypeError:
        print("convert_keypoints: raw is not iterable:", type(raw))
        return [], 0

    for kp in iterator:
        # Case 1: custom object with attributes
        if not isinstance(kp, (list, tuple, np.ndarray)):
            if hasattr(kp, "x") and hasattr(kp, "y"):
                x = float(kp.x)
                y = float(kp.y)
                if hasattr(kp, "score"):
                    score = float(kp.score)
                elif hasattr(kp, "confidence"):
                    score = float(kp.confidence)
                else:
                    score = 1.0
            elif hasattr(kp, "pt"):  # e.g. OpenCV-style points
                x, y = kp.pt[:2]
                x, y = float(x), float(y)
                score = float(getattr(kp, "score", 1.0))
            else:
                print("convert_keypoints: unknown keypoint object type:", type(kp))
                continue
        else:
            # Case 2: tuple/list/np.array → (x, y) or (x, y, score)
            arr = np.asarray(kp, dtype=float)
            if arr.size == 2:
                x, y = arr
                score = 1.0
            elif arr.size >= 3:
                x, y, score = arr[:3]
            else:
                print("convert_keypoints: unexpected tuple size:", arr.shape)
                continue

        v = 2 if score > vis_thresh else 0  # visibility flag
        flat.extend([float(x), float(y), int(v)])
        if v > 0:
            visible_count += 1

    return flat, visible_count


# ============================================================
# WORKER FUNCTION FOR ONE IMAGE
# ============================================================


def process_single_image(
    img_path: Path,
    slice_height: int = 2048,
    slice_width: int = 2048,
    overlap_height_ratio: float = 0.2,
    overlap_width_ratio: float = 0.2,
) -> tuple[str, list]:
    """
    Run SAHI prediction on a single image and return COCO-format entries.

    This function is executed inside worker processes.

    Args:
        img_path: Path to the image file
        slice_height: Height of each slice for SAHI inference
        slice_width: Width of each slice for SAHI inference
        overlap_height_ratio: Vertical overlap ratio between slices
        overlap_width_ratio: Horizontal overlap ratio between slices

    Returns:
        tuple: (filename, list_of_coco_entries)
            - filename: Name of the processed image file
            - list_of_coco_entries: List of COCO-format detection dictionaries
    """
    model = get_model()
    file_to_image_id = get_file_to_image_id()

    filename = img_path.name

    if filename not in file_to_image_id:
        # Return empty result if not in COCO GT
        return filename, []

    image_id = file_to_image_id[filename]

    pred = get_sliced_prediction(
        str(img_path),
        model,
        slice_height=slice_height,
        slice_width=slice_width,
        overlap_height_ratio=overlap_height_ratio,
        overlap_width_ratio=overlap_width_ratio,
        perform_standard_pred=True,
        postprocess_match_threshold=0.5,
        postprocess_match_metric="IOS",
        postprocess_type="KEYPOINT_AWARE",
        keypoint_merge_strategy="LARGEST_BOX",
    )

    entries = []
    for det in pred.object_prediction_list:
        # BBOX xyxy → xywh
        x1, y1, x2, y2 = det.bbox.to_xyxy()
        w, h = float(x2 - x1), float(y2 - y1)

        score = getattr(det.score, "value", det.score)

        # Category ID (using model class directly)
        if hasattr(det, "category") and hasattr(det.category, "id"):
            category_id = int(det.category.id)
        else:
            category_id = int(det.category_id)

        # Keypoints
        kp_raw = getattr(det, "keypoints", None)
        coco_kps, num_kps = convert_keypoints(kp_raw)

        entry = {
            "image_id": image_id,
            "category_id": category_id,
            "bbox": [float(x1), float(y1), float(w), float(h)],
            "score": float(score),
        }

        if coco_kps:
            entry["keypoints"] = coco_kps
            entry["num_keypoints"] = num_kps

        entries.append(entry)

    return filename, entries


# ============================================================
# MAIN: PARALLEL INFERENCE + BUILD COCO JSON
# ============================================================


def run_coco_prediction(
    model_path: str,
    image_dir: str,
    coco_gt_ann: str,
    output_json: str,
    max_images: int | None = None,
    num_workers: int = 8,
    device: str = "cuda:0",
    confidence_threshold: float = 0.25,
    slice_size: int = 2048,
    overlap_ratio: float = 0.2,
) -> dict:
    """
    Run SAHI predictions on images and generate COCO-format results JSON.

    Args:
        model_path: Path to the model weights file (e.g., best.pt)
        image_dir: Directory containing images to process
        coco_gt_ann: Path to COCO ground truth annotation JSON
        output_json: Path to save the output results JSON
        max_images: Maximum number of images to process (None for all)
        num_workers: Number of parallel worker processes
        device: Device to run inference on (e.g., 'cuda:0', 'cpu')
        confidence_threshold: Minimum confidence for detections
        slice_size: Size of slices for SAHI inference (height and width)
        overlap_ratio: Overlap ratio between slices

    Returns:
        dict: Statistics about the prediction run
    """
    global _config
    _config = {
        "model_path": model_path,
        "coco_gt_ann": coco_gt_ann,
        "device": device,
        "confidence_threshold": confidence_threshold,
    }

    # Gather images in folder
    image_paths = sorted(list(Path(image_dir).glob("*.jpg")))
    print(f"Found {len(image_paths)} images.")

    if max_images is not None:
        image_paths = image_paths[:max_images]
        print(f"Using first {len(image_paths)} images (max_images = {max_images})")

    if not image_paths:
        raise RuntimeError(f"No images found in {image_dir}")

    results_json = []

    # Create partial function with slice parameters
    process_func = partial(
        process_single_image,
        slice_height=slice_size,
        slice_width=slice_size,
        overlap_height_ratio=overlap_ratio,
        overlap_width_ratio=overlap_ratio,
    )

    # Parallel inference (process-based)
    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=init_worker,
        initargs=(_config,),
    ) as executor:
        futures = {
            executor.submit(process_func, img_path): img_path
            for img_path in image_paths
        }

        with tqdm(total=len(futures), desc="Running SAHI inference", ncols=100) as pbar:
            for future in as_completed(futures):
                filename, entries = future.result()
                if not entries:
                    tqdm.write(f"[WARN] {filename}: not in COCO GT or no detections.")
                else:
                    tqdm.write(f"{filename}: {len(entries)} detections")
                results_json.extend(entries)
                pbar.update(1)

    # Write results JSON
    os.makedirs(os.path.dirname(output_json) or ".", exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(results_json, f)

    print(f"\nSaved COCO results ({len(results_json)} detections) to:\n  {output_json}")

    return {
        "images_processed": len(image_paths),
        "total_detections": len(results_json),
        "output_file": output_json,
    }


def parse_args():
    """Parse command line arguments for the COCO prediction generator."""
    parser = argparse.ArgumentParser(
        description="Run SAHI predictions on images and generate COCO-format results JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s --model-path ./weights/best.pt --image-dir ./images/test \\
           --coco-gt ./annotations/test.json --output ./results.json

  # With custom parameters
  %(prog)s --model-path ./weights/best.pt --image-dir ./images/test \\
           --coco-gt ./annotations/test.json --output ./results.json \\
           --max-images 50 --num-workers 4 --device cuda:0
        """,
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to the model weights file (e.g., best.pt)",
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        required=True,
        help="Directory containing images to process (*.jpg)",
    )
    parser.add_argument(
        "--coco-gt",
        type=str,
        required=True,
        help="Path to COCO ground truth annotation JSON (for image ID mapping)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the output COCO results JSON",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Maximum number of images to process (default: all)",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=8,
        help="Number of parallel worker processes (default: 8)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        help="Device to run inference on (default: cuda:0)",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.25,
        help="Minimum confidence threshold for detections (default: 0.25)",
    )
    parser.add_argument(
        "--slice-size",
        type=int,
        default=2048,
        help="Size of slices for SAHI inference (default: 2048)",
    )
    parser.add_argument(
        "--overlap-ratio",
        type=float,
        default=0.2,
        help="Overlap ratio between slices (default: 0.2)",
    )
    return parser.parse_args()


def main():
    """Main entry point for the COCO prediction generator."""
    # CUDA requires 'spawn' start method for multiprocessing
    import multiprocessing as mp
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # Already set

    try:
        args = parse_args()

        stats = run_coco_prediction(
            model_path=args.model_path,
            image_dir=args.image_dir,
            coco_gt_ann=args.coco_gt,
            output_json=args.output,
            max_images=args.max_images,
            num_workers=args.num_workers,
            device=args.device,
            confidence_threshold=args.confidence_threshold,
            slice_size=args.slice_size,
            overlap_ratio=args.overlap_ratio,
        )

        print("\n✅ Prediction completed successfully!")
        print("📊 Summary:")
        print(f"   Images processed: {stats['images_processed']}")
        print(f"   Total detections: {stats['total_detections']}")
        print(f"   Output file: {stats['output_file']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()
