"""Планувальник для управління чергою вузлів.

ОПТИМІЗАЦІЯ v4.2:
- Native Cython BloomFilterFast (2.7x швидше за pybloom-live)
- Автоматичний fallback на pybloom-live якщо native не скомпільовано

- Винесено lazy imports на рівень модуля
- Умовний імпорт CrawlerEvent тільки якщо event_bus активний
"""

import heapq
import logging
import re
import sys
from collections import deque
from typing import List, Optional, Set, Union

from graph_crawler.domain.entities.node import Node
from graph_crawler.shared.constants import (
    DEFAULT_URL_PRIORITY,
    PRIORITY_MAX,
    PRIORITY_MIN,
)

logger = logging.getLogger(__name__)

# ОПТИМІЗАЦІЯ v4.2: Спробуємо завантажити Native Bloom Filter
_NATIVE_BLOOM_AVAILABLE = False
_BloomFilterClass = None

try:
    sys.path.insert(0, '/app/web_graf/graph_crawler/native')
    from _bloom_filter import BloomFilterFast
    _NATIVE_BLOOM_AVAILABLE = True
    _BloomFilterClass = BloomFilterFast
    logger.info(" Native Cython BloomFilterFast loaded (2.7x faster)")
except ImportError:
    # Fallback на pybloom-live
    from graph_crawler.shared.utils.bloom_filter import BloomFilter
    _BloomFilterClass = BloomFilter
    logger.debug("Native BloomFilterFast not available, using pybloom-live")

try:
    from graph_crawler.domain.events import CrawlerEvent, EventType

    _EVENTS_AVAILABLE = True
except ImportError:
    _EVENTS_AVAILABLE = False
    CrawlerEvent = None
    EventType = None


