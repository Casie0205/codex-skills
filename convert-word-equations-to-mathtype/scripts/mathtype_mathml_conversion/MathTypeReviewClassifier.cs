using System;
using System.Collections.Generic;

namespace ThesisMathTypeConversionV2
{
    public static class MathTypeReviewClassifier
    {
        public const string TokenMismatch = "RT_TOKEN";
        public const string StructureMismatch = "RT_STRUCTURE";
        public const string MathMlStyleMismatch = "RT_MATHML_STYLE";
        public const string MtefStyleMismatch = "RT_MTEF_STYLE";
        public const string MtefFontProfileMismatch =
            "RT_MTEF_FONT_PROFILE";
        public const string ReplacementCharacter = "READBACK_REPLACEMENT_CHAR";
        public const string AccentScriptUnsupported =
            "SPECIAL_ACCENT_SCRIPT_UNSUPPORTED";
        public const string AccentScriptMixed =
            "SPECIAL_ACCENT_SCRIPT_MIXED";
        public const string AccentScriptUncorrected =
            "SPECIAL_ACCENT_SCRIPT_UNCORRECTED";
        public const string TexReadbackSkippedPeriodAccent =
            MathTypeDiagnosticPolicy
                .UnsupportedPeriodAccentTexReadback;

        public static IList<string> Classify(
            MathMlSnapshot source,
            MathMlRoundTripResult roundTrip,
            IEnumerable<string> additionalIssueCodes)
        {
            if (source == null)
            {
                throw new ArgumentNullException("source");
            }
            if (roundTrip == null)
            {
                throw new ArgumentNullException("roundTrip");
            }

            List<string> issueCodes = new List<string>();
            AddDistinct(issueCodes, additionalIssueCodes);
            if (!roundTrip.TokenSequenceEqual)
            {
                AddDistinct(issueCodes, TokenMismatch);
            }
            if (!roundTrip.StructureSignatureEqual)
            {
                AddDistinct(issueCodes, StructureMismatch);
            }
            if (!roundTrip.StyleSequenceEqual)
            {
                AddDistinct(issueCodes, MathMlStyleMismatch);
            }
            if (!roundTrip.MtefStyleEqual)
            {
                AddDistinct(issueCodes, MtefStyleMismatch);
            }
            if (!roundTrip.MtefFontProfileAccepted)
            {
                AddDistinct(issueCodes, MtefFontProfileMismatch);
            }
            if (!String.IsNullOrEmpty(roundTrip.ReadbackMathMl) &&
                roundTrip.ReadbackMathMl.IndexOf(
                    "\uFFFD",
                    StringComparison.Ordinal) >= 0)
            {
                AddDistinct(issueCodes, ReplacementCharacter);
            }
            return issueCodes;
        }

        private static void AddDistinct(
            IList<string> target,
            IEnumerable<string> values)
        {
            if (values == null)
            {
                return;
            }
            foreach (string value in values)
            {
                AddDistinct(target, value);
            }
        }

        private static void AddDistinct(
            IList<string> target,
            string value)
        {
            if (String.IsNullOrWhiteSpace(value))
            {
                return;
            }
            foreach (string existing in target)
            {
                if (String.Equals(
                    existing,
                    value,
                    StringComparison.Ordinal))
                {
                    return;
                }
            }
            target.Add(value);
        }
    }
}
