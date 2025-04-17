from flask import Flask, request, send_file, render_template_string, after_this_request
import yt_dlp
import os
import uuid
import time

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Downloader</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        input, button { padding: 10px; margin: 10px; width: 300px; }
    </style>
</head>
<body>
    <h1>YouTube Downloader</h1>
    <form method="POST" action="/download">
        <input name="url" placeholder="Enter YouTube URL" required><br>
        <button type="submit">Download Video</button>
    </form>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return "No URL provided", 400

    filename = f"{uuid.uuid4()}.mp4"
    ydl_opts = {
        'outtmpl': filename,
        'format': 'best',
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Ensure file is fully written
        time.sleep(1)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Error deleting file: {e}")
            return response

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
