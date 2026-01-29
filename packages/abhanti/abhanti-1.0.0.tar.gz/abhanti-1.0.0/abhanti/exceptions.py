"""Custom exceptions"""


class AbhantiError(Exception):
    """Base exception"""
    pass


class ProviderError(AbhantiError):
    """Provider error"""
    pass


class ConfigError(AbhantiError):
    """Config error"""
    pass
