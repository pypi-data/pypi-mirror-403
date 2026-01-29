from importlib.metadata import version

HTML_MIME_TYPE = "text/html"
MARKDOWN_MIME_TYPE = "text/markdown"
TEXT_MIME_TYPE = "text/plain"
WEBP_MIME_TYPE = "image/webp"

_MAJOR_VERSION = version("atoti-client").split(".", maxsplit=1)[0]

LINK_MIME_TYPE = f"application/vnd.atoti.link.v{_MAJOR_VERSION}+json"
WIDGET_MIME_TYPE = f"application/vnd.atoti.widget.v{_MAJOR_VERSION}+json"

GRAPHQL_RESPONSE_MIME_TYPE = "application/graphql-response+json"
"""See https://graphql.org/learn/serving-over-http/#headers."""
