def get_user_preferences(user_id: str):
    try:
        @user_profile_cb
        def call_user_service():
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.get(f"{USER_PROFILE_URL}/users/{user_id}")
                response.raise_for_status()
                return response.json()

        return call_user_service()

    except (httpx.RequestError, httpx.HTTPStatusError, pybreaker.CircuitBreakerError):
        raise
