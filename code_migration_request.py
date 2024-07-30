import os
import requests
import subprocess
import json
from datetime import datetime
import re
import time
import glob

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Retrieve environment variables
api_endpoint = os.getenv('API_ENDPOINT')
sonar_token = os.getenv('SONAR_TOKEN')
openai_api_key = os.getenv('OPENAI_API_KEY')
source_language = os.getenv('SOURCE_LANGUAGE')
target_language = os.getenv('TARGET_LANGUAGE')
sonar_project_key = os.getenv('SONAR_PROJECT_KEY')
sonar_host_url = os.getenv('SONAR_HOST_URL')

# File extension mappings for target languages
language_extensions = {
    'kotlin': 'kt',
    'python': 'py',
    'typescript': 'ts',
}

# Source directory with files to be migrated
source_directory = "C:/Users/EmmaR/OneDrive/Documents/commons-text-1.12.0/org/apache/commons/test"

# List of models to use for code migration
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

# Maximum retries for migration and testing processes
MAX_RETRIES = 3

# Function to extract migrated code and extra content based on regex patterns
def extract_code_and_extra_content(response_json):
    migrated_code = response_json.get('migrated_code', '')
    extra_content = response_json.get('extra_content', '')

    # Extract code block using Markdown-style code fences
    code_block_match = re.search(rf'```{target_language}\n([\s\S]*?)\n```', migrated_code, re.IGNORECASE)
    if code_block_match:
        migrated_code = code_block_match.group(1).strip()
    else:
        # Fallback to extracting code block with single quotes
        code_block_match = re.search(rf"'''{target_language}\n([\s\S]*)", migrated_code, re.IGNORECASE)
        if code_block_match:
            migrated_code = code_block_match.group(1).strip()

    return migrated_code, extra_content

# Function to extract code with indentation-based approach
def extract_code_and_extra_content_indentation(response_json):
    migrated_code = ''
    extra_content = ''

    if 'migrated_code' in response_json:
        migrated_code_block = response_json['migrated_code'].strip()
        code_match = re.search(rf'```{target_language}\n(.+?)\n```', migrated_code_block, re.DOTALL | re.IGNORECASE)
        if code_match:
            migrated_code = code_match.group(1).strip()

    return migrated_code, extra_content

# Combine extraction results from different methods
def extract_code_combined(response_json):
    migrated_code_regex, extra_content_regex = extract_code_and_extra_content(response_json)

    if not migrated_code_regex:
        migrated_code_indentation, extra_content_indentation = extract_code_and_extra_content_indentation(response_json)
        migrated_code_combined = migrated_code_indentation
        extra_content_combined = extra_content_indentation
    else:
        migrated_code_combined = migrated_code_regex
        extra_content_combined = extra_content_regex

    return migrated_code_combined, extra_content_combined

# Map models to the extraction functions
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

# Timer variables for tracking model execution time
start_time = time.time()
total_requests = 0
model_times = {}

# Function to run SonarQube Scanner for code quality analysis
def run_sonar_scanner():
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
        result = subprocess.run(sonar_scanner_command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('SonarQube analysis completed successfully.')
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f'Error running SonarQube Scanner: {e}')
        print(e.stderr)

