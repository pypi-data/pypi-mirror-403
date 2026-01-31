from core.exceptions import SyncError


class IngestionIssue(Exception):
    """
    This exception is used to indicate an issue during the ingestion process.
    """

    # Store created issue object ID if it exists for this exception
    issue_id = None
    model_string: str = ""
    defaults: dict[str, str] = {}
    coalesce_fields: dict[str, str] = {}

    def __init__(
        self, model_string: str, data: dict, context: dict = None, issue_id=None
    ):
        super().__init__()
        self.model_string = model_string
        self.data = data
        context = context or {}
        self.defaults = context.pop("defaults", {})
        self.coalesce_fields = context
        self.issue_id = issue_id


class SearchError(IngestionIssue, LookupError):
    def __init__(self, message: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message

    def __str__(self):
        return self.message


class SyncDataError(IngestionIssue, SyncError):
    def __str__(self):
        return f"Sync failed for {self.model_string}: coalesce_fields={self.coalesce_fields} defaults={self.defaults}."


class IPAddressDuplicateError(IngestionIssue, SyncError):
    def __str__(self):
        return f"IP address {self.data.get('address')} already exists in {self.model_string} with coalesce_fields={self.coalesce_fields}."


class IPAddressPrimaryRemovalError(IngestionIssue, SyncError):
    def __str__(self):
        return "Error removing primary IP from other device."


class IPAddressPrimaryAssignmentError(IngestionIssue, SyncError):
    def __str__(self):
        return "Error assigning primary IP to device."


class RequiredDependencyFailedSkip(SearchError):
    """Raised when a required dependency failed, causing this item to be skipped."""
