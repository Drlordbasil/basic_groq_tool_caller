from groq import Groq
import json
import os

# Initialize the Groq client
client = Groq()
MODEL = 'llama3-groq-70b-8192-tool-use-preview'

def create_and_test_code(file_name, code):
    """Create and test Python code in a file within the workspace folder"""
    workspace_dir = "workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    file_path = os.path.join(workspace_dir, file_name)
    
    # Write the code to the file
    with open(file_path, "w") as f:
        f.write(code)
    
    # Test the code by executing it
    try:
        exec(open(file_path).read())
        return json.dumps({"result": "Code executed successfully"})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Define the tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_and_test_code",
            "description": "Create and test Python code in a file within the workspace folder",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to create"
                    },
                    "code": {
                        "type": "string",
                        "description": "The Python code to write and test"
                    }
                },
                "required": ["file_name", "code"]
            }
        }
    }
]

def run_conversation(user_prompt):
    # Initialize the conversation with system and user messages
    messages = [
        {
            "role": "system",
            "content": "You are a code assistant. Use the create_and_test_code function to create and test Python code in files within the workspace folder."
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ]
    
    # Make the initial API call to Groq
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096
    )
    
    # Extract the response and any tool call responses
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    if tool_calls:
        
        available_functions = {
            "create_and_test_code": create_and_test_code,
        }
        
        messages.append(response_message)

        # Process each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            function_response = function_to_call(
                file_name=function_args.get("file_name"),
                code=function_args.get("code")
            )
            # Add the tool response to the conversation
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        
        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        
        return second_response.choices[0].message.content
    return response_message.content


user_prompt = "Create a web scraper that scrapes the current price of BTC from yfinance, then test it."
print(run_conversation(user_prompt))
