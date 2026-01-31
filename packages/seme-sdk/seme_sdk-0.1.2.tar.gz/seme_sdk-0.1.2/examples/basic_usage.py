#!/usr/bin/env python3
"""Basic usage example for SecondMe SDK."""

from seme import SecondMeClient

# Replace with your actual API key
API_KEY = "lba_ak_your_api_key_here"


def main():
    # Create a client with API Key authentication
    client = SecondMeClient(api_key=API_KEY)

    try:
        # Get user information
        print("=== User Info ===")
        user = client.get_user_info()
        print(f"Name: {user.name}")
        print(f"Email: {user.email}")
        print(f"Bio: {user.bio}")
        print(f"Profile Completeness: {user.profile_completeness}")
        print()

        # Get user interest shades
        print("=== User Shades ===")
        shades = client.get_user_shades()
        for shade in shades:
            print(f"- {shade.shade_name} (confidence: {shade.confidence_level})")
        print()

        # Get user soft memory
        print("=== Soft Memory ===")
        memory_response = client.get_user_softmemory(page_size=5)
        print(f"Total memories: {memory_response.total}")
        for memory in memory_response.items:
            print(f"- {memory.content[:50]}...")
        print()

        # Add a note
        print("=== Add Note ===")
        note_id = client.add_note(
            content="This is a test note from the SDK",
            title="SDK Test Note",
        )
        print(f"Created note with ID: {note_id}")
        print()

        # Get chat sessions
        print("=== Chat Sessions ===")
        sessions = client.get_session_list()
        print(f"Total sessions: {len(sessions)}")
        for session in sessions[:3]:  # Show first 3
            print(f"- Session {session.session_id}: {session.last_message[:30] if session.last_message else 'No messages'}...")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
