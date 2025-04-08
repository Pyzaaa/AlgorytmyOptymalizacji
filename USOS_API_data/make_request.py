import requests

# API endpoint
url = 'https://apps.usos.pwr.edu.pl/services/courses/course_edition'
course_id = 'W04ISA-SM0003G'
term_id = "2024/25-L"
fields = "course_id|course_name|lecturers"

# Parameters to send with the request
params = {
    "course_id": course_id,
    "term_id": term_id,
    "fields": fields
}

# Send the GET request
response = requests.get(url, params=params)

# Check the response status
if response.status_code == 200:
    # Successfully received a response
    data = response.json()  # Parse JSON response
    print('Data received:', data)
else:
    # Handle errors
    print(f'Error: Received status code {response.status_code}')
    print('Response content:', response.text)
