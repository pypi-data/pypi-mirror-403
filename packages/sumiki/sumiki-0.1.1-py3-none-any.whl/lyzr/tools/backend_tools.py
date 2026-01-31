"""
Typed Backend Tool Classes

Provides type-safe backend tool actions with IDE autocomplete support.
"""

from enum import Enum
from typing import NamedTuple


class ToolSource(str, Enum):
    """Backend tool source types"""
    ACI = "aci"
    COMPOSIO = "composio"
    OPENAPI = "openapi"


class BackendToolAction(NamedTuple):
    """
    Represents a backend tool action with type safety

    Attributes:
        tool_name: Integration/tool name
        action: Specific action name
        source: Tool source (aci, composio, openapi)
    """
    tool_name: str
    action: str
    source: ToolSource

    @property
    def is_backend(self) -> bool:
        """Identifies this as a backend tool"""
        return True


# ============================================================================
# ACI Tools (Enterprise Integrations)
# ============================================================================

class HubSpot:
    """HubSpot CRM integration"""
    CREATE_CONTACT = BackendToolAction("HUBSPOT", "HUBSPOT_CREATE_CONTACT", ToolSource.ACI)
    GET_DEAL = BackendToolAction("HUBSPOT", "HUBSPOT_GET_DEAL", ToolSource.ACI)
    UPDATE_CONTACT = BackendToolAction("HUBSPOT", "HUBSPOT_UPDATE_CONTACT", ToolSource.ACI)
    DELETE_CONTACT = BackendToolAction("HUBSPOT", "HUBSPOT_DELETE_CONTACT", ToolSource.ACI)
    SEARCH_CONTACTS = BackendToolAction("HUBSPOT", "HUBSPOT_SEARCH_CONTACTS", ToolSource.ACI)


class Stripe:
    """Stripe payment processing"""
    CREATE_CUSTOMER = BackendToolAction("STRIPE", "STRIPE_CREATE_CUSTOMER", ToolSource.ACI)
    CREATE_PAYMENT = BackendToolAction("STRIPE", "STRIPE_CREATE_PAYMENT", ToolSource.ACI)
    CREATE_INVOICE = BackendToolAction("STRIPE", "STRIPE_CREATE_INVOICE", ToolSource.ACI)
    GET_CUSTOMER = BackendToolAction("STRIPE", "STRIPE_GET_CUSTOMER", ToolSource.ACI)
    REFUND_PAYMENT = BackendToolAction("STRIPE", "STRIPE_REFUND_PAYMENT", ToolSource.ACI)


class Shopify:
    """Shopify e-commerce platform"""
    CREATE_ORDER = BackendToolAction("SHOPIFY", "SHOPIFY_CREATE_ORDER", ToolSource.ACI)
    GET_PRODUCT = BackendToolAction("SHOPIFY", "SHOPIFY_GET_PRODUCT", ToolSource.ACI)
    UPDATE_INVENTORY = BackendToolAction("SHOPIFY", "SHOPIFY_UPDATE_INVENTORY", ToolSource.ACI)
    CREATE_PRODUCT = BackendToolAction("SHOPIFY", "SHOPIFY_CREATE_PRODUCT", ToolSource.ACI)
    GET_ORDER = BackendToolAction("SHOPIFY", "SHOPIFY_GET_ORDER", ToolSource.ACI)


class Salesforce:
    """Salesforce enterprise CRM"""
    CREATE_LEAD = BackendToolAction("SALESFORCE", "SALESFORCE_CREATE_LEAD", ToolSource.ACI)
    GET_ACCOUNT = BackendToolAction("SALESFORCE", "SALESFORCE_GET_ACCOUNT", ToolSource.ACI)
    UPDATE_OPPORTUNITY = BackendToolAction("SALESFORCE", "SALESFORCE_UPDATE_OPPORTUNITY", ToolSource.ACI)
    CREATE_CONTACT = BackendToolAction("SALESFORCE", "SALESFORCE_CREATE_CONTACT", ToolSource.ACI)
    GET_LEAD = BackendToolAction("SALESFORCE", "SALESFORCE_GET_LEAD", ToolSource.ACI)


