using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Xml;
using Office = Microsoft.Office.Core;
using Word = Microsoft.Office.Interop.Word;

namespace ThesisMathTypeConversion
{
    public sealed class ConversionSummary
    {
        public string Mode { get; set; }
        public string SourcePath { get; set; }
        public string OutputPath { get; set; }
        public string SourceSha256 { get; set; }
        public int SourceOmmlCount { get; set; }
        public int ConvertedCount { get; set; }
        public int RemainingOmmlCount { get; set; }
        public int MathTypeInlineCount { get; set; }
        public int NativeApiVersion { get; set; }
        public int PageCount { get; set; }
        public int FieldCount { get; set; }
        public int BookmarkCount { get; set; }
        public int RevisionCount { get; set; }
        public bool TrackRevisions { get; set; }
        public double MathTypeMaxWidthPoints { get; set; }
        public double MathTypeMaxHeightPoints { get; set; }
        public int MathTypeWiderThan500PointsCount { get; set; }
        public long OutputBytes { get; set; }
        public string ManifestPath { get; set; }
        public string ProgressPath { get; set; }
        public string PackageValidation { get; set; }
        public int AccentScriptRiskCount { get; set; }
        public int AccentScriptMtefNudgeCount { get; set; }
    }

    public static class WordOmmlMathTypeConverter
    {
        private sealed class MathTypeObjectMetrics
        {
            public int Count { get; set; }
            public double MaxWidthPoints { get; set; }
            public double MaxHeightPoints { get; set; }
            public int WiderThan500PointsCount { get; set; }
        }

        private sealed class AccentScriptCorrectionStatus
        {
            public int PreferenceStatus { get; set; }
            public int SetStatus { get; set; }
            public int CloseStatus { get; set; }
            public int NudgedSuperscriptCount { get; set; }
        }

        private const string MathTypeProgId = "Equation.DSMT4";
        private const string BlankEquationBookmark = "MTBlankEqn";
        private const int EmbeddedEquationSearchWidth = 27;
        private const int AccentScriptVerticalNudge = 32;

        public static ConversionSummary Preflight(
            string sourcePath,
            string manifestPath,
            string progressPath)
        {
            RequireExistingFile(sourcePath, "source document");
            RequireDistinctPaths(
                "preflight",
                sourcePath,
                manifestPath,
                progressPath);
            PrepareOutputFile(manifestPath);
            PrepareOutputFile(progressPath);

            string sourceHash = ComputeSha256(sourcePath);
            Word.Application app = null;
            Word.Document document = null;
            StreamWriter manifest = null;

            try
            {
                WriteProgress(progressPath, "preflight", 0, 0, "opening source document");
                app = CreateHiddenWordApplication();
                document = OpenDocument(app, sourcePath, true);
                int total = document.OMaths.Count;
                int accentScriptRiskCount = 0;

                manifest = CreateManifestWriter(manifestPath);
                WriteManifestHeader(
                    manifest,
                    "preflight",
                    sourcePath,
                    null,
                    sourceHash,
                    total,
                    0);

                for (int index = total; index >= 1; index--)
                {
                    Word.OMath equation = null;
                    Word.Range equationRange = null;
                    try
                    {
                        equation = document.OMaths[index];
                        equationRange = equation.Range;
                        int start = equationRange.Start;
                        int end = equationRange.End;
                        int storyType = (int)equationRange.StoryType;
                        string context = GetContext(document, start, end);
                        ReleaseComObject(equationRange);
                        equationRange = null;
                        TexExportSnapshot tex = ExportEquationAsTex(app, equation);
                        EnsureNonEmptyTex(tex.NormalizedTex, index, start);
                        accentScriptRiskCount += tex.AccentScriptRiskCount;

                        WriteFormulaManifest(
                            manifest,
                            index,
                            start,
                            end,
                            storyType,
                            context,
                            tex,
                            null,
                            null,
                            null,
                            null,
                            null);
                    }
                    finally
                    {
                        ReleaseComObject(equationRange);
                        ReleaseComObject(equation);
                    }

                    int completed = total - index + 1;
                    if (completed == 1 || completed % 10 == 0 || completed == total)
                    {
                        WriteProgress(
                            progressPath,
                            "preflight",
                            completed,
                            total,
                            "exported Word equations to TeX in memory");
                    }
                }

                WriteManifestSummary(
                    manifest,
                    total,
                    total,
                    document.OMaths.Count,
                    0,
                    accentScriptRiskCount,
                    0);

                ConversionSummary summary = CreateWordSummary(
                    "preflight",
                    sourcePath,
                    null,
                    sourceHash,
                    total,
                    total,
                    document,
                    0,
                    new MathTypeObjectMetrics(),
                    manifestPath,
                    progressPath);
                summary.AccentScriptRiskCount = accentScriptRiskCount;
                return summary;
            }
            finally
            {
                if (manifest != null)
                {
                    manifest.Dispose();
                }

                CloseDocumentWithoutSaving(document);
                ReleaseComObject(document);
                QuitWord(app);
                ReleaseComObject(app);
                CollectComGarbage();
            }
        }

        public static ConversionSummary Convert(
            string sourcePath,
            string outputPath,
            string backupPath,
            string manifestPath,
            string progressPath,
            string mathPageDirectory,
            string blankEquationPath,
            string preferencePath)
        {
            return Convert(
                sourcePath,
                outputPath,
                backupPath,
                manifestPath,
                progressPath,
                mathPageDirectory,
                blankEquationPath,
                preferencePath,
                false);
        }

