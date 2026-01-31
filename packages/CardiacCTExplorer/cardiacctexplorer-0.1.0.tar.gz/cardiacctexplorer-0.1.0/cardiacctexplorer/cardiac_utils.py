"""Cardiac CT processing functions"""
import os
import time
import multiprocessing as mp
import json
import importlib.metadata
import numpy as np
import edt
import SimpleITK as sitk
from skimage.morphology import closing, opening, ball
import cardiacctexplorer.general_utils as gu
import cardiacctexplorer.io_utils as io_utils
import cardiacctexplorer.segmentation_utils as su
from cardiacctexplorer.visualization_utils import RenderCardiacData


def compute_input_image_statistics(params):
    """
    Compute simple statistics on the input image
    """
    input_file = params["input_file"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    stats_out_name = f"{stats_folder}input_image_statistics.json"
    out_of_reconstruction_val = params.get("out_of_reconstruction_value", -2048)

    if os.path.exists(stats_out_name):
        if not quiet:
            print(f"{stats_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {stats_out_name}")

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    image_stats = {}
    spacing = ct_img.GetSpacing()
    img_size_vox = ct_img.GetSize()
    image_stats["spacing_x"] = spacing[0]
    image_stats["spacing_y"] = spacing[1]
    image_stats["spacing_z"] = spacing[2]
    image_stats["size_vox_x"] = img_size_vox[0]
    image_stats["size_vox_y"] = img_size_vox[1]
    image_stats["size_vox_z"] = img_size_vox[2]
    image_stats["size_mm_x"] = spacing[0] * img_size_vox[0]
    image_stats["size_mm_y"] = spacing[1] * img_size_vox[1]
    image_stats["size_mm_z"] = spacing[2] * img_size_vox[2]

    ct_img_np = sitk.GetArrayFromImage(ct_img)
    # Get all values above out_of_reconstruction_val + 1
    valid_voxels = ct_img_np[ct_img_np > out_of_reconstruction_val + 1]
    image_stats["full_image_num_valid_voxels"] = int(len(valid_voxels))
    image_stats["full_image_hu_mean"] = float(np.mean(valid_voxels))
    image_stats["full_image_hu_std"] = float(np.std(valid_voxels))
    image_stats["full_image_hu_min"] = int(np.min(valid_voxels))
    image_stats["full_image_hu_max"] = int(np.max(valid_voxels))
    image_stats["full_image_hu_q01"] = float(np.percentile(valid_voxels, 1))
    image_stats["full_image_hu_q99"] = float(np.percentile(valid_voxels, 99))
    image_stats["full_image_hu_q001"] = float(np.percentile(valid_voxels, 0.1))
    image_stats["full_image_hu_q999"] = float(np.percentile(valid_voxels, 99.9))
    json_object = json.dumps(image_stats, indent=4)
    with open(stats_out_name, "w") as outfile:
        outfile.write(json_object)

    return True

#
# def compute_mask_hu_statistics(ct_img_np, mask, spacing, anatomy_name, segm_name, params, hu_stats):
#     quiet = params["quiet"]
#     # verbose = params["verbose"]
#     output_folder = params["output_folder"]
#     write_log_file = params["write_log_file"]
#     out_of_scan_value = params.get("out_of_reconstruction_value", -2048)
#
#     # Remove the part of the mask, where the image values are below out_of_scan_value + 1
#     mask = np.logical_and(mask, ct_img_np > out_of_scan_value + 1)
#
#     if np.sum(mask) == 0:
#         msg = f"Could not find {anatomy_name} label in TotalSegmentator segmentation {segm_name}."
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#
#     erosion_diam = 2  # in mm
#     mask_eroded = su.edt_based_erosion(mask, [spacing[2], spacing[1], spacing[0]], erosion_diam)
#     if np.sum(mask_eroded) == 0:
#         msg = f"Could not find {anatomy_name} label in TotalSegmentator segmentation {segm_name} after erosion."
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#
#     hu_vals = ct_img_np[mask_eroded]
#     hu_stats[f"{anatomy_name}_vox_count"] = len(hu_vals)
#     hu_stats[f"{anatomy_name}_hu_mean"] = np.mean(hu_vals)
#     hu_stats[f"{anatomy_name}_hu_std"] = np.std(hu_vals)
#     hu_stats[f"{anatomy_name}_hu_med"] = np.median(hu_vals)
#     hu_stats[f"{anatomy_name}_hu_min"] = int(np.min(hu_vals))
#     hu_stats[f"{anatomy_name}_hu_max"] = int(np.max(hu_vals))
#     hu_stats[f"{anatomy_name}_hu_q01"] = np.percentile(hu_vals, 1)
#     hu_stats[f"{anatomy_name}_hu_q99"] = np.percentile(hu_vals, 99)
#     hu_stats[f"{anatomy_name}_hu_q001"] = np.percentile(hu_vals, 0.1)
#     hu_stats[f"{anatomy_name}_hu_q999"] = np.percentile(hu_vals, 99.9)
#     return True
#

# def compute_hu_statistics(params):
#     """
#     Compute Hounsfield unit statistics in known regions of the heart
#     """
#     input_file = params["input_file"]
#     ts_folder = params["ts_folder"]
#     output_folder = params["output_folder"]
#     stats_folder = params["stats_folder"]
#     quiet = params["quiet"]
#     verbose = params["verbose"]
#     write_log_file = params["write_log_file"]
#
#     segm_name_total = f"{ts_folder}total.nii.gz"
#     segm_name_hc = f"{ts_folder}heartchambers_highres.nii.gz"
#     stats_out_name = f"{stats_folder}hu_statistics.json"
#     la_segm_id = 2
#     pv_segm_id = 53
#     aorta_segm_id = 6
#
#     if os.path.exists(stats_out_name):
#         if not quiet:
#             print(f"{stats_out_name} already exists - skipping")
#         return True
#
#     if verbose:
#         print(f"Computing {stats_out_name}")
#
#     label_img_total = io_utils.read_nifti_with_logging_cached(segm_name_total, verbose, quiet, write_log_file, output_folder)
#     if label_img_total is None:
#         return False
#
#     label_img_hc = io_utils.read_nifti_with_logging_cached(segm_name_hc, verbose, quiet, write_log_file, output_folder)
#     if label_img_hc is None:
#         return False
#
#     ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
#     if ct_img is None:
#         return False
#
#     ct_img_np = sitk.GetArrayFromImage(ct_img)
#     label_img_total_np = sitk.GetArrayFromImage(label_img_total)
#     label_img_hc_np = sitk.GetArrayFromImage(label_img_hc)
#     pv_mask = label_img_total_np == pv_segm_id
#     la_mask = label_img_hc_np == la_segm_id
#     aorta_mask = label_img_hc_np == aorta_segm_id
#     spacing = label_img_total.GetSpacing()
#
#     hu_stats = {}
#     compute_mask_hu_statistics(ct_img_np, pv_mask, spacing, "pv", segm_name_total,
#                                          params, hu_stats)
#     compute_mask_hu_statistics(ct_img_np, la_mask, spacing, "la", segm_name_hc,
#                                          params, hu_stats)
#     compute_mask_hu_statistics(ct_img_np, aorta_mask, spacing, "aorta", segm_name_hc,
#                                          params, hu_stats)
#
#     json_object = json.dumps(hu_stats, indent=4)
#     with open(stats_out_name, "w") as outfile:
#         outfile.write(json_object)
#     return True

#
# def extract_laa_roi(params):
#     """
#     Extract the region around the left atrial appendage
#     """
#     input_file = params["input_file"]
#     ts_folder = params["ts_folder"]
#     output_folder = params["output_folder"]
#     # scan_id = params["pure_id"]
#     crops_folder = params["crops_folder"]
#     quiet = params["quiet"]
#     verbose = params["verbose"]
#     write_log_file = params["write_log_file"]
#
#     segm_name_total = f"{ts_folder}total.nii.gz"
#     crop_out_name = f"{crops_folder}laa_roi.nii.gz"
#     # crop_out_name_np = f"{crops_folder}laa_roi.npy"
#     laa_label_id = 61
#
#     if os.path.exists(crop_out_name):
#         if not quiet:
#             print(f"{crop_out_name} already exists - skipping")
#         return True
#
#     if verbose:
#         print(f"Computing {crop_out_name}")
#
#     if not os.path.exists(segm_name_total):
#         msg = f"TotalSegmentator segmentation {segm_name_total} not found. Can not extract LAA ROI."
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#     label_img_total = io_utils.read_nifti_with_logging_cached(segm_name_total, verbose, quiet, write_log_file, output_folder)
#     if label_img_total is None:
#         return False
#
#     ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
#     if ct_img is None:
#         return False
#
#     # ct_np = sitk.GetArrayFromImage(ct_img)
#     label_img_total_np = sitk.GetArrayFromImage(label_img_total)
#     laa_mask = label_img_total_np == laa_label_id
#
#     if np.sum(laa_mask) == 0:
#         msg = f"Could not find LAA label in TotalSegmentator segmentation {segm_name_total}."
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#
#     spacing = label_img_total.GetSpacing()
#     # We want at least 1 cubic centimeter
#     min_comp_size_mm3 = 1000
#     min_comp_size_vox = int(min_comp_size_mm3 / (spacing[0] * spacing[1] * spacing[2]))
#     if verbose:
#         print(f"Finding LAA components with min_comp_size: {min_comp_size_vox} voxels = {min_comp_size_mm3:.1f} mm^3")
#
#     components = su.get_components_over_certain_size_as_individual_volumes(laa_mask, min_comp_size_vox, 1)
#     if components is None or len(components) == 0:
#         msg = f"Could not find any components of size > {min_comp_size_mm3} mm3 in {segm_name_total}"
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#
#     laa_mask = components[0]
#
#     com_np = measurements.center_of_mass(laa_mask)
#     # Do the transpose of the coordinates (SimpleITK vs. numpy)
#     com_np = [com_np[2], com_np[1], com_np[0]]
#     com_phys = label_img_total.TransformIndexToPhysicalPoint([int(com_np[0]), int(com_np[1]), int(com_np[2])])
#
#     side_length_mm = 70
#     nvox = 128
#
#     # Create the sampled image with same direction
#     direction = ct_img.GetDirection()
#
#     # Desired voxel spacing for new image
#     new_spacing = [side_length_mm / nvox, side_length_mm / nvox, side_length_mm / nvox]
#
#     com = com_phys
#     dir_x = direction[0]
#     dir_y = direction[4]
#     dir_z = direction[8]
#     # print(f"Directions: {dir_x} {dir_y} {dir_z}")
#     new_origin_x = com[0] - dir_x * side_length_mm / 2
#     new_origin_y = com[1] - dir_y * side_length_mm  / 2
#     new_origin_z = com[2] - dir_z * side_length_mm / 2
#     # print(f"New origin: {new_origin_x} {new_origin_y} {new_origin_z}")
#
#     new_size = [nvox, nvox, nvox]
#     new_image = sitk.Image(new_size, ct_img.GetPixelIDValue())
#     new_image.SetOrigin([new_origin_x, new_origin_y, new_origin_z])
#     new_image.SetSpacing(new_spacing)
#     new_image.SetDirection(direction)
#
#     # Make translation with no offset, since sitk.Resample needs this arg.
#     translation = sitk.TranslationTransform(3)
#     translation.SetOffset((0, 0, 0))
#
#     default_value = -2048.0
#     interpolator = sitk.sitkLinear
#     # Create final resampled image
#     resampled_image = sitk.Resample(ct_img, new_image, translation, interpolator, default_value)
#     sitk.WriteImage(resampled_image, crop_out_name)
#
#     # occ_np = sitk.GetArrayViewFromImage(resampled_image)
#     # occ_np = np.flip(occ_np, 2)
#     # np.save(crop_out_name_np, occ_np)
#
#     return True
#

# def predict_laa_with_nudf(params):
#     """
#     Predict the labelmap of the left atrial appendage using the NUDF model
#     """
#     input_file = params["input_file"]
#     ts_folder = params["ts_folder"]
#     output_folder = params["output_folder"]
#     crops_folder = params["crops_folder"]
#     stats_folder = params["stats_folder"]
#     segm_folder = params["segm_folder"]
#     quiet = params["quiet"]
#     verbose = params["verbose"]
#     write_log_file = params["write_log_file"]
#     device_in = params["device"]
#     min_hu = params.get("minimum_laa_hu_value", 200)
#     crop_name_in = f"{crops_folder}laa_roi.nii.gz"
#     sdf_out_name = f"{segm_folder}laa_nudf_sdf.nii.gz"
#     crop_label_out_name = f"{segm_folder}laa_nudf_label_crop.nii.gz"
#     laa_label_out_name = f"{segm_folder}laa_nudf_label.nii.gz"
#     segm_name_total = f"{ts_folder}total.nii.gz"
#     hu_stats_name = f"{stats_folder}hu_statistics.json"
#
#     debug = False
#
#     if verbose:
#         print(f"Computing LAA prediction with NUDF for {input_file}")
#     if os .path.exists(laa_label_out_name):
#         if verbose:
#             print(f"{laa_label_out_name} already exists - skipping")
#         return True
#
#     # Read HU statistics to adjust min_hu if needed
#     if os.path.exists(hu_stats_name):
#         with open(hu_stats_name, "r") as f:
#             hu_stats = json.load(f)
#         la_q001_hu = hu_stats.get("la_hu_q001", 100000)
#         pv_q001 = hu_stats.get("pv_hu_q001", 100000)
#         aorta_q001 = hu_stats.get("aorta_hu_q001", 100000)
#         min_hu = min(la_q001_hu, pv_q001, aorta_q001, min_hu)
#     if verbose:
#         print(f"Using minimum HU value of {min_hu} for LAA prediction")
#
#     device = select_device(device_in)
#
#     crop_img = io_utils.read_nifti_with_logging_cached(crop_name_in, verbose, quiet, write_log_file, output_folder)
#     if crop_img is None:
#         return False
#
#     crop_img_np = sitk.GetArrayFromImage(crop_img)
#     # Flip to make compatible with NUDF input
#     crop_img_np = np.flip(crop_img_np, 2)
#     # HU normalization
#     crop_normalized = np.clip(crop_img_np, -1000, 1000) / 1000
#     # Reshape to add channel dimension
#     input_data = np.expand_dims(crop_normalized, axis=0)
#
#     # TODO: Get from config
#     resolution = 128
#     batch_points = 100000
#     checkpoint_file = params["nudf_checkpoint_file"]
#
#     nudf_predictor = NUDFPredictor(checkpoint_file, device=device, resolution=resolution, batch_points=batch_points)
#
#     if verbose:
#         print("Setting up NUDF model")
#     if not nudf_predictor.setup_model():
#         msg = "Could not set up NUDF model for LAA prediction."
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#
#     data = {'inputs': np.array(input_data, dtype=np.float32)}
#
#     if verbose:
#         print("Running NUDF prediction")
#     logits, _ = nudf_predictor.predict(data)
#
#     # Export SDF
#     dim = (np.round(len(logits)**(1/3)).astype(int),)*3
#     numpy_3d_sdf_tensor = np.reshape(logits,dim)
#
#     # Flip to get correct orientation
#     numpy_3d_sdf_tensor = np.flip(numpy_3d_sdf_tensor, 2)
#     if debug:
#         img_sdf = sitk.GetImageFromArray(numpy_3d_sdf_tensor)
#         img_sdf.CopyInformation(crop_img)
#         sitk.WriteImage(img_sdf, sdf_out_name)
#
#     if verbose:
#         print("Generating LAA label from SDF")
#
#     # Generate label volume
#     laa_label_np = (numpy_3d_sdf_tensor < 0).astype(np.uint8)
#
#     # Flip crop image back to original orientation
#     crop_img_np = np.flip(crop_img_np, 2)
#     # Should have a minimum HU to be considered part of LAA
#     laa_label_np[crop_img_np <= min_hu] = 0
#
#     spacing = crop_img.GetSpacing()
#     # We want at least 1 cubic centimeter
#     min_comp_size_mm3 = 1000
#     min_comp_size_vox = int(min_comp_size_mm3 / (spacing[0] * spacing[1] * spacing[2]))
#     if verbose:
#         print(f"Finding LAA components with min_comp_size: {min_comp_size_vox} voxels = {min_comp_size_mm3:.1f} mm^3")
#
#     components = su.get_components_over_certain_size_as_individual_volumes(laa_label_np, min_comp_size_vox, 1)
#     if components is None or len(components) == 0:
#         msg = f"Could not find any components of size > {min_comp_size_mm3} mm3 in {input_file}"
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#
#     laa_mask = components[0]
#     laa_mask_sitk = sitk.GetImageFromArray(laa_mask.astype(np.uint8))
#     laa_mask_sitk.CopyInformation(crop_img)
#     if debug:
#         sitk.WriteImage(laa_mask_sitk, crop_label_out_name)
#
#     # Read total segmentation to place LAA label in correct location
#     label_img_total = io_utils.read_nifti_with_logging_cached(segm_name_total, verbose, quiet, write_log_file, output_folder)
#     if label_img_total is None:
#         return False
#
#     # Resample LAA label to original image size and spacing
#     original_size = label_img_total.GetSize()
#     original_spacing = label_img_total.GetSpacing()
#     original_origin = label_img_total.GetOrigin()
#     original_direction = label_img_total.GetDirection()
#     new_image = sitk.Image(original_size, laa_mask_sitk.GetPixelIDValue())
#     new_image.SetOrigin(original_origin)
#     new_image.SetSpacing(original_spacing)
#     new_image.SetDirection(original_direction)
#     # Make translation with no offset, since sitk.Resample needs this arg.
#     translation = sitk.TranslationTransform(3)
#     translation.SetOffset((0, 0, 0))
#     default_value = 0
#     interpolator = sitk.sitkNearestNeighbor
#     # Create final resampled image
#     resampled_image = sitk.Resample(laa_mask_sitk, new_image, translation, interpolator, default_value)
#
#     laa_resampled_np = sitk.GetArrayFromImage(resampled_image)
#     # Remove the LAA part that is covered by the total segmentation
#     label_img_total_np = sitk.GetArrayFromImage(label_img_total)
#     label_img_total_not_laa = (label_img_total_np > 0) & (label_img_total_np != 61) & (label_img_total_np != 51)
#     laa_resampled_np = np.bitwise_and(laa_resampled_np, np.bitwise_not(label_img_total_not_laa))
#
#     laa_label_np = laa_resampled_np == 1
#     components = su.get_components_over_certain_size_as_individual_volumes(laa_label_np, min_comp_size_vox, 1)
#     if components is None or len(components) == 0:
#         msg = f"Could not find any components of size > {min_comp_size_mm3} mm3 in {input_file}"
#         if not quiet:
#             print(msg)
#         if write_log_file:
#             gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
#         return False
#
#     laa_mask = components[0]
#     laa_mask_sitk = sitk.GetImageFromArray(laa_mask.astype(np.uint8))
#     laa_mask_sitk.CopyInformation(resampled_image)
#
#     sitk.WriteImage(laa_mask_sitk, laa_label_out_name)
#
#     return True


def refine_pulmonary_veins(params):
    """
    The pulmonary veins (PV) segmentations from TotalSegmentator mostly does not go all the way to the left atrium (LA),
    This function tries to refine the PV segmentation to include the part that is connected to the LA.
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    hu_stats_name = f"{stats_folder}hu_statistics.json"
    min_hu = params.get("minimum_pv_hu_value", 200)

    segm_name_total = f"{ts_folder}total.nii.gz"
    segm_name_hc = f"{ts_folder}heartchambers_highres.nii.gz"
    segm_name_laa = f"{segm_folder}laa_nudf_label.nii.gz"
    segm_out_name = f"{segm_folder}pv_refined.nii.gz"
    la_segm_id = 2
    pv_segm_id = 53
    dist_threshold = 7
    do_morpho = True
    # debug = True


    if os.path.exists(segm_out_name):
        if not quiet:
            print(f"{segm_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {segm_out_name}")

    if os.path.exists(hu_stats_name):
        with open(hu_stats_name, "r") as f:
            hu_stats = json.load(f)
        la_q001_hu = hu_stats.get("la_hu_q001", 100000)
        pv_q001 = hu_stats.get("pv_hu_q001", 100000)
        min_hu = min(la_q001_hu, pv_q001, min_hu)
    if verbose:
        print(f"Using minimum HU value of {min_hu} for pulmonary veins refinement")

    label_img_total = io_utils.read_nifti_with_logging_cached(segm_name_total, verbose, quiet, write_log_file, output_folder)
    if label_img_total is None:
        return False

    label_img_hc = io_utils.read_nifti_with_logging_cached(segm_name_hc, verbose, quiet, write_log_file, output_folder)
    if label_img_hc is None:
        return False

    label_img_laa = io_utils.read_nifti_with_logging_cached(segm_name_laa, verbose, quiet, write_log_file, output_folder)
    if label_img_laa is None:
        return False

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    ct_img_np = sitk.GetArrayFromImage(ct_img)
    label_img_total_np = sitk.GetArrayFromImage(label_img_total)
    label_img_hc_np = sitk.GetArrayFromImage(label_img_hc)
    label_img_laa_np = sitk.GetArrayFromImage(label_img_laa)
    pv_mask = label_img_total_np == pv_segm_id
    la_mask = label_img_hc_np == la_segm_id
    laa_mask = label_img_laa_np == 1
    spacing = label_img_total.GetSpacing()
    hc_all_mask = label_img_hc_np > 0

    pv_refined_mask = np.copy(pv_mask)
    n_iterations = 3
    for iteration in range(n_iterations):
        if iteration == 2:
            dist_threshold = 2
        if verbose:
            print(f"Refining pulmonary veins - iteration {iteration + 1} of {n_iterations}")
        overlap_mask = su.edt_based_overlap(pv_refined_mask, la_mask, [spacing[2], spacing[1], spacing[0]],
                                            dist_threshold)

        new_refined_mask = np.bitwise_or(pv_refined_mask, overlap_mask)

        # Remove the LAA from the overlap region since it is often get caught in the PV
        new_refined_mask = np.bitwise_and(new_refined_mask, np.bitwise_not(laa_mask))

        # Remove all heart chambers from refined mask to avoid leakage
        new_refined_mask = np.bitwise_and(new_refined_mask, np.bitwise_not(hc_all_mask))

        # Keep only the part of pv that has HU above min_hu
        new_refined_mask = np.bitwise_and(new_refined_mask, ct_img_np > min_hu)

        if do_morpho:
            radius = 3
            if iteration == 2:
                radius = 1
            footprint = ball(radius=radius)
            new_refined_mask = opening(new_refined_mask, footprint)
            footprint = ball(radius=3)
            new_refined_mask = closing(new_refined_mask, footprint)

        min_comp_size_mm = 1000  # in mm3
        min_comp_size_vox = int(min_comp_size_mm / (spacing[0] * spacing[1] * spacing[2]))

        components = su.get_components_over_certain_size_as_individual_volumes(new_refined_mask, min_comp_size_vox, 6)
        if components is None:
            msg = f"Could not find any pv components of size > {min_comp_size_mm} mm3 in {input_file}"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
            return False

        refined_segm = components[0]
        for idx in range(1, len(components)):
            refined_segm = np.bitwise_or(refined_segm, components[idx])

        pv_refined_mask = np.copy(refined_segm)

    label_img_out = sitk.GetImageFromArray(pv_refined_mask.astype(np.uint8))
    label_img_out.CopyInformation(label_img_total)
    sitk.WriteImage(label_img_out, segm_out_name)

    return True


def combine_low_and_high_res_aorta(params):
    """
    TotalSegmentator produces two aorta segmentations - one from the low-res model and one from the high-res model.
    This function combines them into one segmentation.
    It also employs an adaptive thresholding based on HU statistics to remove voxels clearly not part of the aorta blood pool.
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    hu_stats_name = f"{stats_folder}hu_statistics.json"
    min_hu = params.get("minimum_aorta_hu_value", 150)

    segm_name_total = f"{ts_folder}total.nii.gz"
    segm_name_hc = f"{ts_folder}heartchambers_highres.nii.gz"
    segm_out_name = f"{segm_folder}aorta_refined.nii.gz"
    aorta_hires_segm_id = 6
    aorta_lowres_segm_id = 52
    do_morpho = True
    # debug = True

    if os.path.exists(segm_out_name):
        if not quiet:
            print(f"{segm_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {segm_out_name}")

    if os.path.exists(hu_stats_name):
        with open(hu_stats_name, "r") as f:
            hu_stats = json.load(f)
            la_q001_hu = hu_stats.get("la_hu_q001", 100000)
            pv_q001 = hu_stats.get("pv_hu_q001", 100000)
            aorta_q001 = hu_stats.get("aorta_hu_q001", 100000)
            min_hu = min(la_q001_hu, pv_q001, aorta_q001, min_hu)
    if verbose:
        print(f"Using minimum HU value of {min_hu} for aorta combination prediction")

    label_img_total = io_utils.read_nifti_with_logging_cached(segm_name_total, verbose, quiet, write_log_file, output_folder)
    if label_img_total is None:
        return False

    label_img_hc = io_utils.read_nifti_with_logging_cached(segm_name_hc, verbose, quiet, write_log_file, output_folder)
    if label_img_hc is None:
        return False

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    ct_img_np = sitk.GetArrayFromImage(ct_img)
    label_img_total_np = sitk.GetArrayFromImage(label_img_total)
    label_img_hc_np = sitk.GetArrayFromImage(label_img_hc)
    aorta_hi_res = label_img_hc_np == aorta_hires_segm_id
    aorta_low_res = label_img_total_np == aorta_lowres_segm_id

    spacing = label_img_total.GetSpacing()

    combined = np.bitwise_or(aorta_hi_res, aorta_low_res)
    # make sure that HU values are above the minimum
    combined = np.bitwise_and(combined, ct_img_np > min_hu)
    refined_segm = combined
    if do_morpho:
        footprint = ball(radius=3)
        refined_segm = opening(combined, footprint)
        footprint = ball(radius=3)
        refined_segm = closing(refined_segm, footprint)

    # We want at least 5 cubic centimeter
    min_comp_size_mm3 = 5000
    min_comp_size_vox = int(min_comp_size_mm3 / (spacing[0] * spacing[1] * spacing[2]))
    if verbose:
        print(f"Finding aorta components with min_comp_size: {min_comp_size_vox} voxels = {min_comp_size_mm3:.1f} mm^3")

    components = su.get_components_over_certain_size_as_individual_volumes(refined_segm, min_comp_size_vox, 2)
    if components is None or len(components) == 0:
        msg = f"Could not find any aorta components of size > {min_comp_size_mm3} mm3 in {input_file}"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    refined_segm = components[0]
    for idx in range(1, len(components)):
        refined_segm = np.bitwise_or(refined_segm, components[idx])

    label_img_out = sitk.GetImageFromArray(refined_segm.astype(np.uint8))
    label_img_out.CopyInformation(label_img_total)
    sitk.WriteImage(label_img_out, segm_out_name)

    return True


def refine_coronary_artery_aorta_overlap(params):
    """
    Sometime segmentations of the coronary arteries does not meet the aorta segmentation properly,
    especially the original ImageCAS manual segmentations have this issue.
    This function tries to refine the coronary artery segmentation to include the part that is connected to the aorta.
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    image_cas_mode = params.get("image_cas_mode", False)
    hu_stats_name = f"{stats_folder}hu_statistics.json"
    min_hu = params.get("minimum_coronary_artery_hu_value", 20)

    segm_name_aorta = f"{segm_folder}aorta_refined.nii.gz"
    segm_out_name = f"{segm_folder}coronary_arteries_refined.nii.gz"
    dist_threshold = 3
    do_morpho = True
    # debug = True

    # In ImageCAS mode, the coronary artery segmentation is in the same folder as the input image
    if image_cas_mode:
        segm_name_ca = input_file
        segm_name_ca = segm_name_ca.replace("img", "label")
    else:
        segm_name_ca = f"{ts_folder}coronary_arteries.nii.gz"


    if os.path.exists(segm_out_name):
        if not quiet:
            print(f"{segm_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {segm_out_name}")

    if os.path.exists(hu_stats_name):
        with open(hu_stats_name, "r") as f:
            hu_stats = json.load(f)
        la_q001_hu = hu_stats.get("la_hu_q001", 100000)
        pv_q001 = hu_stats.get("pv_hu_q001", 100000)
        min_hu = min(la_q001_hu, pv_q001, min_hu)
    if verbose:
        print(f"Using minimum HU value of {min_hu} for coronary artery refinement")

    label_img_aorta = io_utils.read_nifti_with_logging_cached(segm_name_aorta, verbose, quiet, write_log_file, output_folder)
    if label_img_aorta is None:
        return False

    label_img_ca = io_utils.read_nifti_with_logging_cached(segm_name_ca, verbose, quiet, write_log_file, output_folder)
    if label_img_ca is None:
        return False

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    ct_img_np = sitk.GetArrayFromImage(ct_img)
    label_img_aorta_np = sitk.GetArrayFromImage(label_img_aorta)
    label_img_ca_np = sitk.GetArrayFromImage(label_img_ca)
    aorta_mask = label_img_aorta_np == 1
    ca_mask = label_img_ca_np == 1
    spacing = label_img_aorta.GetSpacing()

    overlap_mask = su.edt_based_overlap(aorta_mask, ca_mask, [spacing[2], spacing[1], spacing[0]],
                                        dist_threshold)

    new_refined_mask = np.bitwise_or(ca_mask, overlap_mask)

    # Remove aorta from mask to  avoid leakage
    new_refined_mask = np.bitwise_and(new_refined_mask, np.bitwise_not(aorta_mask))

    # Keep only the part of pv that has HU above min_hu
    new_refined_mask = np.bitwise_and(new_refined_mask, ct_img_np > min_hu)

    if do_morpho:
        radius = 1
        footprint = ball(radius=radius)
        new_refined_mask = opening(new_refined_mask, footprint)
        footprint = ball(radius=3)
        new_refined_mask = closing(new_refined_mask, footprint)

    min_comp_size_mm = 100  # in mm3
    min_comp_size_vox = int(min_comp_size_mm / (spacing[0] * spacing[1] * spacing[2]))

    # We allow up to 6 components since coronary arteries can be disconnected
    # (not anatomically correct, but can happen in segmentations)
    components = su.get_components_over_certain_size_as_individual_volumes(new_refined_mask, min_comp_size_vox, 6)
    if components is None:
        msg = f"Could not find any pv components of size > {min_comp_size_mm} mm3 for refined coronary artery segmentation"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    if verbose:
        print(f"Found {len(components)} coronary artery components after refinement")
    refined_segm = components[0]
    for idx in range(1, len(components)):
        refined_segm = np.bitwise_or(refined_segm, components[idx])

    ca_refined_mask = np.copy(refined_segm)

    label_img_out = sitk.GetImageFromArray(ca_refined_mask.astype(np.uint8))
    label_img_out.CopyInformation(label_img_aorta)
    sitk.WriteImage(label_img_out, segm_out_name)

    return True



def add_segmentation_to_combined_segmentation(segm, combined, label_num, min_comp_size=1000, max_num_components=1):
    segm_filter = np.bitwise_and(segm, combined == 0)
    components = su.get_components_over_certain_size_as_individual_volumes(segm_filter, min_comp_size,
                                                                            max_num_components)
    if components is not None:
        segm_filter = components[0]
        for idx in range(1, len(components)):
            segm_filter = np.bitwise_or(segm_filter, components[idx])
        combined = np.maximum(combined, segm_filter * label_num)
    return combined


def get_label_names_and_numbers_as_text():
    label_names = ("1 : Myocardium : The muscle tissue surrounding the left ventricle blood pool\n"
                   "2 : LA : The left atrium blood pool\n"
                   "3 : LV : The left ventricle blood pool including the papilary muscles and trabeculation\n"
                   "4 : RA : The right atrium blood pool\n"
                   "5 : RV : The right ventricle blood pool\n"
                   "6 : Aorta : The aorta including the aortic cusp\n"
                   "7 : PA : The pulmonary artery\n"
                   "8 : LAA : The left atrial appendage\n"
                   "9 : Coronary : The left and right coronary arteries\n"
                   "10 : PV : The pulmonary veins\n")
    return label_names


def get_label_names_as_list():
    label_names = ["Myocardium", "LA", "LV", "RA", "RV", "Aorta", "PA", "LAA", "Coronary", "PV"]
    return label_names


def combine_segmentations_into_one_labelmap(params):
    """
    Combine segmentations into one labelmap
    """
    # input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    # stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    # hu_stats_name = f"{stats_folder}hu_statistics.json"
    # min_hu = params.get("minimum_coronary_artery_hu_value", 20)

    segm_name_hc = f"{ts_folder}heartchambers_highres.nii.gz"
    segm_name_aorta = f"{segm_folder}aorta_refined.nii.gz"
    segm_name_ca = f"{segm_folder}coronary_arteries_refined.nii.gz"
    segm_name_pv = f"{segm_folder}pv_refined.nii.gz"
    segm_name_laa = f"{segm_folder}laa_nudf_label.nii.gz"
    segm_out_name = f"{segm_folder}cardiac_combined_segmentation.nii.gz"

    if os.path.exists(segm_out_name):
        if not quiet:
            print(f"{segm_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {segm_out_name}")

    label_img_hc = io_utils.read_nifti_with_logging_cached(segm_name_hc, verbose, quiet, write_log_file, output_folder)
    if label_img_hc is None:
        return False

    label_img_aorta = io_utils.read_nifti_with_logging_cached(segm_name_aorta, verbose, quiet, write_log_file, output_folder)
    if label_img_aorta is None:
        return False

    label_img_ca = io_utils.read_nifti_with_logging_cached(segm_name_ca, verbose, quiet, write_log_file, output_folder)
    if label_img_ca is None:
        return False

    label_img_laa = io_utils.read_nifti_with_logging_cached(segm_name_laa, verbose, quiet, write_log_file, output_folder)
    if label_img_laa is None:
        return False

    label_img_pv = io_utils.read_nifti_with_logging_cached(segm_name_pv, verbose, quiet, write_log_file, output_folder)
    if label_img_pv is None:
        return False

    label_img_hc_np = sitk.GetArrayFromImage(label_img_hc).astype(np.uint8)
    label_img_aorta_np = sitk.GetArrayFromImage(label_img_aorta).astype(np.uint8)
    label_img_ca_np = sitk.GetArrayFromImage(label_img_ca).astype(np.uint8)
    label_img_laa_np = sitk.GetArrayFromImage(label_img_laa).astype(np.uint8)
    label_img_pv_np = sitk.GetArrayFromImage(label_img_pv).astype(np.uint8)

    spacing = label_img_aorta.GetSpacing()
    min_vox_size_100mm3 = int(100 / (spacing[0] * spacing[1] * spacing[2]))
    min_vox_size_1000mm3 = int(1000 / (spacing[0] * spacing[1] * spacing[2]))
    min_vox_size_5000mm3 = int(5000 / (spacing[0] * spacing[1] * spacing[2]))

    combined_segm = np.zeros_like(label_img_hc_np, dtype=np.uint8)
    combined_segm = add_segmentation_to_combined_segmentation(label_img_pv_np, combined_segm, 10, min_vox_size_1000mm3, 6)
    combined_segm = add_segmentation_to_combined_segmentation(label_img_ca_np, combined_segm, 9, min_vox_size_100mm3, 6)
    combined_segm = add_segmentation_to_combined_segmentation(label_img_aorta_np, combined_segm, 6, min_vox_size_5000mm3, 1)
    # Finally add the heart chambers
    for label_num in range(1, 8):
        if label_num != 6: # Aorta already added
            combined_segm = add_segmentation_to_combined_segmentation(label_img_hc_np == label_num, combined_segm,
                                                                  label_num, min_vox_size_1000mm3,  1)
    combined_segm = add_segmentation_to_combined_segmentation(label_img_laa_np, combined_segm, 8, min_vox_size_1000mm3, 1)

    label_img_out = sitk.GetImageFromArray(combined_segm.astype(np.uint8))
    label_img_out.CopyInformation(label_img_hc)
    sitk.WriteImage(label_img_out, segm_out_name)

    return True


def create_image_slices_from_segmentation(params):
    """
    Create image slices from segmentation
    """
    input_file = params["input_file"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    hu_stats_name = f"{stats_folder}hu_statistics.json"
    segm_in_name = f"{segm_folder}cardiac_combined_segmentation.nii.gz"
    base_name_out = f"{segm_folder}cardiac_segmentation"
    check_name = f"{base_name_out}_slice_1_rgb_crop.png"
    segm_id = params.get("segment_id_to_slice", 8)

    if os.path.exists(check_name):
        if not quiet:
            print(f"{check_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing orthogonal slices for segmentation id {segm_id} into {base_name_out}")

    label_img = io_utils.read_nifti_with_logging_cached(segm_in_name, verbose, quiet, write_log_file, output_folder)
    if label_img is None:
        return False

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    min_hu = 0
    max_hu = 500
    if os.path.exists(hu_stats_name):
        with open(hu_stats_name, "r") as f:
            hu_stats = json.load(f)
            la_q001_hu = hu_stats.get("la_hu_q001", 100000)
            pv_q001 = hu_stats.get("pv_hu_q001", 100000)
            aorta_q001 = hu_stats.get("aorta_hu_q001", 100000)
            la_q999 = hu_stats.get("la_hu_q999", 0)
            pv_q999 = hu_stats.get("pv_hu_q999", 0)
            aorta_q999 = hu_stats.get("aorta_hu_q999", 0)
            min_hu = min(la_q001_hu, pv_q001, aorta_q001, min_hu)
            max_hu = max(la_q999, pv_q999, aorta_q999, max_hu)
    if verbose:
        print(f"Using HU value range {min_hu:.0f} - {max_hu:.0f} for cardiac segmentation slices")

    ct_img_np = sitk.GetArrayFromImage(ct_img)
    label_img_np = sitk.GetArrayFromImage(label_img).astype(np.uint8)
    su.extract_orthonogonal_slices_from_given_segment(ct_img_np, label_img_np, segm_id, base_name_out, min_hu, max_hu)

    return True


def check_for_partial_organs(params):
    """
    Check if each segmentation hits the boundaries of the scan and put it into a stats json file
    """
    input_file = params["input_file"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    segm_in_name = f"{segm_folder}cardiac_combined_segmentation.nii.gz"
    low_thresh = params["out_of_reconstruction_value"]
    high_thresh = 16000
    stats_out_name = f"{stats_folder}partial_organ_info.json"

    if os.path.exists(stats_out_name):
        if not quiet:
            print(f"{stats_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {stats_out_name}")

    label_img = io_utils.read_nifti_with_logging_cached(segm_in_name, verbose, quiet, write_log_file, output_folder)
    if label_img is None:
        return False

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    ct_np = sitk.GetArrayFromImage(ct_img)
    label_img_np = sitk.GetArrayFromImage(label_img).astype(np.uint8)
    combined_mask = (low_thresh >= ct_np) | (ct_np > high_thresh)

    # mark all the sides as well
    combined_mask[:, :, 0] = True
    combined_mask[:, :, -1] = True
    combined_mask[:, 0, :] = True
    combined_mask[:, -1, :] = True
    combined_mask[0, :, :] = True
    combined_mask[-1, :, :] = True

    if verbose:
        print("Computing SDF for out-of-scan-field")
    spacing = ct_img.GetSpacing()
    sdf_mask = -edt.sdf(combined_mask, anisotropy=[spacing[2], spacing[1], spacing[0]], parallel=8)

    max_space = np.max(np.asarray(spacing))
    # overlap_dist = 1.0
    overlap_dist = max(2 * max_space, 1)

    label_names = get_label_names_as_list()
    n_labels = len(label_names)
    partial_organ_info = {}
    for label_idx in range(n_labels):
        label_num = label_idx + 1
        label_name = label_names[label_idx]
        # if verbose:
        #     print(f"Checking for partial organ: {label_name} (label {label_num})")
        mask_np = label_img_np  == label_num
        if np.sum(mask_np) == 0:
            # if verbose:
            #     print(f"  No segmentation found for {label_name} (label {label_num}) - skipping")
            partial_organ_info[f"{label_name}_present"] = False
            partial_organ_info[f"{label_name}_partial"] = False
            continue
        partial_organ_info[f"{label_name}_present"] = True

        # Check of the mask touches the side of the scan or reconstruction
        overlap_region = mask_np & (sdf_mask < overlap_dist)
        if np.sum(overlap_region) == 0:
            # if verbose:
            #     print(f"  {label_name} (label {label_num}) segmentation is complete")
            partial_organ_info[f"{label_name}_partial"] = False
        else:
            # if verbose:
            #     print(f"  {label_name} (label {label_num}) segmentation is partial")
            partial_organ_info[f"{label_name}_partial"] = True

    # Save the stats as JSON file
    with open(stats_out_name, "w") as f:
        json.dump(partial_organ_info, f, indent=4)

    return True


def generate_cardiac_mask(label_img, mask_out_name):
    """
    Generate a binary mask from the cardiac segmentation label image
    """
    # labels_to_use = [1, 2, 3, 4, 5, 8, 9]
    labels_to_use = [1, 2, 3, 8, 9]
    label_img_np = sitk.GetArrayFromImage(label_img)
    cardiac_mask_np = np.isin(label_img_np, labels_to_use).astype(np.uint8)
    spacing = label_img.GetSpacing()
    dilation_mm = 2
    dilated_mask = su.edt_based_dilation(cardiac_mask_np, spacing=[spacing[2], spacing[1], spacing[0]],
                                         radius=dilation_mm)
    cardiac_mask_img = sitk.GetImageFromArray(dilated_mask.astype(np.uint8))
    cardiac_mask_img.CopyInformation(label_img)
    sitk.WriteImage(cardiac_mask_img, mask_out_name)


def visualize_cardiac_data(params):
    input_file = params["input_file"]
    # ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    # stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    vis_folder = params["vis_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    cardiac_mask_out = f"{segm_folder}cardiac_mask.nii.gz"
    segm_name_in = f"{segm_folder}cardiac_combined_segmentation.nii.gz"
    image_base_name_in = f"{segm_folder}cardiac_segmentation"


    mask_with_cardiac_segmentation = True
    vis_file = f"{vis_folder}cardiac_visualization.png"
    win_size = params.get("rendering_window_size", [1600, 1200])

    if os.path.exists(vis_file):
        if verbose:
            print(f"{vis_file} already exists - skipping")
        return True

    if verbose:
        print(f"Creating visualization {vis_file}")

    label_img = io_utils.read_nifti_with_logging_cached(segm_name_in, verbose, quiet, write_log_file, output_folder)
    # if label_img is None:
    #     return False

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    mask_image = None
    if mask_with_cardiac_segmentation and label_img is not None:
        mask_image = cardiac_mask_out
        #if not os.path.exists(cardiac_mask_out):
        generate_cardiac_mask(label_img, cardiac_mask_out)

    render_to_file = True
    render_cardiac = RenderCardiacData(win_size, ct_img, label_img, verbose=verbose, quiet=quiet, render_to_file=render_to_file)
    render_cardiac.set_sitk_image_file(input_file, mask_image)
    render_cardiac.set_precomputed_slice(image_base_name_in)
    if render_to_file:
        render_cardiac.render_to_file(vis_file)
    else:
        render_cardiac.render_interactive()

    return True


def gather_all_statistics(params):
    """
    Gather all computed statistics into a single json file
    """
    input_file = params["input_file"]
    scan_name = params["pure_id"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    # write_log_file = params["write_log_file"]
    stats_out_name = f"{stats_folder}all_cardiac_statistics.json"
    img_stats = f"{stats_folder}input_image_statistics.json"
    hu_stats = f"{stats_folder}hu_statistics.json"
    partial_organ_stats = f"{stats_folder}partial_organ_info.json"

    if os.path.exists(stats_out_name):
        if not quiet:
            print(f"{stats_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {stats_out_name}")

    all_stats = {"scan_name": scan_name,
                "input_file": input_file,
                "output_folder": output_folder}
    try:
        tool_version = importlib.metadata.version("CardiacCTExplorer")
    except importlib.metadata.PackageNotFoundError:
        tool_version =  "unknown"
    if tool_version is not None and tool_version != "":
        all_stats["CardiacCTExplorer"] = tool_version

    last_error_message = gu.get_last_error_message()
    if last_error_message:
        all_stats["last_error_message"] = last_error_message
    else:
        all_stats["last_error_message"] = ""

    stats_files = [img_stats, hu_stats, partial_organ_stats]
    for stats_file in stats_files:
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                stats_data = json.load(f)
            all_stats.update(stats_data)

    # Dump the stats as JSON file
    with open(stats_out_name, "w") as f:
        json.dump(all_stats, f, indent=4)

    return True


def do_cardiac_analysis(params):
    """
    Compute cardiac data
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    # scan_id = params["pure_id"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    total_in_name = f"{ts_folder}total.nii.gz"

    # Do not inherit any previous error message
    gu.clear_last_error_message()
    gu.setup_vtk_error_handling(output_folder)

    if not os.path.exists(input_file):
        msg = f"Could not find {input_file} for cardiac analysis"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    ts_total_exists = os.path.exists(total_in_name)
    # ts_hc_exists = os.path.exists(hc_in_name)
    if not ts_total_exists:
        msg = f"Could not find TotalSegmentator segmentations {total_in_name} for cardiac analysis"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    # TODO: add exception handling later. Now we should see where the error occurs
    # try:
    success = True
    if success:
        success = compute_input_image_statistics(params)
    # if success:
    #     success = compute_hu_statistics(params)
    # if success:
    #     success = extract_laa_roi(params)
    # if success:
    #     success = predict_laa_with_nudf(params)
    if success:
        success = refine_pulmonary_veins(params)
    if success:
        success = combine_low_and_high_res_aorta(params)
    if success:
        success = refine_coronary_artery_aorta_overlap(params)
    if success:
        success = combine_segmentations_into_one_labelmap(params)
    if success:
        success = check_for_partial_organs(params)
    if success:
        success = create_image_slices_from_segmentation(params)

    # Visualize data even if some of the previous steps failed
    success = visualize_cardiac_data(params)

    # We gather all statistcs even if some of the previous steps failed
    success = gather_all_statistics(params)
    # except Exception as e:
    #     msg = "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
    #     msg += f"Exception during cardiac analysis of {scan_id}: {str(e)}\n"
    #     msg += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
    #     if not quiet:
    #         print(msg)
    #     if write_log_file:
    #         gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
    #     success = False

    if verbose:
        image_reader_cache_info = io_utils.read_nifti_with_logging_cached.cache_info()
        print(f"Image reader cache info: {image_reader_cache_info}")
    io_utils.read_nifti_with_logging_cached.cache_clear()

    return True


def computer_process(params, output_folder, process_queue, process_id):
    verbose = params["verbose"]

    while not process_queue.empty():
        q_size = process_queue.qsize()
        input_file = process_queue.get()
        if verbose:
            print(f"Process {process_id} running cardiac analysis on: {input_file} - {q_size} left")
        local_start_time = time.time()
        params = gu.set_and_create_folders(input_file, output_folder, params)
        do_cardiac_analysis(params)
        n_proc = params["num_proc_general"]
        elapsed_time = time.time() - local_start_time
        q_size = process_queue.qsize()
        est_time_left = q_size * elapsed_time / n_proc
        time_left_str = gu.display_time(int(est_time_left))
        time_elapsed_str = gu.display_time(int(elapsed_time))
        if verbose:
            print("=================================================================================================")
            print(f"Process {process_id} done with {input_file} - took {time_elapsed_str}.\n"
                  f"Time left {time_left_str} for {q_size} scans (if {n_proc} processes alive)")
            print("=================================================================================================")
        stats_folder = params["stats_folder"]
        time_stats_out = f"{stats_folder}cardiac_proc_time.txt"
        with open(time_stats_out, "w") as f:
            f.write(f"{elapsed_time}\n")


# def setup_nudf_folder_and_get_checkpoint(params):
#     """
#     Setup NUDF model folder and get checkpoint file
#     """
#     verbose = params["verbose"]
#
#     nudf_model_url = params["nudf_model_url"]
#     nudf_checkpoint = params["nudf_checkpoint"]
#     nudf_model_folder = params.get("nudf_model_folder", "")
#     if nudf_model_folder == "":
#         # Find home directory
#         home_dir = str(Path.home())
#         nudf_model_folder = os.path.join(home_dir, ".cardiacctexplorer", "nudf_model")
#         if verbose:
#             print(f"NUDF model folder not specified - setting it to default: {nudf_model_folder}")
#     params["nudf_model_folder"] = nudf_model_folder
#
#     checkpoint_file = os.path.join(nudf_model_folder, nudf_checkpoint)
#     params["nudf_checkpoint_file"] = checkpoint_file
#     if os.path.exists(checkpoint_file):
#         if verbose:
#             print(f"NUDF checkpoint file already exists: {checkpoint_file}")
#         return params
#     if not os.path.exists(nudf_model_folder):
#         os.makedirs(nudf_model_folder)
#     if verbose:
#         print(f"Downloading NUDF model checkpoint from {nudf_model_url} to {checkpoint_file}")
#     load_url(f"{nudf_model_url}{nudf_checkpoint}", model_dir=nudf_model_folder, file_name=nudf_checkpoint,
#              progress=verbose)
#     if not os.path.exists(checkpoint_file):
#         msg = f"Could not download NUDF model checkpoint to {checkpoint_file}"
#         if not params["quiet"]:
#             print(msg)
#         if params["write_log_file"]:
#             gu.write_message_to_log_file(base_dir=params["output_folder"], message=msg, level="error")
#         return False
#     return params
#


def cardiac_analysis(in_files, output_folder, params):
    verbose = params["verbose"]
    # params = setup_nudf_folder_and_get_checkpoint(params)

    num_processes = params.get("num_proc_general", 1)

    if verbose:
        print(f"Computing cardiac data with max {num_processes} processes on {len(in_files)} files. Output to {output_folder}")

    # no need to spawn more processes than files
    num_processes = min(num_processes, len(in_files))

    files_to_process = []
    for fname in in_files:
        params = gu.set_and_create_folders(fname, output_folder, params)
        stats_folder = params["stats_folder"]
        stats_file = f"{stats_folder}/all_cardiac_statistics.json"
        if not os.path.exists(stats_file):
            files_to_process.append(fname)
    if verbose:
        print(f"Found {len(files_to_process)} files to compute cardiac analysis out of {len(in_files)} files")

    in_files = files_to_process
    if len(in_files) == 0:
        if verbose:
            print("No files to compute cardiac analysis on  - all done!")
        return

    # no need to do multiprocessing for one file
    if len(in_files) == 1:
        input_file = in_files[0].strip()
        if verbose:
            print(f"Running cardiac analysis on: {input_file}")
        local_start_time = time.time()
        params = gu.set_and_create_folders(input_file, output_folder, params)
        do_cardiac_analysis(params)
        elapsed_time = time.time() - local_start_time
        elapsed_time_str = gu.display_time(int(elapsed_time))
        if verbose:
            print(f"Done with {input_file} - took {elapsed_time_str}")
        stats_folder = params["stats_folder"]
        time_stats_out = f"{stats_folder}cardiac_proc_time.txt"
        with open(time_stats_out, "w") as f:
            f.write(f"{elapsed_time}\n")
    else:
        process_queue = mp.Queue()
        for idx in in_files:
            input_file = idx.strip()
            process_queue.put(input_file)

        if verbose:
            print(f"Starting {num_processes} processes")

        processes = []
        for i in range(num_processes):
            p = mp.Process(target=computer_process, args=(params, output_folder, process_queue, i + 1))
            p.start()
            processes.append(p)

        if verbose:
            print("Waiting for processes to finish")
        for p in processes:
            p.join()
