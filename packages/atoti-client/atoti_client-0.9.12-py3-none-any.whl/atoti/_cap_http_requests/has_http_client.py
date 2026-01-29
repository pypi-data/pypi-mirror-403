from abc import ABC, abstractmethod

import httpx


class HasHttpClient(ABC):
    @property
    @abstractmethod
    def http_client(self) -> httpx.Client: ...
