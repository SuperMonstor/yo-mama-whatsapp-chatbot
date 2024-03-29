from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time
import json

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = OpenAI(api_key=OPENAI_API_KEY)

# JSON file with gpt instructions
with open('instructions.json') as f:
    instructions = json.load(f)


def create_assistant():
    assistant = client.beta.assistants.create(
        name=instructions['yo-mama-gpt']['name'],
        instructions=instructions['yo-mama-gpt']['instructions'],
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
    )
    # Insert this id into .env file
    print(f'Assistant ID: {assistant.id}')
    return assistant


assistant = create_assistant()

# manage chat threads using shelve
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

# Responses 
def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To {name}:", new_message)
    return new_message


def run_assistant(thread):
  # Retrieve the Assistant
  assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

  # Run the assistant
  run = client.beta.threads.runs.create(
      thread_id=thread.id,
      assistant_id=assistant.id,
  )

  # Wait for completion
  while run.status != "completed":
      # Be nice to the API
      time.sleep(0.5)
      run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

  # Retrieve the Messages
  messages = client.beta.threads.messages.list(thread_id=thread.id)
  new_message = messages.data[0].content[0].text.value
  print(f"Generated message: {new_message}")
  return new_message

new_message = generate_response("chocolate cake.", "123", "John")