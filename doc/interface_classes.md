Structures
----------

The above convenience functions first create an `adaptor` that implements an [interface](interface_classes) for communication with the IPython/Jupyter widget.

```Python
import nglview
struc = nglview.PdbIdStructure("3pqr")  # load file from RCSB PDB
view = nglview.NGLWidget(struc)            # create widget
view                                       # display widget
```


Trajectories
------------

To enable trajectory access pass a second `Trajectory` argument to the widget
constructor or supply a combined `Structure`/`Trajectory` object as the first
argument.

Seperate `Structure` and `Trajectory` objects using `FileStructure` and
`SimpletrajStructure` (requires the [`simpletraj`](https://github.com/arose/simpletraj)
package):

```Python
import nglview
struc = nglview.FileStructure(nglview.datafiles.GRO)
traj = nglview.SimpletrajStructure(nglview.datafiles.XTC)
nglview.NGLWidget(struc, traj)
```

Combined `Structure`/`Trajectory` object utilizing `MDTrajTrajectory` which
wraps a trajectory loaded with [MDTraj](http://mdtraj.org/):

```Python
import nglview
import mdtraj
traj = mdtraj.load(nglview.datafiles.XTC, top=nglview.datafiles.GRO)
strucTraj = nglview.MDTrajTrajectory(traj)
nglview.NGLWidget(strucTraj)
```

The displayed frame can be changed by setting the `frame` property of the
widget instance `w`:

```Python
view.frame = 100  # set to frame no 100
```


Interface classes
=================

You can create your own adaptors simply by following the interfaces for `Structure` and `Trajectory`, which can also be combined into a single class.


Structure
---------

```Python
class MyStructure(nglview.Structure):
    ext = "pdb"  # or gro, cif, mol2, sdf
    params = {}  # loading options passed to NGL
    def get_structure_string(self):
        return "structure in the self.ext format"
```


Trajectory
----------

```Python
class MyTrajectory(nglview.Trajectory):
    def get_coordinates(self, index):
        # return 2D numpy array, shape=(n_atoms, 3)

    def get_coordinates_dict(self):
        # return a dict of encoded 2D numpy array

    @property
    def n_frames(self):
        return 2  # return number of frames
```


Combined
--------

```Python
class MyStructureTrajectory(nglview.Structure, nglview.Trajectory):
    ext = "pdb"  # or gro, cif, mol2, sdf
    params = {}  # loading options passed to NGL

    def get_structure_string(self):
        return "structure in the self.ext format"

    def get_coordinates(self, index):
        # return 2D numpy array, shape=(n_atoms, 3)

    def get_coordinates_dict(self):
