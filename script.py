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
                """Suggest a short, effective sales title for this image in English. Provide a basic description of the image. Describe the image for a client, highlighting its benefits and potential uses in English. List the key artistic styles and the most impactful distinctive elements of the image in English. Provide the response strictly in JSON format.

                Expected JSON Format:
                {
                  "suggested_title": "Short sales title",
                  "basic_description": "A basic, plain description of the image",
                  "persuasive_description": "Client-focused description highlighting benefits and uses",
                  "key_styles": ["Style 1", "Style 2"],
                  "distinctive_elements": ["Element 1", "Element 2"],
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
    "striking": "Stri"
}

SYNONYMS = {
    "helmet": ["headgear", "casque", "helm", "yelmo"],
    "mask": ["face covering", "disguise", "visage", "máscara"],
    "eyes": ["optics", "orbs", "peepers", "ojos"],
    "horns": ["antlers", "protrusions", "spikes", "cuernos"],
    "illustration": ["artwork", "drawing", "depiction", "ilustración"],
    "knight": ["warrior", "cavalier", "caballero"],
    "portrait": ["image", "likeness", "representation", "retrato"],
    "landscape": ["scenery", "view", "vista", "paisaje"],
    "design": ["composition", "layout", "arte", "diseño"],
    "abstract": ["non-representational", "conceptual", "simbólico", "abstracto"],
    "unique": ["original", "distinctive", "singular", "exclusivo"],
    "original": ["unique", "novel", "fresh", "auténtico"],
    "impactful": ["striking", "powerful", "impressive", "conmovedor"],
    "eye-catching": ["arresting", "noticeable", "standout", "llamativo"],
    "exclusive": ["limited", "rare", "one-of-a-kind", "exclusivo"]
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
        "Use it to make a statement."
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

    max_title_length = 200
    combined_title_parts = [suggested_title]

    # Calculate the remaining space for the description
    remaining_length = max_title_length - len(suggested_title)

    if remaining_length > 0:
        # Try to add the first significant words of the description
        description_words = persuasive_description.split()
        added_description = ""
        for word in description_words:
            if len(combined_title_parts[0]) + len(added_description) + len(word) + 1 <= max_title_length:
                added_description += (" " + word)
            else:
                break
        if added_description:
            combined_title_parts.append(added_description.strip())

    combined_title = " ".join(combined_title_parts).strip()

    return {
        "Filename": original_filename,
        "Title": combined_title,
        "Keywords": ", ".join(keywords),
        "Category": category,
        "Releases": releases,
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
    csv_filename = f"XXXXXXX{timestamp}.csv"  # Replace "XXXXXXX" with your name
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Filename", "Title", "Keywords", "Category", "Releases"]
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