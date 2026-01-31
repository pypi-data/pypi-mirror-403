"""Type definitions and enums for MemoryLayer.ai SDK."""

from enum import Enum


class MemoryType(str, Enum):
    """Cognitive memory types - how memory is structured."""

    EPISODIC = "episodic"  # Specific events/interactions
    SEMANTIC = "semantic"  # Facts, concepts, relationships
    PROCEDURAL = "procedural"  # How to do things
    WORKING = "working"  # Current task context


class MemorySubtype(str, Enum):
    """Domain subtypes - what the memory is about."""

    SOLUTION = "Solution"  # Working fixes to problems
    PROBLEM = "Problem"  # Issues encountered
    CODE_PATTERN = "CodePattern"  # Reusable patterns
    FIX = "Fix"  # Bug fixes with context
    ERROR = "Error"  # Error patterns and resolutions
    WORKFLOW = "Workflow"  # Process knowledge
    PREFERENCE = "Preference"  # User/project preferences
    DECISION = "Decision"  # Architectural decisions


class RecallMode(str, Enum):
    """Retrieval strategy for recall queries."""

    RAG = "rag"  # Fast vector similarity search
    LLM = "llm"  # Deep semantic LLM-powered retrieval
    HYBRID = "hybrid"  # Combine both strategies


class SearchTolerance(str, Enum):
    """Search precision level."""

    LOOSE = "loose"  # Fuzzy matching, broader results
    MODERATE = "moderate"  # Balanced precision/recall (default)
    STRICT = "strict"  # Exact matching, high relevance


class RelationshipCategory(str, Enum):
    """High-level relationship categories."""

    CAUSAL = "causal"  # Cause-effect relationships
    SOLUTION = "solution"  # Problem-solution relationships
    CONTEXT = "context"  # Contextual relationships
    LEARNING = "learning"  # Knowledge evolution
    SIMILARITY = "similarity"  # Semantic similarity
    WORKFLOW = "workflow"  # Process dependencies
    QUALITY = "quality"  # Quality assessments


class RelationshipType(str, Enum):
    """Specific relationship types between memories."""

    # Causal
    CAUSES = "CAUSES"
    TRIGGERS = "TRIGGERS"
    LEADS_TO = "LEADS_TO"
    PREVENTS = "PREVENTS"

    # Solution
    SOLVES = "SOLVES"
    ADDRESSES = "ADDRESSES"
    ALTERNATIVE_TO = "ALTERNATIVE_TO"
    IMPROVES = "IMPROVES"

    # Context
    OCCURS_IN = "OCCURS_IN"
    APPLIES_TO = "APPLIES_TO"
    WORKS_WITH = "WORKS_WITH"
    REQUIRES = "REQUIRES"

    # Learning
    BUILDS_ON = "BUILDS_ON"
    CONTRADICTS = "CONTRADICTS"
    CONFIRMS = "CONFIRMS"
    SUPERSEDES = "SUPERSEDES"

    # Similarity
    SIMILAR_TO = "SIMILAR_TO"
    VARIANT_OF = "VARIANT_OF"
    RELATED_TO = "RELATED_TO"

    # Workflow
    FOLLOWS = "FOLLOWS"
    DEPENDS_ON = "DEPENDS_ON"
    ENABLES = "ENABLES"
    BLOCKS = "BLOCKS"

    # Quality
    EFFECTIVE_FOR = "EFFECTIVE_FOR"
    PREFERRED_OVER = "PREFERRED_OVER"
    DEPRECATED_BY = "DEPRECATED_BY"
