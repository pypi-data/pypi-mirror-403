import typing
from typing_extensions import Self
from ..core.pydantic_utilities import pydantic_v1

T = typing.TypeVar("T")

class SyncPage(pydantic_v1.BaseModel, typing.Generic[T]):
    count : int
    has_next: bool
    items: typing.Optional[typing.List[T]]
    get_next: typing.Optional[typing.Callable[[], typing.Optional[Self]]]


# The main pagination classes that handle iteration
class SyncPager(SyncPage[T], typing.Generic[T]):
    def __iter__(self) -> typing.Iterator[T]:  # type: ignore
        for page in self.iter_pages():
            if page.items is not None:
                for item in page.items:
                    yield item

    def iter_pages(self) -> typing.Iterator[SyncPage[T]]:
        page: typing.Union[SyncPager[T], None] = self
        while True:
            if page is not None:
                yield page
                if page.has_next and page.get_next is not None:
                    page = page.get_next()
                    if page is None or page.items is None or len(page.items) == 0:
                        return
                else:
                    return
            else:
                return

    def next_page(self) -> typing.Optional[SyncPage[T]]:
        return self.get_next() if self.get_next is not None else None