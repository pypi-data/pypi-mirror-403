from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class SourceSpan:
    file: str
    line: int
    function: str | None
    column: int | None = None

    def __str__(self) -> str:
        if self.column is not None:
            loc = f"{self.file}:{self.line}:{self.column}"
        else:
            loc = f"{self.file}:{self.line}"

        if self.function:
            return f"{loc} in {self.function}()"
        return loc
