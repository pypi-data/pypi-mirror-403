# Copyright 2014-2022 The PySCF Developers, 2025-2026 Sidereus-AI ltd. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");

from .rhf import Raman
from pyscf import lib, scf

class Raman(Raman):
    pass

scf.uhf.UHF.sRAMAN = lib.class_as_method(Raman)
