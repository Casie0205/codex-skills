using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Xml;
using System.Xml.Xsl;

namespace ThesisMathTypeConversionV2
{
    public sealed class OmmlMathMlTransformer
    {
        private const string OmmlNamespace =
            "http://schemas.openxmlformats.org/officeDocument/2006/math";
        private const string MathMlNamespace =
            "http://www.w3.org/1998/Math/MathML";

        private readonly XslCompiledTransform transform;

        public OmmlMathMlTransformer(string officeOmmlToMathMlXsltPath)
        {
            if (String.IsNullOrWhiteSpace(officeOmmlToMathMlXsltPath) ||
                !File.Exists(officeOmmlToMathMlXsltPath))
            {
                throw new FileNotFoundException(
                    "Office OMML2MML.XSL was not found.",
                    officeOmmlToMathMlXsltPath);
            }

            string xslt = File.ReadAllText(
                officeOmmlToMathMlXsltPath,
                Encoding.UTF8);
            xslt = PatchDelimiterSeparatorContext(xslt);

            transform = new XslCompiledTransform();
            XmlReaderSettings readerSettings = new XmlReaderSettings();
            readerSettings.DtdProcessing = DtdProcessing.Prohibit;
            readerSettings.XmlResolver = null;
            using (StringReader text = new StringReader(xslt))
            using (XmlReader reader = XmlReader.Create(
                text,
                readerSettings,
                officeOmmlToMathMlXsltPath))
            {
                transform.Load(
                    reader,
                    new XsltSettings(false, false),
                    new XmlUrlResolver());
            }
        }

        public MathMlSnapshot Transform(
            int sourceIndex,
            string ommlXml)
        {
            XmlElement equation = LoadEquationElement(ommlXml);
            string rawFragment = TransformFragment(equation);
            string rawMathMl = WrapMathMl(rawFragment);
            XmlDocument normalized = NormalizeMathMl(rawMathMl);
            string normalizedText = Serialize(normalized);
            MathMlCanonicalForm canonical =
                MathMlCanonicalizer.Canonicalize(normalizedText);

            return new MathMlSnapshot
            {
                SourceIndex = sourceIndex,
                RawMathMl = rawMathMl,
                NormalizedMathMl = normalizedText,
                CanonicalMathMl = canonical.Xml,
                CanonicalSha256 = canonical.Sha256,
                TokenSequence = canonical.TokenSequence,
                StructureSignature = canonical.StructureSignature,
                StyleSequence = canonical.StyleSequence,
                Features = CollectFeatures(normalized.DocumentElement),
                ExpectedStyledCharacterCount =
                    canonical.StyledCharacterCount,
                ExpectedMtefCharacterStyleSequence =
                    canonical.MtefCharacterStyleSequence,
                AccentScriptRiskCount =
                    CountAccentScriptRisks(normalizedText)
            };
        }

        public static int CountAccentScriptRisks(string mathMl)
        {
            return GetAccentScriptSuperscripts(mathMl).Count;
        }

        public static IList<string> GetAccentScriptSuperscripts(
            string mathMl)
        {
            XmlDocument document = MathMlCanonicalizer.LoadMathMl(mathMl);
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", MathMlNamespace);
            XmlNodeList superscripts =
                document.SelectNodes("//m:msup | //m:msubsup", namespaces);
            List<string> superscriptValues = new List<string>();
            foreach (XmlNode script in superscripts)
            {
                XmlElement baseElement = FirstElementChild(script);
                if (baseElement != null &&
                    ContainsDotAccent(baseElement))
                {
                    XmlElement superscript = LastElementChild(script);
                    superscriptValues.Add(
                        superscript == null
                            ? String.Empty
                            : superscript.InnerText);
                }
            }
            return superscriptValues;
        }

        private static string PatchDelimiterSeparatorContext(string xslt)
        {
            const string brokenWhen =
                "not(m:dPr[1]/m:sepChr/@m:val)";
            const string fixedWhen =
                "not(../m:dPr[1]/m:sepChr/@m:val)";
            const string brokenValue =
                "select=\"m:dPr[1]/m:sepChr/@m:val\"";
            const string fixedValue =
                "select=\"../m:dPr[1]/m:sepChr/@m:val\"";

            if (CountOccurrences(xslt, brokenWhen) != 1 ||
                CountOccurrences(xslt, brokenValue) != 1)
            {
                throw new InvalidDataException(
                    "OMML2MML.XSL delimiter-separator template no longer " +
                    "matches the verified Office 16 structure.");
            }
            return xslt
                .Replace(brokenWhen, fixedWhen)
                .Replace(brokenValue, fixedValue);
        }

