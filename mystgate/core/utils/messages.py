def message(subject: str, outcome: str, *causes: str) -> str:
    """Format a structured subject, outcome, and optional causes message."""
    base = f"{subject}: {outcome}"
    parts = [cause.strip() for cause in causes if cause.strip()]
    if not parts:
        return base
    return f"{base} ({', '.join(parts)})"
