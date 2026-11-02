using System;
using System.Collections.Generic;

namespace ThesisMathTypeConversionV2
{
    public enum V2ConversionPolicy
    {
        ReviewQueue,
        Strict
    }

    public sealed class MathMlSnapshot
    {
        public int SourceIndex { get; set; }
        public string RawMathMl { get; set; }
        public string NormalizedMathMl { get; set; }
        public string CanonicalMathMl { get; set; }
        public string CanonicalSha256 { get; set; }
        public string TokenSequence { get; set; }
        public string StructureSignature { get; set; }
        public string StyleSequence { get; set; }
        public IList<string> Features { get; set; }
        public int ExpectedStyledCharacterCount { get; set; }
        public string ExpectedMtefCharacterStyleSequence { get; set; }
        public int AccentScriptRiskCount { get; set; }
    }

    public sealed class MathMlRoundTripResult
    {
        public string ReadbackMathMl { get; set; }
        public string CanonicalMathMl { get; set; }
        public string CanonicalSha256 { get; set; }
        public string TokenSequence { get; set; }
        public string StructureSignature { get; set; }
        public string StyleSequence { get; set; }
        public bool CanonicalEqual { get; set; }
        public bool TokenSequenceEqual { get; set; }
        public bool StructureSignatureEqual { get; set; }
        public int ExpectedStyledCharacterCount { get; set; }
        public int ReadbackStyledCharacterCount { get; set; }
        public bool ReadbackStyleCountEqual { get; set; }
        public bool StyleSequenceEqual { get; set; }
        public string MtefCharacterStyleSequence { get; set; }
        public bool MtefStyleEqual { get; set; }
        public bool MtefHasTimesNewRoman { get; set; }
        public bool MtefHasEuclidExtra { get; set; }
        public bool MtefHasLegacyMtExtra { get; set; }
        public bool MtefRequiredStylesUseTimesNewRoman { get; set; }
        public bool MtefMathExtraUsesEuclidExtra { get; set; }
        public bool MtefFontProfileAccepted { get; set; }
        public IList<string> ReviewIssueCodes { get; set; }
        public bool ReviewRequired { get; set; }
        public bool Accepted { get; set; }
    }

    public sealed class V2ConversionSummary
    {
        public string Mode { get; set; }
        public string ConversionPolicy { get; set; }
        public string SourcePath { get; set; }
        public string OutputPath { get; set; }
        public string SourceSha256 { get; set; }
        public int SourceOmmlCount { get; set; }
        public int ConvertedCount { get; set; }
        public int RemainingOmmlCount { get; set; }
        public int MathTypeInlineCount { get; set; }
        public int CanonicalMatchCount { get; set; }
        public int StructuralMatchCount { get; set; }
        public int TokenMatchCount { get; set; }
        public int MathMlStyleMatchCount { get; set; }
        public int MtefStyleMatchCount { get; set; }
        public int MtefFontProfileMatchCount { get; set; }
        public int AccentScriptRiskCount { get; set; }
        public int AccentScriptCorrectionCount { get; set; }
        public int CleanConversionCount { get; set; }
        public int ReviewRequiredCount { get; set; }
        public int FatalErrorCount { get; set; }
        public int PageCount { get; set; }
        public int RevisionCount { get; set; }
        public bool TrackRevisions { get; set; }
        public string ManifestPath { get; set; }
        public string ProgressPath { get; set; }
    }
}
