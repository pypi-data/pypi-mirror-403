from pyscf import lib, scf, dft
import numpy as np

try:
    from ..xtb import XTB
    HAS_XTB = True
except ImportError:
    HAS_XTB = False

def get_homo_lumo(mf):
    if not hasattr(mf, "mo_energy") or not hasattr(mf, "mo_occ"):
            raise RuntimeError("Orbital data missing.")

    mo_energy = mf.mo_energy
    mo_occ = mf.mo_occ
    
    is_uhf = False
    if isinstance(mo_energy, tuple) or (isinstance(mo_energy, np.ndarray) and mo_energy.ndim == 2 and mo_energy.shape[0] == 2):
            is_uhf = True
            
    deg_thr = 1e-4

    if is_uhf:
        if isinstance(mo_energy, tuple):
            ea_a, ea_b = mo_energy
            occ_a, occ_b = mo_occ
        else:
            ea_a, ea_b = mo_energy[0], mo_energy[1]
            occ_a, occ_b = mo_occ[0], mo_occ[1]
        
        def get_idx_e(e, o):
            e = np.asarray(e)
            o = np.asarray(o)
            occ_idx = np.where(o > 1e-6)[0]
            virt_idx = np.where(o <= 1e-6)[0]
            
            # Highest occupied energy
            h_idx = occ_idx[-1] if len(occ_idx) > 0 else None
            h_e = e[h_idx] if h_idx is not None else -np.inf
            
            # Lowest virtual energy
            l_idx = virt_idx[0] if len(virt_idx) > 0 else None
            l_e = e[l_idx] if l_idx is not None else np.inf
            
            # Check degeneracy
            h_idxs = []
            if h_idx is not None:
                # Find all occupied orbitals degenerate with HOMO
                # Note: usually we check occupied ones. 
                # e[occ_idx] check against h_e
                deg_mask = (np.abs(e[occ_idx] - h_e) < deg_thr)
                h_idxs = occ_idx[deg_mask].tolist()
                
            l_idxs = []
            if l_idx is not None:
                # Find all virtual orbitals degenerate with LUMO
                deg_mask = (np.abs(e[virt_idx] - l_e) < deg_thr)
                l_idxs = virt_idx[deg_mask].tolist()
                
            return h_idxs, l_idxs, h_e, l_e
        
        idxs_ha, idxs_la, ha, la = get_idx_e(ea_a, occ_a)
        idxs_hb, idxs_lb, hb, lb = get_idx_e(ea_b, occ_b)
        
        return {
            "is_uhf": True,
            "ha": (idxs_ha, ha), "la": (idxs_la, la),
            "hb": (idxs_hb, hb), "lb": (idxs_lb, lb),
            "homo_e": max(ha, hb), "lumo_e": min(la, lb)
        }
    else:
        e = np.asarray(mo_energy)
        o = np.asarray(mo_occ)
        occ_idx = np.where(o > 1e-6)[0]
        virt_idx = np.where(o <= 1e-6)[0]
        
        h_idx = occ_idx[-1] if len(occ_idx) > 0 else None
        h_e = e[h_idx] if h_idx is not None else -np.inf
        
        l_idx = virt_idx[0] if len(virt_idx) > 0 else None
        l_e = e[l_idx] if l_idx is not None else np.inf
        
        h_idxs = []
        if h_idx is not None:
            deg_mask = (np.abs(e[occ_idx] - h_e) < deg_thr)
            h_idxs = occ_idx[deg_mask].tolist()
            
        l_idxs = []
        if l_idx is not None:
            deg_mask = (np.abs(e[virt_idx] - l_e) < deg_thr)
            l_idxs = virt_idx[deg_mask].tolist()
        
        return {
            "is_uhf": False,
            "h": (h_idxs, h_e), "l": (l_idxs, l_e),
            "homo_e": h_e, "lumo_e": l_e
        }

def run_fd_calc(mf, charge_delta, cache=None):
    if cache is not None and charge_delta in cache:
        return cache[charge_delta]

    mol_neu = mf.mol
    mol_new = mol_neu.copy()
    mol_new.charge += charge_delta

    nelec = mol_new.nelectron
    if nelec % 2 == 1:
        mol_new.spin = 1
    else:
        mol_new.spin = 0
    mol_new.build(0, 0)

    if HAS_XTB and isinstance(mf, XTB):
        mf_new = mol_new.sXTB(method=mf.method)
        mf_new.verbose = 0
        
        from tblite.interface import Calculator
        calc = Calculator(
            method=mf_new.method,
            numbers=mol_new.atom_charges(),
            positions=mol_new.atom_coords(),
            charge=mol_new.charge,
            uhf=mol_new.spin
        )
        res = calc.singlepoint()
        e_tot = res.get("energy")
        charges = res.get("charges")
        density = None
        
        res_tuple = (e_tot, charges, density)
        if cache is not None: cache[charge_delta] = res_tuple
        return res_tuple
    else:
        mf_cls = mf.__class__
        if not getattr(mf, 'unrestricted', False) and mol_new.spin != 0:
            if issubclass(mf_cls, scf.hf.RHF): mf_cls = scf.uhf.UHF
            elif issubclass(mf_cls, dft.rks.RKS): mf_cls = dft.uks.UKS
        mf_new = mf_cls(mol_new)
        if hasattr(mf, 'xc'): mf_new.xc = mf.xc
        if hasattr(mf, 'grids'): mf_new.grids = mf.grids
        mf_new.verbose = 0
        mf_new.run()

        e_tot = mf_new.e_tot
        pop, chg = mf_new.mulliken_pop(verbose=0)
        charges = chg

        density = mf_new.make_rdm1()

        res_tuple = (e_tot, charges, density)
        if cache is not None: cache[charge_delta] = res_tuple
        return res_tuple

def compute_global_from_vip_vea(vip, vea, homo):
    chi = (vip + vea) / 2.0
    mu = -chi
    eta = vip - vea
    
    if abs(eta) > 1e-12:
        s_val = 1.0 / eta
        omega = (mu ** 2) / (2 * eta)
    else:
        s_val = np.inf
        omega = np.inf
        
    n_nu = homo
    
    return {
        "VIP": vip, "VEA": vea, "Mulliken Electronegativity": chi,
        "Chemical Potential": mu, "Hardness": eta, "Softness": s_val,
        "Electrophilicity Index": omega, "Nucleophilicity Index": n_nu
    }

def calculate_global_scalars(mf, method="fmo", cache=None):
    if method == "fmo":
        hl = get_homo_lumo(mf)
        homo, lumo = hl["homo_e"], hl["lumo_e"]
        return compute_global_from_vip_vea(-homo, -lumo, homo)
    else:
        e_neu, _, _ = run_fd_calc(mf, 0, cache)
        e_cat, _, _ = run_fd_calc(mf, 1, cache)
        e_an, _, _ = run_fd_calc(mf, -1, cache)
        
        vip = e_cat - e_neu
        vea = e_neu - e_an
        homo_proxy = -vip
        return compute_global_from_vip_vea(vip, vea, homo_proxy)
