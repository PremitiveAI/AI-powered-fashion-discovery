# app/core/promptts.py

PERSON_PROMPT = """
Return ONLY valid JSON.
Analyze ONLY the PERSON visible in the image crop.
IGNORE background, furniture, walls, floor, people in distance, reflections.

Identify:
- All clothing worn on the body
- All accessories, footwear, jewelry
- ANY object the person is HOLDING, CARRYING, or WEARING

For EACH item you MUST return ALL fields below.
If a value cannot be determined, return null (do NOT omit keys).


══════════════════════════════
BOUNDING BOX RULE
══════════════════════════════
Coordinate system:
- bbox_relative MUST be [ymin, xmin, ymax, xmax]
- Values are integers from 0 to 1000
- Coordinates are RELATIVE TO THE PROVIDED IMAGE CROP ONLY
- Bounding box must be TIGHT and only cover the visible pixels of that item


Allowed categories (choose ONE):
- accessory
- footwear
- clothing
- object
- jewelry
- makeup

ACCESSORY RULES:

Inspect head, face, neck, shoulders, wrists, fingers, and waist.

If an item is WORN or ATTACHED to the body
(using frame, strap, clasp, hook, or resting support)
→ include it in "wearing".

ACCESSORY vs JEWELRY:
- If the item is decorative or functional BUT NOT time-keeping
  → category = accessory
- If the item is worn on wrist/finger/neck and is ornamental or time-related
  → category = jewelry

ACCESSORY TYPES (examples, not exhaustive):
- sunglasses, goggles, eyeglasses
- cap, hat, helmet
- handbag, backpack, sling bag (if worn)
- scarf, mask
- belt | cap | hat
- tie | bow-tie 
type MUST NEVER be "accessory".

RULES:
- subtype MUST be null
- pattern = plain unless a visible design exists
- color = dominant visible body/frame color
- lenses or reflections DO NOT decide color
- bbox_relative must tightly cover the item only

If an item is HELD IN HAND → it goes to "carrying", NOT accessory.

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
  → shirt

- Pullover, short or medium length
  → tshirt

- Pullover, long and clearly below hip
  → kurti

- Tailored outer garment worn over clothes
  AND structured shoulders + lapels
  AND part of a formal or semi-formal outfit
  → blazer

- Outer garment worn over clothes
  AND casual or non-formal tailoring
  (denim, leather, bomber, casual zip style)
  → jacket

- Outer garment worn over clothes
  AND clearly padded, bulky, or winterwear
  → coat

- Otherwise
  → top


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


OBJECT RULES:

Inspect both hands, forearms, and any item supported by the body.

IF an item is HELD, GRASPED, CARRIED, or SUPPORTED by the hands or arms
→ include it in "carrying" with category = object.

TYPE (REQUIRED):
- Use a clear, visible object name
  (e.g. mobile phone, water bottle, paper, box, cup, umbrella, key)

SUBTYPE:
- Always null

PATTERN:
- Always null

COLOR:
- Dominant visible color(s), max 3
- Ignore reflections and lighting
- If unclear → null

SHADE:
- Always null

GENDER:
- Always null

BRAND:
- Include ONLY if logo/text is clearly readable
- Otherwise → null

RULES:
- Objects MUST NEVER appear in "wearing"
- Worn items (clothing, footwear, accessories, jewelry, makeup)
  MUST NEVER be classified as object
- bbox_relative MUST tightly cover the object only

JEWELRY RULES:

Inspect neck, ears, wrists, fingers, ankles, and waist.

If an item is WORN directly on the body
for adornment or time-keeping
(using strap, clasp, hook, or chain)
→ include it in "wearing" with category = jewelry.

TYPE (REQUIRED):
- Wrist timepiece → watch
- Item worn on finger → ring
- Item worn on wrist, arm, neck, or ankle → bracelet | chain | anklet (choose closest)
- Item worn on ear → earring

SUBTYPE:
- Always null

PATTERN:
- No visible design → plain
- Decorative or carved work → embroidered | handwork
- Otherwise → plain

COLOR:
- Dominant visible metal or material color
  (e.g. gold, silver, black)
- Ignore shine and reflections

SHADE:
- Always null

GENDER:
- Clearly gender-specific design → male | female
- Otherwise → unisex

BRAND:
- Include ONLY if logo/text is clearly readable
- Otherwise → null

RULES:
- Jewelry MUST NEVER appear in "carrying"
- Smart watch or analog watch → jewelry (not accessory)
- Eyewear, bags, caps → NOT jewelry
- bbox_relative MUST tightly cover the jewelry item only

MAKEUP RULES:

Inspect face strictly in this order:
1) Lips
2) Cheeks
3) Eyes

Include ONLY these makeup types:
lipstick | blush | eyeliner | eye shadow

Makeup items are ALWAYS:
- category = makeup
- subtype = null
- pattern = solid
- brand = null
- bbox_relative MUST tightly cover only the makeup region

────────────────
LIPSTICK (ABSOLUTE GATE — FIRST STEP):
────────────────

STEP 1 — PRESENCE DECISION (MANDATORY):

Lipstick is PRESENT ONLY IF ALL are true:
- Lip color is clearly cosmetic AND
- Color is uniform, opaque, or stylized AND
- Edges look painted or enhanced beyond natural skin lips

Lipstick is NOT PRESENT IF ANY are true:
- Lips look natural, uneven, or skin-textured
- Color variation matches natural lip tone
- Brownish or pinkish lips WITHOUT visible cosmetic texture
- No clear paint boundary or cosmetic layer

🚫 If lipstick is NOT PRESENT:
→ DO NOT include any lipstick item at all.
→ STOP lipstick processing.

STEP 2 — ATTRIBUTE ASSIGNMENT (ONLY IF PRESENT):

type = lipstick
subtype = null
pattern = solid

COLOR (MANDATORY):
red | dark red | pink | nude | brown | plum | coral | orange | burgundy

SHADE (MANDATORY — NEVER NULL):
- Choose closest descriptive shade
- If unclear → "unspecified"

Allowed shades:
baby pink | soft pink | rose | nude pink | nude brown |
peach | coral | hot pink |
brick red | wine red | maroon |
plum | brown nude |
orange red | unspecified


────────────────
BLUSH
────────────────
- Include ONLY if cosmetic pigment is clearly visible
  and applied symmetrically on both cheeks.
- Natural redness, acne, or lighting ≠ blush.

If blush present:
type = blush

COLOR (MANDATORY):
pink | rose | peach | coral | nude | brown
- Multiple colors allowed if clearly visible

SHADE (MANDATORY):
- Choose closest shade
- If unclear → "unspecified"

────────────────
EYELINER
────────────────
- Include ONLY if a clear cosmetic line is visible
  along the upper or lower eyelid margin.
- Mascara or lash thickness ≠ eyeliner.

If eyeliner present:
type = eyeliner

COLOR (MANDATORY):
black | brown | blue | green | purple
- Multiple colors allowed for graphic / dual-tone liner

SHADE:
- ALWAYS null

────────────────
EYE SHADOW
────────────────
- Include ONLY if cosmetic pigment is visible
  on eyelid ABOVE lash line.
- Skin tone or lighting ≠ eye shadow.

If eye shadow present:
type = eye shadow

COLOR (MANDATORY):
brown | nude | pink | purple | blue | green |
gold | silver | bronze | copper
- Multiple colors allowed if layered or separated

SHADE (MANDATORY):
- Choose closest visible shade
- If unclear → "unspecified"

────────────────
FINAL CONSTRAINTS
────────────────
- Makeup color MUST NEVER be null.
- Shade is REQUIRED for lipstick, blush, eye shadow.
- Shade is ALWAYS null for eyeliner.
- If a makeup item is not confidently visible → DO NOT include it.
- Natural lips → NO lipstick object at all.


Universal multi-color rule (APPLIES TO ALL ITEMS):

- An item may contain multiple colors.
- Return multiple colors ONLY if:
  a) The colors are clearly distinct and intentionally designed, AND
  b) The colors are a core visual feature of the item, not minor accents or patterns.

Color output rules:
- If a single color is visually dominant → return that color only.
- If multiple distinct colors are equally prominent →
  list them as a comma-separated string in the "color" field.
- Do NOT list more than 3 colors.
- Ignore minor accents, highlights, shadows, reflections, or gradients.

  

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


OBJECT_PROMPT = """
Return ONLY valid JSON.
Analyze ONLY the single visible object in the image crop.
IGNORE background, people, shadows, and reflections.

