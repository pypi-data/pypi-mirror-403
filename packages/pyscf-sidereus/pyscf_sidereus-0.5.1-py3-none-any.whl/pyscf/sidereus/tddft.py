from pyscf import lib, scf
import numpy as np
from pyscf import tddft
from .utils.matplotlib import plot_spectrum

# Monkeypatch lib.einsum to avoid numpy 2.x incompatibility in PySCF


def _safe_einsum(*args, **kwargs):
    if '_contract' in kwargs:
        del kwargs['_contract']
    return np.einsum(*args, **kwargs)


lib.einsum = _safe_einsum


class TDDFT(lib.StreamObject):
    def __init__(self, mf, nstates=3):
        self.mf = mf
        self.nstates = nstates
        self.verbose = mf.verbose
        self.stdout = mf.stdout
        self.tddft = None
        self.energies = None
        self.oscillator_strengths = None

    def kernel(self):
        if self.verbose >= lib.logger.NOTE:
            lib.logger.note(
                self.mf, f"Running TDDFT for {self.nstates} states...")

        # Check for gpu4pyscf
        if self.mf.__module__.startswith("gpu4pyscf"):
            self.tddft = self.mf.TDA()
        else:
            self.tddft = self.mf.TDA()

        self.tddft.nstates = self.nstates
        self.energies = self.tddft.kernel()[0]

        # Calculate Oscillator Strengths
        e = self.energies
        mol = self.mf.mol

        # Calculate transition moments
        # transition_dipole() returns (nstates, 3)
        trans_dip = self.tddft.transition_dipole()
        f = []
        for i, ei in enumerate(e):
            # ei is in Hartree
            # |<0|r|I>| in Bohr
            # f = 2/3 * E * mu^2
            mu2 = np.linalg.norm(trans_dip[i])**2
            fi = (2.0 / 3.0) * ei * mu2
            f.append(fi)

        self.oscillator_strengths = np.array(f)

        if self.verbose >= lib.logger.NOTE:
            self.summary()

        return self.energies, self.oscillator_strengths

    def summary(self, spectrum=None, w=0.2):
        log = lib.logger.new_logger(self, 2)

        energies_ev = self.energies * 27.211386
        energies_nm = 1239.84193 / energies_ev

        log.log(
            "----------------------------------------------------\n"
            " State      Energy (eV)    Wavelength (nm)    f     \n"
            "----------------------------------------------------"
        )

        for i, (e_ev, nm, f) in enumerate(zip(energies_ev, energies_nm, self.oscillator_strengths)):
            log.log("{:5d}      {:10.4f}      {:10.4f}       {:8.4f}".format(
                i+1, e_ev, nm, f))
        log.log("----------------------------------------------------\n")

        if spectrum:
            # Plot using energies in eV
            x_min = max(0, min(energies_ev) - 1.0)
            x_max = max(energies_ev) + 1.0

            # Use width w (eV)
            fig, _, _ = plot_spectrum(energies_ev, self.oscillator_strengths, w, 0, 1000,
                                      x_min, x_max,
                                      "Energy (eV)",
                                      "Oscillator Strength",
                                      "Oscillator Strength",
                                      "Absorption Spectrum",
                                      "Sticks")
            fig.savefig(spectrum)
            fig.clf()


# Inject
scf.hf.SCF.sTDDFT = lib.class_as_method(TDDFT)
try:
    from .xtb import XTB
    pass
except ImportError:
    pass
