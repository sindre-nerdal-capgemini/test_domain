import datetime
import os

from models.benchmark import Benchmark
from models.request import  Request

from utilities.file_handler import saveAsCsv, saveHeadersAsCsv
from test_result.aggrategate_test_results import AggregateTestResults
from test_result.test_results import TestResult
from runners.spoltest import Spoltest

class ArchiveSpoltest(Spoltest):
    def __init__(self, domain, url_file, chrome_driver_path, request_in_parallel, test_request_count_after_cached, should_follow_redirects, dom_meta_file, timeout_between_each_chunk, output_dir):
        super().__init__(domain, url_file, chrome_driver_path, request_in_parallel, test_request_count_after_cached, should_follow_redirects, dom_meta_file, timeout_between_each_chunk)
        self.output_root_dir = output_dir
        self.output_dir = self.output_root_dir
        self.output_file = None


    def handle_tests_after_each_chunk(self, tested_benchmarks):
        saveAsCsv(self.output_file, tested_benchmarks)

    def after_run(self):
        test_results = []



        test_result = TestResult(self.test_run_start, self.test_run_end, self.domain, self.request_in_parallel, show_none_200_as_error=True, show_cached_result=self.test_request_count_after_cached > 1)
        test_result.run(self.output_file, self.test_request_count_after_cached)
        test_results.append(test_result)


        pfd_file = f'test_results_{self.domain_name}_{self.test_run_start.strftime("%d.%m.%Y")}.pdf'
        aggregate = AggregateTestResults(os.path.join(self.output_dir, pfd_file), test_results)
        aggregate.run()


    def before_run(self):
        self.output_dir = os.path.join(self.output_root_dir, self.test_run_start.strftime('%d.%m.%Y %H.%M'))
        if os.path.exists(self.output_dir):
            self.output_dir = os.path.join(self.output_root_dir, self.test_run_start.strftime('%d.%m.%Y %H.%M.%S'))

        os.makedirs(self.output_dir)

        output_file_name = f'test_{self.domain_name}_{self.request_in_parallel}_{self.test_run_start.strftime("%d.%m.%Y")}.csv'
        self.output_file = os.path.join(self.output_dir, output_file_name)

        # Creates csv headers
        headers = Benchmark.headers()
        for cached_request_number in range(self.test_request_count_after_cached):
            headers += Request.headers(cached_request_number + 1)
        saveHeadersAsCsv(self.output_file, headers)