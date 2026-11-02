using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Xml;

namespace ThesisMathTypeConversion
{
    public sealed class AccentScriptRisk
    {
        public int Offset { get; set; }
        public string AccentCommand { get; set; }
        public string ScriptMarker { get; set; }
        public string SuperscriptValue { get; set; }
        public string Snippet { get; set; }

        public override string ToString()
        {
            return AccentCommand +
                   ScriptMarker +
                   " at offset " +
                   Offset.ToString(CultureInfo.InvariantCulture) +
                   ": " +
                   Snippet;
        }
    }

    public sealed class SourceAccentScriptRisk
    {
        public int SourceIndex { get; set; }
        public string AccentCharacter { get; set; }
        public string BaseText { get; set; }
        public string SuperscriptText { get; set; }
        public string SubscriptText { get; set; }

        public override string ToString()
        {
            return "sourceIndex=" +
                   SourceIndex.ToString(CultureInfo.InvariantCulture) +
                   ",accent=U+" +
                   ((int)AccentCharacter[0]).ToString("X4") +
                   ",base=" +
                   BaseText +
                   ",sup=" +
                   SuperscriptText +
                   ",sub=" +
                   SubscriptText;
        }
    }

    public static class AccentScriptRiskDetector
    {
        private const string DocumentPart = "word/document.xml";
        private const string MathNamespace =
            "http://schemas.openxmlformats.org/officeDocument/2006/math";
        private const string CombiningDotAbove = "\u0307";
        private const string CombiningDiaeresis = "\u0308";

        private static readonly string[] AccentCommands =
        {
            "\\ddot",
            "\\dot"
        };

        private static readonly string[] SpacingCommands =
        {
            "\\qquad",
            "\\quad",
            "\\,",
            "\\!",
            "\\:",
            "\\;"
        };

        public static IList<AccentScriptRisk> Find(string tex)
        {
            List<AccentScriptRisk> risks = new List<AccentScriptRisk>();
            if (String.IsNullOrWhiteSpace(tex))
            {
                return risks;
            }

            for (int offset = 0; offset < tex.Length; offset++)
            {
                string command = MatchAccentCommand(tex, offset);
                if (command == null)
                {
                    continue;
                }

                int argumentOpen = SkipWhitespace(tex, offset + command.Length);
                if (argumentOpen >= tex.Length || tex[argumentOpen] != '{')
                {
                    continue;
                }

                int argumentClose = FindMatchingBrace(tex, argumentOpen);
                if (argumentClose < 0)
                {
                    continue;
                }

                int expressionStart = offset;
                int scriptSearchStart = argumentClose + 1;
                int previous = SkipWhitespaceBackward(tex, offset - 1);
                int possibleOuterClose = SkipWhitespace(
                    tex,
                    argumentClose + 1);
                if (previous >= 0 &&
                    tex[previous] == '{' &&
                    possibleOuterClose < tex.Length &&
                    tex[possibleOuterClose] == '}')
                {
                    expressionStart = previous;
                    scriptSearchStart = possibleOuterClose + 1;
                }

                int scriptOffset = SkipDetachedEmptyBaseAndSpacing(
                    tex,
                    scriptSearchStart);
                // MathType's TeX import places a detached right superscript
                // too high when the base is a dot or double-dot accent. A
                // pure right subscript does not exhibit the defect, but a
                // combined subscript/superscript may be serialized with the
                // subscript first and must still be detected.
                if (scriptOffset < tex.Length &&
                    tex[scriptOffset] == '_')
                {
                    scriptOffset = SkipDetachedEmptyBaseAndSpacing(
                        tex,
                        FindScriptEnd(tex, scriptOffset));
                }

                if (scriptOffset >= tex.Length ||
                    tex[scriptOffset] != '^')
                {
                    offset = argumentClose;
                    continue;
                }

                int snippetEnd = FindScriptEnd(tex, scriptOffset);
                risks.Add(
                    new AccentScriptRisk
                    {
                        Offset = expressionStart,
                        AccentCommand = command,
                        ScriptMarker = tex[scriptOffset].ToString(),
                        SuperscriptValue =
                            GetSimpleScriptValue(tex, scriptOffset),
                        Snippet = tex.Substring(
                            expressionStart,
                            snippetEnd - expressionStart)
                    });
                offset = Math.Max(offset, argumentClose);
            }

            return risks;
        }

