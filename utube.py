#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import re
import os
from urllib.parse import unquote

# Add your target YouTube Live or Video URLs here
YOUTUBE_CHANNELS = [
    {"name": "Live Harimandir Sahib", "url": "https://www.youtube.com/watch?v=Zdw8mPolGYw"},
    {"name": "Live Channel 2", "url": "https://www.youtube.com/watch?v=Zdw8mPolGYw"},
    {"name": "Live Channel 3", "url": "https://www.youtube.com/watch?v=Zdw8mPolGYw"}
]

OUTPUT_FILE = "youtube_channels.m3u"

def extract_video_id(url):
    """Extract video ID from YouTube URL – robust version"""
    try:
        decoded_url = unquote(url)
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
            r'(?:https?://)?youtu\.be/([^?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^/?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([^/?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^/?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/live/([^/?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/channel/([^/?]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/@([^/?]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, decoded_url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting video ID: {e}")
        return None

def find_ytdlp():
    """Find local yt-dlp binary or standard environment execution path"""
    standard_paths = [
        "/usr/local/bin/yt-dlp", # Absolute path matching installation step
        "yt-dlp", 
        "/usr/bin/yt-dlp"
    ]
    for path in standard_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return path
        except Exception:
            continue
    return None

def get_stream_with_ytdlp(ytdlp_path, video_id):
    """Extract raw streaming URL using target format configurations"""
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    format_options = [
        ["-g", "-f", "best[ext=mp4]"],
        ["-g", "-f", "18"],
        ["-g", "-f", "22/37"],
        ["-g", "-f", "best"]
    ]

    for fmt in format_options:
        cmd = [ytdlp_path] + fmt + [youtube_url]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                stream_url = result.stdout.strip()
                if stream_url and stream_url.startswith(("http://", "https://")):
                    return stream_url
        except Exception:
            continue
    return None

def build_playlist():
    print("Starting YouTube to M3U pipeline...")
    ytdlp = find_ytdlp()
    if not ytdlp:
        print("Error: yt-dlp binary not found in system paths.")
        return

    m3u_lines = ["#EXTM3U\n"]
    valid_streams = 0

    for ch in YOUTUBE_CHANNELS:
        print(f"Resolving stream for: {ch['name']}")
        video_id = extract_video_id(ch['url'])
        
        if not video_id:
            print(f"Skipping: Invalid YouTube URL structure for {ch['name']}")
            continue

        stream_url = get_stream_with_ytdlp(ytdlp, video_id)
        if stream_url:
            m3u_lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="{ch["name"]}" group-title="YouTube Live",{ch["name"]}\n')
            m3u_lines.append(f"{stream_url}\n")
            valid_streams += 1
            print(f"Successfully resolved streaming link for {ch['name']}")
        else:
            print(f"Failed to resolve streaming link for {ch['name']}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)
    print(f"Completed pipeline. Generated {OUTPUT_FILE} with {valid_streams} active stream paths.")

if __name__ == "__main__":
    build_playlist()
