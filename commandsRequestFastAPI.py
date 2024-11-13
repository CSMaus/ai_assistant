from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from command_listener import command_queue

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import openai
from command_listener import command_queue
import os

app = FastAPI()
openai.api_key = ""
with open(os.path.join(os.path.dirname(__file__), 'key.txt'), 'r') as file:
    openai.api_key = file.read().strip()


class CommandRequest(BaseModel):
    command: str
    args: list = []


class TextRequest(BaseModel):
    text: str


def parse_response(response_text):
    """
    Parse the response text from the chat-bot to identify the command and arguments.
    """
    try:
        response_data = eval(response_text)  # Caution with eval; ensure response is safe or use JSON.
        command = response_data.get("command")
        args = response_data.get("args", [])
        return command, args
    except Exception as e:
        print("Failed to parse response:", e)
        return None, []


def get_command_from_text(user_input):
    """
    Send the user's input to OpenAI's API to generate a command response.
    """
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Interpret the following command: {user_input}. Respond in JSON format, with 'command' and 'args'."
               f"Available commands: 'loadData' which requires file path as input, 'updatePlot', 'getFileInformation'.",
        max_tokens=100,
        temperature=0.5
    )

    response_text = response.choices[0].text.strip()
    print("Chat-bot Response:", response_text)
    return parse_response(response_text)


@app.post("/add_command")
async def add_command(request: CommandRequest):
    command_queue.put((request.command, request.args))
    return {"status": "Command added to queue"}


@app.post("/process_text")
async def process_text(request: TextRequest):
    command, args = get_command_from_text(request.text)
    if command:
        command_queue.put((command, args))
        return {"status": f"Command '{command}' with args {args} added to queue"}
    else:
        raise HTTPException(status_code=400, detail="Failed to interpret command")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
