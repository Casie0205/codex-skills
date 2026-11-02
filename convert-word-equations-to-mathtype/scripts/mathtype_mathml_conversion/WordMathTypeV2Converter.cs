using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Xml;
using ThesisMathTypeConversion;
using Word = Microsoft.Office.Interop.Word;

namespace ThesisMathTypeConversionV2
{
    public static class WordMathTypeV2Converter
    {
        private const string DocumentPart = "word/document.xml";
        private const int AccentScriptVerticalNudge = 32;

        public static V2ConversionSummary Preflight(
            string sourcePath,
            string manifestPath,
            string progressPath,
            string officeOmmlToMathMlXsltPath)
        {
            sourcePath = Path.GetFullPath(sourcePath);
            manifestPath = Path.GetFullPath(manifestPath);
            progressPath = Path.GetFullPath(progressPath);
            officeOmmlToMathMlXsltPath =
                Path.GetFullPath(officeOmmlToMathMlXsltPath);
            RequireExistingFile(sourcePath, "source DOCX");
            RequireDistinctPaths(
                sourcePath,
                manifestPath,
                progressPath);
            PrepareOutputFile(manifestPath);
            PrepareOutputFile(progressPath);
            WriteProgress(
                progressPath,
                "preflight",
                0,
                0,
                "reading source OMML directly from DOCX");

            IList<MathMlSnapshot> snapshots =
                ReadSnapshots(
                    sourcePath,
                    officeOmmlToMathMlXsltPath);
            using (StreamWriter manifest = CreateUtf8Writer(manifestPath))
            {
                WriteHeader(
                    manifest,
                    "preflight",
                    sourcePath,
                    ComputeSha256(sourcePath),
                    snapshots.Count,
                    "N/A");
                foreach (MathMlSnapshot snapshot in snapshots)
                {
                    WriteSnapshot(manifest, snapshot);
                }
            }
            WriteProgress(
                progressPath,
                "preflight",
                snapshots.Count,
                snapshots.Count,
                "MathML transformation complete");

            return new V2ConversionSummary
            {
                Mode = "preflight",
                SourcePath = sourcePath,
                SourceSha256 = ComputeSha256(sourcePath),
                SourceOmmlCount = snapshots.Count,
                ManifestPath = manifestPath,
                ProgressPath = progressPath,
                AccentScriptRiskCount =
                    CountAccentScriptRisks(snapshots)
            };
        }

