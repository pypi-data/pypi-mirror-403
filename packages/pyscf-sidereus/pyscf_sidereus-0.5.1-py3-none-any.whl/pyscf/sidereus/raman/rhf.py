# Copyright 2014-2022 The PySCF Developers, 2025-2026 Sidereus-AI ltd. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");

import numpy as np
from pyscf import lib, scf, hessian
from pyscf.hessian import thermo
from pyscf.data import nist
from pyscf.lib import logger
from ..utils.matplotlib import plot_spectrum
# from ..utils.scale import fundamentals as data

def polarizability_derivative_numerical_dEdE(mf, dE=2.5e-3):
    # Return in (   natm, 3,           3, 3      )
    #            < derivative > < polarizability >
    #
    # This function makes the mf object unusable, please make a new one after calling this function.
    mol = mf.mol

    with mol.with_common_orig((0, 0, 0)):
        dipole_integral = mol.intor('int1e_r').reshape(3, mol.nao, mol.nao)
        # int1e_irp: < | r p | >. Used for basis function derivatives approximation?
        # In PySCF, int1e_irp is (3, 3, nao, nao) flattened to (9, nao, nao).
        dipole_integral_derivative = -mol.intor('int1e_irp').reshape(3, 3, mol.nao, mol.nao)

    Hcore = mf.get_hcore()
    
    def get_gradient_at_E(mf, E):
        # E is shape (3,)
        
        # Monkey patch get_hcore to include electric field
        original_get_hcore = mf.get_hcore
        def new_get_hcore(mol=None):
            return Hcore + np.einsum('x,xij->ij', E, dipole_integral)
        
        mf.get_hcore = new_get_hcore
        
        try:
            mf.kernel()
            if not mf.converged:
                logger.warn(mf, "SCF not converged in Raman finite difference step with E=%s", E)
            
            dm = mf.make_rdm1()
            if dm.ndim == 3: # UHF/UKS
                dm = dm[0] + dm[1]
            
            # Compute Nuclear Gradient
            mf_grad = mf.nuc_grad_method()
            g = mf_grad.kernel()
            gradient = g.copy()
            
            # Add explicit derivative of the E-field interaction term: d/dR <psi| -E.mu |psi>
            # The term added to H is E.mu.
            # d_dipoleintegral_dA = mol.intor("int1e_ip_r", comp=3) # (3, 3, nao, nao)
            aoslices = mol.aoslice_by_atom()
            for i_atom in range(mol.natm):
                p0, p1 = aoslices[i_atom][2:]

                d_dipoleintegral_dA = np.zeros((3, 3, mol.nao, mol.nao))
                # Logic from reference adapted to numpy
                d_dipoleintegral_dA[:, :, :, p0:p1] += dipole_integral_derivative[:, :, :, p0:p1]
                d_dipoleintegral_dA[:, :, p0:p1, :] += dipole_integral_derivative[:, :, :, p0:p1].transpose(0, 1, 3, 2)
                d_dipoleintegral_dA = d_dipoleintegral_dA.transpose(1,0,2,3) # (3_grad, 3_field, nao, nao)

                # Contribution: Tr(dm * d(E.mu)/dA) = Tr(dm * E_j * d(mu_j)/dA)
                # d_dipoleintegral_dA[x, y] is d(mu_y)/dA_x
                
                term = np.einsum('xyij,ij->xy', d_dipoleintegral_dA, dm) # (3_grad, 3_field)
                gradient[i_atom, :] += np.dot(term, E)

        finally:
            # Restore (though we iterate, so maybe not strictly necessary if we reset carefully, 
            # but good practice)
            mf.get_hcore = original_get_hcore

        return gradient

    dpdx = np.empty((mol.natm, 3, 3, 3))

    E_0 = np.zeros(3)
    gradient_0 = get_gradient_at_E(mf, E_0)

    for i_xyz in range(3):
        for j_xyz in range(i_xyz + 1, 3):
            E_pp = np.zeros(3)
            E_pp[i_xyz] += dE
            E_pp[j_xyz] += dE
            gradient_pp = get_gradient_at_E(mf, E_pp)

            E_pm = np.zeros(3)
            E_pm[i_xyz] += dE
            E_pm[j_xyz] -= dE
            gradient_pm = get_gradient_at_E(mf, E_pm)

            E_mp = np.zeros(3)
            E_mp[i_xyz] -= dE
            E_mp[j_xyz] += dE
            gradient_mp = get_gradient_at_E(mf, E_mp)

            E_mm = np.zeros(3)
            E_mm[i_xyz] -= dE
            E_mm[j_xyz] -= dE
            gradient_mm = get_gradient_at_E(mf, E_mm)

            dpdx_ij = (gradient_pp + gradient_mm - gradient_pm - gradient_mp) / (4 * dE**2)
            dpdx[:, :, i_xyz, j_xyz] = dpdx_ij
            dpdx[:, :, j_xyz, i_xyz] = dpdx_ij

        E_p = np.zeros(3)
        E_p[i_xyz] += dE
        gradient_p = get_gradient_at_E(mf, E_p)

        E_m = np.zeros(3)
        E_m[i_xyz] -= dE
        gradient_m = get_gradient_at_E(mf, E_m)

        dpdx[:, :, i_xyz, i_xyz] = (gradient_p + gradient_m - 2 * gradient_0) / (dE**2)
    
    # dpdx = - d^3 E / dR dE^2
    dpdx *= -1
    
    return dpdx