        private static int CountOccurrences(string value, string pattern)
        {
            int count = 0;
            int start = 0;
            while (start < value.Length)
            {
                int found = value.IndexOf(
                    pattern,
                    start,
                    StringComparison.Ordinal);
                if (found < 0)
                {
                    break;
                }
                count++;
                start = found + pattern.Length;
            }
            return count;
        }

        private static XmlElement LoadEquationElement(string ommlXml)
        {
            if (String.IsNullOrWhiteSpace(ommlXml))
            {
                throw new InvalidDataException("OMML is empty.");
            }

            XmlDocument document = new XmlDocument();
            document.PreserveWhitespace = true;
            document.XmlResolver = null;
            document.LoadXml(ommlXml);
            if (document.DocumentElement != null &&
                String.Equals(
                    document.DocumentElement.LocalName,
                    "oMath",
                    StringComparison.Ordinal) &&
                String.Equals(
                    document.DocumentElement.NamespaceURI,
                    OmmlNamespace,
                    StringComparison.Ordinal))
            {
                return document.DocumentElement;
            }

            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", OmmlNamespace);
            XmlElement equation =
                document.SelectSingleNode(
                    "//m:oMath[not(ancestor::m:oMath)]",
                    namespaces) as XmlElement;
            if (equation == null)
            {
                throw new InvalidDataException(
                    "No top-level OMML equation was found.");
            }
            return equation;
        }

        private string TransformFragment(XmlElement equation)
        {
            StringBuilder result = new StringBuilder();
            XmlWriterSettings settings = new XmlWriterSettings();
            settings.OmitXmlDeclaration = true;
            settings.ConformanceLevel = ConformanceLevel.Fragment;
            settings.Encoding = new UTF8Encoding(false);
            settings.Indent = false;
            using (XmlWriter writer = XmlWriter.Create(result, settings))
            {
                transform.Transform(
                    equation.CreateNavigator(),
                    null,
                    writer);
            }
            if (result.Length == 0)
            {
                throw new InvalidDataException(
                    "OMML2MML.XSL returned an empty MathML fragment.");
            }
            return result.ToString();
        }

        private static string WrapMathMl(string fragment)
        {
            XmlDocument candidate = new XmlDocument();
            candidate.PreserveWhitespace = false;
            candidate.XmlResolver = null;
            try
            {
                candidate.LoadXml(fragment);
                if (candidate.DocumentElement != null &&
                    String.Equals(
                        candidate.DocumentElement.LocalName,
                        "math",
                        StringComparison.Ordinal) &&
                    String.Equals(
                        candidate.DocumentElement.NamespaceURI,
                        MathMlNamespace,
                        StringComparison.Ordinal))
                {
                    candidate.DocumentElement.SetAttribute(
                        "display",
                        "inline");
                    return Serialize(candidate);
                }
            }
            catch (XmlException)
            {
            }

            return
                "<math xmlns=\"" +
                MathMlNamespace +
                "\" display=\"inline\"><mrow>" +
                fragment +
                "</mrow></math>";
        }

        private static XmlDocument NormalizeMathMl(string mathMl)
        {
            XmlDocument document = MathMlCanonicalizer.LoadMathMl(mathMl);
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", MathMlNamespace);
            XmlNodeList identifiers =
                document.SelectNodes("//m:mi", namespaces);
            foreach (XmlNode node in identifiers)
            {
                NormalizeIdentifier((XmlElement)node);
            }

            NormalizeMathTypeCompatibleVariants(document);
            NormalizeScriptedNamedOperators(document);
            PromoteTrailingCombiningAccents(document);
            PromoteAdjacentCombiningAccents(document);
            NormalizeMathTypeCompatibleAccents(document);
            InsertMissingDifferentialSpacing(document);
            InsertUprightScriptBoundaries(document);
            ValidateMathMl(document);
            return document;
        }