        private static string GetSimpleScriptValue(
            string tex,
            int scriptOffset)
        {
            int valueStart = SkipWhitespace(tex, scriptOffset + 1);
            if (valueStart >= tex.Length)
            {
                return String.Empty;
            }

            string value;
            if (tex[valueStart] == '{')
            {
                int close = FindMatchingBrace(tex, valueStart);
                if (close < 0)
                {
                    return String.Empty;
                }

                value = tex.Substring(
                    valueStart + 1,
                    close - valueStart - 1).Trim();
            }
            else
            {
                value = tex[valueStart].ToString();
            }

            return value.Length == 1 &&
                   value[0] <= 0x7F &&
                   Char.IsLetterOrDigit(value[0])
                ? value
                : String.Empty;
        }

        public static IList<SourceAccentScriptRisk> FindInSourceDocx(
            string documentPath)
        {
            if (String.IsNullOrWhiteSpace(documentPath) ||
                !File.Exists(documentPath))
            {
                throw new FileNotFoundException(
                    "The source DOCX was not found.",
                    documentPath);
            }

            XmlDocument documentXml = new XmlDocument();
            using (FileStream stream = File.Open(
                documentPath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read))
            using (ZipArchive archive = new ZipArchive(
                stream,
                ZipArchiveMode.Read,
                false,
                Encoding.UTF8))
            {
                ZipArchiveEntry entry = archive.GetEntry(DocumentPart);
                if (entry == null)
                {
                    throw new InvalidDataException(
                        "The DOCX is missing " + DocumentPart + ".");
                }

                using (Stream xmlStream = entry.Open())
                {
                    documentXml.Load(xmlStream);
                }
            }

            XmlNamespaceManager namespaces =
                new XmlNamespaceManager(documentXml.NameTable);
            namespaces.AddNamespace("m", MathNamespace);
            XmlNodeList equations = documentXml.SelectNodes(
                "//m:oMath[not(ancestor::m:oMath)]",
                namespaces);
            List<SourceAccentScriptRisk> risks =
                new List<SourceAccentScriptRisk>();
            if (equations == null)
            {
                return risks;
            }

            for (int index = 0; index < equations.Count; index++)
            {
                XmlNode equation = equations[index];
                XmlNodeList accents = equation.SelectNodes(
                    ".//m:sSup/m:e/m:acc | .//m:sSubSup/m:e/m:acc",
                    namespaces);
                if (accents == null)
                {
                    continue;
                }

                foreach (XmlNode accent in accents)
                {
                    XmlNode character = accent.SelectSingleNode(
                        "./m:accPr/m:chr",
                        namespaces);
                    string accentValue = character == null
                        ? String.Empty
                        : GetMathAttribute(character, "val");
                    if (accentValue != CombiningDotAbove &&
                        accentValue != CombiningDiaeresis)
                    {
                        continue;
                    }

                    XmlNode scriptOwner = accent.ParentNode == null
                        ? null
                        : accent.ParentNode.ParentNode;
                    risks.Add(
                        new SourceAccentScriptRisk
                        {
                            SourceIndex = index + 1,
                            AccentCharacter = accentValue,
                            BaseText = GetMathText(accent, namespaces),
                            SuperscriptText = GetMathText(
                                scriptOwner == null
                                    ? null
                                    : scriptOwner.SelectSingleNode(
                                        "./m:sup",
                                        namespaces),
                                namespaces),
                            SubscriptText = GetMathText(
                                scriptOwner == null
                                    ? null
                                    : scriptOwner.SelectSingleNode(
                                        "./m:sub",
                                        namespaces),
                                namespaces)
                        });
                }
            }

            return risks;
        }

