"""Utilities for segmentation processing"""
import numpy as np
from scipy.ndimage import measurements
import edt
import SimpleITK as sitk
from skimage.segmentation import find_boundaries
from skimage.exposure import rescale_intensity
from skimage.util import img_as_ubyte
from skimage import color
from skimage.io import imsave
from skimage.measure import label, regionprops
from cardiacctexplorer.io_utils import read_nifti_file_robustly

def extract_crop_around_segmentation(segm, margin_mm, spacing):
    # print(f"DEBUG: spacing: {spacing[2]:.2f} {spacing[1]:.2f} {spacing[0]:.2f} for shape: {segm.shape}")
    # First coord: z : shape[0] for spacing[2]
    # Second coord: y : shape[1] for spacing[1]
    # Third coord: x : shape[2] for spacing[0]

    x_min = np.min(np.where(segm)[2])
    x_max = np.max(np.where(segm)[2])
    y_min = np.min(np.where(segm)[1])
    y_max = np.max(np.where(segm)[1])
    z_min = np.min(np.where(segm)[0])
    z_max = np.max(np.where(segm)[0])

    # Expanding bounding box in each direction
    expand_mm = margin_mm
    expand_vox_x = int(expand_mm / spacing[0])
    expand_vox_y = int(expand_mm / spacing[1])
    expand_vox_z = int(expand_mm / spacing[2])
    x_min = max(0, x_min - expand_vox_x)
    x_max = min(segm.shape[2] - 1, x_max + expand_vox_x)
    y_min = max(0, y_min - expand_vox_y)
    y_max = min(segm.shape[1] - 1, y_max + expand_vox_y)
    z_min = max(0, z_min - expand_vox_z)
    z_max = min(segm.shape[0] - 1, z_max + expand_vox_z)

    cropped_segm = segm[z_min:z_max+1, y_min:y_max+1, x_min:x_max+1]
    return cropped_segm, x_min, x_max, y_min, y_max, z_min, z_max

def add_crop_into_full_segmentation(cropped_segm, output_segm, x_min, x_max, y_min, y_max, z_min, z_max):
    full_size_overlap_mask = np.zeros_like(output_segm, dtype=bool)
    full_size_overlap_mask[z_min:z_max+1, y_min:y_max+1, x_min:x_max+1] |= cropped_segm
    return full_size_overlap_mask


def get_components_over_certain_size(
    segmentation, min_size=5000, max_number_of_components=2, fast_mode=True
):
    # check for empty segmentation
    if np.sum(segmentation) == 0:
        return None, None
    if fast_mode:
        crop_border_mm = 2
        segm_crop, x_min, x_max, y_min, y_max, z_min, z_max = extract_crop_around_segmentation(
            segmentation, crop_border_mm, [1, 1, 1])
        labels = label(segm_crop)
        bin_c = np.bincount(labels.flat, weights=segm_crop.flat)
        debug = False
        # probably extremely unefficient
        comp_ids = []
        for c in range(max_number_of_components):
            idx = np.argmax(bin_c)
            if bin_c[idx] > min_size:
                comp_ids.append(idx)
                bin_c[idx] = 0

        if len(comp_ids) < 1:
            if debug:
                print(f"No connected components with size above {min_size} found")
            return None, None
        largest_cc_crop = labels == comp_ids[0]
        for idx in range(1, len(comp_ids)):
            largest_cc_crop = np.bitwise_or(largest_cc_crop, labels == comp_ids[idx])

        largest_cc = add_crop_into_full_segmentation(largest_cc_crop, segmentation,
                                          x_min, x_max, y_min, y_max, z_min, z_max)
    else:
        debug = False
        labels = label(segmentation)
        bin_c = np.bincount(labels.flat, weights=segmentation.flat)
        # probably extremely unefficient
        comp_ids = []
        for c in range(max_number_of_components):
            idx = np.argmax(bin_c)
            if bin_c[idx] > min_size:
                comp_ids.append(idx)
                bin_c[idx] = 0

        if len(comp_ids) < 1:
            if debug:
                print(f"No connected components with size above {min_size} found")
            return None, None
        largest_cc = labels == comp_ids[0]
        for idx in range(1, len(comp_ids)):
            largest_cc = np.bitwise_or(largest_cc, labels == comp_ids[idx])

    return largest_cc, len(comp_ids)


