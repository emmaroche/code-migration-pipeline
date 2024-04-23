from flask import Flask, request, jsonify
from langchain_core.prompts import PromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_google_vertexai import VertexAI
from langchain_community.llms import Ollama

app = Flask(__name__)

# AI Models
MODELS = {
    "openai": ChatOpenAI(),
    "vertexai_text_bison": VertexAI(model_name="text-bison"),
    "vertexai_gemini_pro": VertexAI(model_name="gemini-pro"),
    "vertexai_code_bison": VertexAI(model_name="code-bison"),
    "ollama_llama3": Ollama(model="llama3"),
    "ollama_llama2": Ollama(model="llama2"),
    "ollama_codellama": Ollama(model="codellama"),
    "ollama_codegemma": Ollama(model="codegemma")
}

@app.route('/code-migration', methods=['POST'])
def code_migration():
    # Parse request data
    request_data = request.json
    selected_model = request_data.get('model')
    prompt_data = request_data.get('prompt')
    code_to_convert = request_data.get('code')

    # Initialise the model based on the selected model name above
    model = MODELS.get(selected_model)
    if model is None:
        return jsonify({"error": "Invalid model name"}), 400

    # Template for the prompt
    template = """Question: {question}\n\nAnswer: {answer}"""
    prompt = PromptTemplate.from_template(template)

    # Create a chain with the prompt and model
    chain = prompt | model

    # Invoke the chain to convert the code 
    converted_code = chain.invoke({"question": prompt_data, "answer": code_to_convert})

    # Extracting content based on the type of the converted_code object
    if isinstance(converted_code, str):  # If converted_code is a string
        converted_content = converted_code.strip()
    elif hasattr(converted_code, 'content'):  # If converted_code has 'content' attribute
        converted_content = converted_code.content.strip()
    else:
        return jsonify({"error": "Unable to extract converted code"}), 500

    # Construct response
    response = {
        "original_code": code_to_convert.strip(),
        "converted_code": converted_content,
        "model_used": selected_model  
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
