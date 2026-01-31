"""File conversion utilities. Mostly DICOM and NRRD to NIfTI conversion."""
import os
from pathlib import Path
import time
import multiprocessing as mp
import SimpleITK as sitk
import dicom2nifti as d2n
import cardiacctexplorer.general_utils as gu



def do_convert(output_folder, input_file, params):
    verbose = params.get("verbose", False)
    quiet = params.get("quiet", False)
    write_log_file = params.get("write_log_file", False)

    # Do not inherit any previous error message
    gu.clear_last_error_message()
    pure_id = gu.get_pure_scan_file_name(input_file)
    conv_output_folder = f"{output_folder}{pure_id}/NIFTI/"
    conv_out_name = f"{conv_output_folder}{pure_id}.nii.gz"
    Path(conv_output_folder).mkdir(parents=True, exist_ok=True)
    hu_offset = 0
    if params is not None:
        hu_offset = params.get("hounsfield_unit_offset", 0)

    # Check if input is nrrd file
    if input_file.lower().endswith(".nrrd"):
        try:
            # Read nrrd file with SimpleITK
            sitk_image = sitk.ReadImage(input_file)
            if hu_offset != 0:
                # Apply HU offset
                sitk_image = sitk.Cast(sitk_image, sitk.sitkInt16)
                sitk_image = sitk_image + hu_offset

            # Write as NIfTI
            sitk.WriteImage(sitk_image, conv_out_name)
            if verbose:
                print(f"Converted NRRD file {input_file} to NIfTI file {conv_out_name} with HU offset {hu_offset}")
        except Exception as e:
            msg = f"Failed to convert NRRD file {input_file} to NIfTI: {e}"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
            return False
    else:
        try:
            d2n.dicom_series_to_nifti(input_file, conv_out_name, reorient_nifti=True)
        except Exception as e:
            msg = f"Failed to convert DICOM folder {input_file} to NIfTI: {e}"
            if not quiet:
                print(msg)
            if write_log_file:
                gu.write_message_to_log_file(base_dir=output_folder, message=msg, level="error")
            return False
    return True


def computer_process(params, output_folder, process_queue, process_id):
    verbose = params.get("verbose", False)
    # quiet = params.get("quiet", False)
    # write_log_file = params.get("write_log_file", False)

    while not process_queue.empty():
        q_size = process_queue.qsize()
        input_file = process_queue.get()
        if verbose:
            print(f"Process {process_id} converting: {input_file} - {q_size} left")
        local_start_time = time.time()
        do_convert(output_folder, input_file, params)
        elapsed_time = time.time() - local_start_time
        params = gu.set_and_create_folders(input_file, output_folder, params)
        stats_folder = params["stats_folder"]
        time_stats_out = f"{stats_folder}conversion_time.txt"
        with open(time_stats_out, "w") as f:
            f.write(f"{elapsed_time}\n")

        q_size = process_queue.qsize()
        est_time_left = q_size * elapsed_time
        time_left_str = gu.display_time(int(est_time_left))
        time_elapsed_str = gu.display_time(int(elapsed_time))
        if verbose:
            print(f"Process {process_id} done with {input_file} - took {time_elapsed_str}.\n"
                  f"Time left {time_left_str} for {q_size} scans (if only one process)")
    return True

def convert_input_files(in_files, output_folder, params):
    verbose = params.get("verbose", False)
    # quiet = params.get("quiet", False)
   # write_log_file = params.get("write_log_file", False)

    if verbose:
        print(f"Converting {len(in_files)} files. Output to {output_folder}")

    num_processes = params.get("num_proc_general", 1)
    # no need to spawn more processes than files
    num_processes = min(num_processes, len(in_files))

    files_to_process = []
    output_files = []
    for fname in in_files:
        # Get extension and check if it is an nrrd file or if it is a DICOM folder
        is_nrrd = fname.lower().endswith(".nrrd")
        if is_nrrd and not os.path.isfile(fname):
            continue
        if not is_nrrd and not os.path.isdir(fname):
            # not a folder and not nrrd file
            # probably a nifti file
            output_files.append(fname)
            continue

        pure_id = gu.get_pure_scan_file_name(fname)
        conv_output_folder = f"{output_folder}{pure_id}/NIFTI/"
        conv_out_name = f"{conv_output_folder}{pure_id}.nii.gz"
        if not os.path.exists(conv_out_name):
            files_to_process.append(fname)
        output_files.append(conv_out_name)

    if verbose:
        print(f"Found {len(files_to_process)} files/directories to process out of {len(in_files)} files/directories")

    in_files = files_to_process
    if len(in_files) == 0:
        if verbose:
            print("No files to convert!")
        return output_files

    # no need to do multiprocessing for one file
    if len(in_files) == 1:
        input_file = in_files[0].strip()
        if verbose:
            print(f"Converting: {input_file}")
        local_start_time = time.time()
        do_convert(output_folder, input_file, params)
        elapsed_time = time.time() - local_start_time
        elapsed_time_str = gu.display_time(int(elapsed_time))
        if verbose:
            print(f"Done with {input_file} - took {elapsed_time_str}")
        params = gu.set_and_create_folders(input_file, output_folder, params)
        stats_folder = params["stats_folder"]
        time_stats_out = f"{stats_folder}conversion_proc_time.txt"
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
    return output_files
