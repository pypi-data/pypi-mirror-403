#!/usr/bin/env python3
"""
CDL Language Server - Main server implementation.

This module implements the Language Server Protocol for the Crystal
Description Language (CDL), providing features like diagnostics,
completion, hover, and go-to-definition.
"""

import argparse
import logging
import sys

# Configure logging
logging.basicConfig(
    filename="/tmp/cdl-lsp.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("cdl-lsp")

try:
    from lsprotocol import types
    from pygls.lsp.server import LanguageServer

    PYGLS_AVAILABLE = True
except ImportError:
    logger.warning("pygls not installed. Install with: pip install pygls lsprotocol")
    PYGLS_AVAILABLE = False

from .features.code_actions import get_code_actions
from .features.completion import get_completions
from .features.definition import get_definition
from .features.diagnostics import get_diagnostics
from .features.document_symbols import get_document_symbols
from .features.explain import get_explain_result
from .features.formatting import format_cdl
from .features.hover import get_hover_info
from .features.preview import get_preview_capabilities, render_cdl_preview, render_cdl_preview_3d
from .features.signature_help import get_signature_help

# Server metadata
SERVER_NAME = "cdl-language-server"
SERVER_VERSION = "1.0.0"


def create_server() -> "LanguageServer":
    """Create and configure the LSP server."""
    if not PYGLS_AVAILABLE:
        raise ImportError(
            "pygls is required for the LSP server. Install with: pip install pygls lsprotocol"
        )

    server = LanguageServer(name=SERVER_NAME, version=SERVER_VERSION)

    # Document storage
    documents: dict = {}

    # ==========================================================================
    # Lifecycle Events
    # ==========================================================================

    @server.feature(types.INITIALIZE)
    def initialize(params: types.InitializeParams) -> types.InitializeResult:
        """Handle initialization request."""
        logger.info(f"Initializing CDL Language Server {SERVER_VERSION}")
        logger.info(f"Root URI: {params.root_uri}")

        return types.InitializeResult(
            capabilities=types.ServerCapabilities(
                text_document_sync=types.TextDocumentSyncOptions(
                    open_close=True,
                    change=types.TextDocumentSyncKind.Full,
                    save=types.SaveOptions(include_text=True),
                ),
                completion_provider=types.CompletionOptions(
                    trigger_characters=["{", "[", ":", "@", "+", "|", "(", ","],
                    resolve_provider=False,
                ),
                hover_provider=types.HoverOptions(),
                definition_provider=types.DefinitionOptions(),
                diagnostic_provider=types.DiagnosticOptions(
                    inter_file_dependencies=False, workspace_diagnostics=False
                ),
                # New capabilities
                signature_help_provider=types.SignatureHelpOptions(trigger_characters=["(", ","]),
                code_action_provider=types.CodeActionOptions(
                    code_action_kinds=[types.CodeActionKind.QuickFix]
                ),
                document_symbol_provider=True,
                document_formatting_provider=True,
                # Note: execute_command_provider is auto-populated by @server.command() decorators
            ),
            server_info=types.ServerInfo(name=SERVER_NAME, version=SERVER_VERSION),
        )

    @server.feature(types.INITIALIZED)
    def initialized(params: types.InitializedParams) -> None:
        """Handle initialized notification."""
        logger.info("CDL Language Server initialized")

    @server.feature(types.SHUTDOWN)
    def shutdown(params: None) -> None:
        """Handle shutdown request."""
        logger.info("CDL Language Server shutting down")

    # ==========================================================================
    # Document Synchronization
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: types.DidOpenTextDocumentParams) -> None:
        """Handle document open notification."""
        uri = params.text_document.uri
        text = params.text_document.text

        logger.debug(f"Document opened: {uri}")
        documents[uri] = text

        # Publish diagnostics
        diagnostics = get_diagnostics(text)
        server.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
        )

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: types.DidChangeTextDocumentParams) -> None:
        """Handle document change notification."""
        uri = params.text_document.uri

        # Full sync - get the complete new content
        for change in params.content_changes:
            if hasattr(change, "text"):
                documents[uri] = change.text
                break

        text = documents.get(uri, "")
        logger.debug(f"Document changed: {uri}, length: {len(text)}")

        # Publish diagnostics
        diagnostics = get_diagnostics(text)
        server.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
        )

    @server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
    def did_close(params: types.DidCloseTextDocumentParams) -> None:
        """Handle document close notification."""
        uri = params.text_document.uri
        logger.debug(f"Document closed: {uri}")

        if uri in documents:
            del documents[uri]

        # Clear diagnostics
        server.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=uri, diagnostics=[])
        )

    @server.feature(types.TEXT_DOCUMENT_DID_SAVE)
    def did_save(params: types.DidSaveTextDocumentParams) -> None:
        """Handle document save notification."""
        uri = params.text_document.uri
        text = params.text if params.text else documents.get(uri, "")

        logger.debug(f"Document saved: {uri}")

        if text:
            documents[uri] = text
            diagnostics = get_diagnostics(text)
            server.text_document_publish_diagnostics(
                types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
            )

    # ==========================================================================
    # Completion
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_COMPLETION)
    def completion(params: types.CompletionParams) -> types.CompletionList | None:
        """Handle completion request."""
        uri = params.text_document.uri
        position = params.position

        text = documents.get(uri, "")
        if not text:
            return None

        # Get the current line
        lines = text.split("\n")
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        col = position.character

        logger.debug(f"Completion at {uri}:{position.line}:{col}")

        trigger_char = None
        if params.context and params.context.trigger_character:
            trigger_char = params.context.trigger_character

        items = get_completions(line, col, trigger_char)

        return types.CompletionList(is_incomplete=False, items=items)

    # ==========================================================================
    # Hover
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_HOVER)
    def hover(params: types.HoverParams) -> types.Hover | None:
        """Handle hover request."""
        uri = params.text_document.uri
        position = params.position

        text = documents.get(uri, "")
        if not text:
            return None

        lines = text.split("\n")
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        col = position.character

        logger.debug(f"Hover at {uri}:{position.line}:{col}")

        return get_hover_info(line, col, position.line)

    # ==========================================================================
    # Go to Definition
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_DEFINITION)
    def definition(params: types.DefinitionParams) -> types.Location | None:
        """Handle go to definition request."""
        uri = params.text_document.uri
        position = params.position

        text = documents.get(uri, "")
        if not text:
            return None

        lines = text.split("\n")
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        col = position.character

        logger.debug(f"Definition at {uri}:{position.line}:{col}")

        return get_definition(line, col, position.line, uri)

    # ==========================================================================
    # Diagnostics (Pull Model)
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_DIAGNOSTIC)
    def diagnostic(params: types.DocumentDiagnosticParams) -> types.DocumentDiagnosticReport:
        """Handle diagnostic request (pull model)."""
        uri = params.text_document.uri
        text = documents.get(uri, "")

        logger.debug(f"Diagnostic request for {uri}")

        if not text:
            return types.RelatedFullDocumentDiagnosticReport(
                kind=types.DocumentDiagnosticReportKind.Full, items=[]
            )

        diagnostics = get_diagnostics(text)

        return types.RelatedFullDocumentDiagnosticReport(
            kind=types.DocumentDiagnosticReportKind.Full, items=diagnostics
        )

    # ==========================================================================
    # Code Actions
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_CODE_ACTION)
    def code_action(params: types.CodeActionParams) -> list[types.CodeAction] | None:
        """Handle code action request."""
        uri = params.text_document.uri
        diagnostics = params.context.diagnostics

        logger.debug(f"Code action at {uri}")

        if not diagnostics:
            return None

        actions = get_code_actions(uri, params.range, diagnostics)
        return actions if actions else None

    # ==========================================================================
    # Signature Help
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_SIGNATURE_HELP)
    def signature_help(params: types.SignatureHelpParams) -> types.SignatureHelp | None:
        """Handle signature help request."""
        uri = params.text_document.uri
        position = params.position

        text = documents.get(uri, "")
        if not text:
            return None

        lines = text.split("\n")
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        col = position.character

        logger.debug(f"Signature help at {uri}:{position.line}:{col}")

        return get_signature_help(line, col)

    # ==========================================================================
    # Document Symbols
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbol(params: types.DocumentSymbolParams) -> list[types.DocumentSymbol]:
        """Handle document symbol request."""
        uri = params.text_document.uri
        text = documents.get(uri, "")

        logger.debug(f"Document symbols for {uri}")

        if not text:
            return []

        return get_document_symbols(text)

    # ==========================================================================
    # Formatting
    # ==========================================================================

    @server.feature(types.TEXT_DOCUMENT_FORMATTING)
    def formatting(params: types.DocumentFormattingParams) -> list[types.TextEdit]:
        """Handle document formatting request."""
        uri = params.text_document.uri
        text = documents.get(uri, "")

        logger.debug(f"Formatting {uri}")

        if not text:
            return []

        return format_cdl(text, params.options)

    # ==========================================================================
    # Execute Commands (Explain, Preview)
    # ==========================================================================

    @server.command("cdl.explain")
    def cmd_explain(ls, *args) -> dict:
        """Execute cdl.explain command."""
        logger.debug(f"cdl.explain command, args: {args}")

        if args:
            uri = args[0]
            text = documents.get(uri, "")
            if text:
                return get_explain_result(text)
            else:
                return {"content": "Document not found or empty", "kind": "markdown"}
        return {"content": "No document URI provided", "kind": "markdown"}

    @server.command("cdl.preview")
    def cmd_preview(ls, *args) -> dict:
        """Execute cdl.preview command."""
        logger.debug(f"cdl.preview command, args: {args}")

        if args:
            uri = args[0]
            width = args[1] if len(args) > 1 else 600
            height = args[2] if len(args) > 2 else 500
            text = documents.get(uri, "")
            if text:
                return render_cdl_preview(text, width, height)
            else:
                return {"success": False, "error": "Document not found or empty", "svg": ""}
        return {"success": False, "error": "No document URI provided", "svg": ""}

    @server.command("cdl.preview3d")
    def cmd_preview_3d(ls, *args) -> dict:
        """Execute cdl.preview3d command - returns glTF for 3D preview."""
        logger.debug(f"cdl.preview3d command, args: {args}")

        if args:
            uri = args[0]
            text = documents.get(uri, "")
            if text:
                return render_cdl_preview_3d(text)
            else:
                return {"success": False, "error": "Document not found or empty", "gltf": None}
        return {"success": False, "error": "No document URI provided", "gltf": None}

    @server.command("cdl.previewCapabilities")
    def cmd_preview_capabilities(ls, *args) -> dict:
        """Execute cdl.previewCapabilities command."""
        logger.debug("cdl.previewCapabilities command")
        return get_preview_capabilities()

    return server


