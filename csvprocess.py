import pandas as pd

# Load the provided CSV files
metadata_path = r"E:\DL\final_exp\exp3\309.csv"
machine_log_path = r"E:\DL\final_exp\vscode\Machine_data_logging309.csv"

# Offset in milliseconds
offset = 277258

# Read the metadata and machine log CSV files
metadata_df = pd.read_csv(metadata_path)
machine_log_df = pd.read_csv(machine_log_path, header=None)

# Adjust the column names for the machine log
machine_log_df.columns = ['Timestamp', 'Part id', 'laserpower', 'steps', 'startx', 
                          'endx', 'starty', 'endy', 'currentx', 'currenty', 
                          'cgh1', 'cgh2', 'ntptimeoffset', 'request MQTT', 'get MQTT']

# Convert Unix Timestamp to numeric, and drop any rows with NaN
metadata_df['Unix Timestamp'] = pd.to_numeric(metadata_df['Unix Timestamp'], errors='coerce')

# Drop rows with NaN values in Unix Timestamp column
metadata_df = metadata_df.dropna(subset=['Unix Timestamp'])

# Convert Unix Timestamp to 64-bit integers to prevent overflow
metadata_df['Unix Timestamp'] = metadata_df['Unix Timestamp'].astype('int64')

# Adjust Unix Timestamp by adding the offset
metadata_df['Adjusted Machine Timestamp'] = metadata_df['Unix Timestamp'] - offset



# Function to find the closest machine log entry for a given timestamp
def find_closest_machine_log(timestamp):
    diff = machine_log_df['Timestamp'] - timestamp
    abs_diff = abs(diff)
    min_diff = abs_diff.min()
    
    if min_diff <= 16:
        closest_index = abs_diff.idxmin()
        return machine_log_df.iloc[closest_index], min_diff
    return None, None

# Apply the function to each metadata timestamp and store results
results = []

for index, row in metadata_df.iterrows():
    closest_log, min_diff = find_closest_machine_log(row['Adjusted Machine Timestamp'])
    if closest_log is not None:
        log_data = closest_log.to_dict()
        log_data['image time'] = row['Unix Timestamp']
        log_data['Adjusted Machine Time'] = row['Adjusted Machine Timestamp']
        log_data['Error'] = min_diff
        results.append(log_data)

# Create a new DataFrame for the results
results_df = pd.DataFrame(results)

# Save the result to a new CSV file
output_path = r"E:\DL\final_exp\analyze\matched_logs.csv"
results_df.to_csv(output_path, index=False)

print(f"Matching completed. Results saved to {output_path}")
