# Visual Language

## Style Goal

Build a cinematic decision grammar that feels observational, stable, and readable — not promotional, not theatrical. Images serve information and human context before decorative composition. Vertical delivery (9:16) is a Brief format adaptation, not Style identity.

## Inherit from Common Craft

Consult `video-workflow/knowledge/editing-craft/visual-language.md` for:

- Shot size and angle meaning
- Composition, eye trace, and continuity defaults
- Subject-safe reframing for vertical delivery
- Priority stack: Emotion → Story → Rhythm → Attention (continuity subordinate when they conflict)

This Style narrows which sizes, angles, and movements are default vs exceptional.

## Style Defaults

**Shot size mix:** wide establish + medium action dominant; close-up reserved for evidence, contrast, or earned emotion.

**Camera feeling:** observational, stable-to-light handheld; eye-level or neutral angle preferred.

**Composition:** clear subject hierarchy; readable action; attention target named per beat in Blueprint.

**9:16 adaptation (when Brief specifies vertical):** subject-first reframing — fill frame, preserve aspect ratio, reposition for face / hands / key object. No stretch, no unintended letterbox.

## Prefer When

### Shot Size

| Size | Prefer when | Perceptual effect | Narrative effect |
|------|-------------|-------------------|------------------|
| **Wide** | Opening context, spatial relation, city or environment scale | Viewer orients in space | **ESTABLISH**, **CONTEXT** |
| **Medium** | Everyday action readable in one frame — walking, paying, browsing | Natural social distance | Default **EVIDENCE**, **REACTION** |
| **Close** | Specific detail proves narration — hands, label, mechanism | Intimacy without melodrama | **EVIDENCE**, **EMPHASIS** when fact needs proof |
| **Detail / insert** | One object carries the claim — price tag, sign, tool | Concrete specificity | **EVIDENCE**, **REVEAL** |

### Camera Angle

| Angle | Prefer when | Perceptual effect | Narrative effect |
|-------|-------------|-------------------|------------------|
| **Eye-level** | Default human observation | Peer credibility | Most beats |
| **Slight high** | Overview of activity, table surface, crowd flow | Mild overview | **CONTEXT**, **ESTABLISH** |
| **Neutral lateral** | Side view of action without power play | Documentary calm | **EVIDENCE** |

### Camera Movement

| Movement | Prefer when | Perceptual effect | Narrative effect | Capability intent |
|----------|-------------|-------------------|------------------|-------------------|
| **Static / locked** | Action readable without motion; evidence clarity | Honest presence | Default for **EVIDENCE** | `visual.reframe.static` |
| **Gentle push-in** | Static plate needs subtle attention guide | Mild focus shift | **EMPHASIS** on one detail | `visual.motion.push_in` → fallback `visual.reframe.static` |
| **Gentle pan** | Reveal spatial relation within one shot | Environmental discovery | **ESTABLISH**, **CONTEXT** | `visual.motion.pan` → fallback `visual.reframe.static` |
| **Light handheld** | Already present in source; adds lived-in texture | Human presence | **REACTION**, street life | Preserve source; do not amplify artificially |
| **Reframing (post)** | Landscape source, vertical Brief | Subject preserved in frame | All vertical beats | `visual.reframe.static` |

**Avoid (movement):** aggressive zoom, whip pan, crane-like grandeur, constant kinetic reframing — reads ad-like or trailer-like.

### Composition & Blocking

- **Visual hierarchy:** narration subject or evidence object reads first
- **Eye trace:** cut order follows attention target, not decorative symmetry
- **Negative space:** modest breathing room; not empty design frames
- **Blocking:** prefer natural pedestrian or customer behavior over posed stock performance
- **Spatial / lens feeling:** normal-to-mild telephoto for street detail; avoid ultra-wide distortion unless environment scale is the point

## Allow When

- **Close-up** on face when narration discusses social reaction or emotional nuance — not as default beauty shot
- **Slight high angle** for table-level evidence (food, payment, documents)
- **Gentle push-in** on static plate when reframing alone cannot direct attention
- Intentional letterbox or graphic layout only when Brief explicitly requests design treatment
- Creative Direction requests slightly warmer framing or playful composition within readability bounds

