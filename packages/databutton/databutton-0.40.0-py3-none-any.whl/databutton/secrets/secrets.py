import os


def get(name: str) -> str:
    """Return environment variable value for key.

    This is a convenience function for getting a secret value from the environment,
    for legacy Databutton apps that use db.secrets.get(name) to get a secret value.

    You should replace this with os.environ[name] in your app.
    """

    if name in ("DATABASE_URL_DEV", "DATABASE_URL_PROD"):
        print(
            f'WARNING: db.secrets.get("{name}") is deprecated and mapped to '
            + 'environment-dependent os.environ.get("DATABASE_URL")'
        )
        name = "DATABASE_URL"
    elif name in ("DATABASE_URL_ADMIN_DEV", "DATABASE_URL_ADMIN_PROD"):
        print(
            f'WARNING: db.secrets.get("{name}") is deprecated and mapped to '
            + 'environment-dependent os.environ.get("DATABASE_URL") which doesn\'t provide admin access'
        )
        name = "DATABASE_URL"
    else:
        print(
            "WARNING: db.secrets.get(name) is deprecated. Please use os.environ.get(name) instead."
        )

    return os.environ[name]