        private static string MatchAccentCommand(string tex, int offset)
        {
            foreach (string command in AccentCommands)
            {
                if (offset + command.Length > tex.Length ||
                    String.CompareOrdinal(
                        tex,
                        offset,
                        command,
                        0,
                        command.Length) != 0)
                {
                    continue;
                }

                int boundary = offset + command.Length;
                if (boundary >= tex.Length ||
                    !Char.IsLetter(tex[boundary]))
                {
                    return command;
                }
            }

            return null;
        }

        private static string GetMathAttribute(XmlNode node, string localName)
        {
            if (node == null || node.Attributes == null)
            {
                return String.Empty;
            }

            XmlAttribute attribute = node.Attributes[
                localName,
                MathNamespace];
            return attribute == null ? String.Empty : attribute.Value;
        }

        private static string GetMathText(
            XmlNode node,
            XmlNamespaceManager namespaces)
        {
            if (node == null)
            {
                return String.Empty;
            }

            XmlNodeList textNodes = node.SelectNodes(".//m:t", namespaces);
            if (textNodes == null)
            {
                return String.Empty;
            }

            StringBuilder value = new StringBuilder();
            foreach (XmlNode text in textNodes)
            {
                value.Append(text.InnerText);
            }

            return value.ToString();
        }

        private static int SkipDetachedEmptyBaseAndSpacing(
            string tex,
            int offset)
        {
            int current = SkipWhitespace(tex, offset);
            bool advanced;
            do
            {
                advanced = false;
                if (current < tex.Length && tex[current] == '{')
                {
                    int close = FindMatchingBrace(tex, current);
                    if (close >= 0 &&
                        String.IsNullOrWhiteSpace(
                            tex.Substring(current + 1, close - current - 1)))
                    {
                        current = SkipWhitespace(tex, close + 1);
                        advanced = true;
                        continue;
                    }
                }

                foreach (string command in SpacingCommands)
                {
                    if (current + command.Length <= tex.Length &&
                        String.CompareOrdinal(
                            tex,
                            current,
                            command,
                            0,
                            command.Length) == 0)
                    {
                        current = SkipWhitespace(
                            tex,
                            current + command.Length);
                        advanced = true;
                        break;
                    }
                }
            }
            while (advanced);

            return current;
        }

        private static int FindScriptEnd(string tex, int scriptOffset)
        {
            int valueStart = SkipWhitespace(tex, scriptOffset + 1);
            if (valueStart >= tex.Length)
            {
                return scriptOffset + 1;
            }

            if (tex[valueStart] == '{')
            {
                int close = FindMatchingBrace(tex, valueStart);
                return close >= 0 ? close + 1 : tex.Length;
            }

            if (tex[valueStart] == '\\')
            {
                int end = valueStart + 1;
                while (end < tex.Length && Char.IsLetter(tex[end]))
                {
                    end++;
                }

                return end;
            }

            return valueStart + 1;
        }

        private static int FindMatchingBrace(string value, int opening)
        {
            int depth = 0;
            for (int index = opening; index < value.Length; index++)
            {
                if (value[index] == '{')
                {
                    depth++;
                }
                else if (value[index] == '}')
                {
                    depth--;
                    if (depth == 0)
                    {
                        return index;
                    }
                }
            }

            return -1;
        }

        private static int SkipWhitespace(string value, int offset)
        {
            int current = offset;
            while (current < value.Length && Char.IsWhiteSpace(value[current]))
            {
                current++;
            }

            return current;
        }

        private static int SkipWhitespaceBackward(string value, int offset)
        {
            int current = offset;
            while (current >= 0 && Char.IsWhiteSpace(value[current]))
            {
                current--;
            }

            return current;
        }
    }
}
