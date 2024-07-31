from segment_anything import SamPredictor, sam_model_registry, SamAutomaticMaskGenerator
# import matplotlib.pyplot as plt
import torch
import numpy as np
import cv2
from rest_api.utils import image_utils as iu
# import numpy_utils as nu
from PIL import Image
import requests
# import numpy as np
from io import BytesIO


def combine_masks_to_multiclass(masks):
    """
    Combine multiple binary masks into a single multi-class mask.

    Parameters:
    - masks (list of np.ndarray): A list of binary masks, all of the same shape.

    Returns:
    - np.ndarray: A multi-class mask where each input mask is assigned a unique class value based on its index.
    """
    # Ensure all masks are the same size and are binary
    height, width = masks[0].shape
    for mask in masks:
        assert mask.shape == (height, width), "All masks must have the same dimensions"
        assert set(np.unique(mask)).issubset({0, 1}), "Masks must be binary"
        # Initialize the multi-class mask with zeros (background class)
    multiclass_mask = np.zeros((height, width), dtype=np.uint8)
    # Assign each mask a unique class value based on its index
    for i, mask in enumerate(masks, start=1):  # Starting index at 1 to reserve 0 for background
        # Update pixels in the multi-class mask where the current mask is foreground (non-zero)
        multiclass_mask[mask > 0] = i
    return multiclass_mask


def extract_pixel_level_polygons_from_mask(mask):
    class_ids = np.unique(mask)[1:]  # Excludes the background
    class_polygons = []
    for class_id in class_ids:
        binary_mask = np.where(mask == class_id, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            # Directly use contour points for pixel-level detail
            polygon = [[point[0][0], point[0][1]] for point in contour]
            class_polygons.append((class_id, polygon))
            # class_polygons.extend([(class_id, point) for point in polygon])
    return class_polygons


def generate_polygons(url):
    # im = iu.read_image('/Users/apple/Downloads/Organized/AS_0320_03/DJI_0180_AS_0320_03.JPG')
    # im = iu.read_image('/Users/apple/Downloads/fort.jpg')
    # Download the image
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    # Convert image to numpy array
    np_im = np.array(img)
    print('downloaded image')
    # np_im = np.asarray(im)
    sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b_01ec64.pth")
    mask_generator = SamAutomaticMaskGenerator(sam)
    mask_generator = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=20,
        pred_iou_thresh=0.96,
        stability_score_thresh=0.92,
        crop_n_layers=1,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=1000  # Requires open-cv to run post-processing
    )
    print('created sam')
    masks = mask_generator.generate(np_im)
    print('inference')
    seg_masks = [np.array(tuple(item['segmentation']), dtype=np.uint8) for item in masks]
    seg_mask = combine_masks_to_multiclass(seg_masks)
    polygon_data = extract_pixel_level_polygons_from_mask(seg_mask)
    polygons = [polygon for _, polygon in polygon_data]
    print('created polygons')
    return polygons


# generate_polygons('https://uf-ecl-annotator-bucket.s3.amazonaws.com/33280ddb-2e17-49c8-81e9-fe43df8b4d2a.png')