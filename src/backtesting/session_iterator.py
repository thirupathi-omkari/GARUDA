def iterate_sessions(sessions):
    """Yield prepared historical sessions in order."""

    if not sessions:
        return

    for session in sessions:

        yield session