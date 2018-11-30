import csv
import sys
import statistics
import datetime

class TestResult:

    def __init__(self, test_start, test_end, domain, requests_in_parallel=1, show_none_200_as_error=False, show_cached_result=False):
        self.requests_in_parallel = requests_in_parallel
        self.test_start = test_start
        self.test_end = test_end
        self.domain = domain
        self.status = {}
        self.show_none_200_as_error = show_none_200_as_error
        self.number_of_requests = 0
        self.errors = []
        self.response_times = []
        self.cached_response_times = []
        self.show_cached_result = show_cached_result

    def run(self, file_path: str, extra_tries: int = 0):

        with open(file_path, newline='') as csvfile:
            csv_rows = csv.reader(csvfile, delimiter=',')
            headers = next(csv_rows)

            # Index of headers
            RESPONSE_TIME = headers.index('Response time')
            STATUS_CODE = headers.index('Status code')
            SIZE = headers.index('Size')
            LOCATION = headers.index('Location')
            LOG_LINE = headers.index('Log line number')
            TIMESTAMP = headers.index('Executed')
            REQUEST = headers.index('Requested url')

            for row in csv_rows:
                self.number_of_requests += 1
                # Extract each column from each row
                log_line = row[LOG_LINE]
                timestamp = row[TIMESTAMP]
                request_url = row[REQUEST]
                location_url = row[LOCATION]
                status_code = row[STATUS_CODE]
                size = row[SIZE]
                response_time = row[RESPONSE_TIME]

                if len(row) > 7:
                    extra_requests = (len(row) - 7) // 4

                    if self.show_cached_result:
                        for extra in range(extra_requests - len(self.cached_response_times)):
                            self.cached_response_times.append([])

                        for req in range(extra_requests):
                            cached_response_time = row[headers.index(f'Response time(cached {req+1})')]
                            self.cached_response_times[req].append(int(cached_response_time))

                if status_code == '-1':
                    self.errors.append((request_url, location_url))
                else:
                    try:
                        self.status[status_code] = self.status[status_code] + 1
                    except KeyError:
                        self.status[status_code] = 1

                    if self.show_none_200_as_error and int(status_code) >= 300:
                        self.errors.append((request_url, status_code))

                self.response_times.append(int(response_time))


    def status_codes_in_sorted_list(self):
        return [self.requests_in_parallel ,self.number_of_requests] + [self.status[key] for key in sorted(self.status.keys())]

    def statistics(self):
        stats = [['First request', sum(self.response_times), statistics.median(sorted(self.response_times)), sum(self.response_times) // len(self.response_times) ]]
        for index, cached_response in enumerate(self.cached_response_times):
            index += 1
            stats.append([f'After triggered cache {index}', sum(cached_response), statistics.median(sorted(cached_response)), sum(cached_response) // len(cached_response)])
        return stats


if __name__ == '__main__':
    test = TestResult(0, datetime.datetime.now(), datetime.datetime.now() ,"domain")
    try:
        file_name = sys.argv[1]
    except:
        print("Need a valid file path")

    try:
        tries = sys.argv[2]
    except:
        tries = 0

    test.run(file_name, tries)
