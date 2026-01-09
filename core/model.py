from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class Page:
    title: str
    controls: list  # length 3


@dataclass
class Effect:
    name: str
    pages: List[Page]
    params: Dict[str, Any]

    enabled: bool = True
    page_index: int = 0
    control_index: int = 0  # 0..2

    def current_page(self) -> Page:
        return self.pages[self.page_index]

    def current_control(self):
        return self.current_page().controls[self.control_index]
