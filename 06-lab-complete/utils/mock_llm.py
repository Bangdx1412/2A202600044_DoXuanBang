"""Simple mock LLM used for offline testing."""
import random
import time


RESPONSES = {
    "default": [
        "This is a mock AI response generated for local testing.",
        "The production agent is working correctly with the mock model.",
        "Your request was processed successfully by the AI agent.",
    ],
    "docker": [
        "Containers package an app and its dependencies so it can run consistently anywhere.",
    ],
    "redis": [
        "Redis is being used here to keep state shared across multiple instances.",
    ],
    "deploy": [
        "Deployment moves your application from your machine to a server users can access.",
    ],
}


def ask(question: str, delay: float = 0.1) -> str:
    time.sleep(delay + random.uniform(0, 0.05))
    q = question.lower()
    for keyword, answers in RESPONSES.items():
        if keyword in q:
            return random.choice(answers)
    return random.choice(RESPONSES["default"])


def ask_stream(question: str):
    response = ask(question)
    for word in response.split():
        time.sleep(0.05)
        yield word + " "
