import re
import csv
import numpy as np
from datetime import datetime
import set_path
import os

def generate_csv():
    # Define the input and output file paths
    input_file_path = set_path.get_meta_file_path()
    file_name = os.path.splitext(os.path.basename(input_file_path))[0]
    parent_dir = os.path.dirname(os.path.dirname(input_file_path))
    output_file_path = os.path.join(parent_dir, f"{file_name}.csv")

    # Define the range of lines to include in the calculations
    include_start = 100
    include_end = 500000

    # Open the input file for reading and the output file for writing
    with open(input_file_path, 'r', encoding='utf-8') as infile, open(output_file_path, 'w', newline='') as outfile:
        # Create a CSV writer object
        csv_writer = csv.writer(outfile)
        # Write the header row to the CSV file
        csv_writer.writerow(['Original Date', 'Name', 'Unix Timestamp', 'Time Difference (ms)'])
        prev_timestamp = None
        time_differences = []
        
        # Iterate through each line in the input file
        for line_number, line in enumerate(infile, start=1):
            # Use a regular expression to match the desired pattern
            match = re.match(r"(\d+)\s*\|\s*([0-9\.:_]+)\s*\|\s*([0-9a-zA-Z_]+)", line)
            if match:
                # Extract the time string and name from the matched groups
                original_date = match.group(2)
                name = match.group(3)
                
                # Convert the time string to a UNIX timestamp with milliseconds
                dt = datetime.strptime(original_date, "%Y.%m.%d_%H:%M:%S.%f")
                unix_timestamp_ms = dt.timestamp() * 1000  # Convert to milliseconds
                
                if prev_timestamp is not None:
                    time_diff = unix_timestamp_ms - prev_timestamp
                    # Only add the time difference if the line number is within the included range
                    if include_start <= line_number <= include_end:
                        time_differences.append(time_diff)
                else:
                    time_diff = None
                
                # Write the original date, name, UNIX timestamp, and time difference to the CSV file
                csv_writer.writerow([original_date, name, unix_timestamp_ms, time_diff])
                
                # Update the previous timestamp
                prev_timestamp = unix_timestamp_ms
        
        # Calculate the standard deviation and average of the time differences
        if time_differences:
            std_dev = np.std(time_differences)
            std_ave = np.average(time_differences)
        else:
            std_dev = None
            std_ave = None
        
        # Write the standard deviation and average to the CSV file
        csv_writer.writerow(['', '', 'Standard Deviation of Time Differences (ms)', std_dev])
        csv_writer.writerow(['', '', 'Average Time Differences (ms)', std_ave])


if __name__ == "__main__":
    generate_csv()
