import logging


class IndentedFormatter(logging.Formatter):
    def indent(self, record: logging.LogRecord, text: str) -> str:
        """Prefix text with two spaces per nesting level attached to the record."""
        depth = getattr(record, "log_depth", 0)
        if not isinstance(depth, int) or depth <= 0:
            return text
        return f"{'  ' * depth}{text}"
