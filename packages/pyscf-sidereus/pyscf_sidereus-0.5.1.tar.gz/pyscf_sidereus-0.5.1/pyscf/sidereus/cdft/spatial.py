# Adapted from PySCF cubegen
import time
import numpy as np
import pyscf
from pyscf import lib
from pyscf import gto
from pyscf import df
from pyscf.dft import numint
from pyscf import __config__

try:
    from ..xtb import XTB
    HAS_XTB = True
except ImportError:
    HAS_XTB = False

from . import utils

RESOLUTION = getattr(__config__, 'cubegen_resolution', None)
BOX_MARGIN = getattr(__config__, 'cubegen_box_margin', 3.0)
ORIGIN = getattr(__config__, 'cubegen_box_origin', None)
EXTENT = getattr(__config__, 'cubegen_box_extent', None)

class Cube:
    def __init__(self, mol, nx=80, ny=80, nz=80, resolution=RESOLUTION,
                 margin=BOX_MARGIN, origin=ORIGIN, extent=EXTENT):
        from pyscf.pbc.gto import Cell
        self.mol = mol
        coord = mol.atom_coords()

        if isinstance(mol, Cell):
            self.box = mol.lattice_vectors()
            atom_center = (np.max(coord, axis=0) + np.min(coord, axis=0))/2
            box_center = (self.box[0] + self.box[1] + self.box[2])/2
            self.boxorig = atom_center - box_center
        else:
            if extent is None:
                extent = np.max(coord, axis=0) - np.min(coord, axis=0) + 2*margin
            self.box = np.diag(extent)

            if origin is None:
                origin = np.min(coord, axis=0) - margin
            self.boxorig = np.asarray(origin)

        if resolution is not None:
            nx, ny, nz = np.ceil(np.diag(self.box) / resolution).astype(int)

        self.nx = nx
        self.ny = ny
        self.nz = nz

        if isinstance(mol, Cell):
            self.xs = np.linspace(0, 1, nx, endpoint=False)
            self.ys = np.linspace(0, 1, ny, endpoint=False)
            self.zs = np.linspace(0, 1, nz, endpoint=False)
        else:
            self.xs = np.linspace(0, 1, nx, endpoint=True)
            self.ys = np.linspace(0, 1, ny, endpoint=True)
            self.zs = np.linspace(0, 1, nz, endpoint=True)

    def get_coords(self) :
        frac_coords = lib.cartesian_prod([self.xs, self.ys, self.zs])
        return frac_coords @ self.box + self.boxorig

    def get_ngrids(self):
        return self.nx * self.ny * self.nz

    def write(self, field, fname, comment=None):
        assert (field.ndim == 3)
        assert (field.shape == (self.nx, self.ny, self.nz))
        if comment is None:
            comment = 'Generic field'

        mol = self.mol
        coord = mol.atom_coords()
        with open(fname, 'w') as f:
            f.write(comment+'\n')
            f.write(f'PySCF Version: {pyscf.__version__}  Date: {time.ctime()}\n')
            f.write(f'{mol.natm:5d}')
            f.write('%12.6f%12.6f%12.6f\n' % tuple(self.boxorig.tolist()))
            dx = self.xs[-1] if len(self.xs) == 1 else self.xs[1]
            dy = self.ys[-1] if len(self.ys) == 1 else self.ys[1]
            dz = self.zs[-1] if len(self.zs) == 1 else self.zs[1]
            delta = (self.box.T * [dx,dy,dz]).T
            f.write(f'{self.nx:5d}{delta[0,0]:12.6f}{delta[0,1]:12.6f}{delta[0,2]:12.6f}\n')
            f.write(f'{self.ny:5d}{delta[1,0]:12.6f}{delta[1,1]:12.6f}{delta[1,2]:12.6f}\n')
            f.write(f'{self.nz:5d}{delta[2,0]:12.6f}{delta[2,1]:12.6f}{delta[2,2]:12.6f}\n')
            for ia in range(mol.natm):
                atmsymb = mol.atom_symbol(ia)
                f.write('%5d%12.6f'% (gto.charge(atmsymb), 0.))
                f.write('%12.6f%12.6f%12.6f\n' % tuple(coord[ia]))

            for ix in range(self.nx):
                for iy in range(self.ny):
                    for iz0, iz1 in lib.prange(0, self.nz, 6):
                        fmt = '%13.5E' * (iz1-iz0) + '\n'
                        f.write(fmt % tuple(field[ix,iy,iz0:iz1].tolist()))

