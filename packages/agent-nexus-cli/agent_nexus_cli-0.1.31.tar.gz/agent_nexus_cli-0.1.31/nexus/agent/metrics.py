"""Metrics Module.

Handles tracking and local storage of chat session metrics.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nexus.config.settings import settings


@dataclass
class ChatMetrics:
    """Chat Metrics Data Class.

    Data structure for individual request metrics.

    Attrs:
        thread_id: str - Unique thread identifier.
        timestamp: float - Start time of the request.
        request_latency: float - Total request duration in seconds.
        first_token_latency: float | None - Time to first token in seconds.
        input_tokens: int - Number of input tokens.
        output_tokens: int - Number of output tokens.
        total_tokens: int - Total number of tokens.
        cached_tokens: int - Number of cached tokens.
    """

    thread_id: str
    timestamp: float
    request_latency: float
    first_token_latency: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


class MetricsManager:
    """Metrics Manager Class.

    Manages the persistent storage of chat metrics in SQLite.

    Attrs:
        db_path: Path - Path to the metrics database file.

    Methods:
        save_metrics(metrics): Save metrics to the database.
        get_session_summary(thread_id): Get aggregated metrics for a thread.
    """

    def __init__(self) -> None:
        """Initialize Metrics Manager.

        Sets up the database connection and creates the table if it doesn't exist.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """

        self.db_path: Path = settings.nexus_dir / "db" / "metrics.db"
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database table.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    timestamp REAL,
                    request_latency REAL,
                    first_token_latency REAL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    total_tokens INTEGER,
                    cached_tokens INTEGER
                )
                """,
            )

    def save_metrics(self, metrics: ChatMetrics) -> None:
        """Save chat metrics to the database.

        Args:
            metrics: ChatMetrics - Metrics data to save.

        Returns:
            None

        Raises:
            None
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO chat_metrics (
                    thread_id, timestamp, request_latency, first_token_latency,
                    input_tokens, output_tokens, total_tokens, cached_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics.thread_id,
                    metrics.timestamp,
                    metrics.request_latency,
                    metrics.first_token_latency,
                    metrics.input_tokens,
                    metrics.output_tokens,
                    metrics.total_tokens,
                    metrics.cached_tokens,
                ),
            )

    def get_session_summary(self, thread_id: str) -> dict[str, Any]:
        """Get aggregated metrics summary for a specific thread.

        Args:
            thread_id: str - Thread ID to summarize.

        Returns:
            dict[str, Any] - Aggregated metrics summary.

        Raises:
            None
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_requests,
                    SUM(request_latency) as total_latency,
                    AVG(request_latency) as avg_latency,
                    AVG(first_token_latency) as avg_ttft,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cached_tokens) as total_cached_tokens
                FROM chat_metrics
                WHERE thread_id = ?
                """,
                (thread_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}


__all__: list[str] = ["ChatMetrics", "MetricsManager"]