# Function to run tests (based on file extension) after code migration takes place
def run_tests(file_extension):
    if file_extension == 'kt':
        gradle_script = 'C:/Users/EmmaR/OneDrive/Documents/Pipeline/langchain/gradlew.bat'
        gradle_command = f'{gradle_script} test'
        print('\nRunning Gradle tests...\n')
    elif file_extension == 'ts':
        # Build TypeScript files before running tests
        npm_build_command = 'npm run build'
        npm_test_command = 'npm run test'
        print('\nBuilding TypeScript files...\n')
        try:
            build_result = subprocess.run(npm_build_command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Build completed successfully.')
            print(build_result.stdout)
            print('\nRunning npm tests...\n')
            test_result = subprocess.run(npm_test_command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Tests completed successfully.')
            if test_result.stderr:
                print('Test Results:\n', test_result.stderr) 
            return True
        except subprocess.CalledProcessError as e:
            print(f'Error running build or tests: {e}')
            print(e.stderr)
            log_test_error(e)
            return False

# Function to log errors that occur in migration files when attempting to run tests
def log_test_error(e):
    os.makedirs('test_errors', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    error_log_filename = f'test_errors/test_errors_{timestamp}.log'

    with open(error_log_filename, 'a') as error_log:
        error_log.write(f'{datetime.now()}: Error running tests: {e}\n')
        error_log.write(f'{e.stderr}\n')

# Function to get detailed error information from log files
def get_detailed_error_info():
    log_files = glob.glob('test_errors/test_errors_*.log')
    
    if not log_files:
        return "No error logs found."
    
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    latest_log_file = log_files[0]
    
    with open(latest_log_file, 'r') as log_file:
        log_contents = log_file.read()
    
    # Example of extracting error details
    error_details = re.findall(r'(?<=ERROR: ).*', log_contents)
    if not error_details:
        return "No specific error details found."

    # Create a summary of errors
    error_summary = "\n".join(error_details)
    error_info = f"Here are the errors encountered during previous migration attempts:\n{error_summary}"
    
    return error_info

# Function to handle the code migration process
def migrate_code(file_path, selected_model, extraction_functions, retry_attempt=0, error_info=""):
    model_start_time = time.time()

    with open(file_path, 'r') as file:
        code_to_convert = file.read()

    # Prompt for model that includes error information for the model if multiple attempts are needed
    prompt = (
        f"Migrate the provided {source_language} code to {target_language}. "
        f"Preserve all necessary imports and dependencies from {source_language}. "
        f"Adjust for differences in syntax and ensure proper handling of nullability. "
        f"Address any compatibility issues that may arise. "
        f"Here are the errors encountered during previous migration attempts:\n"
        f"{error_info}\n"
        f"Please focus on these specific issues and make necessary corrections."
    )

    payload = {
        'model': selected_model,
        'prompt': prompt,
        'code': code_to_convert
    }

    response = requests.post(api_endpoint, json=payload)

    if response.status_code == 200:
        print(f'Model Used for {file_path}: ', selected_model)
        response_json = response.json()

        extraction_function = extraction_functions.get(selected_model)
        if extraction_function is None:
            raise ValueError(f'No extraction function found for model: {selected_model}')

        migrated_code, extra_content = extraction_function(response_json)
        response_json['migrated_code'] = migrated_code
        response_json['extra_content'] = extra_content

        print(f'Migrated code for {file_path}:\n{migrated_code}')

        output_folder = os.path.join('output', 'src')
        os.makedirs(output_folder, exist_ok=True)

        original_file_name = os.path.basename(file_path)
        file_name_without_extension, _ = os.path.splitext(original_file_name)
        target_language_extension = language_extensions.get(target_language, 'txt')
        output_file_path = os.path.join(output_folder, f'{file_name_without_extension}.{target_language_extension}')

        if migrated_code:
            with open(output_file_path, 'w') as file:
                file.write(migrated_code)
            print(f'Migrated code for {file_path} has been saved to {output_file_path}')
        else:
            print(f'No valid migrated code for {file_path}')

        json_folder = os.path.join('output', 'json', 'src')
        os.makedirs(json_folder, exist_ok=True)
        json_file_path = os.path.join(json_folder, f'response_{file_name_without_extension}.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(response_json, json_file, indent=4)

        print(f'Response JSON for {file_path} has been saved to {json_file_path}')

        model_end_time = time.time()
        model_execution_time = model_end_time - model_start_time
        model_times[selected_model] = model_times.get(selected_model, 0) + model_execution_time

        return True
    else:
        print(f'Error for {file_path} using model {selected_model}: {response.text}')
        if retry_attempt < MAX_RETRIES:
            print(f"Retrying migration for {file_path} (Attempt {retry_attempt + 1})...")
            return migrate_code(file_path, selected_model, extraction_functions, retry_attempt + 1, error_info)
        return False

# Function to retry migration and testing processes if there are errors
def retry_migration_and_tests(file_path, selected_model, extraction_functions):
    retry_attempt = 0
    while retry_attempt < MAX_RETRIES:
        print(f"Attempt {retry_attempt + 1} for {file_path}")

        # Migrate code with the model
        if migrate_code(file_path, selected_model, extraction_functions, retry_attempt):
            global total_requests
            total_requests += 1

            # Re-run tests after migration
            file_extension = language_extensions.get(target_language)
            if run_tests(file_extension):
                print(f"Tests passed for {file_path} on attempt {retry_attempt + 1}")
                return True
            else:
                # Capture and retry with new error details
                error_info = get_detailed_error_info()
                print(f"Tests failed. Error info: {error_info}")
                print(f"Retrying migration with updated error info (Attempt {retry_attempt + 1})...")
                retry_attempt += 1
        else:
            print(f"Migration failed for {file_path}. Skipping tests...")
            break

    return False

# Function to migrate all .java and .js files from a directory
def migrate_files_from_directory(directory, selected_model, extraction_functions):
    print(f"Scanning directory: {directory}")  
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java') or file.endswith('.js'):
                file_path = os.path.join(root, file)
                print(f"Found file: {file_path}") 
                retry_migration_and_tests(file_path, selected_model, extraction_functions)

# Main function to run the migration process
def main():
    global total_requests, model_times
    total_requests = 0
    model_times = {}

    start_time = time.time()

    for selected_model in models:
        print(f"Running model: {selected_model}")
        migrate_files_from_directory(source_directory, selected_model, extraction_functions)

    end_time = time.time()
    total_time = end_time - start_time
    total_time_minutes = total_time / 60.0

    print("\nModel execution times:")
    for model, execution_time in model_times.items():
        print(f"{model}: {execution_time / 60:.2f} minutes")

    print(f"Total number of requests processed: {total_requests}")
    print(f"Total execution time: {total_time_minutes:.2f} minutes")

    print("\nRunning SonarQube analysis...\n")
    # run_sonar_scanner()

if __name__ == "__main__":
    main()
