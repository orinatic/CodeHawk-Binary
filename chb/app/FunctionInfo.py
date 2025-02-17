# ------------------------------------------------------------------------------
# CodeHawk Binary Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 Kestrel Technology LLC
# Copyright (c) 2020      Henny Sipma
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
"""Information about a function carried across analysis rounds."""

import xml.etree.ElementTree as ET

from typing import Dict, Mapping, TYPE_CHECKING

from chb.api.CallTarget import CallTarget
import chb.util.fileutil as UF

if TYPE_CHECKING:
    from chb.api.InterfaceDictionary import InterfaceDictionary


class FunctionInfo:

    def __init__(
            self,
            ixd: "InterfaceDictionary",
            faddr: str,
            xnode: ET.Element) -> None:
        self._ixd = ixd
        self._faddr = faddr
        self.xnode = xnode
        self._calltargets: Dict[str, CallTarget] = {}
        self._variablenames: Dict[int, str] = {}

    @property
    def faddr(self) -> str:
        return self._faddr

    @property
    def ixd(self) -> "InterfaceDictionary":
        return self._ixd

    @property
    def calltargets(self) -> Mapping[str, CallTarget]:
        if len(self._calltargets) == 0:
            ctnode = self.xnode.find("call-targets")
            if ctnode is not None:
                for ctinfo in ctnode.findall("ctinfo"):
                    xaddr = ctinfo.get("a")
                    if xaddr is not None:
                        self._calltargets[xaddr] = (
                            self.ixd.read_xml_call_target(ctinfo))
                    else:
                        raise UF.CHBError("Ctinfo node without address")
            vnnode = self.xnode.find("variable-names")
            if vnnode is not None:
                for xn in vnnode.findall("n"):
                    vix = xn.get("vix")
                    vname = xn.get("name")
                    if vix is not None and vname is not None:
                        self._variablenames[int(vix)] = vname
                    else:
                        raise UF.CHBError("Index or name missing from variablename")
        return self._calltargets

    @property
    def variablenames(self) -> Mapping[int, str]:
        if len(self._variablenames) == 0:
            vnnode = self.xnode.find("variable-names")
            if vnnode is not None:
                for xn in vnnode.findall("n"):
                    vix = xn.get("vix")
                    vname = xn.get("name")
                    if vix is not None and vname is not None:
                        self._variablenames[int(vix)] = vname
                    else:
                        raise UF.CHBError("Index or name missing from variablename")
        return self._variablenames

    def call_target(self, callsite: str) -> CallTarget:
        if self.has_call_target(callsite):
            return self.calltargets[callsite]
        else:
            raise UF.CHBError(
                "Function at "
                + self.faddr
                + "does not have a call target at "
                + callsite)

    def has_call_target(self, callsite: str) -> bool:
        return callsite in self.calltargets

    def has_variable_name(self, index: int) -> bool:
        return index in self.variablenames

    def variable_name(self, index: int) -> str:
        if index in self.variablenames:
            return self.variablenames[index]
        else:
            raise UF.CHBError("Index " + str(index) + " not found in variable names")