def density_on_grid(mol, dm, nx=80, ny=80, nz=80, resolution=RESOLUTION, margin=BOX_MARGIN):
    from pyscf.pbc.gto import Cell
    cc = Cube(mol, nx, ny, nz, resolution, margin)
    GTOval = 'GTOval'
    if isinstance(mol, Cell): GTOval = 'PBC' + GTOval
    coords = cc.get_coords()
    ngrids = cc.get_ngrids()
    blksize = min(8000, ngrids)
    rho = np.empty(ngrids)
    for ip0, ip1 in lib.prange(0, ngrids, blksize):
        ao = mol.eval_gto(GTOval, coords[ip0:ip1])
        rho[ip0:ip1] = numint.eval_rho(mol, ao, dm)
    rho = rho.reshape(cc.nx,cc.ny,cc.nz)
    return cc, rho

def orbital_on_grid(mol, coeff, nx=80, ny=80, nz=80, resolution=RESOLUTION, margin=BOX_MARGIN):
    from pyscf.pbc.gto import Cell
    cc = Cube(mol, nx, ny, nz, resolution, margin)
    GTOval = 'GTOval'
    if isinstance(mol, Cell): GTOval = 'PBC' + GTOval
    coords = cc.get_coords()
    ngrids = cc.get_ngrids()
    blksize = min(8000, ngrids)
    orb = np.empty(ngrids)
    for ip0, ip1 in lib.prange(0, ngrids, blksize):
        ao = mol.eval_gto(GTOval, coords[ip0:ip1])
        orb[ip0:ip1] = np.dot(ao, coeff)
    orb = orb.reshape(cc.nx,cc.ny,cc.nz)
    return cc, orb

