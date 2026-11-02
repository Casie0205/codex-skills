using System;
using System.Xml;

namespace ThesisMathTypeConversionV2
{
    public static class MathTypeDiagnosticPolicy
    {
        public const string UnsupportedPeriodAccentTexReadback =
            "SPECIAL_TEX_READBACK_SKIPPED_PERIOD_ACCENT";

        public static bool ShouldSkipTexReadback(
            MathMlSnapshot source)
        {
            if (source == null ||
                String.IsNullOrWhiteSpace(source.NormalizedMathMl))
            {
                return false;
            }

            XmlDocument document =
                MathMlCanonicalizer.LoadMathMl(
                    source.NormalizedMathMl);
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace(
                "m",
                "http://www.w3.org/1998/Math/MathML");
            XmlNodeList movers =
                document.SelectNodes("//m:mover", namespaces);
            foreach (XmlNode mover in movers)
            {
                if (mover.ChildNodes.Count < 2)
                {
                    continue;
                }
                XmlNode mark = mover.ChildNodes[1];
                string markText = mark.InnerText.Trim();
                if (String.Equals(
                        markText,
                        ".",
                        StringComparison.Ordinal) ||
                    String.Equals(
                        markText,
                        "\u02C9",
                        StringComparison.Ordinal) ||
                    String.Equals(
                        markText,
                        "\u00AF",
                        StringComparison.Ordinal))
                {
                    return true;
                }
            }
            return false;
        }
    }
}
