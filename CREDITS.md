# Credits and asset licenses

The code and the models we built ourselves (campus gate, Students' Union, road obstacles,
rocket package) are MIT, see `LICENSE`.

| Asset | Source | License |
|---|---|---|
| three.js (`game/vendor/`) | https://threejs.org | MIT |
| Characters (`game/assets/person.glb`, derived from Universal Base Characters + Universal Animation Library) | Quaternius, itch.io | CC0 (check the pack page before re-distributing) |
| PBR textures and trees/flowers used in Blender files | Poly Haven | CC0 |
| Car kit used for early blockouts | Kenney Car Kit | CC0 |

## Not included

- **Tesla Roadster car model.** The model used in development came from a public GitHub repo
  with no license, so it is **not** in this repository. The game runs with a plain placeholder
  car. To use your own car, put `car_chassis.glb` and `car_wheel.glb` in `game/assets/`.
  (Those files are git-ignored.)
- **Large downloaded packs** (`blender/game-assets/downloads/`) are git-ignored. Re-download from
  the sources above.

"Tesla" and "Roadster" are trademarks of their owners. This is a fan project and is not
affiliated with or endorsed by Tesla, SpaceX or Obafemi Awolowo University.
