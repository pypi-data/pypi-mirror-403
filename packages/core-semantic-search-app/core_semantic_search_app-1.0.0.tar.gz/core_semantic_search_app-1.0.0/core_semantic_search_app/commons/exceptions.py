""" Semantic Search Exceptions
"""


class SemanticSearchError(Exception):
    """Exception raised by the Semantic Search app."""

    def __init__(self, message):
        self.message = message
