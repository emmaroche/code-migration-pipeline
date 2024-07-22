import os
from dotenv import load_dotenv
import requests
import subprocess
import json
from datetime import datetime
import re
import time

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
api_endpoint = os.getenv('API_ENDPOINT')
sonar_token = os.getenv('SONAR_TOKEN')
openai_api_key = os.getenv('OPENAI_API_KEY')
source_language = os.getenv('SOURCE_LANGUAGE')
target_language = os.getenv('TARGET_LANGUAGE')
sonar_project_key = os.getenv('SONAR_PROJECT_KEY')
sonar_host_url = os.getenv('SONAR_HOST_URL') 

# Define file extension mappings for target languages
language_extensions = {
    'kotlin': 'kt',
    'python': 'py',
    'swift': 'swift',
    'typescript': 'ts',
}

# List of file paths to migrate from the repository
repositories = [
    {
        "repo": "emmaroche/data-preparation",
        "file_paths": [
            # "code-artefacts/java/ShopV6.0/src/controllers/Store.java",
            # "code-artefacts/java/ShopV6.0/src/utils/Utilities.java",
            # "code-artefacts/java/ShopV6.0/src/utils/ScannerInput.java",
            # "code-artefacts/java/ShopV6.0/src/models/Product.java",
            "code-artefacts/java/ShopV6.0/src/main/Driver.java"
        ]
    },
]

