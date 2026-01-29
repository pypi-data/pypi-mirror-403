"""
Utilities parsing and analyzing Python code.
"""

# stdlib
from importlib import import_module
from typing import Dict, List, Tuple

# this package
from .parser import Parser

__all__ = ["get_attr_docs", "get_module_source"]


def get_module_source(modname: str) -> Tuple[str, str]:
	"""
	Try to find the source code for a module.

	:param modname:

	:returns: A tuple of ``filename`` and ``source``.
	"""

	mod = import_module(modname)
	loader = getattr(mod, "__loader__", None)

	if loader and getattr(loader, "get_source", None):
		source = loader.get_source(modname)
		if source:
			return getattr(mod, "__file__", "<string>"), source

	raise ValueError("no source found for module %r" % modname)


def get_attr_docs(modname: str) -> Dict[Tuple[str, str], List[str]]:
	"""
	Extract class attribute docstrings for the given module name.

	:param modname:

	:returns: A mapping of (class name, attribute name) to attribute docstring.
	"""

	srcname, source = get_module_source(modname)

	try:
		parser = Parser(source)
		parser.parse()

		attr_docs: Dict[Tuple[str, str], List[str]] = {}
		for (scope, comment) in parser.comments.items():
			if comment:
				attr_docs[scope] = comment.splitlines() + ['']
			else:
				attr_docs[scope] = ['']

		return attr_docs
	except Exception as exc:
		raise ValueError(f'parsing {(srcname or "<string>")!r} failed: {exc!r}') from exc
