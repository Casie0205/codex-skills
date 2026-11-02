using System;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using Office = Microsoft.Office.Core;
using Word = Microsoft.Office.Interop.Word;

namespace ThesisMathTypeConversion
{
    public sealed class MathTypeReadbackSummary
    {
        public string DocumentPath { get; set; }
        public string DocumentSha256 { get; set; }
        public string ManifestPath { get; set; }
        public int NativeApiVersion { get; set; }
        public int MathTypeCount { get; set; }
        public int QuestionMarkCount { get; set; }
        public int NonAsciiCount { get; set; }
        public int PageCount { get; set; }
    }

    public static class WordMathTypeReadbackVerifier
    {
        private const string MathTypeProgId = "Equation.DSMT4";

        public static MathTypeReadbackSummary Readback(
            string documentPath,
            string manifestPath,
            string progressPath,
            string mathPageDirectory,
            int expectedMathTypeCount)
        {
            RequireExistingFile(documentPath, "MathType document");
            RequireExistingDirectory(mathPageDirectory, "MathType MathPage directory");
            RequireNewPath(manifestPath, "readback manifest");
            if (!String.IsNullOrWhiteSpace(progressPath))
            {
                RequireNewPath(progressPath, "readback progress log");
            }
            RequireDistinctPaths(documentPath, manifestPath, progressPath);
            EnsureParentDirectory(manifestPath);
            if (!String.IsNullOrWhiteSpace(progressPath))
            {
                EnsureParentDirectory(progressPath);
            }

            Word.Application app = null;
            Word.Document document = null;
            MathTypeApiSession mathType = null;
            StreamWriter manifest = null;
            int mathTypeCount = 0;
            int questionMarkCount = 0;
            int nonAsciiCount = 0;

            try
            {
                WriteProgress(
                    progressPath,
                    "readback",
                    0,
                    expectedMathTypeCount,
                    "opening MathType document read-only");
                mathType = new MathTypeApiSession(mathPageDirectory);
                app = CreateHiddenWordApplication();
                document = OpenDocument(app, documentPath);
                manifest = new StreamWriter(
                    manifestPath,
                    false,
                    new UTF8Encoding(false));
                manifest.AutoFlush = true;
                manifest.WriteLine(
                    "{\"type\":\"header\",\"timestamp\":\"" +
                    EscapeJson(DateTime.Now.ToString("o")) +
                    "\",\"documentPath\":\"" +
                    EscapeJson(Path.GetFullPath(documentPath)) +
                    "\",\"nativeApiVersion\":" +
                    mathType.NativeVersion.ToString(CultureInfo.InvariantCulture) +
                    "}");

                Word.InlineShapes shapes = document.InlineShapes;
                try
                {
                    for (int shapeIndex = 1; shapeIndex <= shapes.Count; shapeIndex++)
                    {
                        Word.InlineShape shape = null;
                        object equationObject = null;
                        bool isMathType = false;
                        try
                        {
                            shape = shapes[shapeIndex];
                            try
                            {
                                isMathType = String.Equals(
                                    shape.OLEFormat.ProgID,
                                    MathTypeProgId,
                                    StringComparison.OrdinalIgnoreCase);
                            }
                            catch
                            {
                                isMathType = false;
                            }

                            if (!isMathType)
                            {
                                continue;
                            }

                            mathTypeCount++;
                            Word.Range range = null;
                            int start = -1;
                            int end = -1;
                            try
                            {
                                range = shape.Range;
                                start = range.Start;
                                end = range.End;
                            }
                            finally
                            {
                                ReleaseComObject(range);
                            }

                            equationObject = ActivateAndGetEquationObject(shape);
                            string readbackTex = GetEquationAsTexWithRetry(
                                mathType,
                                equationObject,
                                mathTypeCount);
                            if (readbackTex.IndexOf(
                                "?",
                                StringComparison.Ordinal) >= 0)
                            {
                                questionMarkCount++;
                            }
                            if (ContainsNonAscii(readbackTex))
                            {
                                nonAsciiCount++;
                            }

                            manifest.WriteLine(
                                "{\"type\":\"formula\",\"sourceIndex\":" +
                                mathTypeCount.ToString(CultureInfo.InvariantCulture) +
                                ",\"shapeIndex\":" +
                                shapeIndex.ToString(CultureInfo.InvariantCulture) +
                                ",\"start\":" +
                                start.ToString(CultureInfo.InvariantCulture) +
                                ",\"end\":" +
                                end.ToString(CultureInfo.InvariantCulture) +
                                ",\"widthPoints\":" +
                                shape.Width.ToString(
                                    "R",
                                    CultureInfo.InvariantCulture) +
                                ",\"heightPoints\":" +
                                shape.Height.ToString(
                                    "R",
                                    CultureInfo.InvariantCulture) +
                                ",\"readbackTex\":\"" +
                                EscapeJson(readbackTex) +
                                "\",\"containsQuestionMark\":" +
                                JsonBoolean(
                                    readbackTex.IndexOf(
                                        "?",
                                        StringComparison.Ordinal) >= 0) +
                                ",\"containsNonAscii\":" +
                                JsonBoolean(ContainsNonAscii(readbackTex)) +
                                "}");
                        }
                        finally
                        {
                            if (equationObject != null)
                            {
                                int closeStatus =
                                    mathType.CloseWithoutSavingEquation(
                                        equationObject);
                                MathTypeApiSession.ThrowIfMathTypeError(
                                    closeStatus,
                                    "MTCloseOleObject during readback");
                            }
                            ReleaseComObject(equationObject);
                            ReleaseComObject(shape);
                        }

                        if (isMathType &&
                            (mathTypeCount == 1 ||
                             mathTypeCount % 10 == 0 ||
                             (expectedMathTypeCount >= 0 &&
                              mathTypeCount == expectedMathTypeCount)))
                        {
                            WriteProgress(
                                progressPath,
                                "readback",
                                mathTypeCount,
                                expectedMathTypeCount,
                                "read MathType equations back to TeX");
                        }
                    }
                }
                finally
                {
                    ReleaseComObject(shapes);
                }

                if (expectedMathTypeCount >= 0 &&
                    mathTypeCount != expectedMathTypeCount)
                {
                    throw new InvalidDataException(
                        "Expected " + expectedMathTypeCount +
                        " MathType objects, but read back " +
                        mathTypeCount + ".");
                }

                manifest.WriteLine(
                    "{\"type\":\"summary\",\"timestamp\":\"" +
                    EscapeJson(DateTime.Now.ToString("o")) +
                    "\",\"mathTypeCount\":" +
                    mathTypeCount.ToString(CultureInfo.InvariantCulture) +
                    ",\"questionMarkCount\":" +
                    questionMarkCount.ToString(CultureInfo.InvariantCulture) +
                    ",\"nonAsciiCount\":" +
                    nonAsciiCount.ToString(CultureInfo.InvariantCulture) +
                    "}");

                WriteProgress(
                    progressPath,
                    "readback",
                    mathTypeCount,
                    expectedMathTypeCount,
                    "readback complete");

                return new MathTypeReadbackSummary
                {
                    DocumentPath = Path.GetFullPath(documentPath),
                    DocumentSha256 = ComputeSha256(documentPath),
                    ManifestPath = Path.GetFullPath(manifestPath),
                    NativeApiVersion = mathType.NativeVersion,
                    MathTypeCount = mathTypeCount,
                    QuestionMarkCount = questionMarkCount,
                    NonAsciiCount = nonAsciiCount,
                    PageCount = document.ComputeStatistics(
                        Word.WdStatistic.wdStatisticPages,
                        false)
                };
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
                if (mathType != null)
                {
                    mathType.Dispose();
                }
                CollectComGarbage();
            }
        }

