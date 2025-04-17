from flask import Flask, request, send_file, render_template_string, after_this_request
import yt_dlp
import os
import uuid
import time
import tempfile
import json

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

# Create a function to generate cookie file
def create_cookie_file():
    temp_cookie_file = os.path.join(tempfile.gettempdir(), 'youtube_cookies.txt')
    with open(temp_cookie_file, 'w') as f:
        # Write header required for Netscape cookie file format
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
        f.write("# This is a generated file!  Do not edit.\n\n")
        
        # Write the cookie in proper Netscape format:
        # domain	domain_initial_dot	path	secure	expiry	name	value
        f.write(".youtube.com\tTRUE\t/\tFALSE\t{}\tCONSENT\tYES+cb\n".format(int(time.time()) + 31536000))
        f.write(".youtube.com\tTRUE\t/\tFALSE\t{}\tPREF\tf6=8\n".format(int(time.time()) + 31536000))
    return temp_cookie_file

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return "No URL provided", 400

    filename = f"{uuid.uuid4()}.mp4"
    cookie_file = create_cookie_file()

    ydl_opts = {
        'outtmpl': filename,
        'format': 'best',
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'cookiefile': cookie_file,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['webpage']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Ensure file is fully written
        time.sleep(1)

        @after_this_request
        def cleanup(response):
            try:
                os.remove(filename)
                os.remove(cookie_file)  # Clean up the cookie file
            except Exception as e:
                print(f"Error cleaning up files: {e}")
            return response

        return send_file(filename, as_attachment=True)

    except Exception as e:
        # Clean up files in case of error
        try:
            os.remove(cookie_file)
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass
        return f"Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