        public static V2ConversionSummary Convert(
            string sourcePath,
            string outputPath,
            string backupPath,
            string manifestPath,
            string progressPath,
            string officeOmmlToMathMlXsltPath,
            string blankEquationPath,
            string preferencePath,
            string mathPageDirectory,
            V2ConversionPolicy conversionPolicy)
        {
            sourcePath = Path.GetFullPath(sourcePath);
            outputPath = Path.GetFullPath(outputPath);
            backupPath = String.IsNullOrWhiteSpace(backupPath)
                ? String.Empty
                : Path.GetFullPath(backupPath);
            manifestPath = Path.GetFullPath(manifestPath);
            progressPath = Path.GetFullPath(progressPath);
            officeOmmlToMathMlXsltPath =
                Path.GetFullPath(officeOmmlToMathMlXsltPath);
            blankEquationPath = Path.GetFullPath(blankEquationPath);
            preferencePath = Path.GetFullPath(preferencePath);
            mathPageDirectory = Path.GetFullPath(mathPageDirectory);
            RequireExistingFile(sourcePath, "source DOCX");
            RequireExistingFile(
                officeOmmlToMathMlXsltPath,
                "Office OMML2MML.XSL");
            RequireExistingFile(blankEquationPath, "blank MathType equation");
            RequireExistingFile(preferencePath, "MathType preference file");
            RequireDistinctPaths(
                sourcePath,
                outputPath,
                backupPath,
                manifestPath,
                progressPath);
            RequireNewPath(outputPath, "V2 output DOCX");
            if (!String.IsNullOrWhiteSpace(backupPath))
            {
                RequireNewPath(backupPath, "V2 backup DOCX");
            }
            PrepareOutputFile(manifestPath);
            PrepareOutputFile(progressPath);
            EnsureParentDirectory(outputPath);
            if (!String.IsNullOrWhiteSpace(backupPath))
            {
                EnsureParentDirectory(backupPath);
                File.Copy(sourcePath, backupPath, false);
            }
            File.Copy(sourcePath, outputPath, false);

            IList<MathMlSnapshot> snapshots =
                ReadSnapshots(
                    sourcePath,
                    officeOmmlToMathMlXsltPath);
            string sourceHash = ComputeSha256(sourcePath);
            int accentRiskCount = CountAccentScriptRisks(snapshots);
            int converted = 0;
            int canonicalMatches = 0;
            int tokenMatches = 0;
            int structureMatches = 0;
            int mathMlStyleMatches = 0;
            int mtefStyleMatches = 0;
            int mtefFontProfileMatches = 0;
            int accentCorrections = 0;
            int reviewRequiredCount = 0;
            bool saved = false;
            Word.Application app = null;
            Word.Document document = null;
            MathTypeApiSession mathType = null;
            StreamWriter manifest = null;
            IDisposable oleMessageFilter = null;

            try
            {
                oleMessageFilter = OleMessageFilter.Register();
                manifest = CreateUtf8Writer(manifestPath);
                WriteHeader(
                    manifest,
                    "convert",
                    sourcePath,
                    sourceHash,
                    snapshots.Count,
                    conversionPolicy.ToString());
                WriteProgress(
                    progressPath,
                    "convert",
                    0,
                    snapshots.Count,
                    "opening V2 donor document");

                app = WordV2Interop.CreateHiddenApplication();
                document = app.Documents.Open(
                    FileName: outputPath,
                    ConfirmConversions: false,
                    ReadOnly: false,
                    AddToRecentFiles: false,
                    Visible: false,
                    OpenAndRepair: false);
                mathType = new MathTypeApiSession(mathPageDirectory);

                int sourceCount = document.OMaths.Count;
                if (sourceCount != snapshots.Count)
                {
                    throw new InvalidDataException(
                        "Word reports " +
                        sourceCount +
                        " OMML equations but DOCX XML reports " +
                        snapshots.Count +
                        ".");
                }

                bool originalTrackRevisions = document.TrackRevisions;
                document.TrackRevisions = false;
                try
                {
                    for (int index = sourceCount;
                        index >= 1;
                        index--)
                    {
                        Word.OMath equation = null;
                        Word.Range equationRange = null;
                        Word.Range insertion = null;
                        Word.InlineShape shape = null;
                        object equationObject = null;
                        try
                        {
                            MathMlSnapshot snapshot = snapshots[index - 1];
                            equation = document.OMaths[index];
                            equationRange = equation.Range.Duplicate;
                            int start = equationRange.Start;
                            int end = equationRange.End;
                            equationRange.Delete();
                            insertion = document.Range(start, start);

                            int preferenceStatus =
                                mathType.ApplyPreferencesForNextInlineEquation(
                                    preferencePath);
                            MathTypeApiSession.ThrowIfMathTypeError(
                                preferenceStatus,
                                "MTSetMTPrefs for V2 equation " + index);

                            shape = WordV2Interop.InsertBlankMathType(
                                document,
                                start,
                                blankEquationPath);
                            equationObject =
                                WordV2Interop.ActivateAndGetEquationObject(
                                    shape);
                            MathTypeMathMlNativeBridge.SetEquationFromMathMl(
                                equationObject,
                                snapshot.NormalizedMathMl);

                            WordV2Interop.ReleaseComObject(equationObject);
                            equationObject =
                                WordV2Interop.ActivateAndGetEquationObject(
                                    shape);
                            byte[] initialMtef =
                                MathTypeMathMlNativeBridge.GetEquationMtef(
                                    equationObject);
                            IList<string> riskySuperscripts =
                                OmmlMathMlTransformer
                                    .GetAccentScriptSuperscripts(
                                        snapshot.NormalizedMathMl);
                            List<string> formulaIssueCodes =
                                new List<string>();
                            int equationAccentCorrections = 0;
                            if (riskySuperscripts.Count > 0)
                            {
                                bool accentRepairSupported = true;
                                if (riskySuperscripts[0].Length != 1 ||
                                    riskySuperscripts[0][0] > 0x7F ||
                                    !Char.IsLetterOrDigit(
                                        riskySuperscripts[0][0]))
                                {
                                    accentRepairSupported = false;
                                    formulaIssueCodes.Add(
                                        MathTypeReviewClassifier
                                            .AccentScriptUnsupported);
                                }
                                for (int riskIndex = 1;
                                    riskIndex < riskySuperscripts.Count;
                                    riskIndex++)
                                {
                                    if (!String.Equals(
                                        riskySuperscripts[0],
                                        riskySuperscripts[riskIndex],
                                        StringComparison.Ordinal))
                                    {
                                        accentRepairSupported = false;
                                        formulaIssueCodes.Add(
                                            MathTypeReviewClassifier
                                                .AccentScriptMixed);
                                        break;
                                    }
                                }

                                if (!accentRepairSupported &&
                                    conversionPolicy ==
                                        V2ConversionPolicy.Strict)
                                {
                                    throw new InvalidDataException(
                                        "Equation " +
                                        index +
                                        " has unsupported dot-accent " +
                                        "right-superscript geometry.");
                                }

                                if (accentRepairSupported)
                                {
                                    MtefAccentScriptNudgeResult correction =
                                        MathTypeOleMtef
                                            .NudgeDotAccentRightSuperscripts(
                                                initialMtef,
                                                riskySuperscripts.Count,
                                                AccentScriptVerticalNudge,
                                                riskySuperscripts[0][0]);

                                    int discardStatus =
                                        mathType.CloseWithoutSavingEquation(
                                            equationObject);
                                    MathTypeApiSession.ThrowIfMathTypeError(
                                        discardStatus,
                                        "MTCloseOleObject discard before V2 " +
                                        "accent correction for equation " +
                                        index);
                                    WordV2Interop.ReleaseComObject(
                                        equationObject);
                                    equationObject = null;
                                    WordV2Interop.DeleteInlineShape(shape);
                                    WordV2Interop.ReleaseComObject(shape);
                                    shape = null;

                                    int correctedPreferenceStatus =
                                        mathType
                                            .ApplyPreferencesForNextInlineEquation(
                                                preferencePath);
                                    MathTypeApiSession.ThrowIfMathTypeError(
                                        correctedPreferenceStatus,
                                        "MTSetMTPrefs for corrected V2 equation " +
                                        index);
                                    shape = WordV2Interop.InsertBlankMathType(
                                        document,
                                        start,
                                        blankEquationPath);
                                    equationObject =
                                        WordV2Interop
                                            .ActivateAndGetEquationObject(
                                                shape);
                                    MathTypeMathMlNativeBridge
                                        .SetEquationFromMtef(
                                            equationObject,
                                            correction.Mtef);
                                    equationAccentCorrections =
                                        correction.NudgedSuperscriptCount;
                                }
                                else
                                {
                                    formulaIssueCodes.Add(
                                        MathTypeReviewClassifier
                                            .AccentScriptUncorrected);
                                }
                            }

                            byte[] readbackMtef =
                                MathTypeMathMlNativeBridge.GetEquationMtef(
                                    equationObject);
                            string readbackMathMl =
                                MathTypeOleDataObject.GetMathMl(
                                    equationObject);
                            string readbackTex;
                            if (MathTypeDiagnosticPolicy
                                .ShouldSkipTexReadback(snapshot))
                            {
                                readbackTex =
                                    "[SKIPPED: MathType TeX translator " +
                                    "cannot export this known-unsafe " +
                                    "mover accent safely]";
                                formulaIssueCodes.Add(
                                    MathTypeReviewClassifier
                                        .TexReadbackSkippedPeriodAccent);
                            }
                            else
                            {
                                readbackTex =
                                    mathType.GetEquationAsTex(
                                        equationObject);
                            }
                            MathMlRoundTripResult roundTrip =
                                CompareRoundTrip(
                                    snapshot,
                                    readbackMathMl,
                                    readbackMtef);
                            roundTrip.ReviewIssueCodes =
                                MathTypeReviewClassifier.Classify(
                                    snapshot,
                                    roundTrip,
                                    formulaIssueCodes);
                            roundTrip.ReviewRequired =
                                roundTrip.ReviewIssueCodes.Count > 0;
                            roundTrip.Accepted =
                                !roundTrip.ReviewRequired;
                            WriteConversion(
                                manifest,
                                snapshot,
                                start,
                                end,
                                readbackMathMl,
                                readbackTex,
                                readbackMtef,
                                roundTrip);
                            if (roundTrip.ReviewRequired &&
                                conversionPolicy ==
                                    V2ConversionPolicy.Strict)
                            {
                                throw new InvalidDataException(
                                    "Equation " +
                                    index +
                                    " requires review in strict mode. " +
                                    "issueCodes=" +
                                    String.Join(
                                        ",",
                                        roundTrip.ReviewIssueCodes) +
                                    ".");
                            }

                            int closeStatus =
                                mathType.CloseAndSaveEquation(
                                    equationObject);
                            MathTypeApiSession.ThrowIfMathTypeError(
                                closeStatus,
                                "MTCloseOleObject for V2 equation " + index);
                            WordV2Interop.ReleaseComObject(equationObject);
                            equationObject = null;
                            WordV2Interop.UpdateEquationField(shape);
                            if (roundTrip.ReviewRequired)
                            {
                                reviewRequiredCount++;
                                WriteProgress(
                                    progressPath,
                                    "review",
                                    converted,
                                    sourceCount,
                                    "sourceIndex=" +
                                    index +
                                    ";issueCodes=" +
                                    String.Join(
                                        ",",
                                        roundTrip.ReviewIssueCodes));
                            }

                            if (roundTrip.CanonicalEqual)
                            {
                                canonicalMatches++;
                            }
                            if (roundTrip.TokenSequenceEqual)
                            {
                                tokenMatches++;
                            }
                            if (roundTrip.StructureSignatureEqual)
                            {
                                structureMatches++;
                            }
                            if (roundTrip.MtefStyleEqual)
                            {
                                mtefStyleMatches++;
                            }
                            if (roundTrip.MtefFontProfileAccepted)
                            {
                                mtefFontProfileMatches++;
                            }
                            if (roundTrip.StyleSequenceEqual)
                            {
                                mathMlStyleMatches++;
                            }
                            accentCorrections +=
                                equationAccentCorrections;
                        }
                        catch (Exception exception)
                        {
                            WriteProgress(
                                progressPath,
                                "error",
                                converted,
                                sourceCount,
                                "sourceIndex=" +
                                index +
                                ";exception=" +
                                exception.GetType().FullName +
                                ";message=" +
                                Sanitize(exception.Message));
                            throw;
                        }
                        finally
                        {
                            if (equationObject != null &&
                                mathType != null)
                            {
                                try
                                {
                                    mathType.CloseWithoutSavingEquation(
                                        equationObject);
                                }
                                catch
                                {
                                }
                            }
                            WordV2Interop.ReleaseComObject(equationObject);
                            WordV2Interop.ReleaseComObject(shape);
                            WordV2Interop.ReleaseComObject(insertion);
                            WordV2Interop.ReleaseComObject(equationRange);
                            WordV2Interop.ReleaseComObject(equation);
                        }

                        converted++;
                        if (converted == 1 ||
                            converted % 10 == 0 ||
                            converted == sourceCount)
                        {
                            WriteProgress(
                                progressPath,
                                "convert",
                                converted,
                                sourceCount,
                                "created verified inline MathType objects");
                        }
                    }

                    int remaining = document.OMaths.Count;
                    int mathTypeCount =
                        WordV2Interop.CountInlineMathTypeObjects(document);
                    bool objectCountGateFailed =
                        remaining != 0 ||
                        mathTypeCount != sourceCount ||
                        converted != sourceCount;
                    bool strictSemanticGateFailed =
                        conversionPolicy == V2ConversionPolicy.Strict &&
                        (tokenMatches != sourceCount ||
                        structureMatches != sourceCount ||
                        mathMlStyleMatches != sourceCount ||
                        mtefStyleMatches != sourceCount ||
                        mtefFontProfileMatches != sourceCount ||
                        accentCorrections != accentRiskCount);
                    if (objectCountGateFailed ||
                        strictSemanticGateFailed)
                    {
                        throw new InvalidDataException(
                            "V2 final object-count gate failed: remainingOMML=" +
                            remaining +
                            ";mathType=" +
                            mathTypeCount +
                            ";converted=" +
                            converted +
                            ";policy=" +
                            conversionPolicy +
                            ";tokenMatches=" +
                            tokenMatches +
                            ";structureMatches=" +
                            structureMatches +
                            ";mathMlStyleMatches=" +
                            mathMlStyleMatches +
                            ";mtefStyleMatches=" +
                            mtefStyleMatches +
                            ";mtefFontProfileMatches=" +
                            mtefFontProfileMatches +
                            ";accentRisks=" +
                            accentRiskCount +
                            ";accentCorrections=" +
                            accentCorrections +
                            ".");
                    }

                    document.TrackRevisions = originalTrackRevisions;
                    document.Save();
                    saved = true;

                    V2ConversionSummary summary =
                        new V2ConversionSummary
                        {
                            Mode = "convert",
                            ConversionPolicy =
                                conversionPolicy.ToString(),
                            SourcePath = sourcePath,
                            OutputPath = outputPath,
                            SourceSha256 = sourceHash,
                            SourceOmmlCount = sourceCount,
                            ConvertedCount = converted,
                            RemainingOmmlCount = remaining,
                            MathTypeInlineCount = mathTypeCount,
                            CanonicalMatchCount = canonicalMatches,
                            TokenMatchCount = tokenMatches,
                            StructuralMatchCount = structureMatches,
                            MathMlStyleMatchCount = mathMlStyleMatches,
                            MtefStyleMatchCount = mtefStyleMatches,
                            MtefFontProfileMatchCount =
                                mtefFontProfileMatches,
                            AccentScriptRiskCount = accentRiskCount,
                            AccentScriptCorrectionCount =
                                accentCorrections,
                            CleanConversionCount =
                                sourceCount - reviewRequiredCount,
                            ReviewRequiredCount =
                                reviewRequiredCount,
                            FatalErrorCount = 0,
                            PageCount = document.ComputeStatistics(
                                Word.WdStatistic.wdStatisticPages,
                                false),
                            RevisionCount = document.Revisions.Count,
                            TrackRevisions = document.TrackRevisions,
                            ManifestPath = manifestPath,
                            ProgressPath = progressPath
                        };
                    WriteSummary(manifest, summary);
                    WriteProgress(
                        progressPath,
                        "convert",
                        converted,
                        sourceCount,
                        "saved V2 donor;reviewRequired=" +
                        reviewRequiredCount);
                    return summary;
                }
                finally
                {
                    if (document != null)
                    {
                        try
                        {
                            document.TrackRevisions =
                                originalTrackRevisions;
                        }
                        catch
                        {
                        }
                    }
                }
            }
            finally
            {
                if (manifest != null)
                {
                    manifest.Dispose();
                }
                WordV2Interop.CloseDocumentWithoutSaving(document);
                WordV2Interop.ReleaseComObject(document);
                WordV2Interop.QuitApplication(app);
                WordV2Interop.ReleaseComObject(app);
                if (mathType != null)
                {
                    mathType.Dispose();
                }
                WordV2Interop.CollectComGarbage();
                if (oleMessageFilter != null)
                {
                    oleMessageFilter.Dispose();
                }
                if (!saved)
                {
                    WordV2Interop.DeleteFailedOutput(
                        outputPath,
                        delegate(string message)
                        {
                            WriteProgress(
                                progressPath,
                                "cleanup",
                                converted,
                                snapshots.Count,
                                message);
                        });
                }
            }
        }

