using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Xml;

namespace ThesisMathTypeConversionV2
{
    public sealed class MathMlCanonicalForm
    {
        public string Xml { get; set; }
        public string Sha256 { get; set; }
        public string TokenSequence { get; set; }
        public string StructureSignature { get; set; }
        public string StyleSequence { get; set; }
        public int StyledCharacterCount { get; set; }
        public string MtefCharacterStyleSequence { get; set; }
    }

    public static class MathMlCanonicalizer
    {
        private const string MathMlNamespace =
            "http://www.w3.org/1998/Math/MathML";

        private static readonly HashSet<string> SemanticAttributes =
            new HashSet<string>(StringComparer.Ordinal)
            {
                "accent",
                "accentunder",
                "columnalign",
                "columnlines",
                "columnspacing",
                "columnspan",
                "denomalign",
                "displaystyle",
                "encoding",
                "fence",
                "form",
                "linethickness",
                "lspace",
                "mathvariant",
                "maxsize",
                "minsize",
                "movablelimits",
                "numalign",
                "open",
                "rowalign",
                "rowlines",
                "rowspacing",
                "rowspan",
                "rspace",
                "separator",
                "separators",
                "stretchy",
                "symmetric",
                "close"
            };

        public static MathMlCanonicalForm Canonicalize(string mathMl)
        {
            XmlDocument source = LoadMathMl(mathMl);
            XmlDocument canonical = new XmlDocument();
            canonical.PreserveWhitespace = false;
            XmlElement root = canonical.CreateElement(
                "math",
                MathMlNamespace);
            canonical.AppendChild(root);

            XmlNode content = FindSemanticRoot(source.DocumentElement);
            AppendCanonicalChildren(canonical, root, content);
            ExpandFencedElements(root);
            ExpandNumericListTokens(root);
            UnwrapRedundantRows(root);

            string xml = Serialize(canonical);
            return new MathMlCanonicalForm
            {
                Xml = xml,
                Sha256 = ComputeSha256(xml),
                TokenSequence = BuildTokenSequence(root),
                StructureSignature = BuildStructureSignature(root),
                StyleSequence = BuildStyleSequence(root),
                StyledCharacterCount =
                    CountStyledCharacters(root, null),
                MtefCharacterStyleSequence =
                    BuildMtefCharacterStyleSequence(root)
            };
        }

        private static void ExpandNumericListTokens(XmlElement root)
        {
            XmlNodeList numericNodes =
                root.SelectNodes(".//*[local-name()='mn']");
            List<XmlElement> candidates = new List<XmlElement>();
            foreach (XmlNode node in numericNodes)
            {
                XmlElement element = node as XmlElement;
                if (element != null &&
                    IsCommaSeparatedIntegerList(
                        NormalizeTokenText(element.InnerText)) &&
                    IsExplicitListContext(element))
                {
                    candidates.Add(element);
                }
            }

            foreach (XmlElement candidate in candidates)
            {
                string[] parts = NormalizeTokenText(
                    candidate.InnerText).Split(',');
                for (int index = 0; index < parts.Length; index++)
                {
                    if (index > 0)
                    {
                        XmlElement separator =
                            candidate.OwnerDocument.CreateElement(
                                "mo",
                                MathMlNamespace);
                        separator.InnerText = ",";
                        candidate.ParentNode.InsertBefore(
                            separator,
                            candidate);
                    }

                    XmlElement number =
                        (XmlElement)candidate.CloneNode(false);
                    number.InnerText = parts[index];
                    candidate.ParentNode.InsertBefore(
                        number,
                        candidate);
                }
                candidate.ParentNode.RemoveChild(candidate);
            }
        }

        private static bool IsCommaSeparatedIntegerList(string text)
        {
            if (String.IsNullOrEmpty(text) ||
                text.IndexOf(',') < 0)
            {
                return false;
            }

            string[] parts = text.Split(',');
            if (parts.Length < 2)
            {
                return false;
            }
            foreach (string part in parts)
            {
                if (part.Length == 0)
                {
                    return false;
                }
                foreach (char value in part)
                {
                    if (!Char.IsDigit(value))
                    {
                        return false;
                    }
                }
            }
            return true;
        }

        private static bool IsExplicitListContext(XmlElement number)
        {
            XmlNode sibling = number.NextSibling;
            while (sibling != null)
            {
                XmlElement element = sibling as XmlElement;
                if (element != null)
                {
                    string text = NormalizeTokenText(element.InnerText);
                    return text == "," ||
                           text == "\u2026" ||
                           text == "\u22EF";
                }
                sibling = sibling.NextSibling;
            }
            return false;
        }

