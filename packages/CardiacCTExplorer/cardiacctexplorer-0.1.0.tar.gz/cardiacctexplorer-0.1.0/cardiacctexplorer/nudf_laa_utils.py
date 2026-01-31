"""Utilities to compute left atrial appendage segmentation using the NUDF model"""
import os
from pathlib import Path
import time
import json
import multiprocessing as mp
import SimpleITK as sitk
import numpy as np
from scipy.ndimage import measurements
from torch.utils.model_zoo import load_url
from totalsegmentator.python_api import select_device
import cardiacctexplorer.general_utils as gu
import cardiacctexplorer.io_utils as io_utils
import cardiacctexplorer.segmentation_utils as su
from cardiacctexplorer.nudf_predictor import NUDFPredictor


def compute_mask_hu_statistics(ct_img_np, mask, spacing, anatomy_name, segm_name, params, hu_stats):
    quiet = params["quiet"]
    # verbose = params["verbose"]
    output_folder = params["output_folder"]
    write_log_file = params["write_log_file"]
    out_of_scan_value = params.get("out_of_reconstruction_value", -2048)

    # Remove the part of the mask, where the image values are below out_of_scan_value + 1
    mask = np.logical_and(mask, ct_img_np > out_of_scan_value + 1)

    if np.sum(mask) == 0:
        msg = f"Could not find {anatomy_name} label in TotalSegmentator segmentation {segm_name}."
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    erosion_diam = 2  # in mm
    mask_eroded = su.edt_based_erosion(mask, [spacing[2], spacing[1], spacing[0]], erosion_diam)
    if np.sum(mask_eroded) == 0:
        msg = f"Could not find {anatomy_name} label in TotalSegmentator segmentation {segm_name} after erosion."
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    # Need to cast into floats and ints to avoid types that can not be written to JSON
    hu_vals = ct_img_np[mask_eroded]
    hu_stats[f"{anatomy_name}_vox_count"] = len(hu_vals)
    hu_stats[f"{anatomy_name}_hu_mean"] = float(np.mean(hu_vals))
    hu_stats[f"{anatomy_name}_hu_std"] = float(np.std(hu_vals))
    hu_stats[f"{anatomy_name}_hu_med"] = int(np.median(hu_vals))
    hu_stats[f"{anatomy_name}_hu_min"] = int(np.min(hu_vals))
    hu_stats[f"{anatomy_name}_hu_max"] = int(np.max(hu_vals))
    hu_stats[f"{anatomy_name}_hu_q01"] = int(np.percentile(hu_vals, 1))
    hu_stats[f"{anatomy_name}_hu_q99"] = int(np.percentile(hu_vals, 99))
    hu_stats[f"{anatomy_name}_hu_q001"] = int(np.percentile(hu_vals, 0.1))
    hu_stats[f"{anatomy_name}_hu_q999"] = int(np.percentile(hu_vals, 99.9))
    return True


