import os
import requests
import subprocess
import json
from datetime import datetime
import re
import time
from dotenv import load_dotenv

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

# File extension mappings for target languages
language_extensions = {
    'kotlin': 'kt',
    'typescript': 'ts',
}

# List of source directories to migrate from
source_directories = [
    'C:/Users/EmmaR/OneDrive/Documents/Pipeline/Data'
]

# List of models to use for code migration
models = [
    'VertexAI - PaLM 2',
    # 'VertexAI - Gemini Pro',
    # 'VertexAI - Codey',
    # 'OpenAI - GPT-3.5 Turbo',
    # 'OpenAI - GPT-4o',
    # 'OpenAI - GPT-4 Turbo',
    # 'Ollama - Llama 3',
    # 'Ollama - CodeGemma',
    # 'Ollama - CodeLlama'
]

# Function to extract migrated code based on regex patterns
def extract_code(response_json):
    migrated_code = response_json.get('migrated_code', '')

    if not target_language:
        # When no target language is specified, ignore content before and after ```
        code_block_match = re.search(r'```([\s\S]*?)```', migrated_code, re.IGNORECASE)
        if code_block_match:
            migrated_code = code_block_match.group(1).strip()
        else:
            code_block_match = re.search(r'```([\s\S]*?)```', migrated_code, re.IGNORECASE)
            if code_block_match:
                migrated_code = code_block_match.group(1).strip()
    else:
        # When target language is specified, ignore content before and after ```
        code_block_match = re.search(rf'```{target_language}\n([\s\S]*?)```', migrated_code, re.IGNORECASE)
        if code_block_match:
            migrated_code = code_block_match.group(1).strip()
        else:
            code_block_match = re.search(rf'```{target_language}\n([\s\S]*?)\n```', migrated_code, re.IGNORECASE)
            if code_block_match:
                migrated_code = code_block_match.group(1).strip()

    return migrated_code

# Function to extract migrated code with indentation-based approach
def extract_code_indentation(response_json):
    migrated_code = ''

    if 'migrated_code' in response_json:
        migrated_code_block = response_json['migrated_code'].strip()
        code_match = re.search(rf'```{target_language}\n(.+?)\n```', migrated_code_block, re.DOTALL | re.IGNORECASE)
        if code_match:
            migrated_code = code_match.group(1).strip()

    return migrated_code

# Combine extraction results from different methods
def extract_code_combined(response_json):
    migrated_code_regex = extract_code(response_json)

    if not migrated_code_regex:
        migrated_code_indentation = extract_code(response_json)
        migrated_code_combined = migrated_code_indentation
    else:
        migrated_code_combined = migrated_code_regex

    return migrated_code_combined

# Map models to the extraction functions
extraction_functions = {
    'VertexAI - PaLM 2': extract_code_combined,
    'VertexAI - Gemini Pro': extract_code_combined,  
    'VertexAI - Codey': extract_code_combined, 
    'OpenAI - GPT-3.5 Turbo': extract_code_combined, 
    'OpenAI - GPT-4o': extract_code_combined, 
    'OpenAI - GPT-4 Turbo': extract_code_combined,  
    'Ollama - Llama 3': extract_code_combined,  
    'Ollama - CodeGemma': extract_code_combined, 
    'Ollama - CodeLlama': extract_code_combined
}

# Timer variables for tracking model execution time
total_requests = 0
model_times = {}

