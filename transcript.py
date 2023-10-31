# Importing necessary libraries
import os
import sys
import subprocess
import glob
import shutil

# Define the directory containing the MP4 files
video_dir = "D:\\Videos\\Trans\\kekw"

# Install OpenAI's Whisper if it's not already installed
try:
    import whisper
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'git+https://github.com/openai/whisper.git'])

# Load the model
model = whisper.load_model("medium")

# Get a list of all MP4 files in the directory
video_files = glob.glob(os.path.join(video_dir, "*.mp4"))

# Iterate through all the MP4 files
for video_file_path in video_files:
    # Get the base name of the video file (without extension)
    base_name = os.path.basename(video_file_path)
    video_name = os.path.splitext(base_name)[0]

    # Create a new directory for this video
    new_dir = os.path.join(video_dir, video_name)
    os.makedirs(new_dir, exist_ok=True)

    # Define the paths for the converted audio file and moved video file
    converted_filename = os.path.join(new_dir, "audio.wav")
    moved_video_filename = os.path.join(new_dir, "video.mp4")

    # Convert the video to WAV using ffmpeg
    subprocess.run(['ffmpeg', '-i', video_file_path, converted_filename])

    # Move the original video file to the new directory
    shutil.move(video_file_path, moved_video_filename)

    # Transcribe the audio file
    text = model.transcribe(converted_filename)

    # Write the transcribed text to a TXT file
    with open(os.path.join(new_dir, "full_text.txt"), 'w', encoding='utf-8') as f:
        f.write(text['text'])
