using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace ThesisMathTypeConversion
{
    public sealed class TexExportSnapshot
    {
        public string SourceWordText { get; set; }
        public string RawWordTex { get; set; }
        public string NfkcWordTex { get; set; }
        public string NormalizedTex { get; set; }
        public string ReplacementSummary { get; set; }
        public int AccentScriptRiskCount { get; set; }
        public string AccentScriptRiskDetails { get; set; }
        public int AccentScriptMtefNudgeCount { get; set; }
    }

    internal static class TexNormalizer
    {
        private static readonly IDictionary<char, string> UnicodeMathReplacements =
            new Dictionary<char, string>
            {
                { '\u2212', "-" },
                { '\u221E', "\\infty " },
                { '\u222B', "\\int " },
                { '\u00B0', "\\circ " },
                { '\u2061', " " },
                { '\u2192', "\\to " },
                { '\u0391', "A" },
                { '\u0392', "B" },
                { '\u0393', "{\\Gamma}" },
                { '\u0395', "E" },
                { '\u0396', "Z" },
                { '\u0397', "H" },
                { '\u0398', "{\\Theta}" },
                { '\u0399', "I" },
                { '\u039A', "K" },
                { '\u039B', "{\\Lambda}" },
                { '\u039C', "M" },
                { '\u039D', "N" },
                { '\u039E', "{\\Xi}" },
                { '\u039F', "O" },
                { '\u03A0', "{\\Pi}" },
                { '\u03A1', "P" },
                { '\u03A4', "T" },
                { '\u03A5', "{\\Upsilon}" },
                { '\u03A6', "{\\Phi}" },
                { '\u03A7', "X" },
                { '\u03A8', "{\\Psi}" },
                { '\u03B1', "{\\alpha}" },
                { '\u03B2', "{\\beta}" },
                { '\u03BC', "{\\mu}" },
                { '\u03C4', "{\\tau}" },
                { '\u03B4', "{\\delta}" },
                { '\u03B6', "{\\zeta}" },
                { '\u03B7', "{\\eta}" },
                { '\u03B9', "{\\iota}" },
                { '\u03BA', "{\\kappa}" },
                { '\u03BB', "{\\lambda}" },
                { '\u03BD', "{\\nu}" },
                { '\u03BE', "{\\xi}" },
                { '\u03BF', "o" },
                { '\u03C1', "{\\rho}" },
                { '\u03C2', "{\\varsigma}" },
                { '\u03C3', "{\\sigma}" },
                { '\u03C5', "{\\upsilon}" },
                { '\u03C7', "{\\chi}" },
                { '\u03C9', "{\\omega}" },
                { '\u03D1', "{\\vartheta}" },
                { '\u03D5', "{\\phi}" },
                { '\u03D6', "{\\varpi}" },
                { '\u03F1', "{\\varrho}" },
                { '\u03F5', "{\\epsilon}" },
                { '\u00B7', "\\cdot " },
                { '\u2225', "\\Vert " },
                { '\u03C6', "{\\varphi}" },
                { '\u0394', "{\\Delta}" },
                { '\u2264', "\\leq " },
                { '\u2265', "\\geq " },
                { '\u03B8', "{\\theta}" },
                { '\u00D7', "\\times " },
                { '\u2211', "\\sum " },
                { '\u03C8', "{\\psi}" },
                { '\u00B1', "\\pm " },
                { '\u03B5', "{\\varepsilon}" },
                { '\u226A', "\\ll " },
                { '\u22C5', "\\cdot " },
                { '\u03A9', "{\\Omega}" },
                { '\u03C0', "{\\pi}" },
                { '\u2260', "\\ne " },
                { '\u2207', "\\nabla " },
                { '\u03B3', "{\\gamma}" },
                { '\u03A3', "{\\Sigma}" },
                { '\u226B', "\\gg " },
                { '\u223C', "\\sim " },
                { '\u0176', "\\hat{Y}" },
                { '\u0177', "\\hat{y}" }
            };

        private static readonly IDictionary<string, string> NonStandardCommands =
            new Dictionary<string, string>(StringComparer.Ordinal)
            {
                { "\\varDelta", "\\Delta" },
                { "\\varOmega", "\\Omega" },
                { "\\varSigma", "\\Sigma" },
                { "\\lt", "<" },
                { "\\middle", String.Empty },
                { "\\begin{gathered}", String.Empty },
                { "\\end{gathered}", String.Empty }
            };

        internal static TexExportSnapshot CreateSnapshot(
            string sourceWordText,
            string rawWordTex)
        {
            if (rawWordTex == null)
            {
                throw new ArgumentNullException("rawWordTex");
            }

            string nfkc = rawWordTex.Normalize(NormalizationForm.FormKC);
            List<string> replacements = new List<string>();
            string normalized = nfkc;

            MatchCollection emptyPostfixAccents = Regex.Matches(
                normalized,
                @"(?<base>\\[A-Za-z]+|[A-Za-z0-9])\s*\{\s*\\(?<accent>widehat|widetilde|ddot|dot|hat|bar|tilde)\s*\}");
            if (emptyPostfixAccents.Count > 0)
            {
                normalized = Regex.Replace(
                    normalized,
                    @"(?<base>\\[A-Za-z]+|[A-Za-z0-9])\s*\{\s*\\(?<accent>widehat|widetilde|ddot|dot|hat|bar|tilde)\s*\}",
                    delegate(Match match)
                    {
                        string accent = match.Groups["accent"].Value;
                        if (accent == "widetilde")
                        {
                            accent = "tilde";
                        }

                        return "\\" +
                               accent +
                               "{" +
                               match.Groups["base"].Value +
                               "}";
                    });
                replacements.Add(
                    "empty-postfix-accent->prefix x" +
                    emptyPostfixAccents.Count.ToString(
                        CultureInfo.InvariantCulture));
            }

            MatchCollection postfixGroupedAccents = Regex.Matches(
                normalized,
                @"\{\s*(?<base>\\[A-Za-z]+|[A-Za-z0-9])\s*\\(?<accent>widehat|widetilde|ddot|dot|hat|bar|tilde)\s*\}");
            if (postfixGroupedAccents.Count > 0)
            {
                normalized = Regex.Replace(
                    normalized,
                    @"\{\s*(?<base>\\[A-Za-z]+|[A-Za-z0-9])\s*\\(?<accent>widehat|widetilde|ddot|dot|hat|bar|tilde)\s*\}",
                    delegate(Match match)
                    {
                        string accent = match.Groups["accent"].Value;
                        if (accent == "widetilde")
                        {
                            accent = "tilde";
                        }

                        return "{\\" +
                               accent +
                               "{" +
                               match.Groups["base"].Value +
                               "}}";
                    });
                replacements.Add(
                    "grouped-postfix-accent->prefix x" +
                    postfixGroupedAccents.Count.ToString(
                        CultureInfo.InvariantCulture));
            }

            foreach (KeyValuePair<string, string> command in NonStandardCommands)
            {
                int count = CountOccurrences(normalized, command.Key);
                if (count > 0)
                {
                    normalized = normalized.Replace(command.Key, command.Value);
                    replacements.Add(
                        command.Key + "->" + command.Value + " x" +
                        count.ToString(CultureInfo.InvariantCulture));
                }
            }

            MatchCollection postfixAccents = Regex.Matches(
                normalized,
                @"(?<base>[A-Za-z0-9])\\(?<accent>widehat|widetilde|ddot|dot|hat|bar|tilde)\b");
            if (postfixAccents.Count > 0)
            {
                normalized = Regex.Replace(
                    normalized,
                    @"(?<base>[A-Za-z0-9])\\(?<accent>widehat|widetilde|ddot|dot|hat|bar|tilde)\b",
                    delegate(Match match)
                    {
                        string accent = match.Groups["accent"].Value;
                        if (accent == "widetilde")
                        {
                            accent = "tilde";
                        }

                        return "\\" +
                               accent +
                               "{" +
                               match.Groups["base"].Value +
                               "}";
                    });
                replacements.Add(
                    "postfix-accent->prefix x" +
                    postfixAccents.Count.ToString(
                        CultureInfo.InvariantCulture));
            }

            int wideTildeCount = CountOccurrences(normalized, "\\widetilde");
            if (wideTildeCount > 0)
            {
                normalized = normalized.Replace("\\widetilde", "\\tilde");
                replacements.Add(
                    "\\widetilde->\\tilde x" +
                    wideTildeCount.ToString(CultureInfo.InvariantCulture));
            }

            MatchCollection wrappedDegrees = Regex.Matches(
                normalized,
                @"\^\{\u00B0\}");
            if (wrappedDegrees.Count > 0)
            {
                normalized = Regex.Replace(
                    normalized,
                    @"\^\{\u00B0\}",
                    "^{\\circ}");
                replacements.Add(
                    "^{U+00B0}->^{\\circ} x" +
                    wrappedDegrees.Count.ToString(
                        CultureInfo.InvariantCulture));
            }

            int macronCount = Regex.Matches(
                normalized,
                "([A-Za-z0-9])[\u0304\u0305]").Count;
            if (macronCount > 0)
            {
                normalized = Regex.Replace(
                    normalized,
                    "([A-Za-z0-9])[\u0304\u0305]",
                    "\\bar{$1}");
                replacements.Add(
                    "U+0304/U+0305->\\bar x" +
                    macronCount.ToString(CultureInfo.InvariantCulture));
            }

            int circumflexCount = Regex.Matches(
                normalized,
                "([A-Za-z0-9])\u0302").Count;
            if (circumflexCount > 0)
            {
                normalized = Regex.Replace(
                    normalized,
                    "([A-Za-z0-9])\u0302",
                    "\\hat{$1}");
                replacements.Add(
                    "U+0302->\\hat x" +
                    circumflexCount.ToString(CultureInfo.InvariantCulture));
            }

            MatchCollection primeRuns = Regex.Matches(normalized, "\u2032+");
            if (primeRuns.Count > 0)
            {
                normalized = Regex.Replace(
                    normalized,
                    "\u2032+",
                    delegate(Match match)
                    {
                        StringBuilder primes = new StringBuilder(
                            match.Length * 6);
                        for (int index = 0; index < match.Length; index++)
                        {
                            primes.Append("\\prime");
                        }

                        return primes.ToString();
                    });
                replacements.Add(
                    "U+2032->\\prime runs=" +
                    primeRuns.Count.ToString(CultureInfo.InvariantCulture));
            }

            StringBuilder converted = new StringBuilder(normalized.Length + 32);
            IDictionary<char, int> characterCounts = new Dictionary<char, int>();
            foreach (char character in normalized)
            {
                string replacement;
                if (UnicodeMathReplacements.TryGetValue(character, out replacement))
                {
                    converted.Append(replacement);
                    int count;
                    characterCounts.TryGetValue(character, out count);
                    characterCounts[character] = count + 1;
                }
                else if (character == '\r' || character == '\n')
                {
                    converted.Append(' ');
                    int count;
                    characterCounts.TryGetValue(character, out count);
                    characterCounts[character] = count + 1;
                }
                else
                {
                    converted.Append(character);
                }
            }

            foreach (KeyValuePair<char, int> replacement in characterCounts)
            {
                string label = replacement.Key == '\r'
                    ? "CR"
                    : replacement.Key == '\n'
                        ? "LF"
                        : "U+" + ((int)replacement.Key).ToString("X4");
                replacements.Add(
                    label + " x" +
                    replacement.Value.ToString(CultureInfo.InvariantCulture));
            }

            normalized = converted.ToString().Trim();
            ValidateMathTypeSafeTex(normalized);
            IList<AccentScriptRisk> accentScriptRisks =
                AccentScriptRiskDetector.Find(normalized);
            if (accentScriptRisks.Count > 0)
            {
                replacements.Add(
                    "accent-script-risk x" +
                    accentScriptRisks.Count.ToString(
                        CultureInfo.InvariantCulture));
            }

            return new TexExportSnapshot
            {
                SourceWordText = sourceWordText ?? String.Empty,
                RawWordTex = rawWordTex,
                NfkcWordTex = nfkc,
                NormalizedTex = normalized,
                ReplacementSummary = String.Join("; ", replacements.ToArray()),
                AccentScriptRiskCount = accentScriptRisks.Count,
                AccentScriptRiskDetails = String.Join(
                    " | ",
                    ToRiskStrings(accentScriptRisks))
            };
        }

        internal static void ValidateMathTypeSafeTex(string tex)
        {
            if (String.IsNullOrWhiteSpace(tex))
            {
                throw new InvalidOperationException(
                    "Normalized TeX is empty.");
            }

            for (int index = 0; index < tex.Length; index++)
            {
                char character = tex[index];
                if (character > 127)
                {
                    throw new InvalidOperationException(
                        "Normalized TeX still contains non-ASCII character U+" +
                        ((int)character).ToString("X4") +
                        " at offset " +
                        index.ToString(CultureInfo.InvariantCulture) + ".");
                }

                if (character == '?')
                {
                    throw new InvalidOperationException(
                        "Normalized TeX contains a question mark at offset " +
                        index.ToString(CultureInfo.InvariantCulture) + ".");
                }
            }

            Match invalidVariant = Regex.Match(
                tex,
                @"\\var(?:Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi|Omicron|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega)");
            if (invalidVariant.Success)
            {
                throw new InvalidOperationException(
                    "Normalized TeX still contains unsupported command " +
                    invalidVariant.Value + ".");
            }

            Match unsupportedCommand = Regex.Match(
                tex,
                @"\\(?:widetilde|middle)\b|\\(?:begin|end)\{gathered\}");
            if (unsupportedCommand.Success)
            {
                throw new InvalidOperationException(
                    "Normalized TeX still contains MathType-unsupported command " +
                    unsupportedCommand.Value + ".");
            }

            Match nestedSuperscript = Regex.Match(
                tex,
                @"\^\{\s*\^");
            if (nestedSuperscript.Success)
            {
                throw new InvalidOperationException(
                    "Normalized TeX contains a nested superscript at offset " +
                    nestedSuperscript.Index.ToString(
                        CultureInfo.InvariantCulture) + ".");
            }
        }

        private static int CountOccurrences(string value, string token)
        {
            int count = 0;
            int offset = 0;
            while (offset < value.Length)
            {
                int found = value.IndexOf(token, offset, StringComparison.Ordinal);
                if (found < 0)
                {
                    break;
                }

                count++;
                offset = found + token.Length;
            }

            return count;
        }

        private static string[] ToRiskStrings(
            IList<AccentScriptRisk> risks)
        {
            string[] values = new string[risks.Count];
            for (int index = 0; index < risks.Count; index++)
            {
                values[index] = risks[index].ToString();
            }

            return values;
        }
    }
}
