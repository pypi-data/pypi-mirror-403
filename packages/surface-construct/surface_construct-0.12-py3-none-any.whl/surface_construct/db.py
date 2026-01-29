from random import randint

import ase.db
from ase.calculators.calculator import get_calculator_class
from ase.db.core import now
from ase.io.jsonio import write_json, read_json
import os
from ase.db.row import AtomsRow, row2dct
from surface_construct.utils.atoms import get_atoms_topo_id
from surface_construct.utils import calc_hull_vertices, get_calc_info

"""
重复使用数据的流程

* 计算所有已有表面的格点 vertex hull, 计算所有已有采样点的密度和平均距离。
    * 密度计算 vertex hull 体积 N_sample / V_hull.
    * 每个表面的 sg 返回hull 的顶点，保存起来，就可以作增量计算
    * https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.ConvexHull.html
    * 通过 Delaunay 三角划分计算采样密度分布，得到最稀疏分布区域
    * Delaunay triangulations can be used to determine the density or 
        intensity of points samplings by means of the Delaunay tessellation 
        field estimator (DTFE). [wiki]
* 新的表面 sg 采样前，得到不在 Hull0 中的格点集合，然后进行聚类采样。
    * 聚类的数目大于等于 V_hull1 * rho0
* 拟合新的sg前，找到同时在 Hull0 和 Hull1 中的旧采样点，与新的采样点一起进行拟合
    * 将旧的点，放到新的 sg 中，后续补充采样都基于这个
    
Functions:
- write to db
- read from db
- convert from old version (in future)
- Data types:
    - Structure for molecules and more; Calculators, including parameters, ase.db
    - SurfaceGrid, positions, vectors, properties
    - SurfaceSite, all info for sampling points
    - User

"""
# TODO: 使用关联表进行管理，自动本地对新增文件进行更新索引序号


