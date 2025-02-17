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
"""List of application function addresses and associated md5."""

import xml.etree.ElementTree as ET

from typing import Dict, List


class AppResultData:

    def __init__(
            self,
            xnode: ET.Element) -> None:
        self.xnode = xnode
        self._functions: Dict[str, str] = {}

    def functions(self) -> Dict[str, str]:
        if len(self._functions) == 0:
            xfunctions = self.xnode.find("functions")
            if xfunctions is not None:
                for f in xfunctions.findall("fn"):
                    xfa = f.get("fa")
                    xmd5 = f.get("md5")
                    if xfa is not None and xmd5 is not None:
                        self._functions[xfa] = xmd5
        return self._functions

    def function_addresses(self) -> List[str]:
        return list(self.functions().keys())
