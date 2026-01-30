# Copyright 2014-2022 The PySCF Developers, 2025-2026 Sidereus-AI ltd. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");

from .rhf import Raman
from pyscf import lib, dft

class Raman(Raman):
    pass

dft.uks.UKS.sRAMAN = dft.uks_symm.UKS.sRAMAN = lib.class_as_method(Raman)
try:
    from gpu4pyscf.dft import UKS
    UKS.sRAMAN = lib.class_as_method(Raman)
except ImportError:
    pass
