MODELS_PROMPT = """
Return ONLY valid JSON.
Analyze ONLY the PERSON visible in the image crop.
IGNORE background, furniture, walls, floor, people in distance, reflections.

Identify:
- All clothing worn on the body

For EACH item you MUST return ALL fields below.
If a value cannot be determined, return null (do NOT omit keys).



Allowed categories (choose ONE):
- footwear
- clothing

ACCESSORY RULES:

Inspect head, face, neck, shoulders, wrists, fingers, and waist.

If an item is WORN or ATTACHED to the body
(using frame, strap, clasp, hook, or resting support)
→ include it in "wearing".

RULES:
- subtype MUST be null
- pattern = plain unless a visible design exists
- color = dominant visible body/frame color
- lenses or reflections DO NOT decide color

FOOTWEAR RULES:

Inspect feet and ankle region.

If any item is worn on the feet
→ include it in "wearing" with category = footwear.

TYPE (REQUIRED):
- Closed footwear covering toes → shoes
- Open footwear with exposed toes/heel → sandal

SUBTYPE (REQUIRED):
- Visible laces → lace-up
- No fastening → slip-on
- Heel elevation visible → heeled
- Otherwise → flat

PATTERN (REQUIRED):
- No visible design → plain
- Graphics/logos/text → printed
- Linear bands → striped
- Grid/squares → checked
- Decorative stitching → embroidered | handwork

COLOR (REQUIRED):
- Use dominant visible color(s), max 3, comma-separated
- Ignore shadows, dirt, highlights

GENDER:
- If clearly gender-specific design → male or female
- Otherwise → unisex

BRAND:
- Include ONLY if logo/text is clearly readable
- Otherwise → null

RULES:
- subtype MUST NOT be null
- pattern MUST NOT be null
- bbox_relative must tightly cover the footwear only


CLOTHING RULES:

Inspect the entire body for garments worn on torso, arms, waist, and legs.
All garments MUST be included in "wearing" with category = clothing.

────────────────
TYPE (REQUIRED)
────────────────

UPPER BODY:

- Full front opening (buttons/zip)
  AND worn as inner garment
  → Shirt

- Pullover, short or medium length
  → Shirt

- Pullover, long and clearly below hip
  → Kurtas

- Tailored outer garment worn over clothes
  AND structured shoulders + lapels
  AND part of a formal or semi-formal outfit
  → Blazer

- Outer garment worn over clothes
  AND casual or non-formal tailoring
  (denim, leather, bomber, casual zip style)
  → Jackets

- Outer garment worn over clothes
  AND clearly padded, bulky, or winterwear
  → Blazer

- Otherwise
  → Top


LOWER BODY:
- Denim texture/stitching → jeans
- Two separate legs → pant
- Loose with elastic/drawstring waist → pajama
- No leg separation → skirt
- Ends above knee → shorts

ONE-PIECE:
- Covers torso + legs → dress

DRAPED:
- Shoulder/neck cloth → dupatta
- Full unstitched drape → saree

TYPE MUST ALWAYS BE ONE OF ABOVE.

────────────────
TYPE (REQUIRED)
────────────────

The value of `type` MUST be selected ONLY from the following list.
The text MUST match EXACTLY as written (case, spelling, spacing).
DO NOT add new values.
DO NOT modify, normalize, pluralize, or infer.
If none apply clearly → return null.

ALLOWED TYPE VALUES (ENUM ONLY):

"Polo Shirt"
"T-Shirt"
"Shirt"
"Top"
"Jackets"
"Hoodie"
"Kurtas"
"Blazer"
"suit jacket"
"Jeans"
"Trousers"
"Dress Pants"
"Joggers"
"Boots"
"Flats"
"Sneakers"
"Sunglasses"
"Dress Shirt"
"Dress Shoes"
"Button-down Shirt"
"Pant"
"Blouse"

RULES:
- `type` MUST NOT be null if an item is detected
- `type` MUST be exactly ONE value from the list above
- `type` MUST NEVER be a category name
- NO synonyms or alternate names allowed


────────────────
SUBTYPE RULES (MODEL MUST CHOOSE ONE):
────────────────

UPPER BODY SUBTYPES:

- Sleeves extend below elbow → full-sleeve
- Sleeves cover shoulder and upper arm only → half-sleeve
- No visible sleeves → sleeveless
- Garment length ends clearly above waist → cropped
- Garment length covers torso with no clear sleeve signal → full-length

LOWER BODY SUBTYPES:

LOWER BODY SUBTYPE RULES:

- If leg is visibly tight/narrow along calf
  AND extra fabric bunches or stacks around ankle
  (folds/wrinkles due to excess length)
  → narrow-bottom

- If ankle hem is explicitly gathered, ribbed, or banded
  AND leg above ankle is relaxed or straight
  (jogger-style construction)
  → elastic-bottom

- If leg widens noticeably below the knee
  → bell-bottom

- If leg is wide and loose from thigh downward
  (palazzo, flared-wide, flowy)
  → palazzo | wide-leg

- If leg width is mostly uniform and no clear taper feature exists
  → straight



────────────────
PATTERN (REQUIRED)
────────────────

- No visible design → plain
- Text/graphics/motifs → printed
- Grid/squares → checked
- Linear bands → striped
- Decorative stitching → embroidered | handwork

PATTERN MUST NEVER BE NULL FOR CLOTHING.

────────────────
COLOR (REQUIRED)
────────────────

- Dominant visible color(s)
- Max 3, comma-separated
- Ignore shadows and lighting

────────────────
GENDER
────────────────

- Clearly gender-specific → male | female
- Otherwise → unisex

────────────────
BRAND
────────────────

- Include ONLY if logo/text is clearly readable
- Otherwise → null

────────────────
FINAL RULES
────────────────

- subtype MAY be null if no shape rule matches
- brand is NEVER guessed
- bbox_relative MUST tightly fit garment only
 

{
  "wearing": [
    {
      "category": "clothing | footwear | accessory | jewelry | makeup",
      "type": "ENUM VALUE ONLY",
      "subtype": "ENUM OR null",
      "color": "string or null",
      "shade": "string or null",
      "pattern": "plain | printed | embroidered | handwork | null",
      "brand": null,
      "gender": "male | female | unisex | null",
      "bbox_relative": [0,0,1000,1000]
    }
  ],
  "carrying": [
    {
      "category": "object | bag | accessory",
      "type": "string",
      "subtype": null,
      "color": "string or null",
      "shade": null,
      "pattern": null,
      "brand": null,
      "gender": null,
      "bbox_relative": [0,0,1000,1000]
    }
  ]
}

Rules (MANDATORY):
- If the person is holding something in hands → carrying
- If worn on the body → wearing
- NEVER invent brands
- NEVER include background objects
- ALWAYS include bbox_relative
- If unsure, still return best visible guess (do not drop the item)
"""