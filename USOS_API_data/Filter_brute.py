import json
import re


def extract_courses(pages):
    """Flatten paginated response and return a list of course entries."""
    courses = []
    for page in pages:
        items = page.get('items', [])
        courses.extend(items)
    return courses


def load_and_deduplicate(filename="final_combined_data.json"):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    seen_ids = set()
    unique_courses = []
    found_prefixes = set()

    # Step 1: Process initial_data
    initial_courses = extract_courses(data.get('initial_data', []))

    # Step 2: Process additional_data_by_prefix
    additional_courses = []
    additional_data = data.get('additional_data_by_prefix', {})
    for prefix, prefix_pages in additional_data.items():
        additional_courses.extend(extract_courses(prefix_pages))

    # Combine all courses
    all_courses = initial_courses + additional_courses

    # Step 3: Deduplicate and collect prefixes
    for course in all_courses:
        course_id = course.get('id') or course.get('course_id')
        if course_id:
            if course_id not in seen_ids:
                seen_ids.add(course_id)
                unique_courses.append(course)

                # Extract and store prefix
                match = re.match(r"([A-Z0-9]+)-", course_id)
                if match:
                    found_prefixes.add(match.group(1))

    return unique_courses, sorted(found_prefixes)


def save_deduplicated_courses(output_file="unique_courses-2.json"):
    unique_courses, found_prefixes = load_and_deduplicate()

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_courses, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Saved {len(unique_courses)} unique courses to {output_file}")
    print("📌 Found and used prefixes:")
    for prefix in found_prefixes:
        print(f" - {prefix}")


if __name__ == "__main__":
    save_deduplicated_courses()