        public static ConversionSummary Convert(
            string sourcePath,
            string outputPath,
            string backupPath,
            string manifestPath,
            string progressPath,
            string mathPageDirectory,
            string blankEquationPath,
            string preferencePath,
            bool allowAccentScriptRisks)
        {
            RequireExistingFile(sourcePath, "source document");
            RequireExistingFile(blankEquationPath, "MathType blank equation template");
            RequireExistingFile(preferencePath, "MathType preference file");
            RequireExistingDirectory(mathPageDirectory, "MathType MathPage directory");
            RequireDistinctPaths(
                "conversion",
                sourcePath,
                outputPath,
                backupPath,
                manifestPath,
                progressPath);
            RequireNewPath(outputPath, "output document");
            if (!String.IsNullOrWhiteSpace(backupPath))
            {
                RequireNewPath(backupPath, "backup document");
            }

            PrepareOutputFile(manifestPath);
            PrepareOutputFile(progressPath);
            EnsureParentDirectory(outputPath);
            if (!String.IsNullOrWhiteSpace(backupPath))
            {
                EnsureParentDirectory(backupPath);
            }

            string sourceHash = ComputeSha256(sourcePath);
            if (!String.IsNullOrWhiteSpace(backupPath))
            {
                File.Copy(sourcePath, backupPath, false);
            }
            File.Copy(sourcePath, outputPath, false);

            Word.Application app = null;
            Word.Document document = null;
            MathTypeApiSession mathType = null;
            StreamWriter manifest = null;
            int converted = 0;
            int sourceOmmlCount = 0;
            int accentScriptRiskCount = 0;
            int accentScriptMtefNudgeCount = 0;
            bool saved = false;
            bool originalTrackRevisions = false;

            try
            {
                WriteProgress(progressPath, "convert", 0, 0, "opening candidate document");
                mathType = new MathTypeApiSession(mathPageDirectory);
                app = CreateHiddenWordApplication();
                document = OpenDocument(app, outputPath, false);
                originalTrackRevisions = document.TrackRevisions;
                document.TrackRevisions = false;
                sourceOmmlCount = document.OMaths.Count;

                manifest = CreateManifestWriter(manifestPath);
                WriteManifestHeader(
                    manifest,
                    "convert",
                    sourcePath,
                    outputPath,
                    sourceHash,
                    sourceOmmlCount,
                    mathType.NativeVersion);

                for (int index = sourceOmmlCount; index >= 1; index--)
                {
                    Word.OMath equation = null;
                    Word.Range equationRange = null;
                    Word.Range insertionRange = null;
                    Word.InlineShape mathTypeShape = null;
                    object equationObject = null;
                    string operation = "load Word equation";

                    try
                    {
                        equation = document.OMaths[index];
                        equationRange = equation.Range;
                        int start = equationRange.Start;
                        int end = equationRange.End;
                        int storyType = (int)equationRange.StoryType;
                        string context = GetContext(document, start, end);
                        ReleaseComObject(equationRange);
                        equationRange = null;
                        operation = "export Word equation as normalized TeX";
                        TexExportSnapshot tex = ExportEquationAsTex(app, equation);
                        EnsureNonEmptyTex(tex.NormalizedTex, index, start);
                        accentScriptRiskCount += tex.AccentScriptRiskCount;

                        operation = "delete Word equation and insert blank MathType object";
                        Word.Range convertedEquationRange = null;
                        try
                        {
                            convertedEquationRange = equation.Range;
                            insertionRange = convertedEquationRange.Duplicate;
                        }
                        finally
                        {
                            ReleaseComObject(convertedEquationRange);
                        }
                        insertionRange.Delete();
                        insertionRange.SetRange(start, start);
                        insertionRange.InsertFile(
                            blankEquationPath,
                            BlankEquationBookmark,
                            false,
                            false,
                            false);
                        DeleteBlankEquationBookmark(document);

                        int searchEnd = Math.Min(
                            document.Content.End - 1,
                            start + EmbeddedEquationSearchWidth);
                        insertionRange.SetRange(start, searchEnd);
                        operation = "locate inserted inline MathType object";
                        mathTypeShape = FindInsertedMathTypeShape(insertionRange, start);
                        if (mathTypeShape == null)
                        {
                            throw new InvalidOperationException(
                                "Could not locate the inserted inline MathType object at Word range " +
                                start + ".");
                        }

                        int preferenceStatus;
                        int setStatus;
                        int closeStatus;
                        if (tex.AccentScriptRiskCount > 0 &&
                            !allowAccentScriptRisks)
                        {
                            operation =
                                "generate corrected MathType accent-script equation";
                            AccentScriptCorrectionStatus correction =
                                CorrectAccentScriptGeometry(
                                document,
                                mathTypeShape,
                                mathType,
                                outputPath,
                                index,
                                tex,
                                blankEquationPath,
                                preferencePath);
                            preferenceStatus =
                                correction.PreferenceStatus;
                            setStatus = correction.SetStatus;
                            closeStatus = correction.CloseStatus;
                            tex.AccentScriptMtefNudgeCount =
                                correction.NudgedSuperscriptCount;
                            accentScriptMtefNudgeCount +=
                                correction.NudgedSuperscriptCount;
                        }
                        else
                        {
                            operation = "apply MathType equation preferences";
                            preferenceStatus =
                                mathType.ApplyPreferencesForNextInlineEquation(
                                    preferencePath);
                            MathTypeApiSession.ThrowIfMathTypeError(
                                preferenceStatus,
                                "MTSetMTPrefs for equation " + index);

                            operation = "activate inline MathType object";
                            equationObject =
                                ActivateAndGetEquationObject(mathTypeShape);
                            operation =
                                "write normalized TeX through MathType API";
                            setStatus = mathType.SetEquationFromInlineTex(
                                equationObject,
                                tex.NormalizedTex);
                            MathTypeApiSession.ThrowIfMathTypeError(
                                setStatus,
                                "MTSetEqnFromLangStr for equation " + index);

                            operation = "close and save MathType object";
                            closeStatus =
                                mathType.CloseAndSaveEquation(equationObject);
                            MathTypeApiSession.ThrowIfMathTypeError(
                                closeStatus,
                                "MTCloseOleObject for equation " + index);
                            ReleaseComObject(equationObject);
                            equationObject = null;

                            operation = "refresh embedded equation field";
                            UpdateEquationFieldWithRetry(mathTypeShape);
                        }

                        operation = "verify inserted MathType object";
                        string progId = GetProgIdWithRetry(mathTypeShape);
                        Word.Range finalShapeRange = mathTypeShape.Range;
                        int finalStart = finalShapeRange.Start;
                        int finalEnd = finalShapeRange.End;
                        ReleaseComObject(finalShapeRange);

                        WriteFormulaManifest(
                            manifest,
                            index,
                            start,
                            end,
                            storyType,
                            context,
                            tex,
                            preferenceStatus,
                            setStatus,
                            closeStatus,
                            progId,
                            finalStart + "-" + finalEnd);
                    }
                    catch (Exception exception)
                    {
                        WriteProgress(
                            progressPath,
                            "error",
                            converted,
                            sourceOmmlCount,
                            "sourceIndex=" + index +
                            ";operation=" + operation +
                            ";exception=" + exception.GetType().FullName +
                            ";message=" + SanitizeProgressMessage(exception.Message));
                        throw new InvalidOperationException(
                            "Equation " + index +
                            " failed while attempting to " + operation + ".",
                            exception);
                    }
                    finally
                    {
                        ReleaseComObject(equationObject);
                        ReleaseComObject(mathTypeShape);
                        ReleaseComObject(insertionRange);
                        ReleaseComObject(equationRange);
                        ReleaseComObject(equation);
                    }

                    converted++;
                    if (converted == 1 ||
                        converted % 10 == 0 ||
                        converted == sourceOmmlCount)
                    {
                        WriteProgress(
                            progressPath,
                            "convert",
                            converted,
                            sourceOmmlCount,
                            "created inline Equation.DSMT4 objects");
                    }
                }

                int remaining = document.OMaths.Count;
                if (remaining != 0)
                {
                    throw new InvalidOperationException(
                        remaining + " Word native equations remain after conversion.");
                }

                MathTypeObjectMetrics mathTypeMetrics =
                    InspectInlineMathTypeObjects(document);
                if (mathTypeMetrics.Count != sourceOmmlCount)
                {
                    throw new InvalidOperationException(
                        "Expected " + sourceOmmlCount +
                        " inline MathType objects, but found " +
                        mathTypeMetrics.Count + ".");
                }

                document.TrackRevisions = originalTrackRevisions;
                document.Save();
                saved = true;

                WriteManifestSummary(
                    manifest,
                    sourceOmmlCount,
                    converted,
                    remaining,
                    mathTypeMetrics.Count,
                    accentScriptRiskCount,
                    accentScriptMtefNudgeCount);
                WriteProgress(
                    progressPath,
                    "convert",
                    converted,
                    sourceOmmlCount,
                    "saved candidate document");

                ConversionSummary summary = CreateWordSummary(
                    "convert",
                    sourcePath,
                    outputPath,
                    sourceHash,
                    sourceOmmlCount,
                    converted,
                    document,
                    mathType.NativeVersion,
                    mathTypeMetrics,
                    manifestPath,
                    progressPath);
                summary.OutputBytes = new FileInfo(outputPath).Length;
                summary.AccentScriptRiskCount = accentScriptRiskCount;
                summary.AccentScriptMtefNudgeCount =
                    accentScriptMtefNudgeCount;
                return summary;
            }
            finally
            {
                if (manifest != null)
                {
                    manifest.Dispose();
                }

                if (document != null && !saved)
                {
                    try
                    {
                        document.TrackRevisions = originalTrackRevisions;
                    }
                    catch
                    {
                    }
                }

                CloseDocumentWithoutSaving(document);
                ReleaseComObject(document);
                QuitWord(app);
                ReleaseComObject(app);
                if (mathType != null)
                {
                    mathType.Dispose();
                }
                CollectComGarbage();

                // Corrected accent formulas require an intermediate document
                // save so their temporary donor OLE can be read from the
                // package. If any later gate fails, that disk image may
                // contain a donor and an uninitialized target. Never leave it
                // behind as a plausible conversion candidate.
                if (!saved)
                {
                    DeleteFailedOutputCandidate(
                        outputPath,
                        progressPath,
                        converted,
                        sourceOmmlCount);
                }
            }
        }

