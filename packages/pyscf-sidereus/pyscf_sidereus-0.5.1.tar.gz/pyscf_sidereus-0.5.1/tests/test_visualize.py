import pyscf
import pyscf.sidereus
import os
import pytest


class TestVisualize:
    def setup_method(self, method):
        self.atom = "H 0 0 0; F 0 0 0.917"
        if os.path.exists("test_viz.png"):
            os.remove("test_viz.png")

    def teardown_method(self, method):
        if os.path.exists("test_viz.png"):
            os.remove("test_viz.png")

    def test_visualize_f_plus(self):
        mol = pyscf.M(atom=self.atom)
        mf = mol.sXTB(method="GFN2-xTB")
        mf.kernel()

        # Calculate descriptors
        cdft = mf.sCDFT(method="fmo")
        cdft.kernel()

        # Visualize
        print("\nTesting Visualization...")
        cdft.visualize("f+", "test_viz.png")

        assert os.path.exists("test_viz.png")