def main():
    """Main entry point for the CDL Language Server."""
    parser = argparse.ArgumentParser(
        description="CDL Language Server Protocol implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m lsp                    # Start server with stdio transport
  python -m lsp --tcp --port 2087  # Start server with TCP transport
        """,
    )

    parser.add_argument("--stdio", action="store_true", help="Use stdio transport (default)")
    parser.add_argument("--tcp", action="store_true", help="Use TCP transport instead of stdio")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to for TCP transport (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=2087, help="Port to bind to for TCP transport (default: 2087)"
    )
    parser.add_argument(
        "--version", action="version", version=f"CDL Language Server {SERVER_VERSION}"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging to stderr")

    args = parser.parse_args()

    if args.debug:
        # Also log to stderr
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

    if not PYGLS_AVAILABLE:
        print(
            "Error: pygls is required. Install with: pip install pygls lsprotocol", file=sys.stderr
        )
        sys.exit(1)

    server = create_server()

    logger.info(f"Starting CDL Language Server {SERVER_VERSION}")

    if args.tcp:
        logger.info(f"Using TCP transport on {args.host}:{args.port}")
        server.start_tcp(args.host, args.port)
    else:
        logger.info("Using stdio transport")
        server.start_io()


if __name__ == "__main__":
    main()
