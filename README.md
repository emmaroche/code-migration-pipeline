# Code Migration Pipeline

This repository contains the code for my dissertation's Code Migration Pipeline. The pipeline facilitates the migration of code using generative AI.

## Current Features

- **Code Migration**: Facilitates migration of Java to Kotlin and Javascript to TypeScript.

- **Model Integration**: Incorporates AI models developed by OpenAI, Google, and Meta (e.g., GPT-3.5 Turbo, Gemini Pro, Llama 3, etc.)

- **API Endpoint**: The code_migration_api.py file sets up a Flask-based API for code migration tasks. Running the code_migration_request.py script sends a POST request to this Flask endpoint, including the code to be migrated, the selected AI model, and the migration prompt. 

## Contributors

- [Emma Roche](https://github.com/emmaroche) - Developer
