using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;

namespace ThesisMathTypeConversionV2
{
    internal static class OleDataNativeMethods
    {
        internal const uint GlobalMoveableZeroInit = 0x0042;

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        internal static extern uint RegisterClipboardFormat(string name);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        internal static extern int GetClipboardFormatName(
            uint format,
            StringBuilder name,
            int maximumCharacters);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern IntPtr GlobalAlloc(
            uint flags,
            UIntPtr bytes);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern IntPtr GlobalLock(IntPtr handle);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern bool GlobalUnlock(IntPtr handle);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern UIntPtr GlobalSize(IntPtr handle);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern IntPtr GlobalFree(IntPtr handle);

        [DllImport("ole32.dll")]
        internal static extern void ReleaseStgMedium(
            ref STGMEDIUM medium);
    }

    public static class MathTypeOleDataObject
    {
        private static readonly string[] MathMlOutputFormats =
        {
            "MathML Presentation",
            "MathML"
        };

        public static string GetMathMl(object equationObject)
        {
            List<string> failures = new List<string>();
            foreach (string format in MathMlOutputFormats)
            {
                try
                {
                    byte[] bytes = GetBytes(equationObject, format);
                    string value = DecodeUtf8NullTerminated(bytes);
                    if (!String.IsNullOrWhiteSpace(value))
                    {
                        return value;
                    }
                    failures.Add(format + ": empty");
                }
                catch (Exception exception)
                {
                    failures.Add(
                        format +
                        ": " +
                        exception.GetType().Name +
                        " " +
                        exception.Message);
                }
            }
            throw new InvalidOperationException(
                "MathType OLE did not expose readable MathML. " +
                String.Join("; ", failures.ToArray()));
        }

        public static byte[] GetBytes(
            object equationObject,
            string clipboardFormat)
        {
            IDataObject dataObject = RequireDataObject(equationObject);
            FORMATETC format = CreateFormat(clipboardFormat);
            int query = dataObject.QueryGetData(ref format);
            if (query != 0)
            {
                throw new COMException(
                    "OLE QueryGetData rejected " +
                    clipboardFormat +
                    ".",
                    query);
            }

            STGMEDIUM medium;
            dataObject.GetData(ref format, out medium);
            try
            {
                if (medium.tymed != TYMED.TYMED_HGLOBAL ||
                    medium.unionmember == IntPtr.Zero)
                {
                    throw new InvalidOperationException(
                        "OLE format " +
                        clipboardFormat +
                        " did not return TYMED_HGLOBAL.");
                }
                return CopyGlobalMemory(medium.unionmember);
            }
            finally
            {
                OleDataNativeMethods.ReleaseStgMedium(ref medium);
            }
        }

        public static void SetBytes(
            object equationObject,
            string clipboardFormat,
            byte[] value)
        {
            if (value == null || value.Length == 0)
            {
                throw new ArgumentException(
                    "OLE data is empty.",
                    "value");
            }

            IDataObject dataObject = RequireDataObject(equationObject);
            FORMATETC format = CreateFormat(clipboardFormat);
            IntPtr handle = OleDataNativeMethods.GlobalAlloc(
                OleDataNativeMethods.GlobalMoveableZeroInit,
                (UIntPtr)value.Length);
            if (handle == IntPtr.Zero)
            {
                throw new OutOfMemoryException(
                    "Could not allocate an OLE transfer buffer.");
            }

            try
            {
                IntPtr pointer = OleDataNativeMethods.GlobalLock(handle);
                if (pointer == IntPtr.Zero)
                {
                    throw new InvalidOperationException(
                        "Could not lock the OLE transfer buffer.");
                }
                try
                {
                    Marshal.Copy(value, 0, pointer, value.Length);
                }
                finally
                {
                    OleDataNativeMethods.GlobalUnlock(handle);
                }

                STGMEDIUM medium = new STGMEDIUM
                {
                    tymed = TYMED.TYMED_HGLOBAL,
                    unionmember = handle,
                    pUnkForRelease = null
                };
                try
                {
                    dataObject.SetData(ref format, ref medium, true);
                }
                catch (COMException exception)
                {
                    throw new COMException(
                        "OLE SetData rejected " +
                        clipboardFormat +
                        ". SET formats=[" +
                        DescribeFormats(
                            dataObject,
                            DATADIR.DATADIR_SET) +
                        "]; GET formats=[" +
                        DescribeFormats(
                            dataObject,
                            DATADIR.DATADIR_GET) +
                        "].",
                        exception.ErrorCode);
                }
                handle = IntPtr.Zero;
            }
            finally
            {
                if (handle != IntPtr.Zero)
                {
                    OleDataNativeMethods.GlobalFree(handle);
                }
            }
        }

