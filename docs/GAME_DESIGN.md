# OAU Run: working title

Drive the Tesla Roadster rocket car down the OAU road. Chased by the Yellow House (Mathematics) and the White House (Chemistry and Physics), who will not catch you unless you slow down. Reach the Student Union building: graduation, CGPA screen.

## Research notes (what OAU students actually face)
Sources found in search; use for obstacle flavour.
- Yellow House = Mathematics dept, White House = Chemistry and Physics (OAU slang, Zikoko list).
- E-portal failures: course registration, fees, results.
- Long ICT centre queues for registration and CBT exams.
- Water shortage in halls (Awolowo, ETF, Angola); students fetch water from streams.
- Light problems: dark restrooms and halls, voltage surges that kill appliances.
- Transport crisis: Gboro buses and okada.
- Hostel overcrowding and eviction orders; off-campus rent hikes.
- ID card rule ("No ID card, no exam").
- ASUU and staff strikes shut the campus.
- Handouts sold by lecturers; packed lecture halls.
- Minimum CGPA of 1.0 on a 5.0 scale for active studentship.

## Core rules
- Start CGPA 5.0 (first year). Every hit lowers it; pickups restore health.
- Chaser catches you: carryover. Restart from the last checkpoint (semester gate) with CGPA reset to the checkpoint value.
- Road is gently curved. Steering is required.
- Finish: Student Union building, graduation screen: final CGPA, pickups, obstacles hit, time.
- Easy mode by default: wide lane, forgiving hits.

## Obstacles
| Name | Behaviour | Source |
|---|---|---|
| Stone blocks, gravestones, rocks | solid, swerve | Kenney Graveyard and Nature kits |
| Barrels, cones, tire stacks, crates, jersey barriers, road blocks, speed bumps, broken car | solid or bump | PR_RoadObstacles (built) |
| Jump ramp and OAU gate | fly over | built |
| ICT man (tag-bearing man standing in road) | funny: brush him off, comic knock-back, small CGPA hit | build |
| Registration queue (row of students) | slow zone | build |
| Gboro bus (yellow) | moving, blocks lane | build |
| Okada rider | moving, crosses road | build |
| Handout stack | CGPA penalty | build |
| Portal error sign ("Server busy") | slow zone | build |
| Water bucket line | slippery | build |

## Pickups
Health boost (heart), CGPA boost (A+ star), Rocket fuel can, Water sachet.

## Chasers
Yellow ghost and white ghost: Kenney `character-ghost` recoloured, scaled up as houses with Yellow House / White House signboards.

## End and landmarks
Student Union building: to be modelled from the photo the user will send.

## Round 2: real-world distractions and scenery

Research notes: the web has little OAU-specific funny material, so these come from the user's brief plus general campus-life and runner-game design (shields, speed boost, flight/slow-mo power-ups; mixed obstacle types: static, patrol, projectile, special; difficulty ramps with time).

Landmarks to reference (OAU): Oduduwa Hall, the Amphitheatre, Hezekiah Oluwasanmi Library, halls of residence (Awolowo, Angola, Moremi, Mozambique, ETF, Fajuyi). Architecture: Arieh Sharon's modernist campus.

### Distractions (slow you or tempt you off the line)
| Name | Behaviour |
|---|---|
| Dancing girl | roadside; camera and car "look" away; if you stop to watch you lose a second (distraction meter) |
| Party speaker (DJ stack) | blasts, screen shake, steering wobble zone |
| Hawker with tray of pure water | walks across road; hitting her costs CGPA, grabbing a sachet restores water |
| Lecturer with handouts | steps out; "buy handout" penalty if hit |
| Market stall (mammy market) | roadside crowd, narrows lane |
| Stubborn (grabber) | runs at the car and holds on: slows you until you shake him off (swerve) so the houses can catch up |

### Scenery and roads
Bushes and hedges, palm and broadleaf trees (Kenney Nature), solar street lamps, billboards, bus stop, kiosks, hostel blocks, lecture halls, zebra crossings, side roads and junctions.

### Rules to add
- One mistake can cost you: stubborns hold the car, houses close the gap.
- Gap meter between car and chaser; speed boost and fuel pickups widen it; each hit narrows it.
- Difficulty ramps with distance (more distractions per 100 m).

## Round 3: web game spec (from the user's voice note)
- Platform: website (Three.js), portrait phone screen (normal vertical, no rotating the phone), also good on desktop. Responsive for both.
- Light and cached (service worker). No account, no backend, no login. Everything in the browser (localStorage).
- Sound: the user will supply it. Market-hawker background loop on the ticket screen (Nigerian "solo" hawker chant).
- Economy: CGPA is the currency. Start 5.0. A ticket costs 0.4 CGPA. When CGPA cannot pay a ticket, "come back tomorrow" (daily reset by local date). Developer cheat exists (hidden), nobody cares.
- Flow: ticket screen first. Hawkers hold up tickets; tap one hawker; a bottom sheet (drag up / drag down) opens to pay 0.4 CGPA; then start the engine and drive.
- Camera: portrait chase camera tuned for a narrow screen (wider FOV, higher, car in lower third).