        private static void NormalizeScriptedNamedOperators(
            XmlDocument document)
        {
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", MathMlNamespace);
            XmlNodeList scripts = document.SelectNodes(
                "//m:msub | //m:msup | //m:msubsup | " +
                "//m:munder | //m:mover | //m:munderover",
                namespaces);
            foreach (XmlNode node in scripts)
            {
                XmlElement script = node as XmlElement;
                XmlElement scriptBase = script == null
                    ? null
                    : FirstElementChild(script);
                if (scriptBase == null ||
                    !String.Equals(
                        scriptBase.LocalName,
                        "mrow",
                        StringComparison.Ordinal))
                {
                    continue;
                }

                string collapsed = CollapseWhitespace(
                    scriptBase.InnerText).Replace(" ", String.Empty);
                if (!String.Equals(
                    collapsed,
                    "argmin",
                    StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                XmlElement operatorText = document.CreateElement(
                    "mtext",
                    MathMlNamespace);
                operatorText.InnerText = "arg min";
                script.ReplaceChild(operatorText, scriptBase);
            }
        }

        private static string CollapseWhitespace(string value)
        {
            if (String.IsNullOrWhiteSpace(value))
            {
                return String.Empty;
            }

            StringBuilder result = new StringBuilder();
            bool previousWasWhitespace = false;
            foreach (char character in value.Trim())
            {
                if (Char.IsWhiteSpace(character))
                {
                    if (!previousWasWhitespace)
                    {
                        result.Append(' ');
                    }
                    previousWasWhitespace = true;
                }
                else
                {
                    result.Append(character);
                    previousWasWhitespace = false;
                }
            }
            return result.ToString();
        }

        private static void PromoteAdjacentCombiningAccents(
            XmlDocument document)
        {
            XmlNodeList tokens = document.SelectNodes(
                "//*[local-name()='mi' or local-name()='mo']");
            List<XmlElement> marks = new List<XmlElement>();
            foreach (XmlNode node in tokens)
            {
                XmlElement mark = node as XmlElement;
                if (mark != null &&
                    IsCombiningAccentMark(mark.InnerText))
                {
                    marks.Add(mark);
                }
            }

            foreach (XmlElement mark in marks)
            {
                XmlElement parent = mark.ParentNode as XmlElement;
                if (parent == null ||
                    String.Equals(
                        parent.LocalName,
                        "mover",
                        StringComparison.Ordinal))
                {
                    continue;
                }

                XmlElement accentBase =
                    PreviousElementSibling(mark);
                if (accentBase == null)
                {
                    continue;
                }

                XmlElement mover = document.CreateElement(
                    "mover",
                    MathMlNamespace);
                mover.SetAttribute("accent", "true");
                parent.InsertBefore(mover, accentBase);
                mover.AppendChild(accentBase);
                mover.AppendChild(mark);
            }
        }

        private static void PromoteTrailingCombiningAccents(
            XmlDocument document)
        {
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", MathMlNamespace);
            XmlNodeList scripts = document.SelectNodes(
                "//m:msub | //m:msup | //m:msubsup",
                namespaces);
            foreach (XmlNode node in scripts)
            {
                XmlElement script = node as XmlElement;
                XmlElement scriptBase = script == null
                    ? null
                    : FirstElementChild(script);
                if (scriptBase == null ||
                    !String.Equals(
                        scriptBase.LocalName,
                        "mrow",
                        StringComparison.Ordinal))
                {
                    continue;
                }

                XmlElement mark = LastElementChild(scriptBase);
                if (mark == null ||
                    !IsCombiningAccentMark(mark.InnerText))
                {
                    continue;
                }

                XmlElement first = FirstElementChild(scriptBase);
                if (first == null ||
                    Object.ReferenceEquals(first, mark))
                {
                    continue;
                }

                XmlElement mover = document.CreateElement(
                    "mover",
                    MathMlNamespace);
                mover.SetAttribute("accent", "true");
                XmlElement baseRow = document.CreateElement(
                    "mrow",
                    MathMlNamespace);
                while (scriptBase.FirstChild != null &&
                    !Object.ReferenceEquals(
                        scriptBase.FirstChild,
                        mark))
                {
                    baseRow.AppendChild(scriptBase.FirstChild);
                }
                scriptBase.RemoveChild(mark);
                mover.AppendChild(baseRow);
                mover.AppendChild(mark);
                script.ReplaceChild(mover, scriptBase);
            }
        }

        private static bool IsCombiningAccentMark(string value)
        {
            return value == "\u0302" ||
                   value == "\u0303" ||
                   value == "\u0304" ||
                   value == "\u0305" ||
                   value == "\u0307" ||
                   value == "\u0308" ||
                   value == "\u20D7";
        }

        private static void NormalizeMathTypeCompatibleAccents(
            XmlDocument document)
        {
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", MathMlNamespace);
            XmlNodeList accents = document.SelectNodes(
                "//m:mover[@accent='true']",
                namespaces);
            foreach (XmlNode node in accents)
            {
                XmlElement accent = node as XmlElement;
                XmlElement mark = accent == null
                    ? null
                    : LastElementChild(accent);
                if (mark == null)
                {
                    continue;
                }

                if (String.Equals(
                        mark.InnerText,
                        "\u0304",
                        StringComparison.Ordinal) ||
                    String.Equals(
                        mark.InnerText,
                        "\u0305",
                        StringComparison.Ordinal) ||
                    String.Equals(
                        mark.InnerText,
                        "-",
                        StringComparison.Ordinal) ||
                    String.Equals(
                        mark.InnerText,
                        "\u02C9",
                        StringComparison.Ordinal))
                {
                    mark = EnsureAccentOperator(mark);
                    mark.InnerText = "\u00AF";
                }
                else if (String.Equals(
                         mark.InnerText,
                         "\u0302",
                         StringComparison.Ordinal) ||
                    String.Equals(
                         mark.InnerText,
                         "\u02C6",
                         StringComparison.Ordinal))
                {
                    mark = EnsureAccentOperator(mark);
                    mark.InnerText = "^";
                }
                else if (String.Equals(
                    mark.InnerText,
                    "\u0303",
                    StringComparison.Ordinal))
                {
                    mark.InnerText = "~";
                }
                else if (String.Equals(
                    mark.InnerText,
                    "\u0307",
                    StringComparison.Ordinal))
                {
                    mark.InnerText = "\u02D9";
                }
                else if (String.Equals(
                    mark.InnerText,
                    "\u0308",
                    StringComparison.Ordinal))
                {
                    mark.InnerText = "\u00A8";
                }
            }
        }

        private static XmlElement EnsureAccentOperator(XmlElement mark)
        {
            if (mark == null ||
                String.Equals(
                    mark.LocalName,
                    "mo",
                    StringComparison.Ordinal) ||
                !String.Equals(
                    mark.LocalName,
                    "mi",
                    StringComparison.Ordinal) ||
                mark.ParentNode == null)
            {
                return mark;
            }

            XmlElement accentOperator = mark.OwnerDocument.CreateElement(
                "mo",
                MathMlNamespace);
            accentOperator.InnerText = mark.InnerText;
            mark.ParentNode.ReplaceChild(accentOperator, mark);
            return accentOperator;
        }

        private static void InsertUprightScriptBoundaries(
            XmlDocument document)
        {
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", MathMlNamespace);
            XmlNodeList scripts = document.SelectNodes(
                "//m:msub | //m:msup | //m:msubsup",
                namespaces);
            foreach (XmlNode node in scripts)
            {
                XmlElement script = node as XmlElement;
                if (script == null ||
                    script.ParentNode == null)
                {
                    continue;
                }

                XmlElement previous = PreviousElementSibling(script);
                XmlElement scriptBase = FirstElementChild(script);
                XmlElement baseToken = scriptBase == null
                    ? null
                    : FirstTokenElement(scriptBase);
                if (!IsUprightIdentifier(previous) ||
                    !IsUprightIdentifier(baseToken))
                {
                    continue;
                }

                XmlElement boundary = document.CreateElement(
                    "mspace",
                    MathMlNamespace);
                boundary.SetAttribute("width", "0em");
                script.ParentNode.InsertBefore(boundary, script);
            }
        }

        private static bool IsUprightIdentifier(XmlElement element)
        {
            return element != null &&
                String.Equals(
                    element.LocalName,
                    "mi",
                    StringComparison.Ordinal) &&
                String.Equals(
                    element.GetAttribute("mathvariant"),
                    "normal",
                    StringComparison.OrdinalIgnoreCase);
        }

        private static void InsertMissingDifferentialSpacing(
            XmlDocument document)
        {
            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(document.NameTable);
            namespaces.AddNamespace("m", MathMlNamespace);
            XmlNodeList differentials = document.SelectNodes(
                "//m:mi[@mathvariant='normal' and text()='d']",
                namespaces);
            foreach (XmlNode node in differentials)
            {
                XmlElement differential = node as XmlElement;
                if (differential == null ||
                    differential.ParentNode == null ||
                    !IsDifferentialVariableFollowing(differential))
                {
                    continue;
                }

                XmlElement previous = PreviousElementSibling(differential);
                if (previous == null ||
                    IsExplicitMathSpacing(previous))
                {
                    continue;
                }

                XmlElement spacing = document.CreateElement(
                    "mtext",
                    MathMlNamespace);
                spacing.InnerText = "\u2009";
                differential.ParentNode.InsertBefore(
                    spacing,
                    differential);
            }
        }

        private static XmlElement PreviousElementSibling(XmlElement element)
        {
            XmlNode sibling = element.PreviousSibling;
            while (sibling != null)
            {
                XmlElement siblingElement = sibling as XmlElement;
                if (siblingElement != null)
                {
                    return siblingElement;
                }
                sibling = sibling.PreviousSibling;
            }
            return null;
        }

        private static bool IsDifferentialVariableFollowing(
            XmlElement differential)
        {
            XmlElement following = NextElementSibling(differential);
            if (following == null)
            {
                return false;
            }

            XmlElement firstToken = FirstTokenElement(following);
            if (firstToken == null ||
                !String.Equals(
                    firstToken.LocalName,
                    "mi",
                    StringComparison.Ordinal))
            {
                return false;
            }

            string variant = firstToken.HasAttribute("mathvariant")
                ? firstToken.GetAttribute("mathvariant")
                : String.Empty;
            return !String.Equals(
                variant,
                "normal",
                StringComparison.OrdinalIgnoreCase);
        }

        private static XmlElement NextElementSibling(XmlElement element)
        {
            XmlNode sibling = element.NextSibling;
            while (sibling != null)
            {
                XmlElement siblingElement = sibling as XmlElement;
                if (siblingElement != null)
                {
                    return siblingElement;
                }
                sibling = sibling.NextSibling;
            }
            return null;
        }

        private static XmlElement FirstTokenElement(XmlElement element)
        {
            if (String.Equals(
                    element.LocalName,
                    "mi",
                    StringComparison.Ordinal) ||
                String.Equals(
                    element.LocalName,
                    "mn",
                    StringComparison.Ordinal) ||
                String.Equals(
                    element.LocalName,
                    "mo",
                    StringComparison.Ordinal) ||
                String.Equals(
                    element.LocalName,
                    "mtext",
                    StringComparison.Ordinal) ||
                String.Equals(
                    element.LocalName,
                    "ms",
                    StringComparison.Ordinal))
            {
                return element;
            }

            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement == null)
                {
                    continue;
                }

                XmlElement token = FirstTokenElement(childElement);
                if (token != null)
                {
                    return token;
                }
            }
            return null;
        }

