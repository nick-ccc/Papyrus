import logging
import sys

import uvicorn


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def main() -> None:
    configure_logging()

    from papyrus_agent.utils.config import settings
    from papyrus_agent.utils.templates import template_registry

    log = logging.getLogger(__name__)
    log.info("Starting Papyrus API")
    log.info(
        "Vision LLM: %s/%s @ %s",
        settings.vision_provider, settings.vision_model, settings.vision_base_url,
    )
    log.info(
        "Document LLM: %s/%s @ %s",
        settings.document_provider, settings.document_model, settings.document_base_url,
    )
    log.info(
        "Templates (%s): %s",
        template_registry.directory, ", ".join(template_registry.ids()) or "none",
    )

    uvicorn.run(
        "papyrus_agent.api:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
