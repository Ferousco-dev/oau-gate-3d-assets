# ADD NEXT: OAU Road 1 driving game

Research limits (read first): web search was weak on OAU-specific detail. I found NO source for Road 1, the Student Union building layout, the Sports Complex, Mama Put/Buka food spots, or "Gboro" by name. Items marked (INFERRED) are my own suggestions, not sourced facts. Mechanics ideas (section 2) are design opinion, not researched citations.

## 1. Sourced OAU facts usable in game
- ODLT (Oduduwa Hall Lecture Theatre) is the main night-reading venue; night vendors nearby sell hot drinks, snacks, bread and egg, noodles; students use phone flashlights during power outages; rain and cold interrupt reading. Source: https://theiconsorg.blogspot.com/2025/07/surviving-night-shift-inside-oaus-night.html
- Other lecture halls named: FBLT, HSLT; Faculty of Agriculture is a "quiet" spot. Same source.
- Halls of residence: Awolowo, Angola, Alumni, ETF, Fajuyi (male); Moremi, Ladoke Akintola, Mozambique (female, per one source, others differ); Muritala Muhammad (postgraduate). Sources: https://oaukilonshele.blogspot.com/2019/05/short-history-of-legends-commemorated.html and https://studyplace.ng/?p=8158 (gender split is inconsistent between sources; verify before showing).
- Oduduwa Hall = big events centre; Amphitheatre = biggest lecture theatre. Source (2017 freshers guide, dated): https://wapniyi.blogspot.com/2017/04/exclusive-compilation-for-freshers.html
- Campus designed by Arieh Sharon, built 1963 to 1980, called "Africa's most beautiful campus"; modern heritage site. Sources: https://oauife.edu.ng/?p=8924 and https://oauife.edu.ng/?p=8573
- Transport crisis: union reports shortage of buses and tricycles, overcrowding, too few drivers, over 35,000 people on campus. Source: https://gazettengr.com/oau-students-embark-on-three-day-lecture-boycott-over-transportation-crisis/ (also Premium Times: campus shut for 3 weeks after transport protest, https://www.premiumtimesng.com/news/top-news/875525-oau-shuts-down-campus-for-three-weeks-after-students-protest.html)
- New e-portal launched April 2026, mixed reactions; old portal slow at registration and hostel allocation. Source: https://theiconsorg.blogspot.com/2026/05/new-portal-new-concerns-comparative.html
- Hostel dilapidation, about 18,928 of 26,000+ students live off campus. Source: https://campusreporter.africa/analysis-72-of-oau-students-forced-to-reside-off-campus-open-to-risks/
- A ceiling fell during a lecture, injuring students (headline only, not read in full): https://gazettengr.com/several-oau-students-wounded-as-ceiling-falls-off-during-lecture/
- Students resisted a break order and management cut power (headline only): https://saharareporters.com/2026/04/28/oau-students-defy-three-week-break-order-stage-resistance-management-cuts-power-force
- Kegites (palm wine club) founded 1962 by Ife students. Source: https://campusreporter.africa/cultism-oau-hands-12-students-to-police/ (article is about a cultism arrest, so I would NOT use it for jokes; suggest skipping).
- Not found: ASUU strike specifics for OAU, Mama Put names, Road 1 landmarks.

## 2. Mechanics shortlist (design opinion)
Power-ups: Shield "Carryover Waiver" (absorbs one chaser hit), Rocket refuel pad, Magnet for A+ stars. Near-miss bonus: pass within 1 m of traffic, +0.02 CGPA, combo multiplier. Checkpoints: "Semester gates" every ~400 m; respawn there instead of full restart. CGPA design: start 5.0, each hit -0.1, near-miss/stars +, show live on HUD with grade colour. Chaser behaviour: rubber-band speed (faster when you slow, slower when far ahead), roar audio telegraph before a burst. Difficulty ramp: obstacle density and chaser speed scale per semester gate. Comedy: "Portal Error 504" popup blocking a corner of the HUD for 2 s; "Network error, try again" toast on crash; lecturer "Carryover!" voice line. Audio: horn, generator hum, Afrobeats loop with muffled low-pass when hit, rain ambience. HUD: speed, rocket bar, CGPA, semester progress bar, minimap strip. Mobile: left-thumb steer slider or tilt, right buttons Boost and Brake, auto-throttle.

