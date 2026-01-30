from pyscf import lib
from ..xtb import XTB
from .rhf import OPT as RHFOPT

class OPT(RHFOPT):
    def _gen_calc_block(self, data, mol):
        # pysisyphus configuration for XTB using tblite
        data["calc"] = {
            "type": "tblite",
            "charge": mol.charge,
            "mult": mol.spin + 1,
        }
        
        if self.mf.method:
            method_str = self.mf.method.upper()
            if "GFN1" in method_str:
                data["calc"]["par"] = 1
            elif "GFN0" in method_str:
                data["calc"]["par"] = 0
            
    # _run_yaml and other methods are inherited from RHFOPT

XTB.sOPT = lib.class_as_method(OPT)
