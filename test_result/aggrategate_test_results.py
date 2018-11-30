from generator.pdf_generator import PDFGenerator

class AggregateTestResults:

    def __init__(self, output_file, test_results):
        self.output_file = output_file
        self.generator = PDFGenerator(output_file)
        self.test_results = test_results

    def create_status_code_section(self):
        status_codes = []
        status_codes_headers = ["Test", "Total"] + sorted(self.test_results[0].status.keys())

        for test in self.test_results:
            status_codes.append(test.status_codes_in_sorted_list())

        return self.generator.generate_table(status_codes, status_codes_headers, "Status code", ["Encountered statuscodes during testing"])

    def create_statistics_section(self):
        stats = []
        stats_headers = ["Request number", "Total", "Mean", "Average"]

        for test in self.test_results:
            stats.append(test.statistics())

        stats_tables = []
        for test_index, s in enumerate(stats):
            parallell_requests = self.test_results[test_index].requests_in_parallel

            explaination = [f"Results after running {parallell_requests} requests in parallel.", "All values is in ms."]
            table_title = f"{parallell_requests} in parallel"
            stats_tables.append(self.generator.generate_table(s, stats_headers, table_title, explaination))

        return stats_tables

    def create_errors_table(self):
        errors = []
        errors_headers = ['Test', 'Url', 'Error']

        for test in self.test_results:
            for url, err in test.errors:
                errors.append([test.requests_in_parallel, url, err])

        explaination = [f"Errors encountered during testing."]
        return self.generator.generate_table(errors, errors_headers, "Errors", explaination)


    def run(self):
        if not self.test_results:
            print("no results")
            return

        tests_start = self.test_results[0].test_start
        tests_end = self.test_results[-1].test_end

        # Header
        self.generator.add_header("Testresults")
        self.generator.add_space(40)

        # Details
        self.generator.add_readonly_field("Test(s) started", tests_start.strftime("%Y-%m-%d %H:%M:%S"))
        self.generator.add_readonly_field("Test(s) ended", tests_end.strftime("%Y-%m-%d %H:%M:%S"))
        self.generator.add_readonly_field("Domain", self.test_results[0].domain)
        self.generator.add_readonly_field("Tests with number of requests in parallel", [result.requests_in_parallel for result in self.test_results])

        # Tables
        self.generator.add_content(self.create_status_code_section())
        self.generator.add_space(40)

        for stats_table in self.create_statistics_section():
            self.generator.add_content(stats_table)
            self.generator.add_space(40)
        if any(test.errors for test in self.test_results):
            self.generator.add_content(self.create_errors_table())

        self.generator.generate_pdf()