You MUST determine the object's category.
DO NOT return null or omit fields.

Allowed categories (choose ONE):
- accessory
- footwear
- clothing
- object
- jewelry
- makeup

ACCESSORY TYPES (examples, not exhaustive):
- sunglasses, goggles, eyeglasses
- cap, hat, helmet
- handbag, backpack, sling bag (if worn)
- scarf, mask
- belt | cap | hat
- tie | bow-tie 
type MUST NEVER be "accessory".

RULES:
- subtype MUST be null
- pattern = plain unless a visible design exists
- color = dominant visible body/frame color
- lenses or reflections DO NOT decide color
- bbox_relative must tightly cover the item only

If an item is HELD IN HAND → it goes to "carrying", NOT accessory.

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
  → shirt

- Pullover, short or medium length
  → tshirt

- Pullover, long and clearly below hip
  → kurti

- Tailored outer garment worn over clothes
  AND structured shoulders + lapels
  AND part of a formal or semi-formal outfit
  → blazer

- Outer garment worn over clothes
  AND casual or non-formal tailoring
  (denim, leather, bomber, casual zip style)
  → jacket

- Outer garment worn over clothes
  AND clearly padded, bulky, or winterwear
  → coat

- Otherwise
  → top


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


OBJECT RULES:

Inspect both hands, forearms, and any item supported by the body.

