import json

def browse_and_count_items(json_file):
    # Load the JSON data
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Set to store unique item ids to count different items
    item_ids = set()

    # List to store item names
    item_names = []

    # Loop through the data to extract the necessary information
    for entry in data:
        if 'items' in entry:
            for item in entry['items']:
                # Extract item id and add to the set to count unique items
                item_id = item.get('id')
                if item_id:
                    item_ids.add(item_id)

                # Extract item name in Polish (pl) and English (en)
                item_name_pl = item.get('name', {}).get('pl', 'N/A')
                item_name_en = item.get('name', {}).get('en', 'N/A')

                # Store the item names in the list
                item_names.append((item_name_pl, item_name_en))

    # Output results
    print(f"Total different items: {len(item_ids)}")
    print("\nItem Names:")
    for name_pl, name_en in item_names:
        print(f"PL: {name_pl} | EN: {name_en}")


# Example usage
json_file = "collected_course_data.json"
browse_and_count_items(json_file)
