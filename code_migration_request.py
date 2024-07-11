import os
import requests
import subprocess
import json
from datetime import datetime
import re
import time

# API endpoint 
api_endpoint = 'http://127.0.0.1:5000/code-migration'

# Define the source and target languages
source_language = "Java"
target_language = "Kotlin" 

# Define file extension mappings for target languages
language_extensions = {
    "Kotlin": "kt",
    "Python": "py",
    "Swift": "swift",
    "TypeScript": "ts",
}

# List of file paths to migrate from the repository
repositories = [
    {
        "repo": "emmaroche/data-preparation",
        "file_paths": [
            "code-artefacts/java/ShopV6.0/src/controllers/Store.java",
            "code-artefacts/java/ShopV6.0/src/utils/Utilities.java",
            "code-artefacts/java/ShopV6.0/src/utils/ScannerInput.java",
            "code-artefacts/java/ShopV6.0/src/models/Product.java" 
        ]
    },
]

# Function to extract folder name from file path and create new folder if needed
def get_folder_name(file_path):
    # Split the file path by '/' to extract the folder name
    parts = file_path.split('/')
    # Get the second last part of the path (before the file with the content to migrate)
    if len(parts) >= 2:
        folder_name = parts[-2]
        # Create a new folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        return folder_name
    else:
        return ''

# Function to extract code and extra content
def extract_code_and_extra_content(migrated_code):
    code_lines = []
    extra_content = ''

    in_code_block = False

    for line in migrated_code.split('\n'):
        if re.match(r'```', line):
            in_code_block = not in_code_block
        elif in_code_block:
            code_lines.append(line)
        else:
            extra_content += line + '\n'

    return '\n'.join(code_lines), extra_content.strip()

# Timer variables
start_time = time.time()
total_requests = 0

# Iterate over each repository and file path
for repo_info in repositories:
    github_repo = repo_info["repo"]
    for github_file_path in repo_info["file_paths"]:
        # Construct the raw URL
        raw_url = f"https://raw.githubusercontent.com/{github_repo}/master/{github_file_path}"

        # Download the file content from GitHub
        response = requests.get(raw_url)
        if response.status_code == 200:
            code_to_convert = response.text
        else:
            raise Exception(f"Failed to download the file from GitHub ({github_repo}/{github_file_path}). Status code: {response.status_code}")

        # Define the prompt and selected model name
        prompt = (
            f"Migrate the provided {source_language} code to {target_language}, ensuring compatibility and functionality."
            # "Keep the imports in the file path when migrating the code."
            # f"Replace language-specific syntax and constructs with equivalents in {target_language}, maintaining code integrity."
            # f" Ensure compliance with {target_language}'s type system, idiomatic practices, and coding conventions for optimal performance."
            # f" Ensure compatibility and equivalent functionality when migrating from any frameworks identified as being used to a similar framework in {target_language}."
            # f" Refactor the code to leverage {target_language}'s features and best practices, enhancing maintainability and efficiency."
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
            print(f"Model Used for {github_repo}/{github_file_path}: ", selected_model)
            # Extract the response JSON
            response_json = response.json()

            # Extract the migrated code from the JSON
            migrated_code = response_json.get('migrated_code', '').strip()

            # Separate code and extra content
            migrated_code, extra_content = extract_code_and_extra_content(migrated_code)

            # Add extra content to the JSON
            response_json['extra_content'] = extra_content

            # Determine the output folder based on the file path
            folder_name = get_folder_name(github_file_path)
            if folder_name:
                output_folder = os.path.join('output', selected_model.split(' - ')[-1], folder_name)
            else:
                output_folder = os.path.join('output', selected_model.split(' - ')[-1])

            os.makedirs(output_folder, exist_ok=True)

            # Generate a unique identifier for each file to avoid overwriting
            unique_identifier = datetime.now().strftime('%Y%m%d%H%M%S%f')

            # Determine the file extension based on the target language
            target_language_extension = language_extensions.get(target_language, 'txt')

            # Generate output file path
            output_file_path = os.path.join(output_folder, f"migrated_code_{target_language}_{unique_identifier}_{os.path.basename(github_file_path)}.{target_language_extension}")

            # Save the migrated code to the unique file
            with open(output_file_path, 'w') as file:
                file.write(migrated_code)

            print(f"Migrated code for {github_repo}/{github_file_path} has been saved to {output_file_path}")

            # Save the entire response JSON to a new JSON file
            json_folder = os.path.join('output', 'json', selected_model.split(' - ')[-1])
            os.makedirs(json_folder, exist_ok=True)
            json_file_path = os.path.join(json_folder, f"response_{os.path.basename(github_file_path)}_{unique_identifier}.json")
            with open(json_file_path, 'w') as json_file:
                json.dump(response_json, json_file, indent=4)

            print(f"Response JSON for {github_repo}/{github_file_path} has been saved to {json_file_path}")

            # SonarQube project key 
            sonar_project_key = "Dissertation"

            # Run SonarScanner to analyse the migrated code
            sonar_scanner_command = (
                "sonar-scanner.bat "
                f"-D\"sonar.projectKey={sonar_project_key}\" "
                "-D\"sonar.sources=output\" "  
                "-D\"sonar.host.url=http://localhost:9000\" "
                "-D\"sonar.token=sqp_597c320197ea7108a85634755a2b3f8393afdb8e\""
            )

            print("\nRunning SonarScanner...\n")
            subprocess.run(sonar_scanner_command, shell=True, check=True)

            total_requests += 1

        else:
            print(f"Error for {github_repo}/{github_file_path}: {response.text}")

# Calculate total time taken
end_time = time.time()
total_time = end_time - start_time

# Print summary
print(f"\nAll requests completed in {total_time:.2f} seconds.")
print(f"Total number of requests processed: {total_requests}")
