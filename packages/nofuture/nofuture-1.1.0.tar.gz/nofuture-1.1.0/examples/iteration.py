# Example 4/4: Collection protocols
"""
Ces fonctionnalités permettent d'utiliser MayBe et Result comme des collections
de 0 ou 1 élément, ce qui offre une intégration fluide avec l'écosystème Python.
"""

from itertools import chain, filterfalse
from nofut import MayBe, Result


def example_len():
    """len() retourne 1 pour Just/Ok, 0 pour Nothing/Err"""
    print("# len()")

    # MayBe
    just = MayBe.just(42)
    nothing = MayBe.nothing()
    print(f"len(Just(42)) = {len(just)}")
    print(f"len(Nothing) = {len(nothing)}")

    # Result
    ok = Result.ok("success")
    err = Result.err("failure")
    print(f"len(Ok('success')) = {len(ok)}")
    print(f"len(Err('failure')) = {len(err)}")
    print()


def example_unpacking():
    """Unpacking permet d'extraire la valeur de manière concise"""
    print("# Unpacking")

    # MayBe unpacking
    just = MayBe.just(100)
    (value,) = just
    print(f"Unpacking Just(100): {value}")

    # Extended unpacking
    (*items,) = MayBe.just([1, 2, 3])
    print(f"Extended unpacking: {items}")

    # Result unpacking
    ok = Result.ok(dict(status='ready'))
    (data,) = ok
    print(f"Unpacking Ok: {data}")

    # Unpacking Nothing/Err échoue proprement
    try:
        (val,) = MayBe.nothing()
    except ValueError as e:
        print(f"Unpacking Nothing: {e}")
    print()


def example_for_loops():
    """For loops sur MayBe/Result"""
    print("# For loops")

    # Traiter une valeur optionnelle
    maybe_user = MayBe.just(dict(name='Alice', age=30))
    for user in maybe_user:
        print(f"User found: {user['name']}, age {user['age']}")

    # Nothing n'exécute pas le loop
    for x in MayBe.nothing():
        print(f"This won't print: {x}")

    # Même chose avec Result
    for value in Result.ok(42):
        print(f"Ok value: {value}")

    for value in Result.err("error"):
        print(f"This won't print: {value}")
    print()


def example_builtins():
    """Utilisation avec les fonctions builtin Python"""
    print("# Builtin functions")

    # any() / all()
    print(f"any(Just(True)) = {any(MayBe.just(True))}")
    print(f"any(Just(False)) = {any(MayBe.just(False))}")
    print(f"any(Nothing) = {any(MayBe.nothing())}")
    print(f"all(Nothing) = {all(MayBe.nothing())}  # vacuously true")

    # sum()
    maybe_price = MayBe.just(99)
    total = sum(maybe_price)
    print(f"sum(Just(99)) = {total}")

    # min/max
    maybe_score = Result.ok(87)
    print(f"max(Ok(87)) = {max(maybe_score)}")

    # sorted()
    items = sorted(MayBe.just(5))
    print(f"sorted(Just(5)) = {items}")
    print()


def example_itertools():
    """Combinaison avec itertools pour des patterns avancés"""
    print("# itertools")

    # chain() pour combiner plusieurs MayBe/Result
    m1 = MayBe.just(1)
    m2 = MayBe.nothing()
    m3 = MayBe.just(2)
    m4 = MayBe.just(3)

    combined = list(chain(m1, m2, m3, m4))
    print(f"chain(Just(1), Nothing, Just(2), Just(3)) = {combined}")

    # Combiner des Results (extraire les valeurs Ok uniquement)
    results = [
        Result.ok(10),
        Result.err("error"),
        Result.ok(20),
        Result.ok(30),
    ]
    values = list(chain(*results))
    print(f"Extraire valeurs Ok uniquement: {values}")
    print()


def example_zip_enumerate():
    """zip() et enumerate() avec MayBe/Result"""
    print("# zip() et enumerate()")

    # zip pour combiner deux MayBe
    name = MayBe.just("Alice")
    age = MayBe.just(30)

    for n, a in zip(name, age):
        print(f"zip: {n} is {a} years old")

    # Si l'un est Nothing, zip ne produit rien
    empty_zip = list(zip(MayBe.just("Bob"), MayBe.nothing()))
    print(f"zip avec Nothing: {empty_zip}")

    # enumerate sur Result
    for i, val in enumerate(Result.ok("first")):
        print(f"enumerate: index={i}, value={val}")
    print()


def example_filtering():
    """Utiliser les itérateurs pour filtrer des collections"""
    print("# Filtering patterns")

    # Extraire uniquement les valeurs présentes
    items = [
        MayBe.just(1),
        MayBe.nothing(),
        MayBe.just(2),
        MayBe.nothing(),
        MayBe.just(3),
    ]

    # Méthode 1: chain
    values = list(chain(*items))
    print(f"Extraire valeurs avec chain: {values}")

    # Méthode 2: list comprehension avec len()
    values2 = [val for item in items for val in item]
    print(f"Extraire valeurs avec comprehension: {values2}")

    # Filtrer par taille (éliminer les Nothing/Err)
    present = [m for m in items if len(m) > 0]
    print(f"Filtrer les Nothing: {len(present)} éléments restants")
    print()


def example_practical_use_case():
    """Cas d'usage pratique: validation de formulaire"""
    print("# Cas pratique: validation")

    def validate_age(age_str):
        """Valide et parse un âge"""
        if not age_str:
            return Result.err("Age manquant")
        try:
            age = int(age_str)
            if age < 0 or age > 150:
                return Result.err("Age invalide", code='RANGE_ERROR')
            return Result.ok(age)
        except ValueError:
            return Result.err("Age doit être un nombre", code='PARSE_ERROR')

    # Valider plusieurs champs
    inputs = ['25', 'invalid', '200', '30']
    results = [validate_age(inp) for inp in inputs]

    # Extraire uniquement les âges valides
    valid_ages = list(chain(*results))
    print(f"Âges valides: {valid_ages}")

    # Compter les erreurs
    error_count = sum(1 for r in results if len(r) == 0)
    print(f"Nombre d'erreurs: {error_count}")

    # Calculer la moyenne des âges valides (si présents)
    if valid_ages:
        avg = sum(valid_ages) / len(valid_ages)
        print(f"Âge moyen: {avg}")
    print()


def example_bool_len_consistency():
    """Cohérence entre bool() et len()"""
    print("# Cohérence bool/len")

    # Pour MayBe et Result: bool(x) == (len(x) > 0)
    test_cases = [
        MayBe.just(42),
        MayBe.just(0),
        MayBe.just(False),
        MayBe.just(None),
        MayBe.nothing(),
        Result.ok("ok"),
        Result.err("err"),
    ]

    for case in test_cases:
        b = bool(case)
        l = len(case)
        consistent = b == (l > 0)
        print(f"{repr(case):30} bool={b} len={l} consistent={consistent}")
    print()


if __name__ == '__main__':
    example_len()
    example_unpacking()
    example_for_loops()
    example_builtins()
    example_itertools()
    example_zip_enumerate()
    example_filtering()
    example_practical_use_case()
    example_bool_len_consistency()

    print("# Résumé")
    print("MayBe et Result se comportent comme des collections de 0 ou 1 élément:")
    print("- len() retourne 1 si la valeur est présente, 0 sinon")
    print("- Itération sur Just/Ok produit 1 élément, sur Nothing/Err produit 0")
    print("- Compatible avec unpacking, for loops, builtins (any/all/sum/etc), itertools")
    print("- bool(x) == (len(x) > 0) pour une cohérence totale")
