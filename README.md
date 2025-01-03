# Image Metadata Automation Script for Adobe Stock

## Overview

This Python script automates the process of generating comprehensive metadata for images intended for sale on Adobe Stock. By leveraging the Google Gemini API, it analyzes image content to produce:

*   SEO-optimized titles, prioritizing clarity and searchability on Adobe Stock.
*   Detailed, persuasive descriptions highlighting image benefits and potential applications.
*   Relevant keywords, expanded with synonyms for better discoverability.
*   Suggested use cases and target audiences to aid contributors in categorization.
*   Concise and informative filenames, adhering to best practices for stock image submissions.
*   A formatted output string, ready for direct copy-pasting into your Adobe Stock workflow.

The script is engineered to handle a diverse range of image types, providing valuable metadata even when the Gemini API's response is incomplete. Robust error handling ensures smooth operation and informative reporting.

## Features

*   **Intelligent Image Analysis:** Utilizes the Google Gemini API for in-depth content analysis.
*   **Prioritized SEO Titles:** Generates SEO-friendly titles, ensuring prominence in Adobe Stock searches.
*   **Compelling Descriptions:** Creates persuasive descriptions, emphasizing benefits and use cases for potential buyers.
*   **Enhanced Keyword Extraction:** Extracts, prioritizes, and expands keywords using synonyms for optimal searchability.
*   **Strategic Use Case & Audience Suggestions:** Proposes relevant use cases and target audiences to streamline categorization.
*   **Clean & Descriptive Filenames:** Renames images with concise, descriptive filenames suitable for stock platforms.
*   **Direct-Use Output Formatting:** Produces a cleanly formatted string for immediate copy-pasting of metadata.
*   **Robust Error Handling:** Implements comprehensive error handling to gracefully manage API failures and ensure data generation.
*   **Versatile & Adaptable:** Processes a wide array of images, from abstract art to realistic photography, leveraging templates and fallbacks for consistent metadata generation.

## How It Works

1. **Gemini API Analysis:** The script submits an image to the Gemini API for content analysis, extracting details about objects, scenes, and styles.
2. **Metadata Synthesis:** Based on the analysis, the script intelligently generates:
    *   A primary SEO-optimized title and alternative variants.
    *   A detailed, benefit-oriented description.
    *   A curated list of relevant keywords, expanded with synonyms.
    *   Suggestions for appropriate use cases.
    *   Recommendations for target audiences.
    *   A new, descriptive filename.
    *   A structured output string for easy metadata application.
3. **Image Renaming:** The script renames the image file using the newly generated filename.
4. **Detailed Reporting:** A comprehensive CSV report is generated, logging all processed metadata and any errors encountered.

## Usage

### Prerequisites
* Python 3.6 or higher
* Required Python package: `google-generativeai` (install via `pip install google-generativeai`)
* Google Gemini API key configured as an environment variable (`GOOGLE_API_KEY`) or a Colab Secret.

### Running the Script

1. Clone this repository to your local machine.
2. Set your Google Gemini API key as an environment variable named `GOOGLE_API_KEY` or configure it as a Colab Secret if using Google Colab.
3. Open your terminal and navigate to the directory containing the script (`script.py`).
4. Execute the script, providing the path to the directory of images you wish to process:
    ```bash
    python script.py <directory_path>
    ```

## Input

The script requires a single command-line argument:

*   `<directory_path>`: The path to the directory containing the image files.
    *   Supported image formats: `.jpg`, `.jpeg`, and `.png`.

## Output

The script performs the following actions:

*   Renames the processed image files based on the generated metadata.
*   Creates a CSV report named `image_processing_report_<timestamp>.csv` in the script's directory. This report contains the following columns for each image:
    *   `original_filename`: The original name of the image file.
    *   `new_filename`: The newly generated filename.
    *   `main_title`: The primary SEO-optimized title.
    *   `title_variants`: A comma-separated list of alternative titles.
    *   `detailed_description`: The comprehensive description of the image.
    *   `suggested_use_cases`: A comma-separated list of suggested use cases.
    *   `suggested_target_audience`: A comma-separated list of target audience suggestions.
    *   `gemini_analysis`: The raw JSON response received from the Gemini API.
    *   `error`: Details of any errors encountered during processing.
    *   `output_string`: A formatted string containing the title, use case, and keywords, ready for copy-pasting.

## Code Structure

The script is organized into modular functions for clarity and maintainability:

*   **`analyze_image_content_gemini(image_path: str) -> Dict[str, Any]`**: Sends the image to the Gemini API for analysis and returns the API's response as a dictionary.
*   **`generate_default_main_title(filename: str) -> str`**: Creates a basic default title if API analysis fails.
*   **`generate_default_detailed_description(filename: str, analysis_results: Dict) -> str`**: Generates a fallback description when detailed analysis isn't available.
*   **`generate_default_filename(filename: str) -> str`**: Creates a default filename in case analysis fails.
*   **`generate_compact_title_and_use_case(analysis_results: Dict, filename: str) -> str`**: Creates a concise string combining the title and a potential use case.
*   **`generate_keywords(analysis_results: Dict, title: str, description: str) -> List[str]`**: Generates a list of relevant keywords, including synonyms.
*   **`generate_main_title(analysis_results: Dict) -> str`**: Generates the primary SEO-optimized title, prioritizing Gemini's suggestions.
*   **`generate_title_variants(main_title: str, analysis_results: Dict) -> List[str]`**: Creates alternative title suggestions.
*   **`generate_detailed_description(analysis_results: Dict) -> str`**: Generates a detailed, persuasive description.
*   **`generate_concise_description(analysis_results: Dict) -> str`**: Generates a short description for use in the filename.
*   **`suggest_use_cases(analysis_results: Dict) -> List[str]`**: Suggests potential use cases for the image.
*   **`suggest_target_audience(analysis_results: Dict) -> List[str]`**: Suggests target audiences for the image.
*   **`generate_new_filename(original_filename: str, analysis_results: Dict) -> str`**: Creates a new, informative filename.
*   **`generate_final_output(analysis_results: Dict, new_filename: str, original_filename: str) -> str`**: Creates the formatted output string for easy metadata pasting.
*   **`process_image(image_path: str) -> Dict`**: Orchestrates the metadata generation process for a single image, including error handling.
*   **`main()`**: The main entry point of the script, handling command-line arguments and processing images in the specified directory.

## Customization

*   **`DEFAULT_ABBREVIATIONS`**:  A dictionary used to create concise abbreviations for filenames and use case/audience suggestions. Modify this to suit your preferred abbreviations.
*   **`SYNONYMS`**: A dictionary for expanding keywords with synonyms, improving search discoverability. Add or modify synonyms as needed.
*   **Gemini API Prompts:** The prompt sent to the Gemini API in the `analyze_image_content_gemini` function can be customized to request more specific information or tailor the analysis to your needs.

## Contributing

Contributions to improve this tool are welcome! Please feel free to submit issues, suggest new features, or create pull requests. This is an ongoing project, and your input is valuable.

## License

This project is licensed under the MIT License.

## Acknowledgements

Thanks to Google for providing the Gemini API, which powers the intelligent analysis features of this script!