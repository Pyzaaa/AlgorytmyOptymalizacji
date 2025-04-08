import requests
import json
import time


def extract_course_term_pairs(filename="unique_courses-2.json"):
    with open(filename, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    course_term_pairs = set()

    for course in courses:
        print(course)
        course_id = course.get("id") or course.get("course_id")
        print(course_id)
        if not course_id:
            print("no id found, skipping")
            continue

        # Extract from course terms (usually a list of dicts)
        terms = course.get("terms", [])
        for term in terms:
            term_id = term.get("id")
            if term_id:
                course_term_pairs.add((course_id, term_id))
                break # only first term


    return sorted(course_term_pairs)


def fetch_course_editions(course_term_pairs, base_url):

    print(f'requesting {len(course_term_pairs)} items.')
    print(f'approximate completion time {len(course_term_pairs)*0.3} seconds')

    results = {}
    endpoint = f"{base_url}/services/courses/course_edition"
    fields = "course_id|course_name|lecturers"

    for course_id, term_id in course_term_pairs:
        params = {
            "course_id": course_id,
            "term_id": term_id,
            "fields": fields
        }

        print(f'requesting for {params}')

        try:
            response = requests.get(endpoint, params=params)
            if response.status_code == 200:
                key = f"{course_id}__{term_id}"
                results[key] = response.json()
            else:
                print(f"❌ Failed for {course_id} @ {term_id} - Status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error fetching {course_id} @ {term_id}: {e}")

        time.sleep(0.2)



    return results


def save_results(data, output_file="course_editions_by_terms-2.json"):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ Saved {len(data)} course editions to {output_file}")


def main():
    base_url = "https://apps.usos.pwr.edu.pl"

    course_term_pairs = extract_course_term_pairs()
    edition_data = fetch_course_editions(course_term_pairs, base_url)
    save_results(edition_data)


if __name__ == "__main__":
    main()
