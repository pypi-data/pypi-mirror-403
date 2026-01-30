import pyscf
import pyscf.sidereus
import os
import glob
import pytest

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
