import os
import glob
import shutil
import time
import logging
import cv2
import numpy as np
import tqdm
from PIL import Image, ImageDraw, ImageFont
from typing import Callable, Type, Tuple, Union, Optional, List, Dict, Any
from functools import wraps

# Configure basic logging (Users can override this in their main app)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def split_image_into_four(image_path: str, output_paths: List[str]) -> List[str]:
    """
    Split an image evenly into four parts (Top-Left, Top-Right, Bottom-Left, Bottom-Right).

    Args:
        image_path (str): Path to the source image.
        output_paths (List[str]): A list of 4 file paths for saving the cropped images.

    Returns:
        List[str]: The list of output paths.

    Raises:
        ValueError: If output_paths does not contain exactly 4 elements.
    """
    logger.info(f"Starting image split: {os.path.basename(image_path)} -> 4 parts")
    
    if len(output_paths) != 4:
        raise ValueError("The output_paths list must contain exactly four elements.")
    
    with Image.open(image_path) as img:
        width, height = img.size
        mid_x, mid_y = width // 2, height // 2
        
        # Define regions: (left, upper, right, lower)
        regions = [
            (0, 0, mid_x, mid_y),          # Top-Left
            (mid_x, 0, width, mid_y),      # Top-Right
            (0, mid_y, mid_x, height),     # Bottom-Left
            (mid_x, mid_y, width, height)  # Bottom-Right
        ]
        
        for i, bbox in enumerate(regions):
            cropped = img.crop(bbox)
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_paths[i]), exist_ok=True)
            cropped.save(output_paths[i])
            logger.info(f"Saved part {i+1}: {os.path.basename(output_paths[i])}")
    
    logger.info("Image splitting completed.")
    return output_paths


