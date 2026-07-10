# Team Brief: All-Femme Cyberpunk Blood Bowl Team (Amazon roster)

*Draft v1.2 — 2026-07-10. Companion to `PROJECT.md` (process/pipeline state).
v1.2 syncs the brief with Mace's production run (pose revision, gang-mark
print lesson, emblem placement, status).*

*For: Jason — our resident Amazon specialist coach, gamer, and cyberpunk
lover. This brief is being shared with him for review; his feedback may
revise character blocks before their models are specced.*

This is the master context document for the whole team. Each miniature gets
its own spec when we start it, derived from its character block in §6 — the
per-model spec is where poses and props get pinned to pipeline standard
(explicit prop geometry, every hand accounted for, provable camera angles).

## 1. Project overview

A full 14-model, all-femme, cyberpunk-styled Blood Bowl team built on the
BB2025 **Amazon** roster, produced via the established AI pipeline (Gemini
clay-sculpt turnarounds → Meshy multi-view → trimesh validation → resin).

Design goals, in priority order:

1. **Reads as a Blood Bowl team at arm's length.** Positional roles must be
   distinguishable across the table (blockers bulkiest, blitzers most
   dynamic, throwers with the ball).
2. **Proxy-friendly.** Straight cyberpunk, no fantasy/jungle motifs — the
   team should proxy cleanly for other rosters (esp. Humans). Nothing on a
   model should scream "Amazons only".
3. **14 genuinely distinct individuals.** No two models share a silhouette.
   Distinctness is geometric (build, hair, chrome placement, signature mass,
   pose) — NOT paint-dependent, because the pipeline works in monochrome
   clay-sculpt renders.
4. **Cool, not comedy.** Stylish, athletic, dangerous. Humor lives in names
   and fluff only, never in the sculpt.

## 2. Roster reference (BB2025 Amazon, bloodbowlbase.ru)

Tier 1, Lustrian Superleague. Re-roll 60K, Apothecary 50K.

| Position | Qty | MA | ST | AG | PA | AV | Skills | Cost |
|---|---|---|---|---|---|---|---|---|
| Eagle Warrior (Lineman) | 0-16 | 6 | 3 | 3+ | 4+ | 8+ | Dodge | 50K |
| Python Warrior (Thrower) | 0-2 | 6 | 3 | 3+ | 3+ | 8+ | Dodge, On the Ball, Pass, Safe Pass | 80K |
| Piranha Warrior (Blitzer) | 0-2 | 7 | 3 | 3+ | 4+ | 8+ | Dodge, Hit and Run, Jump Up | 90K |
| Jaguar Warrior (Blocker) | 0-2 | 6 | 4 | 3+ | 4+ | 9+ | Defensive, Dodge | 110K |

The cyberpunk reading of the stat line: everyone has Dodge and light armour —
this is a **reflex-boosted** team. Speed, wired reactions, and slipperiness
over bulk. The blockers are the one exception: ST4/AV9+ juiced heavies.

**Model set (14):** 8 linewomen + 2 throwers + 2 blitzers + 2 blockers —
every legal positional slot filled.

## 3. Team concept

**The team IS a street gang.** The eight linewomen are the gang's core; the
specialists are the gang's own talent, not hired guns:

- **Linewomen → Gangers.** One gang, shared identity (kit, iconography,
  jack ports), eight strongly distinct members. Reflex boosts are the gang's
  one universal augment — every member has visible interface hardware
  (temple studs / neck ports) even when the rest of her chrome is minimal.
- **Throwers → Fixers.** The playmakers who move the goods and call the
  shots. Smart-link arms, field-general poise. On the Ball / Safe Pass as
  personality: the ball arrives where it needs to be, always.
- **Blitzers → Netrunners.** Fast, slippery, impossible to pin down (Hit
  and Run, Jump Up). Light kit, decks and interface cables, poses mid-juke.
  They read the field like ICE and slide through gaps.
- **Blockers → Juicers.** The muscle. Openly on the juice AND heavily
  chromed for strength — hypertrophied builds with industrial/military-grade
  cyberlimbs. The two most massive silhouettes on the roster by a wide
  margin.

## 4. Team-wide visual language

**Kit (every model):** cyber sports kit — recognizable fantasy-football
elements built from cyberpunk materials.

- **Asymmetric armored shoulder pad** (team-standard shape: layered plasteel
  plates with a beveled rim) on the *left* shoulder for all 14 — the single
  strongest unifying element. Specialists may add gear on top, never
  replace it.
- Armored boots with gridiron cleat soles; knee/shin plates optional per
  character.
