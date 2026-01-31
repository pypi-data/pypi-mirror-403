from PIL import Image

def image_info_to_horus(filename):
    try:
        with Image.open(filename) as img:
            print(f"Filename: {filename}")
            print(f"Format: {img.format}")
            print(f"Mode: {img.mode}")
            print(f"Size: {img.size[0]} x {img.size[1]} pixels")
    except FileNotFoundError:
        print("Error: File not found.")
    except Exception as e:
        print("An error occurred:", str(e))
image_info_to_horus("uni.jpg")