        public static ConversionSummary BuildRepresentativeTest(
            string nativeDocumentPath,
            string convertedDocumentPath,
            string manifestPath,
            string progressPath,
            string mathPageDirectory,
            string blankEquationPath,
            string preferencePath)
        {
            RequireExistingFile(preferencePath, "MathType preference file");
            RequireDistinctPaths(
                "representative test",
                nativeDocumentPath,
                convertedDocumentPath,
                manifestPath,
                progressPath);
            RequireNewPath(nativeDocumentPath, "native test document");
            RequireNewPath(convertedDocumentPath, "converted test document");
            EnsureParentDirectory(nativeDocumentPath);

            string[] formulas =
            {
                "x^2+a/b",
                "√(a+b)",
                "∑_(i=1)^n i",
                "∫_0^1 x^2 dx",
                "lim_(x→0) sin(x)/x",
                "α+β=γ",
                "x̅+ŷ",
                "A_(ij)=a_i b_j",
                "f(x)=|x|",
                "‖v‖=√(v_1^2+v_2^2)",
                "r_k=z_k-h_k(x̂_k^-), s_k=r_k^T R_k^(-1) r_k",
                "Δθ_m=10′′, Ω+Σ, μ±τ, a≤b",
                "′′",
                "ω̃^s=(I+K_g+E_g)ω_is^s+b_g+n_g",
                "v̇^n",
                "δv̇^n",
                "R_M=a(1-e^2)/(1-e^2 sin^2 L)^(3/2)",
                "0^°,90^°,180^°,270^°",
                "(°)/(h)",
                "10^″"
            };

            Word.Application app = null;
            Word.Document document = null;

            try
            {
                app = CreateHiddenWordApplication();
                document = app.Documents.Add();

                for (int i = 0; i < formulas.Length; i++)
                {
                    int insertAt = document.Content.End - 1;
                    string prefix = "测试" + (i + 1).ToString(CultureInfo.InvariantCulture) + "：";
                    string suffix = "；结束\r";
                    Word.Range line = null;
                    Word.Range input = null;
                    Word.Range added = null;
                    Word.OMath equation = null;
                    try
                    {
                        line = document.Range(insertAt, insertAt);
                        line.Text = prefix + formulas[i] + suffix;
                        input = document.Range(
                            insertAt + prefix.Length,
                            insertAt + prefix.Length + formulas[i].Length);
                        added = document.OMaths.Add(input);
                        equation = added.OMaths[1];
                        equation.BuildUp();
                    }
                    finally
                    {
                        ReleaseComObject(equation);
                        ReleaseComObject(added);
                        ReleaseComObject(input);
                        ReleaseComObject(line);
                    }
                }

                document.SaveAs2(
                    FileName: nativeDocumentPath,
                    FileFormat: Word.WdSaveFormat.wdFormatXMLDocument);
            }
            finally
            {
                CloseDocumentWithoutSaving(document);
                ReleaseComObject(document);
                QuitWord(app);
                ReleaseComObject(app);
                CollectComGarbage();
            }

            return Convert(
                nativeDocumentPath,
                convertedDocumentPath,
                null,
                manifestPath,
                progressPath,
                mathPageDirectory,
                blankEquationPath,
                preferencePath,
                false);
        }

