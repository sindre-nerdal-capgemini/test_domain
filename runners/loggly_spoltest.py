import datetime
import os
import requests

from dataclasses import dataclass, field
from typing import List

from models.benchmark import Benchmark
from models.request import  Request

from runners.spoltest import Spoltest
import json

@dataclass
class Log:
    timestamp: datetime.datetime
    benchmarks: List[Benchmark] = field(default_factory=list)

    def serialize(self):
        return {
            'timestamp': self.timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            'logs': [x.serialize() for x in self.benchmarks]
        }

class LogglySpoltest(Spoltest):
    def __init__(self, domain, url_file, request_in_parallel, test_request_count_after_cached, should_follow_redirects, dom_meta_file, timeout_between_each_chunk, loggly_url):
        super().__init__(domain, url_file, request_in_parallel, test_request_count_after_cached, should_follow_redirects, dom_meta_file, timeout_between_each_chunk)
        self.results = []
        self.loggly_url = loggly_url

    def handle_tests_after_each_chunk(self, tested_benchmarks):
        self.results += tested_benchmarks


    def before_run(self):
        pass


    def after_run(self):
        log = Log(datetime.datetime.now(), self.results)
        print(log.serialize())
        loggly_request = requests.post(self.loggly_url, json=log.serialize())
        if loggly_request.status_code == 200:
            print("Posted results to loggly")
        else:
            print("Could not post results to loggly..")