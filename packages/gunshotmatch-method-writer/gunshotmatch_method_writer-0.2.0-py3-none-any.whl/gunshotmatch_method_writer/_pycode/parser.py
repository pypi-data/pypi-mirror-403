"""
Utilities parsing and analyzing Python code.
"""

# stdlib
import ast
import inspect
import re
import tokenize
from token import DEDENT, INDENT, NAME, NEWLINE, NUMBER, OP, STRING
from tokenize import COMMENT
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
		"AfterCommentParser",
		"Parser",
		"Token",
		"TokenProcessor",
		"VariableCommentPicker",
		"dedent_docstring",
		"filter_whitespace",
		"get_assign_targets",
		"get_lvar_names",
		]

comment_re = re.compile('^\\s*#: ?(.*)\r?\n?$')
indent_re = re.compile("^\\s*$")


def filter_whitespace(code: str) -> str:  # noqa: D103
	return code.replace('\x0c', ' ')  # replace FF (form feed) with whitespace


def get_assign_targets(node: ast.AST) -> List[ast.expr]:
	"""Get list of targets from Assign and AnnAssign node."""
	if isinstance(node, ast.Assign):
		return node.targets
	else:
		return [node.target]  # type: ignore


def get_lvar_names(node: ast.AST, self: Optional[ast.arg] = None) -> List[str]:
	"""Convert assignment-AST to variable names.

	This raises `TypeError` if the assignment does not create new variable::

		ary[0] = 'foo'
		dic["bar"] = 'baz'
		# => TypeError
	"""
	if self:
		self_id = self.arg

	node_name = node.__class__.__name__
	if node_name in ("Index", "Num", "Slice", "Str", "Subscript"):
		raise TypeError("%r does not create new variable" % node)
	if node_name == "Name":
		if self is None or node.id == self_id:  # type: ignore
			return [node.id]  # type: ignore
		else:
			raise TypeError("The assignment %r is not instance variable" % node)
	elif node_name in ("Tuple", "List"):
		members = []
		for elt in node.elts:  # type: ignore
			try:
				members.extend(get_lvar_names(elt, self))
			except TypeError:
				pass
		return members
	elif node_name == "Attribute":
		if (
				node.value.__class__.__name__ == "Name" and  # type: ignore[attr-defined]  # noqa: W504
				self and node.value.id == self_id  # type: ignore[attr-defined]
				):
			# instance variable
			return ["%s" % get_lvar_names(node.attr, self)[0]]  # type: ignore
		else:
			raise TypeError("The assignment %r is not instance variable" % node)
	elif node_name == "str":
		return [node]  # type: ignore
	elif node_name == "Starred":
		return get_lvar_names(node.value, self)  # type: ignore
	else:
		raise NotImplementedError("Unexpected node name %r" % node_name)


def dedent_docstring(s: str) -> str:
	"""Remove common leading indentation from docstring."""

	def dummy() -> None:
		# dummy function to mock `inspect.getdoc`.
		pass

	dummy.__doc__ = s
	docstring = inspect.getdoc(dummy)
	if docstring:
		return docstring.lstrip("\r\n").rstrip("\r\n")
	else:
		return ''


class Token:
	"""Better token wrapper for tokenize module."""

	def __init__(self, kind: int, value: Any, start: Tuple[int, int], end: Tuple[int, int], source: str) -> None:
		self.kind = kind
		self.value = value
		self.start = start
		self.end = end
		self.source = source

	def __eq__(self, other: Any) -> bool:
		if isinstance(other, int):
			return self.kind == other
		elif isinstance(other, str):
			return self.value == other
		elif isinstance(other, (list, tuple)):
			return [self.kind, self.value] == list(other)
		elif other is None:
			return False
		else:
			raise ValueError("Unknown value: %r" % other)

	def match(self, *conditions: Any) -> bool:  # noqa: D102
		return any(self == candidate for candidate in conditions)

	def __repr__(self) -> str:
		return f'<Token kind={tokenize.tok_name[self.kind]!r} value={self.value.strip()!r}>'


class TokenProcessor:  # noqa: D101

	def __init__(self, buffers: List[str]) -> None:
		lines = iter(buffers)
		self.buffers = buffers
		self.tokens = tokenize.generate_tokens(lambda: next(lines))
		self.current: Optional[Token] = None
		self.previous: Optional[Token] = None

	def get_line(self, lineno: int) -> str:
		"""Returns specified line."""
		return self.buffers[lineno - 1]

	def fetch_token(self) -> Optional[Token]:
		"""
		Fetch the next token from source code.

		Returns :py:obj:`None` if sequence finished.
		"""

		try:
			self.previous = self.current
			self.current = Token(*next(self.tokens))
		except StopIteration:
			self.current = None

		return self.current

	def fetch_until(self, condition: Any) -> List[Optional[Token]]:
		"""Fetch tokens until specified token appeared.

		.. note:: This also handles parenthesis well.
		"""
		tokens = []
		while self.fetch_token():
			tokens.append(self.current)
			if self.current == condition:
				break
			if self.current == [OP, '(']:
				tokens += self.fetch_until([OP, ')'])
			elif self.current == [OP, '{']:
				tokens += self.fetch_until([OP, '}'])
			elif self.current == [OP, '[']:
				tokens += self.fetch_until([OP, ']'])

		return tokens


