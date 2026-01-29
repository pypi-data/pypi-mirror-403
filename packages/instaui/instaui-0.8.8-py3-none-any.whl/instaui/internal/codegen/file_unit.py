from dataclasses import dataclass
from typing import List
from instaui.internal.ast.core import ComponentDef


@dataclass
class FileUnit:
    path: str  # "components/Foo.js"
    components: List[ComponentDef]
    is_entry: bool = False
