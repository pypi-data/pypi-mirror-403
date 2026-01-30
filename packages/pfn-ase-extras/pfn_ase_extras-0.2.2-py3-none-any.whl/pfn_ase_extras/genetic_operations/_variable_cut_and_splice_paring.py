from __future__ import annotations

from ase import Atoms
from ase_ga.cutandsplicepairing import CutAndSplicePairing
from ase_ga.cutandsplicepairing import Positions
from ase_ga.utilities import atoms_too_close
from ase_ga.utilities import CellBounds
from ase_ga.utilities import gather_atoms_by_tag
from ase.geometry import find_mic
import numpy as np
from numpy.random import RandomState


class VariableCutAndSplicePairing(CutAndSplicePairing):
    """The Cut and Splice operator based on CutAndSplicePairing

    This operation is modified so that to accept different
    number of atoms.

    Parameters:

    blmin: dict
        Dictionary with minimal interatomic distances.
        Note: when preserving molecular identity (see use_tags),
        the blmin dict will (naturally) only be applied
        to intermolecular distances (not the intramolecular
        ones).

    number_of_variable_cell_vectors: int (default 0)
        The number of variable cell vectors (0, 1, 2 or 3).
        To keep things simple, it is the 'first' vectors which
        will be treated as variable, i.e. the 'a' vector in the
        univariate case, the 'a' and 'b' vectors in the bivariate
        case, etc.

    p1: float or int between 0 and 1
        Probability that a parent is shifted over a random
        distance along the normal of the cutting plane
        (only operative if number_of_variable_cell_vectors > 0).

    p2: float or int between 0 and 1
        Same as p1, but for shifting along the directions
        in the cutting plane (only operative if
        number_of_variable_cell_vectors > 0).

    minfrac: float between 0 and 1, or None (default)
        Minimal fraction of atoms a parent must contribute
        to the child. If None, each parent must contribute
        at least one atom.

    cellbounds: ase.ga.utilities.CellBounds instance
        Describing limits on the cell shape, see
        :class:`~ase.ga.utilities.CellBounds`.
        Note that it only make sense to impose conditions
        regarding cell vectors which have been marked as
        variable (see number_of_variable_cell_vectors).

    use_tags: bool
        Whether to use the atomic tags to preserve
        molecular identity.

    rng: Random number generator
        By default numpy.random.
    """

    def __init__(
        self,
        blmin: dict[tuple[int, int], float],
        number_of_variable_cell_vectors: int = 3,
        p1: float = 1.0,
        p2: float = 0.0,
        minfrac: float | None = 0.15,
        cellbounds: CellBounds | None = None,
        use_tags: bool = False,
        rng: RandomState | None = None,
        verbose: bool = False,
    ) -> None:
        if rng is None:
            _rng = RandomState()
        else:
            _rng = rng

        super().__init__(
            slab=None,
            n_top=None,
            blmin=blmin,
            number_of_variable_cell_vectors=number_of_variable_cell_vectors,
            p1=p1,
            p2=p2,
            minfrac=minfrac,
            cellbounds=cellbounds,
            use_tags=use_tags,
            rng=_rng,
            verbose=verbose,
        )

        self.scaling_volume = None
        self.descriptor = "VariableCutAndSplicePairing"
        self.min_inputs = 0

    def cross(self, a1: Atoms, a2: Atoms) -> Atoms | None:
        """Crosses the two atoms objects and returns one"""

        if self.use_tags and not np.array_equal(a1.get_tags(), a2.get_tags()):
            err = "Trying to pair two structures with different tags"
            raise ValueError(err)

        cell1 = a1.get_cell()
        cell2 = a2.get_cell()
        for i in range(self.number_of_variable_cell_vectors, 3):
            err = "Unit cells are supposed to be identical in direction %d"
            assert np.allclose(cell1[i], cell2[i]), (err % i, cell1, cell2)

        invalid = True
        counter = 0
        maxcount = 1000
        a1_copy = a1.copy()
        a2_copy = a2.copy()

        # Run until a valid pairing is made or maxcount pairings are tested.
        while invalid and counter < maxcount:
            counter += 1

            newcell = self.generate_unit_cell(cell1, cell2)
            if newcell is None:
                # No valid unit cell could be generated.
                # This strongly suggests that it is near-impossible
                # to generate one from these parent cells and it is
                # better to abort now.
                break

            # Choose direction of cutting plane normal
            if self.number_of_variable_cell_vectors == 0:
                # Will be generated entirely at random
                theta = np.pi * self.rng.random()
                phi = 2.0 * np.pi * self.rng.random()
                cut_n = np.array(
                    [
                        np.cos(phi) * np.sin(theta),
                        np.sin(phi) * np.sin(theta),
                        np.cos(theta),
                    ]
                )
            else:
                # Pick one of the 'variable' cell vectors
                cut_n = self.rng.choice(self.number_of_variable_cell_vectors)

            # Randomly translate parent structures
            for a_copy, a in zip([a1_copy, a2_copy], [a1, a2]):
                a_copy.set_positions(a.get_positions())

                cell = a_copy.get_cell()
                for i in range(self.number_of_variable_cell_vectors):
                    r = self.rng.random()
                    cond1 = i == cut_n and r < self.p1
                    cond2 = i != cut_n and r < self.p2
                    if cond1 or cond2:
                        a_copy.positions += self.rng.random() * cell[i]

                if self.use_tags:
                    # For correct determination of the center-
                    # of-position of the multi-atom blocks,
                    # we need to group their constituent atoms
                    # together
                    gather_atoms_by_tag(a_copy)
                else:
                    a_copy.wrap()

            # Generate the cutting point in scaled coordinates
            cosp1 = np.average(a1_copy.get_scaled_positions(), axis=0)
            cosp2 = np.average(a2_copy.get_scaled_positions(), axis=0)
            cut_p = np.zeros((1, 3))
            for i in range(3):
                if i < self.number_of_variable_cell_vectors:
                    cut_p[0, i] = self.rng.random()
                else:
                    cut_p[0, i] = 0.5 * (cosp1[i] + cosp2[i])

            # Perform the pairing:
            child = self._get_pairing(a1_copy, a2_copy, cut_p, cut_n, newcell)
            if child is None:
                continue

            child.set_cell(newcell, scale_atoms=False)
            child.wrap()
            # Verify whether the atoms are too close or not:
            if atoms_too_close(child, self.blmin, use_tags=self.use_tags):
                continue

            # Passed all the tests
            return child

        return None

    def _get_pairing(
        self,
        a1: Atoms,
        a2: Atoms,
        cutting_point: np.ndarray,
        cutting_normal: int | np.ndarray,
        cell: np.ndarray,
    ) -> Atoms | None:
        """Creates a child from two parents using the given cut.

        Returns None if the generated structure does not contain
        a large enough fraction of each parent (see self.minfrac).

        Does not check whether atoms are too close.

        Parameters:

        cutting_normal: int or (1x3) array

        cutting_point: (1x3) array
            In fractional coordinates

        cell: (3x3) array
            The unit cell for the child structure
        """

        # Generate list of all atoms / atom groups:
        p1: list[Positions] = []
        p2: list[Positions] = []
        sym: list[str] = []
        for ii, (a, p) in enumerate(zip([a1, a2], [p1, p2])):
            tags = a.get_tags() if self.use_tags else np.arange(len(a))
            symbols = a.get_chemical_symbols()
            for i in np.unique(tags):
                indices = np.where(tags == i)[0]
                s = "".join([symbols[j] for j in indices])
                sym.append(s)

                c = a.get_cell()
                cop = np.mean(a.positions[indices], axis=0)
                cut_p = np.dot(cutting_point, c)
                if isinstance(cutting_normal, int):
                    vecs = [c[j] for j in range(3) if j != cutting_normal]
                    cut_n = np.cross(vecs[0], vecs[1])
                else:
                    cut_n = np.dot(cutting_normal, c)
                d = np.dot(cop - cut_p, cut_n)
                spos = a.get_scaled_positions()[indices]
                scop = np.mean(spos, axis=0)
                p.append(Positions(spos, scop, s, d, ii))

        all_points = p1 + p2
        unique_sym = np.unique(sym)

        # Sort these by chemical symbols:
        all_points.sort(key=lambda x: x.symbols, reverse=True)

        # For each atom type make the pairing
        unique_sym.sort()
        use_total = dict()
        for s in unique_sym:
            used = []
            not_used = []
            # The list is looked trough in
            # reverse order so atoms can be removed
            # from the list along the way.
            for i in reversed(range(len(all_points))):
                # If there are no more atoms of this type
                if all_points[i].symbols != s:
                    break
                # Check if the atom should be included
                if all_points[i].to_use():
                    used.append(all_points.pop(i))
                else:
                    not_used.append(all_points.pop(i))

            use_total[s] = used

        # check if the generated structure contains
        # atoms from both parents:
        count1, count2 = 0, 0
        for x in use_total.values():
            count1 += sum([y.origin == 0 for y in x])
            count2 += sum([y.origin == 1 for y in x])

        used_points = [pp for ss in use_total.keys() for pp in use_total[ss]]
        N = len(used_points)
        if N == 0:
            return None

        nmin = 1 if self.minfrac is None else int(round(self.minfrac * N))
        if count1 < nmin or count2 < nmin:
            return None

        # Construct the cartesian positions and reorder the atoms
        # to follow the original order
        newpos = []
        symbols = []
        pbc = a1.get_pbc()
        for p in used_points:
            c = a1.get_cell() if p.origin == 0 else a2.get_cell()  # type: ignore
            pos = np.dot(p.scaled_positions, c)  # type: ignore
            cop = np.dot(p.cop, c)  # type: ignore
            vectors, lengths = find_mic(pos - cop, c, pbc)
            newcop = np.dot(p.cop, cell)  # type: ignore
            pos = newcop + vectors
            symbols.append(p.symbols)  # type: ignore
            for row in pos:
                newpos.append(row)

        _newpos = np.reshape(newpos, (N, 3))
        child = Atoms(symbols=symbols, positions=_newpos, pbc=pbc, cell=cell)
        child.wrap()
        return child
