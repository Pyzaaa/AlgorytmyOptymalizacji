# Function to process the API responses file and filter out status code 400
def filter_api_responses(input_file, output_file):
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            lines = infile.readlines()
            filtered_lines = []
            current_entry = []

            for line in lines:
                if line.strip():  # Ignore blank lines
                    current_entry.append(line)
                else:
                    if current_entry:
                        # Check if status code 400 is present in the current entry
                        if not any('Status Code: 400' in entry_line for entry_line in current_entry):
                            filtered_lines.extend(current_entry)
                            filtered_lines.append('\n')  # Add a newline between entries
                        current_entry = []  # Reset for the next entry

            # Handle the last entry if the file doesn't end with a newline
            if current_entry:
                if not any('Status Code: 400' in entry_line for entry_line in current_entry):
                    filtered_lines.extend(current_entry)

            # Write filtered lines to the output file
            outfile.writelines(filtered_lines)
        print(f"Filtered responses have been saved to '{output_file}'.")
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == '__main__':
    input_file = 'api_responses.txt'
    output_file = 'filtered_api_responses.txt'
    filter_api_responses(input_file, output_file)
