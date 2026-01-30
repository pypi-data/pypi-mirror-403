import pyscf
import pyscf.sidereus
import pytest
import numpy as np

class TestScanTypes:
    def test_scan_angle_h2o(self):
        # Water: O at origin, H at roughly equilibrium
        atom = "O 0 0 0; H 0 0.757 0.586; H 0 -0.757 0.586"
        mol = pyscf.M(atom=atom)
        mf = mol.sXTB(method="GFN2-xTB")
        
        # Scan H-O-H angle (atoms 1-0-2) from 100 to 110 degrees
        scans = [
            {"type": "angle", "atoms": [1, 0, 2], "start": 100.0, "stop": 110.0, "steps": 3}
        ]
        
        results = mf.sSCAN(scans=scans).kernel()
        assert len(results["energies"]) == 4 # 3 steps + 1
        # Check coordinates consistency
        coords = results["coords"]
        assert np.allclose(coords[0], [100.0])
        assert np.allclose(coords[-1], [110.0])

    def test_scan_dihedral_h2o2(self):
        # H2O2
        atom = """
        O 0.000000 0.707107 0.050000
        O 0.000000 -0.707107 0.050000
        H 0.890000 0.890000 -0.450000
        H -0.890000 -0.890000 -0.450000
        """
        mol = pyscf.M(atom=atom)
        mf = mol.sXTB(method="GFN2-xTB")
        
        # Scan H-O-O-H dihedral (atoms 2-0-1-3)
        scans = [
            {"type": "dihedral", "atoms": [2, 0, 1, 3], "start": 90.0, "stop": 120.0, "steps": 3}
        ]
        
        results = mf.sSCAN(scans=scans).kernel()
        assert len(results["energies"]) == 4
        print("\nDihedral Energies:", results["energies"])
