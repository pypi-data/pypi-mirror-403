import unittest
from itertools import chain, islice
from nofut import MayBe


class TestMayBe(unittest.TestCase):

    def test_constructor_new(self):
        # MayBe(None) == Nothing
        m = MayBe(None)
        self.assertFalse(m.is_just())
        self.assertTrue(m.is_nothing())
        with self.assertRaises(ValueError):
            m.unwrap()

        # MayBe(x) avec x non-None == Just(x)
        j = MayBe(0)
        self.assertTrue(j.is_just())
        self.assertFalse(j.is_nothing())
        self.assertEqual(j.unwrap(), 0)

    def test_static_constructors(self):
        j = MayBe.just("val")
        self.assertTrue(j.is_just())
        self.assertEqual(j.unwrap(), "val")

        n = MayBe.nothing()
        self.assertTrue(n.is_nothing())
        with self.assertRaises(ValueError):
            n.unwrap()

    def test_or_else_method(self):
        j = MayBe.just("hello")
        self.assertEqual(j.or_else("fallback"), "hello")

        n = MayBe.nothing()
        self.assertEqual(n.or_else("fallback"), "fallback")

    def test_map_method(self):
        # map sur Just
        j = MayBe.just(5)
        j2 = j.map(lambda x: x + 3)
        self.assertTrue(isinstance(j2, MayBe))
        self.assertTrue(j2.is_just())
        self.assertEqual(j2.unwrap(), 8)

        # map sur Nothing
        n = MayBe.nothing()
        n2 = n.map(lambda x: x * 2)
        self.assertTrue(isinstance(n2, MayBe))
        self.assertTrue(n2.is_nothing())

    def test_map_propagates_exceptions(self):
        j = MayBe.just(1)
        with self.assertRaises(ZeroDivisionError):
            j.map(lambda x: x / 0)

    def test_rshift_operator_flat_map(self):
        j = MayBe.just(10)
        # flat_map normal
        r = j >> (lambda x: MayBe.just(x * 2))
        self.assertTrue(isinstance(r, MayBe))
        self.assertEqual(r.unwrap(), 20)

        # chaînage
        r2 = j >> (lambda x: MayBe.just(x + 1)) >> (lambda x: MayBe.just(x * 3))
        self.assertEqual(r2.unwrap(), (10 + 1) * 3)

        # >> sur Nothing reste Nothing
        n = MayBe.nothing()
        n2 = n >> (lambda x: MayBe.just(x + 1))
        self.assertTrue(n2.is_nothing())

    def test_rshift_invalid_return_type(self):
        j = MayBe.just(10)
        with self.assertRaises(TypeError):
            j >> (lambda x: x * 2)

    def test_or_operator(self):
        j = MayBe.just(7)
        # sur Just, renvoie la valeur interne
        self.assertEqual(j | 100, 7)

        n = MayBe.nothing()
        # sur Nothing, renvoie default
        self.assertEqual(n | 100, 100)

        # default peut être un type complexe
        default_obj = {"a": 1}
        self.assertIs(n | default_obj, default_obj)

    def test_bool_truthiness(self):
        j = MayBe.just("x")
        n = MayBe.nothing()
        self.assertTrue(bool(j))
        self.assertFalse(bool(n))

    def test_len(self):
        j = MayBe.just("x")
        n = MayBe.nothing()
        self.assertEqual(len(j), 1)
        self.assertEqual(len(n), 0)

        j_none = MayBe.just(None)
        self.assertEqual(len(j_none), 1)

    def test_iter(self):
        j = MayBe.just("x")
        n = MayBe.nothing()
        self.assertEqual(list(j), ["x"])
        self.assertEqual(list(n), [])

        j_none = MayBe.just(None)
        self.assertEqual(list(j_none), [None])

    def test_iter_edge_cases(self):
        # Unpacking sur Just
        j = MayBe.just(42)
        a, = j
        self.assertEqual(a, 42)

        # Unpacking sur Nothing doit échouer
        n = MayBe.nothing()
        with self.assertRaises(ValueError):
            b, = n

        # Unpacking multiple doit échouer sur Just (1 seul élément)
        with self.assertRaises(ValueError):
            c, d = j

        # For loop sur Just
        items = []
        for x in MayBe.just(99):
            items.append(x)
        self.assertEqual(items, [99])

        # For loop sur Nothing
        items = []
        for x in MayBe.nothing():
            items.append(x)
        self.assertEqual(items, [])

        # Objets complexes dans iter
        complex_obj = {'a': [1, 2], 'b': 'test'}
        j_complex = MayBe.just(complex_obj)
        self.assertEqual(list(j_complex), [complex_obj])

        # Multiple iterations sur le même objet
        j_multi = MayBe.just('reusable')
        self.assertEqual(list(j_multi), ['reusable'])
        self.assertEqual(list(j_multi), ['reusable'])

        # Cohérence len/bool
        for maybe in [MayBe.just(0), MayBe.just(False), MayBe.just(None)]:
            self.assertEqual(bool(maybe), len(maybe) > 0)
        self.assertEqual(bool(MayBe.nothing()), len(MayBe.nothing()) > 0)

    def test_iter_extended_unpacking(self):
        # Extended unpacking sur Just
        j = MayBe.just(42)
        *items, = j
        self.assertEqual(items, [42])

        # Extended unpacking avec variable
        *values, = MayBe.just("test")
        self.assertEqual(values, ["test"])

        # Extended unpacking sur Nothing
        *empty, = MayBe.nothing()
        self.assertEqual(empty, [])

    def test_iter_with_builtins(self):
        # any() sur Just et Nothing
        self.assertTrue(any(MayBe.just(True)))
        self.assertTrue(any(MayBe.just(1)))
        self.assertFalse(any(MayBe.just(False)))
        self.assertFalse(any(MayBe.just(0)))
        self.assertFalse(any(MayBe.nothing()))

        # all() sur Just et Nothing
        self.assertTrue(all(MayBe.just(True)))
        self.assertFalse(all(MayBe.just(False)))
        self.assertTrue(all(MayBe.nothing()))  # vacuously true

        # sum() sur Just contenant un nombre
        self.assertEqual(sum(MayBe.just(10)), 10)
        self.assertEqual(sum(MayBe.nothing()), 0)

        # min/max sur Just
        self.assertEqual(min(MayBe.just(42)), 42)
        self.assertEqual(max(MayBe.just(99)), 99)

        # min/max sur Nothing doit échouer
        with self.assertRaises(ValueError):
            min(MayBe.nothing())

        # sorted() sur Just
        self.assertEqual(sorted(MayBe.just(5)), [5])
        self.assertEqual(sorted(MayBe.nothing()), [])

        # enumerate() sur Just
        result = list(enumerate(MayBe.just("value")))
        self.assertEqual(result, [(0, "value")])

        # zip() avec Just
        j1 = MayBe.just("a")
        j2 = MayBe.just("b")
        self.assertEqual(list(zip(j1, j2)), [("a", "b")])

    def test_iter_with_itertools(self):
        # chain() pour combiner des MayBe
        j1 = MayBe.just(1)
        j2 = MayBe.just(2)
        n = MayBe.nothing()
        result = list(chain(j1, j2, n))
        self.assertEqual(result, [1, 2])

        # islice() sur Just
        j = MayBe.just(100)
        self.assertEqual(list(islice(j, 1)), [100])
        self.assertEqual(list(islice(j, 0)), [])

        # islice() sur Nothing
        self.assertEqual(list(islice(MayBe.nothing(), 10)), [])

    def test_repr(self):
        self.assertEqual(repr(MayBe.just("abc")), "Just(abc)")
        self.assertEqual(repr(MayBe.nothing()), "Nothing")

    def test_store_explicit_none(self):
        # Just(None) doit conserver None
        j = MayBe.just(None)
        self.assertTrue(j.is_just())
        self.assertFalse(j.is_nothing())
        self.assertIsNone(j.unwrap())
        self.assertEqual(repr(j), "Just(None)")
        # or_else ne remplace pas un None stocké
        self.assertIsNone(j.or_else("fallback"))

    def test_map_on_complex_object(self):
        # map doit fonctionner sur tout PyObject
        j = MayBe.just([1, 2, 3])
        j2 = j.map(lambda lst: lst + [4])
        self.assertTrue(j2.is_just())
        self.assertEqual(j2.unwrap(), [1, 2, 3, 4])

    def test_flat_map_on_just(self):
        j = MayBe.just(10)
        r = j.flat_map(lambda x: MayBe.just(x * 2))
        self.assertTrue(r.is_just())
        self.assertEqual(r.unwrap(), 20)

    def test_flat_map_on_nothing(self):
        n = MayBe.nothing()
        r = n.flat_map(lambda x: MayBe.just(x * 2))
        self.assertTrue(r.is_nothing())

    def test_flat_map_not_called_on_nothing(self):
        n = MayBe.nothing()
        called = []

        def fn(x):
            called.append(x)
            return MayBe.just(x)

        r = n.flat_map(fn)
        self.assertTrue(r.is_nothing())
        self.assertEqual(called, [])

    def test_flat_map_returns_nothing(self):
        j = MayBe.just(5)
        r = j.flat_map(lambda x: MayBe.nothing())
        self.assertTrue(r.is_nothing())

    def test_flat_map_invalid_return_type(self):
        j = MayBe.just(3)
        with self.assertRaises(TypeError):
            j.flat_map(lambda x: x * 2)

    def test_flat_map_propagates_exceptions(self):
        j = MayBe.just(1)
        with self.assertRaises(ZeroDivisionError):
            j.flat_map(lambda x: MayBe.just(x / 0))

    def test_class_getitem_generic_syntax(self):
        # MayBe[T] doit retourner la classe MayBe
        aliased = MayBe[int]
        self.assertIs(aliased, MayBe)

        # Fonctionne avec des types complexes
        aliased2 = MayBe[dict]
        self.assertIs(aliased2, MayBe)

        # Les instances fonctionnent normalement après
        j = aliased.just(42)
        self.assertTrue(j.is_just())
        self.assertEqual(j.unwrap(), 42)

    # Tests pour expect()
    def test_expect_just(self):
        j = MayBe.just(42)
        self.assertEqual(j.expect("should not fail"), 42)

    def test_expect_nothing(self):
        n = MayBe.nothing()
        with self.assertRaises(ValueError) as ctx:
            n.expect("custom error message")
        self.assertIn("custom error message", str(ctx.exception))

    # Tests pour to_option()
    def test_to_option_just(self):
        j = MayBe.just("value")
        self.assertEqual(j.to_option(), "value")

    def test_to_option_nothing(self):
        n = MayBe.nothing()
        self.assertIsNone(n.to_option())

    def test_to_option_just_none(self):
        # Just(None) retourne None mais c'est différent de Nothing
        j = MayBe.just(None)
        self.assertIsNone(j.to_option())

    # Tests pour match()
    def test_match_just(self):
        j = MayBe.just(10)
        result = j.match(just=lambda x: x * 2, nothing=lambda: -1)
        self.assertEqual(result, 20)

    def test_match_nothing(self):
        n = MayBe.nothing()
        result = n.match(just=lambda x: x * 2, nothing=lambda: -1)
        self.assertEqual(result, -1)

    def test_match_just_only(self):
        j = MayBe.just(5)
        result = j.match(just=lambda x: x + 1)
        self.assertEqual(result, 6)

    def test_match_nothing_only(self):
        n = MayBe.nothing()
        result = n.match(nothing=lambda: "empty")
        self.assertEqual(result, "empty")

    def test_match_no_callbacks(self):
        j = MayBe.just(5)
        n = MayBe.nothing()
        self.assertIsNone(j.match())
        self.assertIsNone(n.match())

    def test_match_partial_on_just(self):
        j = MayBe.just(5)
        # only nothing callback, but value is Just
        result = j.match(nothing=lambda: "fallback")
        self.assertIsNone(result)

    def test_match_partial_on_nothing(self):
        n = MayBe.nothing()
        # only just callback, but value is Nothing
        result = n.match(just=lambda x: x * 2)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
