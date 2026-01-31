"""
Core functionality for balancing chemical equations.
"""

from __future__ import annotations

from itertools import combinations
from math import gcd
from functools import reduce

from sympy import Matrix, Rational
from pymatgen.core import Composition


def _gcd_list(nums):
    """Calculate GCD of a list of numbers."""
    nums = [abs(int(x)) for x in nums if int(x) != 0]
    return reduce(gcd, nums) if nums else 1


def _lcm(a: int, b: int) -> int:
    """Calculate LCM of two numbers."""
    return abs(a * b) // gcd(a, b) if a and b else 0


def _lcm_list(nums):
    """Calculate LCM of a list of numbers."""
    nums = [abs(int(n)) for n in nums if int(n) != 0]
    return reduce(_lcm, nums, 1) if nums else 1


def _to_sympy_rational(x):
    """Convert number to sympy Rational using string representation."""
    return Rational(str(x))


def _composition_to_counts(formula: str) -> dict[str, object]:
    """Convert chemical formula to element counts dictionary."""
    comp = Composition(formula)
    d = comp.get_el_amt_dict()
    return {el: _to_sympy_rational(amt) for el, amt in d.items()}


def balance_rxns(
    reactants,
    products,
    *,
    max_products_in_equation: int | None = None,
    require_all_reactants_used: bool = True,
):
    """
    Balance chemical equations and find all possible reactions.
    
    Args:
        reactants: List or tuple of reactant chemical formulas (e.g., ["Fe", "O2"])
        products: List or tuple of product chemical formulas (e.g., ["FeO", "Fe2O3"])
        max_products_in_equation: Maximum number of products in a single equation (default: all)
        require_all_reactants_used: Whether all reactants must be used (default: True)
    
    Returns:
        List of balanced equations. Each element is a list containing:
        - [0]: String representation of the equation (e.g., "4Fe + 3O2 -> 2Fe2O3")
        - [1]: Dictionary of reactants with their coefficients
        - [2]: Dictionary of products with their coefficients
    
    Example:
        >>> reactants = ("Fe", "O2")
        >>> products = ("FeO", "Fe2O3", "Fe3O4")
        >>> results = balance_rxns(reactants, products)
        >>> for eq, r_map, p_map in results:
        ...     print(eq)
        2Fe + O2 -> 2FeO
        4Fe + 3O2 -> 2Fe2O3
        3Fe + 2O2 -> Fe3O4
    """
    reactants = list(reactants)
    products = list(products)

    r_counts = [_composition_to_counts(f) for f in reactants]
    p_counts = [_composition_to_counts(f) for f in products]

    nP = len(products)
    min_k, max_k = 1, (nP if max_products_in_equation is None else min(nP, max_products_in_equation))

    results = []
    dedup = set()

    for k in range(min_k, max_k + 1):
        for idxs in combinations(range(nP), k):
            chosen_products = [products[i] for i in idxs]
            chosen_p_counts = [p_counts[i] for i in idxs]

            species = reactants + chosen_products
            counts = r_counts + chosen_p_counts

            elements = sorted({e for d in counts for e in d.keys()})
            if not elements:
                continue

            # A x = 0; reactants as negative, products as positive
            A = []
            for elem in elements:
                row = []
                for j in range(len(reactants)):
                    row.append(-counts[j].get(elem, Rational(0)))
                for j in range(len(reactants), len(species)):
                    row.append(counts[j].get(elem, Rational(0)))
                A.append(row)

            M = Matrix(A)
            ns = M.nullspace()
            if not ns:
                continue

            for v in ns:
                # Extract denominators using as_numer_denom()
                denoms = []
                for term in v:
                    _, den = term.as_numer_denom()
                    denoms.append(int(den))

                L = _lcm_list(denoms)
                ints = [int(term * L) for term in v]

                r_part = ints[:len(reactants)]
                p_part = ints[len(reactants):]

                def all_pos(xs): return all(x > 0 for x in xs)

                if not (all_pos(r_part) and all_pos(p_part)):
                    ints = [-x for x in ints]
                    r_part = ints[:len(reactants)]
                    p_part = ints[len(reactants):]

                if not (all_pos(r_part) and all_pos(p_part)):
                    continue
                if require_all_reactants_used and any(x == 0 for x in r_part):
                    continue
                if any(x == 0 for x in p_part):
                    continue

                g = _gcd_list(ints)
                ints = [x // g for x in ints]
                r_part = ints[:len(reactants)]
                p_part = ints[len(reactants):]

                rmap = {name: coef for name, coef in zip(reactants, r_part)}
                pmap = {name: coef for name, coef in zip(chosen_products, p_part)}

                def fmt_side(m):
                    # Maintain input order
                    parts = []
                    for s, c in m.items():
                        parts.append(f"{c}{s}" if c != 1 else s)
                    return " + ".join(parts)

                eq = f"{fmt_side(rmap)} -> {fmt_side(pmap)}"

                key = (tuple(sorted(rmap.items())), tuple(sorted(pmap.items())))
                if key in dedup:
                    continue
                dedup.add(key)

                results.append([eq, rmap, pmap])

    return results
