import xml.etree.ElementTree as ET

def xml_to_horus(filename):
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for record in root:
            for element in record:
                print(f"{element.tag}: {element.text}")
            print("\n")

    except FileNotFoundError:
        print("Error: File not found.")
    except ET.ParseError:
        print("Error: Failed to parse XML. Make sure it's well-formed.")
    except Exception as e:
        print("An error occurred:", str(e))

# Example usage
xml_to_horus('basic.xml')
