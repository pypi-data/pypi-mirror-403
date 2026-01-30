from pyscf import lib, scf
from pyscf.hessian import thermo
import numpy as np

class THERMO(lib.StreamObject):
    def __init__(self, mf, temp=298.15, press=101325):
        self.mf = mf
        self.mol = mf.mol
        self.temp = temp
        self.press = press
        self.verbose = mf.verbose
        self.stdout = mf.stdout
        self.results = {}

    def kernel(self, hessian=None):
        if self.mf.e_tot is None:
            self.mf.kernel()

        if hessian is None:
            if self.verbose >= lib.logger.NOTE:
                lib.logger.note(self.mf, "Calculating Hessian...")
            hessian = self.mf.Hessian().kernel()
        
        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(self.mf, "Performing harmonic analysis...")
            if hasattr(hessian, "shape"):
                lib.logger.note(self.mf, f"Hessian shape: {hessian.shape}")
        ha_res = thermo.harmonic_analysis(self.mol, hessian)
        
        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(self.mf, "Calculating thermodynamic properties at T=%.2f K, P=%.2f Pa...", 
                            self.temp, self.press)
        results = thermo.thermo(self.mf, ha_res["freq_au"], self.temp, self.press)
        
        self.results = results
        self.results["vib_dict"] = ha_res
        
        # Add convenient shortcuts
        self.G = results.get("G_tot", (None, None))[0]
        self.H = results.get("H_tot", (None, None))[0]
        self.S = results.get("S_tot", (None, None))[0]
        
        if self.verbose >= lib.logger.NOTE:
            self.summary()
            
        return self.results

    def summary(self):
        thermo.dump_thermo(self.mol, self.results)

# Inject to SCF
scf.hf.SCF.sTHERMO = lib.class_as_method(THERMO)

# Handle sXTB if it exists
try:
    from .xtb import XTB
    XTB.sTHERMO = lib.class_as_method(THERMO)
except ImportError:
    pass