        public static XmlDocument LoadMathMl(string mathMl)
        {
            if (String.IsNullOrWhiteSpace(mathMl))
            {
                throw new InvalidDataException("MathML is empty.");
            }

            XmlDocument document = new XmlDocument();
            document.PreserveWhitespace = false;
            document.XmlResolver = null;
            document.LoadXml(mathMl);
            if (document.DocumentElement == null ||
                !String.Equals(
                    document.DocumentElement.LocalName,
                    "math",
                    StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    "MathML must have a math document element.");
            }
            return document;
        }

        private static XmlNode FindSemanticRoot(XmlElement math)
        {
            if (String.Equals(
                math.LocalName,
                "semantics",
                StringComparison.Ordinal))
            {
                foreach (XmlNode semanticChild in math.ChildNodes)
                {
                    if (semanticChild.NodeType == XmlNodeType.Element &&
                        !String.Equals(
                            semanticChild.LocalName,
                            "annotation",
                            StringComparison.Ordinal) &&
                        !String.Equals(
                            semanticChild.LocalName,
                            "annotation-xml",
                            StringComparison.Ordinal))
                    {
                        return semanticChild;
                    }
                }
                return math;
            }

            foreach (XmlNode child in math.ChildNodes)
            {
                if (child.NodeType != XmlNodeType.Element)
                {
                    continue;
                }

                if (String.Equals(
                    child.LocalName,
                    "semantics",
                    StringComparison.Ordinal))
                {
                    foreach (XmlNode semanticChild in child.ChildNodes)
                    {
                        if (semanticChild.NodeType == XmlNodeType.Element &&
                            !String.Equals(
                                semanticChild.LocalName,
                                "annotation",
                                StringComparison.Ordinal) &&
                            !String.Equals(
                                semanticChild.LocalName,
                                "annotation-xml",
                                StringComparison.Ordinal))
                        {
                            return semanticChild;
                        }
                    }
                }
            }
            return math;
        }

        private static void AppendCanonicalChildren(
            XmlDocument target,
            XmlElement parent,
            XmlNode source)
        {
            if (String.Equals(source.LocalName, "math", StringComparison.Ordinal))
            {
                foreach (XmlNode child in source.ChildNodes)
                {
                    AppendCanonicalNode(target, parent, child);
                }
                return;
            }
            AppendCanonicalNode(target, parent, source);
        }

        private static void AppendCanonicalNode(
            XmlDocument target,
            XmlElement parent,
            XmlNode source)
        {
            if (source.NodeType == XmlNodeType.Text ||
                source.NodeType == XmlNodeType.CDATA)
            {
                string text = String.Equals(
                    parent.LocalName,
                    "mo",
                    StringComparison.Ordinal)
                    ? NormalizeOperatorText(source.Value)
                    : NormalizeTokenText(source.Value);
                if (text.Length > 0)
                {
                    parent.AppendChild(target.CreateTextNode(text));
                }
                return;
            }

            if (source.NodeType != XmlNodeType.Element)
            {
                return;
            }

            if (String.Equals(source.LocalName, "semantics", StringComparison.Ordinal))
            {
                XmlNode semanticRoot = FindSemanticRoot((XmlElement)source);
                if (Object.ReferenceEquals(semanticRoot, source))
                {
                    throw new InvalidDataException(
                        "MathML semantics does not contain a presentation branch.");
                }
                AppendCanonicalNode(target, parent, semanticRoot);
                return;
            }

            if (String.Equals(source.LocalName, "annotation", StringComparison.Ordinal) ||
                String.Equals(source.LocalName, "annotation-xml", StringComparison.Ordinal))
            {
                return;
            }

            XmlElement element = target.CreateElement(
                source.LocalName,
                MathMlNamespace);
            CopySemanticAttributes(target, element, source.Attributes);
            if (String.Equals(
                    source.LocalName,
                    "mi",
                    StringComparison.Ordinal) &&
                !element.HasAttribute("mathvariant"))
            {
                string inferredVariant =
                    InferLegacyMathematicalVariant(source.InnerText);
                if (inferredVariant != null)
                {
                    element.SetAttribute(
                        "mathvariant",
                        inferredVariant);
                }
            }
            parent.AppendChild(element);
            foreach (XmlNode child in source.ChildNodes)
            {
                AppendCanonicalNode(target, element, child);
            }
        }

        private static string InferLegacyMathematicalVariant(string text)
        {
            if (String.IsNullOrEmpty(text))
            {
                return null;
            }
            for (int offset = 0; offset < text.Length; offset++)
            {
                int codePoint = Char.ConvertToUtf32(text, offset);
                if (codePoint == 0x2102 ||
                    codePoint == 0x210D ||
                    codePoint == 0x2115 ||
                    codePoint == 0x2119 ||
                    codePoint == 0x211A ||
                    codePoint == 0x211D ||
                    codePoint == 0x2124)
                {
                    if (codePoint > UInt16.MaxValue)
                    {
                        offset++;
                    }
                    continue;
                }
                return null;
            }
            return "double-struck";
        }

