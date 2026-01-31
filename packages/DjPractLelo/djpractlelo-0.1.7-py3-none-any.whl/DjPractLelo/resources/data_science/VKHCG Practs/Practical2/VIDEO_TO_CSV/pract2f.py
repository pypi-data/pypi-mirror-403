import cv2
import pandas as pd

#Reading Video file
file = 'video.mp4'  
cap = cv2.VideoCapture(file)

# ✅ Extract basic metadata
width = cap.get(3)  # CAP_PROP_FRAME_WIDTH
height = cap.get(4)  # CAP_PROP_FRAME_HEIGHT
fps = cap.get(5)  # CAP_PROP_FPS
frames = cap.get(7)  # CAP_PROP_FRAME_COUNT
duration = frames / fps

cap.release()

df = pd.DataFrame([{
    'filename': file,
    'width': int(width),
    'height': int(height),
    'fps': round(fps, 2),
    'duration (sec)': round(duration, 2)
}])
print(df)
df.to_csv('video_horus.csv', index=False)
print("Saved to video_horus.csv")
