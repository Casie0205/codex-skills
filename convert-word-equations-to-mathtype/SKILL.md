---
name: convert-word-equations-to-mathtype
description: Convert native Microsoft Word OMML equations in a DOCX into editable inline MathType Equation.DSMT4 objects on Windows without UI clicking, keystrokes, or Word macros. Use for reliable batch conversion through MathML, general typography rules, a non-fatal AI review queue for special cases, Markdown intermediates, selective formula repair, minimal OOXML merge, and full package/WMF/Word validation.
---

# Convert Word Equations to MathType

Use the MathML-first V2 workflow:

`OMML → normalized Presentation MathML → MathType native MathML API → editable inline OLE → MathML/MTEF/TeX readback`

TeX is diagnostic output only. Do not use TeX as the production input and do not send `Alt+\`.

Read [references/workflow.md](references/workflow.md) and [references/validation-contract.md](references/validation-contract.md) before converting.

## Core design

Separate the work into two layers:

1. General batch conversion runs once for the whole document.
2. Special cases enter a Markdown AI review ledger and are repaired only by source formula index.

Never add a narrow thesis-specific workaround to the general layer merely to make a hard gate pass. Never restart all converted formulas after discovering one special case.

## Preconditions

- Require Windows, desktop Microsoft Word, and MathType 7.
- Record the source path, byte size, SHA-256, lock state, top-level OMML count, and existing Word processes.
- Use unique absolute paths for source, backup, lightweight donor source, full donor, manifests, Markdown ledgers, final output, and reports.
- Never overwrite the source. Create a byte-identical backup before final merge.
- Use only a hidden automation-owned Word process. Do not click UI, send keystrokes, run macros, or terminate a pre-existing user Word process.

## Typography contract

- Ordinary scalar variables: italic.
- Ordinary vectors and matrices: bold italic; verify final MTEF style `BI`.
- Identity/unit diagonal matrix `I`: bold upright; verify final MTEF style `B`, not `BI`.
- Physical units, function/operator names, transpose `T`, and differentials used as operators: upright.
- Treat character presence, semantic structure, MathML style, MTEF style, and WMF display as separate checks.
- Text, Function, Variable, Vector, Number, and User2 must map to Times New Roman; Math Extra must map to Euclid Extra. Verify both from MTEF v5 record type 17 `FONT_DEF` plus `EQN_PREFS` style-array references; a visible string anywhere in a compressed OLE binary is not evidence.

## Required workflow

1. Run V2 `Preflight` against the source or a lightweight OMML-only donor source.
   - Persist source hash, source index, raw/normalized MathML, canonical tokens, structure signature, style sequence, and accent-script risks.
2. Build a representative real-formula test DOCX and run `Strict`.
   - Cover fractions, roots, scripts, limits, sums, integrals, matrices, cases, norms, Greek variants, functions, units, vector/matrix/identity typography, accents, accent-plus-script geometry, degree/primes, long formulas, and known special patterns.
   - Require all representative formulas to pass token, structure, MathML style, MTEF style, accent correction, and WMF red-error gates.
3. Run the whole lightweight donor exactly once with the default `ReviewQueue`.
   - Continue when an editable inline MathType object can be created, closed, saved, and counted even if semantic/style comparison differs.
   - Stop only for fatal failures: OLE creation/activation/close/save failure, unrecoverable malformed data, object-count loss, Word save failure, or invalid DOCX package.
4. Generate two Markdown files with `build_mathtype_v2_markdown.py`.
   - Full intermediate: every formula's source normalized MathML, MathType diagnostic TeX, and status.
   - AI review ledger: only flagged formulas, with issue codes, source/readback MathML, diagnostic TeX, special-rule ID, conclusion, and selective-repair result.
   - If `MathTypeDiagnosticPolicy` marks a formula's TeX export as unsafe, keep MathML/MTEF verification and record a skipped diagnostic instead of invoking MathType's translator. This prevents non-blocking MathType translator dialogs from accumulating.
5. Review flagged formulas.
   - Confirm representational equivalence when source/readback structure and final MTEF/WMF support it.
   - Otherwise register a numbered narrow rule, build a one-formula or small focused test DOCX, and reprocess only affected indices.
   - Do not rerun the full batch.
6. After all high-risk review items are closed, use `merge_math_type_ole_into_original.py` to transplant only MathType runs, OLE binaries, WMF previews, and necessary relationships into the untouched original.
7. Validate the final DOCX and record any page-count/layout drift. Do not globally shrink or reposition formulas without user approval.

## Review policy

`ReviewQueue` is the default for full batches. The following are reviewable, not fatal:

- token mismatch;
- structure mismatch;
- MathML style mismatch;
- MTEF style mismatch;
- replacement characters in readback;
- unsupported or mixed accent-script geometry;
- WMF or baseline/layout anomalies.

`Strict` is for representative and special-rule regression only.

## Final acceptance

Require:

- final OMML count `0`;
- final inline `Equation.DSMT4` count equals the source OMML count;
- every formula is either automatically clean or explicitly closed in the AI review ledger;
- vector/matrix/identity/unit/function typography passes the final MTEF checks;
- all MathType WMF previews have zero red translator-error text;
- every supported accent-script risk has the expected recorded correction; unsupported cases have explicit AI conclusions;
- no `MT Extra` font remains; the configured Times New Roman/Euclid Extra profile is recognized;
- every formula's `EQN_PREFS` required ordinary style slots point to Times New Roman and Math Extra points to the Euclid Extra `FONT_DEF`;
- ZIP CRC and all XML parts parse;
- no original package part/media is removed or unexpectedly changed;
- only `[Content_Types].xml`, `word/document.xml`, and `word/_rels/document.xml.rels` change among original parts;
- canonical nonformula XML is identical;
- Word opens the final DOCX read-only with no revisions and the expected bookmark count;
- page count and layout drift are reported honestly.

## Output contract

Produce:

- untouched source and byte-identical backup;
- lightweight full donor source and completed MathType donor;
- JSONL conversion manifest and progress log;
- full formula-intermediate Markdown;
- AI review ledger Markdown and special-rule registry;
- donor/final WMF audit JSON;
- minimal-merge preservation report;
- distinct final DOCX;
- Word read-only validation result and page-count comparison.

Do not use intermediate DOCX files for human-readable source/processed formula ledgers; use Markdown. Focused DOCX files are allowed only for actual MathType behavior validation.

## Bundled V2 resources

- `scripts/mathtype_mathml_conversion/Invoke-OmmlMathMlToInlineMathTypeV2.ps1`
- `scripts/mathtype_mathml_conversion/WordMathTypeV2Converter.cs`
- `scripts/mathtype_mathml_conversion/OmmlMathMlTransformer.cs`
- `scripts/mathtype_mathml_conversion/MathMlCanonicalizer.cs`
- `scripts/mathtype_mathml_conversion/MathTypeReviewClassifier.cs`
- `scripts/mathtype_mathml_conversion/MathTypeDiagnosticPolicy.cs`
- `scripts/mathtype_mathml_conversion/MtefStyleAudit.cs`
- `scripts/mathtype_mathml_conversion/MtefFontProfileAudit.cs`
- `scripts/mathtype_mathml_conversion/OpcRelationshipTargetResolver.cs`
- `scripts/mathtype_mathml_conversion/Invoke-MathTypeMtefFontAudit.ps1`
- `scripts/mathtype_mathml_conversion/Test-MtefFontProfileAuditV2.ps1`
- `scripts/mathtype_mathml_conversion/Test-OpcRelationshipTargetResolver.ps1`
- `scripts/mathtype_mathml_conversion/New-RepresentativeOmmlTestDocument.ps1`
- `scripts/mathtype_mathml_conversion/Test-MathMlCanonicalizerV2.ps1`
- `scripts/mathtype_mathml_conversion/Test-MathTypeReviewClassifierV2.ps1`
- `scripts/mathtype_mathml_conversion/build_mathtype_v2_markdown.py`
- `scripts/mathtype_mathml_conversion/test_build_mathtype_v2_markdown.py`
- `scripts/mathtype_tex_conversion/MathTypeOleMtef.cs`
- `scripts/mathtype_tex_conversion/merge_math_type_ole_into_original.py`
- `scripts/mathtype_tex_conversion/mathtype_wmf_audit.py`
- `scripts/mathtype_tex_conversion/preferences/TimesNewRoman-EuclidExtra-10.eqp`
- `scripts/mathtype_tex_conversion/preferences/TimesNewRoman-EuclidExtra-12.eqp`