class CrawlScheduler:
    """
    Планувальник для управління чергою вузлів для сканування.

    Alpha 2.0: Smart Scheduling з Priority Queue
    - Використовує heapq для пріоритизації URL
    - Підтримує url_rules для контролю поведінки
    - Застосовує should_scan та should_follow_links з правил

    v4.2: Native Bloom Filter Integration
    - Використовує Native Cython BloomFilterFast (2.7x швидше)
    - Автоматичний fallback на pybloom-live
    - Економія пам'яті в 10x для великих краулінгів (1M+ URLs)
    - Configurable: можна вимкнути (use_bloom_filter=False)

    Стара версія використовувала BFS (Breadth-First Search).
    Нова версія використовує Priority Queue для контрольованого обходу.
    """

    def __init__(
        self,
        url_rules: Optional[List] = None,
        event_bus=None,
        use_bloom_filter: bool = True,
        bloom_capacity: int = 10_000_000,
        bloom_error_rate: float = 0.001,
    ):
        """
        Ініціалізує scheduler.

        Args:
            url_rules: Список URLRule об'єктів для контролю URL
            event_bus: EventBus для публікації подій (опціонально)
            use_bloom_filter: Використовувати Bloom Filter замість set (default: True)
            bloom_capacity: Capacity Bloom Filter (default: 10M URLs)
            bloom_error_rate: Error rate Bloom Filter (default: 0.1%)
        """
        # Priority queue: (priority, counter, node)
        # Counter потрібен для стабільної сортування при однакових пріоритетах
        self.queue: List = []  # heapq priority queue
        self.counter: int = 0  # Для FIFO при однакових пріоритетах

        # Bloom Filter або set для seen URLs
        # ОПТИМІЗАЦІЯ v4.2: Використовуємо Native BloomFilterFast якщо доступний
        self.use_bloom_filter = use_bloom_filter
        if use_bloom_filter:
            self.seen_urls = _BloomFilterClass(
                capacity=bloom_capacity, error_rate=bloom_error_rate
            )
            bloom_type = "Native Cython" if _NATIVE_BLOOM_AVAILABLE else "pybloom-live"
            logger.info(
                f"🚀 Scheduler initialized with {bloom_type} Bloom Filter: "
                f"capacity={bloom_capacity:,}, error_rate={bloom_error_rate*100}%"
            )
        else:
            self.seen_urls: Union[object, Set[str]] = set()
            logger.debug("Scheduler initialized with Python set (not Bloom Filter)")

        # URL Rules для Smart Scheduling
        self.url_rules = url_rules or []

        # EventBus для подій (Alpha 2.0)
        self.event_bus = event_bus

        # Компілюємо regex патерни для швидкості
        self._compiled_rules = []
        for rule in self.url_rules:
            try:
                compiled_pattern = re.compile(rule.pattern)
                self._compiled_rules.append((compiled_pattern, rule))
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{rule.pattern}': {e}")

        logger.debug(f"Scheduler initialized with {len(self.url_rules)} URL rules")

    def add_node(self, node: Node, priority: Optional[int] = None) -> bool:
        """
        Додає вузол до черги з пріоритетом.

        Alpha 2.0: Застосовує url_rules для:
        1. Фільтрації (action='exclude')
        2. Пріоритизації (priority 1-10)
        3. Контролю поведінки (should_scan, should_follow_links)
        
        ML Plugin Support: Якщо передано priority параметр - використовує його 
        замість обчисленого пріоритету (для child_priorities від плагінів).

        Args:
            node: Вузол для додавання
            priority: Опціональний пріоритет від ML плагіну (перебиває всі інші)

        Returns:
            True якщо вузол додано, False якщо вже був у черзі або відфільтровано
        """
        # Перевіряємо чи вже бачили цей URL
        if node.url in self.seen_urls:
            return False

        # Знаходимо перше правило що матчить URL
        matched_rule = self._match_rule(node.url)

        # Перевіряємо should_scan=False (exclude)
        # URLRule використовує should_scan замість action
        if matched_rule and matched_rule.should_scan is False:
            logger.debug(f"Excluded by rule: {node.url}")
            self.seen_urls.add(node.url)  # Додаємо щоб не перевіряти знову

            # Подія про виключення URL (Alpha 2.0)
            if self.event_bus and _EVENTS_AVAILABLE:
                self.event_bus.publish(
                    CrawlerEvent.create(
                        EventType.URL_EXCLUDED,
                        data={
                            "url": node.url,
                            "pattern": matched_rule.pattern,
                            "reason": "excluded_by_rule",
                        },
                    )
                )
            return False

        #  ML PLUGIN SUPPORT: Використовуємо переданий priority якщо є
        if priority is not None:
            final_priority = priority
            logger.debug(f"Using ML plugin priority: {final_priority} for {node.url}")
        else:
            # Застосовуємо правило до ноди (пріоритет, should_scan, should_follow_links)
            final_priority = self._calculate_priority(node.url, matched_rule, node)
        
        self._apply_rule_to_node(node, matched_rule)

        # Додаємо в priority queue
        # heapq - мінімальна купа, тому інвертуємо пріоритет (-priority)
        # Менше число = вища позиція в черзі
        self.counter += 1
        heapq.heappush(self.queue, (-final_priority, self.counter, node))
        self.seen_urls.add(node.url)

        logger.debug(
            f"Added node: {node.url} (priority={final_priority}, "
            f"should_scan={node.should_scan}, can_create_edges={node.can_create_edges})"
        )

        # Подія про додавання URL в чергу (Alpha 2.0)
        if self.event_bus and _EVENTS_AVAILABLE:
            self.event_bus.publish(
                CrawlerEvent.create(
                    EventType.URL_ADDED_TO_QUEUE,
                    data={
                        "url": node.url,
                        "depth": node.depth,
                        "priority": final_priority,
                        "queue_size": len(self.queue),
                    },
                )
            )

            # Якщо пріоритет нестандартний - додаткова подія
            if final_priority != DEFAULT_URL_PRIORITY:
                self.event_bus.publish(
                    CrawlerEvent.create(
                        EventType.URL_PRIORITIZED,
                        data={
                            "url": node.url,
                            "priority": final_priority,
                            "pattern": matched_rule.pattern if matched_rule else None,
                            "from_ml_plugin": priority is not None,
                        },
                    )
                )

        return True

    def get_next(self) -> Optional[Node]:
        """
        Повертає наступний вузол для сканування (з найвищим пріоритетом).

        Alpha 2.0: Використовує priority queue замість FIFO.

        Returns:
            Вузол або None якщо черга порожня
        """
        if self.is_empty():
            return None

        # Отримуємо вузол з найвищим пріоритетом
        priority, counter, node = heapq.heappop(self.queue)
        logger.debug(f"Getting next node: {node.url} (priority={-priority})")
        return node

    def _match_rule(self, url: str):
        """
        Знаходить перше правило що матчить URL.

        Args:
            url: URL для перевірки

        Returns:
            URLRule або None якщо немає збігів
        """
        for compiled_pattern, rule in self._compiled_rules:
            if compiled_pattern.search(url):
                return rule
        return None

    def _calculate_priority(self, url: str, matched_rule, node: Node) -> int:
        """
        Обчислює пріоритет URL.

         Підтримка динамічних пріоритетів від плагінів!

        Порядок перевірки:
        1. Node.priority атрибут (динамічний, від плагінів) - НАЙВИЩИЙ ПРІОРИТЕТ
        2. URLRule.priority (статичний, regex-based)
        3. DEFAULT_URL_PRIORITY (fallback)

        Args:
            url: URL для перевірки
            matched_rule: Правило що зматчилось або None
            node: Node об'єкт для перевірки динамічного пріоритету

        Returns:
            Пріоритет (1-10, default=DEFAULT_URL_PRIORITY)
        """
        # 1. НОВИЙ МЕХАНІЗМ: Перевіряємо чи Node має динамічний priority (від плагінів)
        # Правильна обробка @property у підкласах Pydantic
        # Якщо priority це @property descriptor - потрібно отримати значення через __get__
        node_priority = self._get_node_priority(node)
        if node_priority is not None:
            logger.debug(f"Using dynamic priority from node: {node_priority} for {url}")
            return node_priority

        # 2. URLRule priority (статичний)
        if matched_rule:
            return matched_rule.priority

        # 3. Fallback на default
        return DEFAULT_URL_PRIORITY

    def _get_node_priority(self, node: Node) -> Optional[int]:
        """
        Безпечно отримує priority з ноди.

        Args:
            node: Node об'єкт

        Returns:
            int priority або None
        """
        # Python автоматично викликає getter для @property
        priority = getattr(node, "priority", None)
        return priority if isinstance(priority, int) else None

    def _apply_rule_to_node(self, node: Node, matched_rule):
        """
        Застосовує правило до ноди (Tell, Don't Ask принцип).

        Args:
            node: Нода для модифікації
            matched_rule: Правило що зматчилось або None
        """
        if not matched_rule:
            return

        # Tell, Don't Ask: правило саме модифікує node
        # Замість того щоб питати значення та встановлювати їх тут
        matched_rule.apply_to_node(node)

    def is_empty(self) -> bool:
        """Перевіряє чи черга порожня."""
        return len(self.queue) == 0

    def size(self) -> int:
        """Повертає розмір черги."""
        return len(self.queue)

    def has_url(self, url: str) -> bool:
        """Перевіряє чи URL вже був побачений."""
        return url in self.seen_urls

    def get_memory_statistics(self) -> dict:
        """
        Повертає статистику використання пам'яті (Alpha 2.0).

        Returns:
            dict з полями:
                - use_bloom_filter: bool - чи використовується Bloom Filter
                - seen_urls_count: int - кількість seen URLs
                - queue_size: int - розмір черги
                - bloom_statistics: dict - статистика Bloom Filter (якщо використовується)
                - bloom_type: str - тип Bloom Filter (native_cython або pybloom_live)

        Example:
            >>> scheduler = CrawlScheduler(use_bloom_filter=True)
            >>> for i in range(10000):
            ...     scheduler.add_node(Node(url=f"https://example.com/page{i}"))
            >>> stats = scheduler.get_memory_statistics()
            >>> print(f"Memory usage: {stats['bloom_statistics']['memory_usage_mb']} MB")
        """
        stats = {
            "use_bloom_filter": self.use_bloom_filter,
            "queue_size": len(self.queue),
            "bloom_type": "native_cython" if _NATIVE_BLOOM_AVAILABLE else "pybloom_live",
        }

        if self.use_bloom_filter:
            # Обидві версії підтримують get_statistics() та len()
            stats["seen_urls_count"] = len(self.seen_urls)
            stats["bloom_statistics"] = self.seen_urls.get_statistics()
        else:
            # Python set
            stats["seen_urls_count"] = len(self.seen_urls)
            stats["bloom_statistics"] = None

        return stats

    def get_summary(self) -> str:
        """
        Повертає текстовий summary scheduler (Alpha 2.0).

        Returns:
            Форматований рядок зі статистикою

        Example:
            >>> scheduler = CrawlScheduler(use_bloom_filter=True)
            >>> print(scheduler.get_summary())
        """
        stats = self.get_memory_statistics()

        lines = [
            " Crawler Scheduler Statistics",
            "" * 42,
            f"Queue Size:         {stats['queue_size']:,}",
            f"Seen URLs:          {stats['seen_urls_count']:,}",
            f"Using Bloom Filter: {'Yes ' if stats['use_bloom_filter'] else 'No (Python set)'}",
        ]

        if stats["bloom_statistics"]:
            bloom_stats = stats["bloom_statistics"]
            lines.extend(
                [
                    "",
                    " Bloom Filter Details:",
                    f"  Capacity:         {bloom_stats['capacity']:,}",
                    f"  Fill Ratio:       {bloom_stats['fill_ratio']*100:.2f}%",
                    f"  Memory Usage:     {bloom_stats['memory_usage_mb']:.2f} MB",
                    f"  Error Rate:       {bloom_stats['error_rate']*100:.2f}%",
                ]
            )

        return "\n".join(lines)
