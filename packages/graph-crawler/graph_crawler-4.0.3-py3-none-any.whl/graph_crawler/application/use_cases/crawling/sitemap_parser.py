"""Парсер sitemap для побудови графу з sitemap.xml файлів.

ОПТИМІЗОВАНО для Python 3.14:
- Async HTTP через aiohttp замість синхронного requests
- Паралельне завантаження sitemap через asyncio.gather()
- ThreadPoolExecutor для CPU-bound XML парсингу
- Збережено sync версію для зворотної сумісності
"""

import asyncio
import logging
import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# ThreadPoolExecutor для CPU-bound XML парсингу (Python 3.14 free-threading optimized)
_xml_workers = (os.cpu_count() or 4) * 2
_xml_executor = ThreadPoolExecutor(
    max_workers=_xml_workers,
    thread_name_prefix="xml_parser_"
)


class SitemapParser:
    """
    Async парсер для sitemap.xml файлів.

    ОПТИМІЗОВАНО для Python 3.14:
    - Async HTTP через aiohttp (NON-BLOCKING I/O)
    - Паралельне завантаження через asyncio.gather()
    - ThreadPoolExecutor для XML парсингу (CPU-bound)

    Підтримує:
    - sitemap index (посилання на інші sitemap)
    - urlset (список URL)
    - robots.txt для отримання sitemap URLs

    Приклад використання:
        >>> parser = SitemapParser()
        >>> # Async версія (рекомендовано)
        >>> result = await parser.parse_from_robots_async("https://example.com")
        >>> print(result['sitemap_urls'])
        >>> print(result['urls'])
        >>>
        >>> # Sync версія (для зворотної сумісності)
        >>> result = parser.parse_from_robots("https://example.com")
    """

    # XML namespaces для sitemap
    SITEMAP_NS = {
        "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "news": "http://www.google.com/schemas/sitemap-news/0.9",
        "image": "http://www.google.com/schemas/sitemap-image/1.1",
        "video": "http://www.google.com/schemas/sitemap-video/1.1",
    }

    def __init__(self, user_agent: str = "GraphCrawler/2.0", timeout: int = 30):
        """
        Ініціалізація парсера.

        Args:
            user_agent: User-Agent для HTTP запитів
            timeout: Timeout для HTTP запитів (секунди)
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self._session = None  # Lazy initialization для aiohttp

    async def _get_session(self):
        """Lazy initialization для aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent},
                timeout=timeout
            )
        return self._session

    def _normalize_url(self, url: str, base_url: str) -> str:
        """
        Нормалізує URL - перетворює відносний URL в абсолютний.

        Args:
            url: URL для нормалізації (може бути відносний)
            base_url: Базовий URL сайту

        Returns:
            Абсолютний URL
        """
        if not url:
            return url

        url = url.strip()

        # Якщо URL вже абсолютний - повертаємо як є
        if url.startswith(('http://', 'https://')):
            return url

        # Відносний URL - перетворюємо в абсолютний
        return urljoin(base_url, url)

    # ============ ASYNC METHODS (RECOMMENDED) ============

    async def parse_from_robots_async(self, base_url: str) -> Dict[str, List[str]]:
        """
        Async парсить sitemap URLs з robots.txt та завантажує їх.

        ОПТИМІЗОВАНО: Паралельне завантаження sitemap через asyncio.gather()!

        Args:
            base_url: Базовий URL сайту (https://example.com)

        Returns:
            Dict з ключами:
            - 'sitemap_urls': список знайдених sitemap URLs
            - 'urls': всі URL з усіх sitemap
            - 'sitemap_indexes': sitemap index URLs (якщо є)
        """
        result = {"sitemap_urls": [], "urls": [], "sitemap_indexes": []}

        try:
            # Завантажуємо robots.txt
            robots_url = urljoin(base_url, "/robots.txt")
            session = await self._get_session()

            async with session.get(robots_url) as response:
                if response.status != 200:
                    logger.warning(f"robots.txt not found at {robots_url}")
                    return await self._try_default_sitemaps_async(base_url, result)

                robots_content = await response.text()

            # Парсимо robots.txt для знаходження sitemap URLs
            sitemap_urls = self._parse_robots_txt(robots_content, base_url)

            if sitemap_urls:
                result["sitemap_urls"] = sitemap_urls
                logger.info(f"Знайдено {len(sitemap_urls)} sitemap URLs в robots.txt")

                # ОПТИМІЗАЦІЯ: Паралельне завантаження всіх sitemap!
                sitemap_results = await asyncio.gather(
                    *[self.parse_sitemap_async(url) for url in sitemap_urls],
                    return_exceptions=True
                )

                for sitemap_data in sitemap_results:
                    if isinstance(sitemap_data, Exception):
                        logger.warning(f"Sitemap parse error: {sitemap_data}")
                        continue
                    result["urls"].extend(sitemap_data.get("urls", []))
                    result["sitemap_indexes"].extend(sitemap_data.get("sitemap_indexes", []))
            else:
                logger.warning(f"Sitemap не знайдено в {robots_url}")
                result = await self._try_default_sitemaps_async(base_url, result)

        except Exception as e:
            logger.error(f"Помилка при читанні robots.txt з {base_url}: {e}")
            result = await self._try_default_sitemaps_async(base_url, result)

        # Видалити дублікати
        result["urls"] = list(set(result["urls"]))
        result["sitemap_indexes"] = list(set(result["sitemap_indexes"]))

        logger.info(f"Всього знайдено {len(result['urls'])} URLs в sitemap")
        return result

    async def _try_default_sitemaps_async(self, base_url: str, result: Dict) -> Dict:
        """Спробувати типові URL для sitemap (async версія)."""
        default_sitemaps = [
            urljoin(base_url, "/sitemap.xml"),
            urljoin(base_url, "/sitemap_index.xml"),
        ]

        for sitemap_url in default_sitemaps:
            try:
                sitemap_data = await self.parse_sitemap_async(sitemap_url)
                if sitemap_data["urls"] or sitemap_data["sitemap_indexes"]:
                    result["sitemap_urls"].append(sitemap_url)
                    result["urls"].extend(sitemap_data["urls"])
                    result["sitemap_indexes"].extend(sitemap_data["sitemap_indexes"])
                    logger.info(f"Знайдено sitemap на {sitemap_url}")
                    break
            except Exception as e:
                logger.debug(f"Не вдалося завантажити {sitemap_url}: {e}")

        return result

    async def parse_sitemap_async(self, sitemap_url: str) -> Dict[str, List[str]]:
        """
        Async парсить один sitemap файл.

        ОПТИМІЗОВАНО:
        - Async HTTP через aiohttp
        - XML парсинг в ThreadPoolExecutor (CPU-bound)

        Args:
            sitemap_url: URL sitemap файлу

        Returns:
            Dict з ключами:
            - 'urls': список URL з urlset
            - 'sitemap_indexes': список sitemap URLs з sitemapindex
        """
        result = {"urls": [], "sitemap_indexes": []}

        # Перевіряємо чи URL абсолютний
        if not sitemap_url.startswith(('http://', 'https://')):
            logger.error(f"Invalid sitemap URL: {sitemap_url}")
            return result

        try:
            session = await self._get_session()

            async with session.get(sitemap_url) as response:
                if response.status != 200:
                    logger.warning(f"Sitemap not found: {sitemap_url} (status={response.status})")
                    return result

                content = await response.read()

            # ОПТИМІЗАЦІЯ: XML парсинг в ThreadPoolExecutor (CPU-bound операція)
            loop = asyncio.get_event_loop()
            parsed_result = await loop.run_in_executor(
                _xml_executor,
                self._parse_sitemap_content_sync,
                content,
                sitemap_url
            )

            return parsed_result

        except Exception as e:
            logger.error(f"Помилка при парсингу sitemap {sitemap_url}: {e}")
            return result

    def _parse_sitemap_content_sync(self, content: bytes, sitemap_url: str) -> Dict[str, List[str]]:
        """
        Синхронний парсинг XML контенту sitemap.
        
        Виконується в ThreadPoolExecutor для не блокування event loop.

        Args:
            content: XML контент
            sitemap_url: URL sitemap для base URL нормалізації

        Returns:
            Dict з URLs та sitemap indexes
        """
        result = {"urls": [], "sitemap_indexes": []}

        try:
            root = ET.fromstring(content)

            # Отримуємо base URL для нормалізації
            parsed = urlparse(sitemap_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Визначити тип sitemap
            if root.tag.endswith("sitemapindex"):
                raw_indexes = self._parse_sitemap_index(root)
                result["sitemap_indexes"] = [self._normalize_url(u, base_url) for u in raw_indexes]
                logger.info(f"Знайдено {len(result['sitemap_indexes'])} sitemap в index {sitemap_url}")

            elif root.tag.endswith("urlset"):
                raw_urls = self._parse_urlset(root)
                result["urls"] = [self._normalize_url(u, base_url) for u in raw_urls]
                logger.info(f"Знайдено {len(result['urls'])} URLs в sitemap {sitemap_url}")

            else:
                logger.warning(f"Невідомий тип sitemap: {root.tag}")

        except ET.ParseError as e:
            logger.error(f"XML parse error for {sitemap_url}: {e}")
        except Exception as e:
            logger.error(f"Error parsing sitemap content {sitemap_url}: {e}")

        return result

    def _parse_robots_txt(self, content: str, base_url: str) -> List[str]:
        """
        Парсить robots.txt для знаходження sitemap URLs.

        Args:
            content: Вміст robots.txt
            base_url: Базовий URL для нормалізації

        Returns:
            Список sitemap URLs
        """
        sitemap_urls = []

        for line in content.splitlines():
            line = line.strip()
            if line.lower().startswith('sitemap:'):
                url = line[8:].strip()
                if url:
                    normalized = self._normalize_url(url, base_url)
                    sitemap_urls.append(normalized)

        return sitemap_urls

    # ============ SYNC METHODS (BACKWARD COMPATIBILITY) ============

    def parse_from_robots(self, base_url: str) -> Dict[str, List[str]]:
        """
        Sync версія parse_from_robots для зворотної сумісності.

        ПРИМІТКА: Для краулінгу використовуйте parse_from_robots_async().
        Sync версія використовує requests для HTTP запитів.

        Args:
            base_url: Базовий URL сайту

        Returns:
            Dict з sitemap URLs та URL списком
        """
        import requests as sync_requests
        
        result = {"sitemap_urls": [], "urls": [], "sitemap_indexes": []}

        try:
            # Завантажуємо robots.txt
            robots_url = urljoin(base_url, "/robots.txt")
            response = sync_requests.get(
                robots_url, 
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.warning(f"robots.txt not found at {robots_url}")
                return self._try_default_sitemaps_sync(base_url, result)

            # Парсимо robots.txt для знаходження sitemap URLs
            sitemap_urls = self._parse_robots_txt(response.text, base_url)

            if sitemap_urls:
                result["sitemap_urls"] = sitemap_urls
                logger.info(f"Знайдено {len(sitemap_urls)} sitemap URLs в robots.txt")

                # Завантажуємо кожен sitemap послідовно
                for url in sitemap_urls:
                    try:
                        sitemap_data = self.parse_sitemap(url)
                        result["urls"].extend(sitemap_data.get("urls", []))
                        result["sitemap_indexes"].extend(sitemap_data.get("sitemap_indexes", []))
                    except Exception as e:
                        logger.warning(f"Error parsing sitemap {url}: {e}")
            else:
                logger.warning(f"Sitemap не знайдено в {robots_url}")
                result = self._try_default_sitemaps_sync(base_url, result)

        except Exception as e:
            logger.error(f"Помилка при читанні robots.txt з {base_url}: {e}")
            result = self._try_default_sitemaps_sync(base_url, result)

        # Видалити дублікати
        result["urls"] = list(set(result["urls"]))
        result["sitemap_indexes"] = list(set(result["sitemap_indexes"]))

        logger.info(f"Всього знайдено {len(result['urls'])} URLs в sitemap")
        return result

    def _try_default_sitemaps_sync(self, base_url: str, result: Dict) -> Dict:
        """Спробувати типові URL для sitemap (sync версія)."""
        default_sitemaps = [
            urljoin(base_url, "/sitemap.xml"),
            urljoin(base_url, "/sitemap_index.xml"),
        ]

        for sitemap_url in default_sitemaps:
            try:
                sitemap_data = self.parse_sitemap(sitemap_url)
                if sitemap_data["urls"] or sitemap_data["sitemap_indexes"]:
                    result["sitemap_urls"].append(sitemap_url)
                    result["urls"].extend(sitemap_data["urls"])
                    result["sitemap_indexes"].extend(sitemap_data["sitemap_indexes"])
                    logger.info(f"Знайдено sitemap на {sitemap_url}")
                    break
            except Exception as e:
                logger.debug(f"Не вдалося завантажити {sitemap_url}: {e}")

        return result

    def parse_sitemap(self, sitemap_url: str) -> Dict[str, List[str]]:
        """
        Sync версія parse_sitemap для зворотної сумісності.

        ПРИМІТКА: Для краулінгу використовуйте parse_sitemap_async().
        Sync версія використовує requests для HTTP запитів.
        """
        import requests as sync_requests
        
        result = {"urls": [], "sitemap_indexes": []}

        # Перевіряємо чи URL абсолютний
        if not sitemap_url.startswith(('http://', 'https://')):
            logger.error(f"Invalid sitemap URL: {sitemap_url}")
            return result

        try:
            response = sync_requests.get(
                sitemap_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.warning(f"Sitemap not found: {sitemap_url} (status={response.status_code})")
                return result

            # Парсимо XML контент
            return self._parse_sitemap_content_sync(response.content, sitemap_url)

        except Exception as e:
            logger.error(f"Помилка при парсингу sitemap {sitemap_url}: {e}")
            return result

    # ============ INTERNAL XML PARSING ============

    def _parse_sitemap_index(self, root: ET.Element) -> List[str]:
        """
        Парсить sitemap index (посилання на інші sitemap).

        Args:
            root: XML root element

        Returns:
            Список sitemap URLs
        """
        sitemap_urls = []

        # Спробувати з namespace
        sitemaps = root.findall(".//sm:sitemap/sm:loc", self.SITEMAP_NS)
        if not sitemaps:
            # Спробувати без namespace
            sitemaps = root.findall(".//sitemap/loc")

        for sitemap in sitemaps:
            url = sitemap.text
            if url:
                sitemap_urls.append(url.strip())

        return sitemap_urls

    def _parse_urlset(self, root: ET.Element) -> List[str]:
        """
        Парсить urlset (список URLs).

        Args:
            root: XML root element

        Returns:
            Список URLs
        """
        urls = []

        # Спробувати з namespace
        url_elements = root.findall(".//sm:url/sm:loc", self.SITEMAP_NS)
        if not url_elements:
            # Спробувати без namespace
            url_elements = root.findall(".//url/loc")

        for url_elem in url_elements:
            url = url_elem.text
            if url:
                urls.append(url.strip())

        return urls

    async def close(self):
        """Закрити aiohttp сесію."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def __del__(self):
        """Cleanup on deletion."""
        if self._session and not self._session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except Exception:
                pass
