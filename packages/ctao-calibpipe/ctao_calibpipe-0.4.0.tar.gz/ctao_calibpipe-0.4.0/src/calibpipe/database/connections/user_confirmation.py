"""Function to ask for a user confirmation."""


def get_user_confirmation(prompt: str) -> bool:
    """Ask a confirmation from the user by displaying a prompt and asking yes or no.

    Parameters
    ----------
    prompt: str
        Prompt to display

    Returns
    -------
    bool
        Answer from the user
    """
    print(f"{prompt} [y/n, default: no]")
    user_input = input()
    return user_input.lower() == "y"
