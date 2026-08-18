# app/services/decision_engine.py
# VISION-FIRST + GEMINI FALLBACK + ANCHOR BACKSTOP
# SINGLE-SCALE, SIZE-INVARIANT, PRODUCTION-SAFE

import cv2
import os
import uuid
from app.services.detector import detect, decode_image, crop, calculate_iou
from app.services.vision_service import describe, localize_objects
from app.core.prompts import PERSON_PROMPT, OBJECT_PROMPT
from app.config.env import env

TMP_DIR = "/tmp/person_crops"
DEBUG_DIR = "/tmp/debug_boxes"
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

MAX_SIDE = 1024

SMALL_ITEM_TYPES = {"earring", "earrings", "ring", "finger ring"}
SMALL_ITEM_MAX_REL_AREA = 0.02  # 2% of person bbox area
SMALL_ITEM_MIN_REL_AREA = 0.0001  # 0.01% of person bbox area

def box_area(box):
    return max(0, (box["x2"] - box["x1"])) * max(0, (box["y2"] - box["y1"]))

def rel_area(box, person_bbox):
    pb_area = box_area(person_bbox)
    return (box_area(box) / pb_area) if pb_area > 0 else 0.0

def clamp_box_to_image(box, shape):
    h, w = shape[:2]
    return {
        "x1": max(0, min(w, box["x1"])),
        "y1": max(0, min(h, box["y1"])),
        "x2": max(0, min(w, box["x2"])),
        "y2": max(0, min(h, box["y2"])),
    }




# =================================================
# RESIZE (SINGLE SOURCE OF TRUTH)
# =================================================
def resize_image_with_aspect(image, max_side=MAX_SIDE):
    h, w = image.shape[:2]
    if max(h, w) <= max_side:
        return image, 1.0
    scale = max_side / max(h, w)
    return (
        cv2.resize(image, (int(w * scale), int(h * scale)), cv2.INTER_AREA),
        scale
    )


# =================================================
# BBOX UTILS
# =================================================
def bbox_from_xyxy(b):
    return {"x1": int(b[0]), "y1": int(b[1]), "x2": int(b[2]), "y2": int(b[3])}


def valid_bbox(b, shape):
    if not b:
        return False
    h, w = shape[:2]
    return (
        0 <= b["x1"] < b["x2"] <= w and
        0 <= b["y1"] < b["y2"] <= h
    )