class Base:
    __basedir__ = '.'
    __version__ = '0.1'  # this will write in the info to ensure the data compatibility

    def __init__(self, db_name=None, user=None):
        if 'extra_dir' not in self.__dict__:
            extra_dir = '.'
        else:
            extra_dir = self.extra_dir
        self.db_path = os.path.join(self.__basedir__, extra_dir, db_name)
        self.db_name = db_name
        self.user = user

        dirname = os.path.dirname(self.db_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    @classmethod
    def read(cls, db_name):
        with open(db_name, 'r') as fd:
            content = read_json(fd)
        obj = cls(db_name=db_name)
        obj.__dict__.update(content)
        return obj

    def todict(self):
        return dict()

    def write(self, db_path=None):
        if db_path is None:
            db_path = self.db_path
        if os.path.isfile(db_path):
            print("Warning: Old db file exists and will be overwrite: {}".format(db_path))
        with open(db_path, 'w') as fd:
            write_json(fd, self.todict())


class AtomsData(Base):

    __basedir__ = os.path.join(os.getenv('SURFSAMPDB') or '.', 'atomsd')

    def __init__(self, atomsrow=None, db_name=None, user=None):

        if type(atomsrow) in (ase.Atoms,):
            self.atoms = atomsrow
            self.atomsrow = AtomsRow(atomsrow)
        else:
            self.atomsrow = atomsrow
            self.atoms = atomsrow.toatoms()
            if self.atoms.calc is None:
                if hasattr(atomsrow, 'calculator'):
                    params = atomsrow.get('calculator_parameters', {})
                    self.atoms.calc = get_calculator_class(atomsrow.calculator)(**params)

        self.atomsrow.ctime = now()
        self.unique_id = self.atomsrow.unique_id
        if user is not None:
            if hasattr(atomsrow, 'user'):
                print("Warning: The user in atomsrow will be updated from {} to {}.".format(
                    atomsrow.user, user))
            self.atomsrow.user = user

        if db_name is None:
            self.extra_dir = "{}-{}".format(
                self.atoms.get_chemical_formula(),
                self.atomsrow.unique_id[:6])
            db_name = self.extra_dir + '.json'
        else:
            self.extra_dir = os.path.dirname(db_name)
            db_name = os.path.basename(db_name)

        super().__init__(db_name, user)

        db = ase.db.connect(self.db_path)
        self.db = db

        self._calc_info = {}  # calculator information, [计算软件，泛函， Cutoff]
        if self.atoms.calc is not None:
            self.calc_info = self.atoms.calc

    def _remove_duplicate(self, unique_id=None):
        if unique_id is None:
            unique_id = self.unique_id
        all_items = [row.id for row in self.db.select(unique_id=unique_id)]
        print("Remove duplicated AtomsData in database, keep last one.")
        self.db.delete(all_items[:-1])

    def todict(self):
        return row2dct(self.atomsrow)

    def write(self, db_path=None):
        if db_path is not None:
            self.db = ase.db.connect(db_path)
        n = self.db.count(unique_id=self.unique_id)
        if n == 0:
            _ = self.db.write(self.atomsrow)
        elif n == 1:
            print("AtomsData exists. Do nothing.")
        else:
            print("Warning: More than one AtomsData in database!")
            self._remove_duplicate()

    @property
    def calc_info(self):
        return self._calc_info

    @calc_info.setter
    def calc_info(self, calc=None):
        if calc is None:
            self._calc_info = {}
        self._calc_info = get_calc_info(calc)

    @classmethod
    def read(cls, db_name):
        db = ase.db.connect(db_name)
        n = db.count()
        if n > 1:
            raise Warning("More than one atoms in this JsonDB! Last one will be return!")
        atomsrow = db.get(n)
        return AtomsData(atomsrow=atomsrow, db_name=db_name)


class GridData(Base):
    __basedir__ = os.path.join(os.getenv('SURFSAMPDB') or '.', 'gridd')

    def __init__(self, atomsdata=None, sg=None,
                 db_name=None, user=None, **kwargs):
        """
        :param sg:
        :param db_name:
        :param db:
        :param kwargs: for reconstruction of sg
        """
        if db_name is None:
            if atomsdata is not None:
                db_name = "sg-{}".format(atomsdata.db_name)
                self.extra_dir = atomsdata.db_name.rstrip('.json')
        super().__init__(db_name, user)
        self.sg_kwargs = kwargs

        self.unique_id = None
        if atomsdata is not None:
            self.unique_id = atomsdata.unique_id

        self.atomsdata = atomsdata  # AtomData.db_name
        self.points = None
        self.vectors = None  # raw vectors
        self.vlen = None
        self.hull_vertices = None  # hull 最外围点的 index
        self.grid_property = {}
        self.grid_property_sigma = {}
        self.grid_nx = None
        self.grid_ny = None
        self.species = None

        self.calc_info = {}
        if self.atomsdata is not None:
            self.calc_info = atomsdata.calc_info

        if sg is not None:
            self.read_sg(sg)

    def read_sg(self, sg, energy_type='optimization', ref_energy=0.0):
        if self.atomsdata is None:
            atomsdata = AtomsData(sg.atoms)
            print("Save sg.atoms to AtomsData {}".format(
                atomsdata.db_path
            ))
            self.atomsdata = atomsdata
        self.species = sg.species
        self.points = sg.points
        if hasattr(sg, '_raw_vector'):
            self.vectors = sg._raw_vector
        else:
            self.vectors = sg.vector
        self.vlen = sg.vlen
        if hasattr(sg, 'grid_property'):
            self.grid_property = sg.grid_property
            self.grid_property['energy'] = {'type': energy_type,
                                            'ref_value': ref_energy,
                                            'value': self.grid_property['energy']
                                            }
            self.grid_property_sigma = sg.grid_property_sigma
        else:
            if hasattr(sg, 'energy'):
                self.grid_property = {'energy': {'type': energy_type,
                                                 'ref_value': ref_energy,
                                                 'value': sg.energy,
                                                 }
                                      }
                self.grid_property_sigma = {'energy': sg.energy_sigma}
        self.grid_nx = sg.grid_nx
        self.grid_ny = sg.grid_ny
        if hasattr(sg, 'hull_vertices'):
            self.hull_vertices = sg.hull_vertices
        else:
            self.hull_vertices = calc_hull_vertices(sg.vector)
        # sg_kwargs
        for k in ['interval', 'radii', 'rads', 'lpca']:
            if hasattr(sg, k):
                self.sg_kwargs[k] = getattr(sg, k)

        self.calc_info = self.atomsdata.calc_info

    def todict(self):
        content = {
            'unique_id': self.unique_id,
            'calc_info': self.calc_info,
            'atomsdata': self.atomsdata.db_path,
            'points': self.points,
            'vectors': self.vectors,
            'species': self.species,
            'vlen': self.vlen,
            'hull_vertices': self.hull_vertices,
            'grid_property': self.grid_property,
            'grid_property_sigma': self.grid_property_sigma,
            'grid_nx': self.grid_nx,
            'grid_ny': self.grid_ny,
            'sg_kwargs': self.sg_kwargs,
            'version': self.__version__,
        }

        if not os.path.isfile(self.atomsdata.db_path):
            self.atomsdata.write()

        return content


class SampleData(Base):
    __basedir__ = os.path.join(os.getenv('SURFSAMPDB') or '.', 'sampd')
    __check_identifier__ = {
        'equal': ["version", "guest_mol", "calc_info", "sg_kwargs.method"]
    }

    def __init__(self, point=None, vector=None, properties=None, griddata=None, sg_species=None,
                 grid_idx=None, db_name=None, user=None, **kwargs):

        self.unique_id = '{:x}'.format(randint(16**31, 16**32 - 1))
        self.extra_dir = '.'
        if db_name is None:
            db_name = "sampd-{}-{}-{}.json".format(griddata.db_name.split('-')[1],
                                                   griddata.db_name.split('-')[2].split('.')[0],
                                                   self.unique_id[:6])
            self.extra_dir = griddata.atomsdata.db_name.rstrip('.json')
        super().__init__(db_name, user)

        properties_default = {
            'energy': None,
        }  # x,y,z,theta,phi,(1,2,3,4),energy:{type,ref_atoms,ref_value,value}

        if properties is not None:
            properties_default.update(properties)
        properties = properties_default.copy()

        sg_kwargs = kwargs

        if point is None or vector is None:
            if grid_idx is not None and griddata is not None:
                point = griddata.points[grid_idx]
                vector = griddata.vectors[grid_idx]

        atomsdata = None
        if griddata is not None:
            atomsdata = griddata.atomsdata
            sg_kwargs.update(griddata.sg_kwargs)

        if sg_species is None:
            if griddata is not None:
                sg_species = griddata.species

        self.sg_species = sg_species  # VIP, surface elements, make the data reused among different system
        self._guest_mol = None  # VIP, guest molecule identity, make the data reused among different system
        self.griddata = griddata
        self.atomsdata = atomsdata
        self.grid_idx = grid_idx
        self.point = point
        self.vector = vector
        self.properties = properties
        self.sg_kwargs = sg_kwargs
        self.sg_kwargs['method'] = 'MLAT'

        self._opt_atoms = None  # optimized, atomsdata

        self.calc_info = {}
        if self.atomsdata is not None:
            self.calc_info = atomsdata.calc_info

    @property
    def opt_atoms(self):
        return self._opt_atoms

    @opt_atoms.setter
    def opt_atoms(self, atoms):
        if type(atoms) in (ase.Atoms,):
            atomsrow = AtomsRow(atoms)
            db_name = os.path.join(self.extra_dir,
                                   "{}-{}.json".format(atoms.get_chemical_formula(),
                                                       atomsrow.get('unique_id')[:6]))
            atomsdata = AtomsData(atoms, db_name=db_name)
            atomsdata.write()
        elif type(atoms) in (AtomsData,):
            atomsdata = atoms
        elif type(atoms) in (str,):
            try:
                atomsdata = AtomsData.read(atoms)
            except FileNotFoundError:
                raise FileNotFoundError
        else:
            raise TypeError
        self._opt_atoms = atomsdata
        self.calc_info = atomsdata.calc_info

    def todict(self):
        content = {
            'unique_id': self.unique_id,
            'calc_info': self.calc_info,
            'griddata': None,
            'atomsdata': None,
            'grid_idx': self.grid_idx,
            'point': self.point,
            'vector': self.vector,
            'properties': self.properties,
            'sg_species': self.sg_species,
            'guest_mol': self.guest_mol,
            'sg_kwargs': self.sg_kwargs,
            'version': self.__version__,
        }

        if self.atomsdata is not None:
            content['atomsdata'] = self.atomsdata.db_path
        if self.griddata is not None:
            content['griddata'] = self.griddata.db_path
            content['vlen'] = self.griddata.vlen

        if self.opt_atoms is not None:
            content['opt_atoms'] = self.opt_atoms.db_path

        return content

    @property
    def guest_mol(self):
        return self._guest_mol

    @guest_mol.setter
    def guest_mol(self, atoms, *args, **kwargs):
        self._guest_mol = get_atoms_topo_id(atoms, *args, **kwargs)

