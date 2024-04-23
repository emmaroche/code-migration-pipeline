import requests

# API endpoint 
api_endpoint = 'http://127.0.0.1:5000/code-migration'

# Define the prompt and selected model name
prompt = "Can you help me migrate this Javascript code to Python?"
selected_model = "ollama_llama3" 

# Path to the file containing the code to convert
file_path = r"C:\Users\EmmaR\Downloads\johnrellis-users-api-master\routes\v1\transformIdOutgoing.js" 

# Read the code from the file
with open(file_path, 'r') as file:
    code_to_convert = file.read()

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
