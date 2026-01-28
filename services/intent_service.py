"""
Intent Detection Service - NLU for automatically detecting user intent
"""
import re
from typing import Dict, List, Optional
from models.schemas import Intent, ChatMode
from config import Config


class IntentService:
    def __init__(self):
        self.confidence_threshold = Config.INTENT_CONFIDENCE_THRESHOLD

        # Intent patterns and keywords
        self.patterns = {
            Intent.AEM_COMPLIANCE: {
                'keywords': [
                    'compliance', 'check', 'audit', 'validate', 'accessibility',
                    'seo', 'performance', 'security', 'analyze page', 'scan',
                    'wcag', 'a11y', 'best practices', 'standards'
                ],
                'phrases': [
                    'check.*compliance', 'run.*audit', 'analyze.*page',
                    'compliance.*check', 'audit.*page', 'scan.*page',
                    'validate.*page', 'check.*accessibility', 'seo.*audit'
                ],
                'aem_keywords': [
                    'aem', 'content', 'page', 'component', 'template'
                ]
            },
            Intent.AEM_QUERY: {
                'keywords': [
                    'find', 'list', 'show', 'get', 'search', 'query',
                    'pages under', 'content under', 'browse', 'display'
                ],
                'phrases': [
                    'find.*pages', 'list.*pages', 'show.*pages',
                    'get.*pages', 'pages under', 'content under',
                    'search.*content', 'browse.*content'
                ],
                'aem_keywords': [
                    'aem', 'content', 'page', 'site', '/content'
                ]
            },
            Intent.FILE_UPLOAD: {
                'keywords': [
                    'upload', 'file', 'document', 'pdf', 'analyze document',
                    'read file', 'parse', 'extract', 'document analysis'
                ],
                'phrases': [
                    'analyze.*document', 'read.*file', 'upload.*file',
                    'parse.*document', 'extract.*from', 'review.*document'
                ]
            },
            Intent.WEB_SEARCH: {
                'keywords': [
                    'search web', 'google', 'find online', 'look up',
                    'search for', 'web search', 'internet', 'online'
                ],
                'phrases': [
                    'search.*web', 'search.*online', 'find.*online',
                    'look.*up', 'search.*internet', 'google.*for'
                ]
            }
        }

    def detect_intent(
            self,
            text: str,
            context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Detect user intent from input text

        Args:
            text: User input text
            context: Previous conversation context

        Returns:
            Dictionary with intent, confidence, and metadata
        """
        text_lower = text.lower().strip()

        # Calculate confidence scores for each intent
        scores = {}

        for intent, patterns in self.patterns.items():
            score = self._calculate_intent_score(text_lower, patterns)
            scores[intent] = score

        # Get highest scoring intent
        if scores:
            max_intent = max(scores, key=scores.get)
            max_confidence = scores[max_intent]

            # If confidence is above threshold, use that intent
            if max_confidence >= self.confidence_threshold:
                result = {
                    'intent': max_intent,
                    'confidence': max_confidence,
                    'suggested_mode': self._intent_to_mode(max_intent),
                    'extracted_entities': self._extract_entities(text, max_intent)
                }
                return result

        # Default to chat intent
        return {
            'intent': Intent.CHAT,
            'confidence': 0.5,
            'suggested_mode': ChatMode.CHAT,
            'extracted_entities': {}
        }

    def _calculate_intent_score(self, text: str, patterns: Dict) -> float:
        """
        Calculate confidence score for an intent

        Args:
            text: Input text
            patterns: Pattern dictionary for intent

        Returns:
            Confidence score (0-1)
        """
        score = 0.0
        weights = {
            'keywords': 0.3,
            'phrases': 0.4,
            'aem_keywords': 0.3
        }

        # Check keyword matches
        keywords = patterns.get('keywords', [])
        if keywords:
            keyword_matches = sum(1 for kw in keywords if kw in text)
            keyword_score = min(keyword_matches / max(len(keywords) * 0.3, 1), 1.0)
            score += keyword_score * weights['keywords']

        # Check phrase patterns
        phrases = patterns.get('phrases', [])
        if phrases:
            phrase_matches = sum(1 for phrase in phrases if re.search(phrase, text))
            phrase_score = min(phrase_matches / max(len(phrases) * 0.5, 1), 1.0)
            score += phrase_score * weights['phrases']

        # Check AEM-specific keywords (for AEM intents)
        aem_keywords = patterns.get('aem_keywords', [])
        if aem_keywords:
            aem_matches = sum(1 for kw in aem_keywords if kw in text)
            aem_score = min(aem_matches / max(len(aem_keywords) * 0.5, 1), 1.0)
            score += aem_score * weights['aem_keywords']

        return min(score, 1.0)

    def _intent_to_mode(self, intent: Intent) -> ChatMode:
        """
        Map intent to chat mode

        Args:
            intent: Detected intent

        Returns:
            Corresponding chat mode
        """
        mapping = {
            Intent.CHAT: ChatMode.CHAT,
            Intent.FILE_UPLOAD: ChatMode.FILE,
            Intent.WEB_SEARCH: ChatMode.WEB,
            Intent.AEM_QUERY: ChatMode.AEM,
            Intent.AEM_COMPLIANCE: ChatMode.AEM,
            Intent.UNKNOWN: ChatMode.CHAT
        }
        return mapping.get(intent, ChatMode.CHAT)

    def _extract_entities(self, text: str, intent: Intent) -> Dict:
        """
        Extract relevant entities based on intent

        Args:
            text: Input text
            intent: Detected intent

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        if intent in [Intent.AEM_QUERY, Intent.AEM_COMPLIANCE]:
            # Extract AEM path
            path_match = re.search(r'/content[/\w-]*', text)
            if path_match:
                entities['path'] = path_match.group(0)

            # Extract action type for compliance
            if intent == Intent.AEM_COMPLIANCE:
                if 'accessibility' in text.lower() or 'a11y' in text.lower():
                    entities['categories'] = ['accessibility']
                elif 'seo' in text.lower():
                    entities['categories'] = ['seo']
                elif 'performance' in text.lower():
                    entities['categories'] = ['performance']
                elif 'security' in text.lower():
                    entities['categories'] = ['security']

        elif intent == Intent.WEB_SEARCH:
            # Extract search query (remove common prefixes)
            query = text
            prefixes = ['search for', 'search', 'find', 'look up', 'google']
            for prefix in prefixes:
                query = re.sub(f'^{prefix}\\s+', '', query, flags=re.IGNORECASE)
            entities['query'] = query.strip()

        elif intent == Intent.FILE_UPLOAD:
            # Extract file-related questions
            question_match = re.search(r'(what|how|explain|summarize|analyze).*', text, re.IGNORECASE)
            if question_match:
                entities['question'] = question_match.group(0)

        return entities

    def should_switch_mode(
            self,
            current_mode: ChatMode,
            detected_intent: Intent,
            confidence: float
    ) -> bool:
        """
        Determine if mode should be automatically switched

        Args:
            current_mode: Current chat mode
            detected_intent: Detected intent
            confidence: Confidence score

        Returns:
            True if mode should switch
        """
        # Only switch if confidence is high
        if confidence < 0.7:
            return False

        suggested_mode = self._intent_to_mode(detected_intent)

        # Don't switch if already in the right mode
        if current_mode == suggested_mode:
            return False

        # Switch for AEM intents
        if detected_intent in [Intent.AEM_QUERY, Intent.AEM_COMPLIANCE]:
            return True

        # Switch for file/web if explicitly mentioned
        if detected_intent in [Intent.FILE_UPLOAD, Intent.WEB_SEARCH]:
            return True

        return False

    def get_mode_suggestion_message(self, suggested_mode: ChatMode) -> str:
        """
        Generate helpful message for mode switch suggestion

        Args:
            suggested_mode: Suggested mode

        Returns:
            User-friendly message
        """
        messages = {
            ChatMode.AEM: "It looks like you want to work with AEM. I've switched to AEM mode for you.",
            ChatMode.FILE: "It seems you want to analyze a file. Please upload your file to continue.",
            ChatMode.WEB: "I'll search the web for that information.",
            ChatMode.CHAT: "Let's continue our conversation."
        }
        return messages.get(suggested_mode, "")