# List of models to run sequentially
models = [
    # 'VertexAI - PaLM 2',
    'VertexAI - Gemini Pro',
    # 'VertexAI - Codey',
    # 'OpenAI - GPT-3.5 Turbo',
    # 'OpenAI - GPT-4o',
    # 'OpenAI - GPT-4 Turbo',
    # 'Ollama - Llama 3',
    # 'Ollama - Llama 2',
    # 'Ollama - CodeGemma',
    # 'Ollama - CodeLlama'
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

# Function to extract code and extra content based on regex
def extract_code_and_extra_content(response_json):
    migrated_code = response_json.get('migrated_code', '')
    extra_content = response_json.get('extra_content', '')

    # Match code block in Markdown format with closing triple backticks for target_language
    code_block_match = re.search(rf'```{target_language}\n([\s\S]*?)\n```', migrated_code, re.IGNORECASE)
    if code_block_match:
        migrated_code = code_block_match.group(1).strip()
    else:
        # Match code block starting with ''' followed by target_language (no closing backticks)
        code_block_match = re.search(rf"'''{target_language}\n([\s\S]*)", migrated_code, re.IGNORECASE)
        if code_block_match:
            migrated_code = code_block_match.group(1).strip()

    return migrated_code, extra_content

# Function to extract code and extra content based on indentation
def extract_code_and_extra_content_indentation(response_json):
    # Initialise variables
    migrated_code = ''
    extra_content = ''

    # Check if 'migrated_code' exists in response_json
    if 'migrated_code' in response_json:
        # Get the migrated code section
        migrated_code_block = response_json['migrated_code'].strip()

        # Extract code from the target_language block
        code_match = re.search(rf'```{target_language}\n(.+?)\n```', migrated_code_block, re.DOTALL | re.IGNORECASE)
        if code_match:
            migrated_code = code_match.group(1).strip()

    return migrated_code, extra_content

# Function to extract code and extra content using both regex and indentation
def extract_code_combined(response_json):
    # Extract using regex-based method
    migrated_code_regex, extra_content_regex = extract_code_and_extra_content(response_json)

    # Only use indentation-based method if regex-based method did not find valid content
    if not migrated_code_regex:
        migrated_code_indentation, extra_content_indentation = extract_code_and_extra_content_indentation(response_json)
        migrated_code_combined = migrated_code_indentation
        extra_content_combined = extra_content_indentation
    else:
        migrated_code_combined = migrated_code_regex
        extra_content_combined = extra_content_regex

    return migrated_code_combined, extra_content_combined

# Map models to their respective extraction functions
extraction_functions = {
    'VertexAI - PaLM 2': extract_code_combined,
    'VertexAI - Gemini Pro': extract_code_combined,  
    'VertexAI - Codey': extract_code_combined, 
    'OpenAI - GPT-3.5 Turbo': extract_code_combined, 
    'OpenAI - GPT-4o': extract_code_combined, 
    'OpenAI - GPT-4 Turbo': extract_code_combined,  
    'Ollama - Llama 2': extract_code_combined, 
    'Ollama - Llama 3': extract_code_combined,  
    'Ollama - CodeGemma': extract_code_combined, 
    'Ollama - CodeLlama': extract_code_combined
}

# Timer variables
start_time = time.time()
total_requests = 0
model_times = {}

# Function to run SonarQube Scanner
def run_sonar_scanner():
    # Construct the SonarQube Scanner command
    sonar_scanner_command = (
        f'sonar-scanner '
        f'-D"sonar.projectKey={sonar_project_key}" '
        f'-D"sonar.sources=output" '
        f'-D"sonar.host.url={sonar_host_url}" '
        f'-D"sonar.token={sonar_token}" '
        f'-D"sonar.exclusions=**/*.java" '
    )

    print('\nRunning SonarQube Scanner...\n')

    try:
        # Run SonarQube Scanner command
        result = subprocess.run(sonar_scanner_command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('SonarQube analysis completed successfully.')
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f'Error running SonarQube Scanner: {e}')
        print(e.stderr)

# Function to run Gradle tests
def run_tests():
    # Use the absolute path to gradlew.bat
    gradle_script = 'C:/Users/EmmaR/OneDrive/Documents/Pipeline/langchain/gradlew.bat'
    gradle_command = f'{gradle_script} test'

    print('\nRunning tests...\n')

    try:
        # Run Gradle command
        result = subprocess.run(gradle_command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('Tests completed successfully.')
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f'Error running tests: {e}')
        print(e.stderr)

# Function to handle code migration and saving the results
def migrate_code(github_repo, github_file_path, selected_model, extraction_functions):
    
    model_start_time = time.time()

    # Construct the raw URL to access the file from GitHub
    raw_url = f'https://raw.githubusercontent.com/{github_repo}/master/{github_file_path}'

    # Download the file content from GitHub
    response = requests.get(raw_url)
    if response.status_code == 200:
        code_to_convert = response.text
    else:
        raise Exception(f'Failed to download the file from GitHub ({github_repo}/{github_file_path}). Status code: {response.status_code}')

    # Define the prompt and selected model name
    prompt = (
        f"Migrate the provided {source_language} code to {target_language} code."
        "Ensure the functionality and compatibility are preserved."
        "Keep the imports in the file path when migrating the code."
    )

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
        print(f'Model Used for {github_repo}/{github_file_path}: ', selected_model)
        # Extract the response JSON
        response_json = response.json()

        # Get the extraction function based on the selected model
        extraction_function = extraction_functions.get(selected_model)
        if extraction_function is None:
            raise ValueError(f'No extraction function found for model: {selected_model}')

        # Extract the migrated code and extra content from the JSON using the specified function
        migrated_code, extra_content = extraction_function(response_json)

        # Update the response JSON
        response_json['migrated_code'] = migrated_code
        response_json['extra_content'] = extra_content

        # Log the migrated code for debugging purposes
        print(f'Migrated code for {github_repo}/{github_file_path}:\n{migrated_code}')

        # Determine the output folder based on the file path
        folder_name = get_folder_name(github_file_path)
        if folder_name:
            output_folder = os.path.join('output', 'src', folder_name)
        else:
            output_folder = os.path.join('output', 'src')

        os.makedirs(output_folder, exist_ok=True)

        # Determine the original file name and target language extension
        original_file_name = os.path.basename(github_file_path)
        file_name_without_extension, _ = os.path.splitext(original_file_name)
        target_language_extension = language_extensions.get(target_language, 'txt')

        # Generate output file path using the original file name and target language extension
        output_file_path = os.path.join(output_folder, f'{file_name_without_extension}.{target_language_extension}')

        # Save the migrated code to the unique file
        if migrated_code:
            with open(output_file_path, 'w') as file:
                file.write(migrated_code)
            print(f'Migrated code for {github_repo}/{github_file_path} has been saved to {output_file_path}')
        else:
            print(f'No valid migrated code for {github_repo}/{github_file_path} using model {selected_model}')

        # Save the entire response JSON to a new JSON file
        json_folder = os.path.join('output', 'json', 'src')
        os.makedirs(json_folder, exist_ok=True)
        json_file_path = os.path.join(json_folder, f'response_{file_name_without_extension}.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(response_json, json_file, indent=4)

        print(f'Response JSON for {github_repo}/{github_file_path} has been saved to {json_file_path}')

        # Stop timer for the model
        model_end_time = time.time()
        model_time = model_end_time - model_start_time
        model_times[selected_model] = model_times.get(selected_model, 0) + model_time

        return True
    else:
        print(f'Error for {github_repo}/{github_file_path} using model {selected_model}: {response.text}')
        return False

# Iterate over each model first, then each repository and file path
for selected_model in models:
    for repo_info in repositories:
        github_repo = repo_info['repo']
        for github_file_path in repo_info['file_paths']:
            extraction_function = extraction_functions.get(selected_model)
            if extraction_function is None:
                raise ValueError(f'No extraction function found for model: {selected_model}')
            
            if migrate_code(github_repo, github_file_path, selected_model, extraction_functions):
                total_requests += 1

# Calculate total time taken
end_time = time.time()
total_time = end_time - start_time

# Calculate total time taken in minutes
total_time_minutes = total_time / 60.0

# Print model times
print("\nModel execution times:")
for model, time_taken in model_times.items():
    time_taken_minutes = time_taken / 60.0
    print(f"{model}: {time_taken_minutes:.2f} minutes")

# Print summary
print(f'\nAll requests completed in {total_time_minutes:.2f} minutes.')
print(f'Total number of requests processed: {total_requests}')

# Run SonarQube Scanner after all migrations are done
run_sonar_scanner()

# Run tests after SonarQube analysis
run_tests()
