# Image Metadata Automation Script for Adobe Stock

## Overview

This Python script automates the process of generating metadata for images intended to be sold on Adobe Stock. It utilizes the Gemini API to analyze image content and generate relevant information, including:

*   SEO-optimized titles
*   Detailed descriptions
*   Suggested use cases
*   Target audiences
*   Keywords
*   A concise and useful filename
*   A formatted output ready to copy and paste into your workflow

The script is designed to handle a wide variety of images and provide useful information even when the Gemini API does not provide a complete response.

## Features

*   **Automated Image Analysis:** Uses the Gemini API to analyze images.
*   **SEO-Optimized Titles:** Generates titles designed for Adobe Stock search.
*   **Persuasive Descriptions:** Creates compelling descriptions with potential use cases.
*   **Keyword Extraction:** Extracts and prioritizes relevant keywords.
*   **Suggested Use Cases & Target Audiences:** Proposes suitable use cases and target audiences.
*   **Unique and Informative Filenames:** Renames images with clear and descriptive filenames.
*   **Output Formatted for Direct Use:** Generates an output string with a clear structure for copy-pasting metadata directly.
*  **Robust Error Handling:** Includes robust error handling for API failures and ensures that some data is generated even when analysis fails.
*   **Versatile and Adaptable:** Designed to process a wide variety of images and generate appropriate metadata, from abstract to realistic scenes, using templates and default responses when no other option is available.

## How It Works

1.  **Image Analysis:** The script uploads an image to the Gemini API, which analyzes its content and returns data about the objects, scenes, styles, etc.
2.  **Metadata Generation:** Using this analysis, the script generates:
    *   A main SEO-optimized title and title variants.
    *   A detailed description designed to attract potential buyers.
    *   A list of relevant keywords.
    *   Suggested use cases.
    *   Target audiences.
    *   A new filename using a naming template.
    *   A formatted output string with a clear structure.
3.  **Image Renaming:** The script renames the image with the new filename.
4. **Output:** The script creates a detailed CSV report containing all the processed metadata and errors (if any).

## Usage

### Prerequisites
* Python 3.6 or higher
* Install required Python packages
    * `pip install google-generativeai`
* Gemini API key configured as environment variable `GOOGLE_API_KEY` or Colab Secret.

### Running the Script

1.  Clone the repository to your local machine.
2.  Set your Google Gemini API key as an environment variable (`GOOGLE_API_KEY`) or a Colab Secret.
3.  Navigate to the directory containing the script in your terminal.
4.  Run the script with the directory of your images as an argument:
    ```bash
    python script.py <directory_path>
    ```

## Input

The script accepts a single argument:
*   `<directory_path>`: The path to the directory containing the images to process.
    *   The script supports images with .jpg, .jpeg, and .png extensions.

## Output

The script outputs:

*   Renamed images with new names based on the generated metadata.
*   A CSV report (`image_processing_report_<timestamp>.csv`) containing the following columns for each image:
    *   `original_filename`: The original filename of the image.
    *   `new_filename`: The generated new filename.
    *   `main_title`: The main title for the image.
    *   `title_variants`: Alternative titles.
    *   `detailed_description`: The complete description for the image.
    *   `suggested_use_cases`: Suggested use cases for the image.
    *   `suggested_target_audience`: Target audience suggestions.
    *   `gemini_analysis`: The raw JSON output from the Gemini API.
    *   `error`: Any error that occurred during the process.
    *  `output_string`: A single string with the structured data, including the title, case of use, and keywords (ready for pasting).

## Code Structure

The code is organized into the following functions:

*   **`analyze_image_content_gemini(image_path: str) -> Dict[str, Any]`**: Analyzes image content using the Gemini API and returns the data as a dictionary.
*   **`generate_default_main_title(filename: str) -> str`**: Generates a default title.
*   **`generate_default_detailed_description(filename: str, analysis_results: Dict) -> str`**: Generates a default description.
*   **`generate_default_filename(filename: str) -> str`**: Generates a default filename.
*   **`generate_compact_title_and_use_case(analysis_results: Dict, filename: str) -> str`**: Generates a compact string with title and use case information.
*   **`generate_keywords(analysis_results: Dict, title: str, description: str) -> List[str]`**: Generates a list of keywords.
*   **`generate_main_title(analysis_results: Dict) -> str`**: Generates the main title using the data of the API.
*   **`generate_title_variants(main_title: str, analysis_results: Dict) -> List[str]`**: Generates different options for the title of the image.
*   **`generate_detailed_description(analysis_results: Dict) -> str`**: Generates the description of the image based on the data from the API.
*   **`generate_concise_description(analysis_results: Dict) -> str`**: Generates a concise description for the filename.
*   **`suggest_use_cases(analysis_results: Dict) -> List[str]`**: Suggest use cases based on the analysis.
*   **`suggest_target_audience(analysis_results: Dict) -> List[str]`**: Suggest the target audiences for the image.
*   **`generate_new_filename(original_filename: str, analysis_results: Dict) -> str`**: Generates a new filename.
*  **`generate_final_output(analysis_results: Dict, new_filename: str, original_filename: str) -> str`**: Generates a single string containing the structured metadata
*   **`process_image(image_path: str) -> Dict`**: Processes a single image file, calling all the previous functions.
*   **`main()`**: The main function that parses the command line arguments, loops through images, and generates the output.

## Customization

*   **`DEFAULT_ABBREVIATIONS`**: Dictionary of abbreviations used for generating filenames and use case/audience suggestions.
*   **`SYNONYMS`**: Dictionary of synonyms used for keyword expansion.
*   **Prompts to Gemini API:** You can further customize the prompts in `analyze_image_content_gemini` for more specific information.

## Contributing

Feel free to submit issues, feature requests or pull requests to improve this tool. This is a project under development and there are always opportunities for expansion and improvement.

## License

This project is under the MIT License.

## Acknowledgements

Thanks to Google for providing the Gemini API :D
=======
