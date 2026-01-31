"""Utils for running TotalSegmentator segmentations"""
import os
import time
import multiprocessing as mp
import SimpleITK as sitk
import numpy as np
from totalsegmentator.python_api import totalsegmentator
import cardiacctexplorer.general_utils as gu
import cardiacctexplorer.io_utils as io_utils


def do_totalsegmentator(params):
    """
    Use TotalSegmentator to compute segmentations
    input_file: full path to input file
    """
    input_file = params["input_file"]
    ts_folder = params["ts_folder"]
    output_folder = params["output_folder"]
    quiet = params["quiet"]
    verbose = params["verbose"]
    write_log_file = params["write_log_file"]
    device = params.get("device_totalsegmentator", "gpu")

    # Do not inherit any previous error message
    gu.clear_last_error_message()

    if not os.path.exists(input_file):
        msg = f"Could not find {input_file} for TotalSegmentator"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(
                base_dir=output_folder, message=msg, level="error"
            )
        return False

    total_out_name = f"{ts_folder}total.nii.gz"
    hc_out_name = f"{ts_folder}heartchambers_highres.nii.gz"
    ca_out_name = f"{ts_folder}coronary_arteries.nii.gz"

    # Nr of threads for resampling
    nr_thr_resamp = 1
    # Nr of threads for saving segmentations
    nr_thr_saving = 1
    # Run faster lower resolution model
    fast_model = False

    # Calc volume (in mm3) and mean intensity. Results will be in statistics.json
    calc_statistics = False
    # Calc radiomics features. Requires pyradiomics. Results will be in statistics_radiomics.json
    calc_radiomics = False
    # Do initial rough body segmentation and crop image to body region
    body_seg = False
    # Process image in 3 chunks for less memory consumption
    force_split = False
    run_quit = quiet
    multi_label = True

    if not os.path.exists(total_out_name):
        # First the total task to get the main segmentation
        task = "total"
        try:
            totalsegmentator(
                input_file,
                total_out_name,
                multi_label,
                nr_thr_resamp,
                nr_thr_saving,
                fast_model,
                device=device,
                nora_tag="None",
                preview=False,
                task=task,
                roi_subset=None,
                statistics=calc_statistics,
                radiomics=calc_radiomics,
                crop_path=None,
                body_seg=body_seg,
                force_split=force_split,
                output_type="nifti",
                quiet=run_quit,
                verbose=verbose,
                test=False,
            )
        except Exception as e:
            msg = f"TotalSegmentator (total) failed on {input_file} with exception: {str(e)}"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(
                    base_dir=output_folder, message=msg, level="error"
                )
            return False
    elif verbose:
        print(f"{total_out_name} already exists - skipping!")

    # Check if the output segmentation is present and of reasonable size
    if not os.path.exists(total_out_name):
        msg = f"Could not find {total_out_name} after TotalSegmentator run"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(
                base_dir=output_folder, message=msg, level="error"
            )
        return False

    # Check if the heart is present in the total segmentation masks
    # Square millimeters - one square centimeter
    heart_present_in_total = False
    volume_threshold = 1000
    heart_label = 51
    label_img = io_utils.read_nifti_with_logging(
        total_out_name, verbose, quiet, write_log_file, output_folder
    )
    # Something is really wrong if total segmentation cannot be read
    if label_img is None:
        return False
    spacing = label_img.GetSpacing()
    vox_size = spacing[0] * spacing[1] * spacing[2]
    label_img_np = sitk.GetArrayFromImage(label_img)
    mask_np = label_img_np == heart_label
    sum_pix = np.sum(mask_np)
    if sum_pix * vox_size < volume_threshold:
        msg = (f"Heart segmentation volume {sum_pix * vox_size:.1f} mm3 is below threshold {volume_threshold} mm3 "
               f"for {input_file} - skipping high-res heart and coronary artery segmentation!")
        if verbose:
            print(msg)
    else:
        heart_present_in_total = True

    if heart_present_in_total and not os.path.exists(hc_out_name):
        task = "heartchambers_highres"
        try:
            totalsegmentator(
                input_file,
                hc_out_name,
                multi_label,
                nr_thr_resamp,
                nr_thr_saving,
                fast_model,
                device=device,
                nora_tag="None",
                preview=False,
                task=task,
                roi_subset=None,
                statistics=calc_statistics,
                radiomics=calc_radiomics,
                crop_path=None,
                body_seg=body_seg,
                force_split=force_split,
                output_type="nifti",
                quiet=run_quit,
                verbose=verbose,
                test=False,
            )
        except Exception as e:
            msg = f"TotalSegmentator (heartchambers_highres) failed on {input_file} with exception: {str(e)}"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(
                    base_dir=output_folder, message=msg, level="error"
                )
            return False
        if not os.path.exists(hc_out_name):
            msg = f"Could not find {hc_out_name} after TotalSegmentator run"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(
                    base_dir=output_folder, message=msg, level="warning"
                )
    elif verbose:
        print(f"{hc_out_name} already exists - skipping!")

    if heart_present_in_total and not os.path.exists(ca_out_name):
        # Check if the heart is present in the segmentation
        # Square millimeters - one square centimeter
        volume_threshold = 1000
        heart_label = 51

        label_img = io_utils.read_nifti_with_logging(
            total_out_name, verbose, quiet, write_log_file, output_folder
        )
        if label_img is None:
            return False

        spacing = label_img.GetSpacing()
        vox_size = spacing[0] * spacing[1] * spacing[2]
        label_img_np = sitk.GetArrayFromImage(label_img)
        mask_np = label_img_np == heart_label
        sum_pix = np.sum(mask_np)
        if sum_pix * vox_size < volume_threshold:
            msg = f"Heart segmentation volume {sum_pix * vox_size:.1f} mm3 is below threshold {volume_threshold} mm3 for {input_file} - skipping high-res heart segmentation!"
            if not quiet:
                print(msg)
            # if write_log_file:
            #     write_message_to_log_file(base_dir=output_folder, message=msg, level="info")
            return True

        task = "coronary_arteries"
        try:
            totalsegmentator(
                input_file,
                ca_out_name,
                multi_label,
                nr_thr_resamp,
                nr_thr_saving,
                fast_model,
                device=device,
                nora_tag="None",
                preview=False,
                task=task,
                roi_subset=None,
                statistics=calc_statistics,
                radiomics=calc_radiomics,
                crop_path=None,
                body_seg=body_seg,
                force_split=force_split,
                output_type="nifti",
                quiet=run_quit,
                verbose=verbose,
                test=False,
            )
        except Exception as e:
            msg = f"TotalSegmentator (coronary_arteries) failed on {input_file} with exception: {str(e)}"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(
                    base_dir=output_folder, message=msg, level="error"
                )
            return False
        if not os.path.exists(ca_out_name):
            msg = f"Could not find {ca_out_name} after TotalSegmentator run"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(
                    base_dir=output_folder, message=msg, level="warning"
                )
    elif verbose:
        print(f"{ca_out_name} already exists - skipping!")

    return True


