import os
import argparse
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Any
import google.generativeai as genai
import re
import time
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

# Configure logging
logging.basicConfig(filename='image_processing.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# --- Gemini API Configuration ---
try:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # For local execution
except ImportError:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # For local execution
if not GOOGLE_API_KEY:
    logging.error("API Key not found. Set GOOGLE_API_KEY environment variable or Colab Secret.")
    raise EnvironmentError("API Key not found. Set GOOGLE_API_KEY environment variable or Colab Secret.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

# --- Constants for API Handling ---
MAX_RETRIES = 5
INITIAL_DELAY = 1
DELAY_BETWEEN_REQUESTS = 1

# --- Gemini API Interaction ---
def analyze_image_content_gemini(image_path: str, max_retries: int = MAX_RETRIES, initial_delay: int = INITIAL_DELAY) -> Dict[str, Any]:
    """Analyzes image content using the Gemini API, enforcing JSON format and handling errors with retries."""
    logging.info(f"Analyzing image with Gemini API: {image_path}")
    default_error_response = {
        "suggested_title": "Unprocessed Image",
        "basic_description": "A basic description of the image.",
        "persuasive_description": "A default description for images that cannot be analyzed.",
        "key_styles": [],
        "distinctive_elements": [],
        "base_description": "A basic, plain description for fallback."
    }
    for attempt in range(max_retries):
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

            contents = [
                {
                    "mime_type": "image/png" if image_path.lower().endswith(".png") else "image/jpeg",
                    "data": image_data
                },
"""
                Analyze the image and provide the following information in JSON format, specifically tailored for listing on Adobe Stock to maximize sales and visibility.  Focus on providing high-quality, relevant information that would be valuable to potential buyers.  **Consider the "7 Ws" (Who, What, Where, When, Why, How, Mood) to make your descriptions and title more comprehensive.**

                **Instructions:**

                1. **Suggest a Short, Effective Sales Title (Max 7 words):**  Create a concise and compelling title that will grab a buyer's attention and clearly describe the image's main subject.  Think like a buyer searching for images on Adobe Stock.  Incorporate relevant keywords naturally. Avoid generic titles. **Address the "7 Ws" where possible (Who, What, Where, When, Mood, Concept).**

                2. **Provide a Basic Description:**  Offer a straightforward, factual description of the image's visual content. **Incorporate "7 Ws" details.**

                3. **Write a Persuasive Description for Clients (Max 150 characters):**  Describe the image in a way that highlights its benefits and potential uses for clients. Imagine how a buyer might use this image for their projects.  Incorporate context and relevant keywords naturally.  Focus on being concise and persuasive. **Incorporate "7 Ws" details where relevant.**

                4. **Suggest Descriptive Keywords (5-10 keywords):**  List keywords that literally describe the visual elements present in the image (e.g., objects, people, setting, colors).  Prioritize the most important and visually prominent elements. **Focus on keywords related to "7 Ws".**

                5. **Suggest Conceptual Keywords (3-5 keywords):**  List keywords that represent the abstract or emotional associations evoked by the image (e.g., serenity, joy, adventure, success, creativity). **Consider "Mood" and "Concept" from "7 Ws".**

                6. **Suggest Stylistic Keywords (3-5 keywords):**  List keywords that describe the artistic or technical style of the image (e.g., digital art, watercolor, black and white, panoramic, flat lay, HDR, illustration, painting).

                7. **Suggest Seasonal Keywords (0-2 keywords, only if applicable):** If the image is clearly related to a specific season, holiday, or time of year, suggest relevant seasonal keywords (e.g., Christmas, Summer, Autumn, Back to School, Winter). If not applicable, leave this list empty.

                **Important Considerations for all Keywords:**

                * **Relevance:** Keywords must be highly relevant to the image content. Irrelevant keywords are detrimental.
                * **Specificity:** Prefer specific keywords over general ones (e.g., "Golden Gate Bridge" instead of "Bridge").
                * **Quality over Quantity:** Focus on providing a smaller set of highly relevant and effective keywords rather than filling up the keyword limit with less relevant terms.
                * **Avoid Redundancy:** Do not repeat similar keywords or synonyms.

                **JSON Output Format:**

                Respond strictly in JSON format as follows:

                ```json
                {
                "suggested_title": "Concise and effective sales title (max 7 words)",
                "basic_description": "A basic, factual description of the image",
                "persuasive_description": "Client-focused description highlighting benefits and uses (max 250 characters)",
                "descriptive_keywords": ["keyword1", "keyword2", "keyword3", ...],
                "conceptual_keywords": ["keyword1", "keyword2", "keyword3", ...],
                "stylistic_keywords": ["keyword1", "keyword2", "keyword3", ...],
                "seasonal_keywords": ["keyword1", "keyword2", ...],
                "base_description": "A basic, plain description for fallback."
                }

            If the image is abstract, describe the emotions and interpretations it may evoke.
            """
            ]

            response = model.generate_content(contents)
            logging.info(f"Raw Gemini API response: {response.text!r}")

            if response.prompt_feedback and response.prompt_feedback.blockReason:
                logging.error(f"Gemini API blocked the prompt for {image_path}. Reason: {response.prompt_feedback.blockReason}")
                return default_error_response

            if not response.candidates:
                logging.error(f"Gemini API returned no candidates for {image_path}.")
                return default_error_response

            json_text = response.text.strip()
            try:
                if json_text.startswith('```json'):
                    json_text = json_text[len('```json'):].strip()
                if json_text.endswith('```'):
                    json_text = json_text[:-len('```')].strip()
                analysis_results = json.loads(json_text)
                logging.info(f"Gemini API analysis successful for {image_path}")
                return analysis_results
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding Gemini API response for {image_path}: {e}, Text: {json_text}")
                default_error_response["persuasive_description"] = response.text
                return default_error_response
            except TypeError as e:
                logging.error(f"TypeError processing Gemini response for {image_path}: {e}, Text: {json_text}")
                default_error_response["persuasive_description"] = response.text
                return default_error_response

        except (ResourceExhausted, ServiceUnavailable) as e:
            logging.warning(f"Gemini API quota or availability error for {image_path} (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logging.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Failed to analyze {image_path} after {max_retries} retries due to API errors.")
                return default_error_response
        except Exception as e:
            logging.error(f"Error analyzing image {image_path} with Gemini API: {e}")
            return default_error_response
        finally:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    return default_error_response

# --- Metadata Generation Functions ---
DEFAULT_ABBREVIATIONS = {
    "abstract": "Abstr",
    "illustration": "Illust",
    "painting": "Paint",
    "digital": "Dig",
    "art": "Art",
    "commercial": "Com",
    "advertising": "Adv",
    "marketing": "Mkt",
    "editorial": "Edit",
    "social media": "Social",
    "web design": "Web",
    "creative": "Cre",
    "artists": "Art",
    "designers": "Des",
    "marketers": "Mkt",
    "editors": "Edit",
    "content creators": "Cont",
    "small business": "SmallBiz",
    "image": "Img",
    "fantasy": "Fant",
    "realistic": "Real",
    "portrait" : "Port",
    "landscape" : "Land",
    "unique": "Uniq",
    "original": "Orig",
    "impactful": "Imp",
    "eye-catching": "Eye",
    "exclusive": "Excl",
    "menacing": "Menac",
    "heroic": "Hero",
    "stylized": "Styl",
    "detailed": "Deta",
    "evocative": "Evoc",
    "striking": "Stri",
    "minimalist": "Min",
    "geometric": "Geom",
    "organic": "Org",
    "vibrant": "Vibr",
    "dynamic": "Dyn",
    "elegant": "Eleg",
    "modern": "Mod",
    "vintage": "Vint",
    "rustic": "Rust",
    "urban": "Urb",
    "nature": "Nat",
    "people": "Peop",
    "animal": "Anim",
    "object": "Obj",
    "concept": "Conc",
    "background": "Bkg",
    "texture": "Text",
    "pattern": "Patt",
    "graphic": "Graph",
    "design": "Des",
    "template": "Temp",
    "mockup": "Mock",
    "print": "Prnt",
    "website": "Web",
    "banner": "Ban",
    "poster": "Post",
    "brochure": "Broch",
    "flyer": "Fly",
    "card": "Card",
    "invitation": "Invit",
    "branding": "Brand",
    "identity": "Ident",
    "corporate": "Corp",
    "business": "Biz",
    "professional": "Prof",
    "clean": "Clean",
    "simple": "Simp",
    "complex": "Complx",
    "bright": "Bright",
    "dark": "Dark",
    "colorful": "Color",
    "monochrome": "Mono",
    "grayscale": "Gray",
    "sepia": "Sepia",
    "warm": "Warm",
    "cool": "Cool",
    "summer": "Sum",
    "winter": "Win",
    "autumn": "Aut",
    "spring": "Spr",
    "night": "Night",
    "day": "Day",
    "sunrise": "Sunr",
    "sunset": "Suns",
    "indoors": "In",
    "outdoors": "Out",
    "close-up": "Close",
    "macro": "Mac",
    "wide": "Wide",
    "aerial": "Aer",
    "lifestyle": "Life",
    "travel": "Trav",
    "food": "Food",
    "fashion": "Fash",
    "beauty": "Beaut",
    "health": "Health",
    "technology": "Tech",
    "education": "Educ",
    "science": "Sci",
    "finance": "Fin",
    "real estate": "RE",
    "event": "Evnt",
    "holiday": "Holi",
    "celebration": "Celebr",
    "music": "Music",
    "sport": "Sport",
    "game": "Game",
    "religion": "Relig",
    "culture": "Cult",
    "history": "Hist",
    "family": "Fam",
    "friendship": "Friend",
    "love": "Love",
    "happy": "Hap",
    "sad": "Sad",
    "angry": "Angry",
    "calm": "Calm",
    "excited": "Excit",
    "serious": "Ser",
    "playful": "Play",
    "powerful": "Pow",
    "gentle": "Gent",
    "dynamic": "Dyn",
    "static": "Stat",
    "isolated": "Isol",
    "group": "Group",
    "single": "Sing",
    "multiple": "Mult",
    "front": "Front",
    "back": "Back",
    "side": "Side",
    "top": "Top",
    "bottom": "Bot",
    "view": "View",
    "shot": "Shot",
    "composition": "Comp",
    "depth": "Depth",
    "focus": "Foc",
    "light": "Light",
    "shadow": "Shad",
    "tone": "Tone",
    "color": "Col",
    "shape": "Shape",
    "form": "Form",
    "line": "Line",
    "space": "Space",
    "balance": "Bal",
    "harmony": "Harm",
    "contrast": "Contr",
    "unity": "Unity",
    "rhythm": "Rhythm",
    "emphasis": "Emph",
    "pattern": "Patt",
    "texture": "Text",
    "surface": "Surf",
    "material": "Mat",
    "element": "Elem",
    "detail": "Det",
    "structure": "Struct",
    "process": "Proc",
    "concept": "Conc",
    "idea": "Idea",
    "symbol": "Symb",
    "metaphor": "Metaph",
    "emotion": "Emo",
    "feeling": "Feel",
    "mood": "Mood",
    "atmosphere": "Atm",
    "story": "Story",
    "narrative": "Narr",
    "message": "Msg",
    "meaning": "Mean",
    "purpose": "Purp",
    "function": "Func",
    "use": "Use",
    "application": "Appl",
    "solution": "Sol",
    "benefit": "Ben",
    "advantage": "Adv",
    "value": "Val",
    "quality": "Qual",
    "style": "Style",
    "technique": "Techn",
    "medium": "Med",
    "genre": "Genre",
    "category": "Cat",
    "type": "Type",
    "kind": "Kind"
}

SYNONYMS = {
    "helmet": ["headgear", "casque", "helm", "protective headwear"],
    "mask": ["face covering", "disguise", "visage", "facial mask", "face mask"],
    "eyes": ["optics", "orbs", "peepers", "visual organs", "sight organs"],
    "horns": ["antlers", "protrusions", "spikes", "pointed growths", "horn-like structures"],
    "illustration": ["artwork", "drawing", "depiction", "graphic art", "pictorial representation"],
    "knight": ["warrior", "cavalier", "mounted soldier", "armored fighter"],
    "portrait": ["image", "likeness", "representation", "figure", "depiction of a person"],
    "landscape": ["scenery", "view", "vista", "natural vista", "geographic view"],
    "design": ["composition", "layout", "art", "arrangement", "visual plan"],
    "abstract": ["non-representational", "conceptual", "symbolic", "non-figurative", "unrealistic"],
    "unique": ["original", "distinctive", "singular", "exclusive", "uncommon", "rare"],
    "original": ["unique", "novel", "fresh", "authentic", "new", "innovative"],
    "impactful": ["striking", "powerful", "impressive", "moving", "forceful", "effective"],
    "eye-catching": ["arresting", "noticeable", "standout", "attention-grabbing", "striking", "conspicuous"],
    "exclusive": ["limited", "rare", "one-of-a-kind", "uncommon", "restricted", "private"],
    "serenity": ["calmness", "peacefulness", "tranquility", "peace", "stillness", "quietude"],
    "adventure": ["exploration", "journey", "expedition", "quest", "thrill", "excitement"],
    "romance": ["affection", "love", "intimacy", "passion", "courtship", "tenderness"],
    "success": ["achievement", "triumph", "victory", "accomplishment", "prosperity", "fulfillment"],
    "mountain": ["peak", "mount", "summit", "highland", "upland"],
    "lake": ["pond", "reservoir", "pool", "body of water", "inland sea"],
    "sunset": ["sundown", "dusk", "evening", "twilight", "setting sun"],
    "water": ["liquid", "H2O", "aqua", "fluid", "beverage"],
    "sky": ["heavens", "firmament", "atmosphere", "airspace", "upper atmosphere"],
    "trees": ["woods", "forest", "grove", "woodland", "timber"],
    "reflection": ["mirror image", "image", "replication", "duplication", "reproduction"],
    "orange sky": ["fiery sky", "amber sky", "sunset sky", "colorful sky", "vibrant sky"],
    "calmness": ["serenity", "tranquility", "peace", "stillness", "quiet"],
    "peacefulness": ["serenity", "calmness", "tranquility", "quietude", "harmony"],
    "tranquility": ["serenity", "calmness", "peacefulness", "repose", "placidity"],
    "peace": ["serenity", "tranquility", "calmness", "harmony", "restfulness"],
    "stillness": ["quietness", "silence", "hush", "motionlessness", "immobility"],
    "quietude": ["quietness", "tranquility", "serenity", "peace", "calm"],
    "exploration": ["adventure", "discovery", "investigation", "voyage", "travel"],
    "journey": ["trip", "voyage", "travel", "adventure", "excursion"],
    "expedition": ["journey", "adventure", "voyage", "exploration", "mission"],
    "quest": ["adventure", "mission", "search", "pursuit", "endeavor"],
    "thrill": ["excitement", "adventure", "rush", "kick", "stimulation"],
    "excitement": ["thrill", "adventure", "enthusiasm", "agitation", "arousal"],
    "affection": ["love", "romance", "tenderness", "fondness", "warmth"],
    "love": ["affection", "romance", "passion", "devotion", "adoration"],
    "intimacy": ["closeness", "affection", "familiarity", "nearness", "warmth"],
    "passion": ["love", "romance", "ardor", "zeal", "fervor"],
    "courtship": ["romance", "dating", "engagement", "wooing", "suing"],
    "tenderness": ["affection", "gentleness", "kindness", "warmth", "softness"],
    "achievement": ["success", "accomplishment", "attainment", "realization", "feat"],
    "triumph": ["victory", "success", "conquest", "mastery", "win"],
    "victory": ["triumph", "win", "success", "conquest", "defeat of opponent"],
    "accomplishment": ["achievement", "success", "feat", "realization", "fulfillment"],
    "prosperity": ["wealth", "affluence", "riches", "fortune", "success"],
    "fulfillment": ["satisfaction", "achievement", "success", "contentment", "gratification"],
    "peak": ["mountain", "summit", "mountaintop", "height", "apex"],
    "mount": ["mountain", "peak", "rise", "hill", "elevation"],
    "summit": ["peak", "top", "apex", "crest", "highest point"],
    "highland": ["mountainous region", "upland", "elevated land", "mountain area", "high country"],
    "upland": ["highland", "elevated region", "plateau", "high ground", "hill country"],
    "pond": ["small lake", "pool", "waterhole", "basin", "still water"],
    "reservoir": ["artificial lake", "water storage", "basin", "tank", "water supply"],
    "pool": ["pond", "puddle", "watering hole", "basin", "small body of water"],
    "body of water": ["lake", "river", "sea", "ocean", "stream"],
    "inland sea": ["large lake", "landlocked sea", "salt lake", "great lake", "large body of water"],
    "sundown": ["sunset", "dusk", "evening", "twilight", "nightfall"],
    "dusk": ["sunset", "twilight", "evening", "sundown", "gloaming"],
    "evening": ["dusk", "nightfall", "sunset", "twilight", "late day"],
    "twilight": ["dusk", "sunset", "evening", "gloaming", "crepuscule"],
    "setting sun": ["sunset", "sundown", "evening sun", "sun going down", "sun dipping below horizon"],
    "liquid": ["water", "fluid", "beverage", "solution", "potion"],
    "aqua": ["water", "light blue", "cyan", "turquoise", "watery color"],
    "fluid": ["liquid", "water", "flowing substance", "liquid matter", "molten"],
    "beverage": ["drink", "liquid", "refreshment", "potion", "libation"],
    "heavens": ["sky", "firmament", "celestial sphere", "upper atmosphere", "air"],
    "firmament": ["sky", "heavens", "vault of heaven", "expanse of sky", "atmosphere"],
    "atmosphere": ["sky", "air", "airspace", "gases surrounding earth", "ambient air"],
    "airspace": ["sky", "air", "upper atmosphere", "flight space", "air lanes"],
    "upper atmosphere": ["sky", "stratosphere", "ionosphere", "exosphere", "outer air"],
    "woods": ["forest", "trees", "woodland", "grove", "copse"],
    "forest": ["woods", "woodland", "trees", "jungle", "rainforest"],
    "grove": ["small forest", "orchard", "copse", "thicket", "woodlot"],
    "woodland": ["forest", "woods", "grove", "copse", "forested area"],
    "timber": ["wood", "lumber", "logs", "wood for building", "forest resources"],
    "mirror image": ["reflection", "duplicate", "reversal", "copy", "echo"],
    "duplicate": ["copy", "replica", "reproduction", "clone", "mirror image"],
    "reversal": ["opposite", "inverse", "contrary", "backward", "mirror image"],
    "copy": ["duplicate", "replica", "reproduction", "imitation", "clone"],
    "echo": ["reverberation", "reflection", "resonation", "repeat", "mirror image"],
    "fiery sky": ["orange sky", "red sky", "vibrant sky", "colorful sky", "dramatic sky"],
    "amber sky": ["orange sky", "yellow-orange sky", "golden sky", "warm sky", "sunset sky"],
    "sunset sky": ["evening sky", "twilight sky", "dusk sky", "sky at sunset", "sky during sundown"],
    "colorful sky": ["vibrant sky", "multicolored sky", "rainbow sky", "bright sky", "sky with many colors"],
    "vibrant sky": ["colorful sky", "bright sky", "intense sky", "lively sky", "dynamic sky"],
    "attention-grabbing": ["eye-catching", "striking", "noticeable", "arresting", "prominent"],
    "attention-getting": ["eye-catching", "noticeable", "striking", "arresting", "prominent"],
    "noticeable": ["eye-catching", "visible", "perceptible", "observable", "evident"],
    "arresting": ["eye-catching", "striking", "captivating", "compelling", "fascinating"],
    "standout": ["eye-catching", "prominent", "remarkable", "distinctive", "conspicuous"],
    "prominent": ["standout", "noticeable", "conspicuous", "obvious", "remarkable"],
    "remarkable": ["notable", "outstanding", "exceptional", "striking", "standout"],
    "distinctive": ["unique", "characteristic", "peculiar", "special", "standout"],
    "conspicuous": ["noticeable", "obvious", "evident", "prominent", "standout"]
}

def generate_default_main_title(filename: str) -> str:
    """Generates a default main title using information from the filename."""
    name_part = os.path.splitext(filename)[0].replace("_", " ").capitalize()
    return f"{name_part} Image"

def generate_default_detailed_description(filename: str, analysis_results: Dict) -> str:
    """Generates a default detailed description using available information."""
    base_description = analysis_results.get("basic_description", "A visually compelling image.")
    key_styles = analysis_results.get("key_styles", [])
    distinctive_elements = analysis_results.get("distinctive_elements", [])

    description_parts = [base_description, "Perfect for your next project."]
    if key_styles:
      description_parts.append(f"Featuring elements of {', '.join(key_styles)}.")
    if distinctive_elements:
      description_parts.append(f"Notably showcasing {', '.join(distinctive_elements)}.")
    return " ".join(description_parts)[:250]

def generate_default_filename(filename: str) -> str:
    """Generates a default filename using the original filename and generic abbreviations."""
    base_name = os.path.splitext(filename)[0]
    abbreviated_name = "".join([DEFAULT_ABBREVIATIONS.get(word.lower(), word[:4].capitalize()) for word in base_name.split("_")[:3]])
    return f"{abbreviated_name}_Img_Data"

def generate_compact_title_and_use_case(analysis_results: Dict, filename: str) -> str:
    """Generates a compact title and use case string, ensuring it does not exceed 200 characters."""
    title_parts = []
    use_case_parts = []

    suggested_title = analysis_results.get("suggested_title", "")
    if suggested_title:
       title_parts.append(suggested_title)
    else:
       base_description = analysis_results.get("basic_description", "")
       if base_description:
           title_parts.extend(base_description.split()[:2])
       title_parts.extend(generate_default_main_title(filename).split()[:3])

    persuasive_description = analysis_results.get("persuasive_description", "").lower()
    suggested_use_cases = analysis_results.get("suggested_use_cases", [])
    suggested_target_audience = analysis_results.get("suggested_target_audience", [])

    use_case_parts = []
    if suggested_use_cases:
       use_case_parts.extend([DEFAULT_ABBREVIATIONS.get(use, use[:3]) for use in suggested_use_cases[:1]])
    if suggested_target_audience:
      use_case_parts.extend([DEFAULT_ABBREVIATIONS.get(ta, ta[:3]) for ta in suggested_target_audience[:1]])

    combined_string = f"{' '.join(title_parts).capitalize()} - {' & '.join(use_case_parts)}".strip()

    return combined_string[:200]

def generate_keywords(analysis_results: Dict, title: str, description: str) -> List[str]:
    """Generates a list of optimized keywords for Adobe Stock search."""
    keywords = set()
    text_to_process = [
        title.lower(),
        analysis_results.get("basic_description", "").lower(),
        analysis_results.get("persuasive_description", "").lower()
    ]

    for text in text_to_process:
      for word in text.split():
          if word in SYNONYMS:
            keywords.update(SYNONYMS[word])
          else:
            keywords.add(word)

    # Remove common and empty keywords
    common_words = {"a", "an", "the", "for", "with", "of", "is", ""}
    unique_keywords = [keyword for keyword in keywords if keyword not in common_words]

    return list(unique_keywords)[:25] # Limit to 25 keywords

def generate_main_title(analysis_results: Dict) -> str:
    """Generates an attractive title with selling keywords, prioritizing Gemini's suggestions."""
    if analysis_results.get("suggested_title"):
        return analysis_results["suggested_title"]

    title_parts = []
    key_styles = analysis_results.get("key_styles", [])[:2]
    distinctive_elements = analysis_results.get("distinctive_elements", [])[:2]

    title_parts.extend([style.replace(" ", "") for style in key_styles if style])
    title_parts.extend([re.sub(r'\W+', '', elem) for elem in distinctive_elements if elem])

    if title_parts:
        return " ".join(title_parts).capitalize()

    base_description = analysis_results.get("basic_description")
    if base_description:
        return base_description[:50].capitalize()

    filename = os.path.basename("")  # This will be an empty string
    name_part = os.path.splitext(filename)[0].replace("_", " ").capitalize()
    return f"{name_part} - Image"

def generate_title_variants(main_title: str, analysis_results: Dict) -> List[str]:
    """Generates variants of the main title for different use cases."""
    variants = [main_title]
    key_styles = analysis_results.get("key_styles", [])
    distinctive_elements = analysis_results.get("distinctive_elements", [])

    if key_styles:
        variants.append(f"{main_title} - {key_styles[0]}")
    if distinctive_elements:
        variants.append(f"{main_title} - {distinctive_elements[0]}")

    return variants

def generate_detailed_description(filename: str, analysis_results: Dict) -> str:
    """Generates a structured and persuasive description, prioritizing Gemini's insights."""
    if analysis_results.get("persuasive_description"):
        return analysis_results["persuasive_description"]

    base_description = analysis_results.get("basic_description")
    if base_description:
        return base_description

    description_parts = []
    key_styles = analysis_results.get("key_styles", [])
    distinctive_elements = analysis_results.get("distinctive_elements", [])

    if base_description:
        description_parts.append(base_description)
    if key_styles:
        description_parts.append(f"Featuring elements of {', '.join(key_styles)}.")
    if distinctive_elements:
        description_parts.append(f"Notably showcasing {', '.join(distinctive_elements)}.")

    if not description_parts:
        return "A default description for images that cannot be analyzed."

    call_to_action = [
        "Perfect for your next creative project.",
        "Ideal for capturing the attention of your audience.",
        "Elevate your content with this impactful visual.",
        "Use it to make a statement.",
        "Enhance your project with this striking image.",
        "Make your message unforgettable with this visual asset.",
        "Grab attention and make an impact.",
        "Bring your vision to life with this compelling artwork.",
        "A valuable addition to any creative toolkit.",
        "Unlock your project's potential with this image.",
        "Drive engagement with this captivating visual.",
        "Transform your content with this high-quality image.",
        "Add a professional touch to your designs.",
        "Stand out from the crowd with this unique visual.",
        "Create visually stunning projects effortlessly.",
        "Inspire your audience with this remarkable image.",
        "Boost your brand with this powerful visual.",
        "Get your message across effectively.",
        "Make a lasting impression with this image.",
        "The perfect visual solution for your needs."
    ]
    
    import random
    description_parts.append(random.choice(call_to_action))
    return " ".join(description_parts)[:250].strip()

def generate_concise_description(analysis_results: Dict) -> str:
    """Generates a concise description for the filename."""
    parts = []
    suggested_title = analysis_results.get("suggested_title", "")
    key_styles = analysis_results.get("key_styles", [])
    distinctive_elements = analysis_results.get("distinctive_elements", [])
    base_description = analysis_results.get("basic_description", "")
    if suggested_title:
      parts.extend(suggested_title.lower().split()[:2])
    if key_styles:
        parts.extend([DEFAULT_ABBREVIATIONS.get(style.lower(), style[:4]) for style in key_styles[:1]])
    if distinctive_elements:
        parts.extend([DEFAULT_ABBREVIATIONS.get(elem.lower(), elem[:4]) for elem in distinctive_elements[:1]])
    if base_description:
      parts.extend([DEFAULT_ABBREVIATIONS.get(word.lower(), word[:3]) for word in base_description.split()[:2]])

    return "_".join(parts)[:50]

def suggest_use_cases(analysis_results: Dict, title: str, description: str) -> List[str]:
    """Suggests relevant use cases based on the analysis results, title and description"""
    keywords = set()
    text_to_process = [
        title.lower(),
        analysis_results.get("basic_description", "").lower(),
        analysis_results.get("persuasive_description", "").lower()
    ]

    for text in text_to_process:
      for word in text.split():
          keywords.add(word)

    use_cases = []
    if "advertising" in keywords or "commercial" in keywords or "marketing" in keywords:
        use_cases.append("Commercial")
    if "editorial" in keywords:
        use_cases.append("Editorial")
    if "social" in keywords or "media" in keywords:
       use_cases.append("Social Media")
    if "web" in keywords or "design" in keywords:
        use_cases.append("Web Design")
    if "creative" in keywords or "art" in keywords or "illustration" in keywords or "painting" in keywords or "drawing" in keywords:
       use_cases.append("Creative")

    if use_cases:
        return [DEFAULT_ABBREVIATIONS.get(use, use) for use in use_cases][:3]
    else:
        return ["Image"]
    
def suggest_target_audience(analysis_results: Dict, title: str, description: str) -> List[str]:
    """Suggests target audience based on the analysis results, title and description"""
    keywords = set()
    text_to_process = [
        title.lower(),
        analysis_results.get("basic_description", "").lower(),
        analysis_results.get("persuasive_description", "").lower()
    ]

    for text in text_to_process:
      for word in text.split():
          keywords.add(word)

    audiences = []
    if "artists" in keywords or "art" in keywords:
        audiences.append("Artists")
    if "designers" in keywords or "design" in keywords:
        audiences.append("Designers")
    if "marketers" in keywords or "marketing" in keywords:
       audiences.append("Marketers")
    if "editors" in keywords or "editorial" in keywords:
        audiences.append("Editors")
    if "content" in keywords or "creators" in keywords:
        audiences.append("Content Creators")
    if "small" in keywords or "business" in keywords:
      audiences.append("Small Business")
    if audiences:
        return [DEFAULT_ABBREVIATIONS.get(ta, ta) for ta in audiences][:3]
    else:
        return ["Data"]

def generate_new_filename(original_filename: str, analysis_results: Dict) -> str:
    """Generates an informative and useful filename, with fallback."""
    concise_description = generate_concise_description(analysis_results)
    use_cases = suggest_use_cases(analysis_results, "", "")
    target_audience = suggest_target_audience(analysis_results, "", "")
    base_description = analysis_results.get("basic_description", "").lower()

    filename_parts = [concise_description]
    if base_description:
       parts = [DEFAULT_ABBREVIATIONS.get(word, word[:3]) for word in base_description.split()[:2]]
       filename_parts.extend(parts)
    if use_cases:
        filename_parts.extend(use_cases[:2])
    if target_audience:
        filename_parts.extend(target_audience[:2])

    base_filename = "_".join(filter(None, filename_parts)).replace(" ", "_")
    base_filename = re.sub(r'[^a-zA-Z0-9_]+', '', base_filename)

    MAX_FILENAME_LENGTH = 200
    _, extension = os.path.splitext(original_filename)
    extension = extension[1:].lower()

    if len(base_filename) + len(extension) + 1 > MAX_FILENAME_LENGTH:
        base_filename = base_filename[:MAX_FILENAME_LENGTH - len(extension) - 1]

    if not base_filename:  # Fallback if everything else fails
        name = os.path.splitext(original_filename)[0]
        # Keep original underscores in fallback
        return f"{name}_Img_Data.{extension}"

    # Ensure unique filenames with a counter
    filepath = os.path.join(os.path.dirname(original_filename), f"{base_filename}.{extension}")
    counter = 1
    while os.path.exists(filepath):
      base_filename_counter = f"{base_filename}_{counter}"
      filepath = os.path.join(os.path.dirname(original_filename), f"{base_filename_counter}.{extension}")
      counter += 1
    return f"{base_filename}{ '' if counter==1 else f'_{counter-1}'}.{extension}"

def generate_final_output(analysis_results: Dict, original_filename: str, category: str = "", releases: str = "") -> Dict:
    """Generates a dictionary with a format suitable for Adobe Stock CSV."""
    suggested_title = analysis_results.get("suggested_title", "")
    persuasive_description = analysis_results.get("persuasive_description", "")
    keywords = generate_keywords(analysis_results, suggested_title + " " + persuasive_description, persuasive_description)
    use_cases = suggest_use_cases(analysis_results, suggested_title, persuasive_description) # CALL suggest_use_cases

    max_title_length = 200
    combined_title_parts = []

    # Start with "Generative AI" at the beginning
    combined_title_parts = ["Generative AI"]

    # Add the suggested title if available
    if suggested_title:
        combined_title_parts.append(suggested_title)

    # Calculate the remaining space for the description (after "Generative AI" and suggested title)
    current_title_length = len(" ".join(combined_title_parts).strip())  # Calculate length so far
    remaining_length = max_title_length - current_title_length

    max_description_words_to_add = 9  # Limit description words to add
    description_words_added_count = 0
    if remaining_length > 0:
        # Try to add the first significant words of the description
        description_words = persuasive_description.split()
        added_description = ""
        for word in description_words:
            if description_words_added_count < max_description_words_to_add: # Check word count limit
                if current_title_length + len(added_description) + len(word) + 1 <= max_title_length:  # Check against updated current_title_length
                    added_description += (" " + word)
                    description_words_added_count += 1 # Increment counter
                else:
                    break  # Stop adding description words if title is too long
            else:
                break # Stop adding description words if word limit reached
        if added_description:
            combined_title_parts.append(added_description.strip())

    combined_title = " ".join(combined_title_parts).strip()

    # Truncate the entire title if it's still too long (unlikely now with word limit, but as a safety)
    if len(combined_title) > max_title_length:
        print(f"Title length before truncation: {len(combined_title)}")
        combined_title = combined_title[:max_title_length].rsplit(' ', 1)[0]
        print(f"Title truncated, new length: {len(combined_title)}, combined_title = '{combined_title}'")
    else:
        print("Title length is within limit, no truncation needed.")

    return {
        "Filename": original_filename,
        "Title": combined_title,
        "Keywords": ", ".join(keywords),
        "Category": category,
        "Releases": releases,
        "Use Cases": ", ".join(use_cases) # ADD "Use Cases" to the dictionary
    }
    
def process_image(image_path: str, category: str = "", releases: str = "") -> Dict:
    """Processes a single image file with robust error handling at all stages."""
    original_filename = os.path.basename(image_path)
    try:
        logging.info(f"Processing image: {image_path}")
        analysis_results = analyze_image_content_gemini(image_path)

        final_output = generate_final_output(analysis_results, original_filename, category, releases)

        return final_output

    except Exception as e:
        logging.error(f"Critical error processing image {image_path}: {e}")
        _, extension = os.path.splitext(original_filename)
        extension = extension[1:].lower()

        # Generate default metadata
        default_title = "Unprocessed Image"
        default_output = {
            "Filename": original_filename,
            "Title":  default_title,
            "Keywords": "",
            "Category": "",
            "Releases": ""
        }
        return default_output

def main():
    parser = argparse.ArgumentParser(description="Automates image tagging and renaming for Adobe Stock.")
    parser.add_argument("directory", help="Path to the directory to process.")
    parser.add_argument("-c", "--category", help="Category number for Adobe Stock.", default="")
    parser.add_argument("-r", "--releases", help="Comma-separated list of release names.", default="")
    args = parser.parse_args()

    directory_path = args.directory
    category = args.category
    releases = args.releases
    processed_data = []

    if not os.path.isdir(directory_path):
        logging.error(f"The specified directory does not exist: {directory_path}")
        print(f"Error: The directory '{directory_path}' does not exist.")
        return

    image_extensions = ('.jpg', '.jpeg', '.png')

    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename.lower().endswith(image_extensions):
                image_path = os.path.join(root, filename)
                result = process_image(image_path, category, releases)
                processed_data.append(result)

    # Generate log file with required name format
    timestamp = datetime.now().strftime("%Y_%m_%d")  # Date format as YYYY_MM_DD
    csv_filename = f"xxxxxx{timestamp}.csv"  # Replace "xxxxxxx" with your name
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # ADD "Use Cases" to fieldnames
            fieldnames = ["Filename", "Title", "Keywords", "Category", "Releases", "Use Cases"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for data in processed_data:
                writer.writerow(data)
        print(f"Processing report saved to '{csv_filename}'")
    except Exception as e:
        logging.error(f"Error saving the report: {e}")
        print(f"Error saving the report: {e}")

if __name__ == "__main__":
    main()