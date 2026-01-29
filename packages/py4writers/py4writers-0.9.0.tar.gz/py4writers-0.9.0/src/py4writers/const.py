class URL:
    """Base URLs"""
    BASE = "https://4writers.net"
    INDEX1 = f"{BASE}/index1.php"
    INDEX2 = f"{BASE}/index2.php"
    DOWNLOAD = f"{BASE}/download.php"
    LOGIN_PAGE = f"{BASE}/login/"


class Get:
    """GET endpoints"""
    ORDERS = f"{URL.INDEX1}?mode=free_orders&category=essay&page=1&pagesize=50&showpages=0"
    COMPLETED_ORDERS = f"{URL.INDEX1}?mode=completed_orders"
    ACTIVE_ORDERS = f"{URL.INDEX1}?mode=active_orders&type=processing"
    FETCH_ORDERS = f"{URL.INDEX2}?mode=free_orders"
    FETCH_COMPLETED_ORDER_DETAILS = f"{URL.INDEX2}?mode=completed_orders"
    FETCH_ACTIVE_ORDER_DETAILS = f"{URL.INDEX2}?mode=active_orders"
    ORDER_FILES = f"{URL.INDEX1}?mode=files&order={{order_index}}"
    DOWNLOAD_FILE = f"{URL.DOWNLOAD}?mode=files&item={{file_id}}"


class Post:
    """POST endpoints"""
    LOGIN = URL.LOGIN_PAGE
    TAKE_ORDER = f"{URL.INDEX2}?mode=free_orders"
    TRACKER = f"{URL.BASE}/tracker.php?type=save"


# HTTP Headers
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0 Safari/537.36 OPR/114.0.0.0"

# Rate limiting
MAX_CONCURRENT_REQUESTS = 10  # Максимум параллельных запросов
