from datetime import datetime
from dataclasses import dataclass, field
from typing import List

@dataclass
class Request:
    """
    Dataclass containing
    """
    url: str
    status_code: int
    size_in_bytes: int
    response_time: int
    errors: List[dict] = field(default_factory=list)
    error_meta: dict = field(default_factory=dict)
    id: int = None
    status_message: str = None

    def to_csv(self):
        return [self.url, self.status_code, self.size_in_bytes, '{0:.0f}'.format(self.response_time), self.errors, self.error_meta, self.id]

    @staticmethod
    def headers(identifier: str):
        header = lambda x: f'{x}{f"(cached {identifier})"}'
        return [header('Location'), header('Status code'), header('Size'), header('Response time')]

    def serialize(self):
        return {
            'header location url': self.url,
            'size_in_bytes': self.size_in_bytes,
            'status_code': self.status_code,
            'response_time (ms)': self.response_time,
            'errors': self.errors,
            'errors_meta': self.error_meta,
            'id': self.id,
            'status_message': self.status_message
        }

    def contains_errors(self):
        return len(self.errors) > 0 or self.status_code < 200 or self.status_code > 302