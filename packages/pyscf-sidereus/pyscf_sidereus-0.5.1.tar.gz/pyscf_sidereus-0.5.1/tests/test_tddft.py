import pyscf
import pyscf.sidereus
import pytest
import os
import numpy as np

class TestTDDFT:
    def setup_method(self, method):
        # Ethylene
        self.atom = "C 0 0 0; C 0 0 1.33; H 0 0.92 -0.54; H 0 -0.92 -0.54; H 0 0.92 1.87; H 0 -0.92 1.87"
        if os.path.exists("tddft_spectrum.png"):
            os.remove("tddft_spectrum.png")

    def teardown_method(self, method):
        if os.path.exists("tddft_spectrum.png"):
            os.remove("tddft_spectrum.png")

    def test_tddft_rhf(self):
        mol = pyscf.M(atom=self.atom, basis="sto-3g")
        mf = mol.RHF()
        mf.kernel()
        
        # TDDFT
        nstates = 3
        tddft = mf.sTDDFT(nstates=nstates)
        e, f = tddft.kernel()
        
        assert len(e) == nstates
        assert len(f) == nstates
        assert np.all(e > 0)
        
        # Plot
        tddft.summary(spectrum="tddft_spectrum.png")
        assert os.path.exists("tddft_spectrum.png")
        
        print("\nExcitation Energies (eV):", e * 27.2114)
        print("Oscillator Strengths:", f)