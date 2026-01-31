"""CardiacCTExplorer Python API functions."""
from pathlib import Path
from typing import Union
import cardiacctexplorer.general_utils as gu
from cardiacctexplorer.totalsegmentator_utils import compute_totalsegmentator_segmentations
from cardiacctexplorer.cardiac_utils import cardiac_analysis
from cardiacctexplorer.fileconverter_utils import convert_input_files
from cardiacctexplorer.measurement_utils import process_measurements
from cardiacctexplorer.nudf_laa_utils import nudf_laa_analysis

def get_default_parameters():
    default_parms = {
        "nudf_model_url": "https://shapeml.compute.dtu.dk/NUDF/",
        "nudf_checkpoint": "NUDF_checkpoint_epoch_24_17-12-2025.tar",
        "nudf_model_folder": "",
        "num_proc_total_segmentator": 1,
        "num_proc_nudf": 1,
        "num_proc_general": 4,
        "recurse_subfolders": False,
        "out_of_reconstruction_value": -2048,
        "minimum_laa_hu_value": 200,
        "minimum_pv_hu_value": 200,
        "minimum_aorta_hu_value": 150,
        "minimum_coronary_artery_hu_value": 20,
        "image_cas_mode": False,
        "segment_id_to_slice": 8,
        "hounsfield_unit_offset": 0,
        "rendering_window_size": [1920, 1080],
        "device" : "gpu",
        "verbose": True,
        "quiet": False,
        "write_log_file": True
    }
    return default_parms


def cardiacctexplorer(in_name: Union[str, Path], output: Union[str, Path], cardiacct_parameters) -> bool:
    """
    Run CardiacCTExplorer from within Python.

    For explanation of the arguments see description of command line
    arguments in bin/cardiacctexplorer.

    Return: success or not
    """
    quiet = cardiacct_parameters.get("quiet", False)
    verbose = cardiacct_parameters.get("verbose", False)
    write_log_file = cardiacct_parameters.get("write_log_file", False)

    # TODO: Need real article link
    if not quiet:
        print("\nIf you use this tool please cite TBD article\n")

    # ts_nr_proc = cardiacct_parameters.get("num_proc_total_segmentator", 1)
    # tg_nr_proc = cardiacct_parameters.get("num_proc_general", 1)
    recurse_subfolder = cardiacct_parameters.get("recurse_subfolders", False)
    image_cas_mode = cardiacct_parameters.get("image_cas_mode", False)

    output = str(output)
    Path(output).mkdir(parents=True, exist_ok=True)

    in_files, msg = gu.gather_input_files_from_input(in_name=in_name, recurse_subfolders=recurse_subfolder,
                                                     image_cas_mode=image_cas_mode)
    if len(in_files) < 1:
        if write_log_file:
            gu.write_message_to_log_file(base_dir=output, message=msg, level="error")
        if not quiet:
            print(msg)
        return False
    if verbose:
        print(f"Found {len(in_files)} input files")

    in_files = convert_input_files(in_files=in_files, output_folder=output, params=cardiacct_parameters)
    if len(in_files) < 1:
        return True

    compute_totalsegmentator_segmentations(in_files=in_files, output_folder=output, params=cardiacct_parameters)
    nudf_laa_analysis(in_files=in_files, output_folder=output, params=cardiacct_parameters)
    cardiac_analysis(in_files=in_files, output_folder=output, params=cardiacct_parameters)
    process_measurements(in_files=in_files, output_folder=output, params=cardiacct_parameters)

    return True