def eval_raman_intensity(mf, hessian=None):
    '''
    Main driver of Raman spectra intensity

    Args:
        mf: mean field object
        hessian: the hessian matrix in shape (natm, natm, 3, 3), if available

    Returns:
        node frequency: in cm^-1
        Raman scattering activity: in Angstrom**4 / AMU
        Depolarization ratio: dimensionless
    '''
    mol = mf.mol

    if hessian is None:
        hess_obj = mf.Hessian()
        hess_obj.auxbasis_response = 2 # specific to density fitting? standard hessian might not need this
        hessian = hess_obj.kernel()
    
    # Ensure hessian shape
    if hessian.ndim == 2:
        hessian = hessian.reshape(mol.natm, 3, mol.nao, 3).transpose(0, 2, 1, 3)
    
    assert hessian.shape == (mol.natm, mol.natm, 3, 3)

    freq_info = thermo.harmonic_analysis(mol, hessian)

    norm_mode = freq_info['norm_mode']
    freq_wavenumber = freq_info['freq_wavenumber']

    mf_copy = mf.copy() # Preserve the original mf
    dalpha_dR = polarizability_derivative_numerical_dEdE(mf_copy)
    dalpha_dQ = lib.einsum('AdEe,iAd->iEe', dalpha_dR, norm_mode)

    n_mode = len(freq_wavenumber)
    raman_intensities = np.zeros(n_mode)
    depolarization_ratio = np.zeros(n_mode)

    for i_mode in range(n_mode):
        dalpha_dQi = dalpha_dQ[i_mode]
        alpha_prime = 1.0/3.0 * (dalpha_dQi[0,0] + dalpha_dQi[1,1] + dalpha_dQi[2,2])
        alpha_prime_square = alpha_prime**2
        beta_prime_square = 0.5 * (
            + (dalpha_dQi[0,0] - dalpha_dQi[1,1])**2
            + (dalpha_dQi[0,0] - dalpha_dQi[2,2])**2
            + (dalpha_dQi[1,1] - dalpha_dQi[2,2])**2
            + 6 * (dalpha_dQi[0,1]**2 + dalpha_dQi[0,2]**2 + dalpha_dQi[1,2]**2)
        )

        raman_intensities[i_mode] = 45 * alpha_prime_square + 7 * beta_prime_square
        denominator = 45 * alpha_prime_square + 4 * beta_prime_square
        if abs(denominator) > 1e-12:
            depolarization_ratio[i_mode] = 3 * beta_prime_square / denominator
        else:
            depolarization_ratio[i_mode] = 0.0

    raman_intensities *= nist.BOHR**4

    return freq_wavenumber, raman_intensities, depolarization_ratio

class Raman(lib.StreamObject):
    def __init__(self, mf):
        self.mol = mf.mol
        self.verbose = mf.mol.verbose
        self.stdout = mf.mol.stdout
        self._scf = self.base = mf
        
        self.mf_hess = None
        self.vib_dict = None
        
        self.raman_intensities = NotImplemented
        self.depolarization_ratio = NotImplemented
        self.freq_wavenumber = NotImplemented

    def kernel(self, hessian=None):
        if self._scf.__module__.startswith("gpu4pyscf"):
            from gpu4pyscf.properties.raman import eval_raman_intensity as eval_raman_gpu
            freq, intensity, depolar = eval_raman_gpu(self._scf, hessian)
            self.freq_wavenumber = freq
            self.raman_intensities = intensity
            self.depolarization_ratio = depolar
        else:
            freq, intensity, depolar = eval_raman_intensity(self._scf, hessian)
            self.freq_wavenumber = freq
            self.raman_intensities = intensity
            self.depolarization_ratio = depolar
            
        self.vib_dict = {
            "freq_wavenumber": self.freq_wavenumber,
            "raman_intensities": self.raman_intensities,
            "depolarization_ratio": self.depolarization_ratio
        }
        return self.raman_intensities

    def summary(self, spectrum=None, w=50):
        log = logger.new_logger(self, 2)
        if self.raman_intensities is NotImplemented:
            self.kernel()

        if isinstance(w, (int, float)):
            w = np.ones_like(self.freq_wavenumber) * w
            
        log.log(
            "----------------------------------------------------------------------\n"
            " Mode      Frequency       Intensity       Depolarization Ratio       \n"
            "   #         cm^-1           A^4/AMU                                  \n"
            "----------------------------------------------------------------------")
            
        for i, (f, inten, depol) in enumerate(zip(self.freq_wavenumber, self.raman_intensities, self.depolarization_ratio)):
            flag_im = np.imag(f) > 1e-10
            chr_im = "i" if flag_im else " "
            log.log("{:5d}   {:12.4f}{:}   {:12.4f}     {:12.4f}".format(
                i, np.abs(f), chr_im, inten, depol))
        log.log("----------------------------------------------------------------------\n")
        
        if spectrum:
            # Similar plotting logic as IR but for Raman
            freq = self.freq_wavenumber
            inten = self.raman_intensities.copy()
            # Remove imaginary or negative freqs
            valid = (np.abs(np.imag(freq)) <= 1e-10) & (np.real(freq) > 0)
            freq = np.real(freq)
            
            # Mask
            inten[~valid] = 0
            
            xmax = max([4000, max(freq) + 5*max(w) if len(freq)>0 else 4000])
            
            fig, _, _ = plot_spectrum(freq, inten, w, 5*w, 4000, 0, xmax,
                                      "Vibration Wavenumber (cm$^{-1}$)",
                                      "Raman Activity (A$^4$/AMU)",
                                      "Raman Activity",
                                      "Raman Activity",
                                      "Raman Activity")
            fig.savefig(spectrum)
            fig.clf()

scf.hf.RHF.sRAMAN = lib.class_as_method(Raman)
