# Image Metadata Automation Script for Adobe Stock ( README AI GENERATED)

## Overview

This Python script automates the process of generating comprehensive metadata for images intended for sale on Adobe Stock. By leveraging the Google Gemini API, it analyzes image content to produce:

*   SEO-optimized titles, prioritizing clarity and searchability on Adobe Stock.
*   Detailed, persuasive descriptions highlighting image benefits and potential applications.
*   Relevant keywords, expanded with synonyms for better discoverability.
*   Suggested use cases and target audiences to aid contributors in categorization.
*   Concise and informative filenames, adhering to best practices for stock image submissions.
*   A structured CSV report containing all generated metadata.

The script is engineered to handle a diverse range of image types, providing valuable metadata even when the Gemini API's response is incomplete. Robust error handling, including API quota management with retries and pacing, ensures smooth operation and informative reporting.

## Features

*   **Intelligent Image Analysis:** Utilizes the Google Gemini API for in-depth content analysis.
*   **Prioritized SEO Titles:** Generates SEO-friendly titles, ensuring prominence in Adobe Stock searches.
*   **Compelling Descriptions:** Creates persuasive descriptions, emphasizing benefits and use cases for potential buyers.
*   **Enhanced Keyword Extraction:** Extracts, prioritizes, and expands keywords using synonyms for optimal searchability.
*  **Strategic Use Case & Audience Suggestions:** Proposes relevant use cases and target audiences to streamline categorization.
*   **Clean & Descriptive Filenames:** Renames images with concise, descriptive filenames suitable for stock platforms.
*   **Structured CSV Output:** Generates a CSV file with all generated metadata for easy import into other tools.
*   **Robust Error Handling:** Implements comprehensive error handling to gracefully manage API failures, including quota limits and service unavailability, and ensures data generation through retries with exponential backoff.
*   **API Quota Management:** Incorporates pacing and retry mechanisms with exponential backoff to manage API quota limits and avoid service interruptions.
*   **Versatile & Adaptable:** Processes a wide array of images, from abstract art to realistic photography, leveraging templates and fallbacks for consistent metadata generation.

## How It Works

1.  **Gemini API Analysis:** The script submits an image to the Gemini API for content analysis, extracting details about objects, scenes, and styles.
2.  **Metadata Synthesis:** Based on the analysis, the script intelligently generates:
    *   A primary SEO-optimized title with a short phrase from the persuasive description (if space allows).
    *   A curated list of relevant keywords, expanded with synonyms.
    *   Suggestions for appropriate use cases and target audiences.
    *   A new, descriptive filename.
3.  **Image Renaming:** The script renames the image file using the newly generated filename.
4.  **CSV Reporting:** A comprehensive CSV report is generated, logging all processed metadata and any errors encountered.

## Usage

### Prerequisites

*   Python 3.6 or higher
*   Required Python package: `google-generativeai` (install via `pip install google-generativeai`)
*   Google Gemini API key configured as an environment variable (`GOOGLE_API_KEY`) or a Colab Secret.

### Running the Script

1.  Clone this repository to your local machine.
2.  Set your Google Gemini API key as an environment variable named `GOOGLE_API_KEY` or configure it as a Colab Secret if using Google Colab.
3.  Open your terminal and navigate to the directory containing the script (`script.py`).
4.  Execute the script, providing the path to the directory of images you wish to process:

    ```bash
    python script.py <directory_path> [-c <category_number>] [-r <release_names>]
    ```

    *   `-c` or `--category` (Optional): Category number for Adobe Stock.
    *   `-r` or `--releases` (Optional): Comma-separated list of release names.

## Input

The script requires a single command-line argument:

*   `<directory_path>`: The path to the directory containing the image files.

    *   Supported image formats: `.jpg`, `.jpeg`, and `.png`.

## Output

The script performs the following actions:

