import pycharmm
from pycharmm import write as pcm_write
from pycharmm import NonBondedScript
from pycharmm import crystal, image

from crimm.Adaptors.pyCHARMMAdaptors import (
    load_chain, load_topology, load_water, load_ions, load_ligands,
    create_water_hs_from_charmm, fetch_coords_from_charmm, sd_minimize,
    patch_disu_from_model
)

from crimm import fetch_rcsb
from crimm.Modeller.Solvator import Solvator
from crimm.Modeller.LoopBuilder import ChainLoopBuilder

from crimm.Modeller.CoordManipulator import CoordManipulator
from crimm.Modeller import TopologyGenerator
from crimm.Adaptors.PropKaAdaptors import PropKaProtonator


CGENFF_PATH = "/export/app/cgenff/silcsbio.2024.1/cgenff/cgenff"
PDBIDS = ['2HZI', '5IGV', '1BG8', '3Q4K', '4PTI', '5IEV']
PDBID = '5IEV'
model = fetch_rcsb(
    PDBID,
    include_solvent=True,
    use_bio_assembly=True,
    organize=True
)

## Place the model center to (0, 0, 0) and place the principle axis along x-axis
coord_man = CoordManipulator()
coord_man.load_entity(model)
coord_man.orient_coords()

# build missing loops if exist
for chain in model.protein:
    if not chain.is_continuous():
        # chain can be built in place now by specifying `inplace = True`
        looper = ChainLoopBuilder(chain, inplace = True)
        # missing terminals will also be built if `include_terminal = True`
        looper.build_from_alphafold(include_terminal = False)

topo = TopologyGenerator(CGENFF_PATH)
topo.generate_model(model, coerce=True)

protonator = PropKaProtonator(topo, pH = 7.4)
protonator.load_model(model)
protonator.apply_patches()

load_topology(model.topology_loader)
for chain in model.protein:
    load_chain(chain)

# we need to patch disulfide bonds in CHARMM
# the disu info is stored in model under model.connect_dict
patch_disu_from_model(model)

load_ligands(model.ligand+model.phos_ligand+model.co_solvent)

## Minimize the protein and ligand first
# Specify nonbonded python object called my_nbonds - this just sets it up
# equivalant CHARMM scripting command: 
# nbonds cutnb 18 ctonnb 13 ctofnb 17 cdie eps 1 atom vatom fswitch vfswitch
non_bonded_script = NonBondedScript(
    cutnb=18.0, ctonnb=13.0, ctofnb=17.0,
    eps=1.0,
    cdie=True,
    atom=True, vatom=True,
    fswitch=True, vfswitch=True
)
# select the C-alpha atoms for harmonic restraints
cons_harm_atoms = pycharmm.SelectAtoms(atom_type='CA')
ener_dict = sd_minimize(
    300, non_bonded_script, cons_harm_selection=cons_harm_atoms
)

## Update the coordinates of the model from CHARMM
fetch_coords_from_charmm(
    model.protein+model.ligand+model.co_solvent+model.phos_ligand
)

solvator = Solvator(model)
solvator.solvate(
    cutoff=8.0, solvcut=2.1, remove_existing_water=False, orient_coords=False
)
solvator.add_balancing_ions()

load_water(model.solvent)
load_ions(model.ion)
create_water_hs_from_charmm(model)

## Setup PBC and Minimize Water
# organize segids and ion types for image and cons_fix
non_solvent_segids = set()
all_ion_types = set()
for chain in model:
    if chain.chain_type == 'Solvent':
        continue
    elif chain.chain_type == 'Ion':
        for res in chain:
            all_ion_types.add(res.resname)
    else:
        for res in chain:
            non_solvent_segids.add(res.segid)

# CHARMM scripting: crystal define cubic @boxsize @boxsize @boxsize 90 90 90
crystal.define_cubic(solvator.box_dim)
# CHARMM scripting: crystal build cutoff @boxhalf noper 0
crystal.build(solvator.box_dim/2)

# Turn on image centering - bysegment for protein, by residue for solvent and ions
# CHARMM scripting: image byseg xcen 0 ycen 0 zcen 0 select segid SEGID end
for segid in non_solvent_segids:
    image.setup_segment(0.0, 0.0, 0.0, segid)
# CHARMM scripting: image byres xcen 0 ycen 0 zcen 0 select resname tip3 end
image.setup_residue(0.0, 0.0, 0.0, 'TIP3')
# CHARMM scripting: image byres xcen 0 ycen 0 zcen 0 select resname ion_type end
for ion_type in all_ion_types:
    image.setup_residue(0.0, 0.0, 0.0, ion_type)

# Now specify nonbonded cutoffs for solvated box
cutnb = min(solvator.box_dim/2, 12)
cutim = cutnb
ctofnb = cutnb - 1.0
ctonnb = cutnb - 3.0

# Another nbonds example
# CHARMM scripting: nbonds cutnb @cutnb cutim @cutim ctofnb @ctofnb ctonnb @ctonnb -
#        inbfrq -1 imgfrq -1
non_bonded_script = pycharmm.NonBondedScript(
    cutnb=cutnb, cutim=cutim, ctonnb=ctonnb, ctofnb=ctofnb,
    eps=1.0,
    cdie=True,
    atom=True, vatom=True,
    fswitch=True, vfswitch=True,
    inbfrq=-1, imgfrq=-1
)

# We want to fix the protein and ligands and minimize the solvent to "fit"
# Select everything but solvent and ions
cons_fix_atoms = pycharmm.SelectAtoms()
for segid in non_solvent_segids:
    cons_fix_atoms |= pycharmm.SelectAtoms(seg_id=segid)

# Minimize the solvent positions with periodic boundary conditions using steepest descents
ener_dict = sd_minimize(200, non_bonded_script, cons_fix_selection=cons_fix_atoms)

fetch_coords_from_charmm(model)
pcm_write.coor_card(f'{PDBID}.crd')
pcm_write.psf_card(f'{PDBID}.psf')
