"""WriteReport tool for parsing and writing diagnostic reports."""

from pathlib import Path
from typing import override, Optional, TYPE_CHECKING
from pydantic import Field
import structlog
import json
import re

from deepdiver_cli.react_core.tool import BaseTool, ToolInput, ToolRet
from deepdiver_cli.utils.file_util import read_text
from deepdiver_cli.utils.xml import extract_tag_content

# Avoid circular imports
if TYPE_CHECKING:
    from deepdiver_cli.session import Session

logger = structlog.get_logger(__name__)


class WriteReportInput(ToolInput):
    """Input parameters for WriteReport tool."""

    report_content: str = Field(
        description="""XML-tagged Markdown report content.
        Ensure the format is correct. If the content contains characters such as `{` or `}`, they need to be escaped to avoid JSON parsing errors.
        """
    )


class WriteReportTool(BaseTool[WriteReportInput]):
    """
    WriteReport tool for parsing XML-tagged Markdown reports and generating
    structured JSON and multiple Markdown files.

    Features:
    - Parses XML tags from Markdown content
    - Builds structured JSON matching report schema
    - Writes multiple output files to session reports directory
    - Handles optional fields gracefully
    - Supports multiple diagnosis entries (P1, P2, etc.)
    """

    name = "WriteReport"
    description = read_text(Path(__file__).parent / "write_report.md")
    params = WriteReportInput
    timeout_s = 30.0

    def __init__(self, session: Optional["Session"] = None) -> None:
        """
        Initialize WriteReport tool with session context.

        Args:
            session: Session object for writing reports. If None, tool will fail when called.
        """
        super().__init__()
        self.session = session

        if not self.session:
            logger.warning("WriteReportTool initialized without session")

    @override
    async def __call__(self, params: WriteReportInput) -> ToolRet:
        """
        Parse report content and generate output files.

        Args:
            params: Input containing report_content (XML-tagged Markdown)

        Returns:
            ToolRet with success status, list of written files, and summary
        """
        try:
            # Validate session is available
            if not self.session:
                return ToolRet(
                    success=False,
                    summary="WriteReport error: No session available for writing reports"
                )

            # Parse report content
            report_data = self._parse_report(params.report_content)

            # Validate required fields
            validation_error = self._validate_report_data(report_data)
            if validation_error:
                return ToolRet(
                    success=False, summary=f"Report validation failed: {validation_error}"
                )

            # Write output files
            written_files = self._write_report_files(report_data)

            # Return success
            return ToolRet(
                success=True,
                summary=f"Successfully wrote {len(written_files)} report files",
                data={
                    "written_files": written_files,
                    "diagnosis_count": len(report_data.get("diagnosis", [])),
                },
                human_readable_content=f"Generated report files:\n"
                + "\n".join(f"  - {f}" for f in written_files),
            )

        except Exception as e:
            logger.error("WriteReport error", error=str(e), exc_info=True)
            return ToolRet(success=False, summary=f"WriteReport error: {str(e)}")

    def _parse_report(self, content: str) -> dict:
        """
        Parse XML-tagged Markdown content into structured data.

        Args:
            content: Raw report content with XML tags

        Returns:
            Dictionary with parsed report data matching JSON schema
        """
        report_data = {}

        # Extract summary (required)
        summaries = extract_tag_content(content, "summary")
        if summaries:
            report_data["summary"] = summaries[0]

        # Extract timeline (optional)
        timelines = extract_tag_content(content, "timeline")
        if timelines:
            # Use the first timeline if there are multiple
            # This might be the top-level timeline
            report_data["timeline"] = timelines[0]

        # Extract diagnosis list
        diagnosis_blocks = extract_tag_content(content, "diagnosis")
        report_data["diagnosis"] = []

        for diagnosis_block in diagnosis_blocks:
            diagnosis_entry = self._parse_diagnosis_block(diagnosis_block)
            report_data["diagnosis"].append(diagnosis_entry)

        # Extract cross_analysis (optional)
        cross_analyses = extract_tag_content(content, "cross_analysis")
        if cross_analyses:
            report_data["cross_analysis"] = cross_analyses[0]

        # Extract recommendations (optional)
        recommendations = extract_tag_content(content, "recommendations")
        if recommendations:
            report_data["recommendations"] = recommendations[0]

        # Extract metadata (optional)
        metadata_blocks = extract_tag_content(content, "metadata")
        if metadata_blocks:
            report_data["metadata"] = self._parse_metadata_block(metadata_blocks[0])

        return report_data

    def _parse_diagnosis_block(self, block: str) -> dict:
        """
        Parse a single diagnosis block.

        Args:
            block: XML content within <diagnosis> tags

        Returns:
            Dictionary with diagnosis data
        """
        diagnosis = {}

        # Extract title
        titles = extract_tag_content(block, "title")
        if titles:
            diagnosis["title"] = titles[0]

        # Extract conclusion
        conclusions = extract_tag_content(block, "conclusion")
        if conclusions:
            diagnosis["conclusion"] = conclusions[0]

        # Extract confidence
        confidences = extract_tag_content(block, "confidence")
        if confidences:
            diagnosis["confidence"] = confidences[0]

        # Extract confidence_score
        confidence_scores = extract_tag_content(block, "confidence_score")
        if confidence_scores:
            try:
                diagnosis["confidence_score"] = float(confidence_scores[0])
            except ValueError:
                diagnosis["confidence_score"] = 0.0

        # Extract root_cause_level
        root_cause_levels = extract_tag_content(block, "root_cause_level")
        if root_cause_levels:
            diagnosis["root_cause_level"] = root_cause_levels[0]

        # Extract root_cause_score
        root_cause_scores = extract_tag_content(block, "root_cause_score")
        if root_cause_scores:
            try:
                diagnosis["root_cause_score"] = float(root_cause_scores[0])
            except ValueError:
                diagnosis["root_cause_score"] = 0

        # Extract reproduction_path
        reproduction_paths = extract_tag_content(block, "reproduction_path")
        if reproduction_paths:
            diagnosis["reproduction_path"] = reproduction_paths[0]

        # Extract timeline (diagnosis-level)
        timelines = extract_tag_content(block, "timeline")
        if timelines:
            diagnosis["timeline"] = timelines[0]

        # Extract evidence_chain
        evidence_chains = extract_tag_content(block, "evidence_chain")
        if evidence_chains:
            diagnosis["evidence_chain"] = evidence_chains[0]

        # Extract alternative_causes
        alternative_causes_blocks = extract_tag_content(block, "alternative_causes")
        if alternative_causes_blocks:
            diagnosis["alternative_causes"] = self._parse_alternative_causes(
                alternative_causes_blocks[0]
            )
        else:
            diagnosis["alternative_causes"] = []

        return diagnosis

    def _parse_alternative_causes(self, block: str) -> list:
        """
        Parse alternative causes block.

        Args:
            block: XML content within <alternative_causes> tags

        Returns:
            List of alternative cause dictionaries
        """
        causes = []
        cause_blocks = extract_tag_content(block, "alternative_cause")

        for cause_block in cause_blocks:
            cause = {}

            # Extract hypothesis
            hypotheses = extract_tag_content(cause_block, "hypothesis")
            if hypotheses:
                cause["hypothesis"] = hypotheses[0]

            # Extract confidence
            confidences = extract_tag_content(cause_block, "confidence")
            if confidences:
                cause["confidence"] = confidences[0]

            # Extract confidence_score
            confidence_scores = extract_tag_content(cause_block, "confidence_score")
            if confidence_scores:
                try:
                    cause["confidence_score"] = float(confidence_scores[0])
                except ValueError:
                    cause["confidence_score"] = 0.0

            # Extract root_cause_level
            root_cause_levels = extract_tag_content(cause_block, "root_cause_level")
            if root_cause_levels:
                cause["root_cause_level"] = root_cause_levels[0]

            # Extract root_cause_score
            root_cause_scores = extract_tag_content(cause_block, "root_cause_score")
            if root_cause_scores:
                try:
                    cause["root_cause_score"] = float(root_cause_scores[0])
                except ValueError:
                    cause["root_cause_score"] = 0

            # Extract exclusion_reason
            exclusion_reasons = extract_tag_content(cause_block, "exclusion_reason")
            if exclusion_reasons:
                cause["exclusion_reason"] = exclusion_reasons[0]

            causes.append(cause)

        return causes

    def _parse_metadata_block(self, block: str) -> dict:
        """
        Parse metadata block.

        Args:
            block: XML content within <metadata> tags

        Returns:
            Dictionary with metadata
        """
        metadata = {}

        # Extract diagnosis_date
        dates = extract_tag_content(block, "diagnosis_date")
        if dates:
            metadata["diagnosis_date"] = dates[0]

        # Extract review_count
        review_counts = extract_tag_content(block, "review_count")
        if review_counts:
            try:
                metadata["review_count"] = int(review_counts[0])
            except ValueError:
                metadata["review_count"] = 0

        # Extract review_result
        review_results = extract_tag_content(block, "review_result")
        if review_results:
            metadata["review_result"] = review_results[0]

        # Extract review_summary
        review_summaries = extract_tag_content(block, "review_summary")
        if review_summaries:
            metadata["review_summary"] = review_summaries[0]

        # Extract knowledge_keys
        knowledge_keys_blocks = extract_tag_content(block, "knowledge_keys")
        if knowledge_keys_blocks:
            keys = extract_tag_content(knowledge_keys_blocks[0], "key")
            metadata["knowledge_keys"] = keys
        else:
            metadata["knowledge_keys"] = []

        # Extract attachment_paths
        attachment_paths_blocks = extract_tag_content(block, "attachment_paths")
        if attachment_paths_blocks:
            paths = extract_tag_content(attachment_paths_blocks[0], "path")
            metadata["attachment_paths"] = paths
        else:
            metadata["attachment_paths"] = []

        # Extract code_paths
        code_paths_blocks = extract_tag_content(block, "code_paths")
        if code_paths_blocks:
            paths = extract_tag_content(code_paths_blocks[0], "path")
            metadata["code_paths"] = paths
        else:
            metadata["code_paths"] = []

        return metadata

    def _validate_report_data(self, data: dict) -> Optional[str]:
        """
        Validate required fields in parsed report data.

        Args:
            data: Parsed report data dictionary

        Returns:
            None if valid, error message string if invalid
        """
        # Check for required summary
        if "summary" not in data or not data["summary"]:
            return "Missing required field: summary"

        # Check for at least one diagnosis
        if "diagnosis" not in data or not data["diagnosis"]:
            return "Missing required field: diagnosis (at least one diagnosis required)"

        # Validate each diagnosis has required fields
        for idx, diagnosis in enumerate(data["diagnosis"]):
            if "title" not in diagnosis or not diagnosis["title"]:
                return f"Diagnosis {idx + 1}: Missing required field: title"
            if "conclusion" not in diagnosis or not diagnosis["conclusion"]:
                return f"Diagnosis {idx + 1}: Missing required field: conclusion"

        return None

    def _extract_problem_number(self, title: str) -> Optional[str]:
        """
        Extract problem number (P1, P2, etc.) from title.

        Args:
            title: Diagnosis title (e.g., "### 2.1 P1: Problem Name")

        Returns:
            Problem number string (e.g., "P1") or None if not found
        """
        # Try to match patterns like "P1:", "P2:", "P1：", "P1 ", etc.
        match = re.search(r"P(\d+)[：:\s]", title)
        if match:
            return f"P{match.group(1)}"
        return None

    def _write_report_files(self, data: dict) -> list:
        """
        Write all report files to session reports directory.

        Args:
            data: Parsed and validated report data

        Returns:
            List of written file paths (relative to reports_dir)
        """
        written_files = []

        # 1. Write report.json
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        self.session.write_report("report.json", json_content)
        written_files.append("report.json")

        # 2. Write summary.md
        if "summary" in data:
            self.session.write_summary_md(data["summary"])
            written_files.append("summary.md")

        # 3. Write timeline.md (if present at top level)
        if "timeline" in data and data["timeline"]:
            self.session.write_timeline_md(data["timeline"])
            written_files.append("timeline.md")

        # 4. Write individual diagnosis and evidence chain files
        for idx, diagnosis in enumerate(data.get("diagnosis", [])):
            # Extract problem number
            problem_num = self._extract_problem_number(diagnosis.get("title", ""))
            if not problem_num:
                problem_num = f"P{idx + 1}"

            # Write diagnosis file
            diagnosis_md = self._build_diagnosis_markdown(diagnosis, problem_num)
            diagnosis_filename = f"diagnosis_{problem_num}.md"
            self.session.write_report(diagnosis_filename, diagnosis_md)
            written_files.append(diagnosis_filename)

            # Write evidence chain file (if present)
            if "evidence_chain" in diagnosis and diagnosis["evidence_chain"]:
                evidence_filename = f"evidence_chain_{problem_num}.md"
                self.session.write_report(evidence_filename, diagnosis["evidence_chain"])
                written_files.append(evidence_filename)

        return written_files

    def _build_diagnosis_markdown(self, diagnosis: dict, problem_num: str) -> str:
        """
        Build Markdown content for a single diagnosis.

        Args:
            diagnosis: Diagnosis data dictionary
            problem_num: Problem number (e.g., "P1")

        Returns:
            Markdown content string
        """
        lines = []

        # Title
        if "title" in diagnosis:
            lines.append(diagnosis["title"])
            lines.append("")

        # Conclusion
        if "conclusion" in diagnosis:
            lines.append(diagnosis["conclusion"])
            lines.append("")

        # Confidence info
        if "confidence" in diagnosis:
            lines.append(f"**Confidence:** {diagnosis['confidence']}")
        if "confidence_score" in diagnosis:
            lines.append(f"**Confidence Score:** {diagnosis['confidence_score']}")
        if "root_cause_level" in diagnosis:
            lines.append(f"**Root Cause Level:** {diagnosis['root_cause_level']}")
        if "root_cause_score" in diagnosis:
            lines.append(f"**Root Cause Score:** {diagnosis['root_cause_score']}")
        lines.append("")

        # Reproduction path
        if "reproduction_path" in diagnosis:
            lines.append("## Reproduction Path")
            lines.append(diagnosis["reproduction_path"])
            lines.append("")

        # Timeline
        if "timeline" in diagnosis:
            lines.append("## Timeline")
            lines.append(diagnosis["timeline"])
            lines.append("")

        # Alternative causes
        if "alternative_causes" in diagnosis and diagnosis["alternative_causes"]:
            lines.append("## Alternative Causes")
            for cause in diagnosis["alternative_causes"]:
                if "hypothesis" in cause:
                    lines.append(f"### {cause['hypothesis']}")
                if "confidence" in cause:
                    lines.append(f"**Confidence:** {cause['confidence']}")
                if "exclusion_reason" in cause:
                    lines.append(f"**Exclusion Reason:** {cause['exclusion_reason']}")
                lines.append("")

        return "\n".join(lines)
