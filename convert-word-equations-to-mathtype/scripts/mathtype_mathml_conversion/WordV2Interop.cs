using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using Office = Microsoft.Office.Core;
using Word = Microsoft.Office.Interop.Word;

namespace ThesisMathTypeConversionV2
{
    internal static class WordV2Interop
    {
        internal const string MathTypeProgId = "Equation.DSMT4";
        private const string BlankEquationBookmark = "MTBlankEqn";
        private const int EmbeddedEquationSearchWidth = 12;

        internal static Word.Application CreateHiddenApplication()
        {
            Word.Application app = new Word.Application();
            app.Visible = false;
            app.DisplayAlerts = Word.WdAlertLevel.wdAlertsNone;
            app.ScreenUpdating = false;
            app.AutomationSecurity =
                Office.MsoAutomationSecurity.msoAutomationSecurityForceDisable;
            app.Options.BackgroundSave = false;
            return app;
        }

        internal static Word.InlineShape InsertBlankMathType(
            Word.Document document,
            int start,
            string blankEquationPath)
        {
            Word.Range insertion = null;
            try
            {
                insertion = document.Range(start, start);
                insertion.InsertFile(
                    blankEquationPath,
                    BlankEquationBookmark,
                    false,
                    false,
                    false);
                DeleteBookmark(document, BlankEquationBookmark);
                int searchEnd = Math.Min(
                    document.Content.End - 1,
                    start + EmbeddedEquationSearchWidth);
                insertion.SetRange(start, searchEnd);
                Word.InlineShape shape =
                    FindInsertedMathTypeShape(insertion, start);
                if (shape == null)
                {
                    shape = FindInsertedMathTypeShape(
                        document,
                        start);
                }
                if (shape == null)
                {
                    throw new InvalidOperationException(
                        "Could not locate the inserted inline MathType object.");
                }
                return shape;
            }
            finally
            {
                ReleaseComObject(insertion);
            }
        }

        internal static void DeleteInlineShape(Word.InlineShape shape)
        {
            if (shape == null)
            {
                return;
            }
            try
            {
                shape.Delete();
            }
            catch
            {
            }
        }

        internal static object ActivateAndGetEquationObject(
            Word.InlineShape shape)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                try
                {
                    shape.OLEFormat.DoVerb(2);
                    return shape.OLEFormat.Object;
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
                "Could not activate the MathType OLE object.",
                lastException);
        }

