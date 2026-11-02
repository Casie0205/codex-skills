# V2 workflow and command reference

Define distinct absolute paths. Use a dedicated run directory and preserve it.

## 1. Preflight

```powershell
$v2 = Join-Path $skillRoot 'scripts\mathtype_mathml_conversion'

& (Join-Path $v2 'Invoke-OmmlMathMlToInlineMathTypeV2.ps1') `
  -Mode Preflight `
  -SourcePath $sourceDocx `
  -ManifestPath $preflightManifest `
  -ProgressPath $preflightProgress
```

Confirm source hash, formula count, normalized MathML, structure/style signatures, and accent-script risk list.

## 2. Representative strict regression

Create a focused test DOCX from real source formula indices:

```powershell
& (Join-Path $v2 'New-RepresentativeOmmlTestDocument.ps1') `
  -SourcePath $sourceDocx `
  -OutputPath $representativeSource `
  -SourceIndices $representativeIndices

& (Join-Path $v2 'Invoke-OmmlMathMlToInlineMathTypeV2.ps1') `
  -Mode Convert `
  -ConversionPolicy Strict `
  -SourcePath $representativeSource `
  -OutputPath $representativeMathType `
  -ManifestPath $representativeManifest `
  -ProgressPath $representativeProgress
```

Run both regression scripts:

```powershell
& (Join-Path $v2 'Test-MathMlCanonicalizerV2.ps1')
& (Join-Path $v2 'Test-MathTypeReviewClassifierV2.ps1')
& (Join-Path $v2 'Test-MtefFontProfileAuditV2.ps1')
& (Join-Path $v2 'Test-OpcRelationshipTargetResolver.ps1')
python (Join-Path $v2 'test_build_mathtype_v2_markdown.py')
```

Audit all representative WMFs and visually inspect accent/script and other geometry-sensitive samples.

## 3. One full general batch

Prefer a lightweight DOCX containing all source OMML formulas in original order. It avoids a full Word resave of the large thesis and serves only as an OLE donor source.

```powershell
& (Join-Path $v2 'Invoke-OmmlMathMlToInlineMathTypeV2.ps1') `
  -Mode Convert `
  -ConversionPolicy ReviewQueue `
  -SourcePath $lightweightOmmlSource `
  -OutputPath $fullDonor `
  -ManifestPath $conversionManifest `
  -ProgressPath $conversionProgress
```

Do not stop or rerun the batch for token, structure, style, accent, or display mismatches. The converter records those differences and continues. Stop only for fatal OLE/save/count/package failures.

Some MathType TeX translators show modal warnings for otherwise valid internal accent characters, notably an ordinary-period `mover` that becomes U+02D9. `MathTypeDiagnosticPolicy` must skip TeX readback for those narrow patterns and retain MathML/MTEF verification. Do not dismiss repeated translator dialogs in a loop; stop the automation-owned MathType/hidden Word processes and fix the diagnostic policy.

## 4. Markdown intermediates and AI review

```powershell
python (Join-Path $v2 'build_mathtype_v2_markdown.py') `
  --manifest $conversionManifest `
  --intermediate-output $fullIntermediateMarkdown `
  --review-output $aiReviewLedger
```

For each flagged source index:

1. compare source and readback MathML;
2. inspect diagnostic TeX;
3. verify final MTEF typography;
4. inspect WMF or Word rendering when geometry matters;
5. mark it confirmed equivalent, or assign a numbered special rule;
6. if repair is needed, create a focused DOCX and reprocess only that index/set.

Never rerun the full donor because of a newly discovered special rule.

## 5. Donor and final WMF audits

```powershell
$shared = Join-Path $skillRoot 'scripts\mathtype_tex_conversion'

python (Join-Path $shared 'mathtype_wmf_audit.py') `
  --docx $fullDonor `
  --report $donorWmfAudit
```

Require the scanned count to equal the source formula count and red-error count to be zero. Non-red baseline or spacing issues still require visual review when flagged.

## 6. Embedded MTEF font-profile gate

Audit the completed donor and final DOCX by extracting every `Equation Native` stream:

```powershell
& (Join-Path $v2 'Invoke-MathTypeMtefFontAudit.ps1') `
  -DocumentPath $finalDocx `
  -ReportPath $mtefFontAudit `
  -ExpectedMathTypeObjectCount $sourceFormulaCount
```

The script must:

- resolve OLE relationships as internal OPC targets and reject external or wrong-type relationships;
- bind the report to the audited byte snapshot with document size and SHA-256;
- parse MTEF v5 `FONT_DEF` records, not search arbitrary OLE bytes;
- parse `EQN_PREFS`, require zero option bits, prove Text/Function/Variable/Vector/Number/User2 reference Times New Roman, and prove Math Extra references Euclid Extra;
- reject exact `MT Extra`, missing mappings, malformed MTEF, count mismatch, and any failed formula with a nonzero process exit.

MathType's global new-equation defaults are separate from preferences embedded in existing equations. A warning that MathType substitutes Euclid Extra can come from a global default that still names `MT Extra` even when every embedded equation passes. Never change the global default without explicit user authorization. If authorized, back it up, change only Math Extra, read the defaults back, and test a newly created equation.

## 7. Minimal package transplant

Proceed only after all high-risk AI-review items are closed.

```powershell
python (Join-Path $shared 'merge_math_type_ole_into_original.py') `
  --original $sourceDocx `
  --donor $fullDonor `
  --output $finalDocx `
  --report $packageReport
```

The merger must preserve every original part except the three necessary package parts and must prove canonical nonformula XML equality.

## 8. Final validation

- Audit all final WMFs again.
- Open the final DOCX in a hidden Word process with `ReadOnly=true`.
- Record pages, OMML count, MathType inline count, revisions, Track Changes, bookmarks, and abnormal object dimensions.
- Compare source/final page counts and representative page positions.
- Do not call the document layout-identical when pagination differs.
