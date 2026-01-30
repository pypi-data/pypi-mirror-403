from pyscf import lib, gto
from tblite.interface import Calculator
import numpy as np

class XTB(lib.StreamObject):
    def __init__(self, mol, method="GFN2-xTB"):
        self.mol = mol
        self.method = method
        self.verbose = mol.verbose
        self.stdout = mol.stdout
        self.e_tot = None
        self._last_grad = None

    def kernel(self):
        coords = self.mol.atom_coords()
        numbers = self.mol.atom_charges()
        
        calc = Calculator(
            method=self.method,
            numbers=numbers,
            positions=coords,
            charge=self.mol.charge,
            uhf=self.mol.spin
        )
        
        res = calc.singlepoint()
        self.e_tot = res.get("energy")
        self._last_grad = res.get("gradient")
        
        # Store orbital data for Koopmans' theorem and other analyses
        self.mo_energy = res.get("orbital-energies")
        self.mo_occ = res.get("orbital-occupations")
        
        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(self, 'xTB energy = %.15g', self.e_tot)
            
        return self.e_tot

    def Gradients(self):
        return Gradients(self)

    def Hessian(self):
        return Hessian(self)

class Gradients(lib.StreamObject):
    def __init__(self, method):
        self.base = method
        self.mol = method.mol
        self.verbose = method.verbose
        self.stdout = method.stdout

    def kernel(self):
        if self.base.e_tot is None or self.base._last_grad is None:
             self.base.kernel()
        return self.base._last_grad

class Hessian(lib.StreamObject):
    def __init__(self, method):
        self.base = method
        self.mol = method.mol
        self.verbose = method.verbose
        self.stdout = method.stdout

    def kernel(self):
        # Numerical Hessian by finite difference of gradients
        mol = self.mol
        natm = mol.natm
        
        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(self.base, "Calculating numerical Hessian for xTB...")
            
        # Step size for finite difference (Bohr)
        h = 0.005 
        
        hess = np.zeros((natm*3, natm*3))
        
        # We need a fresh calculator for displacements
        coords_ref = mol.atom_coords()
        numbers = mol.atom_charges()
        method = self.base.method
        charge = mol.charge
        uhf = mol.spin
        
        def get_grad(coords):
            calc = Calculator(
                method=method, numbers=numbers, positions=coords,
                charge=charge, uhf=uhf
            )
            res = calc.singlepoint()
            return res.get("gradient").flatten()

        for i in range(natm * 3):
            atom_idx = i // 3
            coord_idx = i % 3
            
            # Displace +h
            coords_plus = coords_ref.copy()
            coords_plus[atom_idx, coord_idx] += h
            g_plus = get_grad(coords_plus)
            
            # Displace -h
            coords_minus = coords_ref.copy()
            coords_minus[atom_idx, coord_idx] -= h
            g_minus = get_grad(coords_minus)
            
            # Central difference
            # d2E/dx_i dx_j = d(dE/dx_j) / dx_i ~ (g_j(+) - g_j(-)) / 2h
            # Row i of Hessian
            hess[i, :] = (g_plus - g_minus) / (2 * h)
            
        # Symmetrize
        hess = (hess + hess.T) / 2.0
        
        # Reshape to (natm, natm, 3, 3) for PySCF harmonic analysis
        # Current shape (natm*3, natm*3) corresponds to (natm, 3, natm, 3) -> (A, x, B, y)
        # We need (A, B, x, y)
        hess_reshaped = hess.reshape(natm, 3, natm, 3).transpose(0, 2, 1, 3)
        return hess_reshaped

# Inject to Mole
gto.Mole.sXTB = lib.class_as_method(XTB)