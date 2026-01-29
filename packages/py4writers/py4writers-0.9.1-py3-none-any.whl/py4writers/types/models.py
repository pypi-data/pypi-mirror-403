from dataclasses import dataclass
from typing import List, Optional


@dataclass
class File:
    id: int
    name: str
    author: str
    date: str
    data: Optional[bytes] = None

    def get_download_url(self) -> str:
        """Возвращает ссылку для скачивания файла."""
        return f"https://4writers.net/download.php?mode=files&item={self.id}"


@dataclass
class Order:
    title: str
    subject: str
    order_id: str
    order_index: int
    description: str
    deadline: str
    remaining: str
    order_type: str
    academic_level: str
    style: str
    language: str
    pages: int
    sources: int
    salary: float
    bonus: float
    total: float
    files: Optional[List[File]] = None
    editor_work: Optional[float] = None
    your_payment: Optional[float] = None