class Spatial(lib.StreamObject):
    def __init__(self, mf, method="fmo", nx=80, ny=80, nz=80, resolution=None, margin=3.0, prefix="cdft"):
        self.mf = mf
        self.method = method.lower()
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.resolution = resolution
        self.margin = margin
        self.prefix = prefix
        self.verbose = mf.verbose
        self.stdout = mf.stdout
        self.results = []

    def kernel(self):
        if HAS_XTB and isinstance(self.mf, XTB):
            if self.verbose >= lib.logger.WARN:
                lib.logger.warn(self.mf, "Spatial descriptors not supported for XTB (requires basis set grid evaluation).")
            return None

        if self.mf.e_tot is None:
            self.mf.kernel()

        global_scalars = utils.calculate_global_scalars(self.mf, self.method)

        kwargs = {
            "nx": self.nx, "ny": self.ny, "nz": self.nz, 
            "resolution": self.resolution, "margin": self.margin
        }

        if self.method == "fmo":
            hl = utils.get_homo_lumo(self.mf)
            
            def get_coeffs(idxs, spin=None):
                if not idxs: return []
                coeffs = []
                for idx in idxs:
                    if hl["is_uhf"]:
                        coeffs.append(self.mf.mo_coeff[spin][:, idx])
                    else:
                        coeffs.append(self.mf.mo_coeff[:, idx])
                return coeffs
            
            if hl["is_uhf"]:
                h_idxs, h_spin = (hl["ha"][0], 0) if hl["ha"][1] > hl["hb"][1] else (hl["hb"][0], 1)
                l_idxs, l_spin = (hl["la"][0], 0) if hl["la"][1] < hl["lb"][1] else (hl["lb"][0], 1)
                homo_cs = get_coeffs(h_idxs, h_spin)
                lumo_cs = get_coeffs(l_idxs, l_spin)
            else:
                homo_cs = get_coeffs(hl["h"][0])
                lumo_cs = get_coeffs(hl["l"][0])
                
            self.results = self._calculate_spatial_fmo(homo_cs, lumo_cs, global_scalars, **kwargs)
        else:
            _, _, dm_neu = utils.run_fd_calc(self.mf, 0)
            _, _, dm_cat = utils.run_fd_calc(self.mf, 1)
            _, _, dm_an = utils.run_fd_calc(self.mf, -1)
            
            if dm_neu is None:
                 raise RuntimeError("Density matrices not available for spatial FD.")
            
            self.results = self._calculate_spatial_fd(dm_neu, dm_cat, dm_an, global_scalars, **kwargs)

        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(self.mf, f"Spatial: Generated cube files: {self.results}")

        return self.results

    def _write_derived(self, cc, f_plus, f_minus, f_zero, dual, global_scalars, prefix):
        files = []
        
        # S = Softness, omega = Electrophilicity, N = Nucleophilicity
        S = global_scalars.get("Softness", 0)
        omega = global_scalars.get("Electrophilicity Index", 0)
        N_nu = global_scalars.get("Nucleophilicity Index", 0)
        
        cc.write(S * f_plus, f"{prefix}_s_plus.cube", "Local Softness s+")
        files.append(f"{prefix}_s_plus.cube")
        
        cc.write(S * f_minus, f"{prefix}_s_minus.cube", "Local Softness s-")
        files.append(f"{prefix}_s_minus.cube")
        
        cc.write(S * f_zero, f"{prefix}_s_zero.cube", "Local Softness s0")
        files.append(f"{prefix}_s_zero.cube")
        
        cc.write(S * dual, f"{prefix}_s_dual.cube", "Dual Local Softness")
        files.append(f"{prefix}_s_dual.cube")
        
        cc.write(omega * f_plus, f"{prefix}_omega_plus.cube", "Local Electrophilicity w+")
        files.append(f"{prefix}_omega_plus.cube")
        
        cc.write(N_nu * f_minus, f"{prefix}_n_minus.cube", "Local Nucleophilicity N-")
        files.append(f"{prefix}_n_minus.cube")
        
        return files

    def _calculate_spatial_fmo(self, homo_coeffs, lumo_coeffs, global_scalars, **kwargs):
        prefix = f"{self.prefix}_fmo"
        
        # Calculate averaged density for f- (HOMO)
        cc = None
        f_minus = None
        if homo_coeffs:
            for c in homo_coeffs:
                cc_tmp, orb = orbital_on_grid(self.mf.mol, c, **kwargs)
                dens = orb**2
                if f_minus is None:
                    f_minus = dens
                    cc = cc_tmp
                else:
                    f_minus += dens
            f_minus /= len(homo_coeffs)
        else:
            # Fallback if list empty (shouldn't happen if properly initialized)
            # Create empty grid
            from pyscf.pbc.gto import Cell
            cc = Cube(self.mf.mol, kwargs.get("nx", 80), kwargs.get("ny", 80), kwargs.get("nz", 80))
            f_minus = np.zeros(cc.get_ngrids()).reshape(cc.nx, cc.ny, cc.nz)

        cc.write(f_minus, f"{prefix}_f_minus.cube", "Fukui function f- (HOMO density)")
        
        # Calculate averaged density for f+ (LUMO)
        f_plus = None
        if lumo_coeffs:
            for c in lumo_coeffs:
                cc_tmp, orb = orbital_on_grid(self.mf.mol, c, **kwargs)
                dens = orb**2
                if f_plus is None:
                    f_plus = dens
                else:
                    f_plus += dens
            f_plus /= len(lumo_coeffs)
        else:
            f_plus = np.zeros_like(f_minus)

        cc.write(f_plus, f"{prefix}_f_plus.cube", "Fukui function f+ (LUMO density)")
        
        f_zero = 0.5 * (f_plus + f_minus)
        cc.write(f_zero, f"{prefix}_f_zero.cube", "Fukui function f0")
        
        dual = f_plus - f_minus
        cc.write(dual, f"{prefix}_dual.cube", "Dual descriptor f+ - f-")
        
        files = [f"{prefix}_f_minus.cube", f"{prefix}_f_plus.cube", 
                 f"{prefix}_f_zero.cube", f"{prefix}_dual.cube"]
                 
        files += self._write_derived(cc, f_plus, f_minus, f_zero, dual, global_scalars, prefix)
        return files

    def _calculate_spatial_fd(self, dm_neu, dm_cat, dm_an, global_scalars, **kwargs):
        prefix = f"{self.prefix}_fd"
        mol = self.mf.mol
        
        dm_diff_plus = dm_an - dm_neu
        cc, f_plus = density_on_grid(mol, dm_diff_plus, **kwargs)
        cc.write(f_plus, f"{prefix}_f_plus.cube", "Fukui function f+ (FD)")
        
        dm_diff_minus = dm_neu - dm_cat
        cc, f_minus = density_on_grid(mol, dm_diff_minus, **kwargs)
        cc.write(f_minus, f"{prefix}_f_minus.cube", "Fukui function f- (FD)")
        
        f_zero = 0.5 * (f_plus + f_minus)
        cc.write(f_zero, f"{prefix}_f_zero.cube", "Fukui function f0 (FD)")
        
        dual = f_plus - f_minus
        cc.write(dual, f"{prefix}_dual.cube", "Dual descriptor (FD)")

        files = [f"{prefix}_f_plus.cube", f"{prefix}_f_minus.cube", 
                 f"{prefix}_f_zero.cube", f"{prefix}_dual.cube"]
                 
        files += self._write_derived(cc, f_plus, f_minus, f_zero, dual, global_scalars, prefix)
        return files