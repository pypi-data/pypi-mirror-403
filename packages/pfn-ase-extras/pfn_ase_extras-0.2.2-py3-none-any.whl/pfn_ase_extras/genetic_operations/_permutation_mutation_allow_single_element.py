from __future__ import annotations

from ase import Atoms
from ase_ga.standardmutations import PermutationMutation
from numpy.random import RandomState


class PermutationMutationAllowingSingleElement(PermutationMutation):
    """Mutation that permutes a percentage of the atom types in the cluster.

    Returns None when single-element or n_elems == n_atoms are given.
    """

    def __init__(
        self,
        n_top: int | None,
        probability: float = 0.33,
        test_dist_to_slab: bool = True,
        use_tags: bool = False,
        blmin: dict[tuple[int, int], float] | None = None,
        rng: RandomState = RandomState(),
        verbose: bool = False,
    ):
        super().__init__(
            n_top=n_top,
            probability=probability,
            test_dist_to_slab=test_dist_to_slab,
            use_tags=use_tags,
            blmin=blmin,
            rng=rng,
            verbose=verbose,
        )
        self.descriptor = "PermutationMutationAllowingSingleElement"

    def get_new_individual(self, parents: list[Atoms]) -> tuple[Atoms | None, str]:
        f = parents[0].copy()

        # return None if parent is single element
        if len(set(f.get_atomic_numbers())) == 1:
            return None, "mutation: permutation"

        indi = self.mutate(f)
        if indi is None:
            return indi, "mutation: permutation"

        indi = self.initialize_individual(f, indi)
        indi.info["data"]["parents"] = [f.info["confid"]]

        return self.finalize_individual(indi), "mutation: permutation"
