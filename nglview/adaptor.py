from __future__ import print_function, absolute_import

import os
import os.path
import uuid
import tempfile

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from .base_adaptor import Structure, Trajectory
from .utils.py_utils import FileManager

__all__ = [
    'FileStructure',
    'TextStructure',
    'RdkitStructure',
    'PdbIdStructure',
    'SimpletrajTrajectory',
    'MDTrajTrajectory',
    'PyTrajTrajectory',
    'ParmEdTrajectory',
    'MDAnalysisTrajectory',
    'register_backend',
    'BACKENDS']

BACKENDS = dict()

class register_backend(object):
    def __init__(self, package_name):
        self.package_name = package_name

    def __call__(self, cls):
        BACKENDS[self.package_name] = cls
        return cls

class FileStructure(Structure):

    def __init__(self, path):
        super(FileStructure, self).__init__()
        self.fm = FileManager(path)
        self.ext = self.fm.ext
        self.params = {}
        self.path = path
        if not self.fm.is_filename:
            raise IOError("Not a file: " + path)

    def get_structure_string(self):
        return self.fm.read(force_buffer=True)


class TextStructure(Structure):

    def __init__(self, text, ext='pdb', params={}):
        super(TextStructure, self).__init__()
        self.path = ''
        self.ext = ext
        self.params = params
        self._text = text

    def get_structure_string(self):
        return self._text


class RdkitStructure(Structure):

    def __init__(self, rdkit_mol, ext="pdb"):
        super(RdkitStructure, self).__init__()
        self.path = ''
        self.ext = ext
        self.params = {}
        self._rdkit_mol = rdkit_mol

    def get_structure_string(self):
        from rdkit import Chem
        fh = StringIO(Chem.MolToPDBBlock(self._rdkit_mol))
        return fh.read()


class PdbIdStructure(Structure):

    def __init__(self, pdbid):
        super(PdbIdStructure, self).__init__()
        self.pdbid = pdbid
        self.ext = "cif"
        self.params = {}

    def get_structure_string(self):
        url = "http://www.rcsb.org/pdb/files/" + self.pdbid + ".cif"
        return urlopen(url).read()


@register_backend('simpletraj')
class SimpletrajTrajectory(Trajectory, Structure):
    '''simpletraj adaptor.

    Examples
    --------
    >>> import nglview as nv
    >>> t = nv.SimpletrajTrajectory(nv.datafiles.XTC, nv.datafiles.GRO)
    >>> w = nv.NGLWidget(t)
    >>> w
    '''

    def __init__(self, path, structure_path):
        try:
            import simpletraj
        except ImportError as e:
            raise ImportError(
                "'SimpletrajTrajectory' requires the 'simpletraj' package"
            )
        self.traj_cache = simpletraj.trajectory.TrajectoryCache()
        self.path = path
        self._structure_path = structure_path
        self.ext = os.path.splitext(structure_path)[1][1:]
        self.params = {}
        self.trajectory = None
        self.id = str(uuid.uuid4())
        try:
            self.traj_cache.get(os.path.abspath(self.path))
        except Exception as e:
            raise e

    def get_coordinates(self, index):
        traj = self.traj_cache.get(os.path.abspath(self.path))
        frame = traj.get_frame(index)
        return frame["coords"]

    def get_structure_string(self):
        return open(self._structure_path).read()

    @property
    def n_frames(self):
        traj = self.traj_cache.get(os.path.abspath(self.path))
        return traj.numframes


@register_backend('mdtraj')
class MDTrajTrajectory(Trajectory, Structure):
    '''mdtraj adaptor.

    Example
    -------
    >>> import nglview as nv
    >>> import mdtraj as md
    >>> traj = md.load(nv.datafiles.XTC, nv.datafiles.GRO)
    >>> t = MDTrajTrajectory(traj)
    >>> w = nv.NGLWidget(t)
    >>> w
    '''

    def __init__(self, trajectory):
        self.trajectory = trajectory
        self.ext = "pdb"
        self.params = {}
        self.id = str(uuid.uuid4())

    def get_coordinates(self, index):
        return 10 * self.trajectory.xyz[index]

    @property
    def n_frames(self):
        return self.trajectory.n_frames

    def get_structure_string(self):
        fd, fname = tempfile.mkstemp()
        self.trajectory[0].save_pdb(fname)
        pdb_string = os.fdopen(fd).read()
        # os.close( fd )
        return pdb_string


