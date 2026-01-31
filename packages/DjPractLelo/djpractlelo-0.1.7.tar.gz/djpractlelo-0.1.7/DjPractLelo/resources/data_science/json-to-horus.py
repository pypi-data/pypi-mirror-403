import json

# Load JSON file
with open("course.json", "r") as file:
    data = json.load(file)

# Display HORUS format in IDLE
for course in data["courses"]:
    print(f"Name:- {course['course_name']}")
    print(f"Duration:- {course['duration']}")
    print(f"Average Fee:- {course['average_fee']}")
    print(f"Future Scope:- {course['future_scope']}\n")
