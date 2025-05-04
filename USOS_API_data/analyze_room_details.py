import json
import glob
from collections import Counter, defaultdict

# Attributes of interest
target_attributes = {"LAB_KOMP", "KOMPUTERY", "SALA_CW", "SALA_WYK_MALA", "SALA_WYK_DUZA"}

# Find all JSON files that match room_details*.json
files = glob.glob("room_details-att*.json")

if not files:
    print("No files matching 'room_details*.json' were found.")
else:
    for filename in files:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                rooms = json.load(f)

            # Room type counter
            type_counter = Counter()

            # Attribute counters specific to didactics_room
            attribute_room_count = Counter()
            attribute_capacity_total = defaultdict(int)

            for room in rooms:
                room_type = room.get("type", "unknown")
                type_counter[room_type] += 1

                if room_type == "didactics_room":
                    capacity = room.get("capacity", 0)
                    attributes = room.get("attributes", [])

                    for attr in attributes:
                        attr_id = attr.get("id")
                        if attr_id in target_attributes:
                            attribute_room_count[attr_id] += 1
                            attribute_capacity_total[attr_id] += capacity

            # Print results
            print(f"\nRoom type statistics for {filename}:")
            for room_type, count in type_counter.items():
                print(f"  {room_type}: {count}")

            print(f"\nAttributes in 'didactics_room' for {filename}:")
            for attr in sorted(target_attributes):
                count = attribute_room_count.get(attr, 0)
                capacity = attribute_capacity_total.get(attr, 0)
                print(f"  {attr}: {count} room(s), total capacity: {capacity}")

        except Exception as e:
            print(f"Error reading {filename}: {e}")
