# app/services/vision_service.py

import base64
import json
import re
import cv2
import asyncio

from google import genai
from google.genai import types
from google.cloud import vision
from google.oauth2 import service_account

from app.config.env import env

# -------------------------------------------------------------------
# Gemini (NEW SDK – REQUIRED)
# -------------------------------------------------------------------

genai_client = genai.Client(
    api_key=env("GOOGLE_API_KEY")
)

GEMINI_MODEL = "gemini-2.0-flash"

# -------------------------------------------------------------------
# Vision API
# -------------------------------------------------------------------

KEY_PATH = env("GOOGLE_APPLICATION_CREDENTIALS", default="vision-key.json")

credentials = service_account.Credentials.from_service_account_file(
    KEY_PATH
)

vision_client = vision.ImageAnnotatorClient(
    credentials=credentials
)

# -------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------

def clean_json(text: str) -> str:
    """
    Cleans Gemini response and extracts valid JSON.
    """
    if not text:
        return "{}"

    text = re.sub(r"```(?:json)?|```", "", text).strip()
    text = re.sub(r",\s*([\]\}])", r"\1", text)

    match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
    return match.group(1).strip() if match else "{}"

# -------------------------------------------------------------------
# Gemini Image Description
# -------------------------------------------------------------------

async def describe(image, prompt):
    """
    Uses Gemini to describe clothing/accessories in an image.
    Returns parsed JSON dict.
    """
    ok, buffer = cv2.imencode(".jpg", image)
    if not ok:
        return {}

    image_bytes = buffer.tobytes()
    loop = asyncio.get_event_loop()

    def _call_gemini():
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                ),
            ],
        )
        return response.text or ""

    raw = await loop.run_in_executor(None, _call_gemini)
    cleaned = clean_json(raw)

    try:
        return json.loads(cleaned)
    except Exception as e:
        print("JSON parse error:", e)
        print("Raw Gemini response:", raw)
        return {}

# -------------------------------------------------------------------
# Vision Object Localization
# -------------------------------------------------------------------

def localize_objects(image):
    """
    Uses Google Vision API for object localization.
    """
    ok, buffer = cv2.imencode(".jpg", image)
    if not ok:
        return []

    vision_image = vision.Image(content=buffer.tobytes())
    response = vision_client.object_localization(image=vision_image)

    objects = getattr(response, "localized_object_annotations", [])
    results = []

    for obj in objects:
        label = obj.name.lower()

        if "person" in label:
            continue

        xs = [v.x for v in obj.bounding_poly.normalized_vertices]
        ys = [v.y for v in obj.bounding_poly.normalized_vertices]

        results.append({
            "label": label,
            "bbox_norm": {
                "x1": min(xs),
                "y1": min(ys),
                "x2": max(xs),
                "y2": max(ys),
            },
            "score": float(obj.score),
        })

    return results

# -------------------------------------------------------------------
# Combined Vision + Gemini Pipeline
# -------------------------------------------------------------------

async def describe_with_vision_fallback(image, prompt):
    """
    1. Try Vision API for localization
    2. Use Gemini for attributes
    3. Fallback to Gemini-only if Vision fails
    """

    vision_detections = localize_objects(image)

    gemini_attrs = await describe(image, prompt)

    if vision_detections:
        primary_detection = max(
            vision_detections,
            key=lambda x: x["score"]
        )

        return {
            "vision_detection": primary_detection,
            "gemini_attributes": gemini_attrs,
            "localization_source": "vision_api",
            "confidence": "precise",
        }

    gemini_attrs["localization_source"] = "gemini_only"
    gemini_attrs["confidence"] = "approximate"
    return gemini_attrs
