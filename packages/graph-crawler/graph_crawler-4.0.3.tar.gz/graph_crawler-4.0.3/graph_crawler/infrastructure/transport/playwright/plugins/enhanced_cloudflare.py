"""
Enhanced Cloudflare Bypass плагін для Playwright драйвера.

Покращена версія з:
- Автоматичним Turnstile solver
- Human-like interaction для проходження challenges
- Retry logic з exponential backoff
- Cookie persistence
"""

import asyncio
import logging
import random
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from graph_crawler.infrastructure.transport.base_plugin import BaseDriverPlugin
from graph_crawler.infrastructure.transport.playwright.context import BrowserContext
from graph_crawler.infrastructure.transport.playwright.stages import BrowserStage

logger = logging.getLogger(__name__)


class ChallengeType(Enum):
    """Типи Cloudflare challenge."""
    NONE = "none"
    IUAM_V1 = "iuam_v1"
    IUAM_V2 = "iuam_v2"
    CAPTCHA_V1 = "captcha_v1"
    CAPTCHA_V2 = "captcha_v2"
    TURNSTILE = "turnstile"
    FIREWALL_1020 = "firewall_1020"


class EnhancedCloudflareDetector:
    """Покращений детектор Cloudflare challenge."""

    @staticmethod
    def is_cloudflare_server(headers: Dict[str, str]) -> bool:
        server = headers.get("server", "") or headers.get("Server", "")
        return server.lower().startswith("cloudflare")

    @staticmethod
    def is_iuam_challenge(html: str, status_code: Optional[int], headers: Dict[str, str]) -> bool:
        try:
            if not EnhancedCloudflareDetector.is_cloudflare_server(headers):
                return False
            if status_code not in [429, 503]:
                return False
            if not re.search(r"/cdn-cgi/images/trace/jsch/", html, re.M | re.S):
                return False
            if not re.search(
                r"""<form .*?="challenge-form" action="/\S+__cf_chl_f_tk=""",
                html, re.M | re.S,
            ):
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def is_iuam_v2_challenge(html: str, status_code: Optional[int], headers: Dict[str, str]) -> bool:
        try:
            if not EnhancedCloudflareDetector.is_iuam_challenge(html, status_code, headers):
                return False
            return bool(re.search(
                r"""cpo.src\s*=\s*['"/]cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1""",
                html, re.M | re.S,
            ))
        except Exception:
            return False

    @staticmethod
    def is_captcha_challenge(html: str, status_code: Optional[int], headers: Dict[str, str]) -> bool:
        try:
            if not EnhancedCloudflareDetector.is_cloudflare_server(headers):
                return False
            if status_code != 403:
                return False
            if not re.search(r"/cdn-cgi/images/trace/(captcha|managed)/", html, re.M | re.S):
                return False
            if not re.search(
                r"""<form .*?="challenge-form" action="/\S+__cf_chl_f_tk=""",
                html, re.M | re.S,
            ):
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def is_captcha_v2_challenge(html: str, status_code: Optional[int], headers: Dict[str, str]) -> bool:
        try:
            if not EnhancedCloudflareDetector.is_captcha_challenge(html, status_code, headers):
                return False
            return bool(re.search(
                r"""cpo.src\s*=\s*['"/]cdn-cgi/challenge-platform/\S+orchestrate/(captcha|managed)/v1""",
                html, re.M | re.S,
            ))
        except Exception:
            return False

    @staticmethod
    def is_turnstile_challenge(html: str, status_code: Optional[int], headers: Dict[str, str]) -> bool:
        """Покращене виявлення Turnstile challenge."""
        try:
            # Turnstile може бути і без Cloudflare server header
            turnstile_patterns = [
                r"challenges\.cloudflare\.com/turnstile",
                r"cf-turnstile",
                r'data-sitekey=["\']\w+["\'].*turnstile',
                r"turnstile/v0/api\.js",
                r"cf-turnstile-response",
                r"class=[\"']cf-turnstile[\"']",
                r"id=[\"']cf-turnstile[\"']",
                # Нові паттерни
                r"__cf_chl_tk",
                r"cf_chl_prog",
                r"chlApiSitekey",
            ]

            for pattern in turnstile_patterns:
                if re.search(pattern, html, re.I):
                    logger.debug(f"Turnstile detected via pattern: {pattern}")
                    return True

            return False
        except Exception:
            return False

    @staticmethod
    def is_firewall_blocked(html: str, status_code: Optional[int], headers: Dict[str, str]) -> bool:
        try:
            if not EnhancedCloudflareDetector.is_cloudflare_server(headers):
                return False
            if status_code != 403:
                return False
            return bool(re.search(
                r'<span class="cf-error-code">1020</span>', html, re.M | re.DOTALL
            ))
        except Exception:
            return False

    @staticmethod
    def detect_challenge_type(html: str, status_code: Optional[int], headers: Dict[str, str]) -> ChallengeType:
        # Firewall
        if EnhancedCloudflareDetector.is_firewall_blocked(html, status_code, headers):
            return ChallengeType.FIREWALL_1020
        # Turnstile (перевіряємо раніше)
        if EnhancedCloudflareDetector.is_turnstile_challenge(html, status_code, headers):
            return ChallengeType.TURNSTILE
        # Captcha v2
        if EnhancedCloudflareDetector.is_captcha_v2_challenge(html, status_code, headers):
            return ChallengeType.CAPTCHA_V2
        # Captcha v1
        if EnhancedCloudflareDetector.is_captcha_challenge(html, status_code, headers):
            return ChallengeType.CAPTCHA_V1
        # IUAM v2
        if EnhancedCloudflareDetector.is_iuam_v2_challenge(html, status_code, headers):
            return ChallengeType.IUAM_V2
        # IUAM v1
        if EnhancedCloudflareDetector.is_iuam_challenge(html, status_code, headers):
            return ChallengeType.IUAM_V1
        
        return ChallengeType.NONE


