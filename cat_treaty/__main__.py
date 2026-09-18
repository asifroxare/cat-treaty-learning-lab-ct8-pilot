"""Run the CT6 API with deployment-neutral environment settings."""

import uvicorn

from cat_treaty.runtime import RuntimeSettings


def main() -> None:
    settings = RuntimeSettings.from_environment()
    uvicorn.run(
        "cat_treaty.api:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
