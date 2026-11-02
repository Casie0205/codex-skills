using System;
using System.Runtime.InteropServices;
using System.Text;

namespace ThesisMathTypeConversion
{
    internal static class MathTypeNativeMethods
    {
        private const string MathPageLibrary = "MathPage.WLL";

        [DllImport(MathPageLibrary, CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTInitAPI(short options, short timeout);

        [DllImport(MathPageLibrary, CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTAPIVersion(short apiVersion);

        [DllImport(MathPageLibrary, CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTSetEqnFromLangStr(
            [MarshalAs(UnmanagedType.IDispatch)] object equationObject,
            short languageType,
            byte[] languageString,
            int stringLength);

        [DllImport(
            MathPageLibrary,
            CallingConvention = CallingConvention.Winapi,
            CharSet = CharSet.Ansi)]
        internal static extern int MTGetLangStrFromEqn(
            [MarshalAs(UnmanagedType.IDispatch)] object equationObject,
            short languageType,
            StringBuilder languageString,
            ref int stringLength);

        [DllImport(
            MathPageLibrary,
            CallingConvention = CallingConvention.Winapi,
            CharSet = CharSet.Ansi)]
        internal static extern int MTGetPrefsFromFile(
            string preferenceFile,
            StringBuilder preferences,
            int preferencesLength);

        [DllImport(
            MathPageLibrary,
            CallingConvention = CallingConvention.Winapi,
            CharSet = CharSet.Ansi)]
        internal static extern int MTSetMTPrefs(
            short mode,
            string preferences,
            short timeout);

        [DllImport(MathPageLibrary, CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTCloseOleObject(
            int saveOptions,
            [MarshalAs(UnmanagedType.IDispatch)] object equationObject);

        [DllImport(MathPageLibrary, CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTTermAPI();
    }

    public sealed class MathTypeApiSession : IDisposable
    {
        private const short LaunchAsNeeded = 0;
        private const short TimeoutSeconds = 30;
        private const short ApiVersion = 5;
        private const short TexInputLanguage = 1;
        private const short PreferencesForNextEquation = 1;
        private const short InlineEquationPreferences = 4;
        private const short NoPreferenceTimeout = -1;
        private const int SaveOleObject = 1;
        private const int DoNotSaveOleObject = 0;
        private const int MathTypeOk = 0;

        private bool active;

        public MathTypeApiSession(string mathPageDirectory)
        {
            if (String.IsNullOrWhiteSpace(mathPageDirectory))
            {
                throw new ArgumentException("MathPage directory is required.", "mathPageDirectory");
            }

            string currentPath = Environment.GetEnvironmentVariable("Path") ?? String.Empty;
            if (currentPath.IndexOf(mathPageDirectory, StringComparison.OrdinalIgnoreCase) < 0)
            {
                Environment.SetEnvironmentVariable(
                    "Path",
                    currentPath + ";" + mathPageDirectory,
                    EnvironmentVariableTarget.Process);
            }

            int initResult = MathTypeNativeMethods.MTInitAPI(LaunchAsNeeded, TimeoutSeconds);
            if (initResult <= 0)
            {
                throw new InvalidOperationException(
                    "MathType API initialization failed with status " + initResult + ".");
            }

            active = true;
            NativeVersion = MathTypeNativeMethods.MTAPIVersion(ApiVersion);
            if (NativeVersion <= 0)
            {
                Dispose();
                throw new InvalidOperationException(
                    "MathType API version check failed with status " + NativeVersion + ".");
            }
        }

        public int NativeVersion { get; private set; }

        public int SetEquationFromInlineTex(object equationObject, string tex)
        {
            if (!active)
            {
                throw new ObjectDisposedException("MathTypeApiSession");
            }

            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }

            if (String.IsNullOrWhiteSpace(tex))
            {
                throw new ArgumentException("TeX input is empty.", "tex");
            }

            string inlineTex = WrapAsInlineTex(tex);
            byte[] unicodeBytes = Encoding.Unicode.GetBytes(inlineTex + "\0");
            return MathTypeNativeMethods.MTSetEqnFromLangStr(
                equationObject,
                TexInputLanguage,
                unicodeBytes,
                inlineTex.Length);
        }

        public string GetEquationAsTex(object equationObject)
        {
            if (!active)
            {
                throw new ObjectDisposedException("MathTypeApiSession");
            }

            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }

            int stringLength = 0;
            int sizeStatus = MathTypeNativeMethods.MTGetLangStrFromEqn(
                equationObject,
                TexInputLanguage,
                null,
                ref stringLength);
            ThrowIfMathTypeError(sizeStatus, "MTGetLangStrFromEqn size query");
            if (stringLength <= 0)
            {
                throw new InvalidOperationException(
                    "MathType returned an empty TeX length.");
            }

            StringBuilder buffer = new StringBuilder(stringLength + 2);
            int readStatus = MathTypeNativeMethods.MTGetLangStrFromEqn(
                equationObject,
                TexInputLanguage,
                buffer,
                ref stringLength);
            ThrowIfMathTypeError(readStatus, "MTGetLangStrFromEqn read");
            return buffer.ToString().TrimEnd('\0');
        }

        public int ApplyPreferencesForNextInlineEquation(string preferencePath)
        {
            if (!active)
            {
                throw new ObjectDisposedException("MathTypeApiSession");
            }

            if (String.IsNullOrWhiteSpace(preferencePath) ||
                !System.IO.File.Exists(preferencePath))
            {
                throw new ArgumentException(
                    "A valid MathType preference file is required.",
                    "preferencePath");
            }

            int requiredLength = MathTypeNativeMethods.MTGetPrefsFromFile(
                preferencePath,
                null,
                0);
            if (requiredLength <= 0)
            {
                throw new InvalidOperationException(
                    "MathType could not read preferences from " +
                    preferencePath +
                    "; status " + requiredLength + ".");
            }

            StringBuilder preferences = new StringBuilder(requiredLength + 2);
            int readStatus = MathTypeNativeMethods.MTGetPrefsFromFile(
                preferencePath,
                preferences,
                requiredLength);
            ThrowIfMathTypeError(readStatus, "MTGetPrefsFromFile");

            return MathTypeNativeMethods.MTSetMTPrefs(
                (short)(PreferencesForNextEquation + InlineEquationPreferences),
                preferences.ToString(),
                NoPreferenceTimeout);
        }

        public int CloseAndSaveEquation(object equationObject)
        {
            if (!active)
            {
                throw new ObjectDisposedException("MathTypeApiSession");
            }

            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }

            return MathTypeNativeMethods.MTCloseOleObject(
                SaveOleObject,
                equationObject);
        }

        public int CloseWithoutSavingEquation(object equationObject)
        {
            if (!active)
            {
                throw new ObjectDisposedException("MathTypeApiSession");
            }

            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }

            return MathTypeNativeMethods.MTCloseOleObject(
                DoNotSaveOleObject,
                equationObject);
        }

        public static void ThrowIfMathTypeError(int status, string operation)
        {
            if (status != MathTypeOk)
            {
                throw new InvalidOperationException(
                    operation + " failed with MathType status " + status + ".");
            }
        }

        public void Dispose()
        {
            if (!active)
            {
                return;
            }

            MathTypeNativeMethods.MTTermAPI();
            active = false;
        }

        private static string WrapAsInlineTex(string tex)
        {
            string value = tex.Trim();
            if (value.Length >= 2 &&
                value[0] == '$' &&
                value[value.Length - 1] == '$')
            {
                return value;
            }

            return "$" + value + "$";
        }
    }
}
