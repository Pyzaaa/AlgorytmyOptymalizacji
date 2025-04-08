import requests
import json


def fetch_data(url, initial_start=0, increment=20, max_iterations=10, output_file="data.json"):
    start = initial_start
    iterations = 0
    collected_data = []  # List to collect all the returned data

    while iterations < max_iterations:
        params = {
            'num': '20',
            'start': start,
            'fac_id': 'W4N',
            'fields': 'id|name|terms'
        }

        response = requests.get(url, params=params)

        # If the request fails or doesn't return valid JSON, skip this loop
        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
            break

        data = response.json()

        # Append the current page's data to the collected data
        collected_data.append(data)

        # Check if the next page is available or if we've reached the end
        if 'next_page' in data and not data['next_page']:
            print("No more pages available, exiting...")
            break

        # Increment the start parameter for the next request
        start += increment
        iterations += 1

    # Save the collected data to a JSON file
    with open(output_file, 'w') as json_file:
        json.dump(collected_data, json_file,ensure_ascii=False, indent=4)

    print(f"Data saved to {output_file}")


# Example usage
url = 'https://apps.usos.pwr.edu.pl/services/courses/search'
fetch_data(url, max_iterations=10, output_file="collected_course_data.json")