        private static void CopySemanticAttributes(
            XmlDocument target,
            XmlElement destination,
            XmlAttributeCollection attributes)
        {
            List<XmlAttribute> selected = new List<XmlAttribute>();
            foreach (XmlAttribute attribute in attributes)
            {
                if (SemanticAttributes.Contains(attribute.LocalName))
                {
                    selected.Add(attribute);
                }
            }
            selected.Sort(
                delegate(XmlAttribute left, XmlAttribute right)
                {
                    return String.CompareOrdinal(
                        left.LocalName,
                        right.LocalName);
                });
            foreach (XmlAttribute attribute in selected)
            {
                destination.SetAttribute(
                    attribute.LocalName,
                    NormalizeAttributeValue(attribute.Value));
            }
        }

        private static string NormalizeAttributeValue(string value)
        {
            return String.IsNullOrWhiteSpace(value)
                ? String.Empty
                : value.Trim().ToLowerInvariant();
        }

        private static string NormalizeTokenText(string value)
        {
            if (String.IsNullOrEmpty(value))
            {
                return String.Empty;
            }
            return value
                .Normalize(NormalizationForm.FormKC)
                .Replace("\r", String.Empty)
                .Replace("\n", String.Empty)
                .Replace("\t", String.Empty)
                .Replace("\u200B", String.Empty)
                .Trim();
        }

        private static string NormalizeOperatorText(string value)
        {
            string normalized = NormalizeTokenText(value);
            if (normalized == "-" || normalized == "\u2212")
            {
                return "\u2212";
            }
            if (normalized == "~" ||
                normalized == "\u02DC" ||
                normalized == "\u0303")
            {
                return "\u02DC";
            }
            if (normalized == "\u00AF" ||
                normalized == "\u02C9" ||
                normalized == "\u0304" ||
                normalized == "\u0305")
            {
                return "\u00AF";
            }
            if (normalized == "\u0307" || normalized == "\u02D9")
            {
                return "\u02D9";
            }
            if (normalized == "\u2061" ||
                normalized == "\u2062" ||
                normalized == "\u2063" ||
                normalized == "\u2064")
            {
                return String.Empty;
            }
            return normalized;
        }

        private static void ExpandFencedElements(XmlElement parent)
        {
            List<XmlElement> children = new List<XmlElement>();
            foreach (XmlNode child in parent.ChildNodes)
            {
                XmlElement element = child as XmlElement;
                if (element != null)
                {
                    children.Add(element);
                }
            }

            foreach (XmlElement child in children)
            {
                ExpandFencedElements(child);
                if (!String.Equals(
                    child.LocalName,
                    "mfenced",
                    StringComparison.Ordinal))
                {
                    continue;
                }

                XmlDocument document = parent.OwnerDocument;
                XmlElement row = document.CreateElement(
                    "mrow",
                    MathMlNamespace);
                string open = child.HasAttribute("open")
                    ? child.GetAttribute("open")
                    : "(";
                string close = child.HasAttribute("close")
                    ? child.GetAttribute("close")
                    : ")";
                string separators = child.HasAttribute("separators")
                    ? child.GetAttribute("separators")
                    : ",";

                AppendFenceOperator(document, row, open);
                List<XmlNode> contents = new List<XmlNode>();
                foreach (XmlNode item in child.ChildNodes)
                {
                    contents.Add(item);
                }
                for (int index = 0; index < contents.Count; index++)
                {
                    row.AppendChild(contents[index]);
                    if (index + 1 < contents.Count)
                    {
                        string separator = GetFenceSeparator(
                            separators,
                            index);
                        AppendFenceOperator(
                            document,
                            row,
                            separator);
                    }
                }
                AppendFenceOperator(document, row, close);
                parent.ReplaceChild(row, child);
            }
        }

        private static void AppendFenceOperator(
            XmlDocument document,
            XmlElement row,
            string value)
        {
            if (String.IsNullOrEmpty(value))
            {
                return;
            }
            XmlElement operation = document.CreateElement(
                "mo",
                MathMlNamespace);
            operation.InnerText = NormalizeOperatorText(value);
            row.AppendChild(operation);
        }

        private static string GetFenceSeparator(
            string separators,
            int index)
        {
            string normalized = String.IsNullOrWhiteSpace(separators)
                ? ","
                : separators.Replace(" ", String.Empty);
            if (normalized.Length == 0)
            {
                return String.Empty;
            }
            return normalized[
                Math.Min(index, normalized.Length - 1)].ToString();
        }

