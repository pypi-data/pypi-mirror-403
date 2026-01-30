import pyscf
import pyscf.sidereus


class TestRaman:
    def setup_method(self, method):
        self.atom = 'H 0 0 0; H 0 0 0.74'
        self.basis = 'sto-3g'
        self.xc = 'lda'

    def test_rhf(self):
        mol = pyscf.M(atom=self.atom, basis=self.basis)
        mol.RHF().run().sRAMAN().kernel()

    def test_uhf(self):
        mol = pyscf.M(atom=self.atom, basis=self.basis)
        mol.UHF().run().sRAMAN().kernel()

    def test_rks(self):
        mol = pyscf.M(atom=self.atom, basis=self.basis)
        mol.RKS(xc=self.xc).run().sRAMAN().kernel()

    def test_uks(self):
        mol = pyscf.M(atom=self.atom, basis=self.basis)
        mol.UKS(xc=self.xc).run().sRAMAN().run().summary()
