from datetime import datetime
from dataclasses import dataclass, field
from typing import List
from .request import Request

@dataclass
class Benchmark:
    request_url: str
    log_line_number: int
    timestamp: datetime = None
    test: Request = None
    cachedRequests: List[Request] = field(default_factory=list)


    def to_csv(self):
        cachedRequestsCSV = []
        if self.cachedRequests:
            for cached in self.cachedRequests:
                cachedRequestsCSV += cached.to_csv()

        return [self.log_line_number, self.timestamp, self.request_url.rstrip()] + self.test.to_csv() + cachedRequestsCSV

    @staticmethod
    def headers():
        return ['Log line number', 'Executed', 'Requested url', 'Location', 'Status code', 'Size', 'Response time']

    def serialize(self):
        d =  {
            'request_url': self.request_url,
            'log_line_number': self.log_line_number,
            'timestamp': self.timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            'request': self.test.serialize()
        }
        if self.cachedRequests:
            d['cachedRequests'] = [x.serialize() for x in self.cachedRequests]
        return d