- **Jack ports**: a visible cluster of 2–3 interface studs at the right
  temple or neck on every model — the gang mark. Raised (paintable), never
  fragile pins. **Print-survival caveat (m1 lesson, 2026-07-10):** small
  studs vanish in mesh reconstruction — Jason caught it on Mace's first
  mesh. Her fix is a roughly eye-sized triangular three-pin socket plate
  (proven bold enough to survive). Studs stay the team default on paper;
  each model's spec picks studs-vs-socket at spec time, sized to survive.
- **Position iconography (Jason, 2026-07-10):** each position wears its
  BB2025 totem animal as a flat stencil-style emblem — **EAGLE**
  (linewomen), **PYTHON** (throwers), **PIRANHA** (blitzers), **JAGUAR**
  (blockers). Only the Fixers actually wear jackets, so the default
  placement is the **top plate of the team-standard left shoulder pad,
  directly below the player number** (revised on Mace's run, 2026-07-10 —
  lower plates stay plain) — the one surface every model has;
  jacket/coat wearers (Broker, Dime) can
  carry it larger as a back patch instead. Style: spray-stencil / gang-tag
  silhouette, not fantasy heraldry. Engraved ≥0.15mm and simple enough to
  read at 32mm. Bonus: positions become identifiable at the table, which
  strengthens proxy use.
- Player number engraved on the left pad's top plate, above the position
  emblem (assign at spec time; engraved ≥0.15mm so it survives printing
  and paints easily). Mace wears **8**.
- Athletic base layer: armored bodysuits / compression gear / reinforced
  fatigues per character. **Athletic, not cheesecake** — these are pro
  athletes/streetfighters; muscle tone yes, pin-up posing no.
- The ball (where held): classic spiked/laced Blood Bowl ball silhouette —
  do not gadget-ify it; ball readability is sacred for proxy play.

**Chrome grading (niche rule):** cyberlimbs are fine on any position —
several linos have them (Sable's piston cyberleg, Volt's cyberarm, Dice's
chrome hand), as do the specialists. But **mil-spec grade and/or oversized
chrome is exclusive to the Blockers**: nobody else gets military plating,
hypertrophied builds, or augments bigger than the flesh limb they replace.
Everyone else's chrome is street/sport-grade and body-proportioned.

**Body diversity is load-bearing:** builds range petite → athletic → heavy
across the roster (see the distinctness matrix, §7). This is both
characterful and the main anti-look-alike lever.

**Palette** (paint stage only — sculpts are monochrome): gunmetal/matte
black armour, ONE hot neon accent (magenta recommended; cyan alternate),
white numbers. Neutral enough to sit next to any opponent as a proxy.

**IP guardrails:** original sculpts only. No GW iconography or trademarks
(no "Blood Bowl" text anywhere). No CD Projekt / R. Talsorian marks either —
no Arasaka/Militech/Samurai logos, no "Night City". Genre, not brand.

## 5. Team name (chosen 2026-07-10)

**Firewall FC, a.k.a. "the Furies."** Official club name Firewall FC —
sports-club framing, "you shall not pass" energy for a Dodge/Defensive
team. The Furies is the street name: the linewomen's gang at the team's
core, and what everyone actually calls them at the table. Both names are
fair game for kit flavour (engraved "FFC" crest, Fury iconography).

## 6. The fourteen

Format: **HANDLE** — position. Concept. *Silhouette hooks* (the geometric
features that make her unmistakable in monochrome). Pose sketch (pinned
properly at per-model spec time).

### Blockers / Juicers (Jaguar Warriors)

**BREAKER** — Blocker #1. Ex-dockworker who kept the industrial loader
chrome and added juice on top. The gang's immovable object. *Hooks:*
top-heavy gorilla silhouette — oversized hydraulic cyberarms (both),
knuckles like tow-hitches, subdermal plate ridges across trapezius,
injector rig strapped to one thigh. Shortest-and-widest heavy. Pose: low
wide braced stance, arms flexed outward, weight forward — a wall mid-set.

**GORGON** — Blocker #2. Washout from a corpo super-soldier program; sleek
mil-spec grafts instead of Breaker's industrial slabs. Colder, quieter,
scarier. *Hooks:* tall and V-tapered rather than squat; symmetric chromed
arms with clean panel lines; thick cable-dreads swept back (her namesake —
sculpted as chunky, print-safe locks); glowing spinal stack implied by a
raised vertebral ridge. Pose: upright, mid-stride advance, one arm raised
palm-out to stiff-arm.

### Blitzers / Netrunners (Piranha Warriors)

**GLITCH** — Blitzer #1. Wiry, twitchy, brilliant; runs hot and talks
faster. *Hooks:* smallest frame among the specialists; asymmetric
half-shaved bob; AR goggles pushed up on forehead; slim cyberdeck slung at
the right hip with its interface cable coiled tight around her left
forearm (coiled = print-safe, no floating loops). Pose: full sprint, deep
lean — one of the team's ≤3 dynamic slots; both cleats still reach ground
level (basing rule, §8).

