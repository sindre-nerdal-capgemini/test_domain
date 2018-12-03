import datetime
import sys
import time
import os
import multiprocessing
import asyncio
import concurrent.futures
import argparse
import subprocess
from timeit import default_timer as timer
from bs4 import BeautifulSoup
from lxml import etree
import json
import requests
import re


from models.benchmark import Benchmark
from models.request import  Request
from utilities.file_handler import readFromlog
from abc import ABC, abstractmethod

class Spoltest(ABC):

    def __init__(self, domain: str, url_file: str, request_in_parallel: int = 1, test_request_count_after_cached: int = 0, should_follow_redirects: bool = False, dom_meta_file: str = None, timeout_between_each_chunk: int = 0):
        self.domain = domain
        self.url_file = url_file
        self.request_in_parallel = request_in_parallel
        self.test_request_count_after_cached = test_request_count_after_cached
        self.should_follow_redirects = should_follow_redirects
        self.parse_dom = dom_meta_file is not None
        self.dom_meta_file = dom_meta_file
        self.timeout_between_each_chunk = timeout_between_each_chunk

        self.metas = []
        self.test_run_start = None
        self.test_run_end = None
        self.domain_name = domain.replace("https://", "").replace("http://", "")


        if self.parse_dom:
            try:
                with open(self.dom_meta_file) as f:
                    try:
                        self.metas = json.load(f, encoding='utf-8').get('metas')

                        if not (self.metas or isinstance(self.metas, list)):
                            self.metas = []
                    except:
                        self.metas = []
            except:
                print(f"Could not get metas from file {self.dom_meta_file}")
                self.metas = []
                self.parse_dom = False

    def parse_html(self, req):
        parser = etree.HTMLParser()
        tree   = etree.HTML(req.text)

        document_metas = []

        for item in self.metas:
            should_be_present_in_dom = item.get('should_be_present_in_dom', True)
            document_meta = {
                'should_be_present_in_dom': should_be_present_in_dom,
                'description': item.get('description')
                }

            if item.get('css_selector'):
                document_meta['css_selector'] = item.get('css_selector')
                self.parse_html_by_css_selectors(item, req.content, document_meta)
            elif item.get('xpath'):
                document_meta['xpath'] = item.get('xpath')
                self.parse_html_by_xpath(item, tree, document_meta)

            document_metas.append(document_meta)

        return document_metas

    def parse_html_by_xpath(self, item, tree, document_meta):

        document_meta['attributes'] = []
        document_meta['content'] = ''
        document_meta['exists_in_dom'] = False
        try:
            elm = tree.xpath(item.get('xpath'))
            if elm:
                document_meta['exists_in_dom'] = True
                try:
                    document_meta['content'] = elm[0].text_content()
                except:
                    pass
                try:
                    document_meta['attributes'] = [{x[0]: x[1]} for x in elm[0].attrib.items()]
                except:
                    pass
        except:
            pass


    def parse_html_by_css_selectors(self, item, content, document_meta):
        soup = BeautifulSoup(content, "html.parser")
        node = soup.select_one(item.get('css_selector'))

        if node:
            document_meta['exists_in_dom'] = True
            document_meta['attributes'] = node.attrs
            document_meta['content'] = node.text
        else:
            document_meta['exists_in_dom'] = False
            document_meta['attributes'] = []
            document_meta['content'] = ''

    def test_request(self, benchmark: Benchmark):
        """
        Exectutes a request on a benchmark and times the response time.
        Then the repsonsetime, size of the document, status code and location header is saved on the benchmark object.
        """
        start = time.time()
        with requests.get(benchmark.request_url, allow_redirects=False) as req:
            response_time = (time.time() - start) * 1000
            size = sum(len(chunk) for chunk in req.iter_content())
            req_location = req.headers.get("location", "")
            if not req_location:
                location = ''
            elif req_location.startswith('http'):
                location = req_location
            else:
                location = f'{self.domain}{req_location}'

            request_id = None
            resource_key = '/resource:'
            if resource_key in benchmark.request_url:
                splitted_by_colon = benchmark.request_url.split(':')
                request_id = splitted_by_colon[-1]

            if req.status_code == 200:
                metas = self.parse_html(req)
            else:
                metas = []
            return Request(location, req.status_code, size, response_time, metas, request_id)


    def run_speedtest_for_benchmark(self, mark: Benchmark):
        """
        Tests a benchmark
        If the tests returns a 301 or 302, then the test is run again against the location header in the response.
        This is done a maximum of 5 times or to the repsonse gives a 200 status.
        Each new test creates a new benchmark.

        Returns:
            List of all the tested benchmarks
        """
        tested_benchmarks = [mark]
        for _ in range(5):
            testable_mark = tested_benchmarks[-1]
            try:
                testable_mark.timestamp = datetime.datetime.now()
                testable_mark.test = self.test_request(testable_mark)
                # Do additional tests after triggered the server cache
                if self.test_request_count_after_cached > 0:
                    testable_mark.cachedRequests = []
                    for _ in range(self.test_request_count_after_cached):
                        testable_mark.cachedRequests.append(self.test_request(testable_mark))

            except Exception as e:
                testable_mark.test = Request(f"Error {e}", -1, -1, -1)

            if self.should_follow_redirects and 301 <= testable_mark.test.status_code <= 302:
                new_mark = Benchmark(testable_mark.test.url, testable_mark.log_line_number)
                tested_benchmarks.append(new_mark)
            else:
                break
        return tested_benchmarks

    async def run_speedtest_for_list_of_benchmarks(self, marks, workers: int):
        """
        Does a test agains a list of benchmarks.

        Returns:
            The list of tested benchmarks, but now also containing the benchmark results.
        """
        result = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:

            loop = asyncio.get_event_loop()
            futures = [loop.run_in_executor(
                    executor,
                    self.run_speedtest_for_benchmark,
                    b
                ) for b in marks]

            for res in await asyncio.gather(*futures):
                for line in res:
                    result.append(line)
        return result


    def run(self):
        self.test_run_start = datetime.datetime.now()
        self.before_run()

        time_start = time.time()
        loop = asyncio.get_event_loop()
        chunk_index = 1
        log_lines_count = 0

        # Testloop which tests and persist a chunk from the logfile
        for benchmarks in readFromlog(self.url_file, self.request_in_parallel, self.domain):
            chunk_time_start = time.time()
            log_lines_count += len(benchmarks)

            tested_marks = loop.run_until_complete(self.run_speedtest_for_list_of_benchmarks(benchmarks, self.request_in_parallel))
            self.handle_tests_after_each_chunk(tested_marks)

            chunk_time_end = time.time() - chunk_time_start
            print(f'Completed prosessing chunk {chunk_index} with size {self.request_in_parallel} in {chunk_time_end} seconds')

            time.sleep(self.timeout_between_each_chunk)
            chunk_index += 1

        time_end = time.time() - time_start
        print(f'Total time for {log_lines_count} log lines is {time_end} seconds.')
        self.test_run_end = datetime.datetime.now()
        self.after_run()

    @abstractmethod
    def handle_tests_after_each_chunk(self, tested_marks):
        pass

    @abstractmethod
    def before_run(self):
        pass

    @abstractmethod
    def after_run(self):
        pass