        private static IList<MathMlSnapshot> ReadSnapshots(
            string sourcePath,
            string officeOmmlToMathMlXsltPath)
        {
            OmmlMathMlTransformer transformer =
                new OmmlMathMlTransformer(
                    officeOmmlToMathMlXsltPath);
            XmlDocument document = new XmlDocument();
            document.PreserveWhitespace = true;
            document.XmlResolver = null;
            using (ZipArchive archive = ZipFile.OpenRead(sourcePath))
            {
                ZipArchiveEntry entry = archive.GetEntry(DocumentPart);
                if (entry == null)
                {
                    throw new InvalidDataException(
                        "DOCX is missing " + DocumentPart + ".");
                }
                using (Stream stream = entry.Open())
                {
                    document.Load(stream);
                }
            }

            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace(
                "m",
                "http://schemas.openxmlformats.org/officeDocument/2006/math");
            XmlNodeList equations = document.SelectNodes(
                "//m:oMath[not(ancestor::m:oMath)]",
                namespaces);
            if (equations.Count == 0)
            {
                throw new InvalidDataException(
                    "Source DOCX contains no top-level OMML equations.");
            }

            List<MathMlSnapshot> snapshots =
                new List<MathMlSnapshot>(equations.Count);
            for (int index = 0; index < equations.Count; index++)
            {
                snapshots.Add(
                    transformer.Transform(
                        index + 1,
                        equations[index].OuterXml));
            }
            return snapshots;
        }

