# ------------------------------------------------------------------------------
# CodeHawk Binary Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2021 Aarno Labs LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
"""Representation of registers in all architectures."""

from typing import TYPE_CHECKING

from chb.app.BDictionaryRecord import BDictionaryRecord
import chb.util.fileutil as UF

from chb.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    import chb.app.BDictionary


class Register(BDictionaryRecord):
    """Superclass of registers in all architectures.

    Subclasses:
      arm/ARMRegister
      mips/MIPSRegister
      x86/X86Register

    Corresponding type in bCHLibTypes:
                                                   tags[0]     tags   args
    ----------------------------------------------------------------------------
    type register_t =
    | SegmentRegister of segment_t                   "s"         2      0
    | CPURegister of cpureg_t                        "c"         2      0
    | DoubleRegister of cpureg_t * cpureg_t          "d"         3      0
    | FloatingPointRegister of int                   "f"         1      1
    | ControlRegister of int                         "ctr"       1      1
    | DebugRegister of int                           "dbg"       1      1
    | MmxRegister of int    (* 64 bit register *)    "m"         1      1
    | XmmRegister of int    (* 128 bit register *)   "x"         1      1
    | MIPSRegister of mips_reg_t                     "p"         2      0
    | MIPSSpecialRegister of mips_special_reg_t      "ps         2      0
    | MIPSFloatingPointRegister of int               "pf"        1      1
    | ARMRegister of arm_reg_t                       "a"         2      0

    """

    def __init__(
            self,
            bd: "chb.app.BDictionary.BDictionary",
            ixval: IndexedTableValue) -> None:
        BDictionaryRecord.__init__(self, bd, ixval)

    @property
    def is_arm_register(self) -> bool:
        return False

    @property
    def is_arm_stack_pointer(self) -> bool:
        return False

    @property
    def is_arm_argument_register(self) -> bool:
        return False

    @property
    def is_mips_register(self) -> bool:
        return False

    @property
    def is_mips_stack_pointer(self) -> bool:
        return False

    @property
    def is_mips_argument_register(self) -> bool:
        return False

    @property
    def is_x86_register(self) -> bool:
        return False

    @property
    def is_x86_stack_pointer(self) -> bool:
        return False

    def argument_index(self) -> int:
        raise UF.CHBError("Argument_index not supported by " + str(self))

    def __str__(self) -> str:
        return "register:" + self.tags[0]
