"""
Auto-injection system for RLM.

Detects when user messages reference past context and automatically
retrieves relevant archived context for injection.

Features:
- Pattern-based detection (explicit references like "remember when...")
- Semantic relevance detection (similarity to archived context)
- Keyword extraction for search queries
- Hybrid search combining both methods
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any

from pinkyclawd.config.settings import get_config
from pinkyclawd.config.storage import ContextBlock
from pinkyclawd.rlm.search import get_searcher
from pinkyclawd.rlm.display import get_console

logger = logging.getLogger(__name__)


# Patterns that indicate the user is referencing past context
REFERENCE_PATTERNS = [
    # Explicit memory references
    re.compile(r"\bremember\s+(when|that|the|what|how)", re.IGNORECASE),
    re.compile(r"\brecall\s+(when|that|the|what|how)", re.IGNORECASE),
    re.compile(r"\bearlier\s+(we|you|i)\s+(said|discussed|mentioned|decided|talked|worked)", re.IGNORECASE),
    re.compile(r"\bpreviously\s+(we|you|i)\s+(said|discussed|mentioned|decided|talked|worked)", re.IGNORECASE),
    re.compile(r"\bbefore\s+(we|you|i)\s+(said|discussed|mentioned|decided|talked|worked)", re.IGNORECASE),
    re.compile(r"\bdo\s+you\s+remember", re.IGNORECASE),
    re.compile(r"\bcan\s+you\s+recall", re.IGNORECASE),
    re.compile(r"\bthink\s+back\s+to", re.IGNORECASE),

    # Questions about past discussions
    re.compile(r"\bwhat\s+(did\s+)?(we|you|i)\s+(decide|discuss|say|mention|talk)\s+about", re.IGNORECASE),
    re.compile(r"\bwhat\s+was\s+(the|that|our)\s+(decision|plan|approach|solution)", re.IGNORECASE),
    re.compile(r"\bwhat\s+happened\s+(with|to)\s+(the|that)", re.IGNORECASE),
    re.compile(r"\bwhat\s+did\s+we\s+(do|try|use|build|create|implement|fix)", re.IGNORECASE),
    re.compile(r"\bwhat\s+were\s+we\s+(doing|building|working|trying)", re.IGNORECASE),
    re.compile(r"\bwhere\s+did\s+we\s+(leave|stop|get|end)", re.IGNORECASE),
    re.compile(r"\bwhere\s+were\s+we", re.IGNORECASE),
    re.compile(r"\bhow\s+did\s+we\s+(do|solve|fix|implement|handle)", re.IGNORECASE),
    re.compile(r"\bwhy\s+did\s+we\s+(do|decide|choose|use|change)", re.IGNORECASE),
    re.compile(r"\bwhen\s+did\s+we\s+(last|start|finish|discuss)", re.IGNORECASE),

    # References to past work
    re.compile(r"\bthat\s+(bug|issue|problem|error|feature|function|file|code)\s+(we|you|i)", re.IGNORECASE),
    re.compile(r"\bthe\s+(bug|issue|problem|error|feature|function|file|code)\s+(we|you|i)\s+(fixed|discussed|worked|created|wrote)", re.IGNORECASE),
    re.compile(r"\bgo\s+back\s+to", re.IGNORECASE),
    re.compile(r"\bas\s+(we|you|i)\s+(discussed|mentioned|said|decided)", re.IGNORECASE),
    re.compile(r"\blike\s+(we|you|i)\s+(discussed|mentioned|said|decided)", re.IGNORECASE),
    re.compile(r"\bthe\s+(thing|stuff|work|code)\s+from\s+(before|earlier|yesterday|last)", re.IGNORECASE),
    re.compile(r"\bour\s+(earlier|previous|last)\s+(discussion|conversation|work|approach)", re.IGNORECASE),

    # Continuation references
    re.compile(r"\bcontinue\s+(with|from|where)", re.IGNORECASE),
    re.compile(r"\bpick\s+up\s+(where|from)", re.IGNORECASE),
    re.compile(r"\bback\s+to\s+(what|where|the)", re.IGNORECASE),
    re.compile(r"\blet's\s+(continue|resume|pick\s+up)", re.IGNORECASE),
    re.compile(r"\bcan\s+we\s+(continue|resume|go\s+back)", re.IGNORECASE),
    re.compile(r"\bresume\s+(from|where|what)", re.IGNORECASE),
    re.compile(r"\bwhere\s+we\s+left\s+off", re.IGNORECASE),
    re.compile(r"\bget\s+back\s+to", re.IGNORECASE),
    re.compile(r"\breturn\s+to\s+(the|what|where)", re.IGNORECASE),
    re.compile(r"\bcarry\s+on\s+(with|from)", re.IGNORECASE),

    # Implicit references that suggest missing context
    re.compile(r"\bthat\s+thing\s+(we|you|i)", re.IGNORECASE),
    re.compile(r"\bthe\s+same\s+(thing|way|approach)\s+(as|we)", re.IGNORECASE),
    re.compile(r"\bweren't\s+we\s+(going|supposed|planning)", re.IGNORECASE),
    re.compile(r"\bdidn't\s+(we|you|i)\s+(already|just)", re.IGNORECASE),
    re.compile(r"\byou\s+(told|showed|explained|said)\s+me", re.IGNORECASE),
    re.compile(r"\bi\s+(asked|told|showed|explained)\s+you", re.IGNORECASE),
    re.compile(r"\bwe\s+(already|just)\s+(did|discussed|covered|talked)", re.IGNORECASE),
    re.compile(r"\bwasn't\s+there\s+(a|an|some)", re.IGNORECASE),
    re.compile(r"\blike\s+last\s+time", re.IGNORECASE),
    re.compile(r"\bsame\s+as\s+(before|earlier|last)", re.IGNORECASE),
    re.compile(r"\bthe\s+(one|version|approach)\s+(we|you)\s+(used|tried|discussed)", re.IGNORECASE),
    re.compile(r"\bthat\s+approach\s+(we|you)", re.IGNORECASE),
    re.compile(r"\bthe\s+way\s+(we|you)\s+(did|handled|fixed)", re.IGNORECASE),
]


# Stop words to filter out from keyword extraction
# Expanded list matching TypeScript implementation (180+ words)
STOP_WORDS = frozenset([
    # Basic articles and prepositions
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
    "because", "until", "while", "about", "against",

    # Pronouns
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those",

    # Verb forms
    "am", "having", "doing", "going", "coming", "getting", "making",
    "taking", "using", "trying", "saying", "seeing", "wanting", "needing",
    "knowing", "thinking", "looking", "giving", "finding", "telling",
    "asking", "working", "seeming", "feeling", "leaving", "calling",

    # Contractions
    "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
    "i've", "you've", "we've", "they've", "i'd", "you'd", "he'd", "she'd",
    "we'd", "they'd", "i'll", "you'll", "he'll", "she'll", "we'll", "they'll",
    "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't",
    "doesn't", "don't", "didn't", "won't", "wouldn't", "shan't", "shouldn't",
    "can't", "cannot", "couldn't", "mustn't", "let's", "that's", "who's",
    "what's", "here's", "there's", "when's", "where's", "why's", "how's",

    # Reference words (filtered to prevent noise in search)
    "remember", "recall", "earlier", "previously", "discussed", "mentioned",
    "said", "decided", "talked", "worked", "think", "know", "like",

    # Common verbs
    "get", "got", "make", "made", "take", "took", "come", "came",
    "see", "saw", "want", "wanted", "use", "used", "find", "found",
    "give", "gave", "tell", "told", "ask", "asked", "try", "tried",
    "call", "called", "keep", "kept", "let", "put", "seem", "seemed",
    "leave", "left", "mean", "meant", "set", "run", "ran", "show", "shown",
    "hear", "heard", "play", "played", "move", "moved", "live", "lived",
    "believe", "believed", "bring", "brought", "happen", "happened",
    "write", "wrote", "provide", "provided", "sit", "sat", "stand", "stood",
    "lose", "lost", "pay", "paid", "meet", "met", "include", "included",
    "continue", "continued", "learn", "learned", "change", "changed",
    "lead", "led", "understand", "understood", "watch", "watched",

    # Question/relative words
    "whether", "whichever", "whoever", "whatever", "however", "whenever",
    "wherever", "whose",

    # Adverbs and modifiers
    "also", "even", "still", "already", "always", "never", "ever", "often",
    "sometimes", "usually", "probably", "perhaps", "maybe", "really",
    "actually", "certainly", "definitely", "possibly", "likely", "simply",
    "well", "now", "today", "yesterday", "tomorrow", "soon", "later",
    "back", "away", "around", "over", "off", "out", "up", "down",

    # Conjunctions and connectors
    "however", "therefore", "although", "though", "since", "unless",
    "whereas", "whenever", "wherever", "whether", "moreover", "furthermore",
    "nevertheless", "nonetheless", "otherwise", "hence", "thus", "yet",

    # Numbers and quantities (as words)
    "one", "two", "three", "first", "second", "third", "last", "next",
    "many", "much", "several", "enough", "both", "either", "neither",
    "another", "any", "anything", "everything", "nothing", "something",
    "anyone", "everyone", "someone", "nobody", "everybody", "somebody",
    "anywhere", "everywhere", "somewhere", "nowhere",

    # Common auxiliary phrases
    "going to", "able to", "have to", "got to", "want to", "need to",
    "used to", "ought to", "supposed to",

    # Filler words
    "please", "thanks", "okay", "ok", "yes", "yeah", "no", "nope",
    "right", "sure", "great", "good", "nice", "cool", "fine", "alright",
    "hello", "hi", "hey", "bye", "goodbye",
])


def detects_reference(message: str) -> bool:
    """
    Check if a user message references past context.

    Args:
        message: The user's message text

    Returns:
        True if the message contains patterns indicating past context reference
    """
    return any(pattern.search(message) for pattern in REFERENCE_PATTERNS)


def extract_keywords(message: str) -> list[str]:
    """
    Extract meaningful search keywords from a user message.

    Args:
        message: The user's message text

    Returns:
        List of unique keywords suitable for search
    """
    # Remove punctuation and split into words
    words = re.sub(r"[^\w\s]", " ", message.lower()).split()

    # Filter out stop words and short words
    keywords = [
        word for word in words
        if len(word) > 2 and word not in STOP_WORDS
    ]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique.append(word)

    return unique


@dataclass
class AutoInjectResult:
    """Result of auto-injection analysis."""

    should_inject: bool
    query: str
    blocks: list[ContextBlock] = field(default_factory=list)
    context_text: str = ""
    trigger: str = ""  # What triggered the injection

    @property
    def total_tokens(self) -> int:
        return sum(b.tokens for b in self.blocks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_inject": self.should_inject,
            "query": self.query,
            "blocks": [b.to_dict() for b in self.blocks],
            "total_tokens": self.total_tokens,
            "trigger": self.trigger,
        }


def format_for_injection(blocks: list[ContextBlock]) -> str:
    """
    Format context blocks for injection into the conversation.

    Args:
        blocks: Context blocks to format

    Returns:
        Formatted text for injection as a system message
    """
    if not blocks:
        return ""

    lines = [
        "<auto-retrieved-context>",
        "The following context was automatically retrieved from earlier in this conversation:",
        "",
    ]

    for i, block in enumerate(blocks, 1):
        timestamp = block.created_at.strftime("%Y-%m-%d %H:%M")

        lines.append(f"--- Archived Context {i} ({timestamp}) ---")

        if block.task_description:
            lines.append(f"Task: {block.task_description}")

        if block.summary:
            lines.append(f"Summary: {block.summary}")

        # Include content preview
        if block.content:
            preview = block.content
            if len(preview) > 2000:
                preview = preview[:2000] + "\n...[truncated]"
            lines.append("")
            lines.append("Content:")
            lines.append(preview)

        lines.append("")

    lines.append("</auto-retrieved-context>")
    return "\n".join(lines)


def analyze(
    message: str,
    session_id: str,
    limit: int = 3,
) -> AutoInjectResult:
    """
    Analyze a user message and retrieve relevant context if needed.

    Uses pattern-based detection to determine if the user is
    referencing past context, then searches archived context.

    Args:
        message: The user's message
        session_id: Current session ID
        limit: Maximum number of blocks to retrieve

    Returns:
        AutoInjectResult with injection decision and context
    """
    # Check if message references past context
    if not detects_reference(message):
        return AutoInjectResult(
            should_inject=False,
            query="",
            trigger="no_reference_detected",
        )

    logger.info(f"Detected past context reference in message: {message[:100]}...")

    # Display that we detected a reference
    console = get_console()
    console.print(
        f"[bold cyan]RLM[/bold cyan] [dim]Detected reference to past context[/dim]"
    )

    # Extract keywords for search
    keywords = extract_keywords(message)
    if not keywords:
        return AutoInjectResult(
            should_inject=False,
            query="",
            trigger="no_keywords_extracted",
        )

    # Build search query from top keywords
    query = " ".join(keywords[:5])

    # Search for relevant context
    searcher = get_searcher()
    results = searcher.search(query=query, session_id=session_id, limit=limit)

    blocks = [r.block for r in results]

    if not blocks:
        # Try getting recent blocks if search found nothing
        recent_blocks = searcher.get_recent(session_id=session_id, limit=limit)

        if not recent_blocks:
            logger.info(f"No archived context found for query: {query}")
            console.print(
                f"[bold cyan]RLM[/bold cyan] [dim]No relevant archived context found[/dim]"
            )
            return AutoInjectResult(
                should_inject=False,
                query=query,
                trigger="no_context_found",
            )

        logger.info(f"Using {len(recent_blocks)} recent archived blocks")
        blocks = recent_blocks
        trigger = "recent_blocks"
    else:
        trigger = "keyword_search"

    logger.info(f"Found {len(blocks)} relevant context blocks for injection")

    # Display what we found
    console.print(
        f"[bold cyan]RLM[/bold cyan] [green]Auto-injecting {len(blocks)} archived context blocks[/green]"
    )

    return AutoInjectResult(
        should_inject=True,
        query=query,
        blocks=blocks,
        context_text=format_for_injection(blocks),
        trigger=trigger,
    )


def analyze_with_threshold(
    message: str,
    session_id: str,
    limit: int = 3,
    similarity_threshold: float = 0.4,
) -> AutoInjectResult:
    """
    Enhanced analysis that considers both pattern matching and search relevance.

    Args:
        message: The user's message
        session_id: Current session ID
        limit: Maximum blocks to retrieve
        similarity_threshold: Minimum score for search results

    Returns:
        AutoInjectResult with injection decision and context
    """
    config = get_config()

    # Check if auto-retrieve is enabled
    if not config.rlm.enabled or not config.rlm.auto_retrieve:
        return AutoInjectResult(
            should_inject=False,
            query="",
            trigger="auto_retrieve_disabled",
        )

    # First, check for explicit pattern references
    has_explicit_reference = detects_reference(message)

    if not has_explicit_reference:
        # If no explicit reference, check semantic similarity
        # This allows proactive injection when query is highly relevant
        searcher = get_searcher()
        keywords = extract_keywords(message)

        if not keywords:
            return AutoInjectResult(
                should_inject=False,
                query="",
                trigger="no_keywords",
            )

        query = " ".join(keywords[:5])
        results = searcher.search(query=query, session_id=None, limit=limit)

        # Only inject if we have high-relevance results
        threshold = config.rlm.semantic_search.get("proactive_threshold", 0.65)
        high_relevance = [r for r in results if r.score >= threshold]

        if not high_relevance:
            return AutoInjectResult(
                should_inject=False,
                query=query,
                trigger="below_threshold",
            )

        blocks = [r.block for r in high_relevance[:limit]]

        logger.info(f"Proactive injection: {len(blocks)} blocks above threshold {threshold}")

        console = get_console()
        console.print(
            f"[bold cyan]RLM[/bold cyan] [green]Proactive context injection: "
            f"{len(blocks)} relevant blocks found[/green]"
        )

        return AutoInjectResult(
            should_inject=True,
            query=query,
            blocks=blocks,
            context_text=format_for_injection(blocks),
            trigger="proactive_semantic",
        )

    # Has explicit reference - use standard analysis
    return analyze(message, session_id, limit)


# Convenience function
def should_auto_inject(message: str) -> bool:
    """Quick check if a message should trigger auto-injection."""
    return detects_reference(message)
