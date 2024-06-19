from flask import Flask, request, render_template, send_from_directory
import os
import ffmpeg
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import whisper
from moviepy.config import change_settings
from multiprocessing import Pool
import math

# Configure ImageMagick
change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
GIF_FOLDER = 'gifs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GIF_FOLDER, exist_ok=True)

# Set the number of parallel processes based on your system resources
NUM_PARALLEL_PROCESSES = 4

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return 'No file part'
    file = request.files['video']
    if file.filename == '':
        return 'No selected file'
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    transcribe_and_generate_gifs_parallel(file_path)

    # Close the video file after processing
    video = VideoFileClip(file_path)
    video.reader.close()
    if video.audio is not None:
        video.audio.reader.close_proc()

    return 'GIFs created successfully'

def transcribe_and_generate_gifs_parallel(video_path):
    model = whisper.load_model("base")
    audio = whisper.load_audio(video_path)
    audio = whisper.pad_or_trim(audio)

    result = model.transcribe(audio, word_timestamps=True)
    segments = split_transcription_into_segments(result["segments"])

    generate_gifs(video_path, segments)

def split_transcription_into_segments(segments, max_duration=30):
    new_segments = []
    current_segment = []
    current_duration = 0

    for segment in segments:
        word_duration = segment["end"] - segment["start"]
        if current_duration + word_duration > max_duration:
            new_segments.append(current_segment)
            current_segment = [segment]
            current_duration = word_duration
        else:
            current_segment.append(segment)
            current_duration += word_duration

    if current_segment:
        new_segments.append(current_segment)

    return [
        {
            "start": min(segment["start"] for segment in segment_group),
            "end": max(segment["end"] for segment in segment_group),
            "text": " ".join(segment["text"] for segment in segment_group),
        }
        for segment_group in new_segments
    ]

def generate_gifs(video_path, segments):
    video = VideoFileClip(video_path)
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']

        clip = video.subclip(start, end)
        txt_clip = TextClip(text, fontsize=24, color='white', bg_color='black')
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(clip.duration)
        video_with_text = CompositeVideoClip([clip, txt_clip])

        gif_path = os.path.join(GIF_FOLDER, f"segment_{i}.gif")
        video_with_text.write_gif(gif_path)

    # Properly close video and audio readers
    video.reader.close()
    if video.audio is not None:
        video.audio.reader.close_proc()

if __name__ == '__main__':
    app.run(debug=True)