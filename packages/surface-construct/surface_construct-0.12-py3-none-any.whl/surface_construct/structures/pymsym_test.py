import pymsym
import ase
from ase.build import molecule

def get_symmetry(atoms: ase.Atoms) -> str:
    msym_elements = list()
    for i in atoms:
        msym_elements.append(pymsym.Element(name=i.symbol, coordinates=i.position.tolist()))

    msym_basis_functions = list()
    for element in msym_elements:
        bfs = [pymsym.RealSphericalHarmonic(element=element, n=2, l=1, m=m, name=f"p{m+1}") for m in (-1, 0, 1)]
        element.basis_functions = bfs
        msym_basis_functions += bfs

#    try:
    with pymsym.Context(elements=msym_elements, basis_functions=msym_basis_functions) as ctx:
        return ctx.find_symmetry()
#    except Exception as e:
#        print(e)
#        # diff versions throw libmsym.main.Error or libmsym.libmsym.Error, so I'll drop a blanket Exception
#        # incredibly, this is the desired behavior of libmsym!
#        return "C1"

mol = molecule("C6H6")

print(get_symmetry(mol))

print(pymsym.get_point_group(mol.numbers.tolist(), mol.positions.tolist()))
print(pymsym.get_symmetry_number(mol.numbers.tolist(), mol.positions.tolist()))