        internal static void UpdateEquationField(
            Word.InlineShape shape)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                Word.Range range = null;
                Word.Fields fields = null;
                try
                {
                    range = shape.Range;
                    fields = range.Fields;
                    fields.Update();
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
                    ReleaseComObject(fields);
                    ReleaseComObject(range);
                }
            }
            throw new InvalidOperationException(
                "Could not update the MathType embedding field.",
                lastException);
        }

        internal static int CountInlineMathTypeObjects(
            Word.Document document)
        {
            int count = 0;
            Word.InlineShapes shapes = null;
            try
            {
                shapes = document.InlineShapes;
                for (int index = 1; index <= shapes.Count; index++)
                {
                    Word.InlineShape shape = null;
                    try
                    {
                        shape = shapes[index];
                        if (IsMathTypeShape(shape))
                        {
                            count++;
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
            return count;
        }

        internal static void CloseDocumentWithoutSaving(
            Word.Document document)
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

        internal static void QuitApplication(Word.Application app)
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

        internal static void ReleaseComObject(object value)
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

        internal static void CollectComGarbage()
        {
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            GC.WaitForPendingFinalizers();
        }

        internal static void DeleteFailedOutput(
            string outputPath,
            Action<string> log)
        {
            Exception lastException = null;
            for (int attempt = 1; attempt <= 5; attempt++)
            {
                if (!File.Exists(outputPath))
                {
                    return;
                }
                try
                {
                    File.Delete(outputPath);
                    if (log != null)
                    {
                        log("deleted incomplete V2 output");
                    }
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
            if (log != null)
            {
                log(
                    "failed to delete incomplete V2 output: " +
                    (lastException == null
                        ? "unknown"
                        : lastException.Message));
            }
            throw new InvalidOperationException(
                "The incomplete V2 output could not be deleted.",
                lastException);
        }

        private static Word.InlineShape FindInsertedMathTypeShape(
            Word.Range insertion,
            int expectedStart)
        {
            Word.InlineShapes shapes = null;
            Word.InlineShape fallback = null;
            try
            {
                shapes = insertion.InlineShapes;
                for (int index = 1; index <= shapes.Count; index++)
                {
                    Word.InlineShape candidate = null;
                    bool keep = false;
                    try
                    {
                        candidate = shapes[index];
                        if (!IsMathTypeShape(candidate))
                        {
                            continue;
                        }

                        Word.Range range = null;
                        try
                        {
                            range = candidate.Range;
                            if (range.Start == expectedStart)
                            {
                                ReleaseComObject(fallback);
                                fallback = null;
                                keep = true;
                                return candidate;
                            }
                        }
                        finally
                        {
                            ReleaseComObject(range);
                        }

                        if (fallback == null)
                        {
                            fallback = candidate;
                            keep = true;
                        }
                    }
                    finally
                    {
                        if (!keep)
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

        private static Word.InlineShape FindInsertedMathTypeShape(
            Word.Document document,
            int expectedStart)
        {
            Word.InlineShapes shapes = null;
            Word.InlineShape nearest = null;
            int nearestDistance = Int32.MaxValue;
            try
            {
                shapes = document.InlineShapes;
                for (int index = 1; index <= shapes.Count; index++)
                {
                    Word.InlineShape candidate = null;
                    bool keep = false;
                    try
                    {
                        candidate = shapes[index];
                        if (!IsMathTypeShape(candidate))
                        {
                            continue;
                        }

                        Word.Range range = null;
                        try
                        {
                            range = candidate.Range;
                            int distance = Math.Abs(
                                range.Start - expectedStart);
                            if (distance == 0)
                            {
                                ReleaseComObject(nearest);
                                nearest = null;
                                keep = true;
                                return candidate;
                            }
                            if (distance < nearestDistance &&
                                distance <= EmbeddedEquationSearchWidth)
                            {
                                ReleaseComObject(nearest);
                                nearest = candidate;
                                nearestDistance = distance;
                                keep = true;
                            }
                        }
                        finally
                        {
                            ReleaseComObject(range);
                        }
                    }
                    finally
                    {
                        if (!keep)
                        {
                            ReleaseComObject(candidate);
                        }
                    }
                }
                return nearest;
            }
            finally
            {
                ReleaseComObject(shapes);
            }
        }

        private static bool IsMathTypeShape(Word.InlineShape shape)
        {
            if (shape == null)
            {
                return false;
            }

            Word.OLEFormat oleFormat = null;
            try
            {
                oleFormat = shape.OLEFormat;
                return
                    oleFormat != null &&
                    String.Equals(
                        oleFormat.ProgID,
                        MathTypeProgId,
                        StringComparison.OrdinalIgnoreCase);
            }
            catch (COMException)
            {
                return false;
            }
            catch (NullReferenceException)
            {
                return false;
            }
            finally
            {
                ReleaseComObject(oleFormat);
            }
        }

        private static void DeleteBookmark(
            Word.Document document,
            string bookmarkName)
        {
            Word.Bookmarks bookmarks = null;
            Word.Bookmark bookmark = null;
            try
            {
                bookmarks = document.Bookmarks;
                if (bookmarks.Exists(bookmarkName))
                {
                    bookmark = bookmarks[bookmarkName];
                    bookmark.Delete();
                }
            }
            catch
            {
            }
            finally
            {
                ReleaseComObject(bookmark);
                ReleaseComObject(bookmarks);
            }
        }
    }
}
