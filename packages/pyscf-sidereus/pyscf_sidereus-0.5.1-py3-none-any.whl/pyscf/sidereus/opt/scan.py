from pyscf import lib, scf
from .rhf import OPT as RHFOPT
import numpy as np
from copy import deepcopy
from ..utils import rdkit as rdkit_utils

class SCAN(lib.StreamObject):
    def __init__(self, mf, scans, **kwargs):
        self.mf = mf
        self.mol = mf.mol
        self.scans = scans
        self.verbose = mf.verbose
        self.stdout = mf.stdout
        self.kwargs = kwargs
        self.scan_results = {
            "energies": [],
            "geometries": [],
            "coords": [] 
        }

    def kernel(self):
        return self.run_scan()

    def run_scan(self):
        steps = self.scans[0].get("steps", 10)
        for s in self.scans:
            if s.get("steps", 10) != steps:
                raise ValueError("All scan coordinates must have the same number of steps.")
        
        num_points = steps + 1
        
        scan_values = []
        for s in self.scans:
            start = s.get("start")
            stop = s.get("stop")
            if start is None or stop is None:
                 raise ValueError("Scan start and stop must be defined.")
            vals = np.linspace(start, stop, num_points)
            scan_values.append(vals)
            
        # Ensure RDKit availability
        try:
            from rdkit.Chem import rdMolTransforms
        except ImportError:
            raise ImportError("RDKit is required for geometry manipulation in SCAN.")

        for i in range(num_points):
            if self.verbose >= lib.logger.NOTE:
                lib.logger.note(self.mf, f"Scan step {i+1}/{num_points}")
            
            # Modify Geometry
            rd_mol = rdkit_utils.pyscf2rdmol(self.mf.mol)
            conf = rd_mol.GetConformer()
            
            current_vals = []
            current_constraints = []
            
            for j, s in enumerate(self.scans):
                val = float(scan_values[j][i])
                current_vals.append(val)
                atoms = s["atoms"]
                type_ = s["type"].lower()
                
                # Update RDKit Geometry
                if type_ == "bond":
                    rdMolTransforms.SetBondLength(conf, atoms[0], atoms[1], val)
                elif type_ == "angle":
                    rdMolTransforms.SetAngleDeg(conf, atoms[0], atoms[1], atoms[2], val)
                elif type_ == "dihedral":
                    rdMolTransforms.SetDihedralDeg(conf, atoms[0], atoms[1], atoms[2], atoms[3], val)
                
                # Map type to pysisyphus terminology
                pysis_type_map = {
                    "bond": "bond",
                    "stretch": "bond",
                    "angle": "bend",
                    "bend": "bend",
                    "dihedral": "torsion",
                    "torsion": "torsion"
                }
                pysis_type = pysis_type_map.get(type_, type_)
                
                # Constraint for pysisyphus: [type, atom1, atom2, ...]
                constr_list = [pysis_type] + list(atoms)
                current_constraints.append(constr_list)

            # Update PySCF mol
            new_coords = rdkit_utils.get_coords(rd_mol)
            rdkit_utils.set_coords(self.mf.mol, new_coords)
            
            # Run Constrained Optimization
            opt = self.mf.sOPT(constraints=current_constraints, **self.kwargs)
            mol_opt = opt.kernel()
            
            # Store results
            # Force recalculation of energy for the optimized geometry
            e = self.mf.kernel()
                
            self.scan_results["energies"].append(e)
            self.scan_results["geometries"].append(mol_opt.atom_coords())
            self.scan_results["coords"].append(current_vals)
            
        return self.scan_results

# Register to SCF and XTB
scf.hf.SCF.sSCAN = lib.class_as_method(SCAN)
try:
    from ..xtb import XTB
    XTB.sSCAN = lib.class_as_method(SCAN)
except ImportError:
    pass
