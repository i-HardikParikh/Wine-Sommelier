from enum import Enum


class QueryType(str, Enum):
    WINE_PAIRING = "wine_pairing"
    WINE_RECOMMENDATION = "wine_recommendation"
    WINE_EDUCATION = "wine_education"
    CELLAR_MANAGEMENT = "cellar_management"
    GENERAL = "general"


class DocumentType(str, Enum):
    PDF = "pdf"
    PPTX = "pptx"
    IMAGE = "image"


class NodeType(str, Enum):
    ANALYZE_QUERY = "analyze_query"
    VECTOR_SEARCH = "vector_search"
    VISION_ANALYSIS = "vision_analysis"
    OCR_ANALYSIS = "ocr_analysis"
    ANSWER_SYNTHESIS = "answer_synthesis"
    FALLBACK = "fallback"


class EvalMetric(str, Enum):
    RELEVANCE = "relevance"
    FAITHFULNESS = "faithfulness"
    COMPLETENESS = "completeness"
    SOMMELIER_TONE = "sommelier_tone"