## 3. Realism assets (licences verified only where stated)
- Kenney Nature Kit, CC0 (verified): https://kenney.nl/assets/nature-kit
- Kenney Car Kit, CC0 (verified on page): https://kenney.nl/assets/car-kit (vehicle list not confirmed; check for van/truck usable as danfo base)
- Kenney City Kit (Industrial), CC0 per search result: https://gamedev.net/news/5434-city-kit-industrial/ (check kenney.nl page)
- Quaternius Ultimate Nature Pack (listing tags palm, pine, tree; licence CC0 v1.0): https://quaternius.itch.io/150-lowpoly-nature-models (set to $0)
- Poly Pizza "City Builder Bits" (street light, traffic lights, CC0 per listing): https://poly.pizza/bundle/City-Builder-Bits-1wLdnIddSx
- Poly Haven and ambientCG textures/HDRIs are CC0 per their sites (general knowledge, not re-verified here). I did NOT find a Poly Haven laterite texture; search ambientCG/Poly Haven for "dirt", "red soil", "gravel" and tint it red-orange. The "red laterite" hits were on aitextured.com under a non-CC0 licence: avoid.
- Keke napep: NO CC0 model found. Only a paid CGTrader listing (https://www.cgtrader.com/3d-models/vehicle/other/auto-rickshaw-bajaj-tricycle-keke-napep), royalty-free paid, do not use. Build in Blender. Danfo: nothing found, build from a van mesh. Okada already built.
- Not found: CC0 concrete drain, Nigerian road signs; build in Blender.
- URP settings: I found no sourced numeric values. Unity docs list SSAO (Ambient Occlusion), Bloom, Tonemapping, Color Adjustments as URP volume effects (https://docs.unity.com/en-us/engine/6000.0/manual/post-processing-and-full-screen-effects/effect-availability-reference). Suggested starting point (INFERRED, tune by eye): Tonemapping Neutral or ACES, Bloom intensity about 0.3, SSAO as a Renderer Feature, warm directional light, HDRI skybox plus Environment Lighting from skybox, linear distance fog set in Lighting settings (URP has no fog volume), soft shadows with 4 cascades limited to ~80 m, light haze for harmattan look.

## 4. Ranked list (effort S/M/L; asset = CC0 link or Blender)

### Must add next (top 10)
1. Semester-gate checkpoints, M, why: ends frustration of full restart, gives pacing. Blender (reuse arch).
2. CGPA live HUD with grade colours plus hit/near-miss changes, S, core feedback loop. Code only.
3. Near-miss combo bonus, S, rewards skilled driving. Code only.
4. Shield power-up "Carryover Waiver", S, pickup variety. Blender (simple icon mesh).
5. Chaser rubber-banding plus roar telegraph, M, fair difficulty. Code.
6. Keke napep traffic/obstacle, M, instantly reads as Nigerian. Blender (no CC0 found).
7. Danfo-style yellow-black bus as moving traffic, M, adds to Gboro bus. Kenney Car Kit base https://kenney.nl/assets/car-kit then retexture.
8. Palm trees and mango trees along median, S, strongest realism gain. Quaternius https://quaternius.itch.io/150-lowpoly-nature-models (mango: build/retint).
9. Lighting pass: HDRI sky, fog, tonemapping, bloom, SSAO, S. Settings only (see section 3); Poly Haven HDRI.
10. Power-outage event: lamps and billboard go dark for 10 s, flashlight beam from car (sourced: outages at ODLT), M, comedy plus gameplay. Code plus emissive swaps.

### Nice to have (10)
1. Night-reading ODLT landmark with vendor stalls (sourced), M, Blender.
2. Portal Error 504 HUD popup (sourced portal issues), S, UI.
3. Generator sound and Afrobeats loop with low-pass on hit, S, free CC0 audio from https://freesound.org (filter CC0, verify each).
4. Laterite shoulders and drain edges, M, PBR dirt retinted; concrete drain built in Blender.
5. Overcrowded transport crowd at bus stop (sourced transport crisis), S, reuse NPCs.
6. Rain burst event with wet road, M, particle plus smoothness change.
7. Hall name signage (Awolowo, Moremi, etc.) on hostel blocks, S, Blender text.
8. Hawker running across road, S, reuse hawker.
9. Speed-boost pads "Free Data", S, Blender.
10. Mobile touch HUD, M, Unity UI.

### Later (10)
1. Amphitheatre and Oduduwa Hall landmark buildings (sourced), L, Blender.
2. Arieh Sharon style Humanities Building (mentioned in https://www.withinnigeria.com/2026/03/27/a-1970s-glimpse-into-oaus-iconic-humanities-building/?amp=1), L, Blender.
3. Day/night cycle, M.
4. Harmattan haze season variant, M.
5. Boss chaser "Dean" at final gate (INFERRED), M.
6. Leaderboard of best CGPA, M.
7. Collapsing ceiling gag in lecture hall interior (sourced headline), M, treat lightly.
8. Photo mode with graduation gown, S.
9. LOD and occlusion for mobile build, L.
10. Voice lines in Yoruba/Pidgin, M, record own.
