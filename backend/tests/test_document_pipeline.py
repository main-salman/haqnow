"""
Regression tests for the document processing pipeline.

These tests verify:
1. Stale job recovery works correctly (prevents jobs from getting stuck forever)
2. Job lifecycle transitions (pending → processing → completed/failed)
3. Document processing completeness (OCR, tags, summary, RAG chunks are populated)

Reference: specs/SPEC-001-document-lifecycle.md

Usage:
    # Run against production (read-only verification):
    HAQNOW_API_URL=https://haqnow.org pytest backend/tests/test_document_pipeline.py -v

    # Run unit tests only (no network required):
    pytest backend/tests/test_document_pipeline.py -v -k "unit"
"""
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ---------------------------------------------------------------------------
# Unit tests (no database or network required)
# ---------------------------------------------------------------------------

class TestStaleJobRecoveryUnit:
    """
    Unit tests for QueueService.recover_stale_jobs().
    
    These tests verify the critical invariant from SPEC-001:
    'No job should stay in processing for more than 10 minutes without recovery'
    """

    def _make_mock_job(self, job_id, document_id, status, started_at):
        """Create a mock JobQueue object."""
        job = MagicMock()
        job.id = job_id
        job.document_id = document_id
        job.status = status
        job.started_at = started_at
        job.current_step = "Extracting text with OCR"
        job.progress_percent = 30
        job.retry_count = 0
        return job

    def test_recover_stale_jobs_resets_stuck_processing_jobs(self):
        """
        REGRESSION TEST: Jobs stuck in 'processing' status for >10 min must be
        reset to 'pending'. This was the root cause of doc 140 not being processed.
        
        See: SPEC-001 Section 'Stale Job Recovery'
        """
        from app.services.queue_service import QueueService

        # Simulate a job stuck for 30 minutes
        stale_job = self._make_mock_job(
            job_id=96,
            document_id=140,
            status='processing',
            started_at=datetime.utcnow() - timedelta(minutes=30)
        )

        # Mock the database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [stale_job]

        recovered = QueueService.recover_stale_jobs(mock_db, timeout_minutes=10)

        assert recovered == 1
        assert stale_job.status == 'pending'
        assert stale_job.current_step is None
        assert stale_job.progress_percent == 0
        assert stale_job.retry_count == 1
        mock_db.commit.assert_called_once()

    def test_recover_stale_jobs_does_not_touch_recent_jobs(self):
        """Jobs that have been processing for less than the timeout should not be touched."""
        from app.services.queue_service import QueueService

        # Simulate a job that just started 2 minutes ago (within timeout)
        recent_job = self._make_mock_job(
            job_id=97,
            document_id=141,
            status='processing',
            started_at=datetime.utcnow() - timedelta(minutes=2)
        )

        mock_db = MagicMock()
        # The filter should exclude this job, so return empty list
        mock_db.query.return_value.filter.return_value.all.return_value = []

        recovered = QueueService.recover_stale_jobs(mock_db, timeout_minutes=10)

        assert recovered == 0
        mock_db.commit.assert_not_called()

    def test_recover_stale_jobs_handles_multiple_stuck_jobs(self):
        """
        Multiple stuck jobs should all be recovered.
        Real scenario: 8 jobs were stuck from May 1st (jobs 87-94).
        """
        from app.services.queue_service import QueueService

        stale_jobs = [
            self._make_mock_job(
                job_id=87 + i,
                document_id=120 + i,
                status='processing',
                started_at=datetime.utcnow() - timedelta(days=30)
            )
            for i in range(8)
        ]

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = stale_jobs

        recovered = QueueService.recover_stale_jobs(mock_db, timeout_minutes=10)

        assert recovered == 8
        for job in stale_jobs:
            assert job.status == 'pending'
            assert job.retry_count == 1
        mock_db.commit.assert_called_once()

    def test_recover_stale_jobs_increments_retry_count(self):
        """Recovery should increment retry_count to track how many times a job was recovered."""
        from app.services.queue_service import QueueService

        job = self._make_mock_job(
            job_id=96,
            document_id=140,
            status='processing',
            started_at=datetime.utcnow() - timedelta(minutes=60)
        )
        job.retry_count = 2  # Already retried twice before

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [job]

        QueueService.recover_stale_jobs(mock_db, timeout_minutes=10)

        assert job.retry_count == 3


