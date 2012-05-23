import unittest

import matplotlib.pyplot as plt

import glue
from glue.image_client import ImageClient

class DummyCoords(glue.coordinates.Coordinates):
    def pixel2world(self, *args):
        result = []
        for i,a in enumerate(args):
            result.append([aa * (i+1) for aa in a])
        return result

class TestImageClient(unittest.TestCase):
    def setUp(self):
        self.im = glue.example_data.test_image()
        self.cube = glue.example_data.test_cube()
        self.collect = glue.DataCollection()

    def tearDown(self):
        plt.close('all')

    def create_client_with_image(self):
        client = ImageClient(self.collect)
        self.collect.append(self.im)
        client.set_data(self.im)
        return client

    def create_client_with_cube(self):
        client = ImageClient(self.collect)
        self.collect.append(self.cube)
        client.set_data(self.cube)
        return client

    def test_empty_creation(self):
        client = ImageClient(self.collect)
        self.assertIsNone(client.display_data)

    def test_nonempty_creation(self):
        self.collect.append(self.im)
        client = ImageClient(self.collect)
        self.assertIsNone(client.display_data)
        self.assertFalse(self.im in client.layers)

    def test_invalid_add(self):
        client = ImageClient(self.collect)
        self.assertRaises(TypeError, client.add_layer, self.cube)

    def test_set_data(self):
        client = self.create_client_with_image()
        self.assertIs(client.display_data, self.im)

    def test_slice_disabled_for_2d(self):
        client = self.create_client_with_image()
        self.assertIsNone(client.slice_ind)
        self.assertRaises(IndexError, client.slice_ind, 10)

    def test_slice_disabled_for_no_data(self):
        client = ImageClient(self.collect)
        self.assertIsNone(client.slice_ind)
        self.assertRaises(IndexError, client.slice_ind, 10)

    def test_slice_enabled_for_3D(self):
        client = self.create_client_with_cube()
        self.assertIsNotNone(client.slice_ind)
        client.slice_ind = 5
        self.assertEquals(client.slice_ind, 5)

    def test_add_subset_via_method(self):
        client = ImageClient(self.collect)
        self.collect.append(self.im)
        s = self.im.create_subset()
        client.add_layer(s)
        self.assertTrue(s in client.layers)

    def test_remove_data(self):
        client = ImageClient(self.collect)
        self.collect.append(self.im)
        s = self.im.create_subset()
        client.add_layer(self.im)
        self.assertTrue(self.im in client.layers)
        self.assertTrue(s in client.layers)
        client.delete_layer(self.im)
        self.assertIsNone(client.display_data)
        self.assertFalse(self.im in client.layers)
        self.assertFalse(s in client.layers)

    def test_set_norm(self):
        client = self.create_client_with_image()
        self.assertTrue(client.display_data is not None)
        client.set_norm(vmin = 10, vmax = 100)
        self.assertEquals(client.layers[self.im].norm.vmin, 10)
        self.assertEquals(client.layers[self.im].norm.vmax, 100)

    def test_delete_data(self):
        client = self.create_client_with_image()
        client.delete_layer(self.im)
        self.assertFalse(self.im in client.layers)

    def test_set_attribute(self):
        client = self.create_client_with_image()
        atts = self.im.component_ids()
        self.assertTrue(len(atts) > 1)
        for att in atts:
            client.set_attribute(att)
            self.assertIs(client.display_attribute, att)

    def test_set_data_and_attribute(self):
        client = self.create_client_with_image()
        atts = self.im.component_ids()
        self.assertTrue(len(atts) > 1)
        for att in atts:
            client.set_data(self.im, attribute=att)
            self.assertIs(client.display_attribute, att)
            self.assertIs(client.display_data, self.im)

    def test_set_slice(self):
        client = self.create_client_with_image()
        self.assertRaises(IndexError, client.slice_ind, 10)

    def test_slice_bounds_2d(self):
        client = self.create_client_with_image()
        self.assertEquals(client.slice_bounds(), (0,0))

    def test_slice_bounds_3d(self):
        client = self.create_client_with_cube()
        shape = self.cube.shape
        self.assertEquals(client.slice_bounds(), (0, shape[2]-1))
        client.set_slice_ori(0)
        self.assertEquals(client.slice_bounds(), (0, shape[0]-1))
        client.set_slice_ori(1)
        self.assertEquals(client.slice_bounds(), (0, shape[1]-1))
        client.set_slice_ori(2)
        self.assertEquals(client.slice_bounds(), (0, shape[2]-1))

    def test_slice_ori_on_2d_raises(self):
        client = self.create_client_with_image()
        self.assertRaises(IndexError, client.set_slice_ori, 0)

    def test_slice_ori_out_of_bounds(self):
        client = self.create_client_with_image()
        self.collect.append(self.cube)
        client.set_data(self.cube)
        self.assertRaises(TypeError, client.set_slice_ori, 100)

    def test_apply_roi_2d(self):
        client = self.create_client_with_image()
        self.collect.append(self.cube)
        client.add_layer(self.cube)
        roi = glue.roi.PolygonalROI(vx = [10, 20, 20, 10],
                                    vy = [10, 10, 20, 20])
        client._apply_roi(roi)
        roi2 = self.im.edit_subset.subset_state.roi
        state = self.im.edit_subset.subset_state

        self.assertEquals(roi2.to_polygon()[0], roi.to_polygon()[0])
        self.assertEquals(roi2.to_polygon()[1], roi.to_polygon()[1])
        self.assertIs(state.xatt, self.im.get_world_component_id(1))
        self.assertIs(state.yatt, self.im.get_world_component_id(0))

        # subset only applied to active data
        roi3 = self.cube.edit_subset.subset_state
        self.assertFalse(isinstance(roi3, glue.subset.RoiSubsetState))

    def test_apply_roi_3d(self):
        client = self.create_client_with_cube()
        self.cube.coords = DummyCoords()
        roi = glue.roi.PolygonalROI( vx = [10, 20, 20, 10],
                                     vy =[10, 10, 20, 20])

        client.set_slice_ori(0)
        client._apply_roi(roi)
        state = self.cube.edit_subset.subset_state
        roi2 = state.roi
        self.assertIs(state.xatt, self.cube.get_world_component_id(2))
        self.assertIs(state.yatt, self.cube.get_world_component_id(1))
        self.assertEquals(roi2.to_polygon()[0], [10, 20, 20, 10])
        self.assertEquals(roi2.to_polygon()[1], [20, 20, 40, 40])

        client.set_slice_ori(1)
        client._apply_roi(roi)
        state = self.cube.edit_subset.subset_state
        roi2 = state.roi
        self.assertIs(state.xatt, self.cube.get_world_component_id(2))
        self.assertIs(state.yatt, self.cube.get_world_component_id(0))
        self.assertEquals(roi2.to_polygon()[0], [10, 20, 20, 10])
        self.assertEquals(roi2.to_polygon()[1], [30, 30, 60, 60])

        client.set_slice_ori(2)
        client._apply_roi(roi)
        state = self.cube.edit_subset.subset_state
        roi2 = state.roi
        self.assertIs(state.xatt, self.cube.get_world_component_id(1))
        self.assertIs(state.yatt, self.cube.get_world_component_id(0))
        self.assertEquals(roi2.to_polygon()[0], [20, 40, 40, 20])
        self.assertEquals(roi2.to_polygon()[1], [30, 30, 60, 60])




if __name__ == "__main__":
    unittest.main(failfast=True)