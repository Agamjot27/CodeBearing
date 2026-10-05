"""Ranking evidence, trust boundaries, and bounded graph invariants."""

from pathlib import Path
import unittest

from codebearing.index import build_index_from_sources
from codebearing.retrieval import eligible_lessons, hybrid_search, lexical_search, rank_candidates, select_task_seeds


class RetrievalRankerTests(unittest.TestCase):
    def index(self, sources):
        return build_index_from_sources(Path.cwd(), {path: source.encode() for path, source in sources.items()})

    def lesson(self, index, scope, text, identifier=1):
        path = index.symbols[scope].path
        return {"id": identifier, "scope": scope, "lesson": text, "evidence": path,
                "scope_hash": index.hashes[path], "evidence_hash": index.hashes[path],
                "status": "confirmed", "stale": False}

    def test_camel_snake_and_morphological_terms_match(self):
        index = self.index({"payments.py": "def roundRefund(value):\n    return value\n\ndef list_retries():\n    return []\n"})
        result = lexical_search(index, "fix refund rounding")
        self.assertEqual(result[0]["id"], "payments.py:roundRefund")
        self.assertIn("round", result[0]["signals"]["matched_terms"]["name"])
        self.assertEqual(lexical_search(index, "retry")[0]["id"], "payments.py:list_retries")

    def test_generic_query_returns_no_accidental_code_matches(self):
        index = self.index({"a.py": "def helper():\n    return True\n"})
        self.assertEqual(lexical_search(index, "please fix the code function"), [])

    def test_exact_names_preserve_all_filename_and_length_ties(self):
        sources = {f"{path}.py": "def refund():\n" + "    # refund refund\n" * repeats + "    return 0\n"
                   for path, repeats in (("a", 1), ("b_long_name", 30), ("nested/c", 4), ("z", 2))}
        index = self.index(sources)
        result = lexical_search(index, "refund")
        self.assertEqual(len(result), 4)
        self.assertEqual(len({row["score"] for row in result}), 1)
        self.assertEqual([row["id"] for row in result], sorted(index.symbols))
        lesson = self.lesson(index, "z.py:refund", "refund", 1)
        memory = hybrid_search(index, "refund", lessons=[lesson])
        self.assertEqual([row["id"] for row in memory], sorted(index.symbols))
        self.assertEqual(len({row["score"] for row in memory}), 1)

    def test_exact_full_id_wins(self):
        index = self.index({"a.py": "def refund():\n    return 1\n", "b.py": "def refund():\n    return 2\n"})
        self.assertEqual(lexical_search(index, "b.py:refund")[0]["id"], "b.py:refund")

    def test_bm25_saturates_body_frequency(self):
        index = self.index({"a.py": "def helper():\n    # rounding\n    return 1\n",
                            "b.py": "def other():\n" + "    # rounding\n" * 100 + "    return 2\n"})
        scores = {row["id"]: row["score"] for row in lexical_search(index, "rounding")}
        self.assertLess(scores["b.py:other"], scores["a.py:helper"] * 4)

    def test_only_captured_confirmed_current_lessons_are_eligible(self):
        index = self.index({"a.py": "def helper():\n    return 1\n"})
        valid = self.lesson(index, "a.py:helper", "round refunds carefully")
        variants = [dict(valid, id=2, stale=True), dict(valid, id=3, status="proposed"),
                    dict(valid, id=4, scope_hash="bad"), dict(valid, id=5, evidence_hash="bad"),
                    dict(valid, id=6, evidence="../../secret"), dict(valid, id=7, scope="a.py:missing"),
                    dict(valid, id=8, stale=None), dict(valid, id=9, lesson=""), {}]
        self.assertEqual(eligible_lessons(index, [valid, *variants]), [valid])
        index.sources["a.py"] += b"# changed without updating hashes"
        self.assertEqual(eligible_lessons(index, [valid]), [])

    def test_memory_can_localize_an_opaque_scope_without_lexical_matches(self):
        index = self.index({"a.py": "def f_17():\n    return 1\n"})
        lesson = self.lesson(index, "a.py:f_17", "rounding refund calculations")
        self.assertEqual(lexical_search(index, "refund rounding"), [])
        result = hybrid_search(index, "refund rounding", lessons=[lesson])
        self.assertEqual(result[0]["id"], "a.py:f_17")
        self.assertEqual(result[0]["signals"]["lesson_ids"], [1])
        self.assertLessEqual(result[0]["score"], 0.25)
        self.assertEqual(hybrid_search(index, "refund rounding", lessons=[dict(lesson, status="disputed")]), [])

    def test_graph_pool_remains_bounded_and_seeds_lead(self):
        index = self.index({"a.py": "def entry():\n    return linked()\n\ndef linked():\n    return leaf()\n\ndef leaf():\n    return 1\n\ndef unrelated_refund():\n    return 2\n"})
        lesson = self.lesson(index, "a.py:unrelated_refund", "rounding refunds")
        rows = rank_candidates(index, "refund rounding", ["entry"], 1, [lesson])
        self.assertEqual(rows[0]["id"], "a.py:entry")
        self.assertEqual({row["id"] for row in rows}, {"a.py:entry", "a.py:linked"})
        self.assertEqual(rows[1]["distance"], 1)
        self.assertIn("called by a.py:entry", rows[1]["reasons"])

    def test_repeat_lessons_cannot_amplify_scope_memory(self):
        index = self.index({"a.py": "def entry():\n    return 1\n"})
        single = self.lesson(index, "a.py:entry", "refund rounding")
        many = [dict(single, id=number) for number in range(1, 30)]
        result = hybrid_search(index, "refund rounding", lessons=many)
        self.assertEqual(result[0]["score"], hybrid_search(index, "refund rounding", lessons=[single])[0]["score"])

    def test_invalid_limits_are_rejected(self):
        index = self.index({"a.py": "def helper():\n    return 1\n"})
        for invalid in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                lexical_search(index, "helper", invalid)

    def test_disconnected_task_aspects_survive_single_highest_score(self):
        index = self.index({
            "totals.py": "def bookingTotal():\n    return 1\n",
            "service.py": "def confirm():\n    confirmation = 'booking payment'\n    return confirmation\n",
            "transaction.py": "def run_transaction():\n    return 'rollback'\n",
        })
        matches = hybrid_search(index, "booking confirmation payment rollback", limit=50)
        self.assertEqual(sum(row["score"] == matches[0]["score"] for row in matches), 1)
        selection = select_task_seeds(matches)
        self.assertEqual({row["id"] for row in selection["selected"]}, set(index.symbols))
        self.assertEqual(selection, select_task_seeds(matches))

    def test_seed_selection_preserves_exact_ambiguity_and_avoids_redundancy(self):
        index = self.index({
            "a.py": "def refund():\n    return 'payment'\n",
            "b.py": "def refund():\n    return 'payment rollback'\n",
            "c.py": "def other():\n    return 'payment'\n",
        })
        selection = select_task_seeds(hybrid_search(index, "refund"))
        self.assertEqual([row["id"] for row in selection["selected"]], ["a.py:refund", "b.py:refund"])
        self.assertFalse(selection["ambiguous"])
        exact = select_task_seeds(hybrid_search(index, "b.py:refund"))
        self.assertEqual([row["id"] for row in exact["selected"]], ["b.py:refund"])
        only_payment = select_task_seeds(hybrid_search(index, "payment"))
        highest = hybrid_search(index, "payment")[0]["score"]
        self.assertEqual(len(only_payment["selected"]),
                         sum(row["score"] == highest for row in hybrid_search(index, "payment")))
        index = self.index({f"{i}.py": "def duplicate():\n    return 1\n" for i in range(4)})
        ambiguous = select_task_seeds(hybrid_search(index, "duplicate"))
        self.assertTrue(ambiguous["ambiguous"])
        self.assertEqual(ambiguous["selected"], [])
        self.assertEqual(select_task_seeds([])["selected"], [])

    def test_connected_complement_precedes_unrelated_rare_vocabulary(self):
        index = self.index({"flow.py": "def entry():\n    return linked()\n\ndef linked():\n    return 1\n\ndef unrelated():\n    return 2\n\ndef redundant():\n    return 3\n"})
        index.edges["flow.py:entry"].add("flow.py:redundant")
        def row(name, score, terms):
            return {"id": f"flow.py:{name}", "score": score,
                    "signals": {"exact": False, "matched_terms": {"body": terms}}}
        matches = [row("entry", 1, ["request"]), row("unrelated", .8, ["rare", "vocabulary"]),
                   row("linked", .5, ["rollback"]), row("redundant", .4, ["request"])]
        ordinary = select_task_seeds(matches)
        self.assertEqual(ordinary["selected"][1]["id"], "flow.py:unrelated")
        graph = select_task_seeds(matches, index=index)
        self.assertEqual(graph["selected"][1]["id"], "flow.py:linked")
        self.assertEqual(graph["selected"][1]["reason"], "connected complementary matched terms")
        self.assertEqual(graph["selected"][2]["id"], "flow.py:unrelated")
        self.assertEqual(graph, select_task_seeds(matches, index=index))
        self.assertNotIn("flow.py:redundant", [r["id"] for r in graph["selected"]])

    def test_connected_selector_preserves_exact_ties_and_disconnected_fallback(self):
        index = self.index({"a.py": "def refund():\n    return 'payment'\n",
                            "b.py": "def refund():\n    return 'rollback'\n"})
        for query in ("refund", "a.py:refund", "payment rollback"):
            rows = hybrid_search(index, query)
            before = select_task_seeds(rows)
            after = select_task_seeds(rows, index=index)
            self.assertEqual(before["selected"], after["selected"])
            self.assertEqual(before["ambiguous"], after["ambiguous"])


if __name__ == "__main__":
    unittest.main()
