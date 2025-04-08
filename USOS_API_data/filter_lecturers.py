import json


# Define your custom term sorting priority
TERM_PRIORITY = [
    "2024/25-L",
    "2023/24-Z",
    "2023/24-L",
    "2022/23-Z",
    "2022/23-L"
]


def get_term_order(term_id):
    """Return index of term in priority list; fallback to end if unknown."""
    try:
        return TERM_PRIORITY.index(term_id)
    except ValueError:
        return len(TERM_PRIORITY)


def load_editions(filename="course_editions_by_terms.json"):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_with_lecturers(editions):
    return {
        key: value
        for key, value in editions.items()
        if isinstance(value.get("lecturers"), list) and len(value["lecturers"]) > 0
    }


def sort_by_term(filtered_data):
    def extract_term(key):
        # Key format: course_id__term_id
        parts = key.split("__")
        return parts[1] if len(parts) == 2 else ""

    # Sort based on term priority
    sorted_items = sorted(
        filtered_data.items(),
        key=lambda item: get_term_order(extract_term(item[0]))
    )
    return dict(sorted_items)


def save_sorted(data, output_file="course_editions_with_lecturers_sorted.json"):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ Saved {len(data)} sorted course editions with lecturers to {output_file}")


def main():
    editions = load_editions()
    filtered = filter_with_lecturers(editions)
    sorted_data = sort_by_term(filtered)
    save_sorted(sorted_data)


if __name__ == "__main__":
    main()
