# Photogrammetry Notebook Starter

A notebook-first scaffold for learning how to go from multi-angle photos to a 3D mesh and STL.

## Suggested workflow
1. Work through the notebooks in order.
2. Keep experiments and plots inside notebooks.
3. Move reusable logic into `src/`.
4. Save intermediate artifacts so later notebooks can load them directly.

## Suggested directories
- `notebooks/` — stage-by-stage development
- `data/` — raw and processed inputs
- `outputs/` — saved artifacts like calibration files, clouds, meshes
- `src/` — reusable Python modules once notebook code stabilizes

## Good early milestones
- Two-view sparse reconstruction
- Multi-view sparse reconstruction
- Dense cloud
- Clean mesh
- STL export