        private static bool IsExplicitMathSpacing(XmlElement element)
        {
            if (String.Equals(
                element.LocalName,
                "mspace",
                StringComparison.Ordinal))
            {
                return true;
            }
            if (!String.Equals(
                element.LocalName,
                "mtext",
                StringComparison.Ordinal))
            {
                return false;
            }

            string text = element.InnerText;
            return !String.IsNullOrEmpty(text) &&
                String.IsNullOrWhiteSpace(
                    text
                        .Replace("\u2009", " ")
                        .Replace("\u2004", " "));
        }

        private static void NormalizeMathTypeCompatibleVariants(
            XmlDocument document)
        {
            XmlNodeList styledNodes =
                document.SelectNodes("//*[@mathvariant]");
            foreach (XmlNode node in styledNodes)
            {
                XmlElement element = node as XmlElement;
                if (element == null)
                {
                    continue;
                }

                string variant = element.GetAttribute("mathvariant");
                string compatibleVariant = variant;
                switch (variant)
                {
                    case "sans-serif":
                    case "monospace":
                        compatibleVariant = "normal";
                        break;
                    case "bold-sans-serif":
                        compatibleVariant = "bold";
                        break;
                    case "sans-serif-italic":
                        compatibleVariant = "italic";
                        break;
                    case "sans-serif-bold-italic":
                        compatibleVariant = "bold-italic";
                        break;
                }

                if (!String.Equals(
                    variant,
                    compatibleVariant,
                    StringComparison.Ordinal))
                {
                    element.SetAttribute(
                        "mathvariant",
                        compatibleVariant);
                }
            }
        }

