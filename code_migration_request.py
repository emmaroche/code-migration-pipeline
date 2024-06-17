import requests

# API endpoint 
api_endpoint = 'http://127.0.0.1:5000/code-migration'

# Define the source and target languages
source_language = "Objective-C"
target_language = "Swift"

# GitHub repository and file path
github_repo = "emmaroche/data-preparation"
github_file_path = "code-artefacts/objective-c/Objective-C-Examples-master/ActionSheet/ActionSheet/ViewController.m"

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
    f"Replace language-specific syntax and constructs with equivalents in {target_language}, maintaining code integrity."
    f" Ensure compliance with {target_language}'s type system, idiomatic practices, and coding conventions for optimal performance."
    f" Ensure compatibility and equivalent functionality when migrating from any frameworks identified as being used to a similar framework in {target_language}."
    f" Refactor the code to leverage {target_language}'s features and best practices, enhancing maintainability and efficiency."
    " Provide only the migrated code without any explanations or comments."
)

selected_model = "OpenAI - GPT-4o" 

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
    # Printing the converted code
    print("Converted code:\n")
    print(response.json()['converted_code'])
else:
    print("Error:", response.text)
