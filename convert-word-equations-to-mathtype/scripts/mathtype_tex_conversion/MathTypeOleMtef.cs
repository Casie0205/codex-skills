using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Xml;

namespace ThesisMathTypeConversion
{
    public sealed class MtefAccentScriptNudgeResult
    {
        public byte[] Mtef { get; set; }
        public int NudgedSuperscriptCount { get; set; }
    }

    [ComImport]
    [Guid("0000000B-0000-0000-C000-000000000046")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IStorageNative
    {
        [PreserveSig]
        int CreateStream(
            [MarshalAs(UnmanagedType.LPWStr)] string name,
            uint mode,
            uint reserved1,
            uint reserved2,
            out IStream stream);

        [PreserveSig]
        int OpenStream(
            [MarshalAs(UnmanagedType.LPWStr)] string name,
            IntPtr reserved1,
            uint mode,
            uint reserved2,
            out IStream stream);

        void CreateStorage();
        void OpenStorage();
        void CopyTo();
        void MoveElementTo();
        void Commit(uint flags);
        void Revert();
        void EnumElements();
        void DestroyElement();
        void RenameElement();
        void SetElementTimes();
        void SetClass(ref Guid classId);
        void SetStateBits(uint stateBits, uint mask);
        void Stat(
            out System.Runtime.InteropServices.ComTypes.STATSTG statistics,
            uint flags);
    }

    internal static class MathTypeOleNativeMethods
    {
        [DllImport(
            "ole32.dll",
            CharSet = CharSet.Unicode,
            PreserveSig = true)]
        internal static extern int StgOpenStorage(
            string path,
            IStorageNative priorityStorage,
            uint mode,
            IntPtr excludeNames,
            uint reserved,
            out IStorageNative storage);

        [DllImport(
            "user32.dll",
            CharSet = CharSet.Unicode)]
        internal static extern uint RegisterClipboardFormat(string name);

        [DllImport("kernel32.dll")]
        internal static extern IntPtr GlobalAlloc(uint flags, UIntPtr bytes);

        [DllImport("kernel32.dll")]
        internal static extern IntPtr GlobalLock(IntPtr handle);

        [DllImport("kernel32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool GlobalUnlock(IntPtr handle);

        [DllImport("kernel32.dll")]
        internal static extern IntPtr GlobalFree(IntPtr handle);
    }

    public static class MathTypeOleMtef
    {
        private sealed class AccentAnchor
        {
            public int Offset { get; set; }
            public bool IsStructuredGroup { get; set; }
        }

        private sealed class SuperscriptNudgeTarget
        {
            public int OptionOffset { get; set; }
            public int VerticalOffset { get; set; }
        }

        private const string DocumentPart = "word/document.xml";
        private const string RelationshipsPart =
            "word/_rels/document.xml.rels";
        private const string WordNamespace =
            "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
        private const string RelationshipNamespace =
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
        private const string PackageRelationshipNamespace =
            "http://schemas.openxmlformats.org/package/2006/relationships";
        private const string OfficeNamespace =
            "urn:schemas-microsoft-com:office:office";
        private const string EquationNativeStream = "Equation Native";
        private const string MathTypeEfClipboardFormat = "MathType EF";
        private const uint StorageReadShareExclusive = 0x00000010;
        private const uint GlobalMoveableZeroInit = 0x00000042;
        private const int OleEquationHeaderBytes = 28;
        private const int OleEquationMtefLengthOffset = 8;
        private const byte NudgeOption = 0x08;
        private const int StructuredAccentVerticalOffset = 255;

        private static readonly byte[][] CharacterAccentSignatures =
        {
            new byte[] { 6, 0, 2, 0 },
            new byte[] { 6, 0, 3, 0 }
        };

        // MathType represents a dot/double-dot over a structured base such as
        // \boldsymbol{v} with a limit-style group template rather than a CHAR
        // embellishment. The raw right superscript is about eight points above
        // the normal script line in this structure.
        private static readonly byte[] StructuredAccentSignature =
        {
            3, 0, 23, 32, 0
        };

        private static readonly byte[][] StructuredAccentCharacters =
        {
            new byte[] { 2, 0, 130, 46, 0 },
            new byte[] { 2, 0, 130, 168, 0 }
        };

        private static readonly byte[] DetachedSuperscriptSignature =
        {
            3, 0, 28, 0, 0, 11, 1, 1, 1, 0
        };

        public static byte[] ReadEquationMtefByBookmark(
            string documentPath,
            string bookmarkName)
        {
            if (String.IsNullOrWhiteSpace(documentPath) ||
                !File.Exists(documentPath))
            {
                throw new FileNotFoundException(
                    "The DOCX containing the MathType donor was not found.",
                    documentPath);
            }

            if (String.IsNullOrWhiteSpace(bookmarkName))
            {
                throw new ArgumentException(
                    "A donor bookmark name is required.",
                    "bookmarkName");
            }

            byte[] olePackage;
            using (FileStream stream = File.Open(
                documentPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.ReadWrite))
            using (ZipArchive archive = new ZipArchive(
                stream,
                ZipArchiveMode.Read,
                false))
            {
                string relationId = FindOleRelationshipId(
                    archive,
                    bookmarkName);
                string olePart = ResolveOlePart(archive, relationId);
                ZipArchiveEntry entry = archive.GetEntry(olePart);
                if (entry == null)
                {
                    throw new InvalidDataException(
                        "The bookmarked MathType OLE part is missing: " +
                        olePart);
                }

                using (Stream entryStream = entry.Open())
                using (MemoryStream buffer = new MemoryStream())
                {
                    entryStream.CopyTo(buffer);
                    olePackage = buffer.ToArray();
                }
            }

            return ReadEquationMtefFromOlePackage(olePackage);
        }

        public static MtefAccentScriptNudgeResult
            NudgeDotAccentRightSuperscripts(
                byte[] mtef,
                int expectedRiskCount,
                int verticalOffset,
                char expectedSuperscript)
        {
            if (mtef == null || mtef.Length == 0)
            {
                throw new ArgumentException(
                    "MathType MTEF data is required.",
                    "mtef");
            }

            if (mtef[0] != 5)
            {
                throw new InvalidDataException(
                    "Automatic accent-script repair requires MTEF v5.");
            }

            if (expectedRiskCount <= 0)
            {
                throw new ArgumentOutOfRangeException(
                    "expectedRiskCount");
            }

            if (verticalOffset < -127 || verticalOffset > 126)
            {
                throw new ArgumentOutOfRangeException(
                    "verticalOffset",
                    "The compact MTEF nudge must be between -127 and 126.");
            }

            if (expectedSuperscript > 0x7F ||
                !Char.IsLetterOrDigit(expectedSuperscript))
            {
                throw new InvalidDataException(
                    "Automatic accent-script repair currently supports " +
                    "simple ASCII right superscripts only.");
            }

            List<AccentAnchor> anchors = FindAccentAnchors(mtef);
            if (anchors.Count != expectedRiskCount)
            {
                throw new InvalidDataException(
                    "MathType MTEF accent-script repair expected " +
                    expectedRiskCount +
                    " accent anchor(s), but found " +
                    anchors.Count +
                    ". The equation was not modified.");
            }

            List<SuperscriptNudgeTarget> targets =
                new List<SuperscriptNudgeTarget>();
            foreach (AccentAnchor accent in anchors)
            {
                List<int> templates = FindSequences(
                    mtef,
                    DetachedSuperscriptSignature,
                    accent.Offset + 4,
                    Math.Min(mtef.Length, accent.Offset + 100));
                if (templates.Count == 0)
                {
                    throw new InvalidDataException(
                        "MathType MTEF accent-script repair found no " +
                        "detached superscript template in the local " +
                        "accent window. The equation was not modified.");
                }

                // The MathML-first importer can place a later, unrelated
                // superscript inside the conservative 100-byte search
                // window. The first detached script after the accent is the
                // script structurally attached to that accent.
                int template = templates[0];
                int superscriptContents =
                    template + DetachedSuperscriptSignature.Length;
                int character = FindSingleSimpleCharacterRecord(
                    mtef,
                    superscriptContents);
                if (character < 0)
                {
                    continue;
                }

                int mtCode = ReadCharacterMtCode(mtef, character);
                if (mtCode != expectedSuperscript)
                {
                    throw new InvalidDataException(
                        "MathType MTEF accent-script repair expected " +
                        "superscript '" +
                        expectedSuperscript +
                        "', but the candidate slot has MTCode " +
                        mtCode +
                        ". The equation was not modified.");
                }

                targets.Add(
                    new SuperscriptNudgeTarget
                    {
                        OptionOffset = character + 1,
                        VerticalOffset = accent.IsStructuredGroup
                            ? StructuredAccentVerticalOffset
                            : verticalOffset
                    });
            }

            if (targets.Count != expectedRiskCount)
            {
                throw new InvalidDataException(
                    "MathType MTEF accent-script repair expected " +
                    expectedRiskCount +
                    " superscript slot(s), but found " +
                    targets.Count +
                    ". The equation was not modified.");
            }

            List<byte> corrected = new List<byte>(mtef);
            for (int index = targets.Count - 1;
                index >= 0;
                index--)
            {
                SuperscriptNudgeTarget target = targets[index];
                int optionOffset = target.OptionOffset;
                byte options = corrected[optionOffset];
                if ((options & NudgeOption) != 0)
                {
                    throw new InvalidDataException(
                        "The target MathType superscript already contains " +
                        "a nudge. Automatic repair stopped.");
                }

                corrected[optionOffset] =
                    (byte)(options | NudgeOption);
                corrected.InsertRange(
                    optionOffset + 1,
                    EncodeNudge(0, target.VerticalOffset));
            }

            return new MtefAccentScriptNudgeResult
            {
                Mtef = corrected.ToArray(),
                NudgedSuperscriptCount = targets.Count
            };
        }

        public static void SetEquationFromMtef(
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
                    "MathType MTEF data is required.",
                    "mtef");
            }

            System.Runtime.InteropServices.ComTypes.IDataObject dataObject =
                (System.Runtime.InteropServices.ComTypes.IDataObject)
                equationObject;
            FORMATETC format = new FORMATETC
            {
                cfFormat = unchecked((short)
                    MathTypeOleNativeMethods.RegisterClipboardFormat(
                        MathTypeEfClipboardFormat)),
                dwAspect = DVASPECT.DVASPECT_CONTENT,
                lindex = -1,
                ptd = IntPtr.Zero,
                tymed = TYMED.TYMED_HGLOBAL
            };

            IntPtr handle = MathTypeOleNativeMethods.GlobalAlloc(
                GlobalMoveableZeroInit,
                (UIntPtr)mtef.Length);
            if (handle == IntPtr.Zero)
            {
                throw new OutOfMemoryException(
                    "Could not allocate the MathType MTEF transfer buffer.");
            }

            try
            {
                IntPtr pointer =
                    MathTypeOleNativeMethods.GlobalLock(handle);
                if (pointer == IntPtr.Zero)
                {
                    throw new InvalidOperationException(
                        "Could not lock the MathType MTEF transfer buffer.");
                }

                try
                {
                    Marshal.Copy(mtef, 0, pointer, mtef.Length);
                }
                finally
                {
                    MathTypeOleNativeMethods.GlobalUnlock(handle);
                }

                STGMEDIUM medium = new STGMEDIUM
                {
                    tymed = TYMED.TYMED_HGLOBAL,
                    unionmember = handle,
                    pUnkForRelease = null
                };
                dataObject.SetData(ref format, ref medium, true);
                handle = IntPtr.Zero;
            }
            finally
            {
                if (handle != IntPtr.Zero)
                {
                    MathTypeOleNativeMethods.GlobalFree(handle);
                }
            }
        }

        private static string FindOleRelationshipId(
            ZipArchive archive,
            string bookmarkName)
        {
            ZipArchiveEntry entry = archive.GetEntry(DocumentPart);
            if (entry == null)
            {
                throw new InvalidDataException(
                    "The DOCX is missing " + DocumentPart + ".");
            }

            XmlDocument xml = new XmlDocument();
            using (Stream stream = entry.Open())
            {
                xml.Load(stream);
            }

            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(xml.NameTable);
            namespaces.AddNamespace("w", WordNamespace);
            namespaces.AddNamespace("r", RelationshipNamespace);
            namespaces.AddNamespace("o", OfficeNamespace);
            XmlNode bookmarkStart = xml.SelectSingleNode(
                "//w:bookmarkStart[@w:name='" +
                bookmarkName +
                "']",
                namespaces);
            if (bookmarkStart == null)
            {
                throw new InvalidDataException(
                    "The MathType donor bookmark was not found: " +
                    bookmarkName);
            }

            string bookmarkId = GetAttribute(
                bookmarkStart,
                "id",
                WordNamespace);
            bool inside = false;
            XmlNodeList descendants = xml.SelectNodes("//*");
            if (descendants != null)
            {
                foreach (XmlNode node in descendants)
                {
                    if (node.LocalName == "bookmarkStart" &&
                        node.NamespaceURI == WordNamespace &&
                        GetAttribute(node, "id", WordNamespace) ==
                        bookmarkId)
                    {
                        inside = true;
                        continue;
                    }

                    if (inside &&
                        node.LocalName == "bookmarkEnd" &&
                        node.NamespaceURI == WordNamespace &&
                        GetAttribute(node, "id", WordNamespace) ==
                        bookmarkId)
                    {
                        break;
                    }

                    if (!inside ||
                        node.LocalName != "OLEObject" ||
                        node.NamespaceURI != OfficeNamespace)
                    {
                        continue;
                    }

                    string relationId = GetAttribute(
                        node,
                        "id",
                        RelationshipNamespace);
                    if (!String.IsNullOrWhiteSpace(relationId))
                    {
                        return relationId;
                    }
                }
            }

            throw new InvalidDataException(
                "The MathType donor bookmark does not contain an OLE object.");
        }

        private static string ResolveOlePart(
            ZipArchive archive,
            string relationId)
        {
            ZipArchiveEntry entry = archive.GetEntry(RelationshipsPart);
            if (entry == null)
            {
                throw new InvalidDataException(
                    "The DOCX is missing " + RelationshipsPart + ".");
            }

            XmlDocument xml = new XmlDocument();
            using (Stream stream = entry.Open())
            {
                xml.Load(stream);
            }

            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(xml.NameTable);
            namespaces.AddNamespace(
                "rel",
                PackageRelationshipNamespace);
            XmlNode relationship = xml.SelectSingleNode(
                "//rel:Relationship[@Id='" + relationId + "']",
                namespaces);
            if (relationship == null)
            {
                throw new InvalidDataException(
                    "The bookmarked MathType OLE relationship is missing: " +
                    relationId);
            }

            string target = GetAttribute(
                relationship,
                "Target",
                String.Empty);
            if (String.IsNullOrWhiteSpace(target))
            {
                throw new InvalidDataException(
                    "The bookmarked MathType OLE relationship has no target.");
            }

            string normalized = target.Replace('\\', '/');
            while (normalized.StartsWith("../", StringComparison.Ordinal))
            {
                normalized = normalized.Substring(3);
            }

            return normalized.StartsWith("word/", StringComparison.Ordinal)
                ? normalized
                : "word/" + normalized.TrimStart('/');
        }

        public static byte[] ReadEquationMtefFromOlePackage(
            byte[] olePackage)
        {
            string temporaryPath = Path.Combine(
                Path.GetTempPath(),
                "codex-mathtype-" +
                Guid.NewGuid().ToString("N") +
                ".bin");
            File.WriteAllBytes(temporaryPath, olePackage);
            IStorageNative storage = null;
            IStream stream = null;
            try
            {
                int status = MathTypeOleNativeMethods.StgOpenStorage(
                    temporaryPath,
                    null,
                    StorageReadShareExclusive,
                    IntPtr.Zero,
                    0,
                    out storage);
                Marshal.ThrowExceptionForHR(status);

                status = storage.OpenStream(
                    EquationNativeStream,
                    IntPtr.Zero,
                    StorageReadShareExclusive,
                    0,
                    out stream);
                Marshal.ThrowExceptionForHR(status);

                System.Runtime.InteropServices.ComTypes.STATSTG statistics;
                stream.Stat(out statistics, 1);
                int length = checked((int)statistics.cbSize);
                byte[] equationNative = new byte[length];
                stream.Read(equationNative, length, IntPtr.Zero);
                if (equationNative.Length < OleEquationHeaderBytes)
                {
                    throw new InvalidDataException(
                        "The MathType Equation Native stream is truncated.");
                }

                int headerBytes = BitConverter.ToUInt16(
                    equationNative,
                    0);
                int mtefLength = BitConverter.ToInt32(
                    equationNative,
                    OleEquationMtefLengthOffset);
                if (headerBytes < OleEquationHeaderBytes ||
                    mtefLength <= 0 ||
                    headerBytes + mtefLength > equationNative.Length)
                {
                    throw new InvalidDataException(
                        "The MathType Equation Native header is invalid.");
                }

                byte[] mtef = new byte[mtefLength];
                Buffer.BlockCopy(
                    equationNative,
                    headerBytes,
                    mtef,
                    0,
                    mtefLength);
                return mtef;
            }
            finally
            {
                if (stream != null && Marshal.IsComObject(stream))
                {
                    Marshal.FinalReleaseComObject(stream);
                }

                if (storage != null && Marshal.IsComObject(storage))
                {
                    Marshal.FinalReleaseComObject(storage);
                }

                try
                {
                    File.Delete(temporaryPath);
                }
                catch
                {
                }
            }
        }

        private static List<AccentAnchor> FindAccentAnchors(
            byte[] value)
        {
            List<AccentAnchor> anchors = new List<AccentAnchor>();
            foreach (byte[] signature in CharacterAccentSignatures)
            {
                int start = 0;
                while (start < value.Length)
                {
                    int found = FindSequence(
                        value,
                        signature,
                        start,
                        value.Length);
                    if (found < 0)
                    {
                        break;
                    }

                    anchors.Add(
                        new AccentAnchor
                        {
                            Offset = found,
                            IsStructuredGroup = false
                        });
                    start = found + signature.Length;
                }
            }

            int structuredStart = 0;
            while (structuredStart < value.Length)
            {
                int structured = FindSequence(
                    value,
                    StructuredAccentSignature,
                    structuredStart,
                    value.Length);
                if (structured < 0)
                {
                    break;
                }

                bool containsDotOrDoubleDot = false;
                foreach (byte[] accentCharacter in
                    StructuredAccentCharacters)
                {
                    if (FindSequence(
                        value,
                        accentCharacter,
                        structured + StructuredAccentSignature.Length,
                        Math.Min(value.Length, structured + 80)) >= 0)
                    {
                        containsDotOrDoubleDot = true;
                        break;
                    }
                }
                if (containsDotOrDoubleDot)
                {
                    anchors.Add(
                        new AccentAnchor
                        {
                            Offset = structured,
                            IsStructuredGroup = true
                        });
                }
                structuredStart =
                    structured + StructuredAccentSignature.Length;
            }

            anchors.Sort(
                delegate(AccentAnchor left, AccentAnchor right)
                {
                    return left.Offset.CompareTo(right.Offset);
                });
            return anchors;
        }

        private static byte[] EncodeNudge(int horizontal, int vertical)
        {
            if (horizontal >= -128 &&
                horizontal < 127 &&
                vertical >= -128 &&
                vertical < 127)
            {
                return new byte[]
                {
                    (byte)(horizontal + 128),
                    (byte)(vertical + 128)
                };
            }

            if (horizontal < Int16.MinValue ||
                horizontal > Int16.MaxValue ||
                vertical < Int16.MinValue ||
                vertical > Int16.MaxValue)
            {
                throw new ArgumentOutOfRangeException(
                    "vertical",
                    "MathType MTEF long nudge values must fit Int16.");
            }

            short dx = (short)horizontal;
            short dy = (short)vertical;
            return new byte[]
            {
                128,
                128,
                (byte)(dx & 0xFF),
                (byte)((dx >> 8) & 0xFF),
                (byte)(dy & 0xFF),
                (byte)((dy >> 8) & 0xFF)
            };
        }

        private static int FindSingleSimpleCharacterRecord(
            byte[] mtef,
            int start)
        {
            int current = start;
            int limit = Math.Min(mtef.Length, start + 80);
            while (current < limit)
            {
                byte record = mtef[current];
                if (record == 2)
                {
                    int afterCharacter =
                        SkipCharacterRecord(mtef, current);
                    return afterCharacter >= 0 &&
                           afterCharacter < mtef.Length &&
                           mtef[afterCharacter] == 0
                        ? current
                        : -1;
                }

                if (record == 15)
                {
                    current = SkipUnsignedInteger(mtef, current + 1);
                    continue;
                }

                if (record >= 10 && record <= 14)
                {
                    current++;
                    continue;
                }

                if (record == 9)
                {
                    if (current + 1 >= mtef.Length)
                    {
                        return -1;
                    }

                    byte sizeKind = mtef[current + 1];
                    current += sizeKind == 101
                        ? 4
                        : sizeKind == 100
                            ? 5
                            : 3;
                    continue;
                }

                return -1;
            }

            return -1;
        }

        private static int SkipCharacterRecord(
            byte[] mtef,
            int offset)
        {
            if (offset + 2 > mtef.Length || mtef[offset] != 2)
            {
                return -1;
            }

            int current = offset + 1;
            byte options = mtef[current++];
            if ((options & NudgeOption) != 0)
            {
                current = SkipNudge(mtef, current);
                if (current < 0)
                {
                    return -1;
                }
            }

            current = SkipSignedInteger(mtef, current);
            if (current < 0)
            {
                return -1;
            }

            if ((options & 0x20) == 0)
            {
                current += 2;
            }
            if ((options & 0x04) != 0)
            {
                current++;
            }
            if ((options & 0x10) != 0)
            {
                current += 2;
            }
            if (current > mtef.Length)
            {
                return -1;
            }

            if ((options & 0x01) != 0)
            {
                while (current < mtef.Length &&
                    mtef[current] == 6)
                {
                    if (current + 2 > mtef.Length)
                    {
                        return -1;
                    }

                    byte embellishmentOptions = mtef[current + 1];
                    current += 2;
                    if ((embellishmentOptions & NudgeOption) != 0)
                    {
                        current = SkipNudge(mtef, current);
                        if (current < 0)
                        {
                            return -1;
                        }
                    }

                    current++;
                }

                if (current >= mtef.Length || mtef[current] != 0)
                {
                    return -1;
                }
                current++;
            }

            return current;
        }

        private static int ReadCharacterMtCode(
            byte[] mtef,
            int offset)
        {
            if (offset + 2 > mtef.Length || mtef[offset] != 2)
            {
                return -1;
            }

            int current = offset + 1;
            byte options = mtef[current++];
            if ((options & NudgeOption) != 0)
            {
                current = SkipNudge(mtef, current);
                if (current < 0)
                {
                    return -1;
                }
            }

            current = SkipSignedInteger(mtef, current);
            if (current < 0 ||
                (options & 0x20) != 0 ||
                current + 2 > mtef.Length)
            {
                return -1;
            }

            return mtef[current] | (mtef[current + 1] << 8);
        }

        private static int SkipNudge(byte[] value, int offset)
        {
            if (offset + 2 > value.Length)
            {
                return -1;
            }

            bool longForm =
                value[offset] == 128 &&
                value[offset + 1] == 128;
            int next = offset + (longForm ? 6 : 2);
            return next <= value.Length ? next : -1;
        }

        private static int SkipSignedInteger(
            byte[] value,
            int offset)
        {
            if (offset >= value.Length)
            {
                return -1;
            }

            int next = offset + (value[offset] == 255 ? 3 : 1);
            return next <= value.Length ? next : -1;
        }

        private static int SkipUnsignedInteger(
            byte[] value,
            int offset)
        {
            if (offset >= value.Length)
            {
                return value.Length;
            }

            return value[offset] == 255
                ? Math.Min(value.Length, offset + 3)
                : offset + 1;
        }

        private static int FindSequence(
            byte[] value,
            byte[] pattern,
            int start,
            int end)
        {
            int maximum = Math.Min(
                value.Length - pattern.Length,
                end - pattern.Length);
            for (int offset = Math.Max(0, start);
                offset <= maximum;
                offset++)
            {
                bool matches = true;
                for (int index = 0; index < pattern.Length; index++)
                {
                    if (value[offset + index] != pattern[index])
                    {
                        matches = false;
                        break;
                    }
                }

                if (matches)
                {
                    return offset;
                }
            }

            return -1;
        }

        private static List<int> FindSequences(
            byte[] value,
            byte[] pattern,
            int start,
            int end)
        {
            List<int> matches = new List<int>();
            int current = Math.Max(0, start);
            while (current < end)
            {
                int found = FindSequence(
                    value,
                    pattern,
                    current,
                    end);
                if (found < 0)
                {
                    break;
                }

                matches.Add(found);
                current = found + 1;
            }
            return matches;
        }

        private static string GetAttribute(
            XmlNode node,
            string localName,
            string namespaceUri)
        {
            if (node == null || node.Attributes == null)
            {
                return String.Empty;
            }

            XmlAttribute attribute = String.IsNullOrEmpty(namespaceUri)
                ? node.Attributes[localName]
                : node.Attributes[localName, namespaceUri];
            return attribute == null ? String.Empty : attribute.Value;
        }
    }
}
