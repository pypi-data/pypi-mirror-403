# Cardiac CT Explorer

An open source tool for segmentation of the heart in 3D computed tomography scans with a special focus on the left atrial appendage (LAA).

![CardiacCTExplorer](figs/1.img_cardiac_visualization.png)

**Highlights:**

- Based on the excellent work of the [TotalSegmentator](https://github.com/wasserth/TotalSegmentator) team.
- Supports contrast-enhanced cardiac CT scans.
- Creates a segmentation map including the major heart structures, the left atrial appendage and the pulmonary veins.
- Can generate the data described in [STACOM2025: A Public Cardiac CT Dataset Featuring the Left Atrial Appendage](https://github.com/Bjonze/Public-Cardiac-CT-Dataset)
- Has been validated on a series of open source and some proprietary data sets.
- Generates visualizations for easy validation of outputs.
- Designed as a research tool for population studies.

**Note**: This is not a medical device and is not intended for clinical usage. It is meant for research purposes and explorative analysis of the human aorta.

It is based on work done at [DTU Compute](https://www.compute.dtu.dk/), the [Cardiovascular Research Unit, Rigshospitalet, Copenhagen, Denmark](https://www.rigshospitalet.dk/english/research-and-innovation/units-and-groups/Pages/cardiovascular-ct-research-unit.aspx) and [Universitat Pompeu Fabra](https://www.upf.edu/web/enginyeria/faculty/-/asset_publisher/vto8LcELdA46/content/camara-rey-oscar/maximized).

Please cite these papers if you use CardiacCTExplorer:
```bibtex
@inproceedings{juhl2021implicit,
  title={Implicit neural distance representation for unsupervised and supervised classification of complex anatomies},
  author={Juhl, Kristine Aavild and Morales, Xabier and De Backer, Ole and Camara, Oscar and Paulsen, Rasmus R.},
  booktitle={International Conference on Medical Image Computing and Computer-Assisted Intervention},
  pages={405--415},
  year={2021},
  publisher={Springer}
}

@inproceedings{Hansen2025LAA,
  title       = {A Public Cardiac CT Dataset Featuring the Left Atrial Appendage},
  author      = {Hansen, Bj{\o}rn and Pedersen, Jonas and Kofoed, Klaus F. and Camara, Oscar and Paulsen, Rasmus R. and S{\o}rensen, Kristine},
  booktitle   = {Statistical Atlases and Computational Modeling of the Heart (STACOM), MICCAI Workshop},
  year        = {2025},
  publisher   = {Springer},
  url         = {https://arxiv.org/abs/2510.06090}
}
```
Please also cite the [TotalSegmentator paper](https://pubs.rsna.org/doi/10.1148/ryai.230024) since CardiacCTExplorer is heavily dependent on it. If you use the ImageCAS data, please cite the [ImageCAS paper](https://www.sciencedirect.com/science/article/pii/S0895611123001052).


## Installation

CardiacCTExplorer has been tested on Ubuntu Linux and Windows but should work on most systems. The GPU usage is limited to the TotalSegmentator segmentation tasks and you can see the requirements [here](https://github.com/wasserth/TotalSegmentator?tab=readme-ov-file).

The installation requires a few steps:

1. Create and activate an environment. e.g a conda environment
```
conda create -n CardiacCTExplorerEnv python=3.13
conda activate CardiacCTExplorerEnv
```

2. Install [PyTorch](https://pytorch.org/get-started/locally/). Choose the cuda version that matches with what you have available for your GPU


3. Install CardiacCTExplorer
```
pip install CardiacCTExplorer
```

4. Install the [TotalSegmentator license](https://github.com/wasserth/TotalSegmentator/blob/master/README.md#subtasks). CardiacCTExplorer is dependent on the `heartchambers_highres` subtask and you need to obtain the [license](https://backend.totalsegmentator.com/license-academic/) and install the license key.


## Usage

CardiacCTExplorer can process:
 - single NIFTI files
 - a folder with NIFTI files
 - a text file with NIFTI file names.
 - single NRRD files
 - a folder with NRRD files
 - a text file with NRRD file names.
 - single DICOM folders
 - folder with DICOM folders
 - a text file with DICOM folder names (full path needed)
 
 
```bash
CardiacCTExplorer -i /data/CardiacCT/CardiacCT_scan.nii.gz -o /data/CardiacCT/CardiacCTExplorerOutput/ --verbose
```

Will process the NIFTI file `CardiacCT_scan.nii.gz` and create a sub-folder with results in the specified output folder `/data/CardiacCT/CardiacCTExplorerOutput/`.

If the input is a folder, it will process all `.nii.gz`, `.nrrd`, and `.nii` files in that folder. If the input is the name of a text file, it will process all files (specified with full path names) listed in the text file. Note when processing several files, they all need to have unique base names, since the output will named according to this.

**Expected processing time**: CardiacCTExplorer is not optimized for speed. On a standard PC (January 2026) the processing time is between 5 and 10 minutes per scan. However, it can process several scans simultanously using multiprocessing and it scales well with the number of cores. 

## Outputs

CardiacCTExplorer main outputs are:
- CSV file with some simple measurements. It is called `CardiacCTExplorer_measurements.csv` and will be placed in the specified output folder. One row per input file.
- Visualizations of the results placed in a sub-folder called `all_visualizations`.
- Segmentation masks placed in a sub-folder called `all_segmentations`.
- A log file with potential errors and warnings placed in the specified output folder.

If you can not find your expected segmentation maps, you should check the log file to see if there are any reported errors.


## Advanced settings

The CardiacCTExplorer commandline accept a set of arguments.

See [here](cardiacctexplorer/bin/CardiacCTExplorer.py) for the total set of command line parameters.

## Python API

CardiacCTExplorer can be used as a Python API. For Example:

```Python
from cardiacctexplorer.python_api import cardiacctexplorer, get_default_parameters

def test_cardiacctexplorer():
    params = get_default_parameters()

    input_file = "/data/CardiacCT/CardiacCT_scan.nii.gz"
    output_folder = "/data/CardiacCT/CardiacCTExplorerOutput/"
    
	cardiacctexplorer(input_file, output_folder, params)

if __name__ == "__main__":
    test_cardiacctexplorer()
```

The `params` is a dictionary, where the individual values can be changed before the call to CardiacCTexplorer. The parameters can be seen [here](cardiacctexplorer/python_api.py).


## Cardiac segments and measurements

CardiacCTExplorer generates a segmentation map, with the following labels:


- 0 : **Background**
- 1 : **Myocardium** : The muscle tissue surrounding the left ventricle blood pool
- 2 : **LA** : The left atrium blood pool
- 3 : **LV** : The left ventricle blood pool including the papilary muscles and trabeculation
- 4 : **RA** : The right atrium blood pool
- 5 : **RV** : The right ventricle blood pool
- 6 : **Aorta** : The aorta including the aortic cusp
- 7 : **PA** : The pulmonary artery
- 8 : **LAA** : The left atrial appendage
- 9 : **Coronary** : The left and right coronary arteries
- 10 : **PV** : The pulmonary veins

## What does it do?

In the default (non ImageCAS) mode the framework broadly follows the following steps. This is explained in detail in the [STACOM 2025 paper](https://github.com/Bjonze/Public-Cardiac-CT-Dataset)

- Computes the TotalSegmentator heartchambers_highres segmentations
- Computes the TotalSegmentator coronary_arteries segmentations
- Predicts the LAA using the [NUDF framework](https://link.springer.com/chapter/10.1007/978-3-030-87196-3_38)
- Connects the pulmonary veins to the left atrium using a combination of distance fields, HU statistics and morphological operations.
- Use the coronary artery segmentations from TotalSegmentator
- Connects the coronary arteries to the aorta (if possible)
- Thresholds the coronary arteries so only voxels with a HU value above 20 are kept.


## Check for partial structures

In the CSV file with measurements it is also noted which structures that touches the side of the scan. The aorta will always touch the scan in a cardiac scan. If the left atrial appendage touches the scan, great care should be taken if the LAA is used in any type of geometric analysis. The algorithm uses a value that marks *out-of-reconstruction*. This is typically set by the scanner reconstruction software and ideally should be -2048 or below. This value can be set using the [commandline parameters](cardiacctexplorer/bin/CardiacCTExplorer.py). Please never use -1024 as a default value when resampling scans, since air (or lungs) will sometimes also have this value (use -2048).


## Error handling and pathological cases

CardiacCTExplorer includes a range of checks for the validity and type of scan.  If the processing fails, the log file should be inspected for the cause.


## CardiacCTExplorer on ImageCAS

CardiacCTExplorer can generate segmentation maps of the 
[ImageCAS](https://www.sciencedirect.com/science/article/pii/S0895611123001052) dataset as described in [STACOM2025: A Public Cardiac CT Dataset Featuring the Left Atrial Appendage](https://github.com/Bjonze/Public-Cardiac-CT-Dataset).

Follow this procedure to do this:
1) Download [The ImageCAS data](https://www.kaggle.com/datasets/xiaoweixumedicalai/imagecas)

2) Unpack all volumes and labelmaps into a folder.

3) Run CardiacCTExplorer with the following commandline:

```bash
CardiacCTExplorer -i /data/ImageCAS/volumes/ -o /data/ImageCAS/CardiacCTExplorerOutput/ --verbose -ic
```

The `-ic` tells CardiacCTExplorer that it should work specifically with the ImageCAS data. It will:

- Computes the TotalSegmentator heartchambers_highres segmentations
- Predicts the LAA using the [NUDF framework](https://link.springer.com/chapter/10.1007/978-3-030-87196-3_38)
- Connects the pulmonary veins to the left atrium using a combination of distance fields, HU statistics and morphological operations.
- Use the provided manual annotations of the coronary arteries from the ImageCAS data
- Connects the coronary arteries to the aorta (if possible)
- Thresholds the coronary arteries so only voxels with a HU value above 20 are kept.

Please note that the manual coronary artery segmentations provided by ImageCAS is of varying quality and sometimes include coronary veins. They are, however, by far the most comprehensive open data set currently available.
 