@register_backend('pytraj')
class PyTrajTrajectory(Trajectory, Structure):
    '''PyTraj adaptor.

    Example
    -------
    >>> import nglview as nv
    >>> import pytraj as pt
    >>> traj = pt.load(nv.datafiles.TRR, nv.datafiles.PDB)
    >>> t = nv.PyTrajTrajectory(traj)
    >>> w = nv.NGLWidget(t)
    >>> w
    '''

    def __init__(self, trajectory):
        self.trajectory = trajectory
        self.ext = "pdb"
        self.params = {}
        self.id = str(uuid.uuid4())

    def get_coordinates(self, index):
        return self.trajectory[index].xyz

    @property
    def n_frames(self):
        return self.trajectory.n_frames

    def get_structure_string(self):
        fd, fname = tempfile.mkstemp(suffix=".pdb")
        self.trajectory[:1].save(fname, format="pdb", overwrite=True)
        pdb_string = os.fdopen(fd).read()
        # os.close( fd )
        return pdb_string


@register_backend('parmed')
class ParmEdTrajectory(Trajectory, Structure):
    '''ParmEd adaptor.
    '''

    def __init__(self, trajectory):
        self.trajectory = trajectory
        self.ext = "pdb"
        self.params = {}
        # only call get_coordinates once
        self._xyz = trajectory.get_coordinates()
        self.id = str(uuid.uuid4())
        self.only_save_1st_model = True

    def get_coordinates(self, index):
        return self._xyz[index]

    @property
    def n_frames(self):
        return len(self._xyz)

    def get_structure_string(self):
        fd, fname = tempfile.mkstemp(suffix=".pdb")
        # only write 1st model
        if self.only_save_1st_model:
            self.trajectory.save(
                fname, overwrite=True,
                coordinates=self.trajectory.coordinates)
        else:
            self.trajectory.save(fname, overwrite=True)
        pdb_string = os.fdopen(fd).read()
        # os.close( fd )
        return pdb_string


@register_backend('MDAnalysis')
class MDAnalysisTrajectory(Trajectory, Structure):
    '''MDAnalysis adaptor.

    Can take either a Universe or AtomGroup.

    Example
    -------
    >>> import nglview as nv
    >>> import MDAnalysis as mda
    >>> u = mda.Universe(nv.datafiles.GRO, nv.datafiles.XTC)
    >>> prot = u.select_atoms('protein')
    >>> t = nv.MDAnalysisTrajectory(prot)
    >>> w = nv.NGLWidget(t)
    >>> w
    '''

    def __init__(self, atomgroup):
        self.atomgroup = atomgroup
        self.ext = "pdb"
        self.params = {}
        self.id = str(uuid.uuid4())

    def get_coordinates(self, index):
        self.atomgroup.universe.trajectory[index]
        xyz = self.atomgroup.atoms.positions
        return xyz

    @property
    def n_frames(self):
        return self.atomgroup.universe.trajectory.n_frames

    def get_structure_string(self):
        try:
            import MDAnalysis as mda
        except ImportError:
            raise ImportError(
                "'MDAnalysisTrajectory' requires the 'MDAnalysis' package"
            )
        u = self.atomgroup.universe
        u.trajectory[0]
        f = mda.lib.util.NamedStream(StringIO(), 'tmp.pdb')
        atoms = self.atomgroup.atoms
        # add PDB output to the named stream
        with mda.Writer(f, atoms.n_atoms, multiframe=False) as W:
            W.write(atoms)
        # extract from the stream
        pdb_string = f.read()
        return pdb_string
