"""
Query Analyzer - Analyzes query complexity and intent

This component analyzes incoming queries to determine:
- Complexity level (simple, moderate, complex)
- Intent type (factual, comparison, calculation, summarization, external)
- Entities mentioned
- Whether multiple tools are needed
"""

import logging
import re
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes queries to determine complexity, intent, and tool requirements"""

    def __init__(self, llm_handler=None):
        """
        Initialize query analyzer

        Args:
            llm_handler: Optional LLM handler for semantic intent classification
        """
        self.logger = logging.getLogger(f"{__name__}.QueryAnalyzer")
        self.llm_handler = llm_handler

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query comprehensively

        Args:
            query: User query string

        Returns:
            Dictionary containing:
                - complexity: 'simple' | 'moderate' | 'complex'
                - intent: 'factual' | 'comparison' | 'calculation' | 'summarization' | 'external'
                - entities: List of extracted entities
                - requires_multiple_tools: bool
                - keywords: Dict of detected keywords by category
        """
        self.logger.info(f"Analyzing query: {query[:50]}...")

        # Determine complexity
        complexity = self._assess_complexity(query)

        # Determine intent
        intent = self._classify_intent(query)

        # Extract entities
        entities = self._extract_entities(query)

        # Check if multiple tools are needed
        requires_multiple = self._requires_multiple_tools(query, complexity, intent)

        result = {
            'complexity': complexity,
            'intent': intent,
            'entities': entities,
            'requires_multiple_tools': requires_multiple,
            'keywords': self._extract_keywords(query),
            'query_length': len(query),
            'word_count': len(query.split())
        }

        self.logger.info(f"Analysis: complexity={complexity}, intent={intent}, multiple_tools={requires_multiple}")

        return result

    def _assess_complexity(self, query: str) -> str:
        """
        Assess query complexity

        Args:
            query: User query

        Returns:
            'simple', 'moderate', or 'complex'
        """
        # Count various complexity indicators
        word_count = len(query.split())
        sentence_count = len(re.split(r'[.!?]+', query.strip()))
        question_marks = query.count('?')
        and_or_count = len(re.findall(r'\b(and|or)\b', query, re.IGNORECASE))
        comma_count = query.count(',')

        # Multi-step indicators
        multi_step_keywords = ['then', 'after', 'first', 'next', 'finally', 'also']
        has_multi_step = any(kw in query.lower() for kw in multi_step_keywords)

        # Calculate complexity score
        score = 0

        # Word count
        if word_count > 20:
            score += 2
        elif word_count > 10:
            score += 1

        # Multiple sentences
        if sentence_count > 2:
            score += 2
        elif sentence_count > 1:
            score += 1

        # Multiple questions
        if question_marks > 1:
            score += 2

        # Conjunctions
        if and_or_count > 2:
            score += 2
        elif and_or_count > 0:
            score += 1

        # Commas (complex sentence structure)
        if comma_count > 2:
            score += 1

        # Multi-step indicators
        if has_multi_step:
            score += 3

        # Classify based on score
        if score >= 5:
            return 'complex'
        elif score >= 2:
            return 'moderate'
        else:
            return 'simple'

    def _classify_intent(self, query: str) -> str:
        """
        Classify query intent using LLM (with rule-based fallback)

        Args:
            query: User query

        Returns:
            'factual', 'comparison', 'calculation', 'summarization', or 'external'
        """
        # Try LLM-based classification first
        if self.llm_handler:
            try:
                llm_intent = self._llm_classify_intent(query)
                if llm_intent:
                    return llm_intent
            except Exception as e:
                self.logger.warning(f"LLM classification failed: {e}, falling back to rules")

        # Fallback to rule-based classification
        return self._rule_based_classify_intent(query)

    def _llm_classify_intent(self, query: str) -> str:
        """
        Use LLM to classify query intent

        Args:
            query: User query

        Returns:
            Intent classification or None if failed
        """
        prompt = f"""Classify this query's intent. Choose EXACTLY ONE option:

- conversational: Greetings (hi, hello, hey), gratitude (thanks, thank you), acknowledgments (ok, got it, sure), farewells (bye, goodbye), or simple pleasantries
- factual: Questions about uploaded documents, files, PDFs, or content that the user has provided. Includes queries with "the document", "the file", "this document", "uploaded", or asking about specific documents/policies/reports.
- external: General knowledge, current events, real-time data, famous people, geography, history, scientific facts, definitions, or information from the internet/Wikipedia that is NOT in user's uploaded documents.
- comparison: Comparing two or more things (only if explicitly asking to compare)
- summarization: Asking for a summary or overview (only if explicitly asking to summarize)
- calculation: Math operations or numerical calculations

PRIORITY RULES:
1. Single words like "hi", "hello", "thanks", "ok", "bye" → ALWAYS conversational
2. Short greetings (2-3 words) without questions → conversational
3. If query asks about "the document", "the file", "uploaded" → factual (NOT external)
4. If query asks about general concepts, famous people, current events → external
5. When unsure between factual/external → choose factual (try internal documents first)

Examples:
- "hi" → conversational
- "hello" → conversational
- "thanks" → conversational
- "thank you" → conversational
- "ok" → conversational
- "ok got it" → conversational
- "bye" → conversational
- "What is our remote work policy?" → factual (internal document)
- "What is the document about?" → factual (asking about uploaded document)
- "What are the documents about?" → factual (asking about uploaded documents)
- "Summarize the uploaded file" → summarization (uploaded document)
- "What is port in rebate offer?" → factual (could be in uploaded document)
- "What is the capital of France?" → external (general knowledge, geography)
- "Who is the current Prime Minister of Malaysia?" → external (current events, political figure)
- "What is machine learning?" → external (general knowledge, definition)
- "Compare Policy A and Policy B" → comparison
- "Calculate 15% of the budget" → calculation

Query: "{query}"

Respond with ONLY ONE WORD (conversational/factual/external/comparison/summarization/calculation):"""

        response = self.llm_handler.generate(
            prompt,
            temperature=0.1,  # Low temperature for deterministic results
            max_tokens=10
        )

        # Parse response - extract the last word (more robust parsing)
        valid_intents = ['conversational', 'factual', 'external', 'comparison', 'summarization', 'calculation']

        # Try to find the intent in the response
        response_lower = response.strip().lower()

        # Method 1: Check if response is just the intent word
        if response_lower in valid_intents:
            self.logger.info(f"LLM classified intent: {response_lower}")
            return response_lower

        # Method 2: Extract last line and check
        lines = response_lower.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line in valid_intents:
                self.logger.info(f"LLM classified intent: {line}")
                return line

        # Method 3: Search for any valid intent in the response
        for intent in valid_intents:
            if intent in response_lower:
                self.logger.info(f"LLM classified intent (found in text): {intent}")
                return intent

        # Failed to parse
        self.logger.warning(f"LLM returned invalid intent: {response[:100]}")
        return None

    def _rule_based_classify_intent(self, query: str) -> str:
        """
        Rule-based intent classification (fallback)

        Args:
            query: User query

        Returns:
            Intent classification
        """
        query_lower = query.lower().strip()
        words = query_lower.split()

        # Conversational intent (greetings, acknowledgments, farewells)
        conversational_patterns = [
            'hi', 'hello', 'hey', 'thanks', 'thank you', 'bye', 'goodbye',
            'ok', 'okay', 'got it', 'understood', 'sure', 'great', 'good',
            'cool', 'nice', 'awesome', 'perfect'
        ]

        # Single word conversational
        if len(words) == 1 and words[0] in conversational_patterns:
            return 'conversational'

        # Short greetings without question marks (2-3 words)
        if len(words) <= 3 and '?' not in query:
            if any(word in conversational_patterns for word in words):
                return 'conversational'

        # Comparison intent
        comparison_keywords = [
            'compare', 'versus', ' vs ', ' vs.', 'difference', 'contrast',
            'similarities', 'differ'
        ]
        if any(kw in query_lower for kw in comparison_keywords):
            return 'comparison'

        # Summarization intent (check before calculation to avoid "sum" confusion)
        summarization_keywords = [
            'summarize', 'summary', 'overview', 'key points', 'main points',
            'highlights', 'brief'
        ]
        if any(kw in query_lower for kw in summarization_keywords):
            return 'summarization'

        # Calculation intent
        calculation_keywords = ['calculate', 'compute', ' sum ', 'total', 'average', '%', 'percentage']
        has_numbers = bool(re.search(r'\d+', query))
        if any(kw in query_lower for kw in calculation_keywords) or (has_numbers and any(op in query for op in ['+', '-', '*', '/'])):
            return 'calculation'

        # External intent (current events, external facts)
        external_keywords = [
            'current', 'latest', 'recent', 'today', 'now', 'news',
            'weather', 'stock price', 'exchange rate'
        ]
        if any(kw in query_lower for kw in external_keywords):
            return 'external'

        # Default to factual
        return 'factual'

    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract named entities from query

        Args:
            query: User query

        Returns:
            List of entity strings
        """
        entities = []

        # Pattern 1: Capitalized words (likely proper nouns)
        # Skip first word if it starts with capital (could be sentence start)
        words = query.split()
        for i, word in enumerate(words):
            # Skip common words that are often capitalized
            if word in ['I', 'A', 'The', 'In', 'On', 'At']:
                continue

            # Check if word is capitalized and not at sentence start
            if i > 0 and word[0].isupper() and len(word) > 1:
                entities.append(word)

        # Pattern 2: Quoted text
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)

        # Pattern 3: Common entity patterns
        # Dates
        dates = re.findall(r'\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', query)
        entities.extend(dates)

        # Pattern 4: Multi-word proper nouns (consecutive capitals)
        multi_word_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        multi_word_entities = re.findall(multi_word_pattern, query)
        entities.extend(multi_word_entities)

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.lower() not in seen:
                seen.add(entity.lower())
                unique_entities.append(entity)

        return unique_entities

    def _requires_multiple_tools(self, query: str, complexity: str, intent: str) -> bool:
        """
        Determine if query requires multiple tools

        Args:
            query: User query
            complexity: Query complexity
            intent: Query intent

        Returns:
            True if multiple tools are likely needed
        """
        # Complex queries often need multiple tools
        if complexity == 'complex':
            return True

        # Multi-step keywords
        multi_step_keywords = ['then', 'after that', 'also', 'and then', 'followed by']
        if any(kw in query.lower() for kw in multi_step_keywords):
            return True

        # Multiple questions
        question_marks = query.count('?')
        if question_marks > 1:
            return True

        # Multiple intents (e.g., "compare and summarize")
        intent_keywords = {
            'comparison': ['compare', 'difference'],
            'calculation': ['calculate', 'compute'],
            'summarization': ['summarize', 'overview'],
            'factual': ['what', 'how', 'why']
        }

        matched_intents = 0
        query_lower = query.lower()
        for intent_type, keywords in intent_keywords.items():
            if any(kw in query_lower for kw in keywords):
                matched_intents += 1

        if matched_intents >= 2:
            return True

        # Moderate complexity with certain intents might need multiple tools
        if complexity == 'moderate' and intent in ['comparison', 'calculation']:
            return True

        return False

    def _extract_keywords(self, query: str) -> Dict[str, List[str]]:
        """
        Extract keywords by category

        Args:
            query: User query

        Returns:
            Dictionary mapping categories to keyword lists
        """
        query_lower = query.lower()

        keywords = {
            'comparison': [],
            'calculation': [],
            'summarization': [],
            'external': [],
            'temporal': [],
            'quantitative': []
        }

        # Comparison keywords
        comp_keywords = ['compare', 'versus', 'vs', 'difference', 'contrast', 'similar']
        keywords['comparison'] = [kw for kw in comp_keywords if kw in query_lower]

        # Calculation keywords
        calc_keywords = ['calculate', 'compute', 'sum', 'total', 'average', 'percentage']
        keywords['calculation'] = [kw for kw in calc_keywords if kw in query_lower]

        # Summarization keywords
        summ_keywords = ['summarize', 'summary', 'overview', 'key points', 'highlights']
        keywords['summarization'] = [kw for kw in summ_keywords if kw in query_lower]

        # External keywords
        ext_keywords = ['current', 'latest', 'recent', 'today', 'now', 'news']
        keywords['external'] = [kw for kw in ext_keywords if kw in query_lower]

        # Temporal keywords
        temp_keywords = ['when', 'date', 'time', 'year', 'month', 'day', 'yesterday', 'tomorrow']
        keywords['temporal'] = [kw for kw in temp_keywords if kw in query_lower]

        # Quantitative keywords
        quant_keywords = ['how many', 'how much', 'count', 'number', 'amount', 'quantity']
        keywords['quantitative'] = [kw for kw in quant_keywords if kw in query_lower]

        return keywords
