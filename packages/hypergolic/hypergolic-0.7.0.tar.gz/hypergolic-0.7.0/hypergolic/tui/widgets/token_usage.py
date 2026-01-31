from dataclasses import dataclass


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    def format_header(self) -> str:
        parts = []

        if self.input_tokens:
            parts.append(f"Input: {self.input_tokens:,}")

        if self.output_tokens:
            parts.append(f"Output: {self.output_tokens:,}")

        cache_parts = []
        if self.cache_read_tokens:
            cache_parts.append(f"{self.cache_read_tokens:,} read")
        if self.cache_creation_tokens:
            cache_parts.append(f"{self.cache_creation_tokens:,} write")

        if cache_parts:
            parts.append(f"Cache: {', '.join(cache_parts)}")

        if not parts:
            return ""

        return f"({', '.join(parts)})"

    @classmethod
    def from_api_usage(cls, usage) -> TokenUsage:
        if usage is None:
            return cls()

        return cls(
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        )