        private static MathMlRoundTripResult CompareRoundTrip(
            MathMlSnapshot source,
            string readbackMathMl,
            byte[] finalMtef)
        {
            MathMlCanonicalForm readback =
                MathMlCanonicalizer.Canonicalize(readbackMathMl);
            string matchedMtefStyleSequence =
                MtefStyleAudit.GetExpectedStyleSubsequence(
                    finalMtef,
                    source.ExpectedMtefCharacterStyleSequence);
            bool styleSequenceEqual =
                MathMlCanonicalizer.AreStyleSequencesEquivalent(
                    source.StyleSequence,
                    readback.StyleSequence);
            MtefFontProfileAuditResult fontProfile =
                MtefFontProfileAudit.Inspect(finalMtef);
            return new MathMlRoundTripResult
            {
                ReadbackMathMl = readbackMathMl,
                CanonicalMathMl = readback.Xml,
                CanonicalSha256 = readback.Sha256,
                TokenSequence = readback.TokenSequence,
                StructureSignature = readback.StructureSignature,
                StyleSequence = readback.StyleSequence,
                CanonicalEqual = String.Equals(
                    source.CanonicalSha256,
                    readback.Sha256,
                    StringComparison.Ordinal),
                TokenSequenceEqual = String.Equals(
                    source.TokenSequence,
                    readback.TokenSequence,
                    StringComparison.Ordinal),
                StructureSignatureEqual = String.Equals(
                    source.StructureSignature,
                    readback.StructureSignature,
                    StringComparison.Ordinal),
                ExpectedStyledCharacterCount =
                    source.ExpectedStyledCharacterCount,
                ReadbackStyledCharacterCount =
                    readback.StyledCharacterCount,
                ReadbackStyleCountEqual =
                    source.ExpectedStyledCharacterCount ==
                    readback.StyledCharacterCount,
                StyleSequenceEqual = styleSequenceEqual,
                MtefCharacterStyleSequence =
                    matchedMtefStyleSequence,
                MtefStyleEqual = String.Equals(
                    source.ExpectedMtefCharacterStyleSequence,
                    matchedMtefStyleSequence,
                    StringComparison.Ordinal),
                MtefHasTimesNewRoman =
                    fontProfile.HasTimesNewRoman,
                MtefHasEuclidExtra =
                    fontProfile.HasEuclidExtra,
                MtefHasLegacyMtExtra =
                    fontProfile.HasLegacyMtExtra,
                MtefRequiredStylesUseTimesNewRoman =
                    fontProfile.RequiredStylesUseTimesNewRoman,
                MtefMathExtraUsesEuclidExtra =
                    fontProfile.MathExtraStyleUsesEuclidExtra,
                MtefFontProfileAccepted =
                    fontProfile.Accepted,
                Accepted =
                    String.Equals(
                        source.TokenSequence,
                        readback.TokenSequence,
                        StringComparison.Ordinal) &&
                    String.Equals(
                        source.StructureSignature,
                        readback.StructureSignature,
                        StringComparison.Ordinal) &&
                    styleSequenceEqual &&
                    String.Equals(
                        source.ExpectedMtefCharacterStyleSequence,
                        matchedMtefStyleSequence,
                        StringComparison.Ordinal) &&
                    fontProfile.Accepted
            };
        }

