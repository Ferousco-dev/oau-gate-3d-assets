ASSET      AR_OAUGate  (Obafemi Awolowo University main gate, Ile-Ife)
CATEGORY   architecture, hero building / landmark (one unique piece, not a repeating kit)

VIEWS
  ref/front_photo.jpg   544x564 phone photo, near-frontal. Perspective, NOT orthographic.
                        azimuth 0, elevation ~3 deg (eye level), lens ~28 mm. Subject (crest top to
                        road) fills 0.79 of image height; ground line at y=458 of 564 (0.19 from bottom).
                        Used for: silhouette and proportions of the centre bay, pillars, crest, fascia.
                        Cleaned matte: ref/front_matte.png (hand polygon, passages cut out, cables drawn).
  ref/threequarter_photo.jpg 738x384, near-frontal wide shot, slightly left of axis, lens ~24 mm, hedges hide the ground.
                        Used for: arc plan (the drum curves AWAY from the viewer), wing length, foreground hedges
                        and solar street lamps. Not used for proportions.
  ref/distant_small.jpg 182x173 low resolution, front view. Confirms the layout only.

SCALE      1 unit = 1 m. Evidence: sedan parked behind the arch in front_photo (height ~1.45 m, ~49 px) gives
           >= 34 px/m at that depth, so the gate front plane is taken as 36 px/m. Pillars 415 px -> 11.5 m.
           Gate passage width 135 px -> 3.75 m. Used value 36 px/m. If a real dimension is known (pillar height,
           road width) tell me and every constant rescales.

PROPORTIONS (front_photo, px at 36 px/m, centre of gate at x=268)
  1  pillar height above road             415 px  = 11.5 m
  2  crest top above road                 448 px  = 12.4 m, crest diameter 70 px = 1.9 m, centre z = 11.6 m
  3  pillar centres                       x = 224 and 313 -> +-1.25 m, pillar width 32 px = 0.9 m, depth ~0.8 m
  4  crossbar                             y 68-82 -> z 10.4 to 10.8 m
  5  fascia top above road (centre)       245 px = 6.8 m
  6  cream fascia band                    215-255 px = 1.1 m, darker band below it 0.3 m
  7  gray seal block                      x 200-335 (3.75 m) y 265-355 -> z 2.9 to 5.4 m
  8  seal disc                            diameter 60 px = 1.7 m, centre z = 3.55 m
  9  arch window                          width 1.4 m, z 4.7 to 5.9 m (round top)
  10 lower glass panels                   x 240-295, y 360-420 -> z 1.1 to 2.8 m
  11 arc chord (photo 2)                  about 24 m end to end, drum radius ~13 m, half-angle ~68 deg
  12 big cream piers beside the bay       about 2.8 m wide, reach the roof, start ~3.1 m from the axis

PARTS (construction order)
  Roof slab + fascia + band       one curved ring each, separate objects
  Wing piers + back wall          static
  Side vehicle gates              separate objects, pivot at hinge line (gold lattice), static for now
  Two dark pillars + crossbar     separate static objects
  Crest                           separate disc object
  Seal block, seal disc, arch window, lower glass  separate objects (seal and glass shade differently)
  Stay cables                     10 thin tubes pillar tops -> fascia
  Props (optional)                hedges, topiary, solar lamp poles (separate file)

SILHOUETTE  1 two tall slab pillars joined by a thin crossbar with the round crest above
            2 stay cables fanning to the curved low drum
            3 wide curved cream fascia with darker underband
            4 central gray block with seal over an open driving passage
            5 big cream piers framing the passage

MATERIALS   cream plaster (rough 0.85), dark charcoal painted concrete pillars (0.6), gray block, gold painted
            steel gates (metal 0.8, rough 0.4), blue glass, seal printed texture, steel cables, asphalt (preview only)

ARTICULATION none for the first delivery (static architecture). Sockets: SOCKET_banner_L/R for flags
            (inferred). Side gates get hinge pivots so they can open later.

INFERRED    the rear of the drum (inside curve, back wall, roof top) is not visible in any photo;
            wing length and the inner radius come from photo 2; pillar depth; crest thickness and design
            (generic ring + disc, the real crest is a carved shield); cable attachment points;
            the guard building behind the passage; all dimensions rely on the single car height cue.

TARGET      engine: not stated (Unity assumed from the question), format GLB + FBX, tier hero building
            (20 to 80k tris; this is a stylised low-poly pass, about 5k), game camera three-quarter overhead
            50 deg elevation, 50 mm lens, distance 40 m, subject height at gameplay ~ 128 px.
