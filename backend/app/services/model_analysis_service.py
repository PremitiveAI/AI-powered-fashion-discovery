from google import genai
import uuid
import os
from app.config.env import env

client = genai.Client(api_key=env("GEMINI_API_KEY"))


def generate_prompt_from_image(image_path: str) -> str:
    """
    Generate a cinematic AI image generation prompt from uploaded image.
    Avoids skin and hair color.
    """

    with open(image_path, "rb") as img:
        image_bytes = img.read()

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            {
                "parts": [
                    {
                        "text": (
                            "You are an expert AI prompt engineer for image generation models like "
                            "Stable Diffusion, Midjourney, and DALL·E.\n\n"

                            "Analyze this image and convert it into one single detailed cinematic "
                            "image generation prompt.\n\n"

                            "Rules:\n"
                            "- Do NOT use bullet points\n"
                            "- Do NOT use headings\n"
                            "- Do NOT explain anything\n"
                            "- Return only one flowing paragraph\n"
                            "- Include background details, environment, lighting, mood, pose, posture,\n"
                            "  clothing type, clothing color, textures, fabrics, patterns,\n"
                            "  footwear, accessories, camera angle, and composition\n"
                            "- Avoid mentioning skin color and hair color\n"
                            "- Use professional photography and cinematic description style\n"
                            "- Make it detailed and generation-ready\n"
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_bytes
                        }
                    }
                ]
            }
        ]
    )

    return response.text.strip()

def generate_image_with_gemini1(user_bytes: bytes, prompt: str) -> bytes:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-image")

        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": user_bytes
                }
            ],
            request_options={"timeout": 60}
        )

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data"):
                return part.inline_data.data

        raise Exception("No image generated")

    except Exception as e:
        print("Gemini Error:", str(e))
        raise


def generate_image_with_gemini(user_bytes: bytes, prompt: str) -> bytes:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                prompt,
                genai.types.Part.from_bytes(
                    data=user_bytes,
                    mime_type="image/jpeg"
                )
            ],
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data

        raise Exception("No image returned")

    except Exception as e:
        print("Gemini error:", str(e))
        raise

