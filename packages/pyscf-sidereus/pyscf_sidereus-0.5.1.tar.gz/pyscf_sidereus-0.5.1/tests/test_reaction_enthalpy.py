import pyscf
import pyscf.sidereus
import pytest

class TestReactionEnthalpy:
    def test_protonation_water(self):
        # Constants
        TEMP = 298.15
        PRESS = 101325
        R_HARTREE = 0.0000031668114 
        
        # 1. H+ Enthalpy
        # Check xTB energy for H+
        try:
            mol_h_plus = pyscf.M(atom="H 0 0 0", charge=1, spin=0, verbose=0)
            e_h_plus = mol_h_plus.sXTB(method="GFN2-xTB").kernel()
            print(f"E_elec(H+) from xTB = {e_h_plus} Eh")
        except Exception as e:
            print(f"Could not calc H+ with xTB: {e}")
            e_h_plus = 0.0

        # H = E_elec + 2.5 RT
        h_proton = e_h_plus + 2.5 * R_HARTREE * TEMP
        print(f"\nH(H+) = {h_proton:.6f} Eh")
        # 2. H2O
        mol_h2o = pyscf.M(atom="O 0 0 0; H 0 -0.75 0.6; H 0 0.75 0.6", verbose=0)
        # Optimize
        mf_h2o = mol_h2o.sXTB(method="GFN2-xTB")
        mol_h2o_opt = mf_h2o.sOPT().kernel()
        # Thermo
        th_h2o = mol_h2o_opt.sXTB(method="GFN2-xTB").sTHERMO(temp=TEMP, press=PRESS)
        res_h2o = th_h2o.kernel()
        h_h2o = th_h2o.H
        print(f"H(H2O) = {h_h2o:.6f} Eh")
        
        # 3. H3O+
        # Estimate structure
        mol_h3o = pyscf.M(atom="O 0 0 0.1; H 0 -0.9 -0.2; H 0.8 0.45 -0.2; H -0.8 0.45 -0.2", 
                          charge=1, spin=0, verbose=0)
        # Optimize
        mf_h3o = mol_h3o.sXTB(method="GFN2-xTB")
        mol_h3o_opt = mf_h3o.sOPT().kernel()
        # Thermo
        th_h3o = mol_h3o_opt.sXTB(method="GFN2-xTB").sTHERMO(temp=TEMP, press=PRESS)
        res_h3o = th_h3o.kernel()
        h_h3o = th_h3o.H
        print(f"H(H3O+) = {h_h3o:.6f} Eh")
        
        # 4. Reaction Enthalpy
        # H+ + H2O -> H3O+
        delta_h = h_h3o - (h_h2o + h_proton)
        delta_h_kcal = delta_h * 627.509
        print(f"Delta H = {delta_h:.6f} Eh = {delta_h_kcal:.2f} kcal/mol")
        
        # Proton affinity of water is about -165 kcal/mol (exothermic)
        # GFN2-xTB should be reasonably close (-150 to -180).
        assert delta_h < 0
        assert -180 < delta_h_kcal < -140
