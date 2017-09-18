#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for testing the satpy.readers.hdf4_utils module.
"""

import os
import sys
import numpy as np
from satpy.readers.netcdf_utils import NetCDF4FileHandler
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class FakeNetCDF4FileHandler(NetCDF4FileHandler):
    """Swap-in NetCDF4 File Handler for reader tests to use"""
    def __init__(self, filename, filename_info, filetype_info, **kwargs):
        """Get fake file content from 'get_test_content'"""
        super(NetCDF4FileHandler, self).__init__(filename, filename_info, filetype_info)
        self.file_content = self.get_test_content(filename, filename_info, filetype_info)
        self.file_content.update(kwargs)

    def get_test_content(self, filename, filename_info, filetype_info):
        """Mimic reader input file content
        
        Args:
            filename (str): input filename 
            filename_info (dict): Dict of metadata pulled from filename
            filetype_info (dict): Dict of metadata from the reader's yaml config for this file type

        Returns: dict of file content with keys like:
        
            - 'dataset'
            - '/attr/global_attr'
            - 'dataset/attr/global_attr'
            - 'dataset/shape'
            - '/dimension/my_dim'

        """
        raise NotImplementedError("Fake File Handler subclass must implement 'get_test_content'")


class TestNetCDF4FileHandler(unittest.TestCase):
    """Test NetCDF4 File Handler Utility class"""
    def setUp(self):
        """Create a test NetCDF4 file"""
        from pyhdf.SD import SD, SDC
        h = SD('test.hdf', SDC.WRITE | SDC.CREATE | SDC.TRUNC)
        data = np.arange(10. * 100, dtype=np.float32).reshape((10, 100))
        v1 = h.create('ds1_f', SDC.FLOAT32, (10, 100))
        v1[:] = data
        v2 = h.create('ds1_i', SDC.INT16, (10, 100))
        v2[:] = data.astype(np.int16)

        # Add attributes
        h.test_attr_str = 'test_string'
        h.test_attr_int = 0
        h.test_attr_float = 1.2
        # h.test_attr_str_arr = np.array(b"test_string2")
        for d in [v1, v2]:
            d.test_attr_str = 'test_string'
            d.test_attr_int = 0
            d.test_attr_float = 1.2

        h.end()

    def tearDown(self):
        """Remove the previously created test file"""
        os.remove('test.hdf')

    def test_all_basic(self):
        """Test everything about the NetCDF4 class"""
        from satpy.readers.hdf4_utils import HDF4FileHandler
        from pyhdf.SD import SDC
        file_handler = HDF4FileHandler('test.hdf', {}, {})

        for ds in ('ds1_f', 'ds1_i'):
            self.assertEqual(file_handler[ds + '/dtype'], np.float32 if ds.endswith('f') else np.int16)
            self.assertTupleEqual(file_handler[ds + '/shape'], (10, 100))
            self.assertEqual(file_handler[ds + '/attr/test_attr_str'], 'test_string')
            self.assertEqual(file_handler[ds + '/attr/test_attr_int'], 0)
            self.assertEqual(file_handler[ds + '/attr/test_attr_float'], 1.2)

        self.assertEqual(file_handler['/attr/test_attr_str'], 'test_string')
        # self.assertEqual(file_handler['/attr/test_attr_str_arr'], 'test_string2')
        self.assertEqual(file_handler['/attr/test_attr_int'], 0)
        self.assertEqual(file_handler['/attr/test_attr_float'], 1.2)

        self.assertIsInstance(file_handler.get('ds1_f')[:], np.ndarray)
        self.assertIsNone(file_handler.get('fake_ds'))
        self.assertEqual(file_handler.get('fake_ds', 'test'), 'test')

        self.assertTrue('ds1_f' in file_handler)
        self.assertFalse('fake_ds' in file_handler)


def suite():
    """The test suite for test_netcdf_utils.
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestNetCDF4FileHandler))

    return mysuite