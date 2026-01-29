import unittest
from itertools import chain, islice
from nofut import Result


class TestResult(unittest.TestCase):

    def test_static_constructors(self):
        ok = Result.ok(42)
        self.assertTrue(ok.is_ok())
        self.assertFalse(ok.is_err())
        self.assertEqual(ok.unwrap(), 42)

        err = Result.err("error message")
        self.assertTrue(err.is_err())
        self.assertFalse(err.is_ok())

    def test_err_with_code(self):
        err = Result.err("not found", code="NOT_FOUND")
        self.assertTrue(err.is_err())
        msg, code, details = err.unwrap_err()
        self.assertEqual(msg, "not found")
        self.assertEqual(code, "NOT_FOUND")
        self.assertIsNone(details)

    def test_err_with_details(self):
        err = Result.err("validation", code="INVALID", details={"field": "name"})
        msg, code, details = err.unwrap_err()
        self.assertEqual(msg, "validation")
        self.assertEqual(code, "INVALID")
        self.assertEqual(details, {"field": "name"})

    def test_err_message_only(self):
        err = Result.err("simple error")
        msg, code, details = err.unwrap_err()
        self.assertEqual(msg, "simple error")
        self.assertIsNone(code)
        self.assertIsNone(details)

    def test_unwrap_errors(self):
        ok = Result.ok(42)
        err = Result.err("error")

        with self.assertRaises(ValueError):
            err.unwrap()

        with self.assertRaises(ValueError):
            ok.unwrap_err()

    def test_unwrap_or(self):
        ok = Result.ok("success")
        self.assertEqual(ok.unwrap_or("fallback"), "success")

        err = Result.err("error")
        self.assertEqual(err.unwrap_or("fallback"), "fallback")

    def test_map_on_ok(self):
        ok = Result.ok(5)
        r2 = ok.map(lambda x: x + 3)
        self.assertTrue(isinstance(r2, Result))
        self.assertTrue(r2.is_ok())
        self.assertEqual(r2.unwrap(), 8)

    def test_map_on_err(self):
        err = Result.err("error")
        r2 = err.map(lambda x: x * 2)
        self.assertTrue(isinstance(r2, Result))
        self.assertTrue(r2.is_err())

    def test_map_err_on_err(self):
        err = Result.err("error", code="CODE")
        r2 = err.map_err(lambda msg, code, details: (f"wrapped: {msg}", code, details))
        self.assertTrue(r2.is_err())
        msg, code, _ = r2.unwrap_err()
        self.assertEqual(msg, "wrapped: error")
        self.assertEqual(code, "CODE")

    def test_map_err_on_ok(self):
        ok = Result.ok(42)
        r2 = ok.map_err(lambda msg, code, details: (f"wrapped: {msg}", code, details))
        self.assertTrue(r2.is_ok())
        self.assertEqual(r2.unwrap(), 42)

    def test_map_err_not_called_on_ok(self):
        ok = Result.ok(42)
        called = []

        def fn(msg, code, details):
            called.append((msg, code, details))
            return ("wrapped", code, details)

        r2 = ok.map_err(fn)
        self.assertTrue(r2.is_ok())
        self.assertEqual(r2.unwrap(), 42)
        self.assertEqual(called, [])

    def test_map_err_invalid_return_type(self):
        err = Result.err("error")
        with self.assertRaises(TypeError):
            err.map_err(lambda msg, code, details: "not-a-tuple")

    def test_map_err_propagates_exceptions(self):
        err = Result.err("error")
        with self.assertRaises(ZeroDivisionError):
            err.map_err(lambda msg, code, details: 1 / 0)

    def test_map_propagates_exceptions(self):
        ok = Result.ok(1)
        with self.assertRaises(ZeroDivisionError):
            ok.map(lambda x: x / 0)

    def test_flat_map_on_ok(self):
        ok = Result.ok(10)
        r = ok.flat_map(lambda x: Result.ok(x * 2))
        self.assertTrue(r.is_ok())
        self.assertEqual(r.unwrap(), 20)

    def test_flat_map_on_err(self):
        err = Result.err("error")
        r = err.flat_map(lambda x: Result.ok(x * 2))
        self.assertTrue(r.is_err())

    def test_flat_map_not_called_on_err(self):
        err = Result.err("error")
        called = []

        def fn(x):
            called.append(x)
            return Result.ok(x)

        r = err.flat_map(fn)
        self.assertTrue(r.is_err())
        self.assertEqual(called, [])

    def test_flat_map_returns_err(self):
        ok = Result.ok(5)
        r = ok.flat_map(lambda x: Result.err("oops"))
        self.assertTrue(r.is_err())

    def test_flat_map_invalid_return_type(self):
        ok = Result.ok(3)
        with self.assertRaises(TypeError):
            ok.flat_map(lambda x: x * 2)

    def test_and_then_alias(self):
        ok = Result.ok(10)
        r = ok.and_then(lambda x: Result.ok(x * 2))
        self.assertTrue(r.is_ok())
        self.assertEqual(r.unwrap(), 20)

    def test_rshift_operator(self):
        ok = Result.ok(10)
        r = ok >> (lambda x: Result.ok(x * 2))
        self.assertTrue(isinstance(r, Result))
        self.assertEqual(r.unwrap(), 20)

        # chainage
        r2 = ok >> (lambda x: Result.ok(x + 1)) >> (lambda x: Result.ok(x * 3))
        self.assertEqual(r2.unwrap(), (10 + 1) * 3)

        # >> sur Err reste Err
        err = Result.err("error")
        e2 = err >> (lambda x: Result.ok(x + 1))
        self.assertTrue(e2.is_err())

    def test_rshift_invalid_return_type(self):
        ok = Result.ok(10)
        with self.assertRaises(TypeError):
            ok >> (lambda x: x * 2)

    def test_or_operator(self):
        ok = Result.ok(7)
        self.assertEqual(ok | 100, 7)

        err = Result.err("error")
        self.assertEqual(err | 100, 100)

    def test_bool_truthiness(self):
        ok = Result.ok("x")
        err = Result.err("error")
        self.assertTrue(bool(ok))
        self.assertFalse(bool(err))

    def test_len(self):
        ok = Result.ok("x")
        err = Result.err("error")
        self.assertEqual(len(ok), 1)
        self.assertEqual(len(err), 0)

        ok_none = Result.ok(None)
        self.assertEqual(len(ok_none), 1)

    def test_iter(self):
        ok = Result.ok("x")
        err = Result.err("error")
        self.assertEqual(list(ok), ["x"])
        self.assertEqual(list(err), [])

        ok_none = Result.ok(None)
        self.assertEqual(list(ok_none), [None])

    def test_iter_edge_cases(self):
        # Unpacking sur Ok
        ok = Result.ok(42)
        a, = ok
        self.assertEqual(a, 42)

        # Unpacking sur Err doit échouer
        err = Result.err("fail")
        with self.assertRaises(ValueError):
            b, = err

        # Unpacking multiple doit échouer sur Ok (1 seul élément)
        with self.assertRaises(ValueError):
            c, d = ok

        # For loop sur Ok
        items = []
        for x in Result.ok(99):
            items.append(x)
        self.assertEqual(items, [99])

        # For loop sur Err
        items = []
        for x in Result.err("error"):
            items.append(x)
        self.assertEqual(items, [])

        # Objets complexes dans iter
        complex_obj = {'a': [1, 2], 'b': 'test'}
        ok_complex = Result.ok(complex_obj)
        self.assertEqual(list(ok_complex), [complex_obj])

        # Multiple iterations sur le même objet
        ok_multi = Result.ok('reusable')
        self.assertEqual(list(ok_multi), ['reusable'])
        self.assertEqual(list(ok_multi), ['reusable'])

        # Cohérence len/bool
        for result in [Result.ok(0), Result.ok(False), Result.ok(None)]:
            self.assertEqual(bool(result), len(result) > 0)
        self.assertEqual(bool(Result.err("e")), len(Result.err("e")) > 0)

    def test_iter_extended_unpacking(self):
        # Extended unpacking sur Ok
        ok = Result.ok(42)
        *items, = ok
        self.assertEqual(items, [42])

        # Extended unpacking avec variable
        *values, = Result.ok("test")
        self.assertEqual(values, ["test"])

        # Extended unpacking sur Err
        *empty, = Result.err("error")
        self.assertEqual(empty, [])

    def test_iter_with_builtins(self):
        # any() sur Ok et Err
        self.assertTrue(any(Result.ok(True)))
        self.assertTrue(any(Result.ok(1)))
        self.assertFalse(any(Result.ok(False)))
        self.assertFalse(any(Result.ok(0)))
        self.assertFalse(any(Result.err("error")))

        # all() sur Ok et Err
        self.assertTrue(all(Result.ok(True)))
        self.assertFalse(all(Result.ok(False)))
        self.assertTrue(all(Result.err("error")))  # vacuously true

        # sum() sur Ok contenant un nombre
        self.assertEqual(sum(Result.ok(10)), 10)
        self.assertEqual(sum(Result.err("error")), 0)

        # min/max sur Ok
        self.assertEqual(min(Result.ok(42)), 42)
        self.assertEqual(max(Result.ok(99)), 99)

        # min/max sur Err doit échouer
        with self.assertRaises(ValueError):
            min(Result.err("error"))

        # sorted() sur Ok
        self.assertEqual(sorted(Result.ok(5)), [5])
        self.assertEqual(sorted(Result.err("error")), [])

        # enumerate() sur Ok
        result = list(enumerate(Result.ok("value")))
        self.assertEqual(result, [(0, "value")])

        # zip() avec Ok
        ok1 = Result.ok("a")
        ok2 = Result.ok("b")
        self.assertEqual(list(zip(ok1, ok2)), [("a", "b")])

    def test_iter_with_itertools(self):
        # chain() pour combiner des Result
        ok1 = Result.ok(1)
        ok2 = Result.ok(2)
        err = Result.err("error")
        result = list(chain(ok1, ok2, err))
        self.assertEqual(result, [1, 2])

        # islice() sur Ok
        ok = Result.ok(100)
        self.assertEqual(list(islice(ok, 1)), [100])
        self.assertEqual(list(islice(ok, 0)), [])

        # islice() sur Err
        self.assertEqual(list(islice(Result.err("error"), 10)), [])

    def test_repr(self):
        self.assertEqual(repr(Result.ok(42)), "Ok(42)")
        self.assertEqual(repr(Result.err("fail")), "Err('fail')")
        self.assertEqual(repr(Result.err("fail", code="CODE")), "Err('fail', code='CODE')")

    def test_to_dict_ok(self):
        ok = Result.ok(42)
        d = ok.to_dict()
        self.assertEqual(d, {"ok": True, "value": 42})

    def test_to_dict_ok_complex(self):
        ok = Result.ok({"name": "test", "id": 1})
        d = ok.to_dict()
        self.assertEqual(d, {"ok": True, "value": {"name": "test", "id": 1}})

    def test_to_dict_err_simple(self):
        err = Result.err("not found")
        d = err.to_dict()
        self.assertEqual(d, {"ok": False, "error": "not found"})

    def test_to_dict_err_with_code(self):
        err = Result.err("not found", code="NOT_FOUND")
        d = err.to_dict()
        self.assertEqual(d, {"ok": False, "error": "not found", "code": "NOT_FOUND"})

    def test_to_dict_err_full(self):
        err = Result.err("validation", code="INVALID", details={"field": "name"})
        d = err.to_dict()
        self.assertEqual(d, {"ok": False, "error": "validation", "code": "INVALID", "details": {"field": "name"}})

    def test_store_none_in_ok(self):
        ok = Result.ok(None)
        self.assertTrue(ok.is_ok())
        self.assertIsNone(ok.unwrap())

    def test_ok_requires_value(self):
        with self.assertRaises(TypeError):
            Result.ok()

    def test_chained_operations(self):
        def safe_div(a, b):
            if b == 0:
                return Result.err("division by zero", code="DIV_ZERO")
            return Result.ok(a / b)

        result = Result.ok(10) >> (lambda x: safe_div(x, 2)) >> (lambda x: safe_div(x, 5))
        self.assertTrue(result.is_ok())
        self.assertEqual(result.unwrap(), 1.0)

        result_err = Result.ok(10) >> (lambda x: safe_div(x, 0)) >> (lambda x: safe_div(x, 5))
        self.assertTrue(result_err.is_err())
        msg, code, _ = result_err.unwrap_err()
        self.assertEqual(msg, "division by zero")
        self.assertEqual(code, "DIV_ZERO")

    def test_class_getitem_generic_syntax(self):
        # Result[T, E] doit retourner la classe Result
        aliased = Result[int, str]
        self.assertIs(aliased, Result)

        # Fonctionne avec des types complexes
        aliased2 = Result[dict, Exception]
        self.assertIs(aliased2, Result)

        # Les instances fonctionnent normalement après
        ok = aliased.ok(42)
        self.assertTrue(ok.is_ok())
        self.assertEqual(ok.unwrap(), 42)

    # Tests pour expect()
    def test_expect_ok(self):
        ok = Result.ok(42)
        self.assertEqual(ok.expect("should not fail"), 42)

    def test_expect_err(self):
        err = Result.err("original error")
        with self.assertRaises(ValueError) as ctx:
            err.expect("custom error message")
        self.assertIn("custom error message", str(ctx.exception))

    # Tests pour to_option()
    def test_to_option_ok(self):
        ok = Result.ok("value")
        self.assertEqual(ok.to_option(), "value")

    def test_to_option_err(self):
        err = Result.err("error")
        self.assertIsNone(err.to_option())

    def test_to_option_ok_none(self):
        ok = Result.ok(None)
        self.assertIsNone(ok.to_option())

    # Tests pour from_dict()
    def test_from_dict_ok(self):
        d = {"ok": True, "value": 42}
        r = Result.from_dict(d)
        self.assertTrue(r.is_ok())
        self.assertEqual(r.unwrap(), 42)

    def test_from_dict_ok_complex(self):
        d = {"ok": True, "value": {"name": "test", "id": 1}}
        r = Result.from_dict(d)
        self.assertTrue(r.is_ok())
        self.assertEqual(r.unwrap(), {"name": "test", "id": 1})

    def test_from_dict_err_simple(self):
        d = {"ok": False, "error": "not found"}
        r = Result.from_dict(d)
        self.assertTrue(r.is_err())
        msg, code, details = r.unwrap_err()
        self.assertEqual(msg, "not found")
        self.assertIsNone(code)
        self.assertIsNone(details)

    def test_from_dict_err_with_code(self):
        d = {"ok": False, "error": "not found", "code": "NOT_FOUND"}
        r = Result.from_dict(d)
        self.assertTrue(r.is_err())
        msg, code, details = r.unwrap_err()
        self.assertEqual(msg, "not found")
        self.assertEqual(code, "NOT_FOUND")

    def test_from_dict_err_full(self):
        d = {"ok": False, "error": "validation", "code": "INVALID", "details": {"field": "name"}}
        r = Result.from_dict(d)
        self.assertTrue(r.is_err())
        msg, code, details = r.unwrap_err()
        self.assertEqual(msg, "validation")
        self.assertEqual(code, "INVALID")
        self.assertEqual(details, {"field": "name"})

    def test_from_dict_roundtrip_ok(self):
        original = Result.ok({"data": [1, 2, 3]})
        d = original.to_dict()
        restored = Result.from_dict(d)
        self.assertTrue(restored.is_ok())
        self.assertEqual(restored.unwrap(), {"data": [1, 2, 3]})

    def test_from_dict_roundtrip_err(self):
        original = Result.err("error", code="CODE", details={"x": 1})
        d = original.to_dict()
        restored = Result.from_dict(d)
        self.assertTrue(restored.is_err())
        msg, code, details = restored.unwrap_err()
        self.assertEqual(msg, "error")
        self.assertEqual(code, "CODE")
        self.assertEqual(details, {"x": 1})

    def test_from_dict_missing_ok_key(self):
        d = {"value": 42}
        with self.assertRaises(ValueError):
            Result.from_dict(d)

    def test_from_dict_missing_value_key(self):
        d = {"ok": True}
        with self.assertRaises(ValueError):
            Result.from_dict(d)

    def test_from_dict_missing_error_key(self):
        d = {"ok": False}
        with self.assertRaises(ValueError):
            Result.from_dict(d)

    # Tests pour match()
    def test_match_ok(self):
        ok = Result.ok(10)
        result = ok.match(ok=lambda x: x * 2, err=lambda msg, code, details: -1)
        self.assertEqual(result, 20)

    def test_match_err(self):
        err = Result.err("error", code="CODE")
        result = err.match(ok=lambda x: x, err=lambda msg, code, details: f"{msg}:{code}")
        self.assertEqual(result, "error:CODE")

    def test_match_err_with_details(self):
        err = Result.err("error", code="CODE", details={"x": 1})
        result = err.match(err=lambda msg, code, details: details["x"])
        self.assertEqual(result, 1)

    def test_match_ok_only(self):
        ok = Result.ok(5)
        result = ok.match(ok=lambda x: x + 1)
        self.assertEqual(result, 6)

    def test_match_err_only(self):
        err = Result.err("error")
        result = err.match(err=lambda msg, code, details: msg)
        self.assertEqual(result, "error")

    def test_match_no_callbacks(self):
        ok = Result.ok(5)
        err = Result.err("error")
        self.assertIsNone(ok.match())
        self.assertIsNone(err.match())

    def test_match_partial_on_ok(self):
        ok = Result.ok(5)
        result = ok.match(err=lambda msg, code, details: "fallback")
        self.assertIsNone(result)

    def test_match_partial_on_err(self):
        err = Result.err("error")
        result = err.match(ok=lambda x: x * 2)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
