from abc import ABC, abstractclassmethod, abstractmethod


class APIHandler(ABC):
    def __init__(self) -> None:
        self.DEFAULT_PAGE_LIMIT = 3     # Max number of pages to look at

    @classmethod
    @abstractmethod
    def get_all(cls, start_page, media_type, all_: bool = False, retry_once: bool = True):
        pass