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
"""Access point for most analysis results."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from chb.api.InterfaceDictionary import InterfaceDictionary

from chb.app.AppResultData import AppResultData
from chb.app.AppResultMetrics import AppResultMetrics
from chb.app.BDictionary import BDictionary
from chb.app.Callgraph import Callgraph
from chb.app.Function import Function
from chb.app.FunctionInfo import FunctionInfo
from chb.app.FunctionsData import FunctionsData
from chb.app.JumpTables import JumpTables
from chb.app.SystemInfo import SystemInfo
from chb.app.StringXRefs import StringsXRefs

from chb.elfformat.ELFHeader import ELFHeader

from chb.models.ModelsAccess import ModelsAccess

from chb.peformat.PEHeader import PEHeader

from chb.userdata.UserData import UserData

import chb.util.fileutil as UF


class AppAccess(ABC):

    def __init__(
            self,
            path: str,
            filename: str,
            deps: List[str] = [],
            fileformat: str = "elf",
            arch: str = "x86") -> None:
        """Initializes access to analysis results."""
        self._path = path
        self._filename = filename
        self._deps = deps  # list of summary jars registered as dependencies
        self._fileformat = fileformat  # currently supported: elf, pe
        self._arch = arch  # currently supported: arm, mips, x86

        self._userdata: Optional[UserData] = None

        # file-format specific
        self._peheader: Optional[PEHeader] = None
        self._elfheader: Optional[ELFHeader] = None

        # functions
        self._appresultdata: Optional[AppResultData] = None
        self._functioninfos: Dict[str, FunctionInfo] = {}

        # callgraph
        self._callgraph: Optional[Callgraph] = None

        # summaries
        self.models = ModelsAccess(self.dependencies)

        # application-wide dictionaries
        self._bdictionary: Optional[BDictionary] = None
        self._interfacedictionary: Optional[InterfaceDictionary] = None

        self._systeminfo: Optional[SystemInfo] = None

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def path(self) -> str:
        return self._path

    @property
    def dependencies(self) -> Sequence[str]:
        return self._deps

    # Architecture and file format ---------------------------------------------

    @property
    def architecture(self) -> str:
        return self._arch

    @property
    def fileformat(self) -> str:
        return self._fileformat

    @property
    def arm(self) -> bool:
        return self.architecture == "arm"

    @property
    def mips(self) -> bool:
        return self.architecture == "mips"

    @property
    def x86(self) -> bool:
        return self.architecture == "x86"

    @property
    def elf(self) -> bool:
        return self.fileformat == "elf"

    @property
    def pe(self) -> bool:
        return self.fileformat in ["pe", "pe32"]

    # Dictionaries  ------------------------------------------------------------

    @property
    def bdictionary(self) -> BDictionary:
        if self._bdictionary is None:
            x = UF.get_bdictionary_xnode(self.path, self.filename)
            self._bdictionary = BDictionary(self, x)
        return self._bdictionary

    @property
    def interfacedictionary(self) -> InterfaceDictionary:
        if self._interfacedictionary is None:
            x = UF.get_interface_dictionary_xnode(self.path, self.filename)
            self._interfacedictionary = InterfaceDictionary(self, x)
        return self._interfacedictionary

    # File format --------------------------------------------------------------

    @property
    def peheader(self) -> PEHeader:
        if self.pe:
            if self._peheader is None:
                x = UF.get_pe_header_xnode(self.path, self.filename)
                self._peheader = PEHeader(
                    self.path, self.filename, x, self.dependencies)
            return self._peheader
        else:
            raise UF.CHBError("File with file format "
                              + self.fileformat
                              + " does not have a PE header")

    @property
    def elfheader(self) -> ELFHeader:
        if self.elf:
            if self._elfheader is None:
                x = UF.get_elf_header_xnode(self.path, self.filename)
                self._elfheader = ELFHeader(self.path, self.filename, x)
            return self._elfheader
        else:
            raise UF.CHBError("File with file format "
                              + self.fileformat
                              + " does not have an ELF header")

    # Systeminfo ---------------------------------------------------------------

    @property
    def systeminfo(self) -> SystemInfo:
        if self._systeminfo is None:
            xinfo = UF.get_systeminfo_xnode(self.path, self.filename)
            self._systeminfo = SystemInfo(self.bdictionary, xinfo)
        return self._systeminfo

    @property
    def stringsxrefs(self) -> StringsXRefs:
        return self.systeminfo.stringsxrefs

    @property
    def jumptables(self) -> JumpTables:
        return self.systeminfo.jumptables

    # Functions ----------------------------------------------------------------

    @property
    def appresultdata(self) -> AppResultData:
        if self._appresultdata is None:
            x = UF.get_resultdata_xnode(self.path, self.filename)
            self._appresultdata = AppResultData(x)
        return self._appresultdata

    @property
    def appfunction_addrs(self) -> Sequence[str]:
        """Return a list of all application function addresses."""
        return self.appresultdata.function_addresses()

    def has_function(self, faddr: str) -> bool:
        return faddr in self.appfunction_addrs

    @property
    def functionsdata(self) -> FunctionsData:
        return self.systeminfo.functionsdata

    def has_function_name(self, faddr: str) -> bool:
        return self.systeminfo.has_function_name(faddr)

    def function_name(self, faddr: str) -> str:
        """Return one of the function names, if it has at least one."""

        return self.systeminfo.function_name(faddr)

    def function_names(self, faddr: str) -> Sequence[str]:
        """Return all function names."""

        return self.systeminfo.function_names(faddr)

    @property
    @abstractmethod
    def functions(self) -> Mapping[str, Function]:
        """Return a mapping of function address to function object."""
        ...

    def function(self, faddr: str) -> Function:
        """Return the function object object for the given address."""

        if faddr in self.functions:
            return self.functions[faddr]
        else:
            raise UF.CHBError("Function not found for " + faddr)

    def is_app_function_name(self, name: str) -> bool:
        return self.systeminfo.is_app_function_name(name)

    def is_unique_app_function_name(self, name: str) -> bool:
        return self.systeminfo.is_unique_app_function_name(name)

    def function_address_from_name(self, name: str) -> str:
        return self.systeminfo.function_address_from_name(name)

    def find_enclosing_function(self, iaddr: str) -> Optional[Function]:
        for f in self.functions.values():
            if f.has_instruction(iaddr):
                return f
        else:
            return None

    def function_info(self, faddr: str) -> FunctionInfo:
        if faddr not in self._functioninfos:
            xnode = UF.get_function_info_xnode(self.path, self.filename, faddr)
            self._functioninfos[faddr] = FunctionInfo(
                self.interfacedictionary, faddr, xnode)
        return self._functioninfos[faddr]

    # Callgraph ---------------------------------------------------------------

    @property
    @abstractmethod
    def call_edges(self) -> Mapping[str, Mapping[str, int]]:
        ...

    @property
    def callgraph(self) -> Callgraph:
        if self._callgraph is None:
            calls = self.call_edges
            self._callgraph = Callgraph(calls)
        return self._callgraph

    # Misc ---------------------------------------------------------------------

    '''
    # returns a dictionary of faddr -> string list
    def get_strings(self):
        result = {}
        def f(faddr,fn):
            result[faddr] = fn.get_strings()
        self.iter_functions(f)
        return result


    def get_md5_profile(self):
        """Creates a dictionary of function md5s.

        Structure:
        -- md5hash -> faddr -> instruction count
        """
        result = {}
        def get_md5(faddr,f):
            md5 = f.get_md5_hash()
            result.setdefault(md5,{})
            result[md5][faddr] = mf = {}
            mf['instrs'] = f.get_instruction_count()
            if f.has_name(): mf['names'] = f.get_names()
        self.iter_functions(get_md5)
        profile = {}
        profile['path'] = self.path
        profile['filename'] = self.filename
        profile['imagebase'] = self.peheader.image_base
        profile['md5s'] = result
        return profile

    def get_calls_to_app_function(self,tgtaddr):
        """Returns a dictionary faddr -> Asm/MIPSInstruction list."""
        result = {}
        def f(faddr,fn):
            calls = fn.get_calls_to_app_function(tgtaddr)
            if len(calls) > 0:
                result[faddr] = calls
        self.iter_functions(f)
        return result

    def get_app_calls(self):
        """Returns a dictionary faddr -> Asm/MIPSInstruction."""
        result = {}
        def f(faddr,fn):
            appcalls = fn.get_app_calls()
            if len(appcalls) > 0:
                result[faddr] = appcalls
        self.iter_functions(f)
        return result

    def get_jump_conditions(self):
        """Returns a dictionary faddr -> iaddr -> { data }."""
        result = {}
        def f(faddr,fn):
            jumpconditions = fn.get_jump_conditions()
            if len(jumpconditions) > 0:
                result[faddr] = jumpconditions
        self.iter_functions(f)
        return result

    def get_call_instructions(self):
        """Returns a dictionary faddr -> Asm/MIPSInstruction."""
        result = {}
        def f(faddr,fn):
            appcalls = fn.get_call_instructions()
            if len(appcalls) > 0:
                result[faddr] = appcalls
        self.iter_functions(f)
        return result

    def get_dll_calls(self):
        result = {}
        def f(faddr,fn):
            dllcalls = fn.get_dll_calls()
            if len(dllcalls) > 0:
                result[faddr] = dllcalls
        self.iter_functions(f)
        return result

    def get_ioc_arguments(self):
        dllcalls = self.get_dll_calls()
        result = {}  # ioc -> role-name -> (faddr,iaddr,arg-value)
        problems = {}
        def setproblem(p,dll,fname,faddr,iaddr,params=None,args=None):
            problems.setdefault(p,{})
            problems[p].setdefault(dll,{})
            problems[p][dll].setdefault(fname,[])
            problems[p][dll][fname].append((faddr,iaddr,params,args))
        for faddr in dllcalls:
            for instr in dllcalls[faddr]:
                tgt = instr.get_call_target().get_stub()
                args =  instr.get_call_arguments()
                dll = tgt.get_dll()
                fname = tgt.get_name()
                if self.models.has_dll_summary(dll,fname):
                    summary =  self.models.get_dll_summary(dll,fname)
                    params = summary.get_stack_parameters()
                    if not params is None:
                        if len(args) == len(params):
                            for (param,arg) in zip(params,args):
                                iocroles = [r for r in param.roles() if r.is_ioc()]
                                for r in iocroles:
                                    ioc = r.get_ioc_name()
                                    result.setdefault(ioc,{})
                                    result[ioc].setdefault(r.name,[])
                                    result[ioc][r.name].append((faddr,instr.iaddr,arg))
                        else:  #  len(args) != len(params)
                            setproblem('argument mismatch',dll,fname,faddr,iaddr,
                                           params=len(params),args=len(args))
                    else:   # no parameters
                        setproblem('no parameters',dll,fname,faddr,instr.iaddr)
                else:  # no summary
                    setproblem('no summary',dll,fname,faddr,instr.iaddr)
        return (result,problems)

    def get_unresolved_calls(self):
        result = {}
        def f(faddr,fn):
            unrcalls = fn.get_unresolved_calls()
            if len(unrcalls) > 0:
                result[faddr] = unrcalls
        self.iter_functions(f)
        return result

    # Feature extraction -------------------------------------------------------

    def get_branch_predicates(self):
        result = {}
        def f(faddr,fn):
            predicates = fn.get_branch_predicates()
            if len(predicates) > 0:
                result[faddr] = predicates
        self.iter_functions(f)
        return result

    def get_structured_lhs_variables(self):
        result = {}
        def f(faddr,fn):
            lhsvars = fn.get_structured_lhs_variables()
            if len(lhsvars) > 0:
                result[faddr] = lhsvars
        self.iter_functions(f)
        return result

    def get_structured_lhs_instructions(self):
        result = {}
        def f(faddr,fn):
            lhsinstrs = fn.get_structured_lhs_instructions()
            if len(lhsinstrs) > 0:
                result[faddr] = lhsinstrs
        self.iter_functions(f)
        return result

    def get_structured_rhs_expressions(self):
        result = {}
        def f(faddr,fn):
            rhsxprs = fn.get_structured_rhs_expressions()
            if len(rhsxprs) > 0:
                result[faddr] = rhsxprs
        self.iter_functions(f)
        return result

    def get_return_expressions(self):
        result = {}
        def f(faddr,fn):
            retxprs = fn.get_return_expressions()
            if len(retxprs) > 0:
                result[faddr] = retxprs
        self.iter_functions(f)
        return result

    def get_fn_ioc_arguments(self):
        result = {}
        def f(faddr,fn):
            iocargs = fn.get_ioc_arguments()
            if len(iocargs) > 0:
                result[faddr] = iocargs
        self.iter_functions(f)
        return result

    # Global variables ---------------------------------------------------------

    # returns a dictionary of faddr -> gvar -> count
    def get_global_variables(self):
        result = {}
        def f(faddr,fn):
            result[faddr] = fn.get_global_variables()     # gvar -> count
        self.iter_functions(f)
        return result

    '''
    # Result Metrics -----------------------------------------------------------

    @property
    def result_metrics(self) -> AppResultMetrics:
        x = UF.get_resultmetrics_xnode(self.path, self.filename)
        h = UF.get_resultmetrics_xheader(self.path, self.filename)
        return AppResultMetrics(self.filename, x, h)

    # User data -----------------------------------------------------------

    @property
    def userdata(self) -> UserData:
        if self._userdata is None:
            x = UF.get_user_system_data_xnode(self.path, self.filename)
            self._userdata = UserData(x)
        return self._userdata
