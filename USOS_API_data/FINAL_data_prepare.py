import json

def extract_rooms(filename):
    """
    Extracts didactics rooms and returns a list of dicts with room ID and number.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            rooms = json.load(f)
            didactics_rooms = []
            for room in rooms:
                if room.get("type") == "didactics_room":
                    didactics_rooms.append(room.get("number", "N/A"))

        output_dict = {"rooms" : didactics_rooms}
        return output_dict

    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

def extract_course_and_lecturer_matrix(input_file):
    """
    Extracts course and lecturer full names and course-lecturer matrix.
    Returns a tuple: (list_data_dict, matrix)
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            courses_data = json.load(file)

        course_ids = []
        lecturer_names_set = set()
        course_to_lecturers = {}

        for course in courses_data.values():
            course_id = course.get('course_id')
            if not course_id:
                continue

            course_ids.append(course_id)

            # Build lecturer full names
            lecturer_names = []
            for lec in course.get('lecturers', []):
                first = lec.get('first_name', '').strip()
                last = lec.get('last_name', '').strip()
                if first and last:
                    full_name = f"{first} {last}"
                    lecturer_names.append(full_name)
                    lecturer_names_set.add(full_name)

            course_to_lecturers[course_id] = set(lecturer_names)

        lecturer_names = sorted(list(lecturer_names_set))

        '''        
        # Create matrix
        matrix = []
        for course_id in course_ids:
            row = [1 if name in course_to_lecturers[course_id] else 0 for name in lecturer_names]
            matrix.append(row)'''
        # Replace matrix with mapping of course ID to lecturers
        course_lecturer_mapping = {}
        for course_id in course_ids:
            course_lecturer_mapping[course_id] = list(course_to_lecturers.get(course_id, []))



        list_data = {
            "courses": course_ids,
            "lecturers": lecturer_names
        }

        return list_data, course_lecturer_mapping

    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return {}, []


def save_to_json(data, output_file):
    """
    Saves given data to a JSON file.

    - If 'data' is a list/tuple of dicts, merges them into one dict.
    - If 'data' is a single dict or list, saves as-is.
    - If merging dicts with overlapping keys, raises an error.
    """
    try:
        if isinstance(data, (list, tuple)) and all(isinstance(d, dict) for d in data):
            combined_data = {}
            for d in data:
                overlapping_keys = combined_data.keys() & d.keys()
                if overlapping_keys:
                    raise ValueError(f"Duplicate keys detected: {overlapping_keys}")
                combined_data.update(d)
        else:
            combined_data = data

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=4, ensure_ascii=False)
        print(f"Saved data to '{output_file}'.")

    except Exception as e:
        print(f"Error saving to {output_file}: {e}")




# Example usage
if __name__ == "__main__":
    rooms = extract_rooms("room_details-att.json")
    list_data, mapping = extract_course_and_lecturer_matrix("course_editions_with_lecturers_sorted.json")

    # Save separately (as before)
    #save_to_json(rooms, "didactics_rooms.json")
    #save_to_json(list_data, "course_lecturer_lists.json")
    save_to_json(mapping, "final json/course_lecturer_mapping.json")

    # Or save all in one file
    save_to_json([
        rooms,
        list_data],
        "final json/FINAL_all_data_combined.json")