class EnhancedCloudflarePlugin(BaseDriverPlugin):
    """
    Покращений плагін для обходу Cloudflare захисту.

    Features:
    - Автоматичний Turnstile solver (без зовнішніх сервісів)
    - Human-like mouse movements та clicks
    - Retry з exponential backoff
    - Cookie persistence для уникнення повторних challenges

    Конфігурація:
        wait_timeout: Максимальний час очікування (default: 45s)
        check_interval: Інтервал перевірки (default: 0.5s)
        auto_solve_turnstile: Автоматично вирішувати Turnstile (default: True)
        human_interaction: Human-like взаємодія (default: True)
        max_retries: Максимум повторних спроб (default: 3)

    Приклад:
        plugin = EnhancedCloudflarePlugin(EnhancedCloudflarePlugin.config(
            wait_timeout=60,
            auto_solve_turnstile=True
        ))
    """

    @property
    def name(self) -> str:
        return "enhanced_cloudflare"

    def get_hooks(self) -> List[str]:
        return [
            BrowserStage.NAVIGATION_COMPLETED,
            BrowserStage.CONTENT_READY,
        ]

    async def _get_response_info(self, page, ctx: BrowserContext) -> Tuple[str, Optional[int], Dict[str, str]]:
        try:
            html = await page.content()
            status_code = ctx.status_code
            headers = {}
            if ctx.response:
                try:
                    response_headers = await ctx.response.all_headers()
                    headers = dict(response_headers)
                except Exception:
                    headers = ctx.response_headers or {}
            return html, status_code, headers
        except Exception as e:
            logger.debug(f"Error getting response info: {e}")
            return "", None, {}

    async def _detect_cloudflare(self, page, ctx: BrowserContext) -> ChallengeType:
        try:
            html, status_code, headers = await self._get_response_info(page, ctx)
            return EnhancedCloudflareDetector.detect_challenge_type(html, status_code, headers)
        except Exception as e:
            logger.debug(f"Error detecting Cloudflare: {e}")
            return ChallengeType.NONE

    async def _human_mouse_move(self, page, target_x: float, target_y: float):
        """Human-like mouse movement до цільової точки."""
        try:
            # Отримуємо поточну позицію (або центр viewport)
            viewport = page.viewport_size
            if viewport:
                current_x = viewport["width"] / 2
                current_y = viewport["height"] / 2
            else:
                current_x, current_y = 500, 300

            # Кількість кроків
            steps = random.randint(15, 30)
            
            for i in range(steps):
                # Bezier-подібний рух
                t = i / steps
                # Додаємо невеликий noise
                noise_x = random.uniform(-3, 3)
                noise_y = random.uniform(-3, 3)
                
                x = current_x + (target_x - current_x) * t + noise_x
                y = current_y + (target_y - current_y) * t + noise_y
                
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.005, 0.02))

            # Фінальний рух до точної позиції
            await page.mouse.move(target_x, target_y)
            
        except Exception as e:
            logger.debug(f"Mouse move error: {e}")

    async def _solve_turnstile(self, page, ctx: BrowserContext) -> bool:
        """
        Автоматичне вирішення Turnstile challenge.
        
        Turnstile зазвичай вирішується автоматично, якщо:
        1. Браузер виглядає як справжній (stealth mode)
        2. Є human-like взаємодія
        """
        if not self.config.get("auto_solve_turnstile", True):
            return False

        logger.info("🔄 Attempting to solve Turnstile challenge...")

        try:
            # Шукаємо Turnstile iframe або checkbox
            turnstile_selectors = [
                'iframe[src*="challenges.cloudflare.com/turnstile"]',
                'iframe[src*="turnstile"]',
                '.cf-turnstile iframe',
                '#cf-turnstile iframe',
                'input[name="cf-turnstile-response"]',
            ]

            turnstile_element = None
            for selector in turnstile_selectors:
                try:
                    turnstile_element = await page.wait_for_selector(
                        selector, timeout=5000, state="visible"
                    )
                    if turnstile_element:
                        logger.debug(f"Found Turnstile element: {selector}")
                        break
                except Exception:
                    continue

            if not turnstile_element:
                # Можливо Turnstile ще завантажується
                await asyncio.sleep(2)
                
                # Спробуємо знайти знову
                for selector in turnstile_selectors:
                    try:
                        turnstile_element = await page.wait_for_selector(
                            selector, timeout=3000, state="visible"
                        )
                        if turnstile_element:
                            break
                    except Exception:
                        continue

            if turnstile_element:
                # Human-like взаємодія
                if self.config.get("human_interaction", True):
                    # Рухаємо мишу по сторінці
                    await self._simulate_human_behavior(page)

                # Отримуємо bounding box
                box = await turnstile_element.bounding_box()
                if box:
                    # Клікаємо в центр з невеликим offset
                    click_x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
                    click_y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
                    
                    # Human-like mouse movement
                    await self._human_mouse_move(page, click_x, click_y)
                    
                    # Невелика пауза перед кліком
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    # Клік
                    await page.mouse.click(click_x, click_y)
                    logger.info("✅ Clicked on Turnstile checkbox")
                    
                    # Чекаємо на вирішення довше
                    await asyncio.sleep(3)
                    
                    # Перевіряємо чи є cf-turnstile-response
                    try:
                        response_input = await page.query_selector('input[name="cf-turnstile-response"]')
                        if response_input:
                            response_value = await response_input.get_attribute('value')
                            if response_value:
                                logger.info("✅ Turnstile response token detected")
                                return True
                    except Exception:
                        pass
                    
                    return True
            
            logger.info("⏳ Waiting for Turnstile auto-solve...")
            return True

        except Exception as e:
            logger.warning(f"Turnstile solve error: {e}")
            return False

    async def _simulate_human_behavior(self, page):
        """Швидка симуляція людської поведінки (оптимізовано)."""
        try:
            viewport = page.viewport_size
            if not viewport:
                return

            width = viewport["width"]
            height = viewport["height"]

            # Тільки 1-2 рухи миші замість 2-5
            for _ in range(random.randint(1, 2)):
                x = random.uniform(100, width - 100)
                y = random.uniform(100, height - 100)
                await page.mouse.move(x, y, steps=random.randint(3, 5))
                await asyncio.sleep(0.05)

        except Exception:
            pass

    async def _wait_for_challenge_completion(
        self, page, ctx: BrowserContext, challenge_type: ChallengeType
    ) -> bool:
        """Очікує завершення Cloudflare challenge з exponential backoff."""
        
        wait_timeout = self.config.get("wait_timeout", 60)
        base_interval = self.config.get("check_interval", 0.5)
        max_retries = self.config.get("max_retries", 3) 

        logger.info(
            f"⏳ Waiting for Cloudflare {challenge_type.value} challenge "
            f"(max {wait_timeout}s)..."
        )

        # Якщо це Turnstile - спробуємо вирішити
        if challenge_type == ChallengeType.TURNSTILE:
            await self._solve_turnstile(page, ctx)

        elapsed = 0
        check_count = 0
        retry_count = 0

        while elapsed < wait_timeout:
            check_interval = base_interval * (1 + check_count * 0.1)
            check_interval = min(check_interval, 3.0)
            
            await asyncio.sleep(check_interval)
            elapsed += check_interval
            check_count += 1

            # Перевіряємо статус
            current_type = await self._detect_cloudflare(page, ctx)

            if current_type == ChallengeType.NONE:
                logger.info(f"✅ Cloudflare challenge passed after {elapsed:.1f}s")
                return True

            # Firewall - фатальна помилка
            if current_type == ChallengeType.FIREWALL_1020:
                logger.error("🚫 Cloudflare Firewall 1020 block detected")
                return False

            # Якщо тип змінився - перезапускаємо процес
            if current_type != challenge_type:
                logger.info(f"Challenge type changed: {challenge_type.value} -> {current_type.value}")
                challenge_type = current_type
                
                if current_type == ChallengeType.TURNSTILE:
                    await self._solve_turnstile(page, ctx)

            # Періодичний retry для Turnstile
            if challenge_type == ChallengeType.TURNSTILE and elapsed > 5 and retry_count < max_retries:
                if check_count % 10 == 0:  # Кожні ~5 секунд
                    retry_count += 1
                    logger.info(f"🔄 Retry Turnstile (attempt {retry_count}/{max_retries})")
                    await self._solve_turnstile(page, ctx)
                    # Додаткове очікування після спроби
                    await asyncio.sleep(2)

            # Логування прогресу
            if check_count % 10 == 0:
                logger.debug(f"⏳ Still waiting... ({elapsed:.1f}s/{wait_timeout}s)")

        logger.warning(
            f"⏰ Cloudflare challenge timeout after {wait_timeout}s for {ctx.url}"
        )
        # Встановлюємо прапорець failed для skip цього URL
        ctx.data["cloudflare_failed"] = True
        return False

    async def on_navigation_completed(self, ctx: BrowserContext) -> BrowserContext:
        """Перевіряє наявність Cloudflare challenge після навігації."""
        if not ctx.page:
            return ctx

        try:
            challenge_type = await self._detect_cloudflare(ctx.page, ctx)

            if challenge_type == ChallengeType.NONE:
                return ctx

            # Зберігаємо інформацію
            ctx.data["cloudflare_detected"] = True
            ctx.data["cloudflare_challenge_type"] = challenge_type.value

            logger.warning(f"🛡️ Cloudflare {challenge_type.value} detected on {ctx.url}")
            ctx.emit("cloudflare_detected", url=ctx.url, challenge_type=challenge_type.value)

            # Firewall - одразу виходимо
            if challenge_type == ChallengeType.FIREWALL_1020:
                logger.error(f"🚫 Cloudflare Firewall blocked: {ctx.url}")
                ctx.emit("cloudflare_blocked", url=ctx.url, error_code=1020)
                ctx.data["cloudflare_blocked"] = True
                return ctx

            # Очікуємо завершення
            if await self._wait_for_challenge_completion(ctx.page, ctx, challenge_type):
                ctx.emit("cloudflare_passed", url=ctx.url, challenge_type=challenge_type.value)
                ctx.data["cloudflare_passed"] = True
                
                # Оновлюємо HTML
                ctx.html = await ctx.page.content()
                
                # Зберігаємо cookies для майбутніх запитів
                cookies = await ctx.context.cookies() if ctx.context else []
                ctx.data["cloudflare_cookies"] = cookies
            else:
                ctx.emit("cloudflare_failed", url=ctx.url, challenge_type=challenge_type.value)
                ctx.data["cloudflare_failed"] = True

        except Exception as e:
            logger.error(f"Error in Cloudflare handling: {e}")
            ctx.errors.append(e)

        return ctx

    async def on_content_ready(self, ctx: BrowserContext) -> BrowserContext:
        """Фінальна перевірка на Cloudflare challenge."""
        if not ctx.page:
            return ctx

        # Якщо вже обробляли - пропускаємо
        if ctx.data.get("cloudflare_detected"):
            return ctx

        try:
            challenge_type = await self._detect_cloudflare(ctx.page, ctx)

            if challenge_type == ChallengeType.NONE:
                return ctx

            # Late detection
            logger.warning(f"🛡️ Late Cloudflare {challenge_type.value} detection on {ctx.url}")
            ctx.data["cloudflare_detected"] = True
            ctx.data["cloudflare_challenge_type"] = challenge_type.value
            ctx.emit("cloudflare_detected", url=ctx.url, challenge_type=challenge_type.value)

            if challenge_type == ChallengeType.FIREWALL_1020:
                ctx.emit("cloudflare_blocked", url=ctx.url, error_code=1020)
                ctx.data["cloudflare_blocked"] = True
                return ctx

            if await self._wait_for_challenge_completion(ctx.page, ctx, challenge_type):
                ctx.emit("cloudflare_passed", url=ctx.url)
                ctx.data["cloudflare_passed"] = True
                ctx.html = await ctx.page.content()
            else:
                ctx.emit("cloudflare_failed", url=ctx.url)
                ctx.data["cloudflare_failed"] = True

        except Exception as e:
            logger.error(f"Error in Cloudflare content check: {e}")
            ctx.errors.append(e)

        return ctx
