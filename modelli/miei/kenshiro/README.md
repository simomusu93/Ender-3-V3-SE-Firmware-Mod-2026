# Kenshiro (Fist of the North Star) – figurine

Personal use only (copyrighted character). The reference images are not included in this repository.

## References (local only)
- `riferimenti/foglio_viste.webp` – turnaround sheet (standing pose)
- `riferimenti/posa_combattimento.webp` – fighting pose (front view only)
- `riferimenti/viste/` – cropped views, 1024×1024 on white, ready for 3D generators:
  `01_fronte` (front), `02_tre-quarti-fronte` (front three-quarter), `03_profilo-sinistro` (left), `04_retro` (back),
  `05_profilo-destro` (right), `06_tre-quarti-retro` (back three-quarter)

## Generating the model (multi-view)
Tripo3D or Meshy, "Multiview / multiple images" mode:
- Front → `01_fronte.png`
- Back → `04_retro.png`
- Left / Right → `03_profilo-sinistro.png` and `05_profilo-destro.png`
  (if the result comes out twisted or with the arms wrong, swap the two profiles and try again)

Download as STL, OBJ or GLB and put it in `generato/`.

## Afterwards
Mesh repair, scaling (target height), base, hollowing, cutting into pieces if needed.
