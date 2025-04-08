import requests
import json
import re
from collections import defaultdict


def fetch_data(url, initial_start=0, increment=20, max_iterations=10, extra_params=None):
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

        # Add any extra parameters passed (like 'name')
        if extra_params:
            params.update(extra_params)

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
            break

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Invalid JSON response.")
            break

        collected_data.append(data)

        if 'next_page' in data and not data['next_page']:
            print("No more pages available, exiting...")
            break

        start += increment
        iterations += 1

    return collected_data


def extract_prefixes(collected_data):
    prefixes = set()
    for page in collected_data:
        if 'items' in page:
            for item in page['items']:
                course_id = item.get("id") or item.get("course_id")
                if course_id:
                    match = re.match(r"([A-Z0-9]+)-", course_id)
                    if match:
                        prefixes.add(match.group(1))
    return prefixes

def main():
    url = 'https://apps.usos.pwr.edu.pl/services/courses/search'

    # Step 1: Fetch initial data
    initial_data = fetch_data(url, max_iterations=10)

    # Step 2: Extract course_id prefixes
    prefixes = extract_prefixes(initial_data)

    # Step 3: Use prefixes with '-SI' and '-SM' suffixes for additional fetches
    additional_data = {}
    suffixes = ['SI', 'SM']

    for prefix in prefixes:
        for suffix in suffixes:
            full_name = f"{prefix}-{suffix}"
            print(f"Fetching data for name: {full_name}")
            extra_params = {'name': full_name}
            data = fetch_data(url, extra_params=extra_params, max_iterations=10)
            additional_data[full_name] = data

    # Step 4: Save everything
    output = {
        "initial_data": initial_data,
        "additional_data_by_prefix": additional_data
    }

    with open("final_combined_data.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print("✅ All data saved to final_combined_data.json")

if __name__ == "__main__":
    main()