IF an item is HELD, GRASPED, CARRIED, or SUPPORTED by the hands or arms
→ include it in "carrying" with category = object.

TYPE (REQUIRED):
- Use a clear, visible object name
  (e.g. mobile phone, water bottle, paper, box, cup, umbrella, key)

SUBTYPE:
- Always null

PATTERN:
- Always null

COLOR:
- Dominant visible color(s), max 3
- Ignore reflections and lighting
- If unclear → null

SHADE:
- Always null

GENDER:
- Always null

BRAND:
- Include ONLY if logo/text is clearly readable
- Otherwise → null

RULES:
- Objects MUST NEVER appear in "wearing"
- Worn items (clothing, footwear, accessories, jewelry, makeup)
  MUST NEVER be classified as object
- bbox_relative MUST tightly cover the object only

JEWELRY RULES:

Inspect neck, ears, wrists, fingers, ankles, and waist.

If an item is WORN directly on the body
for adornment or time-keeping
(using strap, clasp, hook, or chain)
→ include it in "wearing" with category = jewelry.

TYPE (REQUIRED):
- Wrist timepiece → watch
- Item worn on finger → ring
- Item worn on wrist, arm, neck, or ankle → bracelet | chain | anklet (choose closest)
- Item worn on ear → earring

SUBTYPE:
- Always null

PATTERN:
- No visible design → plain
- Decorative or carved work → embroidered | handwork
- Otherwise → plain

COLOR:
- Dominant visible metal or material color
  (e.g. gold, silver, black)
- Ignore shine and reflections

SHADE:
- Always null

GENDER:
- Clearly gender-specific design → male | female
- Otherwise → unisex

BRAND:
- Include ONLY if logo/text is clearly readable
- Otherwise → null

RULES:
- Jewelry MUST NEVER appear in "carrying"
- Smart watch or analog watch → jewelry (not accessory)
- Eyewear, bags, caps → NOT jewelry
- bbox_relative MUST tightly cover the jewelry item only

