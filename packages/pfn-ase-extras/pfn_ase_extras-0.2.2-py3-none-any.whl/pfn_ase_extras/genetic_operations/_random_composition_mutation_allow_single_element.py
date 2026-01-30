from __future__ import annotations

from ase import Atoms
from ase_ga.slab_operators import get_add_remove_lists
from ase_ga.slab_operators import get_ordered_composition
from ase_ga.slab_operators import RandomCompositionMutation
import numpy as np
from numpy.random import RandomState


class RandomCompositionMutationAllowingSingleElement(RandomCompositionMutation):
    """Change the current composition to another of the allowed compositions.

    Returns None when single-element atoms are given.
    """

    def __init__(
        self,
        verbose: bool = False,
        num_muts: int = 1,
        element_pools: list[list[str]] | None = None,
        allowed_compositions: list[tuple[int]] | None = None,
        rng: RandomState = RandomState(),
    ):
        super().__init__(
            verbose=verbose,
            num_muts=num_muts,
            allowed_compositions=allowed_compositions,
            distribution_correction_function=None,
            element_pools=element_pools,
            rng=rng,
        )

        self.descriptor = "RandomCompositionMutationAllowingSingleElement"

    def get_new_individual(self, parents: list[Atoms]) -> tuple[Atoms | None, str]:
        f = parents[0].copy()
        parent_message = ": Parent {0}".format(f.info["confid"])

        if (
            self.allowed_compositions is None
            and len(set(f.get_chemical_symbols())) == 1
            and self.element_pools is None
        ):
            # We cannot find another composition without knowledge of
            # other allowed elements or compositions
            return None, self.descriptor + parent_message

        n_elems = len(set(f.get_atomic_numbers()))
        n_atoms = len(f)

        # self.mutate() returns error when n_elems == n_atoms.
        # This is a workaround for it.
        if n_elems == n_atoms or n_elems == 1:
            return None, self.descriptor + parent_message

        # Do the operation
        indi = self.initialize_individual(f, self.operate(f))
        indi.info["data"]["parents"] = [i.info["confid"] for i in parents]

        return self.finalize_individual(indi), self.descriptor + parent_message

    def _sample_allowed_comp(self, n_atoms: int, n_elems: int) -> list[int]:
        assert n_elems < n_atoms
        shuffled = self.rng.permutation(np.array([1] * (n_atoms - n_elems) + [0] * (n_elems - 1)))
        encoded = "".join([str(i) for i in shuffled])
        chosen = [len(ones) + 1 for ones in encoded.split("0")]
        return chosen

    def operate(self, atoms: Atoms) -> Atoms:
        syms = atoms.get_chemical_symbols()
        unique_syms, _, comp = get_ordered_composition(syms, self.element_pools)

        if self.allowed_compositions is not None:
            allowed_comps = self.allowed_compositions
            for i, allowed in enumerate(allowed_comps):
                if comp == tuple(allowed):
                    allowed_comps = np.delete(allowed_comps, i, axis=0)
                    break
            chosen = allowed_comps[self.rng.randint(len(allowed_comps))]
        else:
            n_elems = len(set(atoms.get_chemical_symbols()))
            n_atoms = len(atoms)
            while True:
                chosen = self._sample_allowed_comp(n_atoms, n_elems)
                if chosen != comp:
                    break

        comp_diff = self.get_composition_diff(comp, chosen)

        # Get difference from current composition
        to_add, to_rem = get_add_remove_lists(**dict(zip(unique_syms, comp_diff)))

        # Correct current composition
        syms = atoms.get_chemical_symbols()
        for add, rem in zip(to_add, to_rem):
            tbc = [i for i in range(len(syms)) if syms[i] == rem]
            ai = self.rng.choice(tbc)
            syms[ai] = add

        atoms.set_chemical_symbols(syms)
        self.dcf(atoms)
        return atoms