def add_text_to_image(input_path: str, 
                      output_path: str, 
                      text: str, 
                      position: Tuple[int, int] = (50, 50), 
                      font_size: int = 40, 
                      color: Tuple[int, int, int] = (255, 255, 255), 
                      font_path: Optional[str] = None) -> bool:
    """
    Draw text onto an image and save it.

    Args:
        input_path (str): Path to the input image.
        output_path (str): Path to save the result.
        text (str): Text content to draw.
        position (Tuple[int, int]): (x, y) coordinates. Defaults to (50, 50).
        font_size (int): Font size. Defaults to 40.
        color (Tuple[int, int, int]): RGB color tuple. Defaults to white (255, 255, 255).
        font_path (Optional[str]): Path to a .ttf/.ttc file. If None, tries system default.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        image = Image.open(input_path)
        draw = ImageDraw.Draw(image)
        
        # Font loading logic
        font = None
        if font_path and os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception:
                logger.warning(f"Failed to load custom font: {font_path}, falling back to default.")
        
        if font is None:
            # Try Windows default font if on Windows, otherwise default
            try:
                font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", font_size)
            except OSError:
                font = ImageFont.load_default()
        
        draw.text(position, text, fill=color, font=font)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        logger.info(f"Image saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing image {input_path}: {str(e)}")
        return False


def pad_to_square(image: np.ndarray) -> np.ndarray:
    """
    Pad an image with black borders to make it square.
    """
    h, w = image.shape[:2]
    max_size = max(h, w)
    pad_h = (max_size - h) // 2
    pad_w = (max_size - w) // 2
    
    # Use border constant (black)
    return cv2.copyMakeBorder(
        image, 
        pad_h, max_size - h - pad_h, 
        pad_w, max_size - w - pad_w, 
        cv2.BORDER_CONSTANT, 
        value=(0, 0, 0)
    )


def concat_images_with_padding(image_path1: str, 
                               image_path2: str, 
                               target_size: int = 1024, 
                               save_path: Optional[str] = None) -> np.ndarray:
    """
    Read two images, pad them to squares, resize, and concatenate horizontally.
    """
    img1 = cv2.imread(image_path1)
    img2 = cv2.imread(image_path2)
    
    if img1 is None or img2 is None:
        raise FileNotFoundError(f"Could not read one of the images: {image_path1}, {image_path2}")

    img1_padded = pad_to_square(img1)
    img2_padded = pad_to_square(img2)
    
    img1_resized = cv2.resize(img1_padded, (target_size, target_size))
    img2_resized = cv2.resize(img2_padded, (target_size, target_size))
    
    result = cv2.hconcat([img1_resized, img2_resized])
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cv2.imwrite(save_path, result)
    
    return result


def concat_images_list_with_padding(image_path_list: List[str], 
                                    target_size: int = 1024, 
                                    save_path: Optional[str] = None) -> np.ndarray:
    """
    Concatenate a list of images horizontally. 
    Missing files are replaced with white placeholders.
    """
    out_list = []
    for img_path in image_path_list:
        if not os.path.isfile(img_path):
            # Create white placeholder
            img = np.ones((target_size, target_size, 3), dtype=np.uint8) * 255
        else:
            img_raw = cv2.imread(img_path)
            if img_raw is None:
                 img = np.ones((target_size, target_size, 3), dtype=np.uint8) * 255
            else:
                img_padded = pad_to_square(img_raw)
                img = cv2.resize(img_padded, (target_size, target_size))
        
        out_list.append(img)
    
    result = cv2.hconcat(out_list)
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cv2.imwrite(save_path, result)
    
    return result


def concat_images_list_with_padding_rowmax(image_path_list: List[str], 
                                           target_size: int = 1024, 
                                           save_path: Optional[str] = None, 
                                           max_images_per_row: int = -1) -> np.ndarray:
    """
    Concatenate images with a maximum number of images per row (grid layout).
    """
    out_list = []
    for img_path in image_path_list:
        if not os.path.isfile(img_path):
            img = np.ones((target_size, target_size, 3), dtype=np.uint8) * 255
        else:
            img_raw = cv2.imread(img_path)
            if img_raw is None:
                img = np.ones((target_size, target_size, 3), dtype=np.uint8) * 255
            else:
                img_padded = pad_to_square(img_raw)
                img = cv2.resize(img_padded, (target_size, target_size))
        out_list.append(img)
    
    if not out_list:
        raise ValueError("Image list is empty.")

    if max_images_per_row == -1 or max_images_per_row >= len(out_list):
        result = cv2.hconcat(out_list)
    else:
        rows = []
        for i in range(0, len(out_list), max_images_per_row):
            row_images = out_list[i:i + max_images_per_row]
            
            # Pad the last row with white images if necessary
            while len(row_images) < max_images_per_row:
                row_images.append(np.ones((target_size, target_size, 3), dtype=np.uint8) * 255)
            
            row = cv2.hconcat(row_images)
            rows.append(row)
        
        result = cv2.vconcat(rows)
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cv2.imwrite(save_path, result)
    
    return result


def copy_pyfile(workdir: str, output_root: str, exclude_dirs: Optional[List[str]] = None) -> None:
    """
    Recursively copy all .py files from workdir to output_root, excluding specific directories.
    """
    if exclude_dirs is None:
        exclude_dirs = []
        
    py_files = [
        f for f in glob.glob(f'{workdir}/**/*.py', recursive=True)
        if not any(excluded in f for excluded in exclude_dirs)
    ]
    
    for py_file in py_files:
        # Construct new path
        rel_path = os.path.relpath(py_file, workdir)
        dest_path = os.path.join(output_root, rel_path)
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(py_file, dest_path)


def calculate_pr(gt: Dict[Any, int], pred: Dict[Any, int]) -> Dict[str, float]:
    """
    Calculate Precision, Recall, and other metrics.
    NOTE: In this function, 0 is treated as the Positive class, 1 as Negative.
    """
    gt_keys = set(gt.keys())
    pred_keys = set(pred.keys())
    
    if gt_keys != pred_keys:
        missing_in_pred = gt_keys - pred_keys
        missing_in_gt = pred_keys - gt_keys
        error_msg = []
        if missing_in_pred:
            error_msg.append(f"Keys missing in pred: {missing_in_pred}")
        if missing_in_gt:
            error_msg.append(f"Keys missing in gt: {missing_in_gt}")
        raise ValueError("Dictionary keys do not match!\n" + "\n".join(error_msg))
    
    # Logic: 0 is Positive, 1 is Negative
    tp = sum(1 for k in gt if gt[k] == 0 and pred[k] == 0)
    fp = sum(1 for k in gt if gt[k] == 1 and pred[k] == 0)
    fn = sum(1 for k in gt if gt[k] == 0 and pred[k] == 1)
    tn = sum(1 for k in gt if gt[k] == 1 and pred[k] == 1)
    
    return _compute_metrics(tp, fp, fn, tn)


def calculate_pr2(gt: Dict[Any, int], pred: Dict[Any, int]) -> Dict[str, float]:
    """
    Calculate Precision, Recall, and other metrics.
    NOTE: Standard logic where 1 is Positive, 0 is Negative.
    """
    gt_keys = set(gt.keys())
    pred_keys = set(pred.keys())
    
    if gt_keys != pred_keys:
        missing_in_pred = gt_keys - pred_keys
        missing_in_gt = pred_keys - gt_keys
        error_msg = []
        if missing_in_pred:
            error_msg.append(f"Keys missing in pred: {missing_in_pred}")
        if missing_in_gt:
            error_msg.append(f"Keys missing in gt: {missing_in_gt}")
        raise ValueError("Dictionary keys do not match!\n" + "\n".join(error_msg))
    
    # Logic: 1 is Positive, 0 is Negative
    tp = sum(1 for k in gt if gt[k] == 1 and pred[k] == 1)
    fp = sum(1 for k in gt if gt[k] == 0 and pred[k] == 1)
    fn = sum(1 for k in gt if gt[k] == 1 and pred[k] == 0)
    tn = sum(1 for k in gt if gt[k] == 0 and pred[k] == 0)
    
    return _compute_metrics(tp, fp, fn, tn)


def _compute_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    """Helper function to compute metrics from confusion matrix counts."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # Specific metrics (translated names)
    miss_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # loujian (False Positive Rate)
    false_omission_rate = fn / (fn + tn) if (fn + tn) > 0 else 0.0 # wupan (False Negative Rate approx)
    false_discovery_rate = fp / (fp + tp) if (fp + tp) > 0 else 0.0 # cuojian
    
    return {
        'precision': precision,
        'recall': recall,
        'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
        'fpr': miss_rate,           # formerly loujian
        'fnr': false_omission_rate, # formerly wupan
        'fdr': false_discovery_rate # formerly cuojian
    }


