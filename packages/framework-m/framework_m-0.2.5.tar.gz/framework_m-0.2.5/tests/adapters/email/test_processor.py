"""Tests for Email Processor.

Tests cover:
- EmailProcessor initialization
- process_queue - fetch and send pending emails
- process_single - send single email by ID
- _fetch_pending - get pending emails from queue
- _send_email - send via EmailSenderProtocol
- _update_status - update email status
- _handle_failure - retry logic
- send_queued_email convenience function
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from framework_m.adapters.email.processor import EmailProcessor, send_queued_email
from framework_m.adapters.email.sender_adapter import LogEmailSender
from framework_m.core.doctypes.email_queue import EmailQueue, EmailStatus

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def email_queue_item() -> EmailQueue:
    """Create a test EmailQueue item."""
    return EmailQueue(
        id=uuid4(),
        to=["user@example.com"],
        subject="Test Email",
        body="<p>Hello</p>",
        status=EmailStatus.QUEUED,
    )


@pytest.fixture
def log_sender() -> LogEmailSender:
    """Create LogEmailSender for testing."""
    return LogEmailSender()


# =============================================================================
# Test: EmailProcessor Initialization
# =============================================================================


class TestEmailProcessorInit:
    """Tests for EmailProcessor initialization."""

    def test_init_with_sender(self, log_sender: LogEmailSender) -> None:
        """Processor should initialize with sender."""
        processor = EmailProcessor(sender=log_sender)

        assert processor.sender is log_sender
        assert processor.batch_size == 50

    def test_init_custom_batch_size(self, log_sender: LogEmailSender) -> None:
        """Processor should accept custom batch size."""
        processor = EmailProcessor(sender=log_sender, batch_size=10)

        assert processor.batch_size == 10

    def test_init_with_repository(self, log_sender: LogEmailSender) -> None:
        """Processor should accept repository."""
        mock_repo = MagicMock()
        processor = EmailProcessor(sender=log_sender, repository=mock_repo)

        assert processor._repository is mock_repo

    def test_init_in_memory_queue(self, log_sender: LogEmailSender) -> None:
        """Processor should have in-memory queue fallback."""
        processor = EmailProcessor(sender=log_sender)

        assert isinstance(processor._in_memory_queue, list)
        assert len(processor._in_memory_queue) == 0


# =============================================================================
# Test: process_queue
# =============================================================================


class TestEmailProcessorProcessQueue:
    """Tests for EmailProcessor.process_queue()."""

    @pytest.mark.asyncio
    async def test_process_queue_empty(self, log_sender: LogEmailSender) -> None:
        """process_queue should return 0 when queue empty."""
        processor = EmailProcessor(sender=log_sender)

        processed = await processor.process_queue()

        assert processed == 0

    @pytest.mark.asyncio
    async def test_process_queue_sender_unavailable(self) -> None:
        """process_queue should skip if sender unavailable."""
        mock_sender = AsyncMock()
        mock_sender.is_available = AsyncMock(return_value=False)

        processor = EmailProcessor(sender=mock_sender)

        processed = await processor.process_queue()

        assert processed == 0

    @pytest.mark.asyncio
    async def test_process_queue_with_in_memory_emails(
        self,
        log_sender: LogEmailSender,
        email_queue_item: EmailQueue,
    ) -> None:
        """process_queue should process in-memory emails."""
        processor = EmailProcessor(sender=log_sender)
        processor._in_memory_queue.append(email_queue_item)

        processed = await processor.process_queue()

        assert processed == 1
        assert len(log_sender.sent_emails) == 1

    @pytest.mark.asyncio
    async def test_process_queue_multiple_emails(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """process_queue should process multiple emails."""
        processor = EmailProcessor(sender=log_sender)

        # Add 3 queued emails
        for i in range(3):
            email = EmailQueue(
                id=uuid4(),
                to=[f"user{i}@example.com"],
                subject=f"Email {i}",
                body=f"<p>Body {i}</p>",
                status=EmailStatus.QUEUED,
            )
            processor._in_memory_queue.append(email)

        processed = await processor.process_queue()

        assert processed == 3
        assert len(log_sender.sent_emails) == 3

    @pytest.mark.asyncio
    async def test_process_queue_handles_errors(self) -> None:
        """process_queue should handle send errors gracefully."""
        mock_sender = AsyncMock()
        mock_sender.is_available = AsyncMock(return_value=True)
        mock_sender.send = AsyncMock(side_effect=Exception("Send failed"))

        processor = EmailProcessor(sender=mock_sender)
        processor._in_memory_queue.append(
            EmailQueue(
                id=uuid4(),
                to=["user@example.com"],
                subject="Test",
                body="<p>Hello</p>",
                status=EmailStatus.QUEUED,
            )
        )

        # Should not raise
        processed = await processor.process_queue()

        # Email was attempted but failed
        assert processed == 0  # Didn't complete successfully


# =============================================================================
# Test: process_single
# =============================================================================


class TestEmailProcessorProcessSingle:
    """Tests for EmailProcessor.process_single()."""

    @pytest.mark.asyncio
    async def test_process_single_not_found(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """process_single should return error if email not found."""
        processor = EmailProcessor(sender=log_sender)

        result = await processor.process_single(str(uuid4()))

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_process_single_success(
        self,
        log_sender: LogEmailSender,
        email_queue_item: EmailQueue,
    ) -> None:
        """process_single should send email and return result."""
        processor = EmailProcessor(sender=log_sender)
        processor._in_memory_queue.append(email_queue_item)

        result = await processor.process_single(str(email_queue_item.id))

        assert result.success is True
        assert len(log_sender.sent_emails) == 1


# =============================================================================
# Test: _fetch_pending
# =============================================================================


class TestEmailProcessorFetchPending:
    """Tests for EmailProcessor._fetch_pending()."""

    @pytest.mark.asyncio
    async def test_fetch_pending_empty(self, log_sender: LogEmailSender) -> None:
        """_fetch_pending should return empty list when no emails."""
        processor = EmailProcessor(sender=log_sender)

        pending = await processor._fetch_pending()

        assert pending == []

    @pytest.mark.asyncio
    async def test_fetch_pending_filters_by_status(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """_fetch_pending should only return QUEUED emails."""
        processor = EmailProcessor(sender=log_sender)

        # Add emails with different statuses
        queued = EmailQueue(
            id=uuid4(), to=["a@b.c"], subject="Q", body="q", status=EmailStatus.QUEUED
        )
        sent = EmailQueue(
            id=uuid4(), to=["a@b.c"], subject="S", body="s", status=EmailStatus.SENT
        )
        failed = EmailQueue(
            id=uuid4(), to=["a@b.c"], subject="F", body="f", status=EmailStatus.FAILED
        )

        processor._in_memory_queue.extend([queued, sent, failed])

        pending = await processor._fetch_pending()

        assert len(pending) == 1
        assert pending[0].status == EmailStatus.QUEUED

    @pytest.mark.asyncio
    async def test_fetch_pending_respects_batch_size(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """_fetch_pending should limit to batch_size."""
        processor = EmailProcessor(sender=log_sender, batch_size=2)

        # Add 5 emails
        for i in range(5):
            processor._in_memory_queue.append(
                EmailQueue(
                    id=uuid4(),
                    to=[f"u{i}@b.c"],
                    subject=f"S{i}",
                    body="b",
                    status=EmailStatus.QUEUED,
                )
            )

        pending = await processor._fetch_pending()

        assert len(pending) == 2


# =============================================================================
# Test: _send_email
# =============================================================================


class TestEmailProcessorSendEmail:
    """Tests for EmailProcessor._send_email()."""

    @pytest.mark.asyncio
    async def test_send_email_converts_to_message(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """_send_email should convert EmailQueue to EmailMessage."""
        processor = EmailProcessor(sender=log_sender)

        email = EmailQueue(
            id=uuid4(),
            to=["user@example.com"],
            subject="Test Subject",
            body="<p>HTML</p>",
            text_body="Plain text",
            from_address="sender@example.com",
            reply_to="reply@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            status=EmailStatus.QUEUED,
        )

        result = await processor._send_email(email)

        assert result.success is True
        sent = log_sender.sent_emails[0]
        assert sent.to == ["user@example.com"]
        assert sent.subject == "Test Subject"
        assert sent.html_body == "<p>HTML</p>"
        assert sent.text_body == "Plain text"


# =============================================================================
# Test: send_queued_email convenience function
# =============================================================================


class TestSendQueuedEmail:
    """Tests for send_queued_email convenience function."""

    @pytest.mark.asyncio
    async def test_send_queued_email_not_found(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """send_queued_email should return error if not found."""
        result = await send_queued_email(
            queue_id=str(uuid4()),
            sender=log_sender,
        )

        assert result.success is False


# =============================================================================
# Test: Processor with Repository
# =============================================================================


class TestEmailProcessorWithRepository:
    """Tests for EmailProcessor with repository."""

    @pytest.mark.asyncio
    async def test_fetch_pending_with_repository(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """_fetch_pending should query repository when provided."""
        mock_repo = AsyncMock()
        mock_repo.list = AsyncMock(
            return_value=MagicMock(
                items=[
                    EmailQueue(
                        id=uuid4(),
                        to=["a@b.c"],
                        subject="T",
                        body="b",
                        status=EmailStatus.QUEUED,
                    )
                ]
            )
        )

        processor = EmailProcessor(sender=log_sender, repository=mock_repo)

        pending = await processor._fetch_pending()

        assert len(pending) == 1
        mock_repo.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_email_with_repository(
        self,
        log_sender: LogEmailSender,
    ) -> None:
        """_get_email should query repository when provided."""
        email_id = uuid4()
        mock_repo = AsyncMock()
        mock_repo.get = AsyncMock(
            return_value=EmailQueue(
                id=email_id,
                to=["a@b.c"],
                subject="T",
                body="b",
                status=EmailStatus.QUEUED,
            )
        )

        processor = EmailProcessor(sender=log_sender, repository=mock_repo)

        email = await processor._get_email(str(email_id))

        assert email is not None
        assert email.id == email_id
