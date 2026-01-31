#!/usr/bin/env python3
"""OAuth2 flow example for SecondMe SDK."""

from seme import OAuth2Client, SecondMeClient, TokenResponse

# Replace with your OAuth2 credentials
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REDIRECT_URI = "https://your-app.com/callback"


def on_token_refresh(new_tokens: TokenResponse):
    """Callback when tokens are refreshed."""
    print(f"Tokens refreshed! New access token expires in {new_tokens.expires_in} seconds")
    # In a real app, you would persist the new tokens here
    # save_tokens_to_database(new_tokens)


def main():
    # Step 1: Create OAuth2 client
    oauth = OAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
    )

    # Step 2: Generate authorization URL
    auth_url = oauth.get_authorization_url(
        scopes=["user.info", "user.info.shades", "chat", "note.add"],
        state="random_state_for_csrf_protection",
    )
    print("=== Step 1: Direct user to authorize ===")
    print(f"Authorization URL: {auth_url}")
    print()

    # Step 3: After user authorizes, they'll be redirected to your redirect_uri
    # with a 'code' parameter. Exchange it for tokens:
    print("=== Step 2: Exchange code for tokens ===")
    # In a real app, you'd get this from the redirect callback
    authorization_code = input("Enter the authorization code: ")

    if not authorization_code:
        print("No code provided, exiting.")
        return

    try:
        tokens = oauth.exchange_code(code=authorization_code)
        print(f"Access Token: {tokens.access_token[:20]}...")
        print(f"Refresh Token: {tokens.refresh_token[:20]}...")
        print(f"Expires In: {tokens.expires_in} seconds")
        print(f"Scopes: {tokens.scopes}")
        print()

        # Step 4: Create client with auto-refresh enabled
        print("=== Step 3: Use the API ===")
        client = SecondMeClient.from_oauth(
            oauth_client=oauth,
            token_response=tokens,
            on_token_refresh=on_token_refresh,
        )

        # Now use the client as normal
        user = client.get_user_info()
        print(f"Hello, {user.name}!")

        # The client will automatically refresh the token when it expires
        # (about 5 minutes before the 2-hour expiry)

        client.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
