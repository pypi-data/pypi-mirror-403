import pyscf
import pyscf.sidereus
import pytest
import numpy as np

class TestScan:
    def setup_method(self, method):
        self.atom = "H 0 0 0; F 0 0 0.917"

    def test_scan_xtb(self):
        mol = pyscf.M(atom=self.atom)
        mf = mol.sXTB(method="GFN2-xTB")
        
        # Scan bond length from 0.8 to 1.2 Angstrom in 5 steps
        scans = [
            {"type": "bond", "atoms": [0, 1], "start": 0.8, "stop": 1.2, "steps": 5}
        ]
        
        # Run scan
        scanner = mf.sSCAN(scans=scans)
        results = scanner.kernel()
        
        print("\nScan Results:", results)
        
        assert results is not None
        assert "energies" in results
        assert len(results["energies"]) > 0
        # 5 steps usually means start + 5 steps or just 5 points? 
        # pysisyphus 'steps' usually means number of steps. Total points = steps + 1?
        # Let's check length.
        assert len(results["energies"]) >= 5
        
        # Check if energy changes (not flat)
        energies = results["energies"]
        assert np.std(energies) > 1e-4
