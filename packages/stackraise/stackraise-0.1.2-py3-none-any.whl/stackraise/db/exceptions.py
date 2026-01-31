from __future__ import annotations
import stackraise.db as db

class NotFoundError(Exception):
    """Exception raised when a document is not found in the database."""

    def __init__(self, ref: db.Document.Ref):
        super().__init__(f"Document with reference {ref} not found.")
        self.ref = ref