class AfterCommentParser(TokenProcessor):
	"""Python source code parser to pick up comments after assignments.

	This parser takes code which starts with an assignment statement,
	and returns the comment for the variable if one exists.
	"""

	def __init__(self, lines: List[str]) -> None:
		super().__init__(lines)
		self.comment: Optional[str] = None

	def fetch_rvalue(self) -> List[Optional[Token]]:
		"""Fetch right-hand value of assignment."""
		tokens = []
		while self.fetch_token():
			tokens.append(self.current)
			if self.current == [OP, '(']:
				tokens += self.fetch_until([OP, ')'])
			elif self.current == [OP, '{']:
				tokens += self.fetch_until([OP, '}'])
			elif self.current == [OP, '[']:
				tokens += self.fetch_until([OP, ']'])
			elif self.current == INDENT:
				tokens += self.fetch_until(DEDENT)
			elif self.current == [OP, ';']:
				break
			elif self.current and self.current.kind not in {OP, NAME, NUMBER, STRING}:
				break

		return tokens

	def parse(self) -> None:
		"""Parse the code and obtain comment after assignment."""
		# skip lvalue (or whole of AnnAssign)
		while (tok := self.fetch_token()) and not tok.match([OP, '='], NEWLINE, COMMENT):
			assert self.current

		# skip rvalue (if exists)
		if self.current == [OP, '=']:
			self.fetch_rvalue()

		if self.current == COMMENT:
			self.comment = self.current.value  # type: ignore[union-attr]


class VariableCommentPicker(ast.NodeVisitor):
	"""Python source code parser to pick up variable comments."""

	def __init__(self, buffers: List[str], encoding: str) -> None:
		self.buffers = buffers
		self.context: List[str] = []
		self.comments: Dict[Tuple[str, str], str] = {}
		self.previous: Optional[ast.AST] = None
		super().__init__()

	def get_qualname_for(self, name: str) -> Optional[List[str]]:
		"""
		Get qualified name for given object as a list of string(s).
		"""

		return self.context + [name]

	def add_variable_comment(self, name: str, comment: str) -> None:  # noqa: D102
		qualname = self.get_qualname_for(name)
		if qualname:
			basename = '.'.join(qualname[:-1])
			self.comments[(basename, name)] = comment

	def get_line(self, lineno: int) -> str:
		"""
		Returns specified line.
		"""

		return self.buffers[lineno - 1]

	def visit(self, node: ast.AST) -> None:
		"""Updates self.previous to the given node."""
		super().visit(node)
		self.previous = node

	def visit_Assign(self, node: ast.Assign) -> None:
		"""Handles Assign node and pick up a variable comment."""
		try:
			targets = get_assign_targets(node)
			varnames: List[str] = sum(
					[get_lvar_names(t, self=None) for t in targets],
					[],
					)
			current_line = self.get_line(node.lineno)
		except TypeError:
			return  # this assignment is not new definition!

		# check comments after assignment
		parser = AfterCommentParser([current_line[node.col_offset:]] + self.buffers[node.lineno:])
		parser.parse()
		if parser.comment and comment_re.match(parser.comment):
			for varname in varnames:
				self.add_variable_comment(varname, comment_re.sub("\\1", parser.comment))
			return

		# check comments before assignment
		if indent_re.match(current_line[:node.col_offset]):
			comment_lines = []
			for i in range(node.lineno - 1):
				before_line = self.get_line(node.lineno - 1 - i)
				if comment_re.match(before_line):
					comment_lines.append(comment_re.sub("\\1", before_line))
				else:
					break

			if comment_lines:
				comment = dedent_docstring('\n'.join(reversed(comment_lines)))
				for varname in varnames:
					self.add_variable_comment(varname, comment)
				return

	def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
		"""Handles AnnAssign node and pick up a variable comment."""
		self.visit_Assign(node)  # type: ignore

	def visit_Expr(self, node: ast.Expr) -> None:
		"""Handles Expr node and pick up a comment if string."""
		if (isinstance(self.previous, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Str)):
			try:
				targets = get_assign_targets(self.previous)
				varnames = get_lvar_names(targets[0], None)
				for varname in varnames:
					if isinstance(node.value.s, str):
						docstring = node.value.s
					else:
						docstring = node.value.s.decode("utf-8")

					self.add_variable_comment(varname, dedent_docstring(docstring))
			except TypeError:
				pass  # this assignment is not new definition!

	def visit_ClassDef(self, node: ast.ClassDef) -> None:
		"""Handles ClassDef node and set context."""
		self.context.append(node.name)
		self.previous = node
		for child in node.body:
			self.visit(child)
		self.context.pop()


class Parser:
	"""Python source code parser to pick up variable comments.

	This is a better wrapper for ``VariableCommentPicker``.
	"""

	def __init__(self, code: str, encoding: str = "utf-8") -> None:
		self.code = filter_whitespace(code)
		self.comments: Dict[Tuple[str, str], str] = {}

	def parse(self) -> None:
		"""Parse the source code."""
		self.parse_comments()

	def parse_comments(self) -> None:
		"""Parse the code and pick up comments."""
		tree = ast.parse(self.code, type_comments=True)
		picker = VariableCommentPicker(self.code.splitlines(True), "UTF-8")
		picker.visit(tree)
		self.comments = picker.comments
