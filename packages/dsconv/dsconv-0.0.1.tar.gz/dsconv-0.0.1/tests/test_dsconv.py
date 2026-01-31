#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

import numpy as np

from dsconv import dsconv


class TestConv(unittest.TestCase):

    def test_dsconv(self):
        """Test of the function 'dsconv'."""
        f = np.random.randn(16, 2)
        x = np.random.randn(1024)
        y1 = np.convolve(x, f[:, 0], mode='same')[::2]
        y2 = np.convolve(x, f[:, 1], mode='same')[::2]
        y = np.hstack((y1, y2))
        z = dsconv(
            x.reshape(-1, 1),
            f,
            mode='same',
            offset=0,
        ).reshape(-1)
        self.assertTrue(np.allclose(y, z))


if __name__ == "__main__":
    unittest.main()
