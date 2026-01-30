from pyscf import lib, scf, dft
import numpy as np

try:
    from ..xtb import XTB
    HAS_XTB = True
except ImportError:
    HAS_XTB = False
    
from . import utils

class Descriptors(lib.StreamObject):
    def __init__(self, mf, method="fmo"):
        self.mf = mf
        self.method = method.lower()
        if self.method not in ["fmo", "fd"]:
            raise ValueError("Method must be 'fmo' or 'fd'")
        self.verbose = mf.verbose
        self.stdout = mf.stdout
        self.results = {}
        
        # Cache for FD calculations
        self._cache = {}

    def kernel(self):
        if self.mf.e_tot is None:
            self.mf.kernel()

        # 1. Global Descriptors
        global_res = utils.calculate_global_scalars(self.mf, self.method, self._cache)
        self.results["global"] = global_res
        
        # 2. Atomic Descriptors
        if self.method == "fmo":
            atomic_res = self._calculate_atomic_fmo(global_res)
        else:
            atomic_res = self._calculate_atomic_fd(global_res)
        self.results["atomic"] = atomic_res
             
        self._print_summary()
        return self.results

    def _calculate_atomic_fd(self, global_res):
        _, q_neu, _ = utils.run_fd_calc(self.mf, 0, self._cache)
        _, q_cat, _ = utils.run_fd_calc(self.mf, 1, self._cache)
        _, q_an, _ = utils.run_fd_calc(self.mf, -1, self._cache)
        
        f_plus = q_neu - q_an    
        f_minus = q_cat - q_neu  
        f_zero = (q_cat - q_an) / 2.0
        dual = f_plus - f_minus
        
        return self._compute_atomic_derived(f_plus, f_minus, f_zero, dual, global_res)

    def _calculate_atomic_fmo(self, global_res):        
        if HAS_XTB and isinstance(self.mf, XTB):
            if self.verbose >= lib.logger.WARN:
                lib.logger.warn(self.mf, "FMO Atomic descriptors not implemented for sXTB. Using FD.")
            return self._calculate_atomic_fd(global_res)

        hl = utils.get_homo_lumo(self.mf)
        mol = self.mf.mol
        
        def get_orb_pop(idxs, spin=None):
            if not idxs: return np.zeros(mol.natm)
            
            total_pop = np.zeros(mol.natm)
            
            for idx in idxs:
                if hl["is_uhf"]:
                    mo_coeff = self.mf.mo_coeff[spin]
                    mo = mo_coeff[:, idx]
                else:
                    mo_coeff = self.mf.mo_coeff
                    mo = mo_coeff[:, idx]
                    
                dm = np.outer(mo, mo)
                s = self.mf.get_ovlp()
                pop_orb = np.einsum('ij,ji->i', dm, s).real
                
                pop_atm = np.zeros(mol.natm)
                for i, label in enumerate(mol.ao_labels(fmt=None)):
                    pop_atm[label[0]] += pop_orb[i]
                
                total_pop += pop_atm
            
            # Average over degenerate orbitals
            return total_pop / len(idxs)

        if hl["is_uhf"]:
            # Logic: Use the channel closer to global HOMO/LUMO energy
            # HOMO: max(ha, hb).
            if hl["ha"][1] > hl["hb"][1]:
                h_idxs, h_spin = hl["ha"][0], 0
            else:
                h_idxs, h_spin = hl["hb"][0], 1
                
            # LUMO: min(la, lb)
            if hl["la"][1] < hl["lb"][1]:
                l_idxs, l_spin = hl["la"][0], 0
            else:
                l_idxs, l_spin = hl["lb"][0], 1

            f_minus = get_orb_pop(h_idxs, h_spin)
            f_plus = get_orb_pop(l_idxs, l_spin)
        else:
            f_minus = get_orb_pop(hl["h"][0])
            f_plus = get_orb_pop(hl["l"][0])
            
        f_zero = (f_plus + f_minus) / 2.0
        dual = f_plus - f_minus
        
        return self._compute_atomic_derived(f_plus, f_minus, f_zero, dual, global_res)

    def _compute_atomic_derived(self, f_plus, f_minus, f_zero, dual, global_res):
        S = global_res.get("Softness", 0)
        omega = global_res.get("Electrophilicity Index", 0)
        N_nu = global_res.get("Nucleophilicity Index", 0)
        
        # Softness s(r) = S * f(r)
        s_plus = S * f_plus
        s_minus = S * f_minus
        s_zero = S * f_zero
        s_dual = S * dual
        
        # Local Electrophilicity omega_k = omega * f+_k
        omega_plus = omega * f_plus
        
        # Local Nucleophilicity N_k = N * f-_k
        n_minus = N_nu * f_minus
        
        return {
            "f+": f_plus, "f-": f_minus, "f0": f_zero, "dual": dual,
            "s+": s_plus, "s-": s_minus, "s0": s_zero, "s_dual": s_dual,
            "omega+": omega_plus, "n-": n_minus
        }

    def _print_summary(self):
        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(self.mf, f"CDFT Descriptors (Method: {self.method.upper()})")
            
            lib.logger.note(self.mf, "Global:")
            for k, v in self.results["global"].items():
                lib.logger.note(self.mf, "  %-30s : % .6f", k, v)
            
            lib.logger.note(self.mf, "Atomic (Condensed Fukui & Derived) - First 5 atoms:")
            ats = self.results["atomic"]
            for i in range(min(5, self.mf.mol.natm)):
                lib.logger.note(self.mf, "  Atom %d: f+=%.3f f-=%.3f | s+=%.3f s-=%.3f | w+=%.3f n-=%.3f", 
                                i, ats["f+"][i], ats["f-"][i], 
                                ats["s+"][i], ats["s-"][i], 
                                ats["omega+"][i], ats["n-"][i])
