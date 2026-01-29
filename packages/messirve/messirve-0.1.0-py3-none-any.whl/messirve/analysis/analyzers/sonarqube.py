"""SonarQube analyzer integration."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from messirve.analysis.analyzers.base import BaseAnalyzer
from messirve.analysis.models import (
    AnalysisCategory,
    AnalysisFinding,
    AnalysisMetrics,
    ImpactLevel,
)
from messirve.feature_flags import FeatureFlag, FeatureFlags


class SonarQubeAnalyzer(BaseAnalyzer):
    """Analyzer that integrates with SonarQube scanner.

    This analyzer runs the sonar-scanner CLI tool and optionally
    fetches results from a SonarQube server.

    Requires:
    - sonar-scanner to be installed and available in PATH
    - MESSIRVE_FF_SONARQUBE feature flag to be enabled

    Configuration:
    - server_url: SonarQube server URL (optional)
    - project_key: SonarQube project key (optional)
    - token: SonarQube authentication token (optional, read from SONAR_TOKEN env)
    """

    name = "sonarqube"
    description = "SonarQube static analysis integration"

    def __init__(
        self,
        config: Any,
        server_url: str | None = None,
        project_key: str | None = None,
        token: str | None = None,
    ) -> None:
        """Initialize the SonarQube analyzer.

        Args:
            config: Analysis configuration.
            server_url: SonarQube server URL.
            project_key: SonarQube project key.
            token: SonarQube authentication token.
        """
        super().__init__(config)
        self.server_url = server_url
        self.project_key = project_key
        self.token = token

    def is_available(self) -> bool:
        """Check if sonar-scanner is available and feature flag is enabled.

        Returns:
            True if sonar-scanner is available and the feature flag is enabled.
        """
        if not FeatureFlags.is_enabled(FeatureFlag.SONARQUBE_INTEGRATION):
            return False
        return shutil.which("sonar-scanner") is not None

    def analyze(self, paths: list[Path]) -> tuple[AnalysisMetrics, list[AnalysisFinding]]:
        """Run SonarQube analysis on the given paths.

        Args:
            paths: Paths to analyze.

        Returns:
            Tuple of (metrics, findings).
        """
        findings: list[AnalysisFinding] = []
        metrics = AnalysisMetrics()

        if not self.is_available():
            return metrics, findings

        # Determine project base directory
        if paths:
            project_base = paths[0].parent if paths[0].is_file() else paths[0]
        else:
            project_base = Path.cwd()

        # Build sonar-scanner command
        cmd = ["sonar-scanner", f"-Dsonar.projectBaseDir={project_base}"]

        if self.project_key:
            cmd.append(f"-Dsonar.projectKey={self.project_key}")
        if self.server_url:
            cmd.append(f"-Dsonar.host.url={self.server_url}")
        if self.token:
            cmd.append(f"-Dsonar.token={self.token}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                findings.append(
                    AnalysisFinding(
                        category=AnalysisCategory.QUALITY,
                        message=f"SonarQube scan failed: {result.stderr[:200]}",
                        impact=ImpactLevel.MEDIUM,
                        rule_id="SONAR001",
                    )
                )
                return metrics, findings

            # If server is configured, fetch results
            if self.server_url and self.project_key:
                server_findings = self._fetch_findings_from_server()
                findings.extend(server_findings)
                server_metrics = self._fetch_metrics_from_server()
                if server_metrics:
                    metrics = server_metrics

        except subprocess.TimeoutExpired:
            findings.append(
                AnalysisFinding(
                    category=AnalysisCategory.QUALITY,
                    message="SonarQube scan timed out",
                    impact=ImpactLevel.MEDIUM,
                    rule_id="SONAR002",
                )
            )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            findings.append(
                AnalysisFinding(
                    category=AnalysisCategory.QUALITY,
                    message=f"SonarQube scan error: {e}",
                    impact=ImpactLevel.MEDIUM,
                    rule_id="SONAR003",
                )
            )

        return metrics, findings

    def _fetch_findings_from_server(self) -> list[AnalysisFinding]:
        """Fetch issues from SonarQube server API.

        Returns:
            List of findings from the server.
        """
        if not self.server_url or not self.project_key:
            return []

        try:
            import urllib.error
            import urllib.request

            url = f"{self.server_url}/api/issues/search?componentKeys={self.project_key}"
            headers = {}
            if self.token:
                import base64

                auth = base64.b64encode(f"{self.token}:".encode()).decode()
                headers["Authorization"] = f"Basic {auth}"

            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode())

            findings: list[AnalysisFinding] = []
            for issue in data.get("issues", []):
                severity = issue.get("severity", "MAJOR")
                impact = self._severity_to_impact(severity)

                findings.append(
                    AnalysisFinding(
                        category=AnalysisCategory.QUALITY,
                        message=issue.get("message", ""),
                        file_path=issue.get("component", "").split(":")[-1],
                        line_number=issue.get("line"),
                        impact=impact,
                        rule_id=issue.get("rule", ""),
                    )
                )

            return findings

        except (urllib.error.URLError, json.JSONDecodeError, KeyError):
            return []

    def _fetch_metrics_from_server(self) -> AnalysisMetrics | None:
        """Fetch metrics from SonarQube server API.

        Returns:
            AnalysisMetrics if successful, None otherwise.
        """
        if not self.server_url or not self.project_key:
            return None

        try:
            import urllib.error
            import urllib.request

            metric_keys = "complexity,cognitive_complexity,violations,bugs,vulnerabilities"
            url = (
                f"{self.server_url}/api/measures/component?"
                f"component={self.project_key}&metricKeys={metric_keys}"
            )
            headers = {}
            if self.token:
                import base64

                auth = base64.b64encode(f"{self.token}:".encode()).decode()
                headers["Authorization"] = f"Basic {auth}"

            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode())

            measures = {
                m["metric"]: float(m.get("value", 0))
                for m in data.get("component", {}).get("measures", [])
            }

            return AnalysisMetrics(
                avg_cyclomatic_complexity=measures.get("complexity", 0),
                avg_cognitive_complexity=measures.get("cognitive_complexity", 0),
                total_warnings=int(measures.get("violations", 0)),
                security_issues=int(measures.get("vulnerabilities", 0)),
            )

        except (urllib.error.URLError, json.JSONDecodeError, KeyError):
            return None

    @staticmethod
    def _severity_to_impact(severity: str) -> ImpactLevel:
        """Convert SonarQube severity to ImpactLevel.

        Args:
            severity: SonarQube severity string.

        Returns:
            Corresponding ImpactLevel.
        """
        mapping = {
            "BLOCKER": ImpactLevel.CRITICAL,
            "CRITICAL": ImpactLevel.CRITICAL,
            "MAJOR": ImpactLevel.HIGH,
            "MINOR": ImpactLevel.MEDIUM,
            "INFO": ImpactLevel.LOW,
        }
        return mapping.get(severity, ImpactLevel.MEDIUM)