        private static void UnwrapRedundantRows(XmlElement parent)
        {
            List<XmlElement> children = new List<XmlElement>();
            foreach (XmlNode child in parent.ChildNodes)
            {
                XmlElement element = child as XmlElement;
                if (element != null)
                {
                    children.Add(element);
                }
            }
            foreach (XmlElement child in children)
            {
                UnwrapRedundantRows(child);
            }

            bool parentAllowsUnwrap =
                String.Equals(parent.LocalName, "math", StringComparison.Ordinal) ||
                String.Equals(parent.LocalName, "mrow", StringComparison.Ordinal);
            if (!parentAllowsUnwrap)
            {
                return;
            }

            bool changed = true;
            while (changed)
            {
                changed = false;
                if (parent.ChildNodes.Count == 1)
                {
                    XmlElement only = parent.FirstChild as XmlElement;
                    if (only != null &&
                        String.Equals(
                            only.LocalName,
                            "mrow",
                            StringComparison.Ordinal) &&
                        only.Attributes.Count == 0)
                    {
                        while (only.HasChildNodes)
                        {
                            parent.InsertBefore(only.FirstChild, only);
                        }
                        parent.RemoveChild(only);
                        changed = true;
                    }
                }
            }
        }

        private static string BuildTokenSequence(XmlElement root)
        {
            List<string> tokens = new List<string>();
            CollectTokens(root, null, tokens, false);
            return String.Join("|", tokens.ToArray());
        }

