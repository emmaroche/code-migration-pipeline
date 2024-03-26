import requests

# API endpoint 
api_endpoint = 'http://127.0.0.1:5000/code-migration'

# Define the prompt and model name
prompt = "Can you help me migrate/convert this Javascript code to Typescript?"
model_name = "vertexai_gemini_pro" 

# Path to the file containing the code to convert
file_path = r"C:\Users\EmmaR\Downloads\johnrellis-users-api-master\routes\v1\transformIdOutgoing.js" 

# Read the code from the file
with open(file_path, 'r') as file:
    code_to_convert = file.read()

# Request payload
payload = {
    'model': model_name,
    'prompt': prompt,
    'code': code_to_convert
}

# POST request to the API endpoint
response = requests.post(api_endpoint, json=payload)

# Checking if the request was successful
if response.status_code == 200:
    print("Model Used: ", model_name)
    # Printing the converted code
    print("Converted code:\n")
    print(response.json()['converted_code'])
else:
    print("Error:", response.text)