        public static ConversionSummary Validate(
            string documentPath,
            int expectedMathTypeCount,
            string progressPath)
        {
            RequireExistingFile(documentPath, "converted document");
            if (!String.IsNullOrWhiteSpace(progressPath))
            {
                RequireDistinctPaths(
                    "validation",
                    documentPath,
                    progressPath);
                PrepareOutputFile(progressPath);
                WriteProgress(progressPath, "validate", 0, 1, "opening converted document read-only");
            }

            Word.Application app = null;
            Word.Document document = null;

            try
            {
                app = CreateHiddenWordApplication();
                document = OpenDocument(app, documentPath, true);
                MathTypeObjectMetrics mathTypeMetrics =
                    InspectInlineMathTypeObjects(document);
                int mathTypeCount = mathTypeMetrics.Count;
                int remaining = document.OMaths.Count;

                if (remaining != 0)
                {
                    throw new InvalidOperationException(
                        "Validation found " + remaining + " remaining Word native equations.");
                }

                if (expectedMathTypeCount >= 0 && mathTypeCount != expectedMathTypeCount)
                {
                    throw new InvalidOperationException(
                        "Validation expected " + expectedMathTypeCount +
                        " MathType objects, but found " + mathTypeCount + ".");
                }

                ConversionSummary summary = CreateWordSummary(
                    "validate",
                    documentPath,
                    documentPath,
                    ComputeSha256(documentPath),
                    expectedMathTypeCount,
                    mathTypeCount,
                    document,
                    0,
                    mathTypeMetrics,
                    null,
                    progressPath);
                summary.OutputBytes = new FileInfo(documentPath).Length;
                summary.PackageValidation = ValidateOpenXmlPackage(documentPath);

                if (!String.IsNullOrWhiteSpace(progressPath))
                {
                    WriteProgress(progressPath, "validate", 1, 1, "validation complete");
                }

                return summary;
            }
            finally
            {
                CloseDocumentWithoutSaving(document);
                ReleaseComObject(document);
                QuitWord(app);
                ReleaseComObject(app);
                CollectComGarbage();
            }
        }

        private static Word.Application CreateHiddenWordApplication()
        {
            Word.Application app = new Word.Application();
            app.Visible = false;
            app.DisplayAlerts = Word.WdAlertLevel.wdAlertsNone;
            app.ScreenUpdating = false;
            app.AutomationSecurity = Office.MsoAutomationSecurity.msoAutomationSecurityForceDisable;
            app.Options.SaveNormalPrompt = false;
            app.Options.BackgroundSave = false;
            app.Options.SaveInterval = 0;
            return app;
        }

        private static Word.Document OpenDocument(
            Word.Application app,
            string path,
            bool readOnly)
        {
            return app.Documents.Open(
                FileName: path,
                ConfirmConversions: false,
                ReadOnly: readOnly,
                AddToRecentFiles: false,
                Visible: false,
                OpenAndRepair: false);
        }

        private static TexExportSnapshot ExportEquationAsTex(
            Word.Application app,
            Word.OMath equation)
        {
            Exception lastException = null;
            string sourceWordText = String.Empty;
            for (int attempt = 1; attempt <= 5; attempt++)
            {
                Word.Range selectionRange = null;
                Word.Range convertedRange = null;
                try
                {
                    selectionRange = equation.Range;
                    if (attempt == 1)
                    {
                        sourceWordText = selectionRange.Text;
                    }
                    selectionRange.Select();
                    ReleaseComObject(selectionRange);
                    selectionRange = null;

                    app.CommandBars.ExecuteMso("EquationLaTexFormat");
                    app.CommandBars.ExecuteMso("EquationLinearOne");

                    convertedRange = equation.Range;
                    return TexNormalizer.CreateSnapshot(
                        sourceWordText,
                        convertedRange.Text);
                }
                catch (COMException exception)
                {
                    lastException = exception;
                    if (attempt < 5)
                    {
                        Thread.Sleep(300 * attempt);
                    }
                }
                finally
                {
                    ReleaseComObject(convertedRange);
                    ReleaseComObject(selectionRange);
                }
            }

            throw new InvalidOperationException(
                "Word could not export the equation as LaTeX after five attempts.",
                lastException);
        }

        private static Word.InlineShape FindInsertedMathTypeShape(
            Word.Range searchRange,
            int expectedStart)
        {
            Word.InlineShapes shapes = null;
            Word.InlineShape fallback = null;
            try
            {
                shapes = searchRange.InlineShapes;
                for (int i = 1; i <= shapes.Count; i++)
                {
                    Word.InlineShape candidate = shapes[i];
                    bool keepCandidate = false;
                    try
                    {
                        string progId = candidate.OLEFormat.ProgID;
                        Word.Range candidateRange = candidate.Range;
                        int candidateStart = candidateRange.Start;
                        ReleaseComObject(candidateRange);

                        if (String.Equals(
                            progId,
                            MathTypeProgId,
                            StringComparison.OrdinalIgnoreCase))
                        {
                            if (candidateStart == expectedStart)
                            {
                                if (fallback != null)
                                {
                                    ReleaseComObject(fallback);
                                }
                                keepCandidate = true;
                                return candidate;
                            }

                            if (fallback == null)
                            {
                                fallback = candidate;
                                keepCandidate = true;
                            }
                        }
                    }
                    catch
                    {
                    }
                    finally
                    {
                        if (!keepCandidate)
                        {
                            ReleaseComObject(candidate);
                        }
                    }
                }

                return fallback;
            }
            finally
            {
                ReleaseComObject(shapes);
            }
        }

        private static object ActivateAndGetEquationObject(
            Word.InlineShape mathTypeShape)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                try
                {
                    mathTypeShape.OLEFormat.DoVerb(2);
                    return mathTypeShape.OLEFormat.Object;
                }
                catch (COMException exception)
                {
                    lastException = exception;
                    if (attempt < 3)
                    {
                        Thread.Sleep(250 * attempt);
                    }
                }
            }

