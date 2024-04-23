# Code Migration Pipeline

This repository contains the code for my dissertation's code migration pipeline. The pipeline facilitates the migration of code using large language models provided by OpenAI and VertexAI.

## Current Features

- **Code Migration**: Facilitates migration of code between different programming languages (e.g. Java to Kotlin, Javascript to Python, etc)

- **OpenAI Model Integration**: Incorporates AI models developed by OpenAI and VertexAI (i.e., GPT-3.5 Turbo, Gemini, PaLM2, and Codey)

- **API Endpoint**: Facilitates access to the code migration functionality through a model-agnosti API (code_migration_api.py). Running the code_migration_request.py file, which contains the code to be migrated along with the desired model and migration prompt, sends a POST request to the API.

## Contributors

- [Emma Roche](https://github.com/emmaroche) - Main Developer