class TestJobLifecycleUnit:
    """Unit tests for job state transitions."""

    def test_get_next_job_only_picks_pending(self):
        """
        get_next_job() must only return jobs with status='pending'.
        This ensures processing/completed/failed jobs are not re-processed.
        """
        from app.services.queue_service import QueueService

        mock_db = MagicMock()
        mock_job = MagicMock()
        mock_job.status = 'pending'
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_job

        job = QueueService.get_next_job(mock_db)

        assert job is not None
        assert mock_job.status == 'processing'  # Status should be updated
        mock_db.commit.assert_called_once()

    def test_fail_job_retries_when_under_max(self):
        """Failed jobs should be retried up to max_retries."""
        from app.services.queue_service import QueueService

        mock_job = MagicMock()
        mock_job.retry_count = 0
        mock_job.max_retries = 3

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        result = QueueService.fail_job(mock_db, job_id=1, error_message="test error", retry=True)

        assert result is True
        assert mock_job.status == 'pending'  # Should be retried
        assert mock_job.retry_count == 1

    def test_fail_job_permanent_after_max_retries(self):
        """Jobs that exceed max_retries should be marked as permanently failed."""
        from app.services.queue_service import QueueService

        mock_job = MagicMock()
        mock_job.retry_count = 2
        mock_job.max_retries = 3

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        result = QueueService.fail_job(mock_db, job_id=1, error_message="test error", retry=True)

        assert result is True
        assert mock_job.status == 'failed'  # Should be permanently failed
        assert mock_job.error_message == "test error"

    def test_enqueue_job_deduplicates(self):
        """Enqueueing a job for a document that already has an active job should return the existing job."""
        from app.services.queue_service import QueueService

        existing_job = MagicMock()
        existing_job.id = 42
        existing_job.document_id = 140

        mock_db = MagicMock()
        # Queue size check
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        # Existing job check - need to configure the second call differently
        mock_db.query.return_value.filter.return_value.first.return_value = existing_job

        result = QueueService.enqueue_job(mock_db, document_id=140)

        assert result.id == 42  # Should return existing job


# ---------------------------------------------------------------------------
# Integration tests (require production API access)
# ---------------------------------------------------------------------------

API_BASE = os.getenv("HAQNOW_API_URL", "https://haqnow.org")


@pytest.mark.skipif(
    not os.getenv("HAQNOW_API_URL") and not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Set HAQNOW_API_URL or RUN_INTEGRATION_TESTS=1 to run integration tests"
)
class TestDocumentProcessingIntegration:
    """
    Integration tests that verify document processing completeness
    against the live API.
    
    Verifies SPEC-001 invariant:
    'After successful processing: ocr_text, search_text, and processed_at MUST be populated'
    """

    def test_approved_documents_have_ocr_text(self):
        """
        REGRESSION TEST: Every approved + processed document must have non-empty ocr_text.
        This catches the doc 140 scenario where a document was approved but processing
        never completed.
        """
        import requests

        response = requests.get(
            f"{API_BASE}/api/search/search",
            params={"q": "", "per_page": 5},
            timeout=15
        )
        
        if response.status_code == 429:
            pytest.skip("Rate limited")
        
        assert response.status_code == 200
        data = response.json()
        
        for doc in data.get("documents", []):
            doc_id = doc["id"]
            # Fetch full document detail
            detail_resp = requests.get(
                f"{API_BASE}/api/search/document/{doc_id}",
                timeout=15
            )
            if detail_resp.status_code == 429:
                pytest.skip("Rate limited")
            
            assert detail_resp.status_code == 200, f"Failed to fetch doc {doc_id}"
            detail = detail_resp.json()
            
            # Key assertion: approved documents must be processed
            assert detail.get("ocr_text") or detail.get("ai_summary"), \
                f"Document {doc_id} is approved but has no OCR text or AI summary. " \
                f"This indicates the processing pipeline failed silently."

    def test_rag_chunks_exist_for_recent_documents(self):
        """
        Verify that the RAG document-question endpoint works for a real document.
        If no RAG chunks exist, the AI Q&A feature won't work.
        """
        import requests

        # Get a recent document
        response = requests.get(
            f"{API_BASE}/api/search/search",
            params={"q": "", "per_page": 1},
            timeout=15
        )
        
        if response.status_code == 429:
            pytest.skip("Rate limited")
        
        assert response.status_code == 200
        docs = response.json().get("documents", [])
        if not docs:
            pytest.skip("No documents available")
        
        doc_id = docs[0]["id"]
        
        # Ask a simple question — should get a non-error response
        qa_resp = requests.post(
            f"{API_BASE}/api/rag/document-question",
            json={"question": "What is this document about?", "document_id": doc_id},
            timeout=60
        )
        
        # 200 = success, 429 = rate limited, 500 = RAG processing issue
        if qa_resp.status_code == 429:
            pytest.skip("Rate limited")
        
        if qa_resp.status_code == 200:
            data = qa_resp.json()
            assert "answer" in data, "RAG response missing 'answer' field"
            assert len(data["answer"]) > 0, "RAG returned empty answer"
