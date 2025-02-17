# ------------------------------------------------------------------------------
# CodeHawk Binary Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
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

from typing import cast, Dict, List, Mapping, Optional, TYPE_CHECKING

from chb.elfformat.ELFHeader import ELFHeader

from chb.simulation.SimMemory import SimMemory
import chb.simulation.SimSymbolicValue as SSV
import chb.simulation.SimValue as SV
import chb.simulation.SimUtil as SU

import chb.util.fileutil as UF

if TYPE_CHECKING:
    from chb.mips.simulation.MIPSimulationState import MIPSimulationState


class MIPSimStackMemory(SimMemory):

    def __init__(
            self,
            simstate: "MIPSimulationState",
            initialized: bool = False) -> None:
        SimMemory.__init__(self, simstate, initialized, "stack")

    def set_environment_string(self, iaddr: str) -> None:
        pass


class MIPSimGlobalMemory(SimMemory):

    def __init__(
            self,
            simstate: "MIPSimulationState",
            elfheader: ELFHeader,
            initialized: bool = False):
        SimMemory.__init__(self, simstate, initialized, "global")
        self._elfheader = elfheader
        self._accesses: Dict[str, List[str]] = {}
        self._patched_globals: Mapping[str, str] = {}

    @property
    def elfheader(self) -> ELFHeader:
        return self._elfheader

    @property
    def patched_globals(self) -> Mapping[str, str]:
        if len(self._patched_globals) == 0:
            self._patched_globals = self.simstate.simsupport.get_patched_globals()
        return self._patched_globals

    @property
    def simstate(self) -> "MIPSimulationState":
        return cast("MIPSimulationState", self._simstate)

    def accesses(self) -> Mapping[str, List[str]]:
        return self._accesses

    def get(
            self,
            iaddr: str,
            address: SSV.SimAddress,
            size: int) -> SV.SimValue:
        try:
            result = SimMemory.get(self, iaddr, address, size)
            if result.is_defined:
                return result
            else:
                return self.get_from_section(iaddr, address, size)
        except SU.CHBSimError:
            return self.get_from_section(iaddr, address, size)

    def has_patched_global(self, address: SSV.SimAddress) -> bool:
        return hex(address.offsetvalue) in self.patched_globals

    def get_patched_global(
            self, address: SSV.SimAddress) -> SV.SimDoubleWordValue:
        if self.has_patched_global(address):
            hexval = self.patched_globals[hex(address.offsetvalue)]
            return cast(SV.SimDoubleWordValue, SV.mk_simvalue(int(hexval, 16)))
        else:
            raise UF.CHBError('No patched global found for ' + str(address))

    def get_from_section(
            self,
            iaddr: str,
            address: SSV.SimAddress,
            size: int) -> SV.SimValue:
        if address.is_defined:
            offset = address.offsetvalue

            # address has been patched by user
            if self.has_patched_global(address):
                return self.get_patched_global(address)

            # try to get the value from the file image
            else:
                sectionindex = self.elfheader.get_elf_section_index(offset)
                if sectionindex is None:

                    # address is not in file image
                    self.simstate.add_logmsg(
                        "global memory", str(address) + " uninitialized")
                    return SV.mk_simvalue(0, size=size)

                # store in global memory data structure
                for i in range(offset, offset + size):
                    byteval = self.elfheader.get_memory_value(sectionindex, i)
                    if byteval is not None:
                        self.set_byte(iaddr, i, SV.SimByteValue(byteval))
                    else:
                        raise UF.CHBError(
                            "No value found for "
                            + hex(i)
                            + " in section "
                            + str(sectionindex))

                # retrieve from global memory data structure
                memval = SimMemory.get(self, iaddr, address, size)
                if not memval.is_defined:
                    memval = SV.mk_simvalue(0, size=size)
                self.simstate.add_logmsg(
                    'global memory', str(address) + ' uninitialized')

                self._accesses.setdefault(str(address), [])
                self._accesses[str(address)].append(str(iaddr) + ':' + str(memval))
                return memval
        else:
            raise UF.CHBError("Address is not defined: " + str(address))


class MIPSimBaseMemory(SimMemory):

    def __init__(
            self,
            simstate: "MIPSimulationState",
            base: str,
            initialized: bool = False,
            buffersize: Optional[int] = None) -> None:
        SimMemory.__init__(self, simstate, initialized, base)
        self._buffersize = buffersize
        self._status = "valid"

    @property
    def simstate(self) -> "MIPSimulationState":
        return cast("MIPSimulationState", self._simstate)

    @property
    def bigendian(self) -> bool:
        return self.simstate.bigendian

    @property
    def buffersize(self) -> int:
        if self._buffersize is not None:
            return self._buffersize
        else:
            raise UF.CHBError("Buffersize of memory is not known")

    def free(self) -> None:
        self._status = "freed"

    def is_valid(self) -> bool:
        return self._status == "valid"

    def has_buffersize(self) -> bool:
        return self.buffersize is not None

    def get(self,
            iaddr: str,
            address: SSV.SimAddress,
            size: int) -> SV.SimValue:
        try:
            memval = SimMemory.get(self, iaddr, address, size)
        except SU.CHBSimError as e:
            name = (self.name
                    + '['
                    + str(address.offsetvalue)
                    + ']'
                    + ' (value not retrieved: '
                    + str(e)
                    + ')')
            return SSV.SimSymbol(name)
        else:
            return memval