        private static string GetEquationAsTexWithRetry(
            MathTypeApiSession mathType,
            object equationObject,
            int sourceIndex)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                try
                {
                    return mathType.GetEquationAsTex(equationObject);
                }
                catch (Exception exception)
                {
                    lastException = exception;
                    if (attempt < 3)
                    {
                        Thread.Sleep(250 * attempt);
                    }
                }
            }

            throw new InvalidOperationException(
                "Could not read MathType equation " +
                sourceIndex.ToString(CultureInfo.InvariantCulture) +
                " back to TeX after three attempts.",
                lastException);
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
                "Could not activate a MathType OLE object after three attempts.",
                lastException);
        }

        private static Word.Application CreateHiddenWordApplication()
        {
            Word.Application app = new Word.Application();
            app.Visible = false;
            app.DisplayAlerts = Word.WdAlertLevel.wdAlertsNone;
            app.ScreenUpdating = false;
            app.AutomationSecurity =
                Office.MsoAutomationSecurity.msoAutomationSecurityForceDisable;
            app.Options.SaveNormalPrompt = false;
            app.Options.BackgroundSave = false;
            app.Options.SaveInterval = 0;
            return app;
        }

        private static Word.Document OpenDocument(
            Word.Application app,
            string path)
        {
            return app.Documents.Open(
                FileName: path,
                ConfirmConversions: false,
                ReadOnly: true,
                AddToRecentFiles: false,
                Visible: false,
                OpenAndRepair: false);
        }

        private static void CloseDocumentWithoutSaving(Word.Document document)
        {
            if (document == null)
            {
                return;
            }
            try
            {
                object saveChanges =
                    Word.WdSaveOptions.wdDoNotSaveChanges;
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

        private static bool ContainsNonAscii(string value)
        {
            foreach (char character in value ?? String.Empty)
            {
                if (character > 127)
                {
                    return true;
                }
            }
            return false;
        }

        private static string JsonBoolean(bool value)
        {
            return value ? "true" : "false";
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

        private static void WriteProgress(
            string progressPath,
            string stage,
            int completed,
            int total,
            string message)
        {
            if (String.IsNullOrWhiteSpace(progressPath))
            {
                return;
            }

            string line = DateTime.Now.ToString("o") +
                          "\tstage=" + stage +
                          "\tcompleted=" +
                          completed.ToString(CultureInfo.InvariantCulture) +
                          "\ttotal=" +
                          total.ToString(CultureInfo.InvariantCulture) +
                          "\tmessage=" + message +
                          Environment.NewLine;
            File.AppendAllText(
                progressPath,
                line,
                new UTF8Encoding(false));
        }

        private static string ComputeSha256(string path)
        {
            using (System.Security.Cryptography.SHA256 algorithm =
                System.Security.Cryptography.SHA256.Create())
            using (FileStream stream = File.Open(
                path,
                FileMode.Open,
                FileAccess.Read,
                FileShare.ReadWrite))
            {
                byte[] hash = algorithm.ComputeHash(stream);
                StringBuilder value = new StringBuilder(hash.Length * 2);
                foreach (byte item in hash)
                {
                    value.Append(item.ToString("x2"));
                }
                return value.ToString();
            }
        }

        private static void RequireExistingFile(
            string path,
            string description)
        {
            if (String.IsNullOrWhiteSpace(path) || !File.Exists(path))
            {
                throw new FileNotFoundException(
                    "The " + description + " was not found.",
                    path);
            }
        }

        private static void RequireExistingDirectory(
            string path,
            string description)
        {
            if (String.IsNullOrWhiteSpace(path) || !Directory.Exists(path))
            {
                throw new DirectoryNotFoundException(
                    "The " + description + " was not found: " + path);
            }
        }

        private static void RequireNewPath(
            string path,
            string description)
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

        private static void RequireDistinctPaths(params string[] paths)
        {
            System.Collections.Generic.HashSet<string> seen =
                new System.Collections.Generic.HashSet<string>(
                    StringComparer.OrdinalIgnoreCase);
            foreach (string path in paths)
            {
                if (String.IsNullOrWhiteSpace(path))
                {
                    continue;
                }
                string fullPath = Path.GetFullPath(path)
                    .TrimEnd(
                        Path.DirectorySeparatorChar,
                        Path.AltDirectorySeparatorChar);
                if (!seen.Add(fullPath))
                {
                    throw new ArgumentException(
                        "Readback input and output paths must be distinct: " +
                        fullPath + ".");
                }
            }
        }

        private static void EnsureParentDirectory(string path)
        {
            string parent = Path.GetDirectoryName(Path.GetFullPath(path));
            if (!Directory.Exists(parent))
            {
                Directory.CreateDirectory(parent);
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