MAKEUP RULES:

Inspect face strictly in this order:
1) Lips
2) Cheeks
3) Eyes

Include ONLY these makeup types:
lipstick | blush | eyeliner | eye shadow

Makeup items are ALWAYS:
- category = makeup
- subtype = null
- pattern = solid
- brand = null
- bbox_relative MUST tightly cover only the makeup region

────────────────
LIPSTICK (ABSOLUTE GATE — FIRST STEP):

STEP 1 — PRESENCE DECISION (MANDATORY):

Lipstick is PRESENT ONLY IF ALL are true:
- Lip color is clearly cosmetic AND
- Color is uniform, opaque, or stylized AND
- Edges look painted or enhanced beyond natural skin lips

Lipstick is NOT PRESENT IF ANY are true:
- Lips look natural, uneven, or skin-textured
- Color variation matches natural lip tone
- Brownish or pinkish lips WITHOUT visible cosmetic texture
- No clear paint boundary or cosmetic layer

🚫 If lipstick is NOT PRESENT:
→ DO NOT include any lipstick item at all.
→ STOP lipstick processing.

STEP 2 — ATTRIBUTE ASSIGNMENT (ONLY IF PRESENT):

type = lipstick
subtype = null
pattern = solid

COLOR (MANDATORY):
red | dark red | pink | nude | brown | plum | coral | orange | burgundy

SHADE (MANDATORY — NEVER NULL):
- Choose closest descriptive shade
- If unclear → "unspecified"

Allowed shades:
baby pink | soft pink | rose | nude pink | nude brown |
peach | coral | hot pink |
brick red | wine red | maroon |
plum | brown nude |
orange red | unspecified


────────────────
BLUSH
────────────────
- Include ONLY if cosmetic pigment is clearly visible
  and applied symmetrically on both cheeks.
- Natural redness, acne, or lighting ≠ blush.

If blush present:
type = blush

COLOR (MANDATORY):
pink | rose | peach | coral | nude | brown
- Multiple colors allowed if clearly visible

SHADE (MANDATORY):
- Choose closest shade
- If unclear → "unspecified"

────────────────
EYELINER
────────────────
- Include ONLY if a clear cosmetic line is visible
  along the upper or lower eyelid margin.
- Mascara or lash thickness ≠ eyeliner.

If eyeliner present:
type = eyeliner

COLOR (MANDATORY):
black | brown | blue | green | purple
- Multiple colors allowed for graphic / dual-tone liner

SHADE:
- ALWAYS null

────────────────
EYE SHADOW
────────────────
- Include ONLY if cosmetic pigment is visible
  on eyelid ABOVE lash line.
- Skin tone or lighting ≠ eye shadow.

If eye shadow present:
type = eye shadow

COLOR (MANDATORY):
brown | nude | pink | purple | blue | green |
gold | silver | bronze | copper
- Multiple colors allowed if layered or separated

SHADE (MANDATORY):
- Choose closest visible shade
- If unclear → "unspecified"

────────────────
FINAL CONSTRAINTS
────────────────
- Makeup color MUST NEVER be null.
- Shade is REQUIRED for lipstick, blush, eye shadow.
- Shade is ALWAYS null for eyeliner.
- If a makeup item is not confidently visible → DO NOT include it.
- Natural lips → NO lipstick object at all.


Universal multi-color rule (APPLIES TO ALL ITEMS):

- An item may contain multiple colors.
- Return multiple colors ONLY if:
  a) The colors are clearly distinct and intentionally designed, AND
  b) The colors are a core visual feature of the item, not minor accents or patterns.

Color output rules:
- If a single color is visually dominant → return that color only.
- If multiple distinct colors are equally prominent →
  list them as a comma-separated string in the "color" field.
- Do NOT list more than 3 colors.
- Ignore minor accents, highlights, shadows, reflections, or gradients.



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

Rules:
- category is REQUIRED and NEVER null
- brand ONLY if clearly readable
- Be precise and concise
"""