**WRAITH** — Blitzer #2. The ghost — nobody remembers tackling her because
nobody has. *Hooks:* hood up over a mirrored full-face visor (hood gives a
unique head silhouette and prints clean); long-limbed; matte bodysuit with
minimal plating; blade-runner sprinter's cyberlegs below the knee. Pose:
low sliding juke, one hand skimming the turf.

### Throwers / Fixers (Python Warriors)

**BROKER** — Thrower #1. The senior fixer; owns every favour in the
district. Calm is her whole brand. *Hooks:* knee-length armored coat
(unique big-mass silhouette; sculpts and prints well); smart-link right
arm with visible targeting vanes at the wrist; slicked-back undercut.
Pose: classic quarterback — ball gripped high in the smart-link hand,
off-hand pointing downfield, coat mid-swirl.

**DIME** — Thrower #2. The up-and-comer; drops the perfect pass and lets
you know about it. *Hooks:* cropped bomber jacket over kit (contrast with
Broker's long coat); high ponytail through a gearhead headband; cyber-eye
with a slim brow-mounted rangefinder; ball tucked under one arm. Pose:
scanning mid-jog, head turned sharply left, free hand signalling a route.

### Linewomen / Gangers (Eagle Warriors) — the gang core

**STITCH** — Lino #1. Gang med-tech; patches the crew between drives and
hits exactly as hard as she heals. *Hooks:* trauma-kit satchel on the hip,
one forearm freshly chromed with the bandage wrap still on; practical
short crop. Pose: watchful guard — weight back, hands open, reading the
field. (Sharpened v1.2 to stay distinct from Mace's revised wide-ready.)

**MACE** — Lino #2, jersey #8. The brawler; the one who starts it.
*Hooks:* plated knuckle guards on both fists, flattened nose, heavy jaw,
buzzcut; densest build of the eight; eye-sized triangular three-pin
socket at her right temple as her gang mark (see §4 caveat). Pose
(revised 2026-07-10): wide "wrestle-you-down" ready — stance wider than
shoulders, both feet planted, weight forward, arms wide, open palms out
front. (Her original mid-shove goes back in the pose pool for a future
lino.) *Niche guard:* she must NOT eat into the blockers' lane — dense
but human-scale athlete, no hypertrophy, and (as her personal style, see
§4 chrome grading) no cyberlimbs at all: street-grade knuckle guards are
her whole statement. Mace is just the meanest normal person on the pitch.
*Status (2026-07-10, end of day):* full pipeline exercised concept→STL in
one day — first mesh (m1) is a clean watertight print candidate, but it
ate the temple studs (→ socket redesign) and squeezed her wide stance
(→ pose-matched turnaround templates, now standard). Retake sheet
(r8-A1-final) is the m2 candidate awaiting Dimitri's sign-off. Full spec
in `mace/spec.md`; keepers in `mace/concept-art/`.

**JINX** — Lino #3. The street kid; youngest, fastest mouth, oversized
hand-me-down kit. *Hooks:* smallest and lankiest of the eight; jersey too
big and half-untucked; mismatched shin guards; short twin buns. Pose:
flat-out scramble, arms pumping.

**SABLE** — Lino #4. The quiet veteran; ten seasons, one expression.
*Hooks:* single thick braid over the shoulder (chunky, print-safe); left
leg is a full piston-calf cyberleg; sleeve of old gang tattoos implied as
low relief. Pose: three-point sprinter's stance.

**VOLT** — Lino #5. The live wire; taunts the opposing blitzer by name.
*Hooks:* tall mohawk (the loudest head silhouette in the roster); left
cyberarm with arc-scarring texture; lean and long. Pose: upright taunt,
one hand beckoning, the other cocked back — both hands clearly empty.

**BRICK** — Lino #6. The anchor of the line; goes exactly nowhere she
doesn't choose to. *Hooks:* widest lino, near-blocker mass but zero
cyberlimbs — she's just built like that; scavenged extra-heavy right
shoulder pad over the team-standard left one; hair in a tight knot. Pose:
planted square block stance, arms locked in a wedge.

**ECHO** — Lino #7. The listener; calls out plays she shouldn't be able to
hear. *Hooks:* fully shaved head with twin rows of interface ports over
the scalp; audio collar array around the neck (raised ring, print-safe);
average build — her head hardware IS the silhouette. Pose: lateral
defensive shuffle, arms wide.

**DICE** — Lino #8. The gambler; plays the odds, on and off the pitch.
*Hooks:* string of luck charms on the belt (sculpted chunky); asymmetric
chin-length bob; one full-chrome hand, fingers splayed showing it off.
Pose: easy jog, head turned calling for the pass — both hands visibly
empty.

## 7. Distinctness matrix

No two rows may converge during generation. If a generated sheet drifts
toward another character's column entries, that's a reject.

| # | Handle | Pos | Build | Head/hair | Chrome focus | Signature mass | Pose family |
|---|---|---|---|---|---|---|---|
| 1 | Breaker | Blocker | squat-massive | short crop | both arms, industrial | hydraulic arms | braced wall |
| 2 | Gorgon | Blocker | tall-massive | cable-dreads | both arms, mil-spec | dread mane | stiff-arm advance |
| 3 | Glitch | Blitzer | petite-wiry | half-shaved bob | deck + cable arm | hip deck | full sprint |
| 4 | Wraith | Blitzer | long-limbed | hood + visor | runner cyberlegs | hood | sliding juke |
| 5 | Broker | Thrower | athletic | slick undercut | smart-link R arm | long coat | QB throw |
| 6 | Dime | Thrower | athletic-compact | high ponytail | cyber-eye | bomber jacket | scan + tuck |
| 7 | Stitch | Lino | average | short crop + satchel | fresh forearm | med satchel | watchful guard |
| 8 | Mace | Lino | dense | buzzcut | knuckle plates | none (fists) | wide ready |
| 9 | Jinx | Lino | small-lanky | twin buns | ports only | baggy jersey | scramble |
| 10 | Sable | Lino | athletic | thick braid | piston cyberleg L | braid | 3-point stance |
| 11 | Volt | Lino | tall-lean | mohawk | cyberarm L | mohawk | taunt |
| 12 | Brick | Lino | widest lino | tight knot | none | double pads | square block |
| 13 | Echo | Lino | average | shaved + scalp ports | audio collar | collar array | lateral shuffle |
| 14 | Dice | Lino | average | asym bob | chrome hand R | charm belt | jog + look back |

Build spread: 2 massive, 1 dense, 1 widest-lino, 5 athletic/average, 2
small/petite, 3 tall/long. Head silhouettes: all 14 distinct.

## 8. Technical specs

- **Scale:** 32mm heroic, matching the Igor set — chunky hands/features so
  they don't look spindly next to GW-adjacent minis. Target height ~37mm
  eye-level-scaled for athletic femme builds (confirm against a printed
  Igor before batch production).
- **Bases:** 32mm round (standard BB).
- **Print target:** resin, one-piece per model strongly preferred. Thin
  elements ≥0.6mm, engraved details ≥0.15mm.
- **Basing rule (Jason, 2026-07-10):** minimum TWO contact points per
  model — default pose is both feet planted at ground level, flat is
  best, one foot slightly behind is fine. **Dynamic-pose budget: at most
  ~3 especially dynamic poses on the whole team** (current allocation:
  Glitch's sprint, Wraith's slide, one slot reserved), and even those
  must have both feet bottoming out at ground level — a lifted foot
  can't be glued to a base without pinning.
- **Cyberpunk-specific print hazards** (flag at spec time, every model):
  cables (always coiled/against-body, never free loops), antennae/vanes
  (≥0.6mm, short), mohawks/braids (chunky, connected), visor edges,
  splayed fingers (Dice), coat hems (thicken).
- **Left/right convention (global policy, 2026-07-10):** every side
  reference in prompts, specs, and audits is the **VIEWER'S left/right**,
  anchored to a named view ("front view: pad on the viewer's right");
  profile views are named by visible feature ("the pad side"). Character
  anatomy is stated once per spec as ground truth, then translated.
- **Pipeline:** per the `miniature-concept-pipeline` skill — monochrome
  clay-sculpt 4-view turnarounds (Gemini via `tools/gemini_gen.py`), Meshy
  multi-view (API, ~20 credits/run), trimesh validation, fresh-context
  subagent audits, lineage naming + `lineage.json`, per-round markdown log.
  14 models × multiple rounds each = budget attention on Meshy credits and
  Gemini spend; audit inputs before every paid run.

## 9. Production order (proposal)

Start with ONE model to establish the team-standard kit (shoulder pad
shape, jack ports, boot design) as a visual exemplar, then reuse its
approved sheet as the kit reference for the rest.

First model: **MACE** (Lino #2) — average-complexity, no coat/hood/deck
to complicate reconstruction, easy hands, dense build (forgiving
geometry). She locks the kit standard; she already has a first mesh, with
a refined m2 sheet in review (see her block in §6). Original proposal was
then one specialist of each type (Breaker → Broker → Glitch) to
stress-test the extremes before the remaining linos — but **Jason picks
which character he wants to see next.**
