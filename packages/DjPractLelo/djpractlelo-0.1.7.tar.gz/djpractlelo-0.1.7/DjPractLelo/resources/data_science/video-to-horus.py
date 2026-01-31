import cv2

# Read video file
file = "video.mp4"
cap = cv2.VideoCapture(file)

# Extract video metadata
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = round(cap.get(cv2.CAP_PROP_FPS), 2)
frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = round(frames / fps, 2)

cap.release()

# Display in HORUS format (IDLE output)
print("VIDEO")
print(f"Filename: {file}")
print(f"Width: {width}")
print(f"Height: {height}")
print(f"FPS: {fps}")
print(f"Total Frames: {frames}")
print(f"Duration(sec): {duration}")
