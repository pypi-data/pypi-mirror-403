#!/usr/bin/env python3
#
#  __init__.py
"""
Method writer for GunShotMatch.
"""
#
#  Copyright © 2024 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Redistribution and use in source and binary forms, with or without modification,
#  are permitted provided that the following conditions are met:

#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.

#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER
#  OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# stdlib
import functools
from collections import defaultdict
from types import MappingProxyType
from typing import Dict, List, Mapping

# 3rd party
import attr
import tomli_w
from dom_toml.config import Config as MethodBase
from domdf_python_tools.stringlist import StringList

# this package
from gunshotmatch_method_writer._pycode import get_attr_docs

__all__ = (
		"default_method_toml",
		"get_module_attrib_docstrings",
		"docstring_to_descriptions",
		)

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2024 Dominic Davis-Foster"
__license__: str = "2-Clause BSD License"
__version__: str = "0.2.0"
__email__: str = "dominic@davis-foster.co.uk"


def docstring_to_description(docstring: List[str]) -> str:
	"""
	Remove Sphinx directives and backticks from the docstring to create the description.

	:param docstring:
	"""

	docstring_lines = []
	for line in docstring:
		if line and not line.lstrip().startswith(".."):
			docstring_lines.append(line)
	return '\n'.join(docstring_lines).strip().replace('`', '')


@functools.lru_cache
def get_module_attrib_docstrings(module_name: str) -> Mapping[str, Mapping[str, str]]:
	"""
	Returns a mapping of classes in the given module to their attributes and their docstrings.

	:param module_name:
	"""

	# ma = ModuleAnalyzer.for_module(module_name)
	# ma.analyze()
	attr_docs = get_attr_docs(module_name)

	class_attrib_docstrings: Dict[str, Dict[str, str]] = defaultdict(dict)
	for attribute_path, docstring in attr_docs.items():
		class_name, attr_name = attribute_path
		description = docstring_to_description(docstring)
		class_attrib_docstrings[class_name][attr_name] = description

	return MappingProxyType(dict(class_attrib_docstrings))


def default_method_toml(method: MethodBase, method_name: str = "method") -> str:
	"""
	Generate TOML output for the (default state of) the given method.

	Default values are commented out.
	All properties are accompanied by a short explanatory comment.

	:param method:
	:param method_name: The name of the top-level table for this method.

	:rtype:

	.. versionchanged:: 0.2.0  Added ``method_name`` argument.
	"""

	output = StringList()
	output.indent_type = "# "

	defaults = {}

	method_class = method.__class__
	method_module = method_class.__module__

	docstrings = get_module_attrib_docstrings(method_module)[method_class.__name__]

	for attrib in method_class.__attrs_attrs__:
		if isinstance(attrib.default, attr.Factory):  # type: ignore[arg-type]
			assert attrib.default is not None
			default = attrib.default.factory()
		else:
			default = attrib.default
		defaults[attrib.name] = default

	as_dict = attr.asdict(method, recurse=False)
	for k, v in list(as_dict.items()):

		output.blankline()
		docstring_lines = docstrings[k].splitlines()

		if isinstance(v, MethodBase):

			output.blankline()
			output.append("# ------------------------------")

			heading_toml = tomli_w.dumps({method_name: {k: {}}}).strip().replace('"', '')
			output.append(heading_toml + f" # {docstring_lines[0]}")

			with output.with_indent("### ", 1):
				output.extend(docstring_lines[1:])

			# with output.with_indent("### ", 1):
			# 	output.append(docstrings[k])
			# output.append(tomli_w.dumps({k: {}}).strip())
			# output.append("###")
			output.append(default_method_toml(v, f"{method_name}.{k}"))
		else:

			with output.with_indent_size(1):
				output.extend(docstring_lines)

			if v is None:
				output.append(f"# {k} = ")
				continue

			if v == defaults[k]:
				output.indent_size = 1

			if isinstance(v, (set, tuple)):
				v = list(v)

			if isinstance(v, list) and not v:
				output.append(f"{k} = [ ]")
			elif isinstance(v, list) and len(v) < 5:
				v_repr = repr(v)[1:-1]
				output.append(f"{k} = [ {v_repr}, ]")
			else:
				output.append(tomli_w.dumps({k: v}).strip())

			output.indent_size = 0

	return str(output)
