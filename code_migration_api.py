from flask import Flask, request, jsonify
from langchain_core.prompts import PromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_google_vertexai import VertexAI

app = Flask(__name__)

# AI Models
MODELS = {
    "openai": ChatOpenAI(),
    "vertexai_text_bison": VertexAI(model_name="text-bison"),
    "vertexai_gemini_pro": VertexAI(model_name="gemini-pro"),
    "vertexai_code_bison": VertexAI(model_name="code-bison"),
}

@app.route('/code-migration', methods=['POST'])
def code_migration():
    # Parse request data
    request_data = request.json
    model_name = request_data.get('model')
    prompt_data = request_data.get('prompt')
    code_to_convert = request_data.get('code')

    # Initialise the model based on the model name above
    model = MODELS.get(model_name)
    if model is None:
        return jsonify({"error": "Invalid model name"}), 400

    # Template for the prompt
    template = """Question: {question}\n\nAnswer: {answer}"""
    prompt = PromptTemplate.from_template(template)

    # Create a chain with the prompt and model
    chain = prompt | model

    # Invoke the chain to convert the code 
    converted_code = chain.invoke({"question": prompt_data, "answer": code_to_convert})

    # Construct response
    response = {
        "original_code": code_to_convert.strip(),
        "converted_code": converted_code.strip(),
        "model_used": model_name  
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
