import os
import argparse
from runners.archive_spoltest import ArchiveSpoltest
from runners.loggly_spoltest import LogglySpoltest

ROOT_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')

parser = argparse.ArgumentParser()
parser.add_argument('--domain', '-d', help="The domain to run requests agains. I.E https.example.com", type= str)
parser.add_argument('--file', '-f', help="The inputfile containing rows with a relative url under the specified domain", type=str)
parser.add_argument('--requests-in-parallel', '-rip', nargs='+', help="Number of requests which should run in paralell. Provides a list, to test multiple runs.", type=int, default=[1])
parser.add_argument('--test-request-count-after-cached', '-rert', help="Specifies how many times each request should be run after the cache is triggered. Defaults to 0, so no extra requests is done. I.E if a cache should be triggered", type= int, default=0)
parser.add_argument('--should-follow-redirects', '-sfr', help="Test the request result url if the requests returns a 301 status code", type= bool, default=False)
parser.add_argument('--meta-file', '-mf', help="File containing css selctors for parsing the tested requets's DOM", type= str, default=os.path.join(ROOT_DIR, 'meta.json'))
parser.add_argument('--timeout-between-each-chunk', '-tbec', help="Sets the timeout between each chunk. I.E if only 1 requests-in-parallel, this would be between each request. If requests-in-parallel > it would be between each 'group'.", type=int, default=0)
parser.add_argument('--pdf-report', '-pr', help="Generate pdf report", type=bool, default=False)
parser.add_argument('--loggly-token', '-lt', help="Token for loggly", type=bool, default='')



if __name__ == '__main__':
    args = parser.parse_args()

    domain = args.domain
    logfile = args.file
    requests_in_parallel = args.requests_in_parallel
    test_request_count_after_cached =  args.test_request_count_after_cached
    should_follow_redirects = args.should_follow_redirects
    meta_file =  args.meta_file
    generate_pdf_report =  args.pdf_report
    timeout_between_each_chunk = args.timeout_between_each_chunk
    loggly_token = args.loggly_token

    if not os.path.isfile(logfile):
        print(f"File {logfile} is not a file or path is wrong...")
        exit


    LOGGLY_URL = f'https://logs-01.loggly.com/inputs/{loggly_token}'

    for request_in_parallel in requests_in_parallel:
        if generate_pdf_report:
            test = ArchiveSpoltest(domain, logfile, request_in_parallel, test_request_count_after_cached, should_follow_redirects, meta_file, timeout_between_each_chunk, OUTPUT_DIR)
            test.run()
        if loggly_token:
            test =  LogglySpoltest(domain, logfile, request_in_parallel, test_request_count_after_cached, should_follow_redirects, meta_file, timeout_between_each_chunk, LOGGLY_URL)
            test.run()
