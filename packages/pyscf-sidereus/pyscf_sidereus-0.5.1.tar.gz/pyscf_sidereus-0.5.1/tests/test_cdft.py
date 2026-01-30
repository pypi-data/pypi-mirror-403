import pyscf
import pyscf.sidereus
import numpy as np
import pytest
import os
import glob

class TestCDFT:
    def setup_method(self, method):
        self.atom = "H 0 0 0; F 0 0 0.917"

    def test_cdft_xtb_fmo(self):
        mol = pyscf.M(atom=self.atom)
        mf = mol.sXTB(method="GFN2-xTB")
        mf.kernel()
        
        # FMO Method
        print("\nTesting XTB FMO...")
        res = mf.sCDFT(method="fmo").kernel()
        
        # Check structure
        assert "global" in res
        assert "atomic" in res
        
        # Check Global
        glob = res["global"]
        assert "VIP" in glob
        assert "Hardness" in glob
        assert glob["VIP"] > 0
        
        # Check Atomic
        atom = res["atomic"]
        assert "f+" in atom
        assert len(atom["f+"]) == mol.natm
        
        # Check new descriptors
        assert "s+" in atom
        assert "omega+" in atom
        assert "n-" in atom

    def test_cdft_xtb_fd(self):
        mol = pyscf.M(atom=self.atom)
        mf = mol.sXTB(method="GFN2-xTB")
        mf.kernel()
        
        # FD Method
        print("\nTesting XTB FD...")
        res = mf.sCDFT(method="fd").kernel()
        
        glob = res["global"]
        atom = res["atomic"]
        
        print("FD Global:", glob)
        print("FD Atomic f+:", atom["f+"])
        
        assert glob["VIP"] > 0
        assert np.abs(np.sum(atom["f+"]) - 1.0) < 0.2
        
        assert "s-" in atom

    def test_cdft_rhf_fmo(self):
        mol = pyscf.M(atom=self.atom, basis='sto-3g')
        mf = mol.RHF()
        mf.kernel()
        
        print("\nTesting RHF FMO...")
        res = mf.sCDFT(method="fmo").kernel()
        
        glob = res["global"]
        atom = res["atomic"]
        
        assert glob["VIP"] > 0
        assert np.sum(atom["f-"]) > 0.9
        assert "omega+" in atom

    def test_cdft_rhf_fd(self):
        mol = pyscf.M(atom=self.atom, basis='sto-3g')
        mf = mol.RHF()
        mf.kernel()
        
        print("\nTesting RHF FD...")
        res = mf.sCDFT(method="fd").kernel()
        
        glob = res["global"]
        atom = res["atomic"]
        
        assert glob["VIP"] > 0
        assert np.sum(atom["f+"]) > 0.8


class TestSpatial:
    def setup_method(self, method):
        self.atom = "H 0 0 0; F 0 0 0.917"
        # Cleanup cube files before test
        for f in glob.glob("*.cube"):
            os.remove(f)

    def teardown_method(self, method):
        # Cleanup cube files after test
        for f in glob.glob("*.cube"):
            os.remove(f)

    def test_spatial_rhf_fmo(self):
        mol = pyscf.M(atom=self.atom, basis='sto-3g')
        mf = mol.RHF()
        mf.kernel()
        
        print("\nTesting RHF FMO Spatial...")
        # New API: .spatial().kernel()
        res = mf.sCDFT(method="fmo").spatial(nx=40, ny=40, nz=40).kernel()
        
        files = res
        assert files is not None
        # 4 Fukui + 4 Softness + 1 Electrophilicity + 1 Nucleophilicity = 10 files
        assert len(files) == 10
        for f in files:
            assert os.path.exists(f)
            
    def test_spatial_rhf_fd(self):
        mol = pyscf.M(atom=self.atom, basis='sto-3g')
        mf = mol.RHF()
        mf.kernel()
        
        print("\nTesting RHF FD Spatial...")
        res = mf.sCDFT(method="fd").spatial(nx=40, ny=40, nz=40).kernel()
        
        files = res
        assert files is not None
        assert len(files) == 10
        for f in files:
            assert os.path.exists(f)

    def test_spatial_xtb_warning(self):
        # Should warn and return None for spatial
        mol = pyscf.M(atom=self.atom)
        mf = mol.sXTB(method="GFN2-xTB")
        mf.kernel()
        
        print("\nTesting XTB Spatial Warning...")
        res = mf.sCDFT(method="fmo").spatial().kernel()
        
        assert res is None