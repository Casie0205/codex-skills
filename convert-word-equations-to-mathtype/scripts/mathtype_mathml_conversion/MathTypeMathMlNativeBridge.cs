using System;
using System.Runtime.InteropServices;
using System.Text;

namespace ThesisMathTypeConversionV2
{
    internal static class MathTypeMathMlNativeMethods
    {
        private const string MathPageLibrary = "MathPage.WLL";

        [DllImport(
            MathPageLibrary,
            CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTSetEqnFromLangStr(
            [MarshalAs(UnmanagedType.IDispatch)] object equationObject,
            short languageType,
            byte[] languageString,
            int stringLength);

        [DllImport(
            MathPageLibrary,
            CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTSetEqnFromLangBytes(
            [MarshalAs(UnmanagedType.IDispatch)] object equationObject,
            short languageType,
            byte[] languageBuffer,
            int bufferLength);

        [DllImport(
            MathPageLibrary,
            CallingConvention = CallingConvention.Winapi)]
        internal static extern int MTGetLangBytesFromEqn(
            [MarshalAs(UnmanagedType.IDispatch)] object equationObject,
            short languageType,
            byte[] languageBuffer,
            ref int bufferLength);
    }

    internal static class MathTypeMathMlNativeBridge
    {
        private const short MathMlLanguage = 2;
        private const short MtefLanguage = 3;
        private const int MathTypeOk = 0;

        internal static void SetEquationFromMathMl(
            object equationObject,
            string mathMl)
        {
            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }
            if (String.IsNullOrWhiteSpace(mathMl))
            {
                throw new ArgumentException(
                    "MathML input is empty.",
                    "mathMl");
            }

            byte[] unicodeBytes =
                Encoding.Unicode.GetBytes(mathMl + "\0");
            int status =
                MathTypeMathMlNativeMethods.MTSetEqnFromLangStr(
                    equationObject,
                    MathMlLanguage,
                    unicodeBytes,
                    mathMl.Length);
            if (status != MathTypeOk)
            {
                throw new InvalidOperationException(
                    "MTSetEqnFromLangStr(MathML) failed with MathType " +
                    "status " +
                    status +
                    ".");
            }
        }

        internal static byte[] GetEquationMtef(object equationObject)
        {
            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }

            int requiredLength = 0;
            byte[] probe = new byte[1];
            int sizeStatus =
                MathTypeMathMlNativeMethods.MTGetLangBytesFromEqn(
                    equationObject,
                    MtefLanguage,
                    probe,
                    ref requiredLength);
            if (sizeStatus != MathTypeOk || requiredLength <= 0)
            {
                throw new InvalidOperationException(
                    "MTGetLangBytesFromEqn(MTEF) size query failed with " +
                    "MathType status " +
                    sizeStatus +
                    " and length " +
                    requiredLength +
                    ".");
            }

            byte[] value = new byte[requiredLength];
            int actualLength = value.Length;
            int readStatus =
                MathTypeMathMlNativeMethods.MTGetLangBytesFromEqn(
                    equationObject,
                    MtefLanguage,
                    value,
                    ref actualLength);
            if (readStatus != MathTypeOk ||
                actualLength <= 0 ||
                actualLength > value.Length)
            {
                throw new InvalidOperationException(
                    "MTGetLangBytesFromEqn(MTEF) read failed with " +
                    "MathType status " +
                    readStatus +
                    " and length " +
                    actualLength +
                    ".");
            }
            if (actualLength == value.Length)
            {
                return value;
            }

            byte[] trimmed = new byte[actualLength];
            Buffer.BlockCopy(value, 0, trimmed, 0, actualLength);
            return trimmed;
        }

        internal static void SetEquationFromMtef(
            object equationObject,
            byte[] mtef)
        {
            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }
            if (mtef == null || mtef.Length == 0)
            {
                throw new ArgumentException(
                    "MTEF input is empty.",
                    "mtef");
            }

            int status =
                MathTypeMathMlNativeMethods.MTSetEqnFromLangBytes(
                    equationObject,
                    MtefLanguage,
                    mtef,
                    mtef.Length);
            if (status != MathTypeOk)
            {
                throw new InvalidOperationException(
                    "MTSetEqnFromLangStr(MTEF) failed with MathType " +
                    "status " +
                    status +
                    ".");
            }
        }
    }
}
