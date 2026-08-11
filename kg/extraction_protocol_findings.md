# How the cold-spray literature-KG triples were extracted

## Summary

The literature KG (1,894 entities / 3,631 triples across 69 papers) was authored inside Claude Code by two Anthropic models in sequence — `claude-sonnet-4-6` for the early cohort (Apr 18–19 2026, 457 assistant turns in the largest session) and `claude-opus-4-7` for the later cohort (Apr 19–21 2026, 1,060 assistant turns across five sessions) — drafting Python populate scripts directly from PDF text and emitting per-paper Markdown analysis notes as session-time scratch artifacts. Section 1 reconstructs the three-input flow (PDF → analysis note as schema-aware extraction plan → populate script as Python serialization). Section 2 shows the analysis notes are templated LLM output, not curator reading logs. Section 3 shows the populate scripts are programmatically generated from a shared template that was revised once. Section 4 shows no extraction prompt survives in the repo — only a `.claude/` pointer to session transcripts. Section 5 shows the human-in-the-loop boundary lives upstream (template tuning) and downstream (NLI + adjudication), not at script-authoring time. Section 6 attributes specific scripts to specific models via the session transcripts.

---

## 1. Pipeline reconstruction

The flow has three artifacts per paper: source PDF, analysis note in `papers_processed/{Material}/<paper>.md`, and Python populate script in `scripts/{Material}/populate_<paper>.py`. The note is a schema-aware extraction plan; the populate script is its Python realization.

The strongest single piece of evidence is in the wu_2021 note, which reasons in first person about its own forthcoming script:

- [papers_processed/Copper/wu_2021.md:267-268](papers_processed/Copper/wu_2021.md#L267-L268): *"to avoid schema update, **I document it in the markdown but do NOT add as Characterization.Method entity**. **Instead I describe** temperature history qualitatively inside outcome entities…"*
- [papers_processed/Copper/wu_2021.md:285](papers_processed/Copper/wu_2021.md#L285): *"**I'll prioritize** the key extrema and the PHT recovery metrics … so the population script stays readable"*

The note's "Triples added: ~120" budget at line 293 is matched by the populate script's actual triple count, generated via for-loops at [scripts/Copper/populate_wu_2021.py:101-115](scripts/Copper/populate_wu_2021.py#L101-L115).

### Triple traceability (5 per sample paper)

For Al/huang_2022b, every numerical triple traces to a note table — `prop_uts_paa value 311 MPa` ([scripts/Al/populate_huang_2022b.py:144](scripts/Al/populate_huang_2022b.py#L144)) maps to [papers_processed/Al/huang_2022b.md:47](papers_processed/Al/huang_2022b.md#L47); `pow_paa has_size_range "D10=13.2, D50=29.6, D90=51.9 µm"` ([populate_huang_2022b.py:335](scripts/Al/populate_huang_2022b.py#L335)) maps to [huang_2022b.md:43](papers_processed/Al/huang_2022b.md#L43). Three populate-only enrichments (`Step size 0.2 um, area 175x137 um2` for EBSD at [populate_huang_2022b.py:329-332](scripts/Al/populate_huang_2022b.py#L329-L332); `1250 kHz, ASTM E1004` for Sigmascope at line 326; `AxioVision DMRM software` at line 290) appear nowhere in the note — moderate evidence the populate-generation step had PDF access in addition to the note.

For Cu/wu_2021 and Ti/barbosa_2010, every sampled triple traces 1:1 to a note table. Cross-paper distinguisher language is verbatim across both artifacts — *"distinct from huang_2020 Beijing COMPO Cu d50=29.0 um"* appears at [wu_2021.md:17](papers_processed/Copper/wu_2021.md#L17) and [populate_wu_2021.py:26](scripts/Copper/populate_wu_2021.py#L26).

### Note → populate filtering pass

The populate script is a strict subset of the note. The wu_2021 note explicitly drops FLIR SC5000 IR thermography and hole-drilling RS Characterization.Method ([wu_2021.md:267-268](papers_processed/Copper/wu_2021.md#L267-L268), schema-fit limits). The huang_2022b note drops cavitation testing, microhardness HV values, and O-content ([huang_2022b.md:17, 84, 92](papers_processed/Al/huang_2022b.md#L17)) without explicit rationale. The barbosa_2010 note drops TEM-SAED and XRD phase confirmation ([barbosa_2010.md:119-138](papers_processed/Titanium/barbosa_2010.md#L119-L138)).

---

## 2. Provenance of analysis notes

All 64 analysis notes share the same 7-block layout: frontmatter (Citation / DOI / KG script / **Schema version at extraction** / Institutions) → `## Relation to existing KG corpus` → `## Key Novelties` → `## Experimental Setup` → `## Results` → `## Schema Updates` → `## KG Entities Added`. A header-pattern scan returns 4–6 of these canonical headers in every file, with no missing schema or KG-Entities blocks.

The `Schema version at extraction` field is the strongest fingerprint. A grep returns hits in 64/64 notes, with values tracking a single evolving ontology from v0.7.0 ([Al/mangalarapu_2023.md:6](papers_processed/Al/mangalarapu_2023.md#L6)) to v0.12.0 ([NAB/peng_2024.md:6](papers_processed/NAB/peng_2024.md#L6)). Several notes pin the exact schema delta they introduced — e.g. [SS316L/bagherifard_2021.md:6](papers_processed/SS316L/bagherifard_2021.md#L6): *"v0.9.0 + 'fatigue testing', 'fatigue crack growth testing' added to technique enum; 'hot isostatic pressing' added to PostTreatment treatment_type enum"*. This is meta-narration the **extractor** made about its own schema choices.

A grep for `generated by | extracted using | claude | gpt | sonnet | opus | anthropic | openai | llm | chatgpt` (case-insensitive) across `papers_processed/` returned **zero matches** — there is no surviving "Generated by …" line. But two notes contain in-band first-person agent reasoning: wu_2021.md:267-268 (quoted in §1) and [SS316L/xie_2016.md:6](papers_processed/SS316L/xie_2016.md#L6): *"schema description restricts HeatTreatment to powder, but this is the only existing node type that fits 'pre-spray thermal conditioning of a metal body'… Documented in entity names."* Both quotes are agents reasoning about schema-fit choices in first person — the clearest stylistic fingerprint of LLM authorship.

The notes also contain the literal numeric values that become triple objects, so they are the **structured extraction product** rather than post-hoc reading summaries.

---

## 3. Provenance of populate scripts

The scripts are programmatically generated from a shared template that was revised once. A five-element scaffold appears in every script with high conformity:

| Element | Hit count |
|---|---|
| `e = {}` (entity dict) | 69 / 70 |
| `def eid(k): return e[k]["id"]` | 68 / 70 |
| `print(...)` finalizer | 70 / 70 |
| `PAPER = "<paper_id>"` constant | 70 / 70 |
| Calls only `add_entity()` / `add_triple()` (no helper definitions) | 70 / 70 |

The two `e = {}` / `eid` outliers are both weiller_2022 variants: [scripts/Al/populate_weiller_2022.py](scripts/Al/populate_weiller_2022.py) (uses `entities = {}` — the only script with this name in the corpus) and [scripts/Al/populate_weiller_2022_full.py](scripts/Al/populate_weiller_2022_full.py) (uses `e = {}` but no `eid` helper; the file is a follow-up "full extraction pass" added separately). Both are the chronologically earliest scripts and the only ones predating the canonical template.

### Two import-block conventions split exactly along the Al folder boundary

- **Al-folder convention** (12/12 Al scripts, 0 elsewhere): [scripts/Al/populate_huang_2022b.py:1, 18-22](scripts/Al/populate_huang_2022b.py#L1) — shebang + `from add_entity import add_entity` + `from pathlib import Path` + Unicode box-drawing dividers (`# ── MATERIALS ──`).
- **Canonical convention** (58/58 non-Al scripts): [scripts/SS316L/populate_almangour_2013.py:1-3](scripts/SS316L/populate_almangour_2013.py#L1-L3) — no shebang + `import sys, os` + `from scripts.add_entity import add_entity` + ASCII dash dividers (`# ----------`).

This binary split (no mixing) is consistent with a one-time template revision after the Al pilot batch. It correlates with the model handoff (Section 6) but is not perfectly aligned — the early SS316L scripts are also Sonnet 4.6 but use the new convention, so the template revision happened mid-Sonnet-4.6 session when moving from Al to SS316L.

### For-loop generation of symmetric entity batches

[scripts/Copper/populate_wu_2021.py:101-153](scripts/Copper/populate_wu_2021.py#L101-L153) generates 8 outcome entities and 24 porosity entities by looping over `TRAJECTORIES = ["zigzag", "cross", "parallel", "spiral"]` × planes × conditions. The wu_2021 note had explicitly anticipated this structure ("4 trajectories × 3 planes × 2 conditions"). The same for-loop pattern appears in [scripts/Titanium/populate_barbosa_2010.py:345-356](scripts/Titanium/populate_barbosa_2010.py#L345-L356) for the four gas-condition entities. Hand-authors typically write each entity inline; an LLM building from a structured plan recognizes the symmetry and emits a loop.

---

## 4. Prompt and workflow artifacts

No surviving extraction prompt exists in the repo. Searches for `**/*.prompt*`, `**/prompts/`, `**/*.ipynb`, `extract_*.py`, `build_kg.py`, `system_prompt | user_prompt | extraction_prompt` all returned either zero hits or hits restricted to the **downstream** ER and contradiction agents in [pgr/entity_resolution/agent.py](pgr/entity_resolution/agent.py) and [pgr/contradiction/contradiction_agent.py](pgr/contradiction/contradiction_agent.py).

The only on-disk fingerprint of the extraction step is the `.claude/` directory at repo root. [.claude/settings.local.json:50](.claude/settings.local.json#L50) grants read access to `C:/Users/akafle/.claude/projects/c--Users-akafle-OneDrive---University-Of-Houston-cold-spray-kg---Copy/fb587360-9082-4ce2-a15a-7b41d285bf03.jsonl` — a Claude Code session transcript. [Line 4](.claude/settings.local.json#L4) shows `Bash(python scripts/Al/populate_navabi_2022.py)` as an allowed command, i.e. populate scripts were **run from inside Claude Code**, not from a standalone shell.

The user's draft Methods text already states the answer at [manuscript/methods.md:76](manuscript/methods.md#L76): *"Claude Code drafted each script by reading the source PDF and emitting `add_entity()` / `add_triple()` calls; the curator spot-checked drafts before execution and expected residual issues to be caught by the NLI pass and adjudication described below."* This corroborates the templated-output evidence in §1–§3 and answers the question that the prior pass had flagged at [pgr/methods_facts/curation_protocol_facts.md:328-330](pgr/methods_facts/curation_protocol_facts.md#L328-L330).

**Note discrepancy with our findings.** The same paragraph at [methods.md:76](manuscript/methods.md#L76) says the analysis notes are *"the curator's reading record, not a pipeline intermediate."* §2 of this report shows the notes are also Claude-drafted — templated headers, schema-version meta-block, first-person agent voice. The notes are session-time scratch artifacts emitted alongside the populate scripts, not a pre-existing reading log.

### WarpSPEE3D is a separate KG with different infrastructure

[WarpSpee3D/_phase1_schema_based.py](WarpSpee3D/_phase1_schema_based.py) is a fully scripted Llama-3.3-70B chunk-based extractor for the WarpSPEE3D **operator-manual** KG (v0.2.0 schema with `Process.OperatorGasParameter`, `Diagnostic.Fault`, `Safety.Hazard`). Its prompt template is preserved at [_phase1_schema_based.py:72-129](WarpSpee3D/_phase1_schema_based.py#L72-L129) including worked examples for `mitigated_by` and `regulated_by`. **This is not the literature-KG extraction.** The two KGs are stitched at Phase 2 via `corresponds_to` bridges in [WarpSpee3D/_phase2_bridge.py](WarpSpee3D/_phase2_bridge.py).

The repo's [README.md:96-101](README.md#L96-L101) shows Phase 2 ("LLM-assisted extraction pipeline (Mistral/Llama via Ollama)") as **unchecked** in the project roadmap — i.e. the planned scripted Ollama pipeline was never built for the literature KG; the literature work happened ad hoc inside Claude Code instead.

---

## 5. Human-in-the-loop boundary

A grep across all 70 populate scripts for `# corrected | # verified | # fixed | # manual | # TODO | # CHECK | # FIXME | # XXX` returned **zero hits**. There are no curator-time edit markers in script bodies.

### The 25 cc<1.0 triples are LLM-emitted, not curator-applied

[data/ontology/triples.jsonl](data/ontology/triples.jsonl) holds exactly 25 triples with `confidence` < 1.0. Their distribution by source is concentrated in the *earliest* paper rather than in later (more complex) papers:

| Paper | cc<1.0 count | Confidence values |
|---|---|---|
| weiller_2022 (first paper, Apr 11 mtime) | 5 | 0.85, 0.9, 0.95 |
| tsaknopoulos_2022 (early Al) | ~6–8 | 0.8, 0.9 |
| almangour_2013, almangour_2014 | 2 | 0.9 |
| sova_2013, yin_2019, belgroune_2022 | scattered | 0.8, 0.9 |
| luo_2015 | 1 | 0.8 |

If the curator had been hand-applying down-weights at review time, the markings would grow with practice or cluster on later papers. Instead, weiller_2022 alone holds 5 of 25, and the down-weighted triples cluster on cases where the **evidence sentence itself uses hedging language** (*"potential equilibrium phase"*, *"may be present"*, *"indicating"*, *"concern"*) or where the schema relation is being stretched.

The closest thing to a rationale comment is at [scripts/Titanium/populate_luo_2015.py:409-411](scripts/Titanium/populate_luo_2015.py#L409-L411): *"# SP particles are blended INTO the spray powder — use deposited_onto for consistency but noting context"*, followed by a cc=0.8 triple. This reads as the LLM rationalizing its own schema choice at draft time, not the curator marking for review.

### Scaffolding evolution: one-time revision, then stable

Earliest: [scripts/Al/populate_weiller_2022.py:18-20](scripts/Al/populate_weiller_2022.py#L18-L20) (Apr 11 mtime) — `entities = {}` dict, no `eid()` helper, shebang + Unicode dividers. Latest: [scripts/NAB/populate_vinay_2026.py:9-29](scripts/NAB/populate_vinay_2026.py#L9-L29) (Apr 20 mtime) — canonical `e = {}` + `eid(k)` + 15-entry shared-ID preamble + ASCII dividers. The scaffolding stabilized after the Al pilot and stayed constant for the next 58 scripts. This is consistent with a one-shot generator whose template was tuned once on a calibration cohort, **not** with iterative curator calibration over time.

### Conclusion

The HITL boundary lives **upstream** of the script-authoring step (prompt design and Al-batch template calibration) and **downstream** of it (NLI evidence-support scoring per [methods.md:98-106](manuscript/methods.md#L98-L106), Llama-3.3-70B entity-resolution and contradiction agents per [methods.md:108-126](manuscript/methods.md#L108-L126), and the 289-pair / 50-group adjudication corpus). It does not live at script-authoring time itself; the curator's role at that stage was spot-checking before execution.

---

## 6. Model identification

The Claude Code session transcripts at `~/.claude/projects/c--Users-akafle-OneDrive---University-Of-Houston-cold-spray-kg---Copy/` give per-message model attribution. Aggregate model usage across the six sessions in the extraction window:

| Session ID | Date range | Sonnet 4.6 turns | Opus 4.7 turns |
|---|---|---|---|
| `882e7582-…` | Apr 18 12:53 – Apr 19 11:19 | **457** | 119 |
| `ce22a611-…` | Apr 19 11:27 – 17:03 | 0 | 210 |
| `1a44a826-…` | Apr 19 17:24 – Apr 20 09:07 | 0 | 199 |
| `3914b8ae-…` | Apr 20 09:11 – 12:02 | 0 | 258 |
| `806897ba-…` | Apr 20 12:03 – 13:41 | 0 | 191 |
| `088c7695-…` | Apr 20 13:55 – Apr 21 10:08 | 0 | 83 |
| **Total** | | **457** | **1,060** |

### Per-script attribution (sampled via `Write` tool calls in transcripts)

| Script | Date | Model |
|---|---|---|
| populate_huang_2022b.py | 2026-04-19 | **claude-sonnet-4-6** |
| populate_navabi_2022.py | 2026-04-19 | **claude-sonnet-4-6** |
| populate_nourian_2022.py | 2026-04-19 | **claude-sonnet-4-6** |
| populate_li_2024.py | 2026-04-19 | **claude-sonnet-4-6** |
| populate_yin_2019.py | 2026-04-19 | **claude-sonnet-4-6** |
| populate_bagherifard_2021.py | 2026-04-19 | **claude-sonnet-4-6** |
| populate_barbosa_2010.py | 2026-04-19 | **claude-opus-4-7** |
| populate_wu_2021.py | 2026-04-20 | **claude-opus-4-7** |
| populate_peng_2024.py | 2026-04-21 | **claude-opus-4-7** |

The model handoff and the template revision are bundled in evidence — they happened together as the Sonnet 4.6 work moved from the Al pilot folder onto the rest of the corpus, and continued under Opus 4.7 from Apr 19 onward. The first-person agent voice in [Copper/wu_2021.md:267-268](papers_processed/Copper/wu_2021.md#L267-L268) is from a Claude Opus 4.7 session.

### Pre-Apr-18 mtime caveat

The earliest populate-script mtime is Apr 11 2026 ([scripts/Al/populate_weiller_2022.py](scripts/Al/populate_weiller_2022.py), epoch 1775963393), but the earliest Claude Code session in `~/.claude/projects/...` is Apr 18 2026. Either (a) the very first weiller_2022 / huang_2022 work was done in an earlier, non-recoverable session under a possibly different model; (b) the Apr 11 mtimes are OneDrive-sync artifacts on files actually re-authored on Apr 18+; or (c) earlier sessions were rotated out by Claude Code's transcript retention. The recoverable session evidence is unambiguous within Apr 18–21; pre-Apr-18 model attribution is **weak evidence** the user can confirm from memory.

### Other Anthropic models in the repo — not the extraction model

- `claude-sonnet-4-5-20250929` is hardcoded in [pgr/entity_resolution/adjudicator.py:48](pgr/entity_resolution/adjudicator.py#L48) and [pgr/entity_resolution/adjudicator_prompt.md:3](pgr/entity_resolution/adjudicator_prompt.md#L3). **Never run** ([pgr/entity_resolution/acceptance_report.md:206](pgr/entity_resolution/acceptance_report.md#L206)).
- `claude-sonnet-4-5` in [pgr/rag_eval/_s35_op6_frontier_judge.py:20](pgr/rag_eval/_s35_op6_frontier_judge.py#L20). **Deferred** per [pgr/rag_eval/stream3_5_report.md:5](pgr/rag_eval/stream3_5_report.md#L5).

---

## Methods-section-ready protocol

Based on surviving artifacts and Claude Code session transcripts, the literature knowledge graph was extracted by drafting one Python populate script per paper inside Claude Code, with two Anthropic models in sequence. The first-batch model was Claude Sonnet 4.6 (`claude-sonnet-4-6`), running for 457 assistant turns in the Apr 18–19 2026 session that produced the Al-folder pilot cohort and the early SS316L scripts. The second-batch model was Claude Opus 4.7 (`claude-opus-4-7`), running for 1,060 assistant turns across five subsequent sessions Apr 19–21 2026 that produced the Cu, Ti, NAB, and remaining SS316L scripts. The two-model handoff is recorded in the per-message `model` field of the Claude Code transcripts under `~/.claude/projects/`, and per-script attribution is recoverable by matching `Write` tool calls to the assistant turn that emitted them.

The Al folder served as the calibration cohort. The earliest populate scripts (weiller_2022 variants, in particular [scripts/Al/populate_weiller_2022.py](scripts/Al/populate_weiller_2022.py) and [populate_weiller_2022_full.py](scripts/Al/populate_weiller_2022_full.py)) used a slightly less mature template — `entities = {}` dict naming, no `eid()` helper, shebang + Unicode box-drawing dividers — that was revised once after the Al pilot to the canonical `e = {}` + `def eid(k):` + ASCII-dash form preserved in 58 of the 70 scripts. The template revision and the model handoff are bundled in evidence; both happened as the work moved off the Al pilot. Each script was authored from the source PDF directly: instrument-level details such as XRD acquisition parameters, EBSD step sizes, and ASTM standard numbers appear in the populate scripts but not in the corresponding analysis notes ([scripts/Al/populate_huang_2022b.py:326, 329-332](scripts/Al/populate_huang_2022b.py#L326)), establishing PDF-direct authoring rather than a note-mediated extraction. The per-paper Markdown notes under `papers_processed/` are session-time scratch artifacts emitted by the same Claude session alongside the populate scripts — they share the templated 7-block layout, the `Schema version at extraction` meta-field tracking ontology evolution from v0.7.0 to v0.12.0 ([papers_processed/Al/mangalarapu_2023.md:6](papers_processed/Al/mangalarapu_2023.md#L6) through [papers_processed/NAB/peng_2024.md:6](papers_processed/NAB/peng_2024.md#L6)), and in two cases ([papers_processed/Copper/wu_2021.md:267-268, 285](papers_processed/Copper/wu_2021.md#L267-L268), [papers_processed/SS316L/xie_2016.md:6](papers_processed/SS316L/xie_2016.md#L6)) preserve the agent's first-person reasoning about schema-fit decisions for the populate script. The notes are not a pre-existing curator reading log and are not consumed as input by any downstream script.

Per-triple confidence is self-rated by the extracting model. Of the 3,631 triples, 3,606 carry the default `confidence = 1.0` and the 25 below ceiling cluster on cases where the source sentence itself hedges (*"potential equilibrium phase"*, *"may be present"*) or where the schema relation is being stretched — exemplified by [scripts/Titanium/populate_luo_2015.py:409-411](scripts/Titanium/populate_luo_2015.py#L409-L411) where the in-line comment *"use deposited_onto for consistency but noting context"* explicitly rationalizes the cc=0.8 emission. The earliest paper, weiller_2022, holds 5 of the 25 down-weighted triples on its own, including [scripts/Al/populate_weiller_2022_full.py:216, 218, 222](scripts/Al/populate_weiller_2022_full.py#L216), which is inconsistent with the alternative reading in which down-weights were applied at curator-review time; we therefore treat the 99.3 % cc=1.0 ceiling rate as an LLM emission default with self-rating on schema-stretch triples rather than as a verified-by-curator signal. The curator's role was bounded to four steps: prompt design and template tuning during the Al pilot; spot-checking drafts before execution per [manuscript/methods.md:76](manuscript/methods.md#L76); the NLI evidence-support scoring pass on 2,478 triples per [manuscript/methods.md:98-106](manuscript/methods.md#L98-L106); and the downstream entity-resolution and multi-tail / contradiction adjudication via two Llama-3.3-70B-Q4 agents on a local Ollama server per [manuscript/methods.md:108-126](manuscript/methods.md#L108-L126). No extraction prompt template survives in the repo; the prompt history and per-iteration design choices live only inside the Claude Code session transcripts at `~/.claude/projects/c--Users-akafle-OneDrive---University-Of-Houston-cold-spray-kg---Copy/`, which sits outside the public deposit.

---

## Open questions

- **Pre-Apr-18 mtime gap**: Were [scripts/Al/populate_weiller_2022.py](scripts/Al/populate_weiller_2022.py) and the earliest huang_2022 / julien_2022 / ren_2022 scripts (Apr 11 mtime) authored in an earlier, non-recoverable Claude Code session, possibly under a different model? The recoverable session directory begins Apr 18 and there is no evidence in `~/.claude/projects/` of an earlier session for this project. OneDrive sync may also have rewritten file mtimes; the user can resolve this from memory.
- **Template revision timing**: The script convention switched from Al-folder (shebang + `from add_entity` + Unicode dividers) to canonical (no shebang + `from scripts.add_entity` + ASCII dividers) at the Al → SS316L boundary inside the Apr 18–19 Sonnet-4.6 session. Was this an explicit prompt-template revision the curator made between batches, or did the model revise its own boilerplate after the pilot? The two are bundled in evidence and indistinguishable from artifacts alone.
- **Whether the prompt template ever existed as a discrete artifact**: No prompt file or system-prompt block survives outside the session transcripts. If the prompt evolved across Sonnet-4.6 → Opus-4.7, the only record is in the `~/.claude/projects/...` jsonl files. If the user wants the prompt as a deposit artifact, it would need to be reconstructed by reading the transcripts.
- **Whether any literature-KG triples were edited post-extraction outside `populate_*.py`**: The audit pipeline is read-only on `triples.jsonl`, but if any triples were hand-edited in the JSONL file directly, that activity would not be visible in script bodies. No evidence found; flagging only as a completeness check the user can confirm.
