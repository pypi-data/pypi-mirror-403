"""Progress & Logging - Spinner states and log levels."""

import time

from python_clack import (
    cancel,
    intro,
    is_cancel,
    log,
    outro,
    select,
    spinner,
)


def run() -> None:
    """Run the progress and logging demo."""
    intro("Progress & Logging Demo")

    # Show all log levels first
    log.message("This is log.message() - plain text")
    log.info("This is log.info() - informational")
    log.success("This is log.success() - completed")
    log.warn("This is log.warn() - warning")
    log.error("This is log.error() - error")
    log.step("This is log.step() - progress step")

    while True:
        # Choose spinner outcome
        outcome_result = select(
            "Choose spinner outcome to demonstrate",
            options=[
                {"value": "success", "label": "Success", "hint": "normal completion"},
                {"value": "error", "label": "Error", "hint": "failure state"},
                {"value": "warn", "label": "Warning", "hint": "completed with warnings"},
                {"value": "cancel", "label": "Cancel", "hint": "user cancellation"},
                {"value": "exit", "label": "Back to menu", "hint": "exit this demo"},
            ],
        )
        if is_cancel(outcome_result):
            cancel()
            return
        outcome = str(outcome_result)

        if outcome == "exit":
            break

        # Demonstrate spinner with chosen outcome
        s = spinner()
        s.start("Starting deployment...")
        time.sleep(0.8)

        s.message("Pulling latest changes...")
        time.sleep(0.8)

        s.message("Running tests...")
        time.sleep(0.8)

        s.message("Building application...")
        time.sleep(0.8)

        # End based on choice
        if outcome == "success":
            s.stop("Deployment completed successfully!")
        elif outcome == "error":
            s.error("Deployment failed: connection timeout")
        elif outcome == "warn":
            s.warn("Deployed with 2 deprecation warnings")
        else:
            s.cancel("Deployment cancelled by user")

        print()  # Spacing before next selection

    outro("Progress demo complete!")
