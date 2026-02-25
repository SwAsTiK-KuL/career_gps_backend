import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

class CareerPathModel:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env file")
        self.model_name = model
        print(f"✅ Connected to Gemini ({model}) — All set!")

    def generate(self, user_skills: list, job_description: str, designation: str = "") -> str:
        skills_str = ", ".join(user_skills) if user_skills else "None provided"
        designation_str = designation if designation else "Not specified"

        prompt = f"""You are an expert career coach for a professional in Mumbai, India.

CURRENT DESIGNATION: {designation_str}
CURRENT SKILLS: {skills_str}

TARGET JOB: {job_description}

Create a personalized **Career GPS Roadmap** in clean Markdown format:

# 🚀 Career GPS: From {designation_str} to Your Next Role

## 📊 Skill Match Assessment
(Estimate % match, list strengths and skill gaps)

## 🎯 Short-Term Goals (0–6 months)
(Quick wins, free courses, mini projects to build immediately)

## 🛤️ Medium-Term Goals (6–18 months)
(Hands-on experience, portfolio projects, certifications)

## 🌟 Long-Term Vision (18+ months)
(Senior roles, leadership, specialization paths)

## ⚠️ Potential Roadblocks & How to Overcome Them

## 📚 Top Resources
(Free & paid — prefer India-friendly: GeeksforGeeks, freeCodeCamp, Udemy, NPTEL, etc.)

Be motivating, realistic, and tailor advice to the Indian job market (Mumbai, Bengaluru startups, TCS, Infosys, Zomato, Flipkart, etc.)."""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        response = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        })

        if response.status_code != 200:
            raise ValueError(f"Gemini API error {response.status_code}: {response.text}")

        data = response.json()

        # Check for blocked response
        if "candidates" not in data or len(data["candidates"]) == 0:
            raise ValueError(f"No candidates in response: {data}")

        candidate = data["candidates"][0]

        # Check finish reason
        finish_reason = candidate.get("finishReason", "")
        if finish_reason == "SAFETY":
            raise ValueError("Response blocked by Gemini safety filters")

        if "content" not in candidate:
            raise ValueError(f"No content in candidate: {candidate}")

        if "parts" not in candidate["content"]:
            raise ValueError(f"No parts in content: {candidate['content']}")

        return candidate["content"]["parts"][0]["text"]
