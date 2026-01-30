import pyscf
import pyscf.sidereus
import pytest

class TestThermo:
    def setup_method(self, method):
        self.atom = "H 0 0 0; H 0 0 0.74"

    def test_thermo_rhf(self):
        mol = pyscf.M(atom=self.atom, basis="sto-3g")
        mf = mol.RHF()
        mf.kernel()
        
        # Calculate thermo
        th = mf.sTHERMO()
        res = th.kernel()
        
        assert "G_tot" in res
        assert "H_tot" in res
        assert "S_tot" in res
        
        # Check shortcuts
        assert th.G is not None
        assert th.H is not None
        assert th.S is not None
        
        print(f"\nFree energy G: {th.G}")