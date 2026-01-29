import os
import logging

from cell_imaging_utils.image.image_utils import ImageUtils
import numpy as np

log = logging.getLogger(__name__)
images_save_dir = "{}\\tests\\images".format(os.getcwd())
results_save_dir = "{}\\tests\\results".format(os.getcwd())


organelle_name = "Endoplasmic-reticulum"
image_file_name = "Endoplasmic-reticulum_4993.tiff"
result_image_file_name = "test_sliced.tiff"
# seg_image_file_name = "image_list_test.csv"

if not os.path.exists(results_save_dir):
    os.makedirs(results_save_dir)

def test_image_utils() -> None:
    image = ImageUtils.imread("{}\\{}\\{}".format(images_save_dir,organelle_name,image_file_name))
    print(ImageUtils.get_channel_names(image))
    image_ndarray = ImageUtils.normalize(ImageUtils.image_to_ndarray(image))
    # bf_image = ImageUtils.get_channel(image,3)
    # fl_image = ImageUtils.get_channel(image_ndarray,2)
    # n_image = ImageUtils.add_channel(bf_image,fl_image)
    # print(n_image.shape)
    # ImageUtils.imsave(n_image,"{}\\{}\\{}".format(images_save_dir,organelle_name,result_image_file_name))
    # test_image = ImageUtils.imread(n_image)
    # test_image = ImageUtils.normalize(test_image)
    mask_template = ImageUtils.get_channel(image_ndarray,5)
    test_image = ImageUtils.crop_edges(image_ndarray,mask_template)
    
    # test_image = ImageUtils.project_to_2d(image_ndarray)
    # indexes
    ImageUtils.imsave(test_image,"{}\\{}\\{}".format(images_save_dir,organelle_name,result_image_file_name))

    return None


test_image_utils()