# Function to run SonarQube Scanner for code quality analysis
def run_sonar_scanner():
    sonar_scanner_command = (
        f'sonar-scanner '
        f'-D"sonar.projectKey={sonar_project_key}" '
        f'-D"sonar.sources=output/src" '
        f'-D"sonar.host.url={sonar_host_url}" '
        f'-D"sonar.token={sonar_token}" '
    )
    try:
        result = subprocess.run(sonar_scanner_command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return f'SonarQube analysis completed successfully.\n{result.stdout}'
    except subprocess.CalledProcessError as e:
        return f'Error running SonarQube Scanner:\n{e}\n{e.stderr}'

# Function to run tests (based on file extension) after code migration takes place
def run_tests(file_extension):
    # Define the log file name with timestamp
    log_filename = f'output/test_report/migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'

    try:
        if file_extension == 'kt':
            # Specify the path to the gradlew script
            gradle_script = 'C:/Users/EmmaR/OneDrive/Documents/Pipeline/langchain/gradlew.bat'
            # Command to run Gradle tests
            gradle_command = f'{gradle_script} clean test'

            # Execute the Gradle command
            result = subprocess.run(gradle_command, shell=True, check=True, text=True, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            
            # Write the test results to the log file
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                log_file.write('Gradle Test Results:\n')
                log_file.write(result.stdout)
                if result.stderr:
                    log_file.write('\nGradle Errors:\n')
                    log_file.write(result.stderr)
            
            return result.returncode == 0

        elif file_extension == 'ts':
            # Command to run TypeScript tests
            npm_test_command = 'npm test'
            
            # Execute the npm test command
            test_result = subprocess.run(npm_test_command, shell=True, text=True, 
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

            # Write the test results to the log file
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                log_file.write('\nTest Results:\n')
                log_file.write(test_result.stdout)
                if test_result.stderr:
                    log_file.write('\nTest Errors:\n')
                    log_file.write(test_result.stderr)
                if test_result.returncode == 0:
                    log_file.write('\nTests Passed Successfully.\n')
                else:
                    log_file.write('\nSome Tests Failed.\n')
            
            return test_result.returncode == 0

    except subprocess.CalledProcessError as e:
        # Handle errors from subprocess.run with more detail
        with open(log_filename, 'a', encoding='utf-8') as log_file:
            log_file.write('\nSubprocess error occurred:\n')
            log_file.write(f'Command: {e.cmd}\n')
            log_file.write(f'Exit code: {e.returncode}\n')
            log_file.write(f'Output:\n{e.output}\n')
            log_file.write(f'Error Output:\n{e.stderr}\n')

    except Exception as e:
        # Handle any other exceptions and log them
        with open(log_filename, 'a', encoding='utf-8') as log_file:
            log_file.write('\nUnexpected error occurred:\n')
            log_file.write(f'{e}\n')
            
        print(f'Unexpected error occurred. Details saved to {log_filename}')

    print(f'Log file created at: {log_filename}')
    return False
    
# Function to migrate code and handle errors
def migrate_code(file_path, selected_model, extraction_functions, log_file):
    model_start_time = time.time()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            code_to_migrate = file.read()

        # Simple prompt for Java to Kotlin and JavaScript to TypeScript
        prompt = (
            f"Migrate the provided {source_language} code to {target_language}."
        )

        # Complex prompt for Java to Kotlin

        # Class Code
        # prompt = (
        #     f"Migrate the provided {source_language} code to {target_language}. Follow these instructions for an error-free migration:\n"
        #     f"1. Remove the package import from each file for the purposes of this migration.\n"
        #     f"2. Adjust all other important imports and dependencies from {source_language} to match {target_language}'s syntax and structure.\n"
        #     f"3. Handle static methods and fields by using {target_language}'s appropriate annotations or constructs to maintain static-like behavior.\n"
        #     f"4. Adjust access modifiers and collections. Ensure that {source_language}'s access levels (`public`, `protected`, `private`) are correctly translated into {target_language}'s visibility modifiers.\n"
        #     f"5. Ensure that all mutable properties in {target_language} are declared with `var` instead of `val`.\n"
        # )

        # App Code
        # prompt = (
        #     f"Migrate ALL the provided {source_language} code to {target_language} and keep the functionality the same. Follow these instructions for an error-free migration:\n"
        #     "\n"
        #     f"1. Retain all package imports and adapt other imports from {source_language} to {target_language}'s syntax.\n"
        #     f"2. Handle static methods and fields in {target_language} using `@JvmStatic` and `companion object`.\n"
        #     f"4. Use `var` for mutable properties in {target_language}.\n"
        #     f"5. Make all properties and their setters public in {target_language}, regardless of their access level in {source_language}. Ensure that getters and setters do not cause method signature conflicts.\n"
        #     f"6. Ensure that all function calls are correctly translated from Java to {source_language}. Verify that function invocations and variable assignments are correct and that the syntax matches {source_language}’s expectations.\n"
        #     f"7. Verify that all referenced classes, methods, and variables are properly migrated and imported. Ensure that functions are invoked properly and variables are used as expected in the {source_language} code.\n"
        #     f"8. Do not manually define getters and setters. Rely on {source_language}'s autogenerated methods to avoid conflicts.\n"
        #     "\n"
        #     f"Provide clear and correctly formatted {target_language} code, avoiding unresolved references, syntax errors, and incorrect function invocations."
        # )

        # Complex prompts for JavaScript to TypeScript
        
        # Class Code
        # prompt = (
    #         f"Migrate the provided {source_language} code to {target_language}. Follow these instructions for an error-free migration:\n"
    #         f"1. If they exist, retain all important imports and dependencies from {source_language}. 
    #         f"2. Handle type declarations and generics properly. Ensure all types are correctly defined in {target_language}.\n"
    #         f"3. Adjust syntax differences between {source_language} and {target_language}. Ensure correct usage of language-specific features.\n"
    #         f"4. For TypeScript, handle type assertions, generics, and private fields accurately. Replace 'private' keyword with '#' for private fields.\n"
        # )

        # App Code
        # prompt = (
        #     f"Migrate the provided {source_language} code to {target_language}. Follow these instructions for an error-free migration:\n"
        #     f"1. If they exist, retain all important imports and dependencies from {source_language}. Ensure that all relevant import statements and require calls use the format `.../.../src/` at the start of the original paths, for example: ../schemas/user.schema.js migrates to ../../src/schemas/user.schema.ts.\n"
        #     f"2. Handle type declarations and generics properly. Ensure all types are correctly defined in {target_language}.\n"
        #     f"3. Adjust syntax differences between {source_language} and {target_language}. Ensure correct usage of language-specific features.\n"
        #     f"4. Rename 'delete' to 'deleteUser' where applicable.\n"
        #     f"5. Use `module.exports =` instead of a function name in paginationAndSort.ts.\n"
        #     f"6. Ensure that the format and naming conventions of the migrated code remain consistent with the original code.\n"
        # )

        # Log the prompt used for migration
        log_file.write(f'{datetime.now()}: Using prompt: {prompt}\n')

        payload = {
            'model': selected_model,
            'prompt': prompt,
            'code': code_to_migrate
        }

        response = requests.post(api_endpoint, json=payload)
        response.raise_for_status()

        extraction_function = extraction_functions.get(selected_model)
        if extraction_function is None:
            raise ValueError(f'No extraction function found for model: {selected_model}')

        response_json = response.json()
        migrated_code = extraction_function(response_json)
        response_json['migrated_code'] = migrated_code

        if migrated_code:
            file_name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
            target_language_extension = language_extensions.get(target_language, 'txt')

            # Get the name of the last directory name from the source path
            source_directory = os.path.dirname(file_path)
            last_directory_name = os.path.basename(source_directory)

            # Define the output path based on the last directory name
            output_directory = os.path.join('output', 'src', last_directory_name)
            os.makedirs(output_directory, exist_ok=True)
            
            output_file_path = os.path.join(output_directory, file_name_without_extension + '.' + target_language_extension)
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(migrated_code)
            
            log_file.write(f'{datetime.now()}: Migrated code for {file_path} saved to {output_file_path}.\n')

            json_directory = os.path.join('output', 'json', 'src', last_directory_name)
            os.makedirs(json_directory, exist_ok=True)
            
            json_file_path = os.path.join(json_directory, f'response_{file_name_without_extension}.json')
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(response_json, json_file, indent=4)
            
            log_file.write(f'{datetime.now()}: Response JSON for {file_path} saved to {json_file_path}.\n')

            model_execution_time = time.time() - model_start_time
            model_times[selected_model] = model_times.get(selected_model, 0) + model_execution_time
            log_file.write(f'{datetime.now()}: Model {selected_model} processed {file_path}. Time taken: {model_execution_time:.2f} seconds\n')

            return True
        else:
            log_file.write(f'{datetime.now()}: No valid migrated code for {file_path} using model {selected_model}.\n')
            return False
    except Exception as e:
        error_message = f'{datetime.now()}: Error for {file_path} using model {selected_model}: {e}'
        log_file.write(error_message + '\n')
        if hasattr(e, 'response') and e.response is not None:
            log_file.write(f'{e.response.text}\n')
        return False

# Function to migrate all .java and .js files from a directory
def migrate_files_from_directory(directory, selected_model, extraction_functions, log_file):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java') or file.endswith('.js'):
                file_path = os.path.join(root, file)
                if migrate_code(file_path, selected_model, extraction_functions, log_file):
                    global total_requests
                    total_requests += 1

# Main function to run the migration process
def main():
    global total_requests, model_times
    total_requests = 0
    model_times = {}

    start_time = time.time()

    # Log file for the entire script execution
    log_filename = f'output/migration_logs/migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'
    with open(log_filename, 'w', encoding='utf-8') as log_file:

        # Migrate all files from each source directory
        for selected_model in models:
            log_file.write(f'Running model: {selected_model}\n')
            for source_directory in source_directories:
                migrate_files_from_directory(source_directory, selected_model, extraction_functions, log_file)

        # Determine the file extension for tests
        file_extension = language_extensions.get(target_language)
        
        # Run tests after all migrations are complete
        if file_extension:
            log_file.write('\nRunning tests...\n')
            if run_tests(file_extension):
                log_file.write('All tests passed successfully.\n')
            else:
                log_file.write('Some tests failed. Check the test results for details.\n')
        
        # Run SonarQube analysis
        log_file.write('\nRunning SonarQube analysis...\n')
        sonar_result = run_sonar_scanner()
        log_file.write(sonar_result + '\n')

        end_time = time.time()
        total_time_minutes = (end_time - start_time) / 60.0

        log_file.write('\nModel execution times:\n')
        for model, execution_time in model_times.items():
            if execution_time < 60:
                log_file.write(f'{model}: {execution_time:.2f} seconds\n')
            else:
                log_file.write(f'{model}: {execution_time / 60:.2f} minutes\n')

        log_file.write(f'Total number of requests processed: {total_requests}\n')
        log_file.write(f'Total execution time: {total_time_minutes:.2f} minutes\n')

if __name__ == "__main__":
    main()
