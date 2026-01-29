"""Framework M Core DocTypes."""

from framework_m.core.doctypes.activity_log import ActivityLog
from framework_m.core.doctypes.api_key import ApiKey
from framework_m.core.doctypes.custom_permission import CustomPermission
from framework_m.core.doctypes.document_share import DocumentShare, ShareType
from framework_m.core.doctypes.email_queue import EmailQueue
from framework_m.core.doctypes.error_log import ErrorLog
from framework_m.core.doctypes.file import File
from framework_m.core.doctypes.job_log import JobLog
from framework_m.core.doctypes.notification import Notification, NotificationType
from framework_m.core.doctypes.print_format import PrintFormat
from framework_m.core.doctypes.recent_document import RecentDocument
from framework_m.core.doctypes.scheduled_job import ScheduledJob
from framework_m.core.doctypes.session import Session
from framework_m.core.doctypes.social_account import SocialAccount
from framework_m.core.doctypes.system_settings import SystemSettings
from framework_m.core.doctypes.tenant_translation import TenantTranslation
from framework_m.core.doctypes.todo import Todo
from framework_m.core.doctypes.translation import Translation
from framework_m.core.doctypes.user import LocalUser
from framework_m.core.doctypes.webhook import Webhook
from framework_m.core.doctypes.webhook_log import WebhookLog

__all__ = [
    "ActivityLog",
    "ApiKey",
    "CustomPermission",
    "DocumentShare",
    "EmailQueue",
    "ErrorLog",
    "File",
    "JobLog",
    "LocalUser",
    "Notification",
    "NotificationType",
    "PrintFormat",
    "RecentDocument",
    "ScheduledJob",
    "Session",
    "ShareType",
    "SocialAccount",
    "SystemSettings",
    "TenantTranslation",
    "Todo",
    "Translation",
    "Webhook",
    "WebhookLog",
]
