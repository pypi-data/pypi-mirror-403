"""HTMLReporter - Generate HTML reports from conversation events."""

import json
import webbrowser
from pathlib import Path
from typing import Any

from voiceground.evaluations import EvaluationResult
from voiceground.events import VoicegroundEvent
from voiceground.reporters.base import BaseReporter


def _get_version() -> str:
    """Get the package version, avoiding circular imports."""
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version("voiceground")
    except (PackageNotFoundError, Exception):
        return "0.0.0+dev"


class HTMLReporter(BaseReporter):
    """Reporter that records events and generates self-contained HTML reports.

    Collects all events during pipeline execution and generates an interactive
    HTML report when the pipeline ends. The report is named
    "voiceground_report_{conversation_id}.html".

    Args:
        output_dir: Directory to write output files. Defaults to "reports".
        auto_open: Whether to open the HTML report in browser after generation.
    """

    def __init__(
        self,
        output_dir: str | Path = "reports",
        auto_open: bool = False,
    ):
        self._output_dir = Path(output_dir)
        self._auto_open = auto_open
        self._events: list[VoicegroundEvent] = []
        self._evaluations: list[EvaluationResult] = []
        self._finalized = False
        self._conversation_id: str | None = None

    async def on_start(self, conversation_id: str) -> None:
        """Set the conversation ID when the pipeline starts."""
        self._conversation_id = conversation_id

    async def on_event(self, event: VoicegroundEvent) -> None:
        """Record an event."""
        self._events.append(event)

    async def on_evaluations(self, evaluations: list[EvaluationResult]) -> None:
        """Record evaluation results."""
        self._evaluations = evaluations

    async def on_end(self) -> None:
        """Generate HTML report."""
        # Guard against multiple calls
        if self._finalized:
            return
        self._finalized = True

        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Generate HTML report
        events_data = [event.to_dict() for event in self._events]
        evaluations_data = [e.model_dump() for e in self._evaluations]
        html_path = self._generate_html_report(events_data, evaluations_data)

        if self._auto_open and html_path:
            # Convert path to file:// URL format (works cross-platform)
            file_url = html_path.absolute().as_uri()
            webbrowser.open(file_url)

        # Reset events for potential reuse
        self._events = []

    def _generate_html_report(
        self, events_data: list[dict[str, Any]], evaluations_data: list[dict[str, Any]]
    ) -> Path | None:
        """Generate an HTML report with embedded events and evaluations data.

        Returns the path to the generated HTML file, or None if the
        bundled client is not available.
        """
        # Try to load bundled client template
        template_path = Path(__file__).parent.parent / "_static" / "index.html"

        if not template_path.exists():
            return None

        with open(template_path, encoding="utf-8") as f:
            template = f.read()

        # Inject events data, evaluations, conversation_id, and version into the template
        events_json = json.dumps(events_data)
        evaluations_json = json.dumps(evaluations_data)
        conversation_id_json = (
            json.dumps(self._conversation_id) if self._conversation_id else "null"
        )
        version_json = json.dumps(_get_version())
        script_content = f"""<script>
window.__VOICEGROUND_EVENTS__ = {events_json};
window.__VOICEGROUND_CONVERSATION_ID__ = {conversation_id_json};
window.__VOICEGROUND_VERSION__ = {version_json};
window.__VOICEGROUND_EVALUATIONS__ = {evaluations_json};
</script>"""
        html_content = template.replace(
            "<!-- VOICEGROUND_EVENTS_PLACEHOLDER -->",
            script_content,
        )

        # Generate filename with conversation_id
        if self._conversation_id:
            filename = f"voiceground_report_{self._conversation_id}.html"
        else:
            filename = "voiceground_report.html"

        html_path = self._output_dir / filename
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path