def computer_process(params, output_folder, process_queue, process_id):
    verbose = params.get("verbose", False)
    # quiet = params.get("quiet", False)
    # write_log_file = params.get("write_log_file", False)
    # device = params.get("device_totalsegmentator", "gpu")
    nr_ts = params.get("num_proc_total_segmentator", 1)

    while not process_queue.empty():
        q_size = process_queue.qsize()
        input_file = process_queue.get()
        if verbose:
            print(f"Process {process_id} running TotalSegmentator on: {input_file} - {q_size} left")
        local_start_time = time.time()
        params = gu.set_and_create_folders(input_file, output_folder, params)
        do_totalsegmentator(params)
        elapsed_time = time.time() - local_start_time
        stats_folder = params["stats_folder"]
        time_stats_out = f"{stats_folder}totalsegmentator_proc_time.txt"
        with open(time_stats_out, "w") as f:
            f.write(f"{elapsed_time}\n")

        q_size = process_queue.qsize()
        est_time_left = q_size * elapsed_time / nr_ts
        time_left_str = gu.display_time(int(est_time_left))
        time_elapsed_str = gu.display_time(int(elapsed_time))
        if verbose:
            print(f"Process {process_id} done with {input_file} - took {time_elapsed_str}.\n"
                  f"Time left {time_left_str} for {q_size} scans (if {nr_ts} processes alive)")


def compute_totalsegmentator_segmentations(in_files, output_folder, params):
    verbose = params.get("verbose", False)
    # quiet = params.get("quiet", False)
    # write_log_file = params.get("write_log_file", False)
    nr_ts = params.get("num_proc_total_segmentator", 1)
    device = params.get("device_totalsegmentator", "gpu")
    if verbose:
        print(f"Computing TotalSegmentator segmentations with max {nr_ts} processes on device {device} "
              f"on {len(in_files)} files. Output to {output_folder}")

    num_processes = nr_ts
    # no need to spawn more processes than files
    num_processes = min(num_processes, len(in_files))

    files_to_process = []
    for fname in in_files:
        params = gu.set_and_create_folders(fname, output_folder, params)
        ts_folder = params["ts_folder"]
        total_out_name = f"{ts_folder}total.nii.gz"
        hc_out_name = f"{ts_folder}heartchambers_highres.nii.gz"
        ca_out_name = f"{ts_folder}coronary_arteries.nii.gz"

        # TODO: Perhaps only necessary to check the total task
        check_names = [total_out_name, hc_out_name, ca_out_name]
        all_exist = all([os.path.exists(cname) for cname in check_names])
        if not all_exist:
            files_to_process.append(fname)
        #
        # if not os.path.exists(total_out_name):
        #     files_to_process.append(fname)

    if verbose:
        print(f"Found {len(files_to_process)} files to process with TotalSegmentator out of {len(in_files)} files")

    in_files = files_to_process
    if len(in_files) == 0:
        if verbose:
            print("No files to process with TotalSegmentator - all done!")
        return

    # no need to do multiprocessing for one file
    if len(in_files) == 1:
        input_file = in_files[0].strip()
        if verbose:
            print(f"Running TotalSegmentator on: {input_file}")
        local_start_time = time.time()
        params = gu.set_and_create_folders(input_file, output_folder, params)
        do_totalsegmentator(params)

        elapsed_time = time.time() - local_start_time
        elapsed_time_str = gu.display_time(int(elapsed_time))
        if verbose:
            print(f"Done with {input_file} - took {elapsed_time_str}")
        stats_folder = params["stats_folder"]
        time_stats_out = f"{stats_folder}totalsegmentator_proc_time.txt"
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
