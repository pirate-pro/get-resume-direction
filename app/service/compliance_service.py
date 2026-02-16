from app.models.source import Source


class ComplianceService:
    def validate_source_allowed(self, source: Source) -> None:
        if not source.enabled:
            raise PermissionError(f"Source disabled: {source.code}")
        if not source.robots_allowed:
            raise PermissionError(f"robots policy disallows source: {source.code}")

    def should_pause_for_risk(self, error_message: str) -> bool:
        risk_words = ("captcha", "forbidden", "403", "blocked", "ban")
        msg = error_message.lower()
        return any(word in msg for word in risk_words)