        private static string DescribeFormats(
            IDataObject dataObject,
            DATADIR direction)
        {
            List<string> values = new List<string>();
            IEnumFORMATETC enumerator = null;
            try
            {
                enumerator = dataObject.EnumFormatEtc(direction);
                if (enumerator == null)
                {
                    return "none";
                }

                FORMATETC[] buffer = new FORMATETC[1];
                int[] fetched = new int[1];
                while (enumerator.Next(1, buffer, fetched) == 0 &&
                    fetched[0] == 1)
                {
                    values.Add(
                        ClipboardFormatName(buffer[0].cfFormat) +
                        "/aspect=" +
                        buffer[0].dwAspect +
                        "/tymed=" +
                        buffer[0].tymed +
                        "/lindex=" +
                        buffer[0].lindex);
                }
            }
            catch (Exception exception)
            {
                return "enumeration failed: " +
                    exception.GetType().Name +
                    " " +
                    exception.Message;
            }
            finally
            {
                if (enumerator != null &&
                    Marshal.IsComObject(enumerator))
                {
                    Marshal.FinalReleaseComObject(enumerator);
                }
            }

            return values.Count == 0
                ? "none"
                : String.Join(", ", values.ToArray());
        }

        private static string ClipboardFormatName(short format)
        {
            uint unsignedFormat = unchecked((ushort)format);
            StringBuilder name = new StringBuilder(256);
            int characters = OleDataNativeMethods.GetClipboardFormatName(
                unsignedFormat,
                name,
                name.Capacity);
            if (characters > 0)
            {
                return name.ToString();
            }
            return "#" + unsignedFormat;
        }

        private static IDataObject RequireDataObject(object equationObject)
        {
            if (equationObject == null)
            {
                throw new ArgumentNullException("equationObject");
            }
            IDataObject value = equationObject as IDataObject;
            if (value == null)
            {
                throw new InvalidCastException(
                    "MathType OLE object does not implement IDataObject.");
            }
            return value;
        }

        private static FORMATETC CreateFormat(string clipboardFormat)
        {
            uint registered =
                OleDataNativeMethods.RegisterClipboardFormat(
                    clipboardFormat);
            if (registered == 0 || registered > UInt16.MaxValue)
            {
                throw new InvalidOperationException(
                    "Could not register OLE clipboard format " +
                    clipboardFormat +
                    ".");
            }
            return new FORMATETC
            {
                cfFormat = unchecked((short)registered),
                dwAspect = DVASPECT.DVASPECT_CONTENT,
                lindex = -1,
                ptd = IntPtr.Zero,
                tymed = TYMED.TYMED_HGLOBAL
            };
        }

        private static byte[] CopyGlobalMemory(IntPtr handle)
        {
            ulong unsignedSize =
                OleDataNativeMethods.GlobalSize(handle).ToUInt64();
            if (unsignedSize == 0 || unsignedSize > Int32.MaxValue)
            {
                throw new InvalidOperationException(
                    "OLE HGLOBAL has an invalid size.");
            }

            int size = (int)unsignedSize;
            IntPtr pointer = OleDataNativeMethods.GlobalLock(handle);
            if (pointer == IntPtr.Zero)
            {
                throw new InvalidOperationException(
                    "Could not lock OLE HGLOBAL for reading.");
            }
            try
            {
                byte[] value = new byte[size];
                Marshal.Copy(pointer, value, 0, size);
                return value;
            }
            finally
            {
                OleDataNativeMethods.GlobalUnlock(handle);
            }
        }

        private static string DecodeUtf8NullTerminated(byte[] value)
        {
            int length = Array.IndexOf(value, (byte)0);
            if (length < 0)
            {
                length = value.Length;
            }
            int offset = 0;
            if (length >= 3 &&
                value[0] == 0xEF &&
                value[1] == 0xBB &&
                value[2] == 0xBF)
            {
                offset = 3;
            }
            return new UTF8Encoding(false, true)
                .GetString(value, offset, length - offset)
                .Trim();
        }
    }
}
