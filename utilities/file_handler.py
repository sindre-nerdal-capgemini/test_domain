import csv
from models.benchmark import Benchmark

def readFromlog(logfile_path: str, chunk_size: int):
    """
    A generator function that reads a chunk (x lines) at the time from a file
    """
    log_lines = []
    chunk_counter = 0
    with open(logfile_path, 'r') as log:
        line = 'first'
        line_index = 0
        while line:
            line = log.readline().rstrip('\n')
            line_index += 1
            log_lines.append(Benchmark(line, line_index))
            chunk_counter += 1

            if chunk_counter >= chunk_size:
                chunk_counter = 0
                yield log_lines
                log_lines = []
    yield log_lines

def saveAsCsv(csv_path: str, data: list):
    with open(csv_path, 'a+', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for row in data:
            writer.writerow(row.to_csv())

def saveHeadersAsCsv(csv_path: str, headers: list):
    with open(csv_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(headers)


def save_file(file, data):
    with open(file, 'w') as f:
        try:
            f.write(data)
        except:
            print(f'Could not save file: {file}')