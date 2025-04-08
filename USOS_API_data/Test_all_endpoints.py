import requests
import json

# Function to load endpoints from a JSON file
def load_endpoints(file_path):
    try:
        with open(file_path, 'r') as file:
            endpoints = json.load(file)
        return endpoints
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from the file '{file_path}'.")
        return []

# Base URL of the USOS API
base_url = 'https://apps.usos.pwr.edu.pl/'

# Function to test each endpoint
def test_endpoints(endpoints):
    with open('api_responses.txt', 'w') as file:
        for endpoint in endpoints:
            url = base_url + endpoint['name']
            try:
                print(f"Testing {url}...")
                response = requests.get(url)
                status_code = response.status_code
                if status_code == 200:
                    data = response.json()
                    file.write(f"Endpoint: {url}\nStatus Code: {status_code}\nResponse: {data}\n\n")
                else:
                    file.write(f"Endpoint: {url}\nStatus Code: {status_code}\nResponse: {response.text}\n\n")
            except requests.exceptions.RequestException as e:
                file.write(f"Endpoint: {url}\nError: {e}\n\n")

if __name__ == '__main__':
    endpoints = load_endpoints('endpoint_list.json')
    if endpoints:
        test_endpoints(endpoints)
