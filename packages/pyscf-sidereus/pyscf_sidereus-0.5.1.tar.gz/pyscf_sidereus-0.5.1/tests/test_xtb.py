import pyscf
import pyscf.sidereus


class TestXTB:
    def setup_method(self, method):
        self.atom = "H 0 0 0; F 0 0 0.917"

    def test_xtb(self):
        mol = pyscf.M(atom=self.atom)
        mf = mol.sXTB(method="GFN2-xTB")
        mf.kernel()
        mf.Gradients().kernel()

    def test_opt(self):
        mol = pyscf.M(atom=self.atom)
        mol.sXTB(method="GFN2-xTB").sOPT().kernel()