        private static void CollectTokens(
            XmlElement element,
            string inheritedVariant,
            IList<string> tokens,
            bool mergeWithPreviousText)
        {
            string variant = element.HasAttribute("mathvariant")
                ? element.GetAttribute("mathvariant")
                : inheritedVariant;
            if (IsTokenElement(element.LocalName))
            {
                string text = NormalizeTokenText(element.InnerText);
                bool isTextLike =
                    IsTextLikeToken(element, variant);
                bool isOperatorLike =
                    IsOperatorLikeToken(element, text);
                if (isOperatorLike)
                {
                    text = NormalizeOperatorText(text);
                }
                if (!String.IsNullOrEmpty(text))
                {
                    string prefix = isOperatorLike
                        ? "mo:"
                        : (isTextLike
                            ? "text:"
                            : element.LocalName + ":");
                    if (!isOperatorLike &&
                        isTextLike &&
                        mergeWithPreviousText &&
                        tokens.Count > 0 &&
                        tokens[tokens.Count - 1].StartsWith(
                            "text:",
                            StringComparison.Ordinal))
                    {
                        tokens[tokens.Count - 1] =
                            tokens[tokens.Count - 1] + text;
                    }
                    else
                    {
                        tokens.Add(prefix + text);
                    }
                }
                return;
            }

            bool previousChildWasTextLike = false;
            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement != null)
                {
                    bool childIsTextLike =
                        IsTextLikeToken(childElement, variant);
                    CollectTokens(
                        childElement,
                        variant,
                        tokens,
                        previousChildWasTextLike && childIsTextLike);
                    previousChildWasTextLike = childIsTextLike;
                }
            }
        }

        private static bool IsOperatorLikeToken(
            XmlElement element,
            string text)
        {
            if (!String.Equals(
                    element.LocalName,
                    "mi",
                    StringComparison.Ordinal) &&
                !String.Equals(
                    element.LocalName,
                    "mo",
                    StringComparison.Ordinal) &&
                !String.Equals(
                    element.LocalName,
                    "mtext",
                    StringComparison.Ordinal))
            {
                return false;
            }
            if (String.IsNullOrEmpty(text))
            {
                return false;
            }
            if (IsAccentOperatorText(text))
            {
                return true;
            }

            for (int offset = 0; offset < text.Length; offset++)
            {
                UnicodeCategory category =
                    CharUnicodeInfo.GetUnicodeCategory(text, offset);
                if (category != UnicodeCategory.MathSymbol &&
                    category != UnicodeCategory.ModifierSymbol &&
                    category != UnicodeCategory.OtherSymbol &&
                    category != UnicodeCategory.DashPunctuation &&
                    category != UnicodeCategory.OpenPunctuation &&
                    category != UnicodeCategory.ClosePunctuation &&
                    category != UnicodeCategory.InitialQuotePunctuation &&
                    category != UnicodeCategory.FinalQuotePunctuation &&
                    category != UnicodeCategory.OtherPunctuation)
                {
                    return false;
                }
                if (Char.ConvertToUtf32(text, offset) > UInt16.MaxValue)
                {
                    offset++;
                }
            }
            return true;
        }

        private static bool IsAccentOperatorText(string text)
        {
            return text == "^" ||
                   text == "\u00A8" ||
                   text == "\u00AF" ||
                   text == "\u02C6" ||
                   text == "\u02C9" ||
                   text == "\u02D9" ||
                   text == "\u02DC" ||
                   text == "\u0303" ||
                   text == "\u0304" ||
                   text == "\u0305" ||
                   text == "\u0307" ||
                   text == "\u0308" ||
                   text == "\u20D7";
        }

        private static bool IsTextLikeToken(
            XmlElement element,
            string inheritedVariant)
        {
            string variant = element.HasAttribute("mathvariant")
                ? element.GetAttribute("mathvariant")
                : inheritedVariant;
            string text = NormalizeTokenText(element.InnerText);
            return !String.IsNullOrEmpty(text) &&
                (String.Equals(
                     element.LocalName,
                     "mtext",
                     StringComparison.Ordinal) ||
                 (String.Equals(
                      element.LocalName,
                      "mi",
                      StringComparison.Ordinal) &&
                  (String.Equals(
                       variant,
                       "normal",
                       StringComparison.OrdinalIgnoreCase) ||
                   text.Length > 1)));
        }

        private static bool IsTokenElement(string localName)
        {
            return String.Equals(localName, "mi", StringComparison.Ordinal) ||
                   String.Equals(localName, "mn", StringComparison.Ordinal) ||
                   String.Equals(localName, "mo", StringComparison.Ordinal) ||
                   String.Equals(localName, "mtext", StringComparison.Ordinal) ||
                   String.Equals(localName, "ms", StringComparison.Ordinal);
        }

        private static string BuildStructureSignature(XmlElement root)
        {
            List<string> items = new List<string>();
            CollectStructureItems(root, null, items);
            return JoinStructureItems(items);
        }

        private static void CollectStructureItems(
            XmlElement element,
            string inheritedVariant,
            IList<string> items)
        {
            string variant = element.HasAttribute("mathvariant")
                ? element.GetAttribute("mathvariant")
                : inheritedVariant;
            if (String.Equals(
                    element.LocalName,
                    "maligngroup",
                    StringComparison.Ordinal) ||
                String.Equals(
                    element.LocalName,
                    "malignmark",
                    StringComparison.Ordinal))
            {
                return;
            }
            if (IsTokenElement(element.LocalName))
            {
                string text = NormalizeTokenText(element.InnerText);
                if (!String.IsNullOrEmpty(text))
                {
                    string token = GetStructureToken(
                        element,
                        variant,
                        text);
                    if (!String.Equals(
                            token,
                            "L",
                            StringComparison.Ordinal) ||
                        items.Count == 0 ||
                        !String.Equals(
                            items[items.Count - 1],
                            "L",
                            StringComparison.Ordinal))
                    {
                        items.Add(token);
                    }
                }
                return;
            }
            if (IsTransparentStructureWrapper(element.LocalName))
            {
                foreach (XmlNode child in element.ChildNodes)
                {
                    XmlElement childElement = child as XmlElement;
                    if (childElement != null)
                    {
                        CollectStructureItems(
                            childElement,
                            variant,
                            items);
                    }
                }
                return;
            }
            if (TryCollectLeadingVariationScript(
                element,
                variant,
                items))
            {
                return;
            }

            List<XmlElement> children = new List<XmlElement>();
            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement != null)
                {
                    children.Add(childElement);
                }
            }

            List<string> slots = new List<string>();
            if (String.Equals(
                    element.LocalName,
                    "msqrt",
                    StringComparison.Ordinal) ||
                String.Equals(
                    element.LocalName,
                    "mtd",
                    StringComparison.Ordinal))
            {
                List<string> contents = new List<string>();
                foreach (XmlElement child in children)
                {
                    CollectStructureItems(
                        child,
                        variant,
                        contents);
                }
                slots.Add(JoinStructureItems(contents));
            }
            else
            {
                foreach (XmlElement child in children)
                {
                    List<string> contents = new List<string>();
                    CollectStructureItems(
                        child,
                        variant,
                        contents);
                    slots.Add(JoinStructureItems(contents));
                }
            }

            if (IsScriptElement(element.LocalName) &&
                slots.Count > 0 &&
                items.Count > 0)
            {
                if (String.Equals(
                    slots[0],
                    "∅",
                    StringComparison.Ordinal))
                {
                    slots[0] = items[items.Count - 1];
                    items.RemoveAt(items.Count - 1);
                }
                else
                {
                    int openingFence =
                        FindOpeningFenceIndex(items, slots[0]);
                    if (openingFence >= 0)
                    {
                        List<string> fenced = new List<string>();
                        for (int itemIndex = openingFence;
                            itemIndex < items.Count;
                            itemIndex++)
                        {
                            fenced.Add(items[itemIndex]);
                        }
                        fenced.Add(slots[0]);
                        while (items.Count > openingFence)
                        {
                            items.RemoveAt(items.Count - 1);
                        }
                        slots[0] = JoinStructureItems(fenced);
                    }
                }
            }

            items.Add(
                element.LocalName +
                "(" +
                String.Join(",", slots.ToArray()) +
                ")");
        }

        private static bool TryCollectLeadingVariationScript(
            XmlElement element,
            string inheritedVariant,
            IList<string> items)
        {
            if (!IsScriptElement(element.LocalName))
            {
                return false;
            }

            List<XmlElement> scriptChildren =
                GetElementChildren(element);
            if (scriptChildren.Count < 2)
            {
                return false;
            }

            XmlElement baseElement = scriptChildren[0];
            if (!String.Equals(
                baseElement.LocalName,
                "mrow",
                StringComparison.Ordinal))
            {
                return false;
            }

            List<XmlElement> baseChildren =
                GetElementChildren(baseElement);
            if (baseChildren.Count != 2 ||
                !String.Equals(
                    baseChildren[0].LocalName,
                    "mi",
                    StringComparison.Ordinal))
            {
                return false;
            }

            string leadingText =
                NormalizeTokenText(baseChildren[0].InnerText);
            if (!String.Equals(
                    leadingText,
                    "\u03B4",
                    StringComparison.Ordinal) &&
                !String.Equals(
                    leadingText,
                    "\u0394",
                    StringComparison.Ordinal))
            {
                return false;
            }

            CollectStructureItems(
                baseChildren[0],
                inheritedVariant,
                items);

            List<string> slots = new List<string>();
            List<string> baseSlot = new List<string>();
            CollectStructureItems(
                baseChildren[1],
                inheritedVariant,
                baseSlot);
            slots.Add(JoinStructureItems(baseSlot));
            for (int index = 1;
                index < scriptChildren.Count;
                index++)
            {
                List<string> slot = new List<string>();
                CollectStructureItems(
                    scriptChildren[index],
                    inheritedVariant,
                    slot);
                slots.Add(JoinStructureItems(slot));
            }
            items.Add(
                element.LocalName +
                "(" +
                String.Join(",", slots.ToArray()) +
                ")");
            return true;
        }

        private static List<XmlElement> GetElementChildren(
            XmlElement element)
        {
            List<XmlElement> children = new List<XmlElement>();
            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement != null)
                {
                    children.Add(childElement);
                }
            }
            return children;
        }

        private static string GetStructureToken(
            XmlElement element,
            string variant,
            string text)
        {
            if (String.Equals(
                    element.LocalName,
                    "mo",
                    StringComparison.Ordinal) &&
                IsFenceText(text))
            {
                return "F:" + text;
            }
            if (IsOperatorLikeToken(element, text))
            {
                return "T";
            }
            return IsTextLikeToken(element, variant)
                ? "L"
                : "T";
        }

        private static bool IsFenceText(string text)
        {
            return text == "(" ||
                   text == ")" ||
                   text == "[" ||
                   text == "]" ||
                   text == "{" ||
                   text == "}" ||
                   text == "|" ||
                   text == "‖" ||
                   text == "∥" ||
                   text == "⟨" ||
                   text == "⟩" ||
                   text == "⌈" ||
                   text == "⌉" ||
                   text == "⌊" ||
                   text == "⌋";
        }

        private static int FindOpeningFenceIndex(
            IList<string> items,
            string closingFence)
        {
            string openingFence = null;
            if (String.Equals(closingFence, "F:)", StringComparison.Ordinal))
            {
                openingFence = "F:(";
            }
            else if (String.Equals(
                closingFence,
                "F:]",
                StringComparison.Ordinal))
            {
                openingFence = "F:[";
            }
            else if (String.Equals(
                closingFence,
                "F:}",
                StringComparison.Ordinal))
            {
                openingFence = "F:{";
            }
            else if (String.Equals(
                closingFence,
                "F:⟩",
                StringComparison.Ordinal))
            {
                openingFence = "F:⟨";
            }
            else if (String.Equals(
                closingFence,
                "F:⌉",
                StringComparison.Ordinal))
            {
                openingFence = "F:⌈";
            }
            else if (String.Equals(
                closingFence,
                "F:⌋",
                StringComparison.Ordinal))
            {
                openingFence = "F:⌊";
            }
            else if (String.Equals(
                         closingFence,
                         "F:|",
                         StringComparison.Ordinal) ||
                     String.Equals(
                         closingFence,
                         "F:‖",
                         StringComparison.Ordinal) ||
                     String.Equals(
                         closingFence,
                         "F:∥",
                         StringComparison.Ordinal))
            {
                openingFence = closingFence;
            }
            if (openingFence == null)
            {
                return -1;
            }

            if (String.Equals(
                openingFence,
                closingFence,
                StringComparison.Ordinal))
            {
                for (int index = items.Count - 1; index >= 0; index--)
                {
                    if (String.Equals(
                        items[index],
                        openingFence,
                        StringComparison.Ordinal))
                    {
                        return index;
                    }
                }
                return -1;
            }

            int nestedDepth = 0;
            for (int index = items.Count - 1; index >= 0; index--)
            {
                if (String.Equals(
                    items[index],
                    closingFence,
                    StringComparison.Ordinal))
                {
                    nestedDepth++;
                    continue;
                }
                if (!String.Equals(
                    items[index],
                    openingFence,
                    StringComparison.Ordinal))
                {
                    continue;
                }
                if (nestedDepth == 0)
                {
                    return index;
                }
                nestedDepth--;
            }
            return -1;
        }

        private static bool IsTransparentStructureWrapper(string localName)
        {
            return String.Equals(localName, "math", StringComparison.Ordinal) ||
                   String.Equals(localName, "mrow", StringComparison.Ordinal) ||
                   String.Equals(localName, "mstyle", StringComparison.Ordinal) ||
                   String.Equals(localName, "mspace", StringComparison.Ordinal);
        }

        private static bool IsScriptElement(string localName)
        {
            return String.Equals(localName, "msub", StringComparison.Ordinal) ||
                   String.Equals(localName, "msup", StringComparison.Ordinal) ||
                   String.Equals(
                       localName,
                       "msubsup",
                       StringComparison.Ordinal);
        }

        private static string JoinStructureItems(IList<string> items)
        {
            if (items == null || items.Count == 0)
            {
                return "∅";
            }
            if (items.Count == 1)
            {
                return items[0];
            }
            return "[" + String.Join(";", new List<string>(items).ToArray()) + "]";
        }

        private static string BuildStyleSequence(XmlElement root)
        {
            List<string> styles = new List<string>();
            int position = 0;
            CollectStyleSequence(root, null, styles, ref position);
            return String.Join("|", styles.ToArray());
        }

        private static void CollectStyleSequence(
            XmlElement element,
            string inheritedVariant,
            IList<string> styles,
            ref int position)
        {
            string variant = element.HasAttribute("mathvariant")
                ? element.GetAttribute("mathvariant")
                : inheritedVariant;
            if (IsTokenElement(element.LocalName))
            {
                string text = NormalizeTokenText(element.InnerText);
                if (IsOperatorLikeToken(element, text))
                {
                    text = NormalizeOperatorText(text);
                }
                string style = GetMathMlCharacterStyle(
                    element,
                    variant,
                    text);
                for (int offset = 0; offset < text.Length; offset++)
                {
                    int codePoint = Char.ConvertToUtf32(text, offset);
                    styles.Add(
                        position.ToString(CultureInfo.InvariantCulture) +
                        ":" +
                        codePoint.ToString(CultureInfo.InvariantCulture) +
                        ":" +
                        style);
                    position++;
                    if (codePoint > UInt16.MaxValue)
                    {
                        offset++;
                    }
                }
                return;
            }

            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement != null)
                {
                    CollectStyleSequence(
                        childElement,
                        variant,
                        styles,
                        ref position);
                }
            }
        }

        private static string GetMathMlCharacterStyle(
            XmlElement element,
            string variant,
            string text)
        {
            string normalizedVariant = String.IsNullOrWhiteSpace(variant)
                ? String.Empty
                : variant.Trim().ToLowerInvariant();
            if (normalizedVariant.IndexOf(
                    "bold",
                    StringComparison.Ordinal) >= 0)
            {
                return normalizedVariant.IndexOf(
                    "italic",
                    StringComparison.Ordinal) >= 0
                    ? "BI"
                    : "B";
            }
            if (normalizedVariant.Length > 0 &&
                !String.Equals(
                    normalizedVariant,
                    "normal",
                    StringComparison.Ordinal) &&
                !String.Equals(
                    normalizedVariant,
                    "italic",
                    StringComparison.Ordinal))
            {
                return normalizedVariant;
            }
            if (String.Equals(
                    element.LocalName,
                    "mtext",
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
                    "ms",
                    StringComparison.Ordinal) ||
                String.Equals(
                    normalizedVariant,
                    "normal",
                    StringComparison.Ordinal) ||
                IsOperatorLikeToken(element, text) ||
                (String.Equals(
                     element.LocalName,
                     "mi",
                     StringComparison.Ordinal) &&
                 CountCodePoints(text) > 1 &&
                 normalizedVariant.Length == 0))
            {
                return "U";
            }
            return "I";
        }

        private static int CountCodePoints(string text)
        {
            int count = 0;
            for (int offset = 0; offset < text.Length; offset++)
            {
                int codePoint = Char.ConvertToUtf32(text, offset);
                count++;
                if (codePoint > UInt16.MaxValue)
                {
                    offset++;
                }
            }
            return count;
        }

        public static bool AreStyleSequencesEquivalent(
            string expectedSequence,
            string actualSequence)
        {
            string[] expected = String.IsNullOrEmpty(expectedSequence)
                ? new string[0]
                : expectedSequence.Split('|');
            string[] actual = String.IsNullOrEmpty(actualSequence)
                ? new string[0]
                : actualSequence.Split('|');
            if (expected.Length != actual.Length)
            {
                return false;
            }
            for (int index = 0; index < expected.Length; index++)
            {
                string[] expectedParts = expected[index].Split(':');
                string[] actualParts = actual[index].Split(':');
                if (expectedParts.Length != 3 ||
                    actualParts.Length != 3 ||
                    !String.Equals(
                        expectedParts[0],
                        actualParts[0],
                        StringComparison.Ordinal) ||
                    !String.Equals(
                        expectedParts[1],
                        actualParts[1],
                        StringComparison.Ordinal))
                {
                    return false;
                }
                if (!String.Equals(
                        expectedParts[2],
                        "B",
                        StringComparison.Ordinal) &&
                    !String.Equals(
                        expectedParts[2],
                        "BI",
                        StringComparison.Ordinal) &&
                    !String.Equals(
                        expectedParts[2],
                        actualParts[2],
                        StringComparison.Ordinal))
                {
                    return false;
                }
            }
            return true;
        }

        private static int CountStyledCharacters(
            XmlElement element,
            string inheritedVariant)
        {
            string variant = element.HasAttribute("mathvariant")
                ? element.GetAttribute("mathvariant")
                : inheritedVariant;
            int count = 0;
            if (String.Equals(
                    element.LocalName,
                    "mi",
                    StringComparison.Ordinal) &&
                !String.IsNullOrWhiteSpace(variant) &&
                variant.IndexOf(
                    "bold",
                    StringComparison.OrdinalIgnoreCase) >= 0)
            {
                string text = NormalizeTokenText(element.InnerText);
                for (int offset = 0; offset < text.Length; offset++)
                {
                    int codePoint = Char.ConvertToUtf32(text, offset);
                    count++;
                    if (codePoint > UInt16.MaxValue)
                    {
                        offset++;
                    }
                }
            }

            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement != null)
                {
                    count += CountStyledCharacters(
                        childElement,
                        variant);
                }
            }
            return count;
        }

        private static string BuildMtefCharacterStyleSequence(
            XmlElement root)
        {
            List<string> codes = new List<string>();
            CollectMtefCharacterStyles(
                root,
                null,
                codes);
            return String.Join(",", codes.ToArray());
        }

        private static void CollectMtefCharacterStyles(
            XmlElement element,
            string inheritedVariant,
            IList<string> codes)
        {
            string variant = element.HasAttribute("mathvariant")
                ? element.GetAttribute("mathvariant")
                : inheritedVariant;
            if (String.Equals(
                    element.LocalName,
                    "mi",
                    StringComparison.Ordinal) &&
                !String.IsNullOrWhiteSpace(variant) &&
                variant.IndexOf(
                    "bold",
                    StringComparison.OrdinalIgnoreCase) >= 0)
            {
                string text = NormalizeTokenText(element.InnerText);
                string style =
                    variant.IndexOf(
                        "italic",
                        StringComparison.OrdinalIgnoreCase) >= 0
                    ? "BI"
                    : "B";
                for (int offset = 0; offset < text.Length; offset++)
                {
                    int codePoint = Char.ConvertToUtf32(text, offset);
                    codes.Add(
                        codePoint.ToString(
                            CultureInfo.InvariantCulture) +
                        ":" +
                        style);
                    if (codePoint > UInt16.MaxValue)
                    {
                        offset++;
                    }
                }
            }

            foreach (XmlNode child in element.ChildNodes)
            {
                XmlElement childElement = child as XmlElement;
                if (childElement != null)
                {
                    CollectMtefCharacterStyles(
                        childElement,
                        variant,
                        codes);
                }
            }
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

        private static string ComputeSha256(string value)
        {
            using (SHA256 sha = SHA256.Create())
            {
                byte[] hash = sha.ComputeHash(
                    new UTF8Encoding(false).GetBytes(value));
                StringBuilder text = new StringBuilder(hash.Length * 2);
                foreach (byte item in hash)
                {
                    text.Append(item.ToString("x2"));
                }
                return text.ToString();
            }
        }
    }
}
