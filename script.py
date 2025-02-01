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
import yaml

# Load configuration from YAML file
def load_config(config_file="config.yaml"):
    """Loads configuration from a YAML file."""
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

config = load_config()

# Configure logging
logging.basicConfig(filename=config["logging"]["filename"], level=logging.getLevelName(config["logging"]["level"]),
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# --- Gemini API Configuration ---
GOOGLE_API_KEY = os.environ.get(config["api"]["key_env_variable"])
if not GOOGLE_API_KEY:
    logging.error("API Key not found. Set %s environment variable.", config["api"]["key_env_variable"])
    raise EnvironmentError(f"API Key not found. Set {config['api']['key_env_variable']} environment variable.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name=config["api"]["model_name"])

# --- Constants for API Handling ---
MAX_RETRIES = config["api"]["max_retries"]
INITIAL_DELAY = config["api"]["initial_delay"]
DELAY_BETWEEN_REQUESTS = config["api"]["delay_between_requests"]

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
                Analyze the image and provide the following information in JSON format, specifically tailored for listing on Adobe Stock to maximize sales and visibility. Focus on providing high-quality, relevant information that would be valuable to potential buyers. **Consider the "7 Ws" (Who, What, Where, When, Why, How, Mood) to make your descriptions and title more comprehensive.**

                **Instructions:**

                1. **Suggest a Short, Effective Sales Title (Max 7 words):**  Create a concise and compelling title that will grab a buyer's attention and clearly describe the image's main subject. Think like a buyer searching for images on Adobe Stock. Incorporate relevant keywords naturally. Avoid generic titles. **Address the "7 Ws" where possible (Who, What, Where, When, Mood, Concept).**

                2. **Provide a Basic Description:**  Offer a straightforward, factual description of the image's visual content. **Incorporate "7 Ws" details.**

                3. **Write a Persuasive Description for Clients (Max 150 characters):**  Describe the image in a way that highlights its benefits and potential uses for clients. Imagine how a buyer might use this image for their projects. Incorporate context and relevant keywords naturally. Focus on being concise and persuasive. **Incorporate "7 Ws" details where relevant.**

                4. **Suggest Descriptive Keywords (5-10 keywords):**  List keywords that literally describe the visual elements present in the image (e.g., objects, people, setting, colors). Prioritize the most important and visually prominent elements. **Focus on keywords related to "7 Ws".**

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

                # Formatear el JSON con indentación
                analysis_results = json.loads(json_text)
                formatted_json = json.dumps(analysis_results, indent=4)  # Usar indent=4 para una indentación de 4 espacios
                logging.info(f"Formatted Gemini API analysis:\n{formatted_json}")

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
    return " ".join(description_parts)[:config["adobe_stock"]["max_persuasive_description_length"]]

def generate_default_filename(filename: str) -> str:
    """Generates a default filename using the original filename and generic abbreviations."""
    base_name = os.path.splitext(filename)[0]
    abbreviated_name = "".join([config["abbreviations"].get(word.lower(), word[:4].capitalize()) for word in base_name.split("_")[:3]])
    return f"{abbreviated_name}_Img_Data"


def generate_keywords(analysis_results: Dict, title: str, description: str) -> List[str]:
    """
    Generates a list of optimized keywords for Adobe Stock search.
    This version prioritizes Gemini's keywords, expands synonyms, and adds keywords from title/description.
    """
    keywords = set()

    # Add keywords from Gemini's analysis
    keywords.update(analysis_results.get("descriptive_keywords", []))
    keywords.update(analysis_results.get("conceptual_keywords", []))
    keywords.update(analysis_results.get("stylistic_keywords", []))
    keywords.update(analysis_results.get("seasonal_keywords", []))

    # Add keywords from title and description with synonym expansion
    text_to_process = [title.lower(), description.lower()]
    for text in text_to_process:
        for word in text.split():
            word = word.strip()  # Remove leading/trailing spaces
            if word and word not in config["common_words"] and len(word) > 2:
                if word in config["synonyms"]:
                    keywords.update(config["synonyms"][word])  # Expand synonyms
                else:
                    keywords.add(word) #Add original word if no synonym

    # Remove duplicates and limit to 25 keywords
    unique_keywords = list(keywords)[:25]

    return unique_keywords


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
        parts.extend([config["abbreviations"].get(style.lower(), style[:4]) for style in key_styles[:1]])
    if distinctive_elements:
        parts.extend([config["abbreviations"].get(elem.lower(), elem[:4]) for elem in distinctive_elements[:1]])
    if base_description:
      parts.extend([config["abbreviations"].get(word.lower(), word[:3]) for word in base_description.split()[:2]])

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
        return [config["abbreviations"].get(use, use) for use in use_cases][:3]
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
        return [config["abbreviations"].get(ta, ta) for ta in audiences][:3]
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
       parts = [config["abbreviations"].get(word, word[:3]) for word in base_description.split()[:2]]
       filename_parts.extend(parts)
    if use_cases:
        filename_parts.extend(use_cases[:2])
    if target_audience:
        filename_parts.extend(target_audience[:2])

    base_filename = "_".join(filter(None, filename_parts)).replace(" ", "_")
    base_filename = re.sub(r'[^a-zA-Z0-9_]+', '', base_filename)

    MAX_FILENAME_LENGTH = config["adobe_stock"]["max_filename_length"]
    _, extension = os.path.splitext(original_filename)
    extension = extension[1:].lower()

    if len(base_filename) + len(extension) + 1 > MAX_FILENAME_LENGTH:
        base_filename = base_filename[:MAX_FILENAME_LENGTH - len(extension) - 1]

    if not base_filename:  # Fallback if everything else fails
        name = os.path.splitext(original_filename)[0]
        # Keep original underscores in fallback
        return f"{name}_Img_Data.{extension}"

def generate_final_output(analysis_results: Dict, original_filename: str, category: str = "", releases: str = "") -> Dict:
    """
    Generates the final output for Adobe Stock, with a simplified title and keyword generation, including call to action.
    """
    suggested_title = analysis_results.get("suggested_title", "")
    persuasive_description = analysis_results.get("persuasive_description", "")
    keywords = generate_keywords(analysis_results, suggested_title, persuasive_description)
    use_cases = suggest_use_cases(analysis_results, suggested_title, persuasive_description)

    max_title_length = config["adobe_stock"]["max_title_length"]
    combined_title_parts = [config["adobe_stock"]["title_prefix"]]
    current_title_length = len(combined_title_parts[0])

    # Use suggested title as base if it exists
    if suggested_title:
        combined_title_parts.append(suggested_title)
        current_title_length += len(suggested_title) + 1 # +1 for the space

    # Add keywords to the title if there's space
    descriptive_keywords = analysis_results.get("descriptive_keywords", [])
    conceptual_keywords = analysis_results.get("conceptual_keywords", [])
    combined_keywords = descriptive_keywords + conceptual_keywords

    for keyword in combined_keywords:
        if current_title_length + len(keyword) + 1 <= max_title_length: # +1 for space
            combined_title_parts.append(keyword)
            current_title_length += len(keyword) + 1
        else:
            break

    combined_title = " ".join(combined_title_parts).strip()

    # Add Call to Action if there is space
    import random
    call_to_action_phrase = random.choice(config["call_to_action"])
    if current_title_length + len(call_to_action_phrase) + 3 <= max_title_length: # +3 accounts for " - " separator
        combined_title_parts.append(f" - {call_to_action_phrase}")
        combined_title = " ".join(combined_title_parts).strip() # Re-join with call to action

    # Truncate if necessary (final safety truncation after adding call to action)
    if len(combined_title) > max_title_length:
        combined_title = combined_title[:max_title_length].rsplit(' ', 1)[0]


    return {
        "Filename": original_filename,
        "Title": combined_title,
        "Keywords": ", ".join(keywords),
        "Category": category,
        "Releases": releases,
        "Use Cases": ", ".join(use_cases)
    }

def process_image(image_path: str, category: str = "", releases: str = "") -> Dict:
    """Processes a single image file with robust error handling at all stages."""
    original_filename = os.path.basename(image_path)  # Extract only the filename
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
    parser.add_argument("-config", "--config_file", help="Path to the configuration file.", default="config.yaml") # Added config argument
    args = parser.parse_args()

    directory_path = args.directory
    category = args.category
    releases = args.releases
    config_file = args.config_file # Get config file from argument
    processed_data = []

    global config  # Declare config as global
    config = load_config(config_file) # Load config using the specified config file

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
    csv_filename = f"LucasLopez_{timestamp}.csv"  # Replace "xxxxxxx" with your name
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