        private static void NormalizeIdentifier(XmlElement identifier)
        {
            string value = identifier.InnerText;
            if (String.IsNullOrEmpty(value))
            {
                return;
            }

            string variant = null;
            for (int offset = 0; offset < value.Length; offset++)
            {
                int codePoint = Char.ConvertToUtf32(value, offset);
                if (codePoint > UInt16.MaxValue)
                {
                    offset++;
                }

                string currentVariant = GetMathVariant(codePoint);
                if (currentVariant != null)
                {
                    if (variant == null)
                    {
                        variant = currentVariant;
                    }
                    else if (!String.Equals(
                        variant,
                        currentVariant,
                        StringComparison.Ordinal))
                    {
                        throw new InvalidDataException(
                            "A MathML identifier mixes multiple mathematical " +
                            "alphabet variants.");
                    }
                }
            }

            string normalizedValue = value.Normalize(
                NormalizationForm.FormKC);
            identifier.InnerText = normalizedValue;
            if (variant == null)
            {
                return;
            }

            if (String.Equals(
                    normalizedValue,
                    "I",
                    StringComparison.Ordinal) &&
                String.Equals(
                    variant,
                    "bold-italic",
                    StringComparison.Ordinal))
            {
                variant = "bold";
            }

            if (!String.Equals(
                    variant,
                    "italic",
                    StringComparison.Ordinal))
            {
                identifier.SetAttribute("mathvariant", variant);
            }
        }

