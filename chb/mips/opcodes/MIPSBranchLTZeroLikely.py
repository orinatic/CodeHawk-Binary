# ------------------------------------------------------------------------------
# CodeHawk Binary Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 Kestrel Technology LLC
# Copyright (c) 2020-2021 Henny Sipma
# Copyright (c) 2021      Aarno Labs LLC
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

from typing import cast, List, Sequence, TYPE_CHECKING

from chb.app.InstrXData import InstrXData

from chb.invariants.XXpr import XXpr

from chb.mips.MIPSDictionaryRecord import mipsregistry
from chb.mips.MIPSOpcode import MIPSOpcode, simplify_result
from chb.mips.MIPSOperand import MIPSOperand
from chb.mips.opcodes.MIPSBranchOpcode import MIPSBranchOpcode

import chb.simulation.SimSymbolicValue as SSV
import chb.simulation.SimUtil as SU
import chb.simulation.SimValue as SV

import chb.util.fileutil as UF

from chb.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chb.mips.MIPSDictionary import MIPSDictionary
    from chb.mips.simulation.MIPSimulationState import MIPSimulationState


@mipsregistry.register_tag("bltzl", MIPSOpcode)
class MIPSBranchLTZeroLikely(MIPSBranchOpcode):
    """BLTZL rs, offset

    Branch on Less Than Zero Likely.
    Test a GPR then do a PC-relative conditional branch; execute the
    delay slot only if the branch is taken.

    args[0]: index of rs in mips dictionary
    args[1]: index of offset in mips dictionary
    """

    def __init__(
            self,
            mipsd: "MIPSDictionary",
            ixval: IndexedTableValue) -> None:
        MIPSBranchOpcode.__init__(self, mipsd, ixval)

    @property
    def operands(self) -> Sequence[MIPSOperand]:
        return [self.mipsd.mips_operand(i) for i in self.args]

    @property
    def target(self) -> MIPSOperand:
        return self.mipsd.mips_operand(self.args[1])

    def has_branch_condition(self) -> bool:
        return True

    def branch_condition(self, xdata: InstrXData) -> XXpr:
        return xdata.xprs[2]

    def ft_conditions(self, xdata: InstrXData) -> Sequence[XXpr]:
        return [xdata.xprs[3], xdata.xprs[2]]

    def annotation(self, xdata: InstrXData) -> str:
        """data format a:xxxx

        xprs[0]: rhs
        xprs[1]: condition (syntactic)
        xprs[2]: condition (simplified)
        xprs[3]: condition (negated)
        """

        result = xdata.xprs[1]
        rresult = xdata.xprs[2]
        xresult = simplify_result(xdata.args[1], xdata.args[2], result, rresult)
        return 'if ' + xresult + ' then goto ' + str(self.target)
