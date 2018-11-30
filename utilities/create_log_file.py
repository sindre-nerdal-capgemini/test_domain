"""
    Creates a csv file of relatives url.
    These urls comes from a directory containing only files from "spoling" to a production environment
"""
import os
import sys

def run(dir, csv_file):

    relative_urls = []

    # Do work for each file in the directory
    for filename in os.listdir(dir):
        lines_per_log = 0

        # Read each file
        with open(os.path.join(dir, filename), 'r') as f:

            # Iterate thorugh the file
            for _, row in enumerate(f):
                if row.startswith('http'):
                    try:
                        url = ''.join(row.split('-')[:1])
                        relative_urls.append(url.split('ndla.no')[1])
                    except:
                        print(f"Error on line {_} with row {row}")

                    lines_per_log += 1
        print(f'File {filename} has {lines_per_log} lines to test')

    # Create csv with realtive urls
    with open(csv_file, 'w') as f:
        for line in relative_urls:
            f.write(f'{line}\n')

    print(f'Total urls to test from {len(os.listdir(dir))} file(s) is {len(relative_urls)}')
    print(f'Csv created {csv_file}')

if __name__ == '__main__':
    try:
        directory = sys.argv[1]
    except IndexError:
        print("Need dir with files as input....")

    try:
        output = sys.argv[2]
    except IndexError:
        print("Need output file path as input....")

    run(directory, output)