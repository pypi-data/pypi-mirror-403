"""Refactored API class with improved architecture."""
import asyncio
import json
import logging
import random
from typing import List, Optional, AsyncIterator

import aiohttp

from ..client.aiohttp import AiohttpClient
from ..types.models import File, Order
from ..const import Get, Post, USER_AGENT, MAX_CONCURRENT_REQUESTS
from ..exceptions import AuthenticationError, SessionExpiredError, NetworkError
from ..parsers import OrderParser
from ..utils import async_retry, RateLimiter

logger = logging.getLogger(__name__)


class API:
    """
    Refactored API для работы с 4writers.net.

    Улучшения:
    - Context manager для автоматического закрытия ресурсов
    - Rate limiting для предотвращения блокировок
    - Retry логика для сетевых ошибок
    - Разделение ответственности (парсинг вынесен в OrderParser)
    - Улучшенная обработка ошибок
    """

    def __init__(
        self,
        login: Optional[str] = None,
        password: Optional[str] = None,
        session: Optional[str] = None,
        max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS,
    ):
        """
        Args:
            login: Логин для авторизации
            password: Пароль для авторизации
            session: Готовая сессия (если уже авторизованы)
            max_concurrent_requests: Максимум параллельных запросов
        """
        self._login = login
        self._password = password
        self._session = session
        self.http_client = AiohttpClient()
        self.parser = OrderParser()
        self.rate_limiter = RateLimiter(max_concurrent=max_concurrent_requests)
        self._is_authenticated = session is not None

    async def __aenter__(self) -> "API":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - автоматически закрывает ресурсы."""
        await self.close()

    async def close(self) -> None:
        """Закрывает HTTP клиент и освобождает ресурсы."""
        await self.http_client.close()

    @async_retry(max_attempts=3, delay=1.0, exceptions=(NetworkError,))
    async def login(self) -> None:
        """
        Авторизация через login и password.

        Raises:
            AuthenticationError: Если авторизация не удалась
            NetworkError: Если произошла ошибка сети
        """
        if not self._login or not self._password:
            raise AuthenticationError("Login and password are required for authentication.")

        try:
            response = await self.http_client.request_raw(
                url=Post.LOGIN,
                method="POST",
                headers={
                    "User-Agent": USER_AGENT,
                    "Referer": Post.LOGIN,
                },
                data={"login": self._login, "password": self._password},
            )

            if response.status != 200:
                raise AuthenticationError(f"Login failed with status {response.status}")

            session_cookie = response.cookies.get("session")
            if session_cookie:
                self._session = session_cookie.value
                self._is_authenticated = True
                logger.debug("Authentication successful")
            else:
                raise AuthenticationError("Session ID not found in response")

        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise NetworkError(f"Network error during login: {e}") from e

    def _get_auth_headers(self, extra_headers: Optional[dict] = None) -> dict:
        """
        Возвращает заголовки с авторизацией.

        Args:
            extra_headers: Дополнительные заголовки

        Returns:
            Словарь заголовков
        """
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"session={self._session}",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    async def _ensure_authenticated(self) -> None:
        """
        Проверяет авторизацию и переавторизуется при необходимости.

        Raises:
            SessionExpiredError: Если сессия истекла и не удалось переавторизоваться
        """
        if not self._is_authenticated:
            if self._login and self._password:
                logger.debug("Session not authenticated, attempting to login")
                await self.login()
            else:
                raise SessionExpiredError(
                    "Session not authenticated and credentials not provided"
                )

    @staticmethod
    def _generate_ajax_id() -> str:
        """Генерирует случайный X-Ajax-Id как в браузере."""
        return str(random.randint(10000000000000000, 99999999999999999))

    async def _send_tracker(self, action: str, order_index: int) -> None:
        """
        Отправляет данные на tracker.php перед действием с заказом.

        Args:
            action: Действие (например, "take")
            order_index: Индекс заказа
        """
        tracker_data = {
            "title": "",
            "url": "/index2.php",
            "get": {"mode": "free_orders"},
            "post": {"action": action, "index": str(order_index)},
            "action": "index2.php?mode=free_orders",
            "method": "post",
            "fields": {
                "action": {"type": "hidden", "title": "action", "value": action},
                "index": {"type": "hidden", "title": "index", "value": str(order_index)},
            },
        }

        try:
            await self.http_client.request_raw(
                url=Post.TRACKER,
                method="POST",
                headers=self._get_auth_headers({
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-Ajax-Id": self._generate_ajax_id(),
                }),
                data=None,
                json=tracker_data,
            )
            logger.debug(f"Tracker sent for action={action}, order_index={order_index}")
        except Exception as e:
            logger.warning(f"Failed to send tracker: {e}")

    @async_retry(max_attempts=2, delay=1.0, exceptions=(NetworkError,))
    async def fetch_order_details(
        self, order_index: int, is_completed: bool = False
    ) -> Optional[str]:
        """
        Получает описание заказа.

        Args:
            order_index: Индекс заказа
            is_completed: Флаг выполненного заказа

        Returns:
            Описание заказа или None
        """
        await self._ensure_authenticated()

        try:
            url = (
                Get.FETCH_COMPLETED_ORDER_DETAILS if is_completed else Get.FETCH_ORDERS
            )
            response = await self.http_client.request_raw(
                url=url,
                method="POST",
                data={"action": "view", "index": str(order_index)},
                headers=self._get_auth_headers({"Referer": url}),
            )

            if response.status != 200:
                logger.error(f"Failed to fetch order details for {order_index}: {response.status}")
                return None

            html = await response.text()
            return self.parser.parse_description_from_html(html)

        except Exception as e:
            logger.error(f"Error fetching order details: {e}")
            raise NetworkError(f"Failed to fetch order details: {e}") from e

    @async_retry(max_attempts=2, delay=1.0, exceptions=(NetworkError,))
    async def get_order_files(self, order_index: int) -> List[File]:
        """
        Получает список файлов заказа.

        Args:
            order_index: Индекс заказа

        Returns:
            Список файлов
        """
        await self._ensure_authenticated()

        try:
            url = Get.ORDER_FILES.format(order_index=order_index)
            response = await self.http_client.request_raw(
                url=url,
                method="GET",
                headers=self._get_auth_headers({
                    "Referer": url,
                    "X-Requested-With": "XMLHttpRequest",
                }),
            )

            if response.status != 200:
                logger.error(f"Failed to fetch files for order {order_index}: {response.status}")
                return []

            html = await response.text()
            files = self.parser.parse_files_from_html(html)
            logger.debug(f"Found {len(files)} files for order {order_index}")
            return files

        except Exception as e:
            logger.warning(f"Error fetching order files: {e}")
            return []

    @async_retry(max_attempts=3, delay=1.0, exceptions=(NetworkError,))
    async def download_file(self, file_id: int) -> bytes:
        """
        Скачивает файл по ID.

        Args:
            file_id: ID файла

        Returns:
            Байты файла
        """
        await self._ensure_authenticated()

        try:
            url = Get.DOWNLOAD_FILE.format(file_id=file_id)
            response = await self.http_client.request_raw(
                url=url,
                method="GET",
                headers=self._get_auth_headers({"Referer": url}),
            )

            if response.status != 200:
                logger.error(f"Failed to download file {file_id}: {response.status}")
                return bytes()

            file_bytes = response._body or bytes()
            logger.debug(f"Downloaded file {file_id} ({len(file_bytes)} bytes)")
            return file_bytes

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise NetworkError(f"Failed to download file: {e}") from e

    @async_retry(max_attempts=2, delay=1.0, exceptions=(NetworkError,))
    async def take_order(self, order_index: int) -> bool:
        """
        Берёт заказ в работу.

        Args:
            order_index: Индекс заказа

        Returns:
            True если заказ взят успешно
        """
        await self._ensure_authenticated()

        try:
            # 1. Отправляем данные на tracker (как делает браузер)
            await self._send_tracker("take", order_index)

            # 2. Отправляем запрос на взятие заказа с multipart/form-data
            form_data = aiohttp.FormData()
            form_data.add_field("action", "take")
            form_data.add_field("index", str(order_index))

            response = await self.http_client.request_raw(
                url=Post.TAKE_ORDER,
                method="POST",
                data=form_data,
                headers=self._get_auth_headers({
                    "Referer": "https://4writers.net/welcome/",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-Ajax-Id": self._generate_ajax_id(),
                }),
            )

            if response.status != 200:
                logger.error(f"Failed to take order {order_index}: {response.status}")
                return False

            response_text = await response.text()

            if "Now you can write this order" in response_text:
                logger.debug(f"Successfully took order {order_index}")
                return True
            else:
                logger.warning(f"Failed to take order {order_index}")
                return False

        except Exception as e:
            logger.error(f"Error taking order: {e}")
            return False

    async def _fetch_orders_with_details(
        self,
        orders: List[Order],
        is_completed: bool = False,
    ) -> List[Order]:
        """
        Параллельно загружает детали и файлы для списка заказов с rate limiting.

        Args:
            orders: Список заказов
            is_completed: Флаг выполненных заказов

        Returns:
            Обновлённый список заказов с деталями
        """
        # Создаём задачи с rate limiting
        detail_tasks = [
            self.rate_limiter.execute(
                self.fetch_order_details(order.order_index, is_completed=is_completed)
            )
            for order in orders
        ]

        file_tasks = [
            self.rate_limiter.execute(self.get_order_files(order.order_index))
            for order in orders
        ]

        # Выполняем параллельно
        descriptions = await asyncio.gather(*detail_tasks, return_exceptions=True)
        files_list = await asyncio.gather(*file_tasks, return_exceptions=True)

        # Заполняем данные
        for order, desc, files in zip(orders, descriptions, files_list):
            order.description = desc if not isinstance(desc, Exception) else None
            order.files = files if not isinstance(files, Exception) else None

        return orders

    async def get_orders(
        self,
        page: int = 1,
        page_size: int = 50,
        category: str = "essay",
    ) -> List[Order]:
        """
        Получает список доступных заказов.

        Args:
            page: Номер страницы
            page_size: Количество заказов на странице
            category: Категория заказов

        Returns:
            Список заказов
        """
        await self._ensure_authenticated()

        try:
            # Формируем URL с параметрами
            url = f"{Get.ORDERS.split('?')[0]}?mode=free_orders&category={category}&page={page}&pagesize={page_size}&showpages=0"

            response = await self.http_client.request_raw(
                url=url,
                method="GET",
                headers=self._get_auth_headers({
                    "Referer": url,
                    "X-Requested-With": "XMLHttpRequest",
                }),
            )

            if response.status != 200:
                logger.error(f"Failed to fetch orders: {response.status}")
                return []

            html_content = await response.text()
            orders = self.parser.parse_orders_from_html(html_content, is_completed=False)

            if not orders:
                logger.debug("No orders found")
                return []

            # Загружаем детали параллельно с rate limiting
            orders = await self._fetch_orders_with_details(orders, is_completed=False)

            logger.debug(f"Fetched {len(orders)} orders")
            return orders

        except Exception as e:
            logger.error(f"Error fetching orders: {e}", exc_info=True)
            raise NetworkError(f"Failed to fetch orders: {e}") from e

    async def get_completed_orders(
        self,
        page: int = 1,
    ) -> List[Order]:
        """
        Получает список выполненных заказов.

        Args:
            page: Номер страницы (если поддерживается)

        Returns:
            Список выполненных заказов
        """
        await self._ensure_authenticated()

        try:
            response = await self.http_client.request_raw(
                url=Get.COMPLETED_ORDERS,
                method="GET",
                headers=self._get_auth_headers({"Referer": Get.COMPLETED_ORDERS}),
            )

            if response.status != 200:
                logger.error(f"Failed to fetch completed orders: {response.status}")
                return []

            html_content = await response.text()
            orders = self.parser.parse_orders_from_html(html_content, is_completed=True)

            if not orders:
                logger.debug("No completed orders found")
                return []

            # Загружаем детали параллельно с rate limiting
            orders = await self._fetch_orders_with_details(orders, is_completed=True)

            logger.debug(f"Fetched {len(orders)} completed orders")
            return orders

        except Exception as e:
            logger.error(f"Error fetching completed orders: {e}", exc_info=True)
            raise NetworkError(f"Failed to fetch completed orders: {e}") from e


    async def get_active_orders(
        self,
        order_type: str = "processing",
    ) -> List[Order]:
        """
        Получает список активных заказов (в работе).

        Args:
            order_type: Тип активных заказов (processing, revision, etc.)

        Returns:
            Список активных заказов
        """
        await self._ensure_authenticated()

        try:
            url = f"{Get.ACTIVE_ORDERS.split('&type=')[0]}&type={order_type}"
            response = await self.http_client.request_raw(
                url=url,
                method="GET",
                headers=self._get_auth_headers({
                    "Referer": url,
                    "X-Requested-With": "XMLHttpRequest",
                }),
            )

            if response.status != 200:
                logger.error(f"Failed to fetch active orders: {response.status}")
                return []

            html_content = await response.text()
            orders = self.parser.parse_orders_from_html(html_content, is_completed=False)

            if not orders:
                logger.debug("No active orders found")
                return []

            # Загружаем детали параллельно с rate limiting
            orders = await self._fetch_orders_with_details(orders, is_completed=False)

            logger.debug(f"Fetched {len(orders)} active orders")
            return orders

        except Exception as e:
            logger.error(f"Error fetching active orders: {e}", exc_info=True)
            raise NetworkError(f"Failed to fetch active orders: {e}") from e
    async def iter_orders(
        self,
        page: int = 1,
        page_size: int = 50,
        category: str = "essay",
        max_pages: Optional[int] = None,
    ) -> AsyncIterator[Order]:
        """
        Генератор для получения заказов по одному (streaming).

        Args:
            page: Начальная страница
            page_size: Количество заказов на странице
            category: Категория заказов
            max_pages: Максимальное количество страниц (None = все)

        Yields:
            Order: Заказ с деталями и файлами

        Example:
            async for order in api.iter_orders(page=1, max_pages=3):
                print(f"Order: {order.title}")
        """
        await self._ensure_authenticated()

        current_page = page
        pages_fetched = 0

        while True:
            if max_pages and pages_fetched >= max_pages:
                break

            try:
                # Получаем страницу заказов
                url = f"{Get.ORDERS.split('?')[0]}?mode=free_orders&category={category}&page={current_page}&pagesize={page_size}&showpages=0"

                response = await self.http_client.request_raw(
                    url=url,
                    method="GET",
                    headers=self._get_auth_headers({
                        "Referer": url,
                        "X-Requested-With": "XMLHttpRequest",
                    }),
                )

                if response.status != 200:
                    logger.error(f"Failed to fetch orders page {current_page}: {response.status}")
                    break

                html_content = await response.text()
                orders = self.parser.parse_orders_from_html(html_content, is_completed=False)

                if not orders:
                    logger.debug(f"No more orders on page {current_page}")
                    break

                logger.debug(f"Processing {len(orders)} orders from page {current_page}")

                # Отдаем заказы по одному с деталями
                for order in orders:
                    # Загружаем детали и файлы
                    try:
                        description_task = self.rate_limiter.execute(
                            self.fetch_order_details(order.order_index, is_completed=False)
                        )
                        files_task = self.rate_limiter.execute(
                            self.get_order_files(order.order_index)
                        )

                        description, files = await asyncio.gather(
                            description_task,
                            files_task,
                            return_exceptions=True
                        )

                        if not isinstance(description, Exception) and description:
                            order.description = description
                        if not isinstance(files, Exception) and files:
                            order.files = files

                    except Exception as e:
                        logger.warning(f"Failed to fetch details for order {order.order_index}: {e}")

                    yield order

                current_page += 1
                pages_fetched += 1

            except Exception as e:
                logger.error(f"Error fetching orders page {current_page}: {e}", exc_info=True)
                break

    async def iter_completed_orders(
        self,
        page: int = 1,
        max_pages: Optional[int] = None,
    ) -> AsyncIterator[Order]:
        """
        Генератор для получения выполненных заказов по одному (streaming).

        Args:
            page: Начальная страница
            max_pages: Максимальное количество страниц (None = все)

        Yields:
            Order: Выполненный заказ с деталями и файлами

        Example:
            async for order in api.iter_completed_orders():
                print(f"Completed: {order.title}")
        """
        await self._ensure_authenticated()

        current_page = page
        pages_fetched = 0

        while True:
            if max_pages and pages_fetched >= max_pages:
                break

            try:
                response = await self.http_client.request_raw(
                    url=Get.COMPLETED_ORDERS,
                    method="GET",
                    headers=self._get_auth_headers({"Referer": Get.COMPLETED_ORDERS}),
                )

                if response.status != 200:
                    logger.error(f"Failed to fetch completed orders: {response.status}")
                    break

                html_content = await response.text()
                orders = self.parser.parse_orders_from_html(html_content, is_completed=True)

                if not orders:
                    logger.debug("No more completed orders")
                    break

                logger.debug(f"Processing {len(orders)} completed orders")

                # Отдаем заказы по одному с деталями
                for order in orders:
                    # Загружаем детали и файлы
                    try:
                        description_task = self.rate_limiter.execute(
                            self.fetch_order_details(order.order_index, is_completed=True)
                        )
                        files_task = self.rate_limiter.execute(
                            self.get_order_files(order.order_index)
                        )

                        description, files = await asyncio.gather(
                            description_task,
                            files_task,
                            return_exceptions=True
                        )

                        if not isinstance(description, Exception) and description:
                            order.description = description
                        if not isinstance(files, Exception) and files:
                            order.files = files

                    except Exception as e:
                        logger.warning(f"Failed to fetch details for order {order.order_index}: {e}")

                    yield order

                # Для completed orders пагинация может не поддерживаться
                # Прекращаем после первой страницы
                break

            except Exception as e:
                logger.error(f"Error fetching completed orders: {e}", exc_info=True)
                break

    async def iter_order_files(self, order_index: int) -> AsyncIterator[File]:
        """
        Генератор для получения файлов заказа по одному (streaming).

        Args:
            order_index: Индекс заказа

        Yields:
            File: Файл заказа

        Example:
            async for file in api.iter_order_files(order_index=2569038):
                file_bytes = await api.download_file(file.id)
                save_file(file.name, file_bytes)
        """
        await self._ensure_authenticated()

        try:
            url = Get.ORDER_FILES.format(order_index=order_index)
            response = await self.http_client.request_raw(
                url=url,
                method="GET",
                headers=self._get_auth_headers({
                    "Referer": url,
                    "X-Requested-With": "XMLHttpRequest",
                }),
            )

            if response.status != 200:
                logger.error(f"Failed to fetch files for order {order_index}: {response.status}")
                return

            html = await response.text()
            files = self.parser.parse_files_from_html(html)

            logger.debug(f"Found {len(files)} files for order {order_index}")

            for file in files:
                yield file

        except Exception as e:
            logger.warning(f"Error fetching order files: {e}")

    async def iter_active_orders(
        self,
        order_type: str = "processing",
        max_pages: Optional[int] = None,
    ) -> AsyncIterator[Order]:
        """
        Генератор для получения активных заказов по одному (streaming).

        Args:
            order_type: Тип активных заказов (processing, revision, etc.)
            max_pages: Максимальное количество страниц (None = все)

        Yields:
            Order: Активный заказ с деталями и файлами

        Example:
            async for order in api.iter_active_orders(order_type="processing"):
                print(f"Active: {order.title}")
        """
        await self._ensure_authenticated()

        pages_fetched = 0

        while True:
            if max_pages and pages_fetched >= max_pages:
                break

            try:
                url = f"{Get.ACTIVE_ORDERS.split('&type=')[0]}&type={order_type}"
                response = await self.http_client.request_raw(
                    url=url,
                    method="GET",
                    headers=self._get_auth_headers({
                        "Referer": url,
                        "X-Requested-With": "XMLHttpRequest",
                    }),
                )

                if response.status != 200:
                    logger.error(f"Failed to fetch active orders: {response.status}")
                    break

                html_content = await response.text()
                orders = self.parser.parse_orders_from_html(html_content, is_completed=False)

                if not orders:
                    logger.debug("No more active orders")
                    break

                logger.debug(f"Processing {len(orders)} active orders")

                # Отдаем заказы по одному с деталями
                for order in orders:
                    # Загружаем детали и файлы
                    try:
                        description_task = self.rate_limiter.execute(
                            self.fetch_order_details(order.order_index, is_completed=False)
                        )
                        files_task = self.rate_limiter.execute(
                            self.get_order_files(order.order_index)
                        )

                        description, files = await asyncio.gather(
                            description_task,
                            files_task,
                            return_exceptions=True
                        )

                        if not isinstance(description, Exception) and description:
                            order.description = description
                        if not isinstance(files, Exception) and files:
                            order.files = files

                    except Exception as e:
                        logger.warning(f"Failed to fetch details for order {order.order_index}: {e}")

                    yield order

                # Для active orders пагинация может не поддерживаться
                break

            except Exception as e:
                logger.error(f"Error fetching active orders: {e}", exc_info=True)
                break

    # Convenience methods for different active order types
    
    async def get_processing_orders(self) -> List[Order]:
        """Получает заказы в работе (processing)."""
        return await self.get_active_orders(order_type="processing")
    
    async def get_revision_orders(self) -> List[Order]:
        """Получает заказы на ревизии (revision)."""
        return await self.get_active_orders(order_type="revision")
    
    async def get_late_orders(self) -> List[Order]:
        """Получает просроченные заказы (late)."""
        return await self.get_active_orders(order_type="late")
    
    async def iter_processing_orders(self, max_pages: Optional[int] = None) -> AsyncIterator[Order]:
        """Генератор для заказов в работе (processing)."""
        async for order in self.iter_active_orders(order_type="processing", max_pages=max_pages):
            yield order
    
    async def iter_revision_orders(self, max_pages: Optional[int] = None) -> AsyncIterator[Order]:
        """Генератор для заказов на ревизии (revision)."""
        async for order in self.iter_active_orders(order_type="revision", max_pages=max_pages):
            yield order
    
    async def iter_late_orders(self, max_pages: Optional[int] = None) -> AsyncIterator[Order]:
        """Генератор для просроченных заказов (late)."""
        async for order in self.iter_active_orders(order_type="late", max_pages=max_pages):
            yield order
