from flask import Flask, render_template, request, redirect, url_for
import os
import json
import google.generativeai as genai
import requests
from urllib.parse import unquote

app = Flask(__name__)

# -----------------------------
# GEMINI CONFIG
# -----------------------------
GENAI_API_KEY = "AIzaSyA40oa3Rt25udBUBRUTCSR8xeLDduSWba0"
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# YOUTUBE FETCHER
# -----------------------------
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def getyt(skill):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": skill,
        "type": "playlist",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY
    }
    # Safety check for API Key
    if not YOUTUBE_API_KEY:
        return []

    try:
        response = requests.get(url, params=params)
        data = response.json()
        results = []
        for item in data.get("items", []):
            playlist_id = item["id"]["playlistId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            access_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
            results.append({
                "title": title,
                "channel": channel,
                "playlist_url": access_url,
                "thumbnail": thumbnail
            })
        return results
    except Exception as e:
        print(f"Error fetching YouTube data: {e}")
        return []

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    problem_statement = request.form.get("problem_statement", "")
    solution_text = request.form.get("solution_text", "")

    final_input = f"""
    You are an advanced AI Coding Mentor (Cyberpunk Edition). 
    Analyze the user's code strictly.

    CRITICAL OUTPUT RULES:
    1. Return ONLY RAW JSON. No markdown formatting.
    2. No bold/italic markdown inside JSON.
    3. Do NOT provide direct YouTube links. Only provide search topics. No slashes, no brackets, just names.
    4. Provide a score (0-100) evaluating the solution.
    5. weekly plan should be of 7 days 

    Problem: {problem_statement}
    Solution: {solution_text}

    JSON Structure required:
    {{
      "score": <integer_0_to_100>,
      "strengths": ["point 1", "point 2"],
      "weaknesses": ["point 1", "point 2"],
      "missing_concepts": ["concept 1", "concept 2"],
      "topics_to_learn": ["topic 1", "topic 2"],
      "week_plan": [
        {{"day": "Day 1", "focus": "Topic Name", "task": "Detailed task description..."}},
        {{"day": "Day 2", "focus": "Topic Name", "task": "Detailed task description..."}}
      ],
      "similar_problems": ["Problem A", "Problem B"]
    }}
    """

    try:
        response = model.generate_content(final_input)
        raw_text = response.text.strip()

        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        raw_text = raw_text.replace("**", "").replace("*", "")
        parsed_json = json.loads(raw_text)

    except Exception as e:
        print(f"Error parsing AI response: {e}")
        parsed_json = {
            "score": 0,
            "strengths": ["Error analyzing response"],
            "weaknesses": ["Please try again"],
            "missing_concepts": [],
            "topics_to_learn": [],
            "week_plan": [],
            "similar_problems": []
        }

    # ---- Removed saving JSON to file ----

    return render_template("display.html", data=parsed_json)

@app.route("/roadmap")
def roadmap():
    # Without saved JSON, roadmap cannot be loaded
    # Optionally, show a message
    return render_template("roadmap.html", data={})

# -----------------------------
# LEARN TOPIC (YOUTUBE ONLY)
# -----------------------------
@app.route("/learn/<path:topic>")
def learn_topic(topic):
    topic = unquote(topic)
    yt = getyt(topic)
    return render_template("learn.html", topic=topic, yt=yt)

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
