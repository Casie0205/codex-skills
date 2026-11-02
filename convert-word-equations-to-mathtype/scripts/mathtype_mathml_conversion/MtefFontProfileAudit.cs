using System;
using System.Collections.Generic;
using System.Text;

namespace ThesisMathTypeConversionV2
{
    public sealed class MtefFontProfileAuditResult
    {
        public bool HasTimesNewRoman { get; set; }
        public bool HasEuclidExtra { get; set; }
        public bool HasLegacyMtExtra { get; set; }
        public bool RequiredStylesUseTimesNewRoman { get; set; }
        public bool MathExtraStyleUsesEuclidExtra { get; set; }
        public bool Accepted { get; set; }
    }

    public static class MtefFontProfileAudit
    {
        private const byte FontStyleDefinitionRecord = 8;
        private const byte ColorDefinitionRecord = 16;
        private const byte FontDefinitionRecord = 17;
        private const byte EquationPreferencesRecord = 18;
        private const byte EncodingDefinitionRecord = 19;
        private const string TimesNewRoman = "Times New Roman";
        private const string EuclidExtra = "Euclid Extra";
        private const string LegacyMtExtra = "MT Extra";

        public static MtefFontProfileAuditResult Inspect(byte[] mtef)
        {
            if (mtef == null || mtef.Length < 8 || mtef[0] != 5)
            {
                throw new ArgumentException(
                    "MTEF v5 data is required.",
                    "mtef");
            }

            int offset = FindDefinitionRecordOffset(mtef);
            bool hasTimesNewRoman = false;
            bool hasEuclidExtra = false;
            bool hasLegacyMtExtra = false;
            bool requiredStylesUseTimesNewRoman = false;
            bool mathExtraStyleUsesEuclidExtra = false;
            bool foundEquationPreferences = false;
            List<byte[]> fontDefinitions = new List<byte[]>();

            while (offset < mtef.Length)
            {
                byte recordType = mtef[offset++];
                if (recordType == FontDefinitionRecord)
                {
                    ReadUnsignedInteger(mtef, ref offset);
                    int nameOffset = offset;
                    int nameLength =
                        ReadNullTerminatedValueLength(mtef, ref offset);
                    byte[] fontName = new byte[nameLength];
                    Buffer.BlockCopy(
                        mtef,
                        nameOffset,
                        fontName,
                        0,
                        nameLength);
                    fontDefinitions.Add(fontName);
                    hasTimesNewRoman |= IsExactAscii(
                        mtef,
                        nameOffset,
                        nameLength,
                        TimesNewRoman);
                    hasEuclidExtra |= IsExactAscii(
                        mtef,
                        nameOffset,
                        nameLength,
                        EuclidExtra);
                    hasLegacyMtExtra |= IsExactAscii(
                        mtef,
                        nameOffset,
                        nameLength,
                        LegacyMtExtra);
                    continue;
                }

                if (recordType == EncodingDefinitionRecord)
                {
                    ReadNullTerminatedValueLength(mtef, ref offset);
                    continue;
                }

                if (recordType == FontStyleDefinitionRecord)
                {
                    ReadUnsignedInteger(mtef, ref offset);
                    RequireAvailable(mtef, offset, 1, "FONT_STYLE_DEF");
                    offset++;
                    continue;
                }

                if (recordType == ColorDefinitionRecord)
                {
                    SkipColorDefinition(mtef, ref offset);
                    continue;
                }

                if (recordType >= 100)
                {
                    int futureLength =
                        ReadUnsignedInteger(mtef, ref offset);
                    RequireAvailable(
                        mtef,
                        offset,
                        futureLength,
                        "future record");
                    offset += futureLength;
                    continue;
                }

                if (recordType == EquationPreferencesRecord)
                {
                    RequireAvailable(
                        mtef,
                        offset,
                        1,
                        "EQN_PREFS options");
                    byte equationPreferencesOptions = mtef[offset++];
                    if (equationPreferencesOptions != 0)
                    {
                        throw new FormatException(
                            "MTEF EQN_PREFS options must be zero.");
                    }
                    ReadEquationPreferenceStyleMappings(
                        mtef,
                        ref offset,
                        fontDefinitions,
                        out requiredStylesUseTimesNewRoman,
                        out mathExtraStyleUsesEuclidExtra);
                    foundEquationPreferences = true;
                    break;
                }

                throw new FormatException(
                    "Unexpected MTEF record " +
                    recordType +
                    " before EQN_PREFS.");
            }

            if (!foundEquationPreferences)
            {
                throw new FormatException(
                    "MTEF EQN_PREFS record was not found.");
            }

            return new MtefFontProfileAuditResult
            {
                HasTimesNewRoman = hasTimesNewRoman,
                HasEuclidExtra = hasEuclidExtra,
                HasLegacyMtExtra = hasLegacyMtExtra,
                RequiredStylesUseTimesNewRoman =
                    requiredStylesUseTimesNewRoman,
                MathExtraStyleUsesEuclidExtra =
                    mathExtraStyleUsesEuclidExtra,
                Accepted =
                    hasTimesNewRoman &&
                    hasEuclidExtra &&
                    !hasLegacyMtExtra &&
                    requiredStylesUseTimesNewRoman &&
                    mathExtraStyleUsesEuclidExtra
            };
        }

