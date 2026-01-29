"""SmartPageFinderPlugin - ML плагін для автоматичного пошуку потрібних сторінок.

Використовує g4f (GPT4Free) для інтелектуального аналізу контенту сторінок.
Плагін приймає промпт з описом того, що шукаємо, і автоматично:
1. Аналізує контент кожної сторінки
2. Визначає релевантність сторінки (is_target_page)
3. Виставляє пріоритети для посилань (child_priorities)
4. Може дозволяти/блокувати конкретні URL (explicit_scan_decisions)

Приклади використання:
    >>> from graph_crawler.extensions.plugins.node.smart_page_finder import SmartPageFinderPlugin
    >>>
    >>> # Пошук автомобілів певної марки
    >>> plugin = SmartPageFinderPlugin(
    ...     search_prompt="Шукаю сторінки з автомобілями BMW X5 2024 року",
    ...     config={'min_relevance_score': 0.7}
    ... )
    >>>
    >>> # Пошук статей на тему
    >>> plugin = SmartPageFinderPlugin(
    ...     search_prompt="Статті про машинне навчання та нейронні мережі",
    ... )
    >>>
    >>> # Пошук контенту 18+
    >>> plugin = SmartPageFinderPlugin(
    ...     search_prompt="Сторінки з контентом для дорослих (18+)",
    ...     config={'strict_mode': True}
    ... )
    >>>
    >>> # Використання з GraphCrawler
    >>> graph = gc.crawl(
    ...     "https://example.com",
    ...     plugins=[plugin],
    ...     node_class=SmartFinderNode  # Опціонально
    ... )
    >>>
    >>> # Отримання знайдених сторінок
    >>> target_pages = [n for n in graph if n.user_data.get('is_target_page')]
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from pydantic import Field

from graph_crawler.extensions.plugins.node.base import (
    BaseNodePlugin,
    NodePluginContext,
    NodePluginType,
)

logger = logging.getLogger(__name__)


class RelevanceLevel(str, Enum):
    """Рівні релевантності сторінки."""
    HIGH = "high"           # 0.8-1.0 - точно те, що шукаємо
    MEDIUM = "medium"       # 0.5-0.8 - можливо релевантна
    LOW = "low"             # 0.2-0.5 - малоймовірно
    IRRELEVANT = "irrelevant"  # 0.0-0.2 - точно не те


class SmartPageFinderPlugin(BaseNodePlugin):
    """
    ML плагін для автоматичного пошуку потрібних сторінок на основі g4f.
    
    Працює на етапі ON_AFTER_SCAN - після сканування HTML.
    Аналізує контент сторінки та визначає чи це те, що шукаємо.
    
    Параметри конфігурації:
        enabled (bool): Чи увімкнено плагін (за замовчуванням True)
        min_relevance_score (float): Мінімальний score для позначення як target (0.7)
        priority_boost (int): Додатковий пріоритет для релевантних посилань (10)
        analyze_links (bool): Аналізувати посилання на релевантність (True)
        analyze_content (bool): Аналізувати контент сторінки (True)
        max_text_length (int): Максимальна довжина тексту для аналізу (4000)
        model (str): Модель g4f для використання ('gpt-4o-mini')
        provider (str): Провайдер g4f (None = автовибір)
        cache_results (bool): Кешувати результати аналізу (True)
        strict_mode (bool): Суворий режим - тільки високорелевантні (False)
        
    Результати в user_data:
        is_target_page (bool): Чи це шукана сторінка
        relevance_score (float): Score релевантності 0.0-1.0
        relevance_level (str): Рівень релевантності (high/medium/low/irrelevant)
        relevance_reason (str): Пояснення чому така оцінка
        child_priorities (dict): Пріоритети для дочірніх посилань
        explicit_scan_decisions (dict): Рішення про сканування конкретних URL
        
    Приклад з кастомною Node:
        >>> class SmartFinderNode(gc.Node):
        ...     is_target: bool = Field(default=False)
        ...     relevance_score: float = Field(default=0.0)
        ...     
        ...     def _update_from_context(self, context):
        ...         super()._update_from_context(context)
        ...         self.is_target = context.user_data.get('is_target_page', False)
        ...         self.relevance_score = context.user_data.get('relevance_score', 0.0)
    """
    
    def __init__(self, search_prompt: str, config: Dict[str, Any] = None):
        """
        Ініціалізує SmartPageFinderPlugin.
        
        Args:
            search_prompt: Опис того, що шукаємо (обов'язковий)
            config: Словник з параметрами конфігурації
        """
        super().__init__(config)
        
        if not search_prompt or not search_prompt.strip():
            raise ValueError("search_prompt не може бути порожнім")
        
        self.search_prompt = search_prompt.strip()
        
        # Параметри аналізу
        self.min_relevance_score = self.config.get("min_relevance_score", 0.7)
        self.priority_boost = self.config.get("priority_boost", 10)
        self.analyze_links = self.config.get("analyze_links", True)
        self.analyze_content = self.config.get("analyze_content", True)
        self.max_text_length = self.config.get("max_text_length", 4000)
        self.strict_mode = self.config.get("strict_mode", False)
        
        # Параметри g4f
        self.model = self.config.get("model", "gpt-4o-mini")
        self.provider_name = self.config.get("provider", None)
        
        # Кеш результатів
        self.cache_results = self.config.get("cache_results", True)
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # g4f клієнт (ліниве завантаження)
        self._g4f_client = None
        self._g4f_available = None
        
        logger.info(
            f"SmartPageFinderPlugin initialized: "
            f"prompt='{self.search_prompt[:50]}...', "
            f"min_score={self.min_relevance_score}, "
            f"model={self.model}"
        )
    
    @property
    def plugin_type(self) -> NodePluginType:
        """Тип плагіну - виконується після сканування."""
        return NodePluginType.ON_AFTER_SCAN
    
    @property
    def name(self) -> str:
        """Назва плагіну."""
        return "SmartPageFinderPlugin"
    
    def _init_g4f(self) -> bool:
        """
        Ініціалізує g4f клієнт.
        
        Returns:
            True якщо g4f доступний, False інакше
        """
        if self._g4f_available is not None:
            return self._g4f_available
        
        try:
            import g4f
            from g4f.client import Client
            
            self._g4f_client = Client()
            self._g4f_available = True
            logger.info("g4f successfully initialized")
            return True
            
        except ImportError:
            logger.warning(
                "g4f not installed. Install with: pip install g4f\n"
                "Plugin will use fallback keyword-based analysis."
            )
            self._g4f_available = False
            return False
            
        except Exception as e:
            logger.error(f"Error initializing g4f: {e}")
            self._g4f_available = False
            return False
    
    def _get_provider(self):
        """Отримує провайдер g4f."""
        if not self.provider_name:
            return None
        
        try:
            import g4f.Provider as Provider
            return getattr(Provider, self.provider_name, None)
        except Exception:
            return None
    
    def execute(self, context: NodePluginContext) -> NodePluginContext:
        """
        Виконує аналіз сторінки на релевантність.
        
        Args:
            context: Контекст з даними ноди
            
        Returns:
            Оновлений контекст з результатами аналізу
        """
        try:
            url = context.url
            
            # Перевірка кешу
            if self.cache_results and url in self._cache:
                cached = self._cache[url]
                context.user_data.update(cached)
                logger.debug(f"Using cached result for {url}")
                return context
            
            # Збираємо дані для аналізу
            page_data = self._extract_page_data(context)
            
            # Аналізуємо сторінку
            if self._init_g4f() and self.analyze_content:
                result = self._analyze_with_llm(page_data)
            else:
                result = self._analyze_with_keywords(page_data)
            
            context.user_data['is_target_page'] = result['is_target']
            context.user_data['relevance_score'] = result['score']
            context.user_data['relevance_level'] = result['level']
            context.user_data['relevance_reason'] = result['reason']
            
            # Аналізуємо посилання якщо увімкнено
            if self.analyze_links and context.extracted_links:
                priorities, decisions = self._analyze_links(
                    context.extracted_links, 
                    page_data,
                    result['score']
                )
                context.user_data['child_priorities'] = priorities
                context.user_data['explicit_scan_decisions'] = decisions
            
            # Кешуємо результат
            if self.cache_results:
                self._cache[url] = {
                    'is_target_page': result['is_target'],
                    'relevance_score': result['score'],
                    'relevance_level': result['level'],
                    'relevance_reason': result['reason'],
                }
            
            # Логування
            level_emoji = {
                RelevanceLevel.HIGH.value: "🎯",
                RelevanceLevel.MEDIUM.value: "🔶",
                RelevanceLevel.LOW.value: "🔹",
                RelevanceLevel.IRRELEVANT.value: "⚪"
            }
            emoji = level_emoji.get(result['level'], "❓")
            
            logger.info(
                f"{emoji} {url}: score={result['score']:.2f}, "
                f"level={result['level']}, target={result['is_target']}"
            )
            
        except Exception as e:
            logger.error(
                f"Error in SmartPageFinderPlugin for {context.url}: {e}",
                exc_info=True
            )
            # Встановлюємо дефолтні значення при помилці
            context.user_data['is_target_page'] = False
            context.user_data['relevance_score'] = 0.0
            context.user_data['relevance_level'] = RelevanceLevel.IRRELEVANT.value
            context.user_data['relevance_reason'] = f"Analysis error: {str(e)}"
        
        return context
    
    def _extract_page_data(self, context: NodePluginContext) -> Dict[str, Any]:
        """
        Витягує дані сторінки для аналізу.
        
        Args:
            context: Контекст ноди
            
        Returns:
            Словник з даними сторінки
        """
        data = {
            'url': context.url,
            'title': '',
            'h1': '',
            'description': '',
            'text': '',
            'links_count': len(context.extracted_links),
        }
        
        # Метадані
        if context.metadata:
            data['title'] = context.metadata.get('title', '') or ''
            data['h1'] = context.metadata.get('h1', '') or ''
            data['description'] = context.metadata.get('description', '') or ''
        
        # Текст з HTML
        if context.html_tree:
            try:
                raw_text = getattr(context.html_tree, 'text', '') or ''
                text = ' '.join(raw_text.split())
                data['text'] = text[:self.max_text_length]
            except Exception:
                pass
        
        # Текст з ноди (якщо є кастомне поле)
        node = context.node
        if hasattr(node, 'text') and node.text:
            data['text'] = str(node.text)[:self.max_text_length]
        
        return data
    
    def _analyze_with_llm(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Аналізує сторінку за допомогою LLM (g4f).
        
        Args:
            page_data: Дані сторінки
            
        Returns:
            Результат аналізу
        """
        try:
            # Формуємо промпт для LLM
            system_prompt = """Ти експерт з аналізу веб-сторінок. Твоя задача - визначити чи сторінка відповідає пошуковому запиту.

Відповідай ТІЛЬКИ у форматі JSON:
{
    "score": 0.0-1.0,
    "level": "high|medium|low|irrelevant",
    "reason": "коротке пояснення українською"
}

Рівні:
- high (0.8-1.0): сторінка точно відповідає запиту
- medium (0.5-0.8): сторінка частково відповідає або містить релевантну інформацію
- low (0.2-0.5): є слабкий зв'язок з запитом
- irrelevant (0.0-0.2): сторінка не має відношення до запиту"""

            user_prompt = f"""Пошуковий запит: {self.search_prompt}

Дані сторінки:
URL: {page_data['url']}
Title: {page_data['title']}
H1: {page_data['h1']}
Description: {page_data['description']}
Текст (перші 2000 символів): {page_data['text'][:2000]}

Оціни релевантність цієї сторінки до пошукового запиту."""

            response = self._g4f_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                provider=self._get_provider(),
            )
            
            # Парсимо відповідь
            content = response.choices[0].message.content
            result = self._parse_llm_response(content)
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, falling back to keywords")
            return self._analyze_with_keywords(page_data)
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        Парсить відповідь LLM.
        
        Args:
            content: Текст відповіді
            
        Returns:
            Результат аналізу
        """
        import json
        
        try:
            # Знаходимо JSON у відповіді
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                score = float(data.get('score', 0.0))
                score = max(0.0, min(1.0, score))  # Clamp 0-1
                
                level = data.get('level', 'irrelevant')
                if level not in [e.value for e in RelevanceLevel]:
                    level = self._score_to_level(score)
                
                reason = data.get('reason', 'No reason provided')
                
                return {
                    'score': score,
                    'level': level,
                    'reason': reason,
                    'is_target': score >= self.min_relevance_score
                }
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse LLM response: {e}")
        
        # Fallback - аналіз тексту відповіді
        content_lower = content.lower()
        
        if any(w in content_lower for w in ['high', 'висок', 'точно', 'відповідає']):
            return {'score': 0.85, 'level': 'high', 'reason': content[:100], 'is_target': True}
        elif any(w in content_lower for w in ['medium', 'середн', 'частково', 'можливо']):
            return {'score': 0.6, 'level': 'medium', 'reason': content[:100], 'is_target': False}
        elif any(w in content_lower for w in ['low', 'низьк', 'малоймовірно']):
            return {'score': 0.3, 'level': 'low', 'reason': content[:100], 'is_target': False}
        else:
            return {'score': 0.1, 'level': 'irrelevant', 'reason': content[:100], 'is_target': False}
    
    def _analyze_with_keywords(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback аналіз на основі ключових слів (без LLM).
        
        Покращена версія з точнішим скорингом для пошуку конкретного контенту.
        
        Args:
            page_data: Дані сторінки
            
        Returns:
            Результат аналізу
        """
        # Витягуємо ключові слова з промпту
        keywords = self._extract_keywords(self.search_prompt)
        
        if not keywords:
            return {
                'score': 0.0,
                'level': RelevanceLevel.IRRELEVANT.value,
                'reason': 'No keywords extracted from search prompt',
                'is_target': False
            }
        
        # Аналізуємо різні частини сторінки з різною вагою
        url_text = page_data['url'].lower()
        title_text = page_data['title'].lower()
        h1_text = page_data['h1'].lower()
        description_text = page_data['description'].lower()
        body_text = page_data['text'].lower()
        
        # Рахуємо збіги з вагами
        url_matches = sum(1 for kw in keywords if kw.lower() in url_text)
        title_matches = sum(1 for kw in keywords if kw.lower() in title_text)
        h1_matches = sum(1 for kw in keywords if kw.lower() in h1_text)
        desc_matches = sum(1 for kw in keywords if kw.lower() in description_text)
        body_matches = sum(1 for kw in keywords if kw.lower() in body_text)
        
        # Рахуємо точні фрази (якщо промпт містить фразу в лапках або це назва)
        exact_phrase = ' '.join(keywords[:4]).lower()  # Перші 4 слова як фраза
        exact_phrase_alt = '-'.join(keywords[:4]).lower()  # Slug версія
        
        exact_match_url = exact_phrase in url_text or exact_phrase_alt in url_text
        exact_match_title = exact_phrase in title_text
        exact_match_h1 = exact_phrase in h1_text
        
        # Розраховуємо score з вагами
        total_keywords = len(keywords)
        
        # Ваги: URL і title найважливіші для ідентифікації сторінки
        weighted_score = 0.0
        
        # URL містить keywords - дуже важливо (вага 0.35)
        if total_keywords > 0:
            url_score = min(1.0, url_matches / min(total_keywords, 3)) * 0.35
            weighted_score += url_score
        
        # Title містить keywords (вага 0.30)
        if total_keywords > 0:
            title_score = min(1.0, title_matches / min(total_keywords, 4)) * 0.30
            weighted_score += title_score
        
        # H1 містить keywords (вага 0.15)
        if total_keywords > 0:
            h1_score = min(1.0, h1_matches / min(total_keywords, 4)) * 0.15
            weighted_score += h1_score
        
        # Body містить keywords (вага 0.20)
        if total_keywords > 0:
            body_score = min(1.0, body_matches / total_keywords) * 0.20
            weighted_score += body_score
        
        # БОНУСИ за точні збіги
        if exact_match_url:
            weighted_score = min(1.0, weighted_score + 0.3)  # Великий бонус!
        if exact_match_title:
            weighted_score = min(1.0, weighted_score + 0.2)
        if exact_match_h1:
            weighted_score = min(1.0, weighted_score + 0.15)
        
        # Фінальний score
        score = min(1.0, weighted_score)
        
        level = self._score_to_level(score)
        is_target = score >= self.min_relevance_score
        
        if self.strict_mode and level != RelevanceLevel.HIGH.value:
            is_target = False
        
        # Формуємо reason
        matched_in = []
        if url_matches > 0:
            matched_in.append(f"URL({url_matches})")
        if title_matches > 0:
            matched_in.append(f"title({title_matches})")
        if h1_matches > 0:
            matched_in.append(f"h1({h1_matches})")
        if body_matches > 0:
            matched_in.append(f"body({body_matches})")
        
        reason = f"Keywords found in: {', '.join(matched_in) if matched_in else 'none'}"
        if exact_match_url or exact_match_title:
            reason += " [EXACT MATCH!]"
        
        return {
            'score': score,
            'level': level,
            'reason': reason,
            'is_target': is_target
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Витягує ключові слова з тексту.
        
        Args:
            text: Вхідний текст
            
        Returns:
            Список ключових слів
        """
        # Стоп-слова (українські та англійські)
        stop_words = {
            'і', 'та', 'або', 'а', 'але', 'що', 'як', 'це', 'на', 'в', 'у', 'з', 'із',
            'до', 'від', 'про', 'для', 'по', 'за', 'над', 'під', 'між', 'через',
            'шукаю', 'знайти', 'потрібно', 'хочу', 'треба', 'сторінки', 'сторінка',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'about',
            'find', 'search', 'looking', 'want', 'need', 'pages', 'page', 'content'
        }
        
        # Токенізація
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Фільтрація
        keywords = []
        for word in words:
            if len(word) >= 3 and word not in stop_words:
                keywords.append(word)
        
        return list(set(keywords))  # Унікальні
    
    def _score_to_level(self, score: float) -> str:
        """Конвертує score у рівень релевантності."""
        if score >= 0.8:
            return RelevanceLevel.HIGH.value
        elif score >= 0.5:
            return RelevanceLevel.MEDIUM.value
        elif score >= 0.2:
            return RelevanceLevel.LOW.value
        else:
            return RelevanceLevel.IRRELEVANT.value
    
    def _analyze_links(
        self, 
        links: List[str], 
        page_data: Dict[str, Any],
        page_score: float
    ) -> Tuple[Dict[str, int], Dict[str, bool]]:
        """
        Аналізує посилання та встановлює пріоритети для ML-керованого краулінгу.
        
        Це КЛЮЧОВА функція для пріоритизації - визначає куди краулер піде першим!
        
        Args:
            links: Список посилань
            page_data: Дані поточної сторінки
            page_score: Score релевантності поточної сторінки
            
        Returns:
            Tuple (priorities dict, explicit_decisions dict)
        """
        priorities = {}
        decisions = {}
        
        keywords = self._extract_keywords(self.search_prompt)
        
        # Патерни для контентних сторінок (високий пріоритет)
        content_patterns = [
            r'/fiction/\d+',           # Сторінка книги/fiction
            r'/book/\d+',              # Сторінка книги
            r'/novel/\d+',             # Сторінка novel
            r'/story/\d+',             # Сторінка story
            r'/article/',              # Статті
            r'/post/',                 # Пости
            r'/product/',              # Продукти
            r'/item/',                 # Items
            r'/details/',              # Деталі
            r'/view/',                 # View pages
        ]
        
        # Патерни для навігаційних сторінок (середній пріоритет - можуть вести до контенту)
        navigation_patterns = [
            r'\?page=\d+',             # Пагінація - ВАЖЛИВО для пошуку!
            r'/page/\d+',              # Пагінація
            r'/category/',             # Категорії
            r'/tag/',                  # Теги
            r'/genre/',                # Жанри
            r'/list',                  # Списки
            r'/browse',                # Browse pages
            r'/search',                # Search результати
            r'best-rated',             # Best rated
            r'popular',                # Popular
            r'trending',               # Trending
        ]
        
        # Патерни для ігнорування (низький пріоритет)
        ignore_patterns = [
            r'/login', r'/register', r'/signup', r'/signin',
            r'/cart', r'/checkout', r'/payment',
            r'/privacy', r'/terms', r'/cookie', r'/legal', r'/tos',
            r'/contact', r'/about', r'/faq', r'/help',
            r'/profile/\d+$',          # Профілі користувачів
            r'/user/',                 # User pages
            r'/account',               # Account
            r'/settings',              # Settings
            r'/notifications',         # Notifications
            r'/messages',              # Messages
            r'/forums?/',              # Forums
            r'/comment',               # Comments
            r'/review',                # Reviews без контенту
            r'\.(pdf|doc|docx|xls|xlsx|zip|rar|exe|dmg)$',
            r'/wp-admin', r'/admin', r'/dashboard',
            r'/api/', r'/ajax/',       # API endpoints
            r'/cdn/', r'/static/',     # Static resources
            r'#',                      # Anchors
            r'javascript:',            # JS links
            r'mailto:',                # Email links
        ]
        
        for link in links:
            link_lower = link.lower()
            
            # Базовий пріоритет
            priority = 5
            
            # 1. Перевіряємо чи це ігнорувати
            should_ignore = False
            for pattern in ignore_patterns:
                if re.search(pattern, link_lower):
                    priority = 1  # Мінімальний пріоритет
                    should_ignore = True
                    break
            
            if should_ignore:
                priorities[link] = priority
                continue
            
            # 2. Перевіряємо ключові слова в URL - НАЙВАЖЛИВІШЕ!
            keyword_matches = sum(1 for kw in keywords if kw.lower() in link_lower)
            
            if keyword_matches >= 3:
                priority = 15  # Дуже високий - багато збігів!
            elif keyword_matches >= 2:
                priority = 12  # Високий пріоритет
            elif keyword_matches == 1:
                priority = 9   # Середньо-високий пріоритет
            
            # 3. Перевіряємо контентні патерни
            for pattern in content_patterns:
                if re.search(pattern, link_lower):
                    priority = max(priority, 10)  # Контентні сторінки важливі
                    # Якщо є і keywords - ще вищий пріоритет
                    if keyword_matches > 0:
                        priority = min(15, priority + keyword_matches * 2)
                    break
            
            # 4. Навігаційні сторінки - можуть вести до контенту
            for pattern in navigation_patterns:
                if re.search(pattern, link_lower):
                    priority = max(priority, 7)  # Навігація важлива для пошуку
                    # Пагінація з ключовими словами - високий пріоритет
                    if keyword_matches > 0 and ('page=' in link_lower or '/page/' in link_lower):
                        priority = min(13, priority + 3)
                    break
            
            # 5. Бонус якщо поточна сторінка релевантна
            if page_score >= 0.7:
                priority = min(15, priority + 2)  # Посилання з релевантних сторінок важливіші
            elif page_score >= 0.5:
                priority = min(13, priority + 1)
            
            # 6. Спеціальні правила для конкретного URL тексту
            # Якщо в URL є частина пошукового запиту (slug)
            search_slug = '-'.join(self.search_prompt.lower().split()[:3])
            if search_slug in link_lower or search_slug.replace('-', '') in link_lower.replace('-', ''):
                priority = 15  # Максимальний пріоритет - можливо це те що шукаємо!
            
            priorities[link] = priority
        
        # Логуємо топ пріоритетні посилання
        if priorities:
            top_links = sorted(priorities.items(), key=lambda x: x[1], reverse=True)[:5]
            logger.debug(f"Top priority links: {[(url.split('/')[-1][:30], p) for url, p in top_links]}")
        
        return priorities, decisions
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Повертає статистику роботи плагіну.
        
        Returns:
            Словник зі статистикою
        """
        if not self._cache:
            return {'total_analyzed': 0, 'target_pages': 0, 'avg_score': 0.0}
        
        scores = [v['relevance_score'] for v in self._cache.values()]
        targets = sum(1 for v in self._cache.values() if v['is_target_page'])
        
        return {
            'total_analyzed': len(self._cache),
            'target_pages': targets,
            'avg_score': sum(scores) / len(scores) if scores else 0.0,
            'score_distribution': {
                'high': sum(1 for v in self._cache.values() if v['relevance_level'] == 'high'),
                'medium': sum(1 for v in self._cache.values() if v['relevance_level'] == 'medium'),
                'low': sum(1 for v in self._cache.values() if v['relevance_level'] == 'low'),
                'irrelevant': sum(1 for v in self._cache.values() if v['relevance_level'] == 'irrelevant'),
            }
        }
    
    def clear_cache(self):
        """Очищує кеш результатів."""
        self._cache.clear()
        logger.info("SmartPageFinderPlugin cache cleared")
    
    def __repr__(self):
        return (
            f"SmartPageFinderPlugin("
            f"prompt='{self.search_prompt[:30]}...', "
            f"min_score={self.min_relevance_score}, "
            f"model={self.model}, "
            f"enabled={self.enabled})"
        )


# КАСТОМНА НОДА ДЛЯ ЗРУЧНОЇ РОБОТИ З ПЛАГІНОМ

def create_smart_finder_node_class():
    """
    Фабрика для створення кастомного Node класу для SmartPageFinderPlugin.
    
    Використання:
        >>> SmartFinderNode = create_smart_finder_node_class()
        >>> graph = gc.crawl(url, plugins=[plugin], node_class=SmartFinderNode)
        >>> for node in graph:
        ...     if node.is_target:
        ...         print(f"Found: {node.url} (score: {node.relevance_score})")
    """
    try:
        import graph_crawler as gc
        from pydantic import Field
        from typing import Optional
        
        class SmartFinderNode(gc.Node):
            """Node з підтримкою SmartPageFinderPlugin."""
            
            is_target: bool = Field(default=False, description="Чи це шукана сторінка")
            relevance_score: float = Field(default=0.0, description="Score релевантності 0.0-1.0")
            relevance_level: str = Field(default="irrelevant", description="Рівень релевантності")
            relevance_reason: str = Field(default="", description="Пояснення оцінки")
            text: Optional[str] = Field(default=None, description="Текст сторінки")
            
            def _update_from_context(self, context):
                """Оновлює дані з контексту після сканування."""
                super()._update_from_context(context)
                
                # Витягуємо текст
                if context.html_tree:
                    try:
                        raw_text = getattr(context.html_tree, 'text', '') or ''
                        self.text = ' '.join(raw_text.split())[:5000]
                    except Exception:
                        pass
                
                # Копіюємо результати плагіну
                self.is_target = context.user_data.get('is_target_page', False)
                self.relevance_score = context.user_data.get('relevance_score', 0.0)
                self.relevance_level = context.user_data.get('relevance_level', 'irrelevant')
                self.relevance_reason = context.user_data.get('relevance_reason', '')
        
        return SmartFinderNode
        
    except ImportError:
        logger.warning("graph_crawler not available, returning None")
        return None


# Експортуємо для зручності
SmartFinderNode = create_smart_finder_node_class()