class Slack:
    """Slack team communication"""
    SEND_MESSAGE = BackendToolAction("SLACK", "SLACK_SEND_MESSAGE", ToolSource.ACI)
    CREATE_CHANNEL = BackendToolAction("SLACK", "SLACK_CREATE_CHANNEL", ToolSource.ACI)
    POST_FILE = BackendToolAction("SLACK", "SLACK_POST_FILE", ToolSource.ACI)
    GET_CHANNEL = BackendToolAction("SLACK", "SLACK_GET_CHANNEL", ToolSource.ACI)
    INVITE_USER = BackendToolAction("SLACK", "SLACK_INVITE_USER", ToolSource.ACI)


# ============================================================================
# Composio Tools (Standard App Integrations)
# ============================================================================

class Gmail:
    """Gmail email service"""
    SEND_EMAIL = BackendToolAction("gmail", "GMAIL_SEND_EMAIL", ToolSource.COMPOSIO)
    READ_EMAIL = BackendToolAction("gmail", "GMAIL_READ_EMAIL", ToolSource.COMPOSIO)
    SEARCH_EMAIL = BackendToolAction("gmail", "GMAIL_SEARCH_EMAIL", ToolSource.COMPOSIO)
    DELETE_EMAIL = BackendToolAction("gmail", "GMAIL_DELETE_EMAIL", ToolSource.COMPOSIO)
    CREATE_DRAFT = BackendToolAction("gmail", "GMAIL_CREATE_DRAFT", ToolSource.COMPOSIO)


class GitHub:
    """GitHub development platform"""
    CREATE_ISSUE = BackendToolAction("github", "GITHUB_CREATE_ISSUE", ToolSource.COMPOSIO)
    CREATE_PR = BackendToolAction("github", "GITHUB_CREATE_PR", ToolSource.COMPOSIO)
    GET_REPO = BackendToolAction("github", "GITHUB_GET_REPO", ToolSource.COMPOSIO)
    MERGE_PR = BackendToolAction("github", "GITHUB_MERGE_PR", ToolSource.COMPOSIO)
    CREATE_BRANCH = BackendToolAction("github", "GITHUB_CREATE_BRANCH", ToolSource.COMPOSIO)


class GoogleCalendar:
    """Google Calendar service"""
    CREATE_EVENT = BackendToolAction("googlecalendar", "GCAL_CREATE_EVENT", ToolSource.COMPOSIO)
    GET_EVENT = BackendToolAction("googlecalendar", "GCAL_GET_EVENT", ToolSource.COMPOSIO)
    UPDATE_EVENT = BackendToolAction("googlecalendar", "GCAL_UPDATE_EVENT", ToolSource.COMPOSIO)
    DELETE_EVENT = BackendToolAction("googlecalendar", "GCAL_DELETE_EVENT", ToolSource.COMPOSIO)
    LIST_EVENTS = BackendToolAction("googlecalendar", "GCAL_LIST_EVENTS", ToolSource.COMPOSIO)


class GoogleDrive:
    """Google Drive storage service"""
    UPLOAD_FILE = BackendToolAction("googledrive", "GDRIVE_UPLOAD_FILE", ToolSource.COMPOSIO)
    GET_FILE = BackendToolAction("googledrive", "GDRIVE_GET_FILE", ToolSource.COMPOSIO)
    SHARE_FILE = BackendToolAction("googledrive", "GDRIVE_SHARE_FILE", ToolSource.COMPOSIO)
    DELETE_FILE = BackendToolAction("googledrive", "GDRIVE_DELETE_FILE", ToolSource.COMPOSIO)
    CREATE_FOLDER = BackendToolAction("googledrive", "GDRIVE_CREATE_FOLDER", ToolSource.COMPOSIO)


class Notion:
    """Notion productivity workspace"""
    CREATE_PAGE = BackendToolAction("notion", "NOTION_CREATE_PAGE", ToolSource.COMPOSIO)
    GET_PAGE = BackendToolAction("notion", "NOTION_GET_PAGE", ToolSource.COMPOSIO)
    UPDATE_DATABASE = BackendToolAction("notion", "NOTION_UPDATE_DATABASE", ToolSource.COMPOSIO)
    CREATE_DATABASE = BackendToolAction("notion", "NOTION_CREATE_DATABASE", ToolSource.COMPOSIO)
    SEARCH_PAGES = BackendToolAction("notion", "NOTION_SEARCH_PAGES", ToolSource.COMPOSIO)
