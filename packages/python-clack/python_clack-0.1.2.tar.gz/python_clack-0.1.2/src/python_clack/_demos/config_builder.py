"""Configuration Builder - Settings with disabled options."""

from python_clack import (
    cancel,
    confirm,
    intro,
    is_cancel,
    log,
    multiselect,
    outro,
    select,
)


def run() -> None:
    """Run the configuration builder demo."""
    intro("Project Configuration Builder")

    log.info("Some options are disabled to show the feature")

    # Framework selection with disabled options
    framework_result = select(
        "Choose a framework",
        options=[
            {"value": "fastapi", "label": "FastAPI", "hint": "modern async"},
            {"value": "flask", "label": "Flask", "hint": "simple & flexible"},
            {"value": "django", "label": "Django", "hint": "batteries included"},
            {
                "value": "enterprise",
                "label": "Enterprise Suite",
                "hint": "requires license",
                "disabled": True,
            },
        ],
    )
    if is_cancel(framework_result):
        cancel()
        return
    framework = str(framework_result)

    # Database selection
    database = select(
        "Select database",
        options=[
            {"value": "sqlite", "label": "SQLite", "hint": "file-based"},
            {"value": "postgres", "label": "PostgreSQL", "hint": "production ready"},
            {"value": "mysql", "label": "MySQL", "hint": "widely supported"},
            {
                "value": "oracle",
                "label": "Oracle",
                "hint": "enterprise only",
                "disabled": True,
            },
        ],
    )
    if is_cancel(database):
        cancel()
        return

    # Features with some disabled based on framework
    is_django = framework == "django"
    features: list[str] = multiselect(  # type: ignore[assignment]
        "Select features to enable",
        options=[
            {"value": "auth", "label": "Authentication"},
            {"value": "api", "label": "REST API"},
            {
                "value": "admin",
                "label": "Admin Panel",
                "hint": "built-in" if is_django else "requires setup",
            },
            {"value": "celery", "label": "Background Tasks"},
            {
                "value": "graphql",
                "label": "GraphQL",
                "hint": "coming soon",
                "disabled": True,
            },
        ],
        required=True,
    )
    if is_cancel(features):
        cancel()
        return

    # Deployment target
    deploy = select(
        "Deployment target",
        options=[
            {"value": "docker", "label": "Docker", "hint": "containerized"},
            {
                "value": "serverless",
                "label": "Serverless",
                "hint": "AWS Lambda/Cloud Functions",
            },
            {"value": "vps", "label": "VPS", "hint": "traditional server"},
            {
                "value": "kubernetes",
                "label": "Kubernetes",
                "hint": "requires cluster",
                "disabled": True,
            },
        ],
    )
    if is_cancel(deploy):
        cancel()
        return

    # Custom confirm labels
    generate = confirm(
        "Generate configuration files?",
        active="Generate",
        inactive="Skip",
        initial_value=True,
    )
    if is_cancel(generate):
        cancel()
        return

    # Summary
    log.success(f"Framework: {framework}")
    log.info(f"Database: {database}")
    log.step(f"Features: {', '.join(features)}")
    log.info(f"Deploy to: {deploy}")

    if generate:
        log.success("Configuration files generated!")
    else:
        log.warn("Skipped file generation")

    outro("Configuration complete!")
