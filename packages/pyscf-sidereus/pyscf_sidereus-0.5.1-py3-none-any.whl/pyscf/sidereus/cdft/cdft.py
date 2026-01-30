from pyscf import lib, scf
try:
    from ..xtb import XTB
    HAS_XTB = True
except ImportError:
    HAS_XTB = False

from .descriptors import Descriptors
from .spatial import Spatial

try:
    from ..utils import rdkit as rdkit_utils
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


class CDFT(lib.StreamObject):
    def __init__(self, mf, method="fmo"):
        self.mf = mf
        self.method = method
        self.results = {}
        self.verbose = mf.verbose
        self.stdout = mf.stdout

    def kernel(self):
        # Calculate Global and Atomic descriptors
        tool = Descriptors(self.mf, method=self.method)
        self.results = tool.kernel()
        return self.results

    def spatial(self, nx=80, ny=80, nz=80, resolution=None, margin=3.0, prefix="cdft"):
        return Spatial(self.mf, method=self.method,
                       nx=nx, ny=ny, nz=nz, resolution=resolution,
                       margin=margin, prefix=prefix)

    def visualize(self, descriptor_name, filename):
        if not HAS_RDKIT:
            raise ImportError("RDKit is required for visualization.")

        if "atomic" not in self.results:
            if self.verbose >= lib.logger.WARN:
                lib.logger.warn(
                    self.mf, "No atomic results found. Running kernel() first.")
            self.kernel()

        atomic_res = self.results.get("atomic", {})
        if descriptor_name not in atomic_res:
            raise ValueError(
                f"Descriptor '{descriptor_name}' not found in atomic results. Available: {list(atomic_res.keys())}")

        values = atomic_res[descriptor_name]

        labels = {i: f"{val:.3f}" for i, val in enumerate(values)}

        rd_mol = rdkit_utils.pyscf2rdmol(self.mf.mol)

        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(
                self.mf, f"Visualizing '{descriptor_name}' to {filename}")

        rdkit_utils.draw_rdmol_with_label(rd_mol, labels, filename)
        return filename


scf.hf.SCF.sCDFT = lib.class_as_method(CDFT)
try:
    from ..xtb import XTB
    XTB.sCDFT = lib.class_as_method(CDFT)
except ImportError:
    pass
