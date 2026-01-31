"""Utility functions to gather measurements from multiple scans."""
import os.path
import shutil
from pathlib import Path
from datetime import datetime
import cardiacctexplorer.general_utils as gu

def flatten_json(y):
    out = {}

    def flatten(x, name=""):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + "_")
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + "_")
                i += 1
        else:
            out[str(name[:-1])] = str(x)

    flatten(y)
    return out


def gather_all_stat_columen_names(in_files, output_folder, params):
    verbose = params["verbose"]
    quiet = params["quiet"]
    write_log_file = params["write_log_file"]

    all_column_names_set = set()
    all_column_names = []
    for in_file in in_files:
        params = gu.set_and_create_folders(in_file, output_folder, params)
        stats_folder = params["stats_folder"]
        stats_file = f"{stats_folder}all_cardiac_statistics.json"

        if not os.path.isfile(stats_file):
            if verbose:
                print(f"Measurement file {stats_file} not found, skipping")
            continue
        json_stuff = gu.read_json_file(stats_file)
        if json_stuff is None:
            if not quiet:
                print(f"Error reading {stats_file}")
            if write_log_file:
                gu.write_message_to_log_file(
                    base_dir=output_folder,
                    message=f"Error reading {stats_file}",
                    level="error",
                )
            continue
        flat_json = flatten_json(json_stuff)
        columns = flat_json.keys()

        for c in columns:
            if c not in all_column_names_set:
                all_column_names_set.add(c)
                all_column_names.append(c)

    return list(all_column_names)


def gather_measurements_from_file(in_file, all_column_names, output_folder, params):
    verbose = params["verbose"]
    quiet = params["quiet"]
    write_log_file = params["write_log_file"]

    params = gu.set_and_create_folders(in_file, output_folder, params)
    stats_folder = params["stats_folder"]
    stats_file = f"{stats_folder}all_cardiac_statistics.json"

    if not os.path.isfile(stats_file):
        if verbose:
            print(f"Measurement file {stats_file} not found, skipping")
        return None
    json_stuff = gu.read_json_file(stats_file)
    if json_stuff is None:
        if not quiet:
            print(f"Error reading {stats_file}")
        if write_log_file:
            gu.write_message_to_log_file(
                base_dir=output_folder,
                message=f"Error reading {stats_file}",
                level="error",
            )
        return None
    flat_json = flatten_json(json_stuff)
    columns = flat_json.keys()

    values = {}
    for c in all_column_names:
        values[c] = ""
    for c in columns:
        values[c] = flat_json[c]

    return values


def get_all_measurement(in_files, all_column_names, output_folder, measures_out, params):
    f = open(measures_out, "a")
    for in_file in in_files:
        values = gather_measurements_from_file(in_file, all_column_names, output_folder, params)
        if values is not None:
            for c in all_column_names:
                f.write(f"{values[c]},")
            f.write("\n")
    f.close()


def copy_all_visualization(in_files, output_folder, params):
    verbose = params["verbose"]

    if verbose:
        print(f"Copying visualizations to {output_folder}all_visualizations/")

    out_vis_folder = f"{output_folder}all_visualizations/"
    Path(out_vis_folder).mkdir(parents=True, exist_ok=True)

    for in_file in in_files:
        params = gu.set_and_create_folders(in_file, output_folder, params)
        vis_in_folder = params["vis_folder"]
        scan_id = params["pure_id"]
        vis_in = f"{vis_in_folder}cardiac_visualization.png"
        vis_out = f"{out_vis_folder}{scan_id}_cardiac_visualization.png"

        if not os.path.isfile(vis_in):
            if verbose:
                print(f"Visualization {vis_in} not found, skipping")
            continue

        shutil.copy(vis_in, vis_out)
    return True


def copy_all_segmentations(in_files, output_folder, params):
    verbose = params["verbose"]

    out_segm_folder = f"{output_folder}all_segmentations/"
    Path(out_segm_folder).mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Copying segmentations to {out_segm_folder}")

    for in_file in in_files:
        params = gu.set_and_create_folders(in_file, output_folder, params)
        segm_in_folder = params["segm_folder"]
        scan_id = params["pure_id"]
        segm_in = f"{segm_in_folder}cardiac_combined_segmentation.nii.gz"
        segm_out = f"{out_segm_folder}{scan_id}_cardiac_segmentations.nii.gz"

        if not os.path.isfile(segm_in):
            if verbose:
                print(f"Segmentation {segm_in} not found, skipping")
            continue

        shutil.copy(segm_in, segm_out)
    return True


def process_measurements(in_files, output_folder, params):
    verbose = params["verbose"]
    quiet = params["quiet"]
    write_log_file = params["write_log_file"]
    measures_out = f"{output_folder}CardiacCTExplorer_measurements.csv"
    now_date = datetime.strftime(datetime.now(), "%d-%m-%Y-%H-%M-%S")

    if verbose:
        print(f"Gathering measurements from {len(in_files)} files. Output to {output_folder}")

    if os.path.exists(measures_out):
        name_no_extension = os.path.splitext(measures_out)[0]
        backup_name = f"{name_no_extension}_backup_{now_date}.csv"
        if verbose:
            print(f"Measurement output file {measures_out} already exists. Backing up to {backup_name}")
        try:
            shutil.move(measures_out, backup_name)
        except Exception as e:
            # probably permission error since file is open in excel
            msg = f"Could not back up existing measurement file {measures_out} to {backup_name}: {str(e)}"
            if not quiet:
                print(msg)
            name_no_extension = os.path.splitext(measures_out)[0]
            measures_out = f"{name_no_extension}_new_{now_date}.csv"
            if not quiet:
                print(f"Writing new measurement file to {measures_out} instead")

    all_column_names = gather_all_stat_columen_names(in_files, output_folder, params)
    if len(all_column_names) < 1:
        msg = f"No measurement files found in {output_folder}"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(
                base_dir=output_folder, message=msg, level="error"
            )
        return False

    if verbose:
        print(f"Found {len(all_column_names)} different measurement columns")

    try:
        f = open(measures_out, "w")
        for c in all_column_names:
            f.write(f"{c},")
        f.write("\n")
        f.close()

        get_all_measurement(in_files, all_column_names, output_folder, measures_out, params)
    except Exception as e:
        msg = f"Error writing to {measures_out}: {str(e)}"
        if not quiet:
            print(msg)
        if write_log_file:
            gu.write_message_to_log_file(
                base_dir=output_folder, message=msg, level="error"
            )

    copy_all_visualization(in_files, output_folder, params)
    copy_all_segmentations(in_files, output_folder, params)
    return True