def get_components_over_certain_size_as_individual_volumes(
    segmentation, min_size=5000, max_number_of_components=2, fast_mode=True
):
    # check for empty segmentation
    if np.sum(segmentation) == 0:
        return None
    if fast_mode:
        crop_border_mm = 2
        segm_crop, x_min, x_max, y_min, y_max, z_min, z_max = extract_crop_around_segmentation(
            segmentation, crop_border_mm, [1, 1, 1])
        labels = label(segm_crop)
        bin_c = np.bincount(labels.flat, weights=segm_crop.flat)
        debug = False
        # probably extremely unefficient
        comp_ids = []
        for c in range(max_number_of_components):
            idx = np.argmax(bin_c)
            if debug:
                print(f"{bin_c[idx]}")
            if bin_c[idx] > min_size:
                comp_ids.append(idx)
                bin_c[idx] = 0

        if len(comp_ids) < 1:
            if debug:
                print(f"No connected components with size above {min_size} found")
            return None

        components = []
        for idx in range(len(comp_ids)):
            largest_cc_crop = labels == comp_ids[idx]
            largest_cc = add_crop_into_full_segmentation(largest_cc_crop, segmentation,
                                              x_min, x_max, y_min, y_max, z_min, z_max)
            components.append(largest_cc)
    else:
        labels = label(segmentation)
        bin_c = np.bincount(labels.flat, weights=segmentation.flat)
        debug = False
        # probably extremely unefficient
        comp_ids = []
        for c in range(max_number_of_components):
            idx = np.argmax(bin_c)
            if debug:
                print(f"{bin_c[idx]}")
            if bin_c[idx] > min_size:
                comp_ids.append(idx)
                bin_c[idx] = 0

        if len(comp_ids) < 1:
            if debug:
                print(f"No connected components with size above {min_size} found")
            return None

        components = []
        for idx in range(len(comp_ids)):
            largest_cc = labels == comp_ids[idx]
            components.append(largest_cc)

    return components


def close_cavities_in_segmentations(segmentation, fast_mode=True):
    """
    Close cavities in segmentations by finding the largest connected component of the background
    """
    # check for empty segmentation
    if np.sum(segmentation) == 0:
        return None, None
    if fast_mode:
        crop_border_mm = 5
        segm_crop, x_min, x_max, y_min, y_max, z_min, z_max = extract_crop_around_segmentation(
            segmentation, crop_border_mm, [1, 1, 1])
        background = segm_crop == 0
        labels = label(background)
        bin_c = np.bincount(labels.flat, weights=background.flat)
        n_comp = np.count_nonzero(bin_c)
        idx = np.argmax(bin_c)
        connected_background = labels == idx
        closed_segm_crop = np.bitwise_not(connected_background)
        closed_segm = add_crop_into_full_segmentation(closed_segm_crop, segmentation,
                                              x_min, x_max, y_min, y_max, z_min, z_max)
    else:
        background = segmentation == 0
        labels = label(background)
        bin_c = np.bincount(labels.flat, weights=background.flat)
        n_comp = np.count_nonzero(bin_c)
        idx = np.argmax(bin_c)

        connected_background = labels == idx
        closed_segm = np.bitwise_not(connected_background)
    return closed_segm, n_comp