        private static string GetMathVariant(int codePoint)
        {
            if (codePoint >= 0x1D400 && codePoint <= 0x1D433)
            {
                return "bold";
            }
            if (codePoint >= 0x1D434 && codePoint <= 0x1D467)
            {
                return "italic";
            }
            if (codePoint >= 0x1D468 && codePoint <= 0x1D49B)
            {
                return "bold-italic";
            }
            if (codePoint >= 0x1D49C && codePoint <= 0x1D4CF)
            {
                return "script";
            }
            if (codePoint >= 0x1D4D0 && codePoint <= 0x1D503)
            {
                return "bold-script";
            }
            if (codePoint >= 0x1D504 && codePoint <= 0x1D537)
            {
                return "fraktur";
            }
            if (codePoint >= 0x1D538 && codePoint <= 0x1D56B)
            {
                return "double-struck";
            }
            if (codePoint >= 0x1D56C && codePoint <= 0x1D59F)
            {
                return "bold-fraktur";
            }
            if (codePoint >= 0x1D5A0 && codePoint <= 0x1D5D3)
            {
                return "sans-serif";
            }
            if (codePoint >= 0x1D5D4 && codePoint <= 0x1D607)
            {
                return "bold-sans-serif";
            }
            if (codePoint >= 0x1D608 && codePoint <= 0x1D63B)
            {
                return "sans-serif-italic";
            }
            if (codePoint >= 0x1D63C && codePoint <= 0x1D66F)
            {
                return "sans-serif-bold-italic";
            }
            if (codePoint >= 0x1D670 && codePoint <= 0x1D6A3)
            {
                return "monospace";
            }
            if (codePoint >= 0x1D6A8 && codePoint <= 0x1D6E1)
            {
                return "bold";
            }
            if (codePoint >= 0x1D6E2 && codePoint <= 0x1D71B)
            {
                return "italic";
            }
            if (codePoint >= 0x1D71C && codePoint <= 0x1D755)
            {
                return "bold-italic";
            }
            if (codePoint >= 0x1D756 && codePoint <= 0x1D78F)
            {
                return "bold-sans-serif";
            }
            if (codePoint >= 0x1D790 && codePoint <= 0x1D7C9)
            {
                return "sans-serif-bold-italic";
            }
            if (codePoint >= 0x1D7CE && codePoint <= 0x1D7D7)
            {
                return "bold";
            }
            if (codePoint >= 0x1D7D8 && codePoint <= 0x1D7E1)
            {
                return "double-struck";
            }
            if (codePoint >= 0x1D7E2 && codePoint <= 0x1D7EB)
            {
                return "sans-serif";
            }
            if (codePoint >= 0x1D7EC && codePoint <= 0x1D7F5)
            {
                return "bold-sans-serif";
            }
            if (codePoint >= 0x1D7F6 && codePoint <= 0x1D7FF)
            {
                return "monospace";
            }

            if (codePoint == 0x2110 || codePoint == 0x2130)
            {
                return "script";
            }
            if (codePoint == 0x211D)
            {
                return "double-struck";
            }
            return null;
        }

