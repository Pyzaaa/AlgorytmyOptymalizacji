import requests

# List of potential API endpoints to test
endpoints = [
    'https://apps.usos.pwr.edu.pl/services/apisrv/installation',
    'https://apps.usos.pwr.edu.pl/services/apisrv/now',
    'https://apps.usos.pwr.edu.pl/services/courses/classtypes_index',
    'https://apps.usos.pwr.edu.pl/services/apiref/method_index'
]

def test_api_endpoints():
    for endpoint in endpoints:
        try:
            print(f"Testing endpoint: {endpoint}")
            response = requests.get(endpoint)
            if response.status_code == 200:
                print(f"Success! Data received from {endpoint}:")
                print(response.json())
            else:
                print(f"Failed to retrieve data from {endpoint}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while accessing {endpoint}: {e}")

if __name__ == '__main__':
    test_api_endpoints()