# =================================================
# DEBUG DRAW (RESIZED SPACE)
# =================================================
def draw_debug(resized_img, person_bbox, items):
    name = str(uuid.uuid4()) + ".jpg"
    img = resized_img.copy()

    # draw person box
    cv2.rectangle(
        img,
        (person_bbox["x1"], person_bbox["y1"]),
        (person_bbox["x2"], person_bbox["y2"]),
        (0, 255, 0),
        3
    )

    for it in items:
        b = it["bbox"]
        if b is None:
            # skip drawing if no coordinates
            continue

        cv2.rectangle(
            img,
            (b["x1"], b["y1"]),
            (b["x2"], b["y2"]),
            (0, 0, 255),
            2
        )
        cv2.putText(
            img,
            it["type"] or "item",
            (b["x1"], max(20, b["y1"] - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )

    path = f"{DEBUG_DIR}/{name}"
    cv2.imwrite(path, img)
    return f"debug/{name}"



# =================================================
# CONVERSIONS (ALL IN RESIZED SPACE)
# =================================================
def vision_norm_to_resized(norm, person_bbox, crop_shape):
    ch, cw = crop_shape[:2]
    return {
        "x1": person_bbox["x1"] + int(norm["x1"] * cw),
        "y1": person_bbox["y1"] + int(norm["y1"] * ch),
        "x2": person_bbox["x1"] + int(norm["x2"] * cw),
        "y2": person_bbox["y1"] + int(norm["y2"] * ch),
    }


def gemini_relative_to_resized(rel, person_bbox, crop_shape):
    ch, cw = crop_shape[:2]
    ymin, xmin, ymax, xmax = rel

    x1 = person_bbox["x1"] + int(xmin * cw / 1000)
    y1 = person_bbox["y1"] + int(ymin * ch / 1000)
    x2 = person_bbox["x1"] + int(xmax * cw / 1000)
    y2 = person_bbox["y1"] + int(ymax * ch / 1000)

    # Clamp to resized image bounds
    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}



def fallback_bbox(person_bbox):
    w = person_bbox["x2"] - person_bbox["x1"]
    h = person_bbox["y2"] - person_bbox["y1"]
    return {
        "x1": person_bbox["x1"] + int(w * 0.2),
        "y1": person_bbox["y1"] + int(h * 0.25),
        "x2": person_bbox["x1"] + int(w * 0.8),
        "y2": person_bbox["y1"] + int(h * 0.7),
    }



# =================================================
# PERSON MODE — VISION FIRST, GEMINI SECOND, ANCHOR LAST
# =================================================
async def analyze_person_mode(resized_image, detections):
    persons = [d for d in detections if d["label"] == "person"]
    persons.sort(
        key=lambda d: (d["bbox"][2] - d["bbox"][0]) *
                      (d["bbox"][3] - d["bbox"][1]),
        reverse=True
    )

    out = []

    for idx, det in enumerate(persons[:1]):
        person_bbox = bbox_from_xyxy(det["bbox"])

        person_crop = crop(
            resized_image,
            [person_bbox["x1"], person_bbox["y1"],
             person_bbox["x2"], person_bbox["y2"]],
            pad=2
        )

        cv2.imwrite(f"{TMP_DIR}/person_{idx+1}.jpg", person_crop)

        attrs = await describe(person_crop, PERSON_PROMPT)

        try:
            vision_items = localize_objects(person_crop) or []
        except Exception:
            vision_items = []

        items = []

        for src, relation in [
            (attrs.get("wearing", []), "wearing"),
            (attrs.get("carrying", []), "carrying")
        ]:
            for obj in src:
                t = (obj.get("type") or "").lower()

                item = choose_best_bbox(
                    obj,
                    relation,
                    t,
                    vision_items,
                    person_bbox,
                    person_crop,
                    resized_image
                )
                items.append(item)

        debug_url = draw_debug(resized_image, person_bbox, items)
        final_url = f"{env('BASE_URL')}{debug_url}"
        out.append({
            "person_id": f"person_{idx+1}",
            "input_type": "person",
            "bbox": person_bbox,
            "crop_ref": f"/crops/person_{idx+1}.jpg",
            "debug_url": final_url,
            "items": items
        })

    return {"data": out}


# =================================================
# OBJECT MODE
# =================================================
async def analyze_object_mode(resized_image):
    attrs = await describe(resized_image, OBJECT_PROMPT)

    try:
        vision = localize_objects(resized_image) or []
    except Exception:
        vision = []

    bbox = None
    if vision and "bbox_norm" in vision[0]:
        h, w = resized_image.shape[:2]
        n = vision[0]["bbox_norm"]
        bbox = {
            "x1": int(n["x1"] * w),
            "y1": int(n["y1"] * h),
            "x2": int(n["x2"] * w),
            "y2": int(n["y2"] * h),
        }

    if not valid_bbox(bbox, resized_image.shape):
        h, w = resized_image.shape[:2]
        bbox = {
            "x1": int(w * 0.25),
            "y1": int(h * 0.25),
            "x2": int(w * 0.75),
            "y2": int(h * 0.75),
        }

    # Normalize attrs to list
    if isinstance(attrs, dict):
        attrs = [attrs]

    if not isinstance(attrs, list):
        raise TypeError(f"Expected list or dict from describe(), got {type(attrs)}")

    clean_items = []

    for item in attrs:
        # HARD GUARD
        if not isinstance(item, dict):
            print("⚠️ Skipping invalid item:", item)
            continue

        item["bbox"] = bbox
        clean_items.append(item)

    attrs = clean_items

    return {
        "data": [{
            "object_id": "object_1",
            "input_type": "object",
            "items": attrs
        }]
    }


# =================================================
# ENTRY
# =================================================
# async def analyze_image(file):
#     orig_image = decode_image(await file.read())
#     resized, _ = resize_image_with_aspect(orig_image)
#     detections = detect(resized)

#     if any(d["label"] == "person" for d in detections):
#         return await analyze_person_mode(resized, detections)

#     return await analyze_object_mode(resized)

async def analyze_image(file):
    # orig_image = decode_image(await file.read())
    orig_image = decode_image(file)
    
    resized, _ = resize_image_with_aspect(orig_image)
    detections = detect(resized)

    if any(d["label"] == "person" for d in detections):
        return await analyze_person_mode(resized, detections)
    
    return await analyze_object_mode(orig_image)

SYNONYMS = {
    "blazer": {"blazer", "jacket", "coat"},
    "top": {"top", "shirt", "t-shirt", "tee", "blouse"},
    "denim shorts": {"shorts", "denim shorts", "jean shorts"},
    "earring": {"earring", "earrings", "jewelry"},
    "ring": {"ring", "jewelry"},
    "cell phone": {"cell phone", "phone", "mobile", "smartphone"},
    "makeup":{"lipstick, eyeliner, eyeshadow"}
}

def label_match(gem_type, vision_label):
    g = (gem_type or "").lower().strip()
    v = (vision_label or "").lower().strip()
    for key, vals in SYNONYMS.items():
        if g in vals and v in vals:
            return True
    # fallback substring
    return g in v or v in g


def near_point(box, pt, max_dist_px=24):
    # center of box vs landmark point
    cx = (box["x1"] + box["x2"]) // 2
    cy = (box["y1"] + box["y2"]) // 2
    dx = abs(cx - pt[0]); dy = abs(cy - pt[1])
    return (dx*dx + dy*dy) <= (max_dist_px * max_dist_px)

def small_item_valid(box, person_bbox, resized_shape, item_type, landmarks=None):
    # size gate
    ra = rel_area(box, person_bbox)
    if ra < SMALL_ITEM_MIN_REL_AREA or ra > SMALL_ITEM_MAX_REL_AREA:
        return False

    # landmark gate
    if landmarks is None:
        # Without landmarks, be conservative: reject unless Vision was precise
        return False

    if item_type in {"earring", "earrings"}:
        ear_pts = []
        if "left_ear" in landmarks: ear_pts.append(landmarks["left_ear"])
        if "right_ear" in landmarks: ear_pts.append(landmarks["right_ear"])
        return any(near_point(box, p) for p in ear_pts)

    if item_type in {"ring", "finger ring"}:
        hand_pts = []
        for k in ("right_index_tip","right_index_dip","left_index_tip","left_index_dip","right_ring_tip","left_ring_tip"):
            if k in landmarks: hand_pts.append(landmarks[k])
        return any(near_point(box, p) for p in hand_pts)

    return True  # non-small items


def choose_best_bbox(
    obj,
    relation,
    t,
    vision_items,
    person_bbox,
    person_crop,
    resized_image,
    landmarks=None
):
    # --- Vision candidates ---
    matched_visions = []
    for v in vision_items:
        if label_match(t, v.get("label")) and "bbox_norm" in v:
            vbox = vision_norm_to_resized(v["bbox_norm"], person_bbox, person_crop.shape)
            vbox = clamp_box_to_image(vbox, resized_image.shape)
            if valid_bbox(vbox, resized_image.shape):
                matched_visions.append(vbox)

    # --- Gemini candidate ---
    gem_candidate = None
    if obj.get("bbox_relative"):
        gc = gemini_relative_to_resized(obj["bbox_relative"], person_bbox, person_crop.shape)
        gc = clamp_box_to_image(gc, resized_image.shape)
        if valid_bbox(gc, resized_image.shape):
            gem_candidate = gc

    # --- Decide best (Vision > Gemini) ---
    if matched_visions:
        bbox, conf = matched_visions[0], "precise"
    elif gem_candidate:
        bbox, conf = gem_candidate, "approximate"
    else:
        bbox, conf = None, "none"

    # --- Small-item policy: earrings/rings must pass size + landmark gates ---
    item_type = (t or "").lower()
    if item_type in SMALL_ITEM_TYPES:
        if bbox is None:
            # already null
            pass
        else:
            if not small_item_valid(bbox, person_bbox, resized_image.shape, item_type, landmarks):
                bbox, conf = None, "none"

    return {
        **{k: obj.get(k) for k in ("category","type","subtype","color","shade","brand","gender","pattern")},
        "bbox": bbox,          # <-- can be None
        "relation": relation,
        "confidence": conf
    }