        private static void ValidateMathMl(XmlDocument document)
        {
            if (document.SelectSingleNode(
                "//*[local-name()='merror']") != null)
            {
                throw new InvalidDataException(
                    "Normalized MathML contains merror.");
            }

            string text = document.InnerText;
            if (text.IndexOf('\uFFFD') >= 0 ||
                text.IndexOf('?') >= 0)
            {
                throw new InvalidDataException(
                    "Normalized MathML contains a replacement character or " +
                    "question mark.");
            }

            XmlNodeList elements = document.SelectNodes("//*");
            foreach (XmlNode node in elements)
            {
                if (!String.Equals(
                    node.NamespaceURI,
                    MathMlNamespace,
                    StringComparison.Ordinal))
                {
                    throw new InvalidDataException(
                        "Normalized MathML contains a non-MathML element: " +
                        node.Name +
                        ".");
                }
            }
        }

        private static IList<string> CollectFeatures(XmlElement root)
        {
            SortedSet<string> features =
                new SortedSet<string>(StringComparer.Ordinal);
            CollectFeaturesRecursive(root, features);
            return new List<string>(features);
        }

        private static void CollectFeaturesRecursive(
            XmlElement element,
            ISet<string> features)
        {
            if (!String.Equals(element.LocalName, "math", StringComparison.Ordinal) &&
                !String.Equals(element.LocalName, "mrow", StringComparison.Ordinal) &&
                !String.Equals(element.LocalName, "mi", StringComparison.Ordinal) &&
                !String.Equals(element.LocalName, "mn", StringComparison.Ordinal) &&
                !String.Equals(element.LocalName, "mo", StringComparison.Ordinal))
            {
                features.Add(element.LocalName);
            }
            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement != null)
                {
                    CollectFeaturesRecursive(childElement, features);
                }
            }
        }

        private static bool ContainsDotAccent(XmlElement baseElement)
        {
            XmlElement candidate = baseElement;
            bool unwrapped = true;
            while (candidate != null && unwrapped)
            {
                unwrapped = false;
                if (String.Equals(
                    candidate.LocalName,
                    "mrow",
                    StringComparison.Ordinal))
                {
                    XmlElement onlyChild = null;
                    int elementChildCount = 0;
                    foreach (XmlNode child in candidate.ChildNodes)
                    {
                        XmlElement childElement = child as XmlElement;
                        if (childElement != null)
                        {
                            onlyChild = childElement;
                            elementChildCount++;
                        }
                    }
                    if (elementChildCount == 1)
                    {
                        candidate = onlyChild;
                        unwrapped = true;
                    }
                }
                else if (String.Equals(
                    candidate.LocalName,
                    "msub",
                    StringComparison.Ordinal))
                {
                    candidate = FirstElementChild(candidate);
                    unwrapped = true;
                }
            }

            if (candidate == null ||
                !String.Equals(
                    candidate.LocalName,
                    "mover",
                    StringComparison.Ordinal))
            {
                return false;
            }

            XmlElement accent = LastElementChild(candidate);
            if (accent == null)
            {
                return false;
            }
            string text = accent.InnerText;
            return text == "\u02D9" ||
                   text == "\u0307" ||
                   text == "\u00A8" ||
                   text == "\u0308";
        }

        private static XmlElement FirstElementChild(XmlNode node)
        {
            foreach (XmlNode child in node.ChildNodes)
            {
                XmlElement element = child as XmlElement;
                if (element != null)
                {
                    return element;
                }
            }
            return null;
        }

        private static XmlElement LastElementChild(XmlNode node)
        {
            for (int index = node.ChildNodes.Count - 1;
                index >= 0;
                index--)
            {
                XmlElement element = node.ChildNodes[index] as XmlElement;
                if (element != null)
                {
                    return element;
                }
            }
            return null;
        }

        private static string Serialize(XmlDocument document)
        {
            XmlWriterSettings settings = new XmlWriterSettings();
            settings.OmitXmlDeclaration = true;
            settings.Indent = false;
            settings.NewLineHandling = NewLineHandling.None;
            settings.Encoding = new UTF8Encoding(false);
            StringBuilder value = new StringBuilder();
            using (XmlWriter writer = XmlWriter.Create(value, settings))
            {
                document.Save(writer);
            }
            return value.ToString();
        }
    }
}
