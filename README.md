# AlgorytmyOptymalizacji



## mamy:
- course_id typu: W04ISA-SM0003G *(większość kursów)*
- term_id: 2024/25-L
- nazwiska i id prowadzących
- jakie są pokoje w danych budynkach (nie wiadomo czy wszystkie)
- ilość miejsc w tych pokojach i jakie zajęcia można tam prowadzić

## Nie mamy:
- Który kierunek ma jaki kurs (mniej więcej na podstawie ID kursu można się domyślać)
- Ile powinny trwać zajęcia w semestrze/dniu?
- 



## USOS_API_data/
### important files (sorted by input > script > output):
- brute_request.py - requests courses for many combinations of course_ids
- final_combined_data.json
- Filter_brute.py - Filters data gathered by brute request
- unique_courses.json / unique_courses-2.json
- request_lecturers.py - Makes request for every filtered course id to get lecturer info
- course_editions_by_terms.json / course_editions_by_terms-2.json
- filter_lecturers.py - Filters requested lecturer data keeping only courses with lecturers and sotrts by term
- course_lecturers.json - output, unsorted
- course_editions_with_lecturers_sorted.json - output, sorted by term
- FINAL_data_prepare - gathers information from JSON files into final combined JSONs
### building info files
- request_building_rooms.py - requests room IDs of a building and filters for only room ID and name
- building_rooms.json - output of the script
- request_room_details.py - requests details of the room- type and capacity (+ attributes)
- room_details.json / room_details-att.json - saved room details without/with additional attributes
- analyze_room_details.py - analyze room_details json files to find how many rooms of given type there are and what they can be used for

### API access / testing
- endpoint_list.json - list of all endpoints from *services/apiref/method_index*
- API_Tester.py - makes request to some endpoints
- Test_all_endpoints.py - makes request to all endpoints
- api_responses.txt - all responses
- Browse_responses.py - filters responses
- filtered_api_responses.txt - non 400 responses
- request_courses.py - requests ~100 courses from W4N
- Analyze_course_data.py
- make_request.py - debug / test script for making a single request

### analiza pokoi dla C-3

```
Room type statistics for room_details-att.json:
  staff_members_room: 21
  didactics_room: 27

Attributes in 'didactics_room' for room_details-att.json:
  KOMPUTERY: 10 room(s), total capacity: 152
  LAB_KOMP: 11 room(s), total capacity: 179
  SALA_CW: 2 room(s), total capacity: 92
  SALA_WYK_DUZA: 0 room(s), total capacity: 0
  SALA_WYK_MALA: 2 room(s), total capacity: 191```