*   Renames the processed image files based on the generated metadata.
*   Creates a CSV report named `XXXXXXX_<timestamp>.csv` in the script's directory (replace "XXXXXXX" with your name). This report contains the following columns for each image:
    *   `Filename`: The original name of the image file.
    *   `Title`: The primary SEO-optimized title (with an added short phrase from the persuasive description if space allows).
    *   `Keywords`: A comma-separated list of relevant keywords.
    *   `Category`: The category number provided as an argument (if any).
    *   `Releases`: The comma-separated list of release names provided as an argument (if any).

## Code Structure

The script is organized into modular functions for clarity and maintainability:

*   **`analyze_image_content_gemini(image_path: str, max_retries: int = MAX_RETRIES, initial_delay: int = INITIAL_DELAY) -> Dict[str, Any]`**: Sends the image to the Gemini API for analysis and returns the API's response as a dictionary. Implements retry logic with exponential backoff and pacing to manage API quotas.
*   **`generate_default_main_title(filename: str) -> str`**: Creates a basic default title if API analysis fails.
*   **`generate_default_detailed_description(filename: str, analysis_results: Dict) -> str`**: Generates a fallback description when detailed analysis isn't available.
*   **`generate_default_filename(filename: str) -> str`**: Creates a default filename in case analysis fails.
*   **`generate_compact_title_and_use_case(analysis_results: Dict, filename: str) -> str`**: Creates a concise string combining the title and a potential use case (not directly used in final output).
*   **`generate_keywords(analysis_results: Dict, title: str, description: str) -> List[str]`**: Generates a list of relevant keywords, including synonyms.
*  **`generate_main_title(analysis_results: Dict) -> str`**: Generates the primary SEO-optimized title, prioritizing Gemini's suggestions (not directly used in final output).
*  **`generate_title_variants(main_title: str, analysis_results: Dict) -> List[str]`**: Creates alternative title suggestions (not directly used in final output).
*   **`generate_detailed_description(analysis_results: Dict) -> str`**: Generates a detailed, persuasive description (not directly used in final output).
*   **`generate_concise_description(analysis_results: Dict) -> str`**: Generates a short description for use in the filename.
*   **`suggest_use_cases(analysis_results: Dict, title: str, description: str) -> List[str]`**: Suggests potential use cases for the image.
*   **`suggest_target_audience(analysis_results: Dict, title: str, description: str) -> List[str]`**: Suggests target audiences for the image.
*   **`generate_new_filename(original_filename: str, analysis_results: Dict) -> str`**: Creates a new, informative filename.
*   **`generate_final_output(analysis_results: Dict, original_filename: str, category: str = "", releases: str = "") -> Dict`**: Creates a dictionary for each image suitable for the CSV report.
*  **`process_image(image_path: str, category: str = "", releases: str = "") -> Dict`**: Orchestrates the metadata generation process for a single image, including error handling.
*   **`main()`**: The main entry point of the script, handling command-line arguments and processing images in the specified directory.

## Customization

*   **`DEFAULT_ABBREVIATIONS`**: A dictionary used to create concise abbreviations for filenames and use case/audience suggestions. Modify this to suit your preferred abbreviations.
*   **`SYNONYMS`**: A dictionary for expanding keywords with synonyms, improving search discoverability. Add or modify synonyms as needed.
*   **Gemini API Prompts:** The prompt sent to the Gemini API in the `analyze_image_content_gemini` function can be customized to request more specific information or tailor the analysis to your needs.
*  **`MAX_RETRIES`, `INITIAL_DELAY`, `DELAY_BETWEEN_REQUESTS`**: Constants that control how the script handles API quota limits. Adjust the values to fine-tune the script's behavior.

## Contributing

Contributions to improve this tool are welcome! Please feel free to submit issues, suggest new features, or create pull requests. This is an ongoing project, and your input is valuable.

## License

This project is licensed under the MIT License.

## Acknowledgements

Thanks to Google for providing the Gemini API, which powers the intelligent analysis features of this script!