        private static int CountAccentScriptRisks(
            IEnumerable<MathMlSnapshot> snapshots)
        {
            int count = 0;
            foreach (MathMlSnapshot snapshot in snapshots)
            {
                count += OmmlMathMlTransformer.CountAccentScriptRisks(
                    snapshot.NormalizedMathMl);
            }
            return count;
        }

        private static void WriteHeader(
            StreamWriter writer,
            string mode,
            string sourcePath,
            string sourceHash,
            int count,
            string conversionPolicy)
        {
            writer.WriteLine(
                "{\"type\":\"header\",\"mode\":\"" +
                EscapeJson(mode) +
                "\",\"sourcePath\":\"" +
                EscapeJson(sourcePath) +
                "\",\"sourceSha256\":\"" +
                EscapeJson(sourceHash) +
                "\",\"sourceOmmlCount\":" +
                count.ToString(CultureInfo.InvariantCulture) +
                ",\"conversionPolicy\":\"" +
                EscapeJson(conversionPolicy) +
                "\"" +
                "}");
            writer.Flush();
        }

        private static void WriteSnapshot(
            StreamWriter writer,
            MathMlSnapshot snapshot)
        {
            writer.WriteLine(
                "{\"type\":\"formula\",\"sourceIndex\":" +
                snapshot.SourceIndex.ToString(CultureInfo.InvariantCulture) +
                ",\"rawMathMl\":\"" +
                EscapeJson(snapshot.RawMathMl) +
                "\",\"normalizedMathMl\":\"" +
                EscapeJson(snapshot.NormalizedMathMl) +
                "\",\"canonicalMathMl\":\"" +
                EscapeJson(snapshot.CanonicalMathMl) +
                "\",\"canonicalSha256\":\"" +
                EscapeJson(snapshot.CanonicalSha256) +
                "\",\"tokenSequence\":\"" +
                EscapeJson(snapshot.TokenSequence) +
                "\",\"structureSignature\":\"" +
                EscapeJson(snapshot.StructureSignature) +
                "\",\"styleSequence\":\"" +
                EscapeJson(snapshot.StyleSequence) +
                "\",\"features\":\"" +
                EscapeJson(String.Join(",", snapshot.Features)) +
                "\",\"expectedStyledCharacterCount\":" +
                snapshot.ExpectedStyledCharacterCount.ToString(
                    CultureInfo.InvariantCulture) +
                ",\"expectedMtefCharacterStyleSequence\":\"" +
                EscapeJson(
                    snapshot.ExpectedMtefCharacterStyleSequence) +
                "\",\"accentScriptRiskCount\":" +
                snapshot.AccentScriptRiskCount.ToString(
                    CultureInfo.InvariantCulture) +
                "}");
            writer.Flush();
        }

