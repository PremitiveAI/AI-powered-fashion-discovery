from google import genai
from google.genai import types
from PIL import Image
import io, os
from dotenv import load_dotenv
from app.core.photo_prompts import PHOTO_PROMPTS,USER_PROMPT 


load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not found")

client = genai.Client(api_key=api_key)

def _image_part(data: bytes, mime: str):
    return types.Part.from_bytes(data=data, mime_type=mime)

def generate_final_image_bytes(
    user_bytes: bytes,
    cloth_bytes: bytes,
    output_path: str
):

    model_id = "gemini-2.5-flash-image"

    contents = [
         types.Part.from_text(text=PHOTO_PROMPTS),
        types.Part.from_text(text=USER_PROMPT),
        _image_part(user_bytes, "image/jpeg"),
        _image_part(cloth_bytes, "image/jpeg")
    ]

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image = Image.open(io.BytesIO(part.inline_data.data))
            image.save(output_path)
            return
        
    # for part in response.candidates[0].content.parts:
    #     if part.inline_data:
    #         image = Image.open(io.BytesIO(part.inline_data.data))
    #         image.save(output_path)
    #         return

    raise RuntimeError("Gemini did not return an image")



def generate_final_image(user_photo_path, clothing_items_paths):
    # This model is the one ChatGPT/Gemini uses for "Nano Banana" image creation
    model_id = "gemini-2.5-flash-image"

    # Prepare images
    user_img = _image_part(user_photo_path)
    cloth_img = _image_part(clothing_items_paths)
    contents = [
        types.Part.from_text(
            text="TASK: Use the following person as the identity reference."
        ),
        user_img,
        types.Part.from_text(text="You are an image editing and virtual try-on system. Input includes one base image of a person and one reference image containing exactly one clothing item (shirt OR t-shirt OR pants OR jeans OR sunglasses ONLY). Your task is to apply ONLY the selected clothing item from the reference image onto the person in the base image. STRICT RULES: Replace ONLY the provided clothing category and nothing else. Do NOT modify, add, remove, or hallucinate any other clothing or accessories. If a shirt or t-shirt is selected, completely remove the existing upper-body clothing first, then apply the new item. If pants or jeans are selected, completely remove the existing lower-body clothing first, then apply the new item. If sunglasses are selected, replace ONLY the eyewear. Preserve the person’s face, body shape, pose, skin tone, hair, lighting, and background EXACTLY as in the base image. Use photorealistic rendering with correct fabric folds, shadows, and perspective. Use ONLY ONE reference image per generation. Do NOT mix garments. Do NOT generate or substitute any random clothing. Output a single realistic image where the person is wearing ONLY the selected clothing item from the reference image, correctly aligned and naturally fitted."),
        cloth_img
    ]


    # Detailed Instruction
    # final_prompt = (
    #     "You Are an Expert"
    #     "Don NOT change person clothes automatically and randomly"
    #     "only applied clohtes or accessories should be change"
    #     "person photo should be real don NOT generate randome image"
        
    # )
    # contents.append(types.Part.from_text(text=final_prompt))


    print("⏳ Weaving your new outfit... please wait.")

    # 2. Use generate_content with IMAGE modality
    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            # This is the secret: tell the model to return an IMAGE
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE")
            ]
        )
    )

    # 3. Extract and save the image from the parts
    for i, part in enumerate(response.candidates[0].content.parts):
        if part.inline_data:
            # Convert bytes to PIL Image
            img_data = part.inline_data.data
            img = Image.open(io.BytesIO(img_data))
            
            output_filename = f"final_tryon_{i}.png"
            img.save(output_filename)
            return output_filename

    raise RuntimeError("Model did not return an image part.")


def gemini_has_face(image_bytes: bytes) -> bool:
    contents = [
        types.Part.from_text(
            text=(
                "Answer ONLY YES or NO.\n"
                "Is this image suitable for a virtual clothing try-on?\n\n"
                "YES if:\n"
                "- The person is real\n"
                "- Face is visible\n"
                "- Upper body orientation is clear enough to place clothing\n\n"
                "NO if:\n"
                "- Image is too cropped\n"
                "- Only partial face (eyes only)\n"
                "- Heavy occlusion\n"
                "- Mannequin, artwork, or fake person"
            )
        ),
        _image_part(image_bytes, "image/jpeg")
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(
            max_output_tokens=3
        )
    )

    answer = (response.text or "").strip().upper()
    return answer == "YES"

def gemini_is_safe_tryon(image_bytes: bytes) -> bool:
    contents = [
        types.Part.from_text(
            text=(
                "Answer ONLY YES or NO.\n"
                "Is this image SAFE for a virtual clothing try-on?\n\n"
                "Answer NO if ANY of the following are present:\n"
                "- Nudity or near-nudity\n"
                "- Exposed breasts, buttocks, or genitals\n"
                "- Transparent or see-through clothing revealing body\n"
                "- Sexual posing or erotic intent\n"
                "- Underwear-only images\n"
                "- Lingerie or swimwear with sexual presentation\n"
                "- Adult sexual content\n\n"
                "Answer YES only if:\n"
                "- The person is clothed in normal clothing\n"
                "- No sexual or nude content is visible"
            )
        ),
        _image_part(image_bytes, "image/jpeg")
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(
            max_output_tokens=3
        )
    )

    answer = (response.text or "").strip().upper()
    return answer == "YES"


