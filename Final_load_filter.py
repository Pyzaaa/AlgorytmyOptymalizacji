import json
import shutil
import os


# File paths
lecturers_path = "USOS_API_data/final json/final_course_lecturers.json"
courses_path = "USOS_API_data/final json/final_course_data.json"
rooms_mapping_path = "USOS_API_data/final json/final_class_type_to_rooms.json"
output_dir = "Final_load_data"
output_path = os.path.join(output_dir, "merged_filtered_course_data.json")

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load lecturers data
with open(lecturers_path, 'r', encoding='utf-8') as f:
    lecturers_data = json.load(f)

# Load course data
with open(courses_path, 'r', encoding='utf-8') as f:
    course_data = json.load(f)


# Define filtering function
def is_valid_course(code):
    return not code.endswith(('G', 'D'))


# Filter and merge data
merged_data = {}
for code, details in course_data.items():
    if is_valid_course(code):
        merged_data[code] = details.copy()
        merged_data[code]["lecturers"] = lecturers_data.get(code, [])

# Save merged data
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, indent=4, ensure_ascii=False)

print(f"Filtered and merged data saved to: {output_path}")

# Copy the rooms mapping file to the output directory
shutil.copy2(rooms_mapping_path, output_dir)
print(f"Copied room type mapping to: {output_dir}")
