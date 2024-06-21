import os
import requests
import subprocess
from datetime import datetime

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
            # "code-artefacts/java/ShopV6.0/src/controllers/Store.java",
            # "code-artefacts/java/ShopV6.0/src/utils/ScannerInput.java",
            # "code-artefacts/java/ShopV6.0/src/utils/Utilities.java",
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
            "\n\n"
            "Keep the imports in the file path when migrating the code."
            f"Replace language-specific syntax and constructs with equivalents in {target_language}, maintaining code integrity."
            f" Ensure compliance with {target_language}'s type system, idiomatic practices, and coding conventions for optimal performance."
            f" Ensure compatibility and equivalent functionality when migrating from any frameworks identified as being used to a similar framework in {target_language}."
            f" Refactor the code to leverage {target_language}'s features and best practices, enhancing maintainability and efficiency."
            " Provide only the migrated code without any explanations, comments, or markdown syntax."
        )

        selected_model = "VertexAI - Codey"

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
            # Extract the migrated code
            migrated_code = response.json().get('migrated_code', '')

            # Determine the output folder based on the file path
            folder_name = get_folder_name(github_file_path)
            if folder_name:
                output_folder = os.path.join('output', selected_model, folder_name)
            else:
                output_folder = 'output'

            os.makedirs(output_folder, exist_ok=True)

            # Generates a unique identifier for each file to avoid overwriting
            unique_identifier = datetime.now().strftime('%Y%m%d%H%M%S')

            # Determine the file extension based on the target language
            target_language_extension = language_extensions.get(target_language, 'txt')

            # Generate output file path
            output_file_path = os.path.join(output_folder, f"migrated_code_{target_language}_{unique_identifier}_{os.path.basename(github_file_path)}.{target_language_extension}")

            # Save the migrated code to the unique file
            with open(output_file_path, 'w') as file:
                file.write(migrated_code)

            print(f"Migrated code for {github_repo}/{github_file_path} has been saved to {output_file_path}")

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

        else:
            print(f"Error for {github_repo}/{github_file_path}: {response.text}")
