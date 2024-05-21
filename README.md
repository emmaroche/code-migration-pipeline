# Code Migration Pipeline

This repository contains the code for my dissertation's Code Migration Pipeline. The pipeline facilitates the migration of code using generative AI / large language models provided by OpenAI, VertexAI and Ollama.

## Current Features

- **Code Migration**: Facilitates migration of code between different programming languages (e.g. Javascript to Python, Java to Kotlin etc)

- **Model Integration**: Incorporates AI models developed by OpenAI, VertexAI, and Ollama (e.g., GPT-3.5 Turbo, Gemini Pro, Llama 3, etc.)

- **API Endpoint**: Facilitates access to the code migration functionality through a model-agnosti API (code_migration_api.py). Running the code_migration_request.py file, which contains the code to be migrated along with the desired model and migration prompt, sends a POST request to the API.

## Contributors

- [Emma Roche](https://github.com/emmaroche) - Main Developer
