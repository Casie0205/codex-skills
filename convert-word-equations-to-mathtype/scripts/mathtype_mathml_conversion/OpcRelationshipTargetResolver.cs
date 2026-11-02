using System;
using System.Collections.Generic;

namespace ThesisMathTypeConversionV2
{
    public static class OpcRelationshipTargetResolver
    {
        public const string OleObjectRelationshipType =
            "http://schemas.openxmlformats.org/officeDocument/2006/" +
            "relationships/oleObject";

        public static string ResolveOleObjectPart(
            string sourcePartName,
            string target,
            string targetMode,
            string relationshipType)
        {
            if (!string.IsNullOrWhiteSpace(targetMode) &&
                !string.Equals(
                    targetMode,
                    "Internal",
                    StringComparison.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "External OPC relationships are not auditable.",
                    "targetMode");
            }
            if (!string.Equals(
                relationshipType,
                OleObjectRelationshipType,
                StringComparison.Ordinal))
            {
                throw new ArgumentException(
                    "The relationship is not an OLE object relationship.",
                    "relationshipType");
            }
            if (string.IsNullOrWhiteSpace(sourcePartName))
            {
                throw new ArgumentException(
                    "The source part name is required.",
                    "sourcePartName");
            }
            if (string.IsNullOrWhiteSpace(target))
            {
                throw new ArgumentException(
                    "The relationship target is required.",
                    "target");
            }

            string normalizedTarget = target.Replace('\\', '/');
            if (normalizedTarget.IndexOf('?') >= 0 ||
                normalizedTarget.IndexOf('#') >= 0)
            {
                throw new ArgumentException(
                    "OPC part targets cannot contain a query or fragment.",
                    "target");
            }
            Uri absoluteTarget;
            if (Uri.TryCreate(
                normalizedTarget,
                UriKind.Absolute,
                out absoluteTarget))
            {
                throw new ArgumentException(
                    "Absolute external URIs are not internal OPC parts.",
                    "target");
            }

            List<string> segments = new List<string>();
            if (!normalizedTarget.StartsWith(
                "/",
                StringComparison.Ordinal))
            {
                string normalizedSource =
                    sourcePartName.Replace('\\', '/').TrimStart('/');
                string[] sourceSegments =
                    normalizedSource.Split(
                        new[] { '/' },
                        StringSplitOptions.RemoveEmptyEntries);
                for (int index = 0;
                    index < sourceSegments.Length - 1;
                    index++)
                {
                    segments.Add(DecodeSegment(sourceSegments[index]));
                }
            }

            string[] targetSegments =
                normalizedTarget.Split(
                    new[] { '/' },
                    StringSplitOptions.None);
            foreach (string rawSegment in targetSegments)
            {
                if (rawSegment.Length == 0 || rawSegment == ".")
                {
                    continue;
                }
                string segment = DecodeSegment(rawSegment);
                if (segment == ".")
                {
                    continue;
                }
                if (segment == "..")
                {
                    if (segments.Count == 0)
                    {
                        throw new ArgumentException(
                            "The OPC target traverses above package root.",
                            "target");
                    }
                    segments.RemoveAt(segments.Count - 1);
                    continue;
                }
                segments.Add(segment);
            }

            if (segments.Count == 0)
            {
                throw new ArgumentException(
                    "The OPC target does not identify a package part.",
                    "target");
            }
            return string.Join("/", segments.ToArray());
        }

        private static string DecodeSegment(string value)
        {
            string decoded = Uri.UnescapeDataString(value);
            if (decoded.Length == 0 ||
                decoded.IndexOf('/') >= 0 ||
                decoded.IndexOf('\\') >= 0 ||
                decoded.IndexOf(':') >= 0 ||
                decoded.IndexOf('\0') >= 0)
            {
                throw new ArgumentException(
                    "The OPC target contains an invalid path segment.");
            }
            return decoded;
        }
    }
}