## Avoid When

- Close-up used for generic "film look" without evidence or contrast job
- Low angle on ordinary shopping or street scenes — implies heroism or promo power
- Aggressive shallow depth and dramatic angle on mundane evidence (see RC-VIS-001)
- Every shot reframed with motion because static feels "boring"
- Crop removes hands, face, or payment action that narration references

## Prohibit

- Horizontal stretch to fill 9:16
- Unintended black bars (letterbox / pillarbox) in vertical deliverable
- **visual.motion.aggressive_zoom** as default attention tool
- Decorative dutch angle, lens flare worship, or perpetual shallow-DoF "cinema skin"
- Framing that contradicts narration fact (wrong country cues, wrong activity, wrong season implied)

## Exceptions

- Owner local intent requests heightened contrast or reveal on a named beat — stronger angle or push allowed for that beat only
- Privacy blur or intentional obscuring of identifiable faces when Brief or ethics require it
- Brief requests letterbox or split-screen layout as explicit design override
- No reframing-capable route verified: select alternate source or alternate range before accepting bad crop

## Trade-offs

| Choice | Gain | Cost |
|--------|------|------|
| Medium-dominant grammar | Credibility, readability | Less visual punch |
| Static over motion | Observational honesty | May feel plain vs trailer genres |
| Subject-first 9:16 crop | Mobile readability | Loses environmental width |
| Gentle push-in vs static | Directed attention | Slight "produced" feeling if overused |
| Evidence close-up | Proof strength | Risks melodrama if unmotivated |

## Capability Intent

| Visual decision | Primary capability | Fallback |
|-----------------|-------------------|----------|
| Asset choice for function | `visual.select_asset` | — |
| Vertical / horizontal reframe | `visual.reframe.static` | alternate source |
| Motivated subtle push | `visual.motion.push_in` | `visual.reframe.static` |
| Environmental pan within shot | `visual.motion.pan` | `visual.reframe.static` |
| Clip duration to beat | `visual.trim` | — |
| Abnormal slow motion correction | `visual.motion.speed_change` | replace source |
| Hard cut between sizes | `edit.cut` | — |

Forbidden for default use: `visual.motion.aggressive_zoom`.

Final framing verification belongs to deliverable QA (`qa.final_artifact`, `qa.visual.frame`) — transform read-back alone is insufficient.

## Blueprint Mapping

| Blueprint field | Visual language use |
|-----------------|---------------------|
| `visual_intent` | Declares what the image must accomplish (prove, orient, contrast) |
| `attention_target` | Drives shot size, reframe anchor, composition priority |
| `preferred_shot_functions` | Maps to size / angle defaults (e.g., EVIDENCE → medium or close) |
| `narrative_function` | Informs whether close or wide is stylistically appropriate |
| `color_effect_intent` | Natural default; see `06-color-look-effects.md` |
| `capability_requirements` | e.g., `visual.reframe.static`, `visual.motion.push_in` when beat needs motion |

Optional `shot_plan` entries may specify per-shot size, angle, movement, and reframe anchor when continuity is critical.

## QA Signals

- Wide / medium / close mix serves information — not random size montage
- Close-ups correlate with evidence, contrast, or earned emotion beats
- Vertical deliverable: subject visible; no unintended bars; hands and faces preserved when narrated
- Camera assertiveness stays low — piece does not read as ad or trailer
- Motion on static plates is rare, motivated, and subtle
- Generic stock posing flagged and deprioritized

## Reference Cases

**RC-VIS-001:** Payment at counter — **EVIDENCE**, attention on hands. Preferred: medium stable neutral angle. Avoid: aggressive push-in with shallow depth. Because observational style treats payment as everyday proof, not spectacle.

**Street establish:** Wide or medium-wide at eye level for **ESTABLISH** — orient viewer before semantic units. Prefer readable signage and pedestrian flow over drone-like grandeur.

**Vertical hands action:** Reframe anchor on hands and transaction object; subtitle safe zone in lower third considered in composition hierarchy.
