import os
import requests
import subprocess
import json
from datetime import datetime
import re
import time

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

# Define file extension mappings for target languages
language_extensions = {
    'kotlin': 'kt',
    'python': 'py',
    'typescript': 'ts',
}

# Source directory with .java files
source_directory = "C:/Users/EmmaR/OneDrive/Documents/commons-text-1.12.0/org/apache/commons/test"

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

        # Ensure the test_errors directory exists
        os.makedirs('test_errors', exist_ok=True)

        # Generate the log file name with a timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        error_log_filename = f'test_errors/test_errors_{timestamp}.log'

        # Log the error with timestamp
        with open(error_log_filename, 'a') as error_log:
            error_log.write(f'{datetime.now()}: Error running tests: {e}\n')
            error_log.write(f'{e.stderr}\n')
# Function to handle code migration and saving the results
def migrate_code(file_path, selected_model, extraction_functions):
    
    model_start_time = time.time()

    with open(file_path, 'r') as file:
        code_to_convert = file.read()

    prompt = (
        f"Migrate the provided {source_language} code to {target_language}, ensuring functionality and compatibility. "
        # f"Preserve all necessary imports and dependencies from {source_language}. "
        # f"Adjust for differences in syntax, such as type declarations, function definitions, and property accessors. "
        # f"Convert all immutable properties val to mutable properties var only if reassignment is needed. Otherwise, keep them as val for better immutability practices. "
        # f"Ensure proper handling of nullability, using {target_language}'s safe calls (?.) or non-null asserted calls (!!.) as appropriate. "
        # f"Replace null checks with safe call operators (?.) and use the Elvis operator (?:) for providing default values where necessary. "
        # f"Remove constructors in Kotlin objects since they are not allowed and refactor initialization logic if needed. "
        # f"Convert Java static methods to Kotlin companion objects or top-level functions as appropriate. "
        # f"Replace loops and conditional structures with idiomatic Kotlin constructs where applicable, such as using for-each loops or when expressions. "
        # f"Refactor any utility classes or methods to take advantage of Kotlin's extension functions and higher-order functions. "
        # f"Ensure proper usage of Kotlin collections and standard library functions to enhance readability and performance. "
        # f"Ensure that Java collections such as HashSet are converted to the appropriate Kotlin collections, like Set, to avoid type mismatch errors. "
        # f"Retain the original logic and structure of the code while adhering to {target_language}'s coding standards and best practices. "
        # f"Test the converted code to ensure it functions as expected and address any compatibility issues."
        # f"Remove code comments."
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
        return False

# Function to handle migration of Java files from the source directory
def migrate_files_from_directory(directory, selected_model, extraction_functions):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                if migrate_code(file_path, selected_model, extraction_functions):
                    global total_requests
                    total_requests += 1

# Main execution loop
for selected_model in models:
    # Migrate files from the source directory
    migrate_files_from_directory(source_directory, selected_model, extraction_functions)

# Calculate total time taken
end_time = time.time()
total_time = end_time - start_time
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
# run_sonar_scanner()

# Run tests after SonarQube analysis
run_tests()