        private static void ReadEquationPreferenceStyleMappings(
            byte[] value,
            ref int offset,
            IList<byte[]> fontDefinitions,
            out bool requiredStylesUseTimesNewRoman,
            out bool mathExtraUsesEuclid)
        {
            SkipDimensionArray(value, ref offset);
            SkipDimensionArray(value, ref offset);
            RequireAvailable(value, offset, 1, "style array count");
            int styleCount = value[offset++];
            int[] requiredTimesStyleIndices =
                new[] { 0, 1, 2, 6, 7, 9 };
            bool[] requiredTimesStyleMatches =
                new bool[requiredTimesStyleIndices.Length];
            mathExtraUsesEuclid = false;
            for (int styleIndex = 0;
                styleIndex < styleCount;
                styleIndex++)
            {
                int fontIndex = ReadUnsignedInteger(value, ref offset);
                if (fontIndex == 0)
                {
                    continue;
                }
                RequireAvailable(
                    value,
                    offset,
                    1,
                    "style character flags");
                offset++;
                if (fontIndex > fontDefinitions.Count)
                {
                    throw new FormatException(
                        "EQN_PREFS references missing FONT_DEF index " +
                        fontIndex +
                        ".");
                }
                if (styleIndex == 10)
                {
                    byte[] fontName = fontDefinitions[fontIndex - 1];
                    mathExtraUsesEuclid = IsExactAscii(
                        fontName,
                        0,
                        fontName.Length,
                        EuclidExtra);
                }
                int requiredPosition = Array.IndexOf(
                    requiredTimesStyleIndices,
                    styleIndex);
                if (requiredPosition >= 0)
                {
                    byte[] fontName = fontDefinitions[fontIndex - 1];
                    requiredTimesStyleMatches[requiredPosition] =
                        IsExactAscii(
                            fontName,
                            0,
                            fontName.Length,
                            TimesNewRoman);
                }
            }
            requiredStylesUseTimesNewRoman = true;
            foreach (bool mapped in requiredTimesStyleMatches)
            {
                requiredStylesUseTimesNewRoman &= mapped;
            }
        }

        private static int FindDefinitionRecordOffset(byte[] mtef)
        {
            int offset = 5;
            ReadNullTerminatedValueLength(mtef, ref offset);
            RequireAvailable(mtef, offset, 1, "equation options");
            byte equationOptions = mtef[offset++];
            if ((equationOptions & 0xFE) != 0)
            {
                throw new FormatException(
                    "Unsupported MTEF equation option bits.");
            }
            return offset;
        }

        private static int ReadNullTerminatedValueLength(
            byte[] value,
            ref int offset)
        {
            int start = offset;
            while (offset < value.Length && value[offset] != 0)
            {
                offset++;
            }
            if (offset >= value.Length)
            {
                throw new FormatException(
                    "MTEF contains an unterminated string.");
            }
            int length = offset - start;
            offset++;
            return length;
        }

        private static int ReadUnsignedInteger(
            byte[] value,
            ref int offset)
        {
            RequireAvailable(value, offset, 1, "unsigned integer");
            int first = value[offset++];
            if (first < 255)
            {
                return first;
            }

            RequireAvailable(value, offset, 2, "extended unsigned integer");
            int result = value[offset] | (value[offset + 1] << 8);
            offset += 2;
            return result;
        }

        private static void SkipDimensionArray(
            byte[] value,
            ref int offset)
        {
            RequireAvailable(value, offset, 1, "dimension array count");
            int dimensionCount = value[offset++];
            int nibbleByteOffset = offset;
            int nibbleIndex = 0;
            for (int dimension = 0;
                dimension < dimensionCount;
                dimension++)
            {
                int units = ReadNibble(
                    value,
                    nibbleByteOffset,
                    ref nibbleIndex);
                if (units < 0 || units > 4)
                {
                    throw new FormatException(
                        "MTEF dimension has invalid units.");
                }
                while (true)
                {
                    int character = ReadNibble(
                        value,
                        nibbleByteOffset,
                        ref nibbleIndex);
                    if (character == 0x0F)
                    {
                        break;
                    }
                    if (character > 0x0B)
                    {
                        throw new FormatException(
                            "MTEF dimension has an invalid value nibble.");
                    }
                }
            }
            int byteCount = (nibbleIndex + 1) / 2;
            RequireAvailable(
                value,
                nibbleByteOffset,
                byteCount,
                "dimension array values");
            offset = nibbleByteOffset + byteCount;
        }

        private static int ReadNibble(
            byte[] value,
            int byteOffset,
            ref int nibbleIndex)
        {
            int currentByteOffset = byteOffset + (nibbleIndex / 2);
            RequireAvailable(
                value,
                currentByteOffset,
                1,
                "dimension nibble");
            int current = value[currentByteOffset];
            int result = (nibbleIndex % 2) == 0
                ? (current >> 4) & 0x0F
                : current & 0x0F;
            nibbleIndex++;
            return result;
        }

        private static void SkipColorDefinition(
            byte[] value,
            ref int offset)
        {
            RequireAvailable(value, offset, 1, "COLOR_DEF options");
            byte options = value[offset++];
            int componentCount = (options & 0x01) != 0 ? 4 : 3;
            RequireAvailable(
                value,
                offset,
                componentCount * 2,
                "COLOR_DEF values");
            offset += componentCount * 2;
            if ((options & 0x04) != 0)
            {
                ReadNullTerminatedValueLength(value, ref offset);
            }
        }

        private static bool IsExactAscii(
            byte[] value,
            int offset,
            int length,
            string expected)
        {
            byte[] pattern = Encoding.ASCII.GetBytes(expected);
            if (length != pattern.Length)
            {
                return false;
            }
            for (int index = 0; index < pattern.Length; index++)
            {
                if (value[offset + index] != pattern[index])
                {
                    return false;
                }
            }
            return true;
        }

        private static void RequireAvailable(
            byte[] value,
            int offset,
            int length,
            string field)
        {
            if (length < 0 ||
                offset < 0 ||
                offset > value.Length - length)
            {
                throw new FormatException(
                    "MTEF ended while reading " + field + ".");
            }
        }
    }
}
