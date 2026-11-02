# V2 validation contract

## General batch completion

- Source formula count and SHA-256 are recorded.
- Every source formula produces one editable inline `Equation.DSMT4` object.
- Final donor OMML count is zero and MathType count equals the source count.
- Fatal error count is zero.
- Every non-clean formula appears in the AI review ledger with risk codes.

## Formula correctness

- Compare token sequence, parent/slot-preserving structure signature, MathML style sequence, and final MTEF style separately.
- Ordinary vectors/matrices are MTEF `BI`.
- Identity matrix `I` is MTEF `B`.
- Units, functions/operators, transpose `T`, and operator differentials remain upright.
- Automatically clean formulas pass all relevant comparisons.
- Review-queue formulas have an explicit AI conclusion or a tested special-rule repair.
- Representation-only differences may be accepted only with source/readback evidence; never hide replacement characters, missing symbols, changed attachment, or changed mathematical semantics.
- Diagnostic TeX is optional when MathType's translator is known to raise a modal warning for a valid internal accent. Record the skip reason and rely on MathML, MTEF, and WMF evidence; never leave a translator-dialog loop running.

## Accent and script geometry

- Enumerate dot/double-dot accent bases carrying right superscripts.
- Automatic MTEF repair is allowed only for the validated narrow structure.
- Record expected risk and correction counts.
- Visually inspect geometry-sensitive formulas; semantic round-trip and red-WMF checks cannot detect a raised script or misplaced combining accent.
- Never move a script inside an accent argument without proving semantic and visual equivalence.

## WMF display

- Scan every generated WMF for MathType translator-error red.
- Scanned WMF count equals the formula count.
- Red-error count is zero for representative, donor, and final documents.
- Review non-red baseline, clipping, spacing, and accent placement when the ledger or visual sample indicates risk.

## Fonts

- Apply the bundled Times New Roman/Euclid Extra preference before every equation.
- Extract each OLE object's `Equation Native` stream and parse MTEF v5 record type 17 `FONT_DEF`; do not accept compressed-OLE visible-string scans.
- Require exact Times New Roman and Euclid Extra definitions, no exact `MT Extra`, zero `EQN_PREFS` option bits, Text/Function/Variable/Vector/Number/User2 references to Times New Roman, and a Math Extra reference to Euclid Extra.
- Bind the audit to document SHA-256, byte size, and expected MathType object count. Any rejection or count mismatch must return a nonzero process exit after writing the report.
- Treat global MathType new-equation defaults and embedded equation preferences separately. Do not change global defaults or system fonts merely to suppress a warning without separate user approval.

## DOCX preservation

- ZIP CRC passes and every XML part parses.
- No original part is removed.
- Exactly one OLE binary and one WMF preview are added per formula.
- Original media remain byte-identical.
- Among original parts, only `[Content_Types].xml`, `word/document.xml`, and `word/_rels/document.xml.rels` may change.
- Canonical nonformula `word/document.xml` is identical.
- Source, donor, and final paths are distinct; publish final output atomically.

## Word read-only acceptance

- Final Word open succeeds with `ReadOnly=true`.
- OMML is zero and inline MathType count equals the source formula count.
- Revisions remain zero and Track Changes remains off.
- Bookmark and field counts have no unexplained changes.
- Record source/final page counts and any abnormal inline object dimensions.

## Failure policy

Fatal failures stop and invalidate the output:

- OLE creation, activation, close, or save failure;
- Word save failure;
- object-count loss;
- malformed or corrupt DOCX package;
- inability to preserve source package boundaries.

Reviewable differences do not stop the full batch:

- token, structure, MathML style, or MTEF style mismatch;
- replacement characters;
- unsupported accent/script geometry;
- WMF or layout anomalies.

Keep those outputs labelled as donors/intermediates until AI review is closed. Repair only affected indices and never replace a failed formula with guessed text or a visual-only image.
