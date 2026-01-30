"""Trust module exceptions."""


class TrustError(Exception):
    """Base trust error."""
    pass


class SigningError(TrustError):
    """Signing failed."""
    pass


class VerificationError(TrustError):
    """Verification failed."""
    pass
