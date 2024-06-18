import os
import requests
from datetime import datetime

# API endpoint 
api_endpoint = 'http://127.0.0.1:5000/code-migration'

# Define the source and target languages
source_language = "Java"
target_language = "Kotlin"  # Example: Replace with actual target language dynamically

# Define file extension mappings for target languages
language_extensions = {
    "Kotlin": "kt",
    "Python": "py",
    "Swift": "swift",
    "TypeScript": "ts",
}

# GitHub repository and file path
github_repo = "emmaroche/data-preparation"
github_file_path = "code-artefacts/java/ShopV6.0/src/controllers/Store.java"

# Construct the raw URL
raw_url = f"https://raw.githubusercontent.com/{github_repo}/master/{github_file_path}"

# Download the file content from GitHub
response = requests.get(raw_url)
if response.status_code == 200:
    code_to_convert = response.text
else:
    raise Exception(f"Failed to download the file from GitHub. Status code: {response.status_code}")

# Define the prompt and selected model name
prompt = (
    f"Migrate the provided {source_language} code to {target_language}, ensuring compatibility and functionality."
    "\n\n"
    "Preserve the functionality and structure of the code while excluding any comments."
    f"Replace language-specific syntax and constructs with equivalents in {target_language}, maintaining code integrity."
    f" Ensure compliance with {target_language}'s type system, idiomatic practices, and coding conventions for optimal performance."
    f" Ensure compatibility and equivalent functionality when migrating from any frameworks identified as being used to a similar framework in {target_language}."
    f" Refactor the code to leverage {target_language}'s features and best practices, enhancing maintainability and efficiency."
    " Provide only the migrated code without any explanations, comments, or markdown syntax."
)

selected_model = "VertexAI - Gemini Pro" 

# Request payload
payload = {
    'model': selected_model,
    'prompt': prompt,
    'code': code_to_convert
}

# POST request to the API endpoint
response = requests.post(api_endpoint, json=payload)

# Checking if the request was successful
if response.status_code == 200:
    print("Model Used: ", selected_model)
    # Extract the converted code
    converted_code = response.json().get('converted_code', '')

    # Remove any markdown code block markers for output saving purposes
    if converted_code.startswith("```") and converted_code.endswith("```"):
        converted_code = converted_code[converted_code.find("\n")+1:converted_code.rfind("\n")]

    # Print the converted code
    print("Converted code:\n")
    print(converted_code)

    # Create a folder named 'output' (if it doesn't exist) to store the converted code
    output_folder = 'output'
    os.makedirs(output_folder, exist_ok=True)

    # Determine the file extension based on the target language
    file_extension = language_extensions.get(target_language, 'txt')

    # Generate a unique filename using a timestamp and target language
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    output_file_path = os.path.join(output_folder, f"converted_code_{target_language}_{timestamp}.{file_extension}")
    
    # Save the converted code to the unique file
    with open(output_file_path, 'w') as file:
        file.write(converted_code)

    print("\n\n" f"Converted code has been saved to {output_file_path}")
else:
    print("Error:", response.text)
