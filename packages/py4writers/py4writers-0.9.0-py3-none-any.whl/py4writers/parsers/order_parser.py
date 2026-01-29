"""HTML Parser for orders."""
import re
import logging
from typing import Dict, Callable, Optional, Any
from bs4 import BeautifulSoup, Tag

from ..types.models import Order, File
from ..exceptions import ParsingError

logger = logging.getLogger(__name__)


class OrderParser:
    """Парсер для заказов с сайта 4writers.net"""

    @staticmethod
    def safe_int(value_str: str) -> Optional[int]:
        """Безопасное преобразование в int."""
        try:
            return int(value_str.strip()) if value_str and value_str.strip() else None
        except (ValueError, AttributeError, TypeError):
            return None

    @staticmethod
    def safe_float(value_str: str) -> Optional[float]:
        """Безопасное преобразование в float."""
        try:
            cleaned = value_str.replace("$", "").replace(" ", "").replace("-", "").strip()
            # Убираем всё после '+' (preferred writer bonus)
            if "+" in cleaned:
                cleaned = cleaned.split("+")[0]
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError, TypeError):
            return None

    @staticmethod
    def get_field_mapping(is_completed: bool = False) -> Dict[str, Callable[[Tag], Any]]:
        """
        Возвращает mapping для извлечения полей из HTML.

        Args:
            is_completed: True для completed_orders, False для free_orders
        """
        safe_int = OrderParser.safe_int
        safe_float = OrderParser.safe_float

        # Базовый mapping для всех заказов
        mapping = {
            "title": lambda order: (
                order.find("div", class_="order_title").text.strip()
                if order.find("div", class_="order_title")
                else None
            ),
            "subject": lambda order: (
                order.find("div", class_="order_subject").text.strip()
                if order.find("div", class_="order_subject")
                else None
            ),
            "order_id": lambda order: (
                order.find("div", class_="order_id").find("span", class_="value").text.strip()
                if order.find("div", class_="order_id")
                   and order.find("div", class_="order_id").find("span", class_="value")
                else None
            ),
            "deadline": lambda order: (
                order.find("div", class_="deadline").find("span", class_="value").text.strip()
                if order.find("div", class_="deadline")
                else None
            ),
            "remaining": lambda order: (
                order.find("div", class_="remaining").text.strip()
                if order.find("div", class_="remaining")
                else None
            ),
            "order_type": lambda order: OrderParser._get_label_value(order, "Order type"),
            "academic_level": lambda order: OrderParser._get_label_value(order, "Academic level"),
            "style": lambda order: OrderParser._get_label_value(order, "Style"),
            "language": lambda order: OrderParser._get_label_value(order, "Language"),
            "pages": lambda order: safe_int(OrderParser._get_label_value(order, "Pages") or ""),
            "sources": lambda order: safe_int(OrderParser._get_label_value(order, "Sources") or ""),
            "salary": lambda order: safe_float(OrderParser._get_label_value(order, "Salary") or ""),
            "bonus": lambda order: safe_float(OrderParser._get_label_value(order, "Bonus") or ""),
            "total": lambda order: safe_float(OrderParser._get_label_value(order, "Total") or ""),
        }

        # order_index парсится по-разному для free и completed
        if is_completed:
            mapping["order_index"] = lambda order: OrderParser._parse_order_index_completed(order)
        else:
            mapping["order_index"] = lambda order: OrderParser._parse_order_index_free(order)

        # Дополнительные поля для completed orders
        if is_completed:
            mapping["editor_work"] = lambda order: OrderParser._parse_editor_work(order)
            mapping["your_payment"] = lambda order: safe_float(
                OrderParser._get_label_value(order, "Your payment") or ""
            )

        return mapping

    @staticmethod
    def _get_label_value(order: Tag, label: str) -> Optional[str]:
        """Получает значение по label из HTML."""
        label_cell = order.find("div", class_="label_cell", string=label)
        if label_cell:
            value_cell = label_cell.find_next_sibling("div")
            if value_cell:
                return value_cell.text.strip()
        return None

    @staticmethod
    def _parse_order_index_free(order: Tag) -> Optional[int]:
        """Парсит order_index для free_orders (формат: index: '12345')."""
        view_btn = order.find("a", title="View") or order.find("a", string="View")
        if not view_btn:
            return None

        onclick = view_btn.get("onclick", "")
        match = re.search(r"index:\s*'(\d+)'", onclick)
        return int(match.group(1)) if match else None

    @staticmethod
    def _parse_order_index_completed(order: Tag) -> Optional[int]:
        """Парсит order_index для completed_orders (формат: index: 12345)."""
        view_btn = order.find("a", title="View")
        if not view_btn:
            return None

        onclick = view_btn.get("onclick", "")
        match = re.search(r"index:\s*(\d+)", onclick)
        return int(match.group(1)) if match else None

    @staticmethod
    def _parse_editor_work(order: Tag) -> Optional[float]:
        """Парсит editor_work (может быть n/a)."""
        editor_work_str = OrderParser._get_label_value(order, "Editor's work")
        if not editor_work_str or "n/a" in editor_work_str.lower():
            return None
        return OrderParser.safe_float(editor_work_str)

    @staticmethod
    def parse_orders_from_html(html: str, is_completed: bool = False) -> list[Order]:
        """
        Парсит список заказов из HTML.

        Args:
            html: HTML контент страницы
            is_completed: True если это completed_orders

        Returns:
            Список объектов Order

        Raises:
            ParsingError: Если парсинг не удался
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            order_items = soup.find_all("div", class_="order-item")

            if not order_items:
                logger.info("No orders found in HTML")
                return []

            field_mapping = OrderParser.get_field_mapping(is_completed=is_completed)
            orders = []

            for order_html in order_items:
                try:
                    order_data = {
                        key: extractor(order_html)
                        for key, extractor in field_mapping.items()
                    }

                    # Добавляем поля, которые заполнятся позже
                    order_data["description"] = None
                    order_data["files"] = None

                    # Для free orders добавляем пустые поля completed
                    if not is_completed:
                        order_data["editor_work"] = None
                        order_data["your_payment"] = None

                    order = Order(**order_data)
                    orders.append(order)

                except Exception as e:
                    logger.warning(f"Failed to parse order: {e}", exc_info=True)
                    continue

            logger.info(f"Parsed {len(orders)} orders from HTML")
            return orders

        except Exception as e:
            raise ParsingError(f"Failed to parse orders HTML: {e}") from e

    @staticmethod
    def parse_files_from_html(html: str) -> list[File]:
        """
        Парсит список файлов из HTML.

        Args:
            html: HTML контент страницы с файлами

        Returns:
            Список объектов File
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            table = soup.find("table", class_="table")
            if not table:
                return []

            tbody = table.find("tbody")
            if not tbody:
                return []

            file_rows = tbody.find_all("tr")
            files = []

            for row in file_rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                file_date = cols[0].text.strip()
                file_author = cols[1].text.strip()
                file_link_tag = cols[2].find("a")

                if file_link_tag and "href" in file_link_tag.attrs:
                    file_name = file_link_tag.text.strip()
                    file_id_match = re.search(r"item=(\d+)", file_link_tag["href"])
                    file_id = int(file_id_match.group(1)) if file_id_match else None

                    if file_id:
                        files.append(
                            File(
                                date=file_date,
                                author=file_author,
                                name=file_name,
                                id=file_id,
                            )
                        )

            logger.info(f"Parsed {len(files)} files from HTML")
            return files

        except Exception as e:
            logger.warning(f"Failed to parse files: {e}")
            return []

    @staticmethod
    def parse_description_from_html(html: str) -> Optional[str]:
        """
        Парсит описание заказа из HTML.

        Args:
            html: HTML контент страницы с деталями заказа

        Returns:
            Описание заказа или None
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Ищем <td> с текстом "Description"
            desc_td = soup.find("td", string="Description")
            if desc_td:
                # Находим следующий <td> с описанием
                next_td = desc_td.find_next_sibling("td")
                if next_td:
                    return next_td.get_text(strip=True)
            return None
        except Exception as e:
            logger.warning(f"Failed to parse description: {e}")
            return None
