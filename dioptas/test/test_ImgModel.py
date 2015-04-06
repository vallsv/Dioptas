# -*- coding: utf8 -*-
__author__ = 'Clemens Prescher'

import unittest
import gc
import os
from PyQt4 import QtGui

import numpy as np

from model.ImgModel import ImgModel
from model.Helper.ImgCorrection import DummyCorrection


unittest_path = os.path.dirname(__file__)
data_path = os.path.join(unittest_path, 'data')


class ImgDataUnitTest(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication([])
        self.img_model = ImgModel()
        self.img_model.load(os.path.join(data_path, 'image_001.tif'))

    def tearDown(self):
        del self.app
        del self.img_model
        gc.collect()

    def perform_transformations_tests(self):
        self.assertEqual(np.sum(np.absolute(self.img_model.get_img_data())), 0)
        self.img_model.rotate_img_m90()
        self.assertEqual(np.sum(np.absolute(self.img_model.get_img_data())), 0)
        self.img_model.flip_img_horizontally()
        self.assertEqual(np.sum(np.absolute(self.img_model.get_img_data())), 0)
        self.img_model.rotate_img_p90()
        self.assertEqual(np.sum(np.absolute(self.img_model.get_img_data())), 0)
        self.img_model.flip_img_vertically()
        self.assertEqual(np.sum(np.absolute(self.img_model.get_img_data())), 0)
        self.img_model.reset_img_transformations()
        self.assertEqual(np.sum(np.absolute(self.img_model.get_img_data())), 0)

    def test_flipping_images(self):
        original_image = np.copy(self.img_model._img_data)
        self.img_model.flip_img_vertically()
        self.assertTrue(np.array_equal(self.img_model._img_data, np.flipud(original_image)))

    def test_simple_background_subtraction(self):
        self.first_image = np.copy(self.img_model.get_img_data())
        self.img_model.load_next_file()
        self.second_image = np.copy(self.img_model.get_img_data())

        self.img_model.load(os.path.join(data_path, 'image_001.tif'))
        self.img_model.load_background(os.path.join(data_path, 'image_002.tif'))

        self.assertFalse(np.array_equal(self.first_image, self.img_model.get_img_data()))

        self.img_model.load_next_file()
        self.assertEqual(np.sum(self.img_model.get_img_data()), 0)

    def test_background_subtraction_with_supersampling(self):
        self.img_model.load_background(os.path.join(data_path, 'image_002.tif'))

        self.img_model.set_supersampling(2)
        self.img_model.get_img_data()
        self.img_model.set_supersampling(3)
        self.img_model.get_img_data()

        self.img_model.load_next_file()
        self.img_model.get_img_data()

    def test_background_subtraction_with_transformation(self):

        self.img_model.load_background(os.path.join(data_path, 'image_002.tif'))
        original_img = np.copy(self.img_model._img_data)
        original_background = np.copy(self.img_model._background_data)

        self.assertNotEqual(self.img_model._background_data, None)
        self.assertFalse(np.array_equal(self.img_model.img_data,  self.img_model._img_data))

        original_img_background_subtracted = np.copy(self.img_model.get_img_data())
        self.assertTrue(np.array_equal(original_img_background_subtracted, original_img-original_background))

        ### now comes the main process - flipping the image
        self.img_model.flip_img_vertically()
        flipped_img = np.copy(self.img_model._img_data)
        self.assertTrue(np.array_equal(np.flipud(original_img), flipped_img))

        flipped_background = np.copy(self.img_model._background_data)
        self.assertTrue(np.array_equal(np.flipud(original_background), flipped_background))

        flipped_img_background_subtracted = np.copy(self.img_model.get_img_data())
        self.assertTrue(np.array_equal(flipped_img_background_subtracted, flipped_img-flipped_background))

        self.assertTrue(np.array_equal(np.flipud(original_img_background_subtracted),
                                       flipped_img_background_subtracted))
        self.assertEqual(np.sum(np.flipud(original_img_background_subtracted)-flipped_img_background_subtracted), 0)

        self.img_model.load(os.path.join(data_path, 'image_002.tif'))
        self.perform_transformations_tests()


    def test_background_subtraction_with_supersampling_and_image_transformation(self):
        self.img_model.load_background(os.path.join(data_path, 'image_002.tif'))
        self.img_model.load(os.path.join(data_path, 'image_002.tif'))

        self.img_model.set_supersampling(2)
        self.assertEqual(self.img_model.get_img_data().shape, (4096, 4096))

        self.perform_transformations_tests()

        self.img_model.set_supersampling(3)
        self.assertEqual(self.img_model.get_img_data().shape, (6144, 6144))

        self.perform_transformations_tests()

        self.img_model.load(os.path.join(data_path, 'image_002.tif'))
        self.assertEqual(self.img_model.get_img_data().shape, (6144, 6144))

        self.perform_transformations_tests()

    def test_background_scaling_and_offset(self):
        self.img_model.load_background(os.path.join(data_path, 'image_002.tif'))

        #assure that everything is correct before
        self.assertTrue(np.array_equal(self.img_model.get_img_data(),
                                       self.img_model._img_data-self.img_model._background_data))

        #set scaling and see difference
        self.img_model.set_background_scaling(2.4)
        self.assertTrue(np.array_equal(self.img_model.get_img_data(),
                                       self.img_model._img_data-2.4*self.img_model._background_data))

        #set offset and see the difference
        self.img_model.set_background_scaling(1.0)
        self.img_model.set_background_offset(100.0)
        self.assertTrue(np.array_equal(self.img_model.img_data,
                                       self.img_model._img_data-(self.img_model._background_data+100.0)))

        #use offset and scaling combined
        self.img_model.set_background_scaling(2.3)
        self.img_model.set_background_offset(100.0)
        self.assertTrue(np.array_equal(self.img_model.img_data,
                                       self.img_model._img_data-(2.3*self.img_model._background_data+100)))

    def test_background_with_different_shape(self):
        self.img_model.load_background(os.path.join(data_path, 'CeO2_Pilatus1M.tif'))
        self.assertEqual(self.img_model._background_data, None)

        self.img_model.load_background(os.path.join(data_path, 'image_002.tif'))
        self.assertTrue(self.img_model._background_data is not None)

        self.img_model.load(os.path.join(data_path, 'CeO2_Pilatus1M.tif'))
        self.assertEqual(self.img_model._background_data, None)

    def test_absorption_correction_with_supersampling(self):
        original_image = np.copy(self.img_model.get_img_data())
        dummy_correction = DummyCorrection(self.img_model.get_img_data().shape, 0.6)

        self.img_model.add_img_correction(dummy_correction, "Dummy 1")
        self.assertAlmostEqual(np.sum(original_image)/0.6, np.sum(self.img_model.get_img_data()), places=4)

        self.img_model.set_supersampling(2)
        self.img_model.get_img_data()

    def test_absorption_correction_with_different_image_sizes(self):
        dummy_correction = DummyCorrection(self.img_model.get_img_data().shape, 0.4)
        # self.img_data.set_absorption_correction(np.ones(self.img_data._img_data.shape)*0.4)
        self.img_model.add_img_correction(dummy_correction, "Dummy 1")
        self.assertTrue(self.img_model._img_corrections.has_items())


        self.img_model.load(os.path.join(data_path, 'CeO2_Pilatus1M.tif'))
        self.assertFalse(self.img_model.has_corrections())

    def test_adding_several_absorption_corrections(self):
        original_image = np.copy(self.img_model.get_img_data())
        img_shape = original_image.shape
        self.img_model.add_img_correction(DummyCorrection(img_shape, 0.4))
        self.img_model.add_img_correction(DummyCorrection(img_shape, 3))
        self.img_model.add_img_correction(DummyCorrection(img_shape, 5))

        self.assertTrue(np.sum(original_image)/(0.5*3*5), np.sum(self.img_model.get_img_data()))

        self.img_model.delete_img_correction(1)
        self.assertTrue(np.sum(original_image)/(0.5*5), np.sum(self.img_model.get_img_data()))


    def test_saving_data(self):
        self.img_model.load(os.path.join(data_path, 'image_001.tif'))
        filename = os.path.join(data_path, 'test.tif')
        self.img_model.save(filename)
        first_img_array = np.copy(self.img_model._img_data)
        self.img_model.load(filename)
        self.assertTrue(np.array_equal(first_img_array, self.img_model._img_data))
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)


    def test_rotation(self):
        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_m90()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))
        self.img_model.reset_img_transformations()

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_p90()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))
        self.img_model.reset_img_transformations()

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.flip_img_horizontally()
        self.img_model.flip_img_horizontally()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))
        self.img_model.reset_img_transformations()

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.flip_img_vertically()
        self.img_model.flip_img_vertically()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))
        self.img_model.reset_img_transformations()

        self.img_model.flip_img_vertically()
        self.img_model.flip_img_horizontally()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_p90()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_m90()
        self.img_model.flip_img_horizontally()
        transformed_data = self.img_model.get_img_data()
        self.img_model.load(os.path.join(data_path, 'image_001.tif'))
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), transformed_data))
        self.img_model.reset_img_transformations()

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.rotate_img_m90()
        self.img_model.reset_img_transformations()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.rotate_img_p90()
        self.img_model.reset_img_transformations()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.flip_img_horizontally()
        self.img_model.reset_img_transformations()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.flip_img_vertically()
        self.img_model.reset_img_transformations()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))

        pre_transformed_data = self.img_model.get_img_data()
        self.img_model.flip_img_vertically()
        self.img_model.flip_img_horizontally()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_p90()
        self.img_model.rotate_img_m90()
        self.img_model.rotate_img_m90()
        self.img_model.flip_img_horizontally()
        self.img_model.reset_img_transformations()
        self.assertTrue(np.array_equal(self.img_model.get_img_data(), pre_transformed_data))


if __name__ == '__main__':
    unittest.main()