            throw new InvalidOperationException(
                "Could not activate the inline MathType OLE object after three attempts.",
                lastException);
        }

        private static void UpdateEquationFieldWithRetry(
            Word.InlineShape mathTypeShape)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                Word.Range shapeRange = null;
                Word.Fields shapeFields = null;
                try
                {
                    shapeRange = mathTypeShape.Range;
                    shapeFields = shapeRange.Fields;
                    shapeFields.Update();
                    return;
                }
                catch (COMException exception)
                {
                    lastException = exception;
                    if (attempt < 3)
                    {
                        Thread.Sleep(250 * attempt);
                    }
                }
                finally
                {
                    ReleaseComObject(shapeFields);
                    ReleaseComObject(shapeRange);
                }
            }

            throw new InvalidOperationException(
                "Could not refresh the inline MathType field after three attempts.",
                lastException);
        }

        private static string GetProgIdWithRetry(Word.InlineShape mathTypeShape)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                try
                {
                    return mathTypeShape.OLEFormat.ProgID;
                }
                catch (COMException exception)
                {
                    lastException = exception;
                    if (attempt < 3)
                    {
                        Thread.Sleep(250 * attempt);
                    }
                }
            }

            throw new InvalidOperationException(
                "Could not read the inline MathType ProgID after three attempts.",
                lastException);
        }

        private static MathTypeObjectMetrics InspectInlineMathTypeObjects(
            Word.Document document)
        {
            MathTypeObjectMetrics metrics = new MathTypeObjectMetrics();
            Word.InlineShapes shapes = null;
            try
            {
                shapes = document.InlineShapes;
                for (int i = 1; i <= shapes.Count; i++)
                {
                    Word.InlineShape shape = null;
                    try
                    {
                        shape = shapes[i];
                        if (String.Equals(
                            shape.OLEFormat.ProgID,
                            MathTypeProgId,
                            StringComparison.OrdinalIgnoreCase))
                        {
                            metrics.Count++;
                            metrics.MaxWidthPoints = Math.Max(
                                metrics.MaxWidthPoints,
                                shape.Width);
                            metrics.MaxHeightPoints = Math.Max(
                                metrics.MaxHeightPoints,
                                shape.Height);
                            if (shape.Width > 500.0f)
                            {
                                metrics.WiderThan500PointsCount++;
                            }
                        }
                    }
                    catch
                    {
                    }
                    finally
                    {
                        ReleaseComObject(shape);
                    }
                }
            }
            finally
            {
                ReleaseComObject(shapes);
            }

            return metrics;
        }

        private static string GetContext(
            Word.Document document,
            int start,
            int end)
        {
            Word.Range contextRange = null;
            try
            {
                int contextStart = Math.Max(0, start - 40);
                int contextEnd = Math.Min(document.Content.End - 1, end + 40);
                contextRange = document.Range(contextStart, contextEnd);
                return contextRange.Text;
            }
            catch
            {
                return String.Empty;
            }
            finally
            {
                ReleaseComObject(contextRange);
            }
        }

        private static void DeleteBlankEquationBookmark(Word.Document document)
        {
            if (!document.Bookmarks.Exists(BlankEquationBookmark))
            {
                return;
            }

            Word.Bookmark bookmark = null;
            try
            {
                bookmark = document.Bookmarks[BlankEquationBookmark];
                bookmark.Delete();
            }
            finally
            {
                ReleaseComObject(bookmark);
            }
        }

        private static ConversionSummary CreateWordSummary(
            string mode,
            string sourcePath,
            string outputPath,
            string sourceHash,
            int sourceOmmlCount,
            int convertedCount,
            Word.Document document,
            int nativeApiVersion,
            MathTypeObjectMetrics mathTypeMetrics,
            string manifestPath,
            string progressPath)
        {
            return new ConversionSummary
            {
                Mode = mode,
                SourcePath = sourcePath,
                OutputPath = outputPath,
                SourceSha256 = sourceHash,
                SourceOmmlCount = sourceOmmlCount,
                ConvertedCount = convertedCount,
                RemainingOmmlCount = document.OMaths.Count,
                MathTypeInlineCount = mathTypeMetrics.Count,
                NativeApiVersion = nativeApiVersion,
                PageCount = document.ComputeStatistics(
                    Word.WdStatistic.wdStatisticPages,
                    false),
                FieldCount = document.Fields.Count,
                BookmarkCount = document.Bookmarks.Count,
                RevisionCount = document.Revisions.Count,
                TrackRevisions = document.TrackRevisions,
                MathTypeMaxWidthPoints = mathTypeMetrics.MaxWidthPoints,
                MathTypeMaxHeightPoints = mathTypeMetrics.MaxHeightPoints,
                MathTypeWiderThan500PointsCount =
                    mathTypeMetrics.WiderThan500PointsCount,
                ManifestPath = manifestPath,
                ProgressPath = progressPath
            };
        }

        private static string ValidateOpenXmlPackage(string documentPath)
        {
            int entryCount = 0;
            int xmlCount = 0;
            int ommlCount = 0;
            int mathTypeOleCount = 0;
            int parseFailures = 0;

            using (FileStream stream = File.Open(
                documentPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read))
            using (ZipArchive archive = new ZipArchive(
                stream,
                ZipArchiveMode.Read,
                false,
                Encoding.UTF8))
            {
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    entryCount++;
                    using (Stream entryStream = entry.Open())
                    {
                        MemoryStream copy = new MemoryStream();
                        entryStream.CopyTo(copy);
                        byte[] bytes = copy.ToArray();
                        copy.Dispose();

                        if (!entry.FullName.EndsWith(
                            ".xml",
                            StringComparison.OrdinalIgnoreCase) &&
                            !entry.FullName.EndsWith(
                                ".rels",
                                StringComparison.OrdinalIgnoreCase))
                        {
                            continue;
                        }

                        xmlCount++;
                        try
                        {
                            XmlDocument xml = new XmlDocument();
                            using (MemoryStream xmlStream = new MemoryStream(bytes))
                            {
                                xml.Load(xmlStream);
                            }

                            XmlNamespaceManager ns = new XmlNamespaceManager(xml.NameTable);
                            ns.AddNamespace(
                                "m",
                                "http://schemas.openxmlformats.org/officeDocument/2006/math");
                            ns.AddNamespace(
                                "o",
                                "urn:schemas-microsoft-com:office:office");
                            XmlNodeList equations = xml.SelectNodes("//m:oMath", ns);
                            if (equations != null)
                            {
                                ommlCount += equations.Count;
                            }

                            XmlNodeList oleObjects = xml.SelectNodes(
                                "//o:OLEObject[@ProgID='" + MathTypeProgId + "']",
                                ns);
                            if (oleObjects != null)
                            {
                                mathTypeOleCount += oleObjects.Count;
                            }
                        }
                        catch
                        {
                            parseFailures++;
                        }
                    }
                }
            }

            if (parseFailures != 0)
            {
                throw new InvalidDataException(
                    parseFailures + " XML package parts could not be parsed.");
            }

            if (ommlCount != 0)
            {
                throw new InvalidDataException(
                    "Open XML package still contains " + ommlCount + " m:oMath elements.");
            }

            return "entries=" + entryCount +
                   ";xmlParts=" + xmlCount +
                   ";omml=" + ommlCount +
                   ";mathTypeOle=" + mathTypeOleCount +
                   ";xmlParseFailures=" + parseFailures;
        }

        private static StreamWriter CreateManifestWriter(string manifestPath)
        {
            EnsureParentDirectory(manifestPath);
            StreamWriter writer = new StreamWriter(
                manifestPath,
                false,
                new UTF8Encoding(false));
            writer.AutoFlush = true;
            return writer;
        }

        private static void WriteManifestHeader(
            StreamWriter writer,
            string mode,
            string sourcePath,
            string outputPath,
            string sourceHash,
            int sourceOmmlCount,
            int nativeApiVersion)
        {
            writer.WriteLine(
                "{\"type\":\"header\",\"mode\":\"" + EscapeJson(mode) +
                "\",\"timestamp\":\"" + EscapeJson(DateTime.Now.ToString("o")) +
                "\",\"sourcePath\":\"" + EscapeJson(sourcePath) +
                "\",\"outputPath\":\"" + EscapeJson(outputPath) +
                "\",\"sourceSha256\":\"" + EscapeJson(sourceHash) +
                "\",\"sourceOmmlCount\":" + sourceOmmlCount +
                ",\"nativeApiVersion\":" + nativeApiVersion + "}");
        }

        private static void WriteFormulaManifest(
            StreamWriter writer,
            int sourceIndex,
            int start,
            int end,
            int storyType,
            string context,
            TexExportSnapshot tex,
            int? preferenceStatus,
            int? setStatus,
            int? closeStatus,
            string progId,
            string finalRange)
        {
            writer.WriteLine(
                "{\"type\":\"formula\",\"sourceIndex\":" + sourceIndex +
                ",\"start\":" + start +
                ",\"end\":" + end +
                ",\"storyType\":" + storyType +
                ",\"context\":\"" + EscapeJson(context) +
                "\",\"sourceWordText\":\"" +
                EscapeJson(tex == null ? null : tex.SourceWordText) +
                "\",\"rawWordTex\":\"" +
                EscapeJson(tex == null ? null : tex.RawWordTex) +
                "\",\"nfkcWordTex\":\"" +
                EscapeJson(tex == null ? null : tex.NfkcWordTex) +
                "\",\"normalizedTex\":\"" +
                EscapeJson(tex == null ? null : tex.NormalizedTex) +
                "\",\"tex\":\"" +
                EscapeJson(tex == null ? null : tex.NormalizedTex) +
                "\",\"replacementSummary\":\"" +
                EscapeJson(tex == null ? null : tex.ReplacementSummary) +
                "\",\"accentScriptRiskCount\":" +
                (tex == null
                    ? "0"
                    : tex.AccentScriptRiskCount.ToString(
                        CultureInfo.InvariantCulture)) +
                ",\"accentScriptRiskDetails\":\"" +
                EscapeJson(tex == null
                    ? null
                    : tex.AccentScriptRiskDetails) +
                "\",\"accentScriptMtefNudgeCount\":" +
                (tex == null
                    ? "0"
                    : tex.AccentScriptMtefNudgeCount.ToString(
                        CultureInfo.InvariantCulture)) +
                ",\"preferenceStatus\":" +
                NullableIntJson(preferenceStatus) +
                ",\"setStatus\":" + NullableIntJson(setStatus) +
                ",\"closeStatus\":" + NullableIntJson(closeStatus) +
                ",\"progId\":\"" + EscapeJson(progId) +
                "\",\"finalRange\":\"" + EscapeJson(finalRange) + "\"}");
        }

        private static void WriteManifestSummary(
            StreamWriter writer,
            int sourceOmmlCount,
            int processed,
            int remainingOmmlCount,
            int mathTypeInlineCount,
            int accentScriptRiskCount,
            int accentScriptMtefNudgeCount)
        {
            writer.WriteLine(
                "{\"type\":\"summary\",\"timestamp\":\"" +
                EscapeJson(DateTime.Now.ToString("o")) +
                "\",\"sourceOmmlCount\":" + sourceOmmlCount +
                ",\"processed\":" + processed +
                ",\"remainingOmmlCount\":" + remainingOmmlCount +
                ",\"mathTypeInlineCount\":" + mathTypeInlineCount +
                ",\"accentScriptRiskCount\":" + accentScriptRiskCount +
                ",\"accentScriptMtefNudgeCount\":" +
                accentScriptMtefNudgeCount +
                "}");
        }

        private static void WriteProgress(
            string progressPath,
            string stage,
            int completed,
            int total,
            string message)
        {
            EnsureParentDirectory(progressPath);
            string line = DateTime.Now.ToString("o") +
                          "\tstage=" + stage +
                          "\tcompleted=" + completed +
                          "\ttotal=" + total +
                          "\tmessage=" + message +
                          Environment.NewLine;
            File.AppendAllText(progressPath, line, new UTF8Encoding(false));
        }

        private static void DeleteFailedOutputCandidate(
            string outputPath,
            string progressPath,
            int completed,
            int total)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 5; attempt++)
            {
                if (!File.Exists(outputPath))
                {
                    if (attempt > 1)
                    {
                        WriteProgress(
                            progressPath,
                            "cleanup",
                            completed,
                            total,
                            "deleted failed output candidate after retry");
                    }
                    return;
                }

                try
                {
                    File.Delete(outputPath);
                    WriteProgress(
                        progressPath,
                        "cleanup",
                        completed,
                        total,
                        "deleted failed output candidate");
                    return;
                }
                catch (Exception exception)
                {
                    lastException = exception;
                    if (attempt < 5)
                    {
                        Thread.Sleep(250 * attempt);
                    }
                }
            }

            string detail =
                "failed to delete output candidate after 5 attempts;path=" +
                outputPath +
                ";exception=" +
                (lastException == null
                    ? "unknown"
                    : lastException.GetType().FullName) +
                ";message=" +
                SanitizeProgressMessage(
                    lastException == null
                        ? "unknown cleanup failure"
                        : lastException.Message);
            WriteProgress(
                progressPath,
                "cleanup-error",
                completed,
                total,
                detail);
            throw new InvalidOperationException(
                "Conversion failed and the incomplete output candidate could " +
                "not be deleted. See the progress log for details.",
                lastException);
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
                                "\\u" + ((int)character).ToString("x4"));
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

        private static string NullableIntJson(int? value)
        {
            return value.HasValue
                ? value.Value.ToString(CultureInfo.InvariantCulture)
                : "null";
        }

        private static string SanitizeProgressMessage(string value)
        {
            if (String.IsNullOrEmpty(value))
            {
                return String.Empty;
            }

            return value
                .Replace("\r", " ")
                .Replace("\n", " ")
                .Replace("\t", " ");
        }

        private static void EnsureNonEmptyTex(string tex, int index, int start)
        {
            if (String.IsNullOrWhiteSpace(tex))
            {
                throw new InvalidDataException(
                    "Equation " + index +
                    " at Word range " + start +
                    " exported as empty TeX.");
            }
        }

        private static AccentScriptCorrectionStatus
            CorrectAccentScriptGeometry(
            Word.Document document,
            Word.InlineShape mathTypeShape,
            MathTypeApiSession mathType,
            string outputPath,
            int sourceIndex,
            TexExportSnapshot tex,
            string blankEquationPath,
            string preferencePath)
        {
            IList<AccentScriptRisk> risks =
                AccentScriptRiskDetector.Find(tex.NormalizedTex);
            if (risks.Count != 1 ||
                String.IsNullOrEmpty(risks[0].SuperscriptValue))
            {
                throw new InvalidDataException(
                    "Equation " + sourceIndex +
                    " uses an unsupported accent-script structure. " +
                    "Automatic repair currently requires exactly one " +
                    "simple ASCII right superscript.");
            }

            Word.Range donorInsertion = null;
            Word.InlineShape donorShape = null;
            object donorObject = null;
            int donorSetStatus = 0;
            int donorCloseStatus = 0;
            string bookmarkName =
                "_CodexMt" +
                sourceIndex.ToString(CultureInfo.InvariantCulture) +
                Guid.NewGuid().ToString("N").Substring(0, 8);
            byte[] donorMtef = null;
            try
            {
                int donorStart = Math.Max(0, document.Content.End - 1);
                donorInsertion = document.Range(donorStart, donorStart);
                donorInsertion.InsertFile(
                    blankEquationPath,
                    BlankEquationBookmark,
                    false,
                    false,
                    false);
                DeleteBlankEquationBookmark(document);

                int donorSearchEnd = Math.Min(
                    document.Content.End - 1,
                    donorStart + EmbeddedEquationSearchWidth);
                donorInsertion.SetRange(donorStart, donorSearchEnd);
                donorShape = FindInsertedMathTypeShape(
                    donorInsertion,
                    donorStart);
                if (donorShape == null)
                {
                    throw new InvalidOperationException(
                        "Could not locate the temporary MathType donor for " +
                        "equation " + sourceIndex + ".");
                }

                int donorPreferenceStatus =
                    mathType.ApplyPreferencesForNextInlineEquation(
                        preferencePath);
                MathTypeApiSession.ThrowIfMathTypeError(
                    donorPreferenceStatus,
                    "MTSetMTPrefs for donor equation " + sourceIndex);

                donorObject =
                    ActivateAndGetEquationObject(donorShape);
                donorSetStatus = mathType.SetEquationFromInlineTex(
                    donorObject,
                    tex.NormalizedTex);
                MathTypeApiSession.ThrowIfMathTypeError(
                    donorSetStatus,
                    "MTSetEqnFromLangStr for donor equation " +
                    sourceIndex);
                donorCloseStatus =
                    mathType.CloseAndSaveEquation(donorObject);
                MathTypeApiSession.ThrowIfMathTypeError(
                    donorCloseStatus,
                    "MTCloseOleObject for donor equation " +
                    sourceIndex);
                ReleaseComObject(donorObject);
                donorObject = null;
                UpdateEquationFieldWithRetry(donorShape);

                Word.Range donorRange = null;
                Word.Bookmark donorBookmark = null;
                try
                {
                    donorRange = donorShape.Range.Duplicate;
                    donorBookmark = document.Bookmarks.Add(
                        bookmarkName,
                        donorRange);
                    document.Save();
                }
                finally
                {
                    ReleaseComObject(donorBookmark);
                    ReleaseComObject(donorRange);
                }

                try
                {
                    donorMtef =
                        MathTypeOleMtef.ReadEquationMtefByBookmark(
                            outputPath,
                            bookmarkName);
                }
                finally
                {
                    DeleteBookmark(document, bookmarkName);
                }
            }
            finally
            {
                if (donorObject != null)
                {
                    try
                    {
                        mathType.CloseWithoutSavingEquation(
                            donorObject);
                    }
                    catch
                    {
                    }
                }

                DeleteBookmark(document, bookmarkName);
                DeleteInlineShape(donorShape);
                ReleaseComObject(donorObject);
                ReleaseComObject(donorShape);
                ReleaseComObject(donorInsertion);
            }

            if (donorMtef == null || donorMtef.Length == 0)
            {
                throw new InvalidDataException(
                    "The temporary MathType donor did not provide MTEF " +
                    "for equation " + sourceIndex + ".");
            }

            MtefAccentScriptNudgeResult correction =
                MathTypeOleMtef.NudgeDotAccentRightSuperscripts(
                    donorMtef,
                    tex.AccentScriptRiskCount,
                    AccentScriptVerticalNudge,
                    risks[0].SuperscriptValue[0]);

            object equationObject = null;
            int preferenceStatus = 0;
            int resetStatus = 0;
            int closeStatus = 0;
            try
            {
                preferenceStatus =
                    mathType.ApplyPreferencesForNextInlineEquation(
                        preferencePath);
                MathTypeApiSession.ThrowIfMathTypeError(
                    preferenceStatus,
                    "MTSetMTPrefs for corrected equation " +
                    sourceIndex);

                equationObject =
                    ActivateAndGetEquationObject(mathTypeShape);
                resetStatus = mathType.SetEquationFromInlineTex(
                    equationObject,
                    "\\,");
                MathTypeApiSession.ThrowIfMathTypeError(
                    resetStatus,
                    "MTSetEqnFromLangStr reset for equation " +
                    sourceIndex);

                MathTypeOleMtef.SetEquationFromMtef(
                    equationObject,
                    correction.Mtef);
                string readback = mathType.GetEquationAsTex(
                    equationObject);
                ValidateCorrectedAccentScriptReadback(
                    readback,
                    tex.NormalizedTex,
                    tex.AccentScriptRiskCount,
                    sourceIndex);

                closeStatus = mathType.CloseAndSaveEquation(
                    equationObject);
                MathTypeApiSession.ThrowIfMathTypeError(
                    closeStatus,
                    "MTCloseOleObject after MTEF correction for equation " +
                    sourceIndex);
                ReleaseComObject(equationObject);
                equationObject = null;
                UpdateEquationFieldWithRetry(mathTypeShape);
            }
            catch
            {
                if (equationObject != null)
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

                throw;
            }
            finally
            {
                ReleaseComObject(equationObject);
            }

            return new AccentScriptCorrectionStatus
            {
                PreferenceStatus = preferenceStatus,
                SetStatus = donorSetStatus,
                CloseStatus = closeStatus == 0
                    ? donorCloseStatus
                    : closeStatus,
                NudgedSuperscriptCount =
                    correction.NudgedSuperscriptCount
            };
        }

        private static void ValidateCorrectedAccentScriptReadback(
            string readbackTex,
            string expectedTex,
            int expectedRiskCount,
            int sourceIndex)
        {
            if (String.IsNullOrWhiteSpace(readbackTex) ||
                readbackTex.IndexOf('?') >= 0)
            {
                throw new InvalidDataException(
                    "Equation " + sourceIndex +
                    " returned an empty or question-mark MathType readback " +
                    "after MTEF accent-script correction.");
            }

            string value = readbackTex.Trim();
            if (value.Length >= 2 &&
                value[0] == '$' &&
                value[value.Length - 1] == '$')
            {
                value = value.Substring(1, value.Length - 2);
            }

            if (!String.Equals(
                value,
                expectedTex,
                StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    "Equation " + sourceIndex +
                    " changed during MTEF accent-script correction. " +
                    "Expected exact normalized TeX '" +
                    expectedTex +
                    "', read back '" +
                    value +
                    "'.");
            }

            int actualRiskCount =
                AccentScriptRiskDetector.Find(value).Count;
            if (actualRiskCount != expectedRiskCount)
            {
                throw new InvalidDataException(
                    "Equation " + sourceIndex +
                    " lost its dot/double-dot accent-with-right-script " +
                    "structure after MTEF correction. Expected " +
                    expectedRiskCount +
                    ", read back " +
                    actualRiskCount +
                    ".");
            }
        }

        private static void DeleteBookmark(
            Word.Document document,
            string bookmarkName)
        {
            if (document == null ||
                String.IsNullOrWhiteSpace(bookmarkName) ||
                !document.Bookmarks.Exists(bookmarkName))
            {
                return;
            }

            Word.Bookmark bookmark = null;
            try
            {
                bookmark = document.Bookmarks[bookmarkName];
                bookmark.Delete();
            }
            finally
            {
                ReleaseComObject(bookmark);
            }
        }

        private static void DeleteInlineShape(
            Word.InlineShape shape)
        {
            if (shape == null)
            {
                return;
            }

            Word.Range range = null;
            try
            {
                range = shape.Range.Duplicate;
                range.Delete();
            }
            finally
            {
                ReleaseComObject(range);
            }
        }

        private static void RequireExistingFile(string path, string description)
        {
            if (String.IsNullOrWhiteSpace(path) || !File.Exists(path))
            {
                throw new FileNotFoundException(
                    "The " + description + " was not found.",
                    path);
            }
        }

        private static void RequireExistingDirectory(string path, string description)
        {
            if (String.IsNullOrWhiteSpace(path) || !Directory.Exists(path))
            {
                throw new DirectoryNotFoundException(
                    "The " + description + " was not found: " + path);
            }
        }

        private static void RequireDistinctPaths(
            string operation,
            params string[] paths)
        {
            Dictionary<string, string> seen =
                new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (string path in paths)
            {
                if (String.IsNullOrWhiteSpace(path))
                {
                    continue;
                }

                string fullPath = Path.GetFullPath(path)
                    .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
                string prior;
                if (seen.TryGetValue(fullPath, out prior))
                {
                    throw new ArgumentException(
                        "The " + operation +
                        " paths must be distinct, but the same path was supplied twice: " +
                        fullPath + ".");
                }

                seen.Add(fullPath, path);
            }
        }

        private static void RequireNewPath(string path, string description)
        {
            if (String.IsNullOrWhiteSpace(path))
            {
                throw new ArgumentException(
                    "A path is required for the " + description + ".");
            }

            if (File.Exists(path) || Directory.Exists(path))
            {
                throw new IOException(
                    "The " + description + " already exists: " + path);
            }
        }

        private static void PrepareOutputFile(string path)
        {
            if (String.IsNullOrWhiteSpace(path))
            {
                throw new ArgumentException("An output file path is required.");
            }

            RequireNewPath(path, "log or manifest");
            EnsureParentDirectory(path);
        }

        private static void EnsureParentDirectory(string path)
        {
            string directory = Path.GetDirectoryName(path);
            if (!String.IsNullOrWhiteSpace(directory))
            {
                Directory.CreateDirectory(directory);
            }
        }

        private static string ComputeSha256(string path)
        {
            using (SHA256 hash = SHA256.Create())
            using (FileStream stream = File.OpenRead(path))
            {
                byte[] bytes = hash.ComputeHash(stream);
                StringBuilder value = new StringBuilder(bytes.Length * 2);
                foreach (byte item in bytes)
                {
                    value.Append(item.ToString("x2"));
                }
                return value.ToString();
            }
        }

        private static void CloseDocumentWithoutSaving(Word.Document document)
        {
            if (document == null)
            {
                return;
            }

            try
            {
                object saveChanges = Word.WdSaveOptions.wdDoNotSaveChanges;
                object missing = Type.Missing;
                ((Word._Document)document).Close(
                    ref saveChanges,
                    ref missing,
                    ref missing);
            }
            catch
            {
            }
        }

        private static void QuitWord(Word.Application app)
        {
            if (app == null)
            {
                return;
            }

            try
            {
                object missing = Type.Missing;
                ((Word._Application)app).Quit(
                    ref missing,
                    ref missing,
                    ref missing);
            }
            catch
            {
            }
        }

        private static void ReleaseComObject(object value)
        {
            if (value == null || !Marshal.IsComObject(value))
            {
                return;
            }

            try
            {
                Marshal.FinalReleaseComObject(value);
            }
            catch
            {
            }
        }

        private static void CollectComGarbage()
        {
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            GC.WaitForPendingFinalizers();
        }
    }
}