def remove_folder(path: str) -> None:
    """Safely remove a directory."""
    if os.path.exists(path):
        shutil.rmtree(path)


def get_name_list(glob_pattern: Union[str, List[str]], ext: List[str], in_dir: str) -> List[str]:
    """
    Get a sorted list of file paths matching extensions.
    """
    name_list = []
    if isinstance(glob_pattern, list):
        for pat in glob_pattern:
            name_list += get_name_list(pat, ext, in_dir)
        return sorted(list(set(name_list))) # Ensure unique and sorted
    else:
        for ext_i in ext:
            # Construct pattern carefully
            full_pattern = os.path.join(in_dir, glob_pattern + f'.{ext_i}')
            # Handle double slashes if they occur
            full_pattern = full_pattern.replace('//', '/')
            name_list += glob.glob(full_pattern)
        return sorted(name_list)

    
def wrap_dir(func: Callable, 
             in_dir: str, 
             out_dir: str, 
             ext: List[str] = ['jpg', 'png', 'jpeg'], 
             level: int = 2, 
             output_isdir: bool = False, 
             out_ext: Optional[str] = 'jpg', 
             skip_exist: bool = False) -> None:
    """
    Recursively process files in a directory using a given function.
    
    Args:
        func: The function to apply (must accept input_path and output_path).
        in_dir: Input directory root.
        out_dir: Output directory root.
        ext: List of extensions to process.
        level: Depth of recursion (or use 0 for auto-deep search).
        output_isdir: If True, output_path passed to func is a directory, not a file.
        out_ext: Extension for the output file.
        skip_exist: If True, skips processing if output exists.
    """
    assert isinstance(level, int)
    
    if level > 0:
        glob_str = os.path.join(*['*'] * level)
    else:
        # Heuristic for irregular folder structures (depth 1 to 5)
        glob_str = [os.path.join(*['*'] * i) for i in range(1, 6)]
            
    name_list = get_name_list(glob_str, ext, in_dir)
    
    logger.info(f"Found {len(name_list)} files to process.")
    
    for name_i in tqdm.tqdm(name_list):
        # Calculate relative path to maintain structure
        rel_path = os.path.relpath(name_i, in_dir)
        
        if output_isdir:
            out_name_i = os.path.join(out_dir, os.path.dirname(rel_path), os.path.splitext(os.path.basename(name_i))[0])
        else:
            base_name = os.path.splitext(rel_path)[0]
            if out_ext:
                out_name_i = os.path.join(out_dir, f"{base_name}.{out_ext}")
            else:
                out_name_i = os.path.join(out_dir, base_name)
            
        if skip_exist and os.path.exists(out_name_i):
            logger.debug(f'{out_name_i} already exists, skipping.')
            continue
        
        # Ensure parent dir exists
        if output_isdir:
            os.makedirs(out_name_i, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(out_name_i), exist_ok=True)
            
        try:
            func(input_path=name_i, output_path=out_name_i)
        except Exception as e:
            logger.error(f'Error processing {name_i}: {e}')
            

def retry(
    max_attempts: int = 3,
    delay: int = 1,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """
    Decorator to retry a function upon exception.
    
    Args:
        max_attempts: Maximum number of attempts.
        delay: Delay in seconds between attempts.
        exceptions: The exception type(s) to catch.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.warning(
                            f"Function {func.__name__} failed on attempt {attempt}/{max_attempts}. Giving up."
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt}/{max_attempts}: {str(e)}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    
                    time.sleep(current_delay)
            
            raise last_exception
        return wrapper
    return decorator