def edt_based_opening(segmentation, spacing, radius, fast_mode=True):
    # check for empty segmentation
    if np.sum(segmentation) == 0:
        return None
    if fast_mode:
        crop_border_mm = radius * 2
        segm_crop, x_min, x_max, y_min, y_max, z_min, z_max \
            = extract_crop_around_segmentation(segmentation, crop_border_mm, [spacing[2], spacing[1], spacing[0]])
        sdf_mask = -edt.sdf(segm_crop, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
        eroded_mask = sdf_mask < -radius
        sdf_mask = -edt.sdf(eroded_mask, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
        opened_mask_crop = sdf_mask <= radius
        opened_mask = add_crop_into_full_segmentation(opened_mask_crop, segmentation,
                                                      x_min, x_max, y_min, y_max, z_min, z_max)
    else:
        sdf_mask = -edt.sdf(
            segmentation, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        eroded_mask = sdf_mask < -radius
        sdf_mask = -edt.sdf(
            eroded_mask, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        opened_mask = sdf_mask <= radius
    return opened_mask


def edt_based_closing(segmentation, spacing, radius, fast_mode=True):
    # check for empty segmentation
    if np.sum(segmentation) == 0:
        return None
    if fast_mode:
        crop_border_mm = radius * 2
        segm_crop, x_min, x_max, y_min, y_max, z_min, z_max \
            = extract_crop_around_segmentation(segmentation, crop_border_mm, [spacing[2], spacing[1], spacing[0]])
        sdf_mask = -edt.sdf(segm_crop, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
        dilated_mask = sdf_mask <= radius
        sdf_mask = -edt.sdf(dilated_mask, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
        closed_mask_crop = sdf_mask < -radius
        closed_mask = add_crop_into_full_segmentation(closed_mask_crop, segmentation,
                                                      x_min, x_max, y_min, y_max, z_min, z_max)
    else:
        sdf_mask = -edt.sdf(
            segmentation, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        dilated_mask = sdf_mask <= radius
        sdf_mask = -edt.sdf(
            dilated_mask, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        closed_mask = sdf_mask < -radius
    return closed_mask


def edt_based_dilation(segmentation, spacing, radius, fast_mode=True):
    # check for empty segmentation
    if np.sum(segmentation) == 0:
        return None
    if fast_mode:
        crop_border_mm = radius * 2
        segm_crop, x_min, x_max, y_min, y_max, z_min, z_max \
            = extract_crop_around_segmentation(segmentation, crop_border_mm, [spacing[2], spacing[1], spacing[0]])
        sdf_mask = -edt.sdf(segm_crop, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
        dilated_mask_crop = sdf_mask <= radius
        dilated_mask = add_crop_into_full_segmentation(dilated_mask_crop, segmentation,
                                                      x_min, x_max, y_min, y_max, z_min, z_max)
    else:
        sdf_mask = -edt.sdf(
            segmentation, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        dilated_mask = sdf_mask <= radius
    return dilated_mask


def edt_based_erosion(segmentation, spacing, radius, fast_mode=True):
    # check for empty segmentation
    if np.sum(segmentation) == 0:
        return None
    if fast_mode:
        crop_border_mm = radius * 2
        segm_crop, x_min, x_max, y_min, y_max, z_min, z_max \
            = extract_crop_around_segmentation(segmentation, crop_border_mm, [spacing[2], spacing[1], spacing[0]])
        sdf_mask = -edt.sdf(segm_crop, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
        eroded_mask_crop = sdf_mask < -radius
        eroded_mask = add_crop_into_full_segmentation(eroded_mask_crop, segmentation,
                                                      x_min, x_max, y_min, y_max, z_min, z_max)
    else:
        sdf_mask = -edt.sdf(
            segmentation, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        eroded_mask = sdf_mask < -radius
    return eroded_mask


def edt_based_overlap(segmentation_1, segmentation_2, spacing, radius, fast_mode=True):
    """
    Compute the overlap between two segmentations using the Euclidean distance transform
    """
    # check for empty segmentation
    if np.sum(segmentation_1) == 0 or np.sum(segmentation_2) == 0:
        return None
    if fast_mode:
        # Find smallest segmentation to crop around
        sum_1 = np.sum(segmentation_1)
        sum_2 = np.sum(segmentation_2)
        if sum_1 < sum_2:
            crop_border_mm = radius * 2
            segm_crop, x_min, x_max, y_min, y_max, z_min, z_max \
                = extract_crop_around_segmentation(segmentation_1, crop_border_mm, [spacing[2], spacing[1], spacing[0]])
            sdf_mask_1 = -edt.sdf(segm_crop, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
            sdf_mask_2_crop = -edt.sdf(
                segmentation_2[z_min:z_max+1, y_min:y_max+1, x_min:x_max+1],
                anisotropy=[spacing[0], spacing[1], spacing[2]],
                parallel=8,
            )
            overlap_mask_crop = (sdf_mask_1 < radius) & (sdf_mask_2_crop < radius)
            overlap_mask = add_crop_into_full_segmentation(overlap_mask_crop, segmentation_1,
                                                          x_min, x_max, y_min, y_max, z_min, z_max)
        else:
            crop_border_mm = radius * 2
            segm_crop, x_min, x_max, y_min, y_max, z_min, z_max \
                = extract_crop_around_segmentation(segmentation_2, crop_border_mm, [spacing[2], spacing[1], spacing[0]])
            sdf_mask_2 = -edt.sdf(segm_crop, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8)
            sdf_mask_1_crop = -edt.sdf(
                segmentation_1[z_min:z_max+1, y_min:y_max+1, x_min:x_max+1],
                anisotropy=[spacing[0], spacing[1], spacing[2]],
                parallel=8,
            )
            overlap_mask_crop = (sdf_mask_1_crop < radius) & (sdf_mask_2 < radius)
            overlap_mask = add_crop_into_full_segmentation(overlap_mask_crop, segmentation_2,
                                                          x_min, x_max, y_min, y_max, z_min, z_max)
    else:
        sdf_mask_1 = -edt.sdf(
            segmentation_1, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        sdf_mask_2 = -edt.sdf(
            segmentation_2, anisotropy=[spacing[0], spacing[1], spacing[2]], parallel=8
        )
        overlap_mask = (sdf_mask_1 < radius) & (sdf_mask_2 < radius)

        # overlap_mask = np.bitwise_and(sdf_mask_1 < radius, sdf_mask_2 < radius)
    return overlap_mask


def edt_based_compute_landmark_from_segmentation_overlap(
    segmentation_1,
    segmentation_2,
    radius,
    segm_sitk_img,
    overlap_name,
    lm_name,
    min_size_mm3 = 2000,
    only_larges_components=True,
    debug=False,
):
    if debug:
        print(f"Computing {overlap_name} and {lm_name}")

    spacing = segm_sitk_img.GetSpacing()
    spc_trans = [spacing[2], spacing[1], spacing[0]]
    min_size_vox = min_size_mm3 / (spacing[0] * spacing[1] * spacing[2])

    overlap_mask = edt_based_overlap(segmentation_1, segmentation_2, spc_trans, radius)
    if overlap_mask is None:
        if debug:
            print(f"No overlap found for {overlap_name}")
        return False
    if only_larges_components:
        overlap_mask, n_comp = get_components_over_certain_size(overlap_mask, min_size_vox, 1)
        if overlap_mask is None or n_comp < 1:
            if debug:
                print(f"No components found in {overlap_name}")
            return False

    if np.sum(overlap_mask) == 0:
        if debug:
            print(f"No overlap found for {overlap_name}")
        return False

    com_np = measurements.center_of_mass(overlap_mask)
    com_np = [com_np[2], com_np[1], com_np[0]]

    com_phys = segm_sitk_img.TransformIndexToPhysicalPoint(
        [int(com_np[0]), int(com_np[1]), int(com_np[2])]
    )
    if debug:
        img_o = sitk.GetImageFromArray(overlap_mask.astype(int))
        img_o.CopyInformation(segm_sitk_img)

        print(f"saving {overlap_name}")
        sitk.WriteImage(img_o, overlap_name)

    end_p_out = open(lm_name, "w")
    end_p_out.write(f"{com_phys[0]} {com_phys[1]} {com_phys[2]}")
    end_p_out.close()
    return True


def compute_segmentation_volume(segmentation_file, segm_id):
    """
    Compute the volume of a segmentation
    """
    segmentation, _ = read_nifti_file_robustly(segmentation_file)
    if segmentation is None:
        return 0
    #
    # try:
    #     segmentation = sitk.ReadImage(segmentation_file)
    # except RuntimeError as e:
    #     print(f"Got an exception {str(e)}")
    #     print(f"Error reading {segmentation_file}")
    #     return 0

    spacing = segmentation.GetSpacing()

    segmentation_np = sitk.GetArrayFromImage(segmentation)
    volume = np.sum(segmentation_np == segm_id)
    volume = volume * spacing[0] * spacing[1] * spacing[2]
    return volume


def read_nifti_itk_to_numpy(file_name):
    img, _ = read_nifti_file_robustly(file_name)
    if img is None:
        return None, None, None
    #
    # try:
    #     img = sitk.ReadImage(file_name)
    # except RuntimeError as e:
    #     print(f"Got an exception {str(e)}")
    #     print(f"Error reading {file_name}")
    #     return None, None, None

    i2 = sitk.GetArrayFromImage(img)
    spacing = img.GetSpacing()
    size = img.GetSize()
    return i2, spacing, size


def check_if_segmentation_hit_sides_of_scan(segmentation, segm_id, n_slices_to_check=8):
    """
    Return the sides (if any) that the segmentation hits
    """
    shp = segmentation.shape
    bin_segm = segmentation == segm_id

    down = np.sum(bin_segm[0:n_slices_to_check, :, :])
    up = np.sum(bin_segm[shp[0] - 1 - n_slices_to_check : shp[0] - 1, :, :])
    left = np.sum(bin_segm[:, 0:n_slices_to_check, :])
    right = np.sum(bin_segm[:, shp[1] - 1 - n_slices_to_check : shp[1] - 1, :])
    front = np.sum(bin_segm[:, :, 0:n_slices_to_check])
    back = np.sum(bin_segm[:, :, shp[2] - 1 - n_slices_to_check : shp[2] - 1])

    sides = set()
    if up > 0:
        sides.add("up")
    if down > 0:
        sides.add("down")
    if left > 0:
        sides.add("left")
    if right > 0:
        sides.add("right")
    if front > 0:
        sides.add("front")
    if back > 0:
        sides.add("back")

    return sides


def set_window_and_level_on_single_slice(img_in, img_window, img_level):
    out_min = 0
    out_max = 1
    in_min = img_level - img_window / 2
    in_max = img_level + img_window / 2
    # in_max = 800

    # https://scikit-image.org/docs/stable/api/skimage.exposure.html#skimage.exposure.rescale_intensity
    out_img = rescale_intensity(img_in, in_range=(in_min, in_max), out_range=(out_min, out_max))

    return out_img

def write_single_slice_with_overlay(single_slice_np, single_slice_np_img,
                                    img_window, img_level, slice_out_name, slice_out_name_cropped):
    boundary = find_boundaries(single_slice_np, mode='thick')

    single_slice_np_img = set_window_and_level_on_single_slice(single_slice_np_img, img_window, img_level)
    scaled_ubyte = img_as_ubyte(single_slice_np_img)
    scaled_2_rgb = color.gray2rgb(scaled_ubyte)
    rgb_boundary = [255, 0, 0]
    scaled_2_rgb[boundary > 0] = rgb_boundary
    imsave(slice_out_name, np.flipud(scaled_2_rgb))

    region_p = regionprops(img_as_ubyte(boundary))
    if len(region_p) < 1:
        print(f"No regions found for {slice_out_name}")
        return
    bbox = list(region_p[0].bbox)

    shp = boundary.shape
    # Extend bbox range.
    # TODO set value elsewhere
    extend = 20
    bbox[0] = max(0, bbox[0] - extend)
    bbox[1] = max(0, bbox[1] - extend)
    bbox[2] = min(shp[0], bbox[2] + extend)
    bbox[3] = min(shp[1], bbox[3] + extend)

    scaled_2_rgb_crop = scaled_2_rgb[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    imsave(slice_out_name_cropped, np.flipud(scaled_2_rgb_crop))


def extract_orthonogonal_slices_from_given_segment(img_np, label_img_np, segment_id, base_name, min_hu, max_hu):
    slice_1_out_rgb = f"{base_name}_slice_1_rgb.png"
    # slice_1_out_label = f"{stat_dir}{segment_name}_slice_1_label.png"
    slice_1_out_rgb_crop = f"{base_name}_slice_1_rgb_crop.png"
    slice_2_out_rgb = f"{base_name}_slice_2_rgb.png"
    slice_2_out_rgb_crop = f"{base_name}_slice_2_rgb_crop.png"
    slice_3_out_rgb = f"{base_name}_slice_3_rgb.png"
    slice_3_out_rgb_crop = f"{base_name}_slice_3_rgb_crop.png"
    # slice_out_info = f"{stat_dir}{segment_name}_slice_info.json"
    # Default values. If the values is -10000 they should be automatically computed
    visualization_min_hu = min_hu
    visualization_max_hu = max_hu

    mask_np = label_img_np == segment_id
    if np.sum(mask_np) < 10:
        return

    img_window = visualization_max_hu - visualization_min_hu
    img_level = (visualization_max_hu + visualization_min_hu) / 2.0

    com_np = measurements.center_of_mass(mask_np)

    rel_idx = int(com_np[0])
    single_slice_np = mask_np[rel_idx, :, :]
    single_slice_np_img = img_np[rel_idx, :, :]
    write_single_slice_with_overlay(single_slice_np, single_slice_np_img, img_window, img_level,
                                    slice_1_out_rgb, slice_1_out_rgb_crop)

    rel_idx = int(com_np[1])
    single_slice_np = mask_np[:, rel_idx, :]
    single_slice_np_img = img_np[:, rel_idx, :]
    write_single_slice_with_overlay(single_slice_np, single_slice_np_img, img_window, img_level,
                                    slice_2_out_rgb, slice_2_out_rgb_crop)

    rel_idx = int(com_np[2])
    single_slice_np = mask_np[:, :, rel_idx]
    single_slice_np_img = img_np[:, :, rel_idx]
    write_single_slice_with_overlay(single_slice_np, single_slice_np_img, img_window, img_level,
                                    slice_3_out_rgb, slice_3_out_rgb_crop)
