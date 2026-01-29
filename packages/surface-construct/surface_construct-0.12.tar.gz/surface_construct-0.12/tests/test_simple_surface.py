import pytest
import ase.build
from surface_construct.structures.surface import Surface, Crystal, Slab

class TestSimpleSurface:
    def test_Cu111_termination(self):
        bulk = ase.build.bulk('Cu')
        c = Crystal(bulk)
        s = Surface(c, (1,1,1))

        slab1 = Slab(s)
        superslab1 = slab1.supercell((3,3))
        terms = superslab1.get_all_terminations(unique=True)
        atoms_list = [t.atoms for t in terms.values]

        slab2 = Slab(s, from_last=True)
        superslab2 = slab2.supercell((3,3))
        terms_last = superslab2.get_all_terminations(unique=True)
        assert len(terms) == len(terms_last) == 23
        assert set(terms) == set(terms_last)

    def test_Cu211_termination(self):
        bulk = ase.build.bulk('Cu')
        c = Crystal(bulk)
        s = Surface(c, (2,1,1))

        slab1 = Slab(s, layers=6)
        slab1.set_layers(3)
        superslab1 = slab1.supercell((2,3))
        terms = superslab1.get_all_terminations(unique=True)

        slab2 = Slab(s, from_last=True, layers=6)
        slab2.set_layers(3)
        superslab2 = slab2.supercell((2,3))
        terms_last = superslab2.get_all_terminations(unique=True)
        assert len(terms) == len(terms_last)
        assert set(terms) == set(terms_last)