def compute_hu_statistics(params):
    """
    Compute Hounsfield unit statistics in known regions of the heart
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    stats_folder = params["stats_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]

    segm_name_total = f"{ts_folder}total.nii.gz"
    segm_name_hc = f"{ts_folder}heartchambers_highres.nii.gz"
    stats_out_name = f"{stats_folder}hu_statistics.json"
    la_segm_id = 2
    pv_segm_id = 53
    aorta_segm_id = 6

    if os.path.exists(stats_out_name):
        if not quiet:
            print(f"{stats_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {stats_out_name}")

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
    pv_mask = label_img_total_np == pv_segm_id
    la_mask = label_img_hc_np == la_segm_id
    aorta_mask = label_img_hc_np == aorta_segm_id
    spacing = label_img_total.GetSpacing()

    hu_stats = {}
    compute_mask_hu_statistics(ct_img_np, pv_mask, spacing, "pv", segm_name_total,
                                         params, hu_stats)
    compute_mask_hu_statistics(ct_img_np, la_mask, spacing, "la", segm_name_hc,
                                         params, hu_stats)
    compute_mask_hu_statistics(ct_img_np, aorta_mask, spacing, "aorta", segm_name_hc,
                                         params, hu_stats)

    json_object = json.dumps(hu_stats, indent=4)
    with open(stats_out_name, "w") as outfile:
        outfile.write(json_object)
    return True


def extract_laa_roi(params):
    """
    Extract the region around the left atrial appendage
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    # scan_id = params["pure_id"]
    crops_folder = params["crops_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]

    segm_name_total = f"{ts_folder}total.nii.gz"
    crop_out_name = f"{crops_folder}laa_roi.nii.gz"
    # crop_out_name_np = f"{crops_folder}laa_roi.npy"
    laa_label_id = 61

    if os.path.exists(crop_out_name):
        if not quiet:
            print(f"{crop_out_name} already exists - skipping")
        return True

    if verbose:
        print(f"Computing {crop_out_name}")

    if not os.path.exists(segm_name_total):
        msg = f"TotalSegmentator segmentation {segm_name_total} not found. Can not extract LAA ROI."
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False
    label_img_total = io_utils.read_nifti_with_logging_cached(segm_name_total, verbose, quiet, write_log_file, output_folder)
    if label_img_total is None:
        return False

    ct_img = io_utils.read_nifti_with_logging_cached(input_file, verbose, quiet, write_log_file, output_folder)
    if ct_img is None:
        return False

    # ct_np = sitk.GetArrayFromImage(ct_img)
    label_img_total_np = sitk.GetArrayFromImage(label_img_total)
    laa_mask = label_img_total_np == laa_label_id

    if np.sum(laa_mask) == 0:
        msg = f"Could not find LAA label in TotalSegmentator segmentation {segm_name_total}."
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    spacing = label_img_total.GetSpacing()
    # We want at least 1 cubic centimeter
    min_comp_size_mm3 = 1000
    min_comp_size_vox = int(min_comp_size_mm3 / (spacing[0] * spacing[1] * spacing[2]))
    if verbose:
        print(f"Finding LAA components with min_comp_size: {min_comp_size_vox} voxels = {min_comp_size_mm3:.1f} mm^3")

    components = su.get_components_over_certain_size_as_individual_volumes(laa_mask, min_comp_size_vox, 1)
    if components is None or len(components) == 0:
        msg = f"Could not find any components of size > {min_comp_size_mm3} mm3 in {segm_name_total}"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    laa_mask = components[0]

    com_np = measurements.center_of_mass(laa_mask)
    # Do the transpose of the coordinates (SimpleITK vs. numpy)
    com_np = [com_np[2], com_np[1], com_np[0]]
    com_phys = label_img_total.TransformIndexToPhysicalPoint([int(com_np[0]), int(com_np[1]), int(com_np[2])])

    side_length_mm = 70
    nvox = 128

    # Create the sampled image with same direction
    direction = ct_img.GetDirection()

    # Desired voxel spacing for new image
    new_spacing = [side_length_mm / nvox, side_length_mm / nvox, side_length_mm / nvox]

    com = com_phys
    dir_x = direction[0]
    dir_y = direction[4]
    dir_z = direction[8]
    # print(f"Directions: {dir_x} {dir_y} {dir_z}")
    new_origin_x = com[0] - dir_x * side_length_mm / 2
    new_origin_y = com[1] - dir_y * side_length_mm  / 2
    new_origin_z = com[2] - dir_z * side_length_mm / 2
    # print(f"New origin: {new_origin_x} {new_origin_y} {new_origin_z}")

    new_size = [nvox, nvox, nvox]
    new_image = sitk.Image(new_size, ct_img.GetPixelIDValue())
    new_image.SetOrigin([new_origin_x, new_origin_y, new_origin_z])
    new_image.SetSpacing(new_spacing)
    new_image.SetDirection(direction)

    # Make translation with no offset, since sitk.Resample needs this arg.
    translation = sitk.TranslationTransform(3)
    translation.SetOffset((0, 0, 0))

    default_value = -2048.0
    interpolator = sitk.sitkLinear
    # Create final resampled image
    resampled_image = sitk.Resample(ct_img, new_image, translation, interpolator, default_value)
    sitk.WriteImage(resampled_image, crop_out_name)

    # occ_np = sitk.GetArrayViewFromImage(resampled_image)
    # occ_np = np.flip(occ_np, 2)
    # np.save(crop_out_name_np, occ_np)

    return True


def predict_laa_with_nudf(params):
    """
    Predict the labelmap of the left atrial appendage using the NUDF model
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    crops_folder = params["crops_folder"]
    stats_folder = params["stats_folder"]
    segm_folder = params["segm_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    device_in = params["device"]
    min_hu = params.get("minimum_laa_hu_value", 200)
    crop_name_in = f"{crops_folder}laa_roi.nii.gz"
    sdf_out_name = f"{segm_folder}laa_nudf_sdf.nii.gz"
    crop_label_out_name = f"{segm_folder}laa_nudf_label_crop.nii.gz"
    laa_label_out_name = f"{segm_folder}laa_nudf_label.nii.gz"
    segm_name_total = f"{ts_folder}total.nii.gz"
    hu_stats_name = f"{stats_folder}hu_statistics.json"

    debug = False

    if verbose:
        print(f"Computing LAA prediction with NUDF for {input_file}")
    if os .path.exists(laa_label_out_name):
        if verbose:
            print(f"{laa_label_out_name} already exists - skipping")
        return True

    # Read HU statistics to adjust min_hu if needed
    if os.path.exists(hu_stats_name):
        with open(hu_stats_name, "r") as f:
            hu_stats = json.load(f)
        la_q001_hu = hu_stats.get("la_hu_q001", 100000)
        pv_q001 = hu_stats.get("pv_hu_q001", 100000)
        aorta_q001 = hu_stats.get("aorta_hu_q001", 100000)
        min_hu = min(la_q001_hu, pv_q001, aorta_q001, min_hu)
    if verbose:
        print(f"Using minimum HU value of {min_hu} for LAA prediction")

    device = select_device(device_in)

    crop_img = io_utils.read_nifti_with_logging_cached(crop_name_in, verbose, quiet, write_log_file, output_folder)
    if crop_img is None:
        return False

    crop_img_np = sitk.GetArrayFromImage(crop_img)
    # Flip to make compatible with NUDF input
    crop_img_np = np.flip(crop_img_np, 2)
    # HU normalization
    crop_normalized = np.clip(crop_img_np, -1000, 1000) / 1000
    # Reshape to add channel dimension
    input_data = np.expand_dims(crop_normalized, axis=0)

    # TODO: Get from config
    resolution = 128
    batch_points = 100000
    checkpoint_file = params["nudf_checkpoint_file"]

    nudf_predictor = NUDFPredictor(checkpoint_file, device=device, resolution=resolution, batch_points=batch_points)

    if verbose:
        print("Setting up NUDF model")
    if not nudf_predictor.setup_model():
        msg = "Could not set up NUDF model for LAA prediction."
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    data = {'inputs': np.array(input_data, dtype=np.float32)}

    if verbose:
        print("Running NUDF prediction")
    logits, _ = nudf_predictor.predict(data)

    # Export SDF
    dim = (np.round(len(logits)**(1/3)).astype(int),)*3
    numpy_3d_sdf_tensor = np.reshape(logits,dim)

    # Flip to get correct orientation
    numpy_3d_sdf_tensor = np.flip(numpy_3d_sdf_tensor, 2)
    if debug:
        img_sdf = sitk.GetImageFromArray(numpy_3d_sdf_tensor)
        img_sdf.CopyInformation(crop_img)
        sitk.WriteImage(img_sdf, sdf_out_name)

    if verbose:
        print("Generating LAA label from SDF")

    # Generate label volume
    laa_label_np = (numpy_3d_sdf_tensor < 0).astype(np.uint8)

    # Flip crop image back to original orientation
    crop_img_np = np.flip(crop_img_np, 2)
    # Should have a minimum HU to be considered part of LAA
    laa_label_np[crop_img_np <= min_hu] = 0

    spacing = crop_img.GetSpacing()
    # We want at least 1 cubic centimeter
    min_comp_size_mm3 = 1000
    min_comp_size_vox = int(min_comp_size_mm3 / (spacing[0] * spacing[1] * spacing[2]))
    if verbose:
        print(f"Finding LAA components with min_comp_size: {min_comp_size_vox} voxels = {min_comp_size_mm3:.1f} mm^3")

    components = su.get_components_over_certain_size_as_individual_volumes(laa_label_np, min_comp_size_vox, 1)
    if components is None or len(components) == 0:
        msg = f"Could not find any components of size > {min_comp_size_mm3} mm3 in {segm_name_total}"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    laa_mask = components[0]
    laa_mask_sitk = sitk.GetImageFromArray(laa_mask.astype(np.uint8))
    laa_mask_sitk.CopyInformation(crop_img)
    if debug:
        sitk.WriteImage(laa_mask_sitk, crop_label_out_name)

    # Read total segmentation to place LAA label in correct location
    label_img_total = io_utils.read_nifti_with_logging_cached(segm_name_total, verbose, quiet, write_log_file, output_folder)
    if label_img_total is None:
        return False

    # Resample LAA label to original image size and spacing
    original_size = label_img_total.GetSize()
    original_spacing = label_img_total.GetSpacing()
    original_origin = label_img_total.GetOrigin()
    original_direction = label_img_total.GetDirection()
    new_image = sitk.Image(original_size, laa_mask_sitk.GetPixelIDValue())
    new_image.SetOrigin(original_origin)
    new_image.SetSpacing(original_spacing)
    new_image.SetDirection(original_direction)
    # Make translation with no offset, since sitk.Resample needs this arg.
    translation = sitk.TranslationTransform(3)
    translation.SetOffset((0, 0, 0))
    default_value = 0
    interpolator = sitk.sitkNearestNeighbor
    # Create final resampled image
    resampled_image = sitk.Resample(laa_mask_sitk, new_image, translation, interpolator, default_value)

    laa_resampled_np = sitk.GetArrayFromImage(resampled_image)
    # Remove the LAA part that is covered by the total segmentation
    label_img_total_np = sitk.GetArrayFromImage(label_img_total)
    label_img_total_not_laa = (label_img_total_np > 0) & (label_img_total_np != 61) & (label_img_total_np != 51)
    laa_resampled_np = np.bitwise_and(laa_resampled_np, np.bitwise_not(label_img_total_not_laa))

    laa_label_np = laa_resampled_np == 1
    components = su.get_components_over_certain_size_as_individual_volumes(laa_label_np, min_comp_size_vox, 1)
    if components is None or len(components) == 0:
        msg = f"Could not find any components of size > {min_comp_size_mm3} mm3 in {segm_name_total}"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    laa_mask = components[0]
    laa_mask_sitk = sitk.GetImageFromArray(laa_mask.astype(np.uint8))
    laa_mask_sitk.CopyInformation(resampled_image)

    sitk.WriteImage(laa_mask_sitk, laa_label_out_name)

    return True


def do_nudf_laa(params):
    """
    Compute LAA segmentation using NUDF
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    total_in_name = f"{ts_folder}total.nii.gz"

    # Do not inherit any previous error message
    gu.clear_last_error_message()
    gu.setup_vtk_error_handling(output_folder)

    if not os.path.exists(input_file):
        msg = f"Could not find {input_file} for NUDF LAA analysis"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    ts_total_exists = os.path.exists(total_in_name)
    if not ts_total_exists:
        msg = f"Could not find TotalSegmentator segmentations {total_in_name} for NUDF LAA analysis"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        return False

    try:
        success = True
        if success:
            success = compute_hu_statistics(params)
        if success:
            success = extract_laa_roi(params)
        if success:
            success = predict_laa_with_nudf(params)
    except Exception as e:
        msg = "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
        msg += f"Exception during NUDF LAA analysis of {input_file}: {str(e)}\n"
        msg += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
        success = False

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
            print(f"Process {process_id} running NUDF LAA analysis on: {input_file} - {q_size} left")
        local_start_time = time.time()
        params = gu.set_and_create_folders(input_file, output_folder, params)
        do_nudf_laa(params)
        n_proc = params["num_proc_nudf"]
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
        time_stats_out = f"{stats_folder}nudf_laa_proc_time.txt"
        with open(time_stats_out, "w") as f:
            f.write(f"{elapsed_time}\n")


def setup_nudf_folder_and_get_checkpoint(params):
    """
    Setup NUDF model folder and get checkpoint file
    """
    verbose = params["verbose"]

    nudf_model_url = params["nudf_model_url"]
    nudf_checkpoint = params["nudf_checkpoint"]
    nudf_model_folder = params.get("nudf_model_folder", "")
    if nudf_model_folder == "":
        # Find home directory
        home_dir = str(Path.home())
        nudf_model_folder = os.path.join(home_dir, ".cardiacctexplorer", "nudf_model")
        if verbose:
            print(f"NUDF model folder not specified - setting it to default: {nudf_model_folder}")
    params["nudf_model_folder"] = nudf_model_folder

    checkpoint_file = os.path.join(nudf_model_folder, nudf_checkpoint)
    params["nudf_checkpoint_file"] = checkpoint_file
    if os.path.exists(checkpoint_file):
        if verbose:
            print(f"NUDF checkpoint file already exists: {checkpoint_file}")
        return params
    if not os.path.exists(nudf_model_folder):
        os.makedirs(nudf_model_folder)
    if verbose:
        print(f"Downloading NUDF model checkpoint from {nudf_model_url} to {checkpoint_file}")
    load_url(f"{nudf_model_url}{nudf_checkpoint}", model_dir=nudf_model_folder, file_name=nudf_checkpoint,
             progress=verbose)
    if not os.path.exists(checkpoint_file):
        msg = f"Could not download NUDF model checkpoint to {checkpoint_file}"
        if not params["quiet"]:
            print(msg)
        if params["write_log_file"]:
            gu.write_message_to_log_file(base_dir=params["output_folder"], message=msg, level="error")
        return False
    return params


def nudf_laa_analysis(in_files, output_folder, params):
    verbose = params["verbose"]
    params = setup_nudf_folder_and_get_checkpoint(params)

    num_processes = params.get("num_proc_nudf", 1)

    if verbose:
        print(f"Computing NUDF LAA with max {num_processes} processes on {len(in_files)} files. Output to {output_folder}")

    # no need to spawn more processes than files
    num_processes = min(num_processes, len(in_files))

    files_to_process = []
    for fname in in_files:
        params = gu.set_and_create_folders(fname, output_folder, params)
        segm_folder = params["segm_folder"]
        segm_file = f"{segm_folder}/laa_nudf_label.nii.gz"
        if not os.path.exists(segm_file):
            files_to_process.append(fname)
    if verbose:
        print(f"Found {len(files_to_process)} files to compute NUDF LAA out of {len(in_files)} files")

    in_files = files_to_process
    if len(in_files) == 0:
        if verbose:
            print("No files to compute NUDF LAA on  - all done!")
        return

    # no need to do multiprocessing for one file
    if len(in_files) == 1:
        input_file = in_files[0].strip()
        if verbose:
            print(f"Running NUDF LAA on: {input_file}")
        local_start_time = time.time()
        params = gu.set_and_create_folders(input_file, output_folder, params)
        do_nudf_laa(params)
        elapsed_time = time.time() - local_start_time
        elapsed_time_str = gu.display_time(int(elapsed_time))
        if verbose:
            print(f"Done with {input_file} - took {elapsed_time_str}")
        stats_folder = params["stats_folder"]
        time_stats_out = f"{stats_folder}nudf_laa_proc_time.txt"
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
