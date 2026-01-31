#!/usr/bin/env python3
"""Streaming chat example for SecondMe SDK."""

from seme import SecondMeClient

# Replace with your actual API key
API_KEY = "lba_ak_your_api_key_here"


def main():
    client = SecondMeClient(api_key=API_KEY)

    try:
        # Simple streaming chat
        print("=== Simple Streaming Chat ===")
        print("You: Hello, can you introduce yourself?")
        print("Assistant: ", end="", flush=True)

        session_id = None
        for chunk in client.chat_stream("Hello, can you introduce yourself?"):
            if chunk.delta:
                print(chunk.delta, end="", flush=True)
            if chunk.session_id:
                session_id = chunk.session_id

        print("\n")

        # Continue the conversation in the same session
        if session_id:
            print(f"(Session ID: {session_id})")
            print()
            print("=== Continuing Conversation ===")
            print("You: What are your main capabilities?")
            print("Assistant: ", end="", flush=True)

            for chunk in client.chat_stream(
                "What are your main capabilities?",
                session_id=session_id,
            ):
                if chunk.delta:
                    print(chunk.delta, end="", flush=True)

            print("\n")

        # Chat with custom system prompt
        print("=== Chat with Custom System Prompt ===")
        print("You: Tell me a joke")
        print("Assistant: ", end="", flush=True)

        for chunk in client.chat_stream(
            "Tell me a joke",
            system_prompt="You are a friendly comedian who loves puns.",
        ):
            if chunk.delta:
                print(chunk.delta, end="", flush=True)

        print("\n")

        # Get session history
        if session_id:
            print("=== Session History ===")
            messages = client.get_session_messages(session_id)
            for msg in messages:
                role = "You" if msg.role == "user" else "Assistant"
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                print(f"{role}: {content}")

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