        private static void WriteConversion(
            StreamWriter writer,
            MathMlSnapshot snapshot,
            int start,
            int end,
            string readbackMathMl,
            string readbackTex,
            byte[] readbackMtef,
            MathMlRoundTripResult roundTrip)
        {
            writer.WriteLine(
                "{\"type\":\"formula\",\"sourceIndex\":" +
                snapshot.SourceIndex.ToString(CultureInfo.InvariantCulture) +
                ",\"wordStart\":" +
                start.ToString(CultureInfo.InvariantCulture) +
                ",\"wordEnd\":" +
                end.ToString(CultureInfo.InvariantCulture) +
                ",\"normalizedMathMl\":\"" +
                EscapeJson(snapshot.NormalizedMathMl) +
                "\",\"expectedCanonicalSha256\":\"" +
                EscapeJson(snapshot.CanonicalSha256) +
                "\",\"readbackMathMl\":\"" +
                EscapeJson(readbackMathMl) +
                "\",\"readbackTex\":\"" +
                EscapeJson(readbackTex) +
                "\",\"readbackMtefLength\":" +
                readbackMtef.Length.ToString(CultureInfo.InvariantCulture) +
                ",\"readbackMtefSha256\":\"" +
                ComputeSha256(readbackMtef) +
                "\",\"readbackCanonicalSha256\":\"" +
                EscapeJson(roundTrip.CanonicalSha256) +
                "\",\"canonicalEqual\":" +
                roundTrip.CanonicalEqual.ToString().ToLowerInvariant() +
                ",\"tokenEqual\":" +
                roundTrip.TokenSequenceEqual.ToString().ToLowerInvariant() +
                ",\"structureEqual\":" +
                roundTrip.StructureSignatureEqual.ToString().ToLowerInvariant() +
                ",\"styleEqual\":" +
                roundTrip.StyleSequenceEqual.ToString().ToLowerInvariant() +
                ",\"expectedStyledCharacterCount\":" +
                roundTrip.ExpectedStyledCharacterCount.ToString(
                    CultureInfo.InvariantCulture) +
                ",\"readbackStyledCharacterCount\":" +
                roundTrip.ReadbackStyledCharacterCount.ToString(
                    CultureInfo.InvariantCulture) +
                ",\"readbackStyleCountEqual\":" +
                roundTrip.ReadbackStyleCountEqual.ToString().ToLowerInvariant() +
                ",\"mtefCharacterStyleSequence\":\"" +
                EscapeJson(roundTrip.MtefCharacterStyleSequence) +
                "\",\"mtefStyleEqual\":" +
                roundTrip.MtefStyleEqual.ToString().ToLowerInvariant() +
                ",\"mtefHasTimesNewRoman\":" +
                roundTrip.MtefHasTimesNewRoman
                    .ToString()
                    .ToLowerInvariant() +
                ",\"mtefHasEuclidExtra\":" +
                roundTrip.MtefHasEuclidExtra
                    .ToString()
                    .ToLowerInvariant() +
                ",\"mtefHasLegacyMtExtra\":" +
                roundTrip.MtefHasLegacyMtExtra
                    .ToString()
                    .ToLowerInvariant() +
                ",\"mtefRequiredStylesUseTimesNewRoman\":" +
                roundTrip.MtefRequiredStylesUseTimesNewRoman
                    .ToString()
                    .ToLowerInvariant() +
                ",\"mtefMathExtraUsesEuclidExtra\":" +
                roundTrip.MtefMathExtraUsesEuclidExtra
                    .ToString()
                    .ToLowerInvariant() +
                ",\"mtefFontProfileAccepted\":" +
                roundTrip.MtefFontProfileAccepted
                    .ToString()
                    .ToLowerInvariant() +
                ",\"reviewRequired\":" +
                roundTrip.ReviewRequired.ToString().ToLowerInvariant() +
                ",\"reviewIssueCodes\":\"" +
                EscapeJson(
                    roundTrip.ReviewIssueCodes == null
                        ? String.Empty
                        : String.Join(
                            ",",
                            roundTrip.ReviewIssueCodes)) +
                "\"" +
                ",\"accepted\":" +
                roundTrip.Accepted.ToString().ToLowerInvariant() +
                "}");
            writer.Flush();
        }

        private static void WriteSummary(
            StreamWriter writer,
            V2ConversionSummary summary)
        {
            writer.WriteLine(
                "{\"type\":\"summary\",\"sourceOmmlCount\":" +
                summary.SourceOmmlCount +
                ",\"conversionPolicy\":\"" +
                EscapeJson(summary.ConversionPolicy) +
                "\"" +
                ",\"convertedCount\":" +
                summary.ConvertedCount +
                ",\"remainingOmmlCount\":" +
                summary.RemainingOmmlCount +
                ",\"mathTypeInlineCount\":" +
                summary.MathTypeInlineCount +
                ",\"canonicalMatchCount\":" +
                summary.CanonicalMatchCount +
                ",\"tokenMatchCount\":" +
                summary.TokenMatchCount +
                ",\"structureMatchCount\":" +
                summary.StructuralMatchCount +
                ",\"mathMlStyleMatchCount\":" +
                summary.MathMlStyleMatchCount +
                ",\"mtefStyleMatchCount\":" +
                summary.MtefStyleMatchCount +
                ",\"mtefFontProfileMatchCount\":" +
                summary.MtefFontProfileMatchCount +
                ",\"accentScriptRiskCount\":" +
                summary.AccentScriptRiskCount +
                ",\"accentScriptCorrectionCount\":" +
                summary.AccentScriptCorrectionCount +
                ",\"cleanConversionCount\":" +
                summary.CleanConversionCount +
                ",\"reviewRequiredCount\":" +
                summary.ReviewRequiredCount +
                ",\"fatalErrorCount\":" +
                summary.FatalErrorCount +
                "}");
            writer.Flush();
        }

