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
from utilities.file_handler import readFromlog, save_file
from abc import ABC, abstractmethod

STATUS_CODES = {
    '200': 'OK',
    '307': 'Temporary Redirect',
    '400': 'Bad Request',
    '404': 'Not Found',
}

class Spoltest(ABC):

    def __init__(self, domain: str, request_in_parallel: int = 1, test_request_count_after_cached: int = 0, should_follow_redirects: bool = False, dom_meta_file: str = None, timeout_between_each_chunk: int = 0, output_dir: str=''):
        self.domain = domain
        self.files = []
        self.request_in_parallel = request_in_parallel
        self.test_request_count_after_cached = test_request_count_after_cached
        self.should_follow_redirects = should_follow_redirects
        self.parse_dom = dom_meta_file is not None
        self.dom_meta_file = dom_meta_file
        self.timeout_between_each_chunk = timeout_between_each_chunk
        self.output_dir = output_dir
        self.search_for_errors = []
        self.error_meta = []
        self.test_run_start = None
        self.test_run_end = None
        self.domain_name = domain.replace("https://", "").replace("http://", "")


        if self.parse_dom:
            try:
                with open(self.dom_meta_file) as f:
                    try:
                        file = json.load(f, encoding='utf-8')
                        self.search_for_errors = file.get('search_for_errors', [])
                        self.error_meta = file.get('error_metas', [])
                    except:
                        pass
            except:
                print(f"Could not get metas from file {self.dom_meta_file}")
                self.parse_dom = False

    def parse_html(self, req):
        parser = etree.HTMLParser()
        tree   = etree.HTML(req.text)

        document_errors = []

        for item in self.search_for_errors:
            should_be_present_in_dom = item.get('should_be_present_in_dom', True)
            document_error = {
                'should_be_present_in_dom': should_be_present_in_dom,
                'description': item.get('description'),
                'method': item.get('method'),
                'path': item.get('path')
                }

            if item.get('method') == 'css_selector':
                self.parse_html_by_css_selectors(item, req.content, document_error)
            elif item.get('method') == 'xpath':
                self.parse_html_by_xpath(item, tree, document_error)

            if document_error.get('should_be_present_in_dom') and not document_error.get('exists_in_dom'):
                document_errors.append(document_error)
            elif not document_error.get('should_be_present_in_dom') and document_error.get('exists_in_dom'):
                document_errors.append(document_error)

        meta = {}
        if document_errors:
            meta = self.parse_html_error_meta(tree)

        return document_errors, meta

    def parse_html_error_meta(self, tree):
        error_metas = {}
        for error_meta in self.error_meta:
            path = error_meta.get('path')
            name = error_meta.get('name')

            if not path or not name:
                continue
            element = tree.find(path)
            if element is not None and element.text:
                error_metas[name] = element.text
        return error_metas

    def parse_html_by_xpath(self, item, tree, document_error):

        document_error['attributes'] = []
        document_error['content'] = ''
        document_error['exists_in_dom'] = False
        try:
            elm = tree.xpath(item.get('path'))
            if elm:
                document_error['exists_in_dom'] = True
                try:
                    document_error['content'] = elm[0].text_content()
                except:
                    pass
                try:
                    document_error['attributes'] = [{x[0]: x[1]} for x in elm[0].attrib.items()]
                except:
                    pass
        except:
            pass


    def parse_html_by_css_selectors(self, item, content, document_error):
        soup = BeautifulSoup(content, "html.parser")
        node = soup.select_one(item.get('path'))

        if node:
            document_error['exists_in_dom'] = True
            document_error['attributes'] = node.attrs
            document_error['content'] = node.text
        else:
            document_error['exists_in_dom'] = False
            document_error['attributes'] = []
            document_error['content'] = ''

    def add_error_meta(self, req):
        parser = etree.HTMLParser()
        tree   = etree.HTML(req.text)

        document_metas = {}
        title = tree.find(".//div[@class='c-article__header']//h1")
        content_type = tree.find(".//div[@class='c-article__title c-article__title--icon']//p")
        topic_title = tree.find(".//h1[@class='c-resources__topic-title']")

        if title is not None and title.text:
            document_metas['title'] = title.text
        if content_type is not None and content_type.text:
            document_metas['content_type'] = content_type.text
        if topic_title is not None and topic_title.text:
            document_metas['topic_title'] = topic_title.text


        return document_metas




    def test_request(self, benchmark: Benchmark, request_id=None):
        """
        Exectutes a request on a benchmark and times the response time.
        Then the repsonsetime, size of the document, status code and location header is saved on the benchmark object.
        """
        start = time.time()
        benchmark.timestamp = datetime.datetime.now()
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

            status_message= STATUS_CODES[str(req.status_code)]
            if req.status_code == 200:
                errors, error_meta = self.parse_html(req)
            else:
                errors = []
                error_meta = []


            return Request(location, req.status_code, size, response_time, errors, error_meta, request_id, status_message=status_message)


    def run_speedtest_for_benchmark(self, mark: Benchmark):
        """
        Tests a benchmark
        If the tests returns a 301 or 302, then the test is run again against the location header in the response.
        This is done a maximum of 5 times or to the repsonse gives a 200 status.
        Each new test creates a new benchmark.

        Returns:
            List of all the tested benchmarks
        """
        resource_key = '/resource:'
        if resource_key in mark.request_url:
            splitted_by_colon = mark.request_url.split(':')
            request_id = splitted_by_colon[-1]

        tested_benchmarks = [mark]
        for _ in range(5):
            testable_mark = tested_benchmarks[-1]
            try:
                testable_mark.timestamp = datetime.datetime.now()
                testable_mark.test = self.test_request(testable_mark, request_id)
                # Do additional tests after triggered the server cache
                if self.test_request_count_after_cached > 0:
                    testable_mark.cachedRequests = []
                    for _ in range(self.test_request_count_after_cached):
                        testable_mark.cachedRequests.append(self.test_request(testable_mark, request_id))

            except Exception as e:
                testable_mark.test = Request(f"Error {e}", -1, -1, -1)
                tested_benchmarks.append(testable_mark)

            if self.should_follow_redirects and 301 <= testable_mark.test.status_code <= 302:
                new_mark = Benchmark(testable_mark.test.url, testable_mark.log_line_number)
                tested_benchmarks.append(new_mark)
            else:
                break

        return [x for x in tested_benchmarks if x.contains_errors()]


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

    def run_file(self, file):
        time_start = time.time()
        loop = asyncio.get_event_loop()
        chunk_index = 1
        log_lines_count = 0

        # Testloop which tests and persist a chunk from the logfile
        for benchmarks in readFromlog(file, self.request_in_parallel):
            chunk_time_start = time.time()
            log_lines_count += len(benchmarks)

            tested_marks = loop.run_until_complete(self.run_speedtest_for_list_of_benchmarks(benchmarks, self.request_in_parallel))
            self.handle_tests_after_each_chunk(tested_marks)

            chunk_time_end = time.time() - chunk_time_start
            #print(f'Completed prosessing chunk {chunk_index} with size {self.request_in_parallel} in {chunk_time_end} seconds')

            time.sleep(self.timeout_between_each_chunk)
            chunk_index += 1

        time_end = time.time() - time_start
        print(f'File {os.path.basename(file)}: Total time for {log_lines_count} log lines is {time_end} seconds.')

    def download_files(self):
        sitemap_name = 'sitemap.xml'
        sitemap = requests.get(f'{self.domain}/{sitemap_name}')
        save_file(os.path.join(self.output_dir, sitemap_name), sitemap.text)
        self.files = []

        with open(os.path.join(self.output_dir, sitemap_name)) as xml_file:
            sitemap_namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
            root    = etree.parse(xml_file)
            files = root.findall(f'.//{{{sitemap_namespace}}}sitemap')

            for f in files:
                location = f.find(f'.//{{{sitemap_namespace}}}loc')
                if not location.text:
                    continue

                filename = location.text.split('/')[-1]
                if filename.endswith('.xml'):
                    continue
                file_data = requests.get(location.text)
                file_path = os.path.join(self.output_dir, filename)
                save_file(file_path, file_data.text)
                self.files.append(file_path)

                print(f'Downloaded files: {filename}')
                break

    def run(self):
        self.test_run_start = datetime.datetime.now()
        self.before_run()

        self.download_files()

        for file in self.files:
            self.run_file(file)

        self.test_run_end = datetime.datetime.now()
        print(f'Total running time {self.test_run_end - self.test_run_start}')
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