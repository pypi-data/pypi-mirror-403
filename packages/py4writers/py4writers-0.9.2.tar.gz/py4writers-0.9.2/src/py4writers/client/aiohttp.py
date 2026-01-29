from json import encoder
import ssl
import typing
import json
import certifi
import aiohttp
from aiohttp import ClientSession, TCPConnector

if typing.TYPE_CHECKING:
    from aiohttp import ClientResponse


class AiohttpClient:
    def __init__(
        self,
        session: ClientSession | None = None,
        timeout: aiohttp.ClientTimeout | None = None,
        **session_params: typing.Any,
    ) -> None:
        self.session = session
        self.session_params = session_params
        self.timeout = timeout or aiohttp.ClientTimeout(total=30)  # 30 секунд по умолчанию
        self._session_owner = session is None  # Флаг: мы создали сессию или получили извне

    def __repr__(self) -> str:
        return "<{}: session={!r}, timeout={}, closed={}>".format(
            self.__class__.__name__,
            self.session,
            self.timeout,
            True if self.session is None else self.session.closed,
        )

    async def request_raw(
        self,
        url: str,
        method: str = "GET",
        data: dict[str, typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> "ClientResponse":
        if not self.session:
            self.session = ClientSession(
                connector=TCPConnector(
                    ssl=ssl.create_default_context(cafile=certifi.where())
                ),
                json_serialize=json.dumps,
                **self.session_params,
            )
        response = await self.session.request(
            url=url,
            method=method,
            data=data,
            timeout=self.timeout,
            **kwargs,
        )
        # Читаем тело, чтобы соединение можно было переиспользовать
        await response.read()
        # Освобождаем соединение обратно в пул
        response.release()
        return response

    async def request_json(
        self,
        url: str,
        method: str = "GET",
        data: dict[str, typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> dict[str, typing.Any]:
        response = await self.request_raw(url, method, data, **kwargs)
        return await response.json(
            encoding="UTF-8",
            loads=json.loads,
            content_type=None,
        )

    async def request_text(
        self,
        url: str,
        method: str = "GET",
        data: dict[str, typing.Any] | aiohttp.FormData | None = None,
        **kwargs: typing.Any,
    ) -> str:
        response = await self.request_raw(url, method, data, **kwargs)  # type: ignore
        return await response.text(encoding="UTF-8")

    async def request_bytes(
        self,
        url: str,
        method: str = "GET",
        data: dict[str, typing.Any] | aiohttp.FormData | None = None,
        **kwargs: typing.Any,
    ) -> bytes:
        response = await self.request_raw(url, method, data, **kwargs)  # type: ignore
        if response._body is None:
            await response.read()
        return response._body or bytes()

    async def request_content(
        self,
        url: str,
        method: str = "GET",
        data: dict[str, typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> bytes:
        response = await self.request_raw(url, method, data, **kwargs)
        return response._body or bytes()

    async def close(self) -> None:
        """Закрывает сессию, если мы её владельцы."""
        if self._session_owner and self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self) -> "AiohttpClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - автоматически закрывает сессию."""
        await self.close()

    @classmethod
    def get_form(
        cls,
        data: dict[str, typing.Any],
        files: dict[str, tuple[str, bytes]] | None = None,
    ) -> aiohttp.formdata.FormData:
        files = files or {}
        form = aiohttp.formdata.FormData(quote_fields=False)

        for k, v in data.items():
            form.add_field(k, encoder.encode(v) if not isinstance(v, str) else v)

        for n, (filename, content) in files.items():
            form.add_field(n, content, filename=filename)

        return form

    def __del__(self) -> None:
        """Убираем антипаттерн __del__ - используйте async context manager вместо этого."""
        # Оставляем только для backward compatibility, но лучше использовать async with
        if self._session_owner and self.session and not self.session.closed:
            try:
                if self.session._connector is not None and self.session._connector_owner:
                    self.session._connector.close()
                self.session._connector = None
            except Exception:
                pass  # Игнорируем ошибки в __del__


__all__ = ("AiohttpClient",)
