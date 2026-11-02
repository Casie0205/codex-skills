using System;
using System.Collections.Generic;
using System.Globalization;

namespace ThesisMathTypeConversionV2
{
    public static class MtefStyleAudit
    {
        private sealed class CharacterDescriptor
        {
            public int MtCode { get; set; }
            public int Typeface { get; set; }
        }

        private const byte CharacterRecord = 2;
        private const byte NudgeOption = 0x08;
        private const byte FontPosition8Option = 0x04;
        private const byte FontPosition16Option = 0x10;
        private const byte NoMtCodeOption = 0x20;
        private const byte KnownCharacterOptions = 0x3F;
        private const int VectorTypeface = 7;

        public static string GetStyledCharacterSequence(byte[] mtef)
        {
            List<string> codes = new List<string>();
            foreach (CharacterDescriptor character in
                ReadCharacterDescriptors(mtef))
            {
                if (IsStyledTypeface(character.Typeface))
                {
                    codes.Add(
                        character.MtCode.ToString(
                            CultureInfo.InvariantCulture));
                }
            }
            return String.Join(",", codes.ToArray());
        }

        public static string GetStyledCharacterDescriptorSequence(
            byte[] mtef)
        {
            List<string> values = new List<string>();
            foreach (CharacterDescriptor character in
                ReadCharacterDescriptors(mtef))
            {
                if (IsStyledTypeface(character.Typeface))
                {
                    values.Add(
                        character.MtCode.ToString(
                            CultureInfo.InvariantCulture) +
                        ":" +
                        character.Typeface.ToString(
                            CultureInfo.InvariantCulture));
                }
            }
            return String.Join(",", values.ToArray());
        }

        public static string GetCharacterStyleSequence(byte[] mtef)
        {
            List<string> values = new List<string>();
            foreach (CharacterDescriptor character in
                ReadCharacterDescriptors(mtef))
            {
                string style = GetStyleCode(character.Typeface);
                if (style != null)
                {
                    values.Add(
                        character.MtCode.ToString(
                            CultureInfo.InvariantCulture) +
                        ":" +
                        style);
                }
            }
            return String.Join(",", values.ToArray());
        }

        private static IList<CharacterDescriptor>
            ReadCharacterDescriptors(byte[] mtef)
        {
            if (mtef == null || mtef.Length < 8 || mtef[0] != 5)
            {
                throw new ArgumentException(
                    "MTEF v5 data is required.",
                    "mtef");
            }

            List<CharacterDescriptor> characters =
                new List<CharacterDescriptor>();
            for (int offset = FindRecordStart(mtef);
                offset + 4 < mtef.Length;
                offset++)
            {
                if (mtef[offset] != CharacterRecord)
                {
                    continue;
                }

                int cursor = offset + 1;
                byte options = mtef[cursor++];
                if ((options & ~KnownCharacterOptions) != 0)
                {
                    continue;
                }
                if ((options & NudgeOption) != 0 &&
                    !SkipNudge(mtef, ref cursor))
                {
                    continue;
                }

                int typeface;
                if (!ReadSignedInteger(
                    mtef,
                    ref cursor,
                    out typeface))
                {
                    continue;
                }
                if ((options & NoMtCodeOption) != 0 ||
                    cursor + 1 >= mtef.Length)
                {
                    continue;
                }

                int mtCode =
                    mtef[cursor] |
                    (mtef[cursor + 1] << 8);
                cursor += 2;
                if ((options & FontPosition8Option) != 0)
                {
                    cursor++;
                }
                if ((options & FontPosition16Option) != 0)
                {
                    cursor += 2;
                }
                if (cursor > mtef.Length)
                {
                    continue;
                }

                characters.Add(
                    new CharacterDescriptor
                    {
                        MtCode = mtCode,
                        Typeface = typeface
                    });
            }
            return characters;
        }

        private static bool IsStyledTypeface(int typeface)
        {
            return typeface < 0 || typeface == VectorTypeface;
        }

        private static string GetStyleCode(int typeface)
        {
            if (typeface == VectorTypeface)
            {
                return "B";
            }
            if (typeface < 0)
            {
                return "BI";
            }
            return null;
        }

        public static string GetExpectedStyleSubsequence(
            byte[] mtef,
            string expectedSequence)
        {
            if (String.IsNullOrWhiteSpace(expectedSequence))
            {
                return String.Empty;
            }

            string[] expected = expectedSequence.Split(',');
            string[] actual =
                GetCharacterStyleSequence(mtef).Split(',');
            List<string> matched = new List<string>();
            int expectedIndex = 0;
            foreach (string code in actual)
            {
                if (expectedIndex >= expected.Length)
                {
                    break;
                }
                if (String.Equals(
                    code,
                    expected[expectedIndex],
                    StringComparison.Ordinal))
                {
                    matched.Add(code);
                    expectedIndex++;
                }
            }
            return String.Join(",", matched.ToArray());
        }

        private static int FindRecordStart(byte[] mtef)
        {
            int cursor = 5;
            while (cursor < mtef.Length && mtef[cursor] != 0)
            {
                cursor++;
            }
            if (cursor + 1 >= mtef.Length)
            {
                throw new ArgumentException(
                    "MTEF header has no application-key terminator.",
                    "mtef");
            }
            return cursor + 2;
        }

        private static bool SkipNudge(
            byte[] value,
            ref int cursor)
        {
            if (cursor + 1 >= value.Length)
            {
                return false;
            }
            byte horizontal = value[cursor++];
            byte vertical = value[cursor++];
            if (horizontal == 0x80 && vertical == 0x80)
            {
                if (cursor + 3 >= value.Length)
                {
                    return false;
                }
                cursor += 4;
            }
            return true;
        }

        private static bool ReadSignedInteger(
            byte[] value,
            ref int cursor,
            out int result)
        {
            result = 0;
            if (cursor >= value.Length)
            {
                return false;
            }
            byte first = value[cursor++];
            if (first != 0xFF)
            {
                result = first - 128;
                return true;
            }
            if (cursor + 1 >= value.Length)
            {
                return false;
            }
            int encoded =
                value[cursor] |
                (value[cursor + 1] << 8);
            cursor += 2;
            result = encoded - 32768;
            return true;
        }
    }
}
