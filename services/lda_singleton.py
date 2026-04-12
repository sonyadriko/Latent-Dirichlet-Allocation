"""
Singleton LDA Service Instance
Ensures all routers use the same LDA service instance
"""
from services.lda_service import LDAService

# Global singleton instance - shared across all routers
_lda_service_instance = None


def get_lda_service() -> LDAService:
    """Get the global LDA service singleton instance"""
    global _lda_service_instance
    if _lda_service_instance is None:
        _lda_service_instance = LDAService()
    return _lda_service_instance


def reset_lda_service():
    """Reset the global LDA service instance (useful for testing)"""
    global _lda_service_instance
    _lda_service_instance = None