        private static void WriteProgress(
            string progressPath,
            string stage,
            int completed,
            int total,
            string message)
        {
            EnsureParentDirectory(progressPath);
            File.AppendAllText(
                progressPath,
                DateTime.Now.ToString("o") +
                "\tstage=" +
                stage +
                "\tcompleted=" +
                completed.ToString(CultureInfo.InvariantCulture) +
                "\ttotal=" +
                total.ToString(CultureInfo.InvariantCulture) +
                "\tmessage=" +
                Sanitize(message) +
                Environment.NewLine,
                new UTF8Encoding(false));
        }

        private static StreamWriter CreateUtf8Writer(string path)
        {
            EnsureParentDirectory(path);
            return new StreamWriter(
                new FileStream(
                    path,
                    FileMode.Create,
                    FileAccess.Write,
                    FileShare.Read),
                new UTF8Encoding(false));
        }

        private static void PrepareOutputFile(string path)
        {
            if (String.IsNullOrWhiteSpace(path))
            {
                throw new ArgumentException("Output path is required.");
            }
            EnsureParentDirectory(path);
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }

        private static void EnsureParentDirectory(string path)
        {
            string parent = Path.GetDirectoryName(
                Path.GetFullPath(path));
            if (!String.IsNullOrEmpty(parent))
            {
                Directory.CreateDirectory(parent);
            }
        }

        private static void RequireExistingFile(
            string path,
            string label)
        {
            if (String.IsNullOrWhiteSpace(path) ||
                !File.Exists(path))
            {
                throw new FileNotFoundException(
                    label + " was not found.",
                    path);
            }
        }

        private static void RequireNewPath(string path, string label)
        {
            if (String.IsNullOrWhiteSpace(path))
            {
                throw new ArgumentException(label + " path is required.");
            }
            if (File.Exists(path) || Directory.Exists(path))
            {
                throw new IOException(
                    label + " already exists: " + path);
            }
        }

        private static void RequireDistinctPaths(params string[] paths)
        {
            HashSet<string> normalized =
                new HashSet<string>(
                    StringComparer.OrdinalIgnoreCase);
            foreach (string path in paths)
            {
                if (String.IsNullOrWhiteSpace(path))
                {
                    continue;
                }
                string full = Path.GetFullPath(path);
                if (!normalized.Add(full))
                {
                    throw new InvalidOperationException(
                        "All V2 source and output paths must be distinct: " +
                        full);
                }
            }
        }

        private static string ComputeSha256(string path)
        {
            using (SHA256 sha = SHA256.Create())
            using (Stream stream = File.OpenRead(path))
            {
                byte[] hash = sha.ComputeHash(stream);
                StringBuilder value = new StringBuilder(hash.Length * 2);
                foreach (byte item in hash)
                {
                    value.Append(item.ToString("x2"));
                }
                return value.ToString();
            }
        }

        private static string ComputeSha256(byte[] value)
        {
            using (SHA256 sha = SHA256.Create())
            {
                byte[] hash = sha.ComputeHash(value);
                StringBuilder text = new StringBuilder(hash.Length * 2);
                foreach (byte item in hash)
                {
                    text.Append(item.ToString("x2"));
                }
                return text.ToString();
            }
        }

        private static string Sanitize(string value)
        {
            return String.IsNullOrEmpty(value)
                ? String.Empty
                : value
                    .Replace("\r", " ")
                    .Replace("\n", " ")
                    .Replace("\t", " ");
        }

        private static string EscapeJson(string value)
        {
            if (value == null)
            {
                return String.Empty;
            }
            StringBuilder escaped = new StringBuilder(value.Length + 16);
            foreach (char character in value)
            {
                switch (character)
                {
                    case '"':
                        escaped.Append("\\\"");
                        break;
                    case '\\':
                        escaped.Append("\\\\");
                        break;
                    case '\b':
                        escaped.Append("\\b");
                        break;
                    case '\f':
                        escaped.Append("\\f");
                        break;
                    case '\n':
                        escaped.Append("\\n");
                        break;
                    case '\r':
                        escaped.Append("\\r");
                        break;
                    case '\t':
                        escaped.Append("\\t");
                        break;
                    default:
                        if (character < 32)
                        {
                            escaped.Append(
                                "\\u" +
                                ((int)character).ToString("x4"));
                        }
                        else
                        {
                            escaped.Append(character);
                        }
                        break;
                }
            }
            return escaped.ToString();
        }
    }
}
