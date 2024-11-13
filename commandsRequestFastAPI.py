from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from command_listener import command_queue

app = FastAPI()


class CommandRequest(BaseModel):
    command: str
    args: list = []


@app.post("/add_command")
async def add_command(request: CommandRequest):
    command_queue.put((request.command, request.args))
    return {"status": "Command added to queue"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)


