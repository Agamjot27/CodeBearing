"""Narrow captured Python declaration evidence and indivisible budget contracts."""

from pathlib import Path
import unittest

from codebearing.context import compile_context, estimate_tokens
from codebearing.index import build_index_from_sources


class ExceptionContextTests(unittest.TestCase):
    def index(self, source):
        return build_index_from_sources(Path.cwd(), {"retrying.py": source.encode()})

    def test_referenced_local_exception_and_ancestors_are_cited_in_full(self):
        source = "class ParentFault(Exception):\n    pass\n\nclass RetryFault(ParentFault):\n    pass\n\nclass Unrelated:\n    pass\n\ndef operation():\n    try:\n        return 1\n    except RetryFault:\n        raise\n"
        index = self.index(source)
        result = compile_context(index, ["operation"], depth=0)
        self.assertIn("Module exception declaration: retrying.py:1-2 | ParentFault", result["text"])
        self.assertIn("class RetryFault(ParentFault):\n    pass", result["text"])
        self.assertNotIn("class Unrelated", result["text"])
        self.assertEqual(result["missing_seeds"], [])
        self.assertTrue(result["complete"])
        self.assertLess(result["text"].index("class ParentFault"), result["text"].index("class RetryFault"))

    def test_exception_declaration_and_function_are_one_budgeted_excerpt(self):
        source = "class LocalFault(Exception):\n" + "    # substantial original declaration\n" * 30 + "    pass\n\ndef operation():\n    raise LocalFault('failed')\n"
        index = self.index(source)
        full = compile_context(index, ["operation"], depth=0)
        self.assertIn(source.split("\n\ndef operation")[0], full["text"])
        bounded = compile_context(index, ["operation"], budget=128, depth=0)
        self.assertEqual(bounded["missing_seeds"], ["retrying.py:operation"])
        self.assertEqual(bounded["included"], [])
        self.assertNotIn("class LocalFault", bounded["text"])
        self.assertNotIn("def operation", bounded["text"])
        self.assertLessEqual(estimate_tokens(bounded["text"]), 128)
        self.assertEqual(bounded["omitted"][0]["reason"], "estimated token budget")

    def test_local_binding_does_not_resolve_to_module_exception(self):
        for binding in ("def operation(LocalFault):\n    raise LocalFault()\n",
                        "def operation():\n    LocalFault = ValueError\n    raise LocalFault()\n",
                        "def operation():\n    from external import LocalFault\n    raise LocalFault()\n"):
            with self.subTest(binding=binding):
                result = compile_context(self.index("class LocalFault(Exception):\n    pass\n\n" + binding), ["operation"], depth=0)
                self.assertNotIn("Module exception declaration:", result["text"])

    def test_ambiguous_or_dynamic_module_declarations_remain_unsupported(self):
        for declaration in ("class LocalFault(Exception):\n    pass\nLocalFault = ValueError\n",
                            "class LocalFault(external.Exception):\n    pass\n",
                            "class LocalFault(Exception):\n    pass\nclass LocalFault(Exception):\n    pass\n",
                            "@transform\nclass LocalFault(Exception):\n    pass\n",
                            "from external import *\nclass LocalFault(Exception):\n    pass\n",
                            "Exception = OtherType\nclass LocalFault(Exception):\n    pass\n"):
            with self.subTest(declaration=declaration):
                result = compile_context(self.index(declaration + "\ndef operation():\n    raise LocalFault()\n"), ["operation"], depth=0)
                self.assertNotIn("Module exception declaration:", result["text"])

    def test_captured_bytes_and_language_boundary_are_preserved(self):
        index = self.index("class LocalFault(Exception):\n    pass\n\ndef operation():\n    raise LocalFault()\n")
        # The root need not contain retrying.py. Compiler evidence must come from
        # this captured index, never a fresh filesystem read or import execution.
        python = compile_context(index, ["operation"], depth=0)
        self.assertIn("class LocalFault(Exception)", python["text"])
        index.symbols["retrying.py:operation"].language = "typescript"
        other = compile_context(index, ["operation"], depth=0)
        self.assertNotIn("Module exception declaration:", other["text"])


if __name__ == "__main__":
    unittest.main()
