#!/usr/bin/env python3
"""
AI Accounting CLI Chat Tool

Interactive command-line chat interface for the Accounting OS.

Usage:
    # First time: Login with OTP (sent to your email)
    python cli/chat.py

    # Future sessions: Auto-login with saved credentials
    python cli/chat.py

    # Force new OTP login
    python cli/chat.py --login

    # Clear saved credentials
    python cli/chat.py --logout

    # Local development
    python cli/chat.py --api-url http://localhost:8000

    # Legacy: Use JWT token directly
    export ACCOUNTING_API_TOKEN="your_jwt_token"
    python cli/chat.py

Features:
- OTP email authentication (no password needed!)
- Automatic credential storage and refresh
- Natural language financial queries
- Session persistence across conversations
- File attachments (CSV, Excel, images, PDFs)
- Markdown formatting
- Command history
"""

import sys
import os
import requests
import json
import uuid
import base64
import mimetypes
import re
import readline  # For command history and arrow key navigation
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import argparse
import getpass

# Try to import rich for better markdown rendering
try:
    from rich.console import Console
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Try to import sseclient for real-time progress (SSE)
try:
    import sseclient
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False


class AccountingChatCLI:
    """CLI chat interface for Accounting OS."""

    CREDENTIALS_DIR = Path.home() / ".accounting_cli"
    CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"

    def __init__(self, api_url: str, auth_token: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.auth_token = auth_token
        self.session_id = f"cli-session-{uuid.uuid4()}"
        self.user_email = None
        self.token_expires_at = None

        # Create headers if token provided
        if auth_token:
            self.headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
        else:
            self.headers = {"Content-Type": "application/json"}

    @classmethod
    def load_credentials(cls) -> Optional[Dict[str, Any]]:
        """Load stored credentials from disk (does not check expiration - let auto-refresh handle it)."""
        try:
            if cls.CREDENTIALS_FILE.exists():
                with open(cls.CREDENTIALS_FILE, 'r') as f:
                    creds = json.load(f)
                return creds
        except Exception as e:
            print(f"⚠️  Could not load credentials: {str(e)}")
            return None

        return None

    @classmethod
    def save_credentials(cls, access_token: str, expires_in: int, user_email: str):
        """Save credentials to disk."""
        try:
            # Create credentials directory if it doesn't exist
            cls.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

            # Calculate expiry time
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            creds = {
                "access_token": access_token,
                "expires_at": expires_at.isoformat(),
                "user_email": user_email
            }

            # Save to file
            with open(cls.CREDENTIALS_FILE, 'w') as f:
                json.dump(creds, f, indent=2)

            # Set file permissions (user read/write only)
            os.chmod(cls.CREDENTIALS_FILE, 0o600)

            print(f"✅ Credentials saved for {user_email}")

        except Exception as e:
            print(f"⚠️  Could not save credentials: {str(e)}")

    @classmethod
    def clear_credentials(cls):
        """Clear stored credentials."""
        try:
            if cls.CREDENTIALS_FILE.exists():
                cls.CREDENTIALS_FILE.unlink()
                print("✅ Credentials cleared")
        except Exception as e:
            print(f"⚠️  Could not clear credentials: {str(e)}")

    def login_with_otp(self) -> bool:
        """
        Authenticate user with OTP.

        Returns:
            True if authentication successful, False otherwise
        """
        print("\n" + "=" * 60)
        print("OTP Authentication")
        print("=" * 60)

        # Get email
        email = input("\nEmail: ").strip()
        if not email:
            print("❌ Email is required")
            return False

        # Request OTP
        print(f"\n📧 Sending OTP to {email}...")
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/auth/otp/request",
                json={"identifier": email, "method": "email"},
                timeout=10
            )

            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                print(f"❌ Failed to send OTP: {error_msg}")
                return False

            result = response.json()
            expires_in = result.get("expires_in", 300)
            print(f"✅ {result.get('message', 'OTP sent successfully')}")
            print(f"⏱️  OTP expires in {expires_in // 60} minutes\n")

        except Exception as e:
            print(f"❌ Error sending OTP: {str(e)}")
            return False

        # Get OTP from user
        otp_code = getpass.getpass("Enter OTP code: ").strip()
        if not otp_code:
            print("❌ OTP code is required")
            return False

        # Verify OTP
        print("\n🔐 Verifying OTP...")
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/auth/otp/verify",
                json={"identifier": email, "otp": otp_code},
                timeout=10
            )

            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Invalid OTP")
                print(f"❌ {error_msg}")
                return False

            result = response.json()
            access_token = result.get("access_token")
            expires_in = result.get("expires_in")
            user = result.get("user", {})

            if not access_token:
                print("❌ No access token received")
                return False

            # Set token
            self.auth_token = access_token
            self.user_email = email
            self.headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # Set expiration time
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            print(f"✅ Authentication successful!")
            print(f"👤 Logged in as: {user.get('full_name', email)}")

            # Ask to save credentials
            save = input("\n💾 Save credentials for future sessions? (y/n): ").strip().lower()
            if save == 'y':
                self.save_credentials(access_token, expires_in, email)

            return True

        except Exception as e:
            print(f"❌ Error verifying OTP: {str(e)}")
            return False

    def refresh_token(self) -> bool:
        """
        Refresh access token.

        Returns:
            True if refresh successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/auth/refresh-token",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                access_token = result.get("access_token")
                expires_in = result.get("expires_in")

                self.auth_token = access_token
                self.headers["Authorization"] = f"Bearer {access_token}"

                # Update expiration time
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                if self.user_email:
                    self.save_credentials(access_token, expires_in, self.user_email)

                return True
            else:
                # Show error details for debugging
                try:
                    error_data = response.json()
                    print(f"⚠️  Refresh failed: {error_data.get('error', {}).get('message', response.text)}")
                except:
                    print(f"⚠️  Refresh failed with status {response.status_code}")
                return False

        except Exception as e:
            print(f"⚠️  Refresh error: {str(e)}")
            return False

    def is_token_expired(self) -> bool:
        """Check if the current token is expired or about to expire."""
        if not self.token_expires_at:
            return False  # Unknown expiration, assume valid

        # Refresh if token expires within 5 minutes (proactive refresh)
        # This ensures we refresh before the token actually expires,
        # since the refresh endpoint requires a valid token
        buffer = timedelta(minutes=5)
        return datetime.utcnow() + buffer >= self.token_expires_at

    def ensure_valid_token(self) -> bool:
        """
        Ensure we have a valid token, refreshing or re-authenticating if necessary.

        Returns:
            True if we have a valid token, False if authentication failed
        """
        if not self.auth_token:
            return False

        if self.is_token_expired():
            # Check if token is already fully expired (can't be refreshed)
            if self.token_expires_at and datetime.utcnow() >= self.token_expires_at:
                print("\n❌ Token has expired.")
                print("🔐 Automatic re-authentication required...\n")

                # Attempt automatic re-login
                if self.login_with_otp():
                    print("✅ Re-authenticated successfully!\n")
                    return True
                else:
                    print("\n❌ Re-authentication failed.")
                    return False

            # Token is about to expire, try to refresh
            print("🔄 Token expiring soon, refreshing...")
            if self.refresh_token():
                print("✅ Token refreshed successfully")
                return True
            else:
                # Refresh failed, try re-login
                print("⚠️  Token refresh failed. Attempting re-authentication...\n")
                if self.login_with_otp():
                    print("✅ Re-authenticated successfully!\n")
                    return True
                else:
                    print("\n❌ Re-authentication failed.")
                    return False

        return True

    def make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with automatic token refresh on 401.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            Exception if request fails after retry
        """
        # First attempt
        response = requests.request(method, url, **kwargs)

        # If 401 Unauthorized, try to refresh token and retry
        if response.status_code == 401 and self.user_email:
            print("🔄 Authentication expired, refreshing token...")
            if self.refresh_token():
                print("✅ Token refreshed, retrying request...")
                # Update Authorization header and retry
                if "headers" in kwargs:
                    kwargs["headers"]["Authorization"] = f"Bearer {self.auth_token}"
                else:
                    kwargs["headers"] = {"Authorization": f"Bearer {self.auth_token}"}
                response = requests.request(method, url, **kwargs)
            else:
                print("❌ Token refresh failed")

        return response

    def parse_file_mentions(self, message: str, working_dir: str = ".") -> tuple[str, List[str]]:
        """
        Parse file mentions in message and return cleaned message + file paths.

        Supports:
        - @filename syntax: @transactions.csv
        - Absolute paths in quotes: '/path/to/file.xlsx'
        - Absolute paths without quotes: /path/to/file.csv
        - Paths with spaces (quoted): @"/path with spaces/file.csv"
        - Paths with ~: @~/Documents/report.pdf

        Examples:
            "import @transactions.csv" → ("import transactions.csv", ["./transactions.csv"])
            "import '/Users/path/data.xlsx'" → ("import data.xlsx", ["/Users/path/data.xlsx"])
            "analyze @~/data.xlsx and @report.pdf" → ("analyze data.xlsx and report.pdf", ["/Users/name/data.xlsx", "./report.pdf"])

        Args:
            message: User message that may contain file mentions
            working_dir: Directory to search for files (default: current directory)

        Returns:
            Tuple of (cleaned_message, list_of_file_paths)
        """
        import re

        # Pattern 1: @filename (supports spaces if quoted: @"my file.csv")
        # Pattern 2: '/absolute/path' or "/absolute/path"
        # Pattern 3: /absolute/path (without quotes, but must look like a path)
        pattern = r'@(?:"([^"]+)"|(\S+))|[\'"]([/~][^\'"]+)[\'"]|(?:^|\s)(/[^\s]+\.[\w]+)(?:\s|$)'

        file_paths = []

        def replace_mention(match):
            # Get filename from any of the capture groups
            # Group 1: @"quoted path", Group 2: @unquoted, Group 3: 'quoted' or "quoted", Group 4: /absolute/path
            filepath_str = match.group(1) or match.group(2) or match.group(3) or match.group(4)

            if not filepath_str:
                return match.group(0)

            # Expand ~ to home directory
            filepath_str = os.path.expanduser(filepath_str)

            # Check if it's an absolute path or relative path
            if os.path.isabs(filepath_str):
                # Absolute path
                file_path = Path(filepath_str)
            else:
                # Relative path - check in working directory
                file_path = Path(working_dir) / filepath_str

            # Normalize path
            file_path = file_path.resolve()

            if file_path.exists() and file_path.is_file():
                file_paths.append(str(file_path))
                # Replace filepath with just filename in message
                return file_path.name
            else:
                # File doesn't exist - leave mention as-is and warn
                print(f"⚠️  File not found: {filepath_str}")
                return match.group(0)  # Keep original mention

        # Replace all @filename mentions
        cleaned_message = re.sub(pattern, replace_mention, message)

        return cleaned_message, file_paths

    def list_available_files(self, working_dir: str = ".", pattern: str = "*") -> List[str]:
        """
        List files in working directory that match pattern.

        Args:
            working_dir: Directory to search (default: current directory)
            pattern: Glob pattern for files (default: all files)

        Returns:
            List of filenames (not full paths)
        """
        try:
            dir_path = Path(working_dir)
            files = [f.name for f in dir_path.glob(pattern) if f.is_file()]
            return sorted(files)
        except Exception as e:
            print(f"⚠️  Error listing files: {str(e)}")
            return []

    def upload_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Upload a local file and return file metadata."""
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                print(f"❌ File not found: {file_path}")
                return None

            if not file_path_obj.is_file():
                print(f"❌ Not a file: {file_path}")
                return None

            # Get file info
            file_size = file_path_obj.stat().st_size
            filename = file_path_obj.name

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path_obj))
            if not mime_type:
                mime_type = "application/octet-stream"

            # Check file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                print(f"❌ File too large: {file_size / (1024*1024):.2f}MB (max: 10MB)")
                return None

            # Read and encode file
            with open(file_path_obj, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode('utf-8')

            return {
                "filename": filename,
                "content_type": mime_type,
                "size": file_size,
                "content": file_content
            }

        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            return None

    def chat(self, message: str, file_paths: Optional[List[str]] = None, show_metadata: bool = False) -> Dict[str, Any]:
        """Send a message to the Accounting OS with optional file attachments."""
        # Ensure token is valid (auto-refresh or re-login if needed)
        if not self.ensure_valid_token():
            return {
                "success": False,
                "message": "❌ Authentication failed."
            }

        try:
            # Process file attachments
            file_attachments = []
            if file_paths:
                print(f"\n📎 Uploading {len(file_paths)} file(s)...")
                for file_path in file_paths:
                    file_data = self.upload_file(file_path)
                    if file_data:
                        file_attachments.append(file_data)
                        print(f"  ✓ {file_data['filename']} ({file_data['size'] / 1024:.1f}KB)")
                    else:
                        return {
                            "success": False,
                            "message": f"Failed to upload file: {file_path}"
                        }

            payload = {
                "message": message,
                "session_id": self.session_id,
                "stream": False
            }

            # Add file attachments if any
            if file_attachments:
                payload["file_attachments"] = file_attachments

            response = requests.post(
                f"{self.api_url}/api/v1/agent/chat",
                headers=self.headers,
                json=payload,
                timeout=120  # Increased timeout for file uploads
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("❌ Authentication failed. Please check your token.")
                sys.exit(1)
            else:
                return {
                    "success": False,
                    "message": f"Error: {response.status_code} - {response.text}"
                }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": f"❌ Could not connect to {self.api_url}. Is the server running?"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "❌ Request timed out. Please try again."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Error: {str(e)}"
            }

    def chat_with_progress(self, message: str, file_paths: Optional[List[str]] = None, show_metadata: bool = False) -> Dict[str, Any]:
        """
        Send a message to Accounting OS via Server-Sent Events (SSE) with real-time progress.

        This provides a better UX with progress messages that replace each other,
        similar to how Slack shows typing indicators and progress.

        SSE is more reliable than WebSocket for this use case because:
        - Auto-reconnection is built into the SSE spec
        - Standard HTTP (works through proxies/firewalls)
        - Simpler authentication (uses Authorization header)
        - Better for one-way server→client updates
        """
        if not SSE_AVAILABLE:
            # Fallback to regular HTTP chat
            print("⚠️  SSE client not available, using standard chat")
            print("   Install with: pip install sseclient-py")
            return self.chat(message, file_paths, show_metadata)

        # Ensure token is valid (auto-refresh or re-login if needed)
        if not self.ensure_valid_token():
            return {
                "success": False,
                "message": "❌ Authentication failed."
            }

        try:
            # Process file attachments
            file_attachments = []
            if file_paths:
                print(f"\n📎 Uploading {len(file_paths)} file(s)...")
                for file_path in file_paths:
                    file_data = self.upload_file(file_path)
                    if file_data:
                        file_attachments.append(file_data)
                        print(f"  ✓ {file_data['filename']} ({file_data['size'] / 1024:.1f}KB)")
                    else:
                        return {
                            "success": False,
                            "message": f"Failed to upload file: {file_path}"
                        }

            # Prepare request payload
            payload = {
                "message": message,
                "session_id": self.session_id,
                "stream": True
            }

            # Add file attachments if any
            if file_attachments:
                payload["file_attachments"] = file_attachments

            # Send request to SSE endpoint
            response = requests.post(
                f"{self.api_url}/api/v1/agent/chat/stream",
                headers=self.headers,
                json=payload,
                stream=True,  # Enable streaming
                timeout=120
            )

            if response.status_code == 401:
                print("❌ Authentication failed. Please check your token.")
                return {"success": False, "message": "Authentication failed"}

            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Error: {response.status_code} - {response.text}"
                }

            # Track current progress line for replacement
            last_progress = None
            final_response = None

            # Parse SSE events
            client = sseclient.SSEClient(response)

            for event in client.events():
                event_type = event.event or "message"  # Default to "message" if no event type

                # Parse event data
                try:
                    data = json.loads(event.data) if event.data else {}
                except json.JSONDecodeError as e:
                    print(f"\n⚠️  Invalid JSON in event data: {event.data}")
                    continue

                if event_type == "typing":
                    # Show/hide typing indicator
                    is_typing = data.get("is_typing")
                    if is_typing:
                        print("\n💭 Thinking...", end="", flush=True)
                    else:
                        # Clear typing indicator
                        print("\r" + " " * 20 + "\r", end="", flush=True)

                elif event_type == "progress":
                    # Show progress message (replaces previous progress)
                    progress_msg = data.get("message", "")

                    # Build full display text
                    display_text = f"⏳ {progress_msg}"

                    # Clear entire previous line by filling it with spaces
                    if last_progress:
                        # Clear the full length of the previous display
                        clear_length = len(f"⏳ {last_progress}")
                        print("\r" + " " * clear_length + "\r", end="", flush=True)

                    # Print new progress
                    print(display_text, end="", flush=True)
                    last_progress = progress_msg

                elif event_type == "final":
                    # Clear progress line before showing final response
                    if last_progress:
                        clear_length = len(f"⏳ {last_progress}")
                        print("\r" + " " * clear_length + "\r", end="", flush=True)

                    # Final response received
                    final_response = {
                        "success": data.get("success", True),
                        "message": data.get("message", ""),
                        "files": data.get("files", []),
                        "suggestions": data.get("suggestions", []),
                        "execution_time_ms": data.get("execution_time_ms", 0)
                    }
                    break

                elif event_type == "error":
                    # Clear progress line
                    if last_progress:
                        clear_length = len(f"⏳ {last_progress}")
                        print("\r" + " " * clear_length + "\r", end="", flush=True)

                    final_response = {
                        "success": False,
                        "message": data.get("message", "Unknown error")
                    }
                    break

            # Return final response or error
            if final_response:
                return final_response
            else:
                return {
                    "success": False,
                    "message": "Stream ended without final response"
                }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": f"❌ Could not connect to {self.api_url}. Is the server running?"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "❌ Request timed out. Please try again."
            }
        except Exception as e:
            # Fallback to regular chat on SSE error
            print(f"\n⚠️  SSE error: {str(e)}")
            print("⚠️  Falling back to standard chat...")
            return self.chat(message, file_paths, show_metadata)

    def get_capabilities(self) -> Dict[str, Any]:
        """Get available Accounting OS capabilities."""
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/agent/capabilities",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {}

        except Exception as e:
            print(f"Warning: Could not fetch capabilities - {str(e)}")
            return {}

    def render_markdown(self, text: str) -> str:
        """
        Render markdown text for terminal display.

        If rich library is available, uses rich for proper rendering.
        Otherwise, uses simple text substitution for common markdown syntax.
        """
        if RICH_AVAILABLE:
            # Use rich for beautiful markdown rendering
            console = Console()
            console.print(Markdown(text))
            return ""  # Already printed
        else:
            # Simple markdown to terminal text conversion
            # Bold: **text** or __text__ -> text in bold (using ANSI codes)
            text = re.sub(r'\*\*(.+?)\*\*', r'\033[1m\1\033[0m', text)
            text = re.sub(r'__(.+?)__', r'\033[1m\1\033[0m', text)

            # Italic: *text* or _text_ -> text in italic
            text = re.sub(r'\*(.+?)\*', r'\033[3m\1\033[0m', text)
            text = re.sub(r'_(.+?)_', r'\033[3m\1\033[0m', text)

            # Code: `text` -> highlighted
            text = re.sub(r'`(.+?)`', r'\033[96m\1\033[0m', text)

            # Headers: # Text -> bold and larger
            text = re.sub(r'^### (.+)$', r'\033[1m\1\033[0m', text, flags=re.MULTILINE)
            text = re.sub(r'^## (.+)$', r'\033[1;4m\1\033[0m', text, flags=re.MULTILINE)
            text = re.sub(r'^# (.+)$', r'\033[1;4;96m\1\033[0m', text, flags=re.MULTILINE)

            # Lists: - item or * item
            text = re.sub(r'^[\-\*] (.+)$', r'  • \1', text, flags=re.MULTILINE)

            # Numbered lists: 1. item
            text = re.sub(r'^(\d+)\. (.+)$', r'  \1. \2', text, flags=re.MULTILINE)

            # Links: [text](url) -> text (url)
            text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\1 (\033[94m\2\033[0m)', text)

            return text

    def format_response(self, response: Dict[str, Any], show_metadata: bool = False):
        """Format and print the response."""
        if not response.get("success"):
            error_msg = response.get('message', 'Unknown error')
            # Handle case where error message is a dict
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("markdown", str(error_msg))
            print(f"\n{error_msg}\n")
            return

        # Print main message with markdown rendering
        message = response.get("message", "")

        # Handle case where message is a dict (from API renderer)
        if isinstance(message, dict):
            message = message.get("markdown", str(message))

        if message:
            print()  # Newline before message
            if RICH_AVAILABLE:
                # Rich will handle printing
                self.render_markdown(message)
            else:
                # Print our simple rendered markdown
                rendered = self.render_markdown(message)
                print(rendered)
            print()  # Newline after message

        # Print files if any
        files = response.get("files", [])
        if files:
            print("📎 Files generated:")
            for file_info in files:
                filename = file_info.get("filename", "unknown")
                file_type = file_info.get("type", "file")
                url = file_info.get("url", "")
                print(f"  - {filename} ({file_type})")
                if url:
                    print(f"    URL: {url}")
            print()

        # Print suggestions
        suggestions = response.get("suggestions", [])
        if suggestions:
            print("💡 You can try:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
            print()

        # Print metadata if requested
        if show_metadata:
            execution_time = response.get("execution_time_ms", 0)
            tokens_used = response.get("tokens_used")
            print(f"⏱️  Execution time: {execution_time}ms")
            if tokens_used:
                print(f"🎯 Tokens used: {tokens_used}")
            print()

    def run_interactive(self, show_metadata: bool = False):
        """Run interactive chat session with command history."""
        # Setup command history
        history_file = self.CREDENTIALS_DIR / ".chat_history"
        try:
            # Create history directory if it doesn't exist
            self.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

            # Load history if it exists
            if history_file.exists():
                readline.read_history_file(str(history_file))

            # Set history length (keep last 1000 commands)
            readline.set_history_length(1000)
        except Exception as e:
            # History is optional, continue without it if there's an error
            pass

        print("=" * 60)
        print("AI Accounting Assistant - CLI Chat")
        print("=" * 60)
        print(f"Session ID: {self.session_id}")
        print("Type 'help' for commands, 'exit' to quit")
        print("💡 Use ↑/↓ arrows to navigate command history\n")

        # Get capabilities
        capabilities = self.get_capabilities()
        if capabilities:
            print("✅ Connected to Accounting OS")
            print(f"📊 Available operations: {len(capabilities.get('queries', []))} queries, "
                  f"{len(capabilities.get('actions', []))} actions, "
                  f"{len(capabilities.get('reports', []))} reports\n")

        try:
            while True:
                try:
                    user_input = input("You: ").strip()

                    if not user_input:
                        continue

                    # Handle commands
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        print("\nGoodbye! 👋\n")
                        break

                    elif user_input.lower() == 'help':
                        self.show_help()
                        continue

                    elif user_input.lower() == 'capabilities':
                        self.show_capabilities(capabilities)
                        continue

                    elif user_input.lower() == 'files':
                        # List available files in current directory
                        files = self.list_available_files()
                        if files:
                            print("\n📁 Available files in current directory:")
                            for i, filename in enumerate(files, 1):
                                print(f"  {i}. {filename}")
                            print(f"\n💡 Tip: Use @filename to attach files (e.g., 'import @{files[0]}')")
                        else:
                            print("\n📁 No files found in current directory")
                        print()
                        continue

                    elif user_input.lower() == 'clear':
                        os.system('clear' if os.name != 'nt' else 'cls')
                        continue

                    elif user_input.lower() == 'new':
                        self.session_id = f"cli-session-{uuid.uuid4()}"
                        print(f"🔄 New session started: {self.session_id}\n")
                        continue

                    elif user_input.lower().startswith('upload '):
                        # Handle file upload command
                        file_paths = user_input[7:].strip().split()
                        if not file_paths:
                            print("❌ Usage: upload <file1> [file2] [...]\n")
                            continue

                        print("\n📎 Preparing to upload files...")
                        print("💬 Enter your message about these files:")
                        message = input("You: ").strip()

                        if not message:
                            print("❌ Message required for file upload\n")
                            continue

                        print("\nAssistant: ", end="", flush=True)
                        # Use SSE chat for progress if available
                        if SSE_AVAILABLE:
                            response = self.chat_with_progress(message, file_paths=file_paths, show_metadata=show_metadata)
                        else:
                            response = self.chat(message, file_paths=file_paths, show_metadata=show_metadata)
                        self.format_response(response, show_metadata=show_metadata)
                        continue

                    # Parse @filename mentions and auto-attach files
                    cleaned_message, auto_file_paths = self.parse_file_mentions(user_input)

                    # Show which files are being attached (if any)
                    if auto_file_paths:
                        print(f"\n📎 Auto-attaching {len(auto_file_paths)} file(s):")
                        for fp in auto_file_paths:
                            file_size = Path(fp).stat().st_size / 1024
                            print(f"  ✓ {Path(fp).name} ({file_size:.1f}KB)")

                    # Send message to Accounting OS
                    print("\nAssistant: ", end="", flush=True)
                    # Use SSE chat for progress if available
                    if SSE_AVAILABLE:
                        response = self.chat_with_progress(cleaned_message, file_paths=auto_file_paths or None, show_metadata=show_metadata)
                    else:
                        response = self.chat(cleaned_message, file_paths=auto_file_paths or None, show_metadata=show_metadata)
                    self.format_response(response, show_metadata=show_metadata)

                except KeyboardInterrupt:
                    print("\n\nGoodbye! 👋\n")
                    break
                except EOFError:
                    print("\n\nGoodbye! 👋\n")
                    break
        finally:
            # Save command history on exit
            try:
                readline.write_history_file(str(history_file))
            except:
                pass

    def show_help(self):
        """Show help information."""
        print("\n" + "=" * 60)
        print("Available Commands:")
        print("=" * 60)
        print("  help                       - Show this help message")
        print("  capabilities               - Show available operations")
        print("  files                      - List files in current directory")
        print("  upload <file1> [file2...]  - Upload and process files")
        print("  clear                      - Clear the screen")
        print("  new                        - Start a new session")
        print("  exit/quit/q                - Exit the chat")
        print("\nExample queries:")
        print("  - Show me my transactions for last month")
        print("  - Create a journal entry for office rent ₦500,000")
        print("  - Generate balance sheet as PDF")
        print("  - What were my top expenses in Q4?")
        print("  - List all my accounts")
        print("\nFile upload methods:")
        print("  1. Using @ syntax (auto-attach):")
        print("     - import @transactions.csv")
        print("     - analyze @data.xlsx and @report.pdf")
        print("     - process @~/Documents/bank-statement.xlsx")
        print("     - upload @\"/path/with spaces/file.csv\"")
        print("  2. Using upload command:")
        print("     - upload transactions.csv")
        print("     - upload receipt.jpg invoice.pdf")
        print("  3. Using --files flag (single query mode):")
        print("     - python cli/chat.py --message \"import\" --files data.csv")
        print("=" * 60 + "\n")

    def show_capabilities(self, capabilities: Dict[str, Any]):
        """Show available capabilities."""
        print("\n" + "=" * 60)
        print("Accounting OS Capabilities:")
        print("=" * 60)

        queries = capabilities.get("queries", [])
        if queries:
            print(f"\n📊 Queries ({len(queries)}):")
            for q in queries[:10]:
                print(f"  - {q}")
            if len(queries) > 10:
                print(f"  ... and {len(queries) - 10} more")

        actions = capabilities.get("actions", [])
        if actions:
            print(f"\n⚡ Actions ({len(actions)}):")
            for a in actions[:10]:
                print(f"  - {a}")
            if len(actions) > 10:
                print(f"  ... and {len(actions) - 10} more")

        reports = capabilities.get("reports", [])
        if reports:
            print(f"\n📈 Reports ({len(reports)}):")
            for r in reports:
                print(f"  - {r}")

        file_formats = capabilities.get("file_formats", [])
        if file_formats:
            print(f"\n📄 File Formats: {', '.join(file_formats)}")

        integrations = capabilities.get("integrations", [])
        if integrations:
            print(f"\n🔌 Integrations: {', '.join(integrations)}")

        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI Accounting CLI Chat Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive chat with OTP login (recommended)
  python cli/chat.py

  # Login with OTP and save credentials
  python cli/chat.py --login

  # Clear saved credentials
  python cli/chat.py --logout

  # With metadata
  python cli/chat.py --show-metadata

  # Single query (uses saved credentials or prompts for OTP)
  python cli/chat.py --message "show my balance"

  # Upload and process local files
  python cli/chat.py --message "import these transactions" --files transactions.csv

  # Multiple files
  python cli/chat.py --message "process these receipts" --files receipt1.jpg receipt2.jpg

  # Local development
  python cli/chat.py --api-url http://localhost:8000

  # Legacy: Use existing JWT token
  export ACCOUNTING_API_TOKEN="your_jwt_token"
  python cli/chat.py
        """
    )

    parser.add_argument(
        "--api-url",
        default="https://ai.faxter.com",
        help="API base URL (default: https://ai.faxter.com)"
    )

    parser.add_argument(
        "--token",
        default=None,
        help="Authentication token (JWT). If not provided, uses saved credentials or OTP login"
    )

    parser.add_argument(
        "--login",
        action="store_true",
        help="Force OTP login even if credentials are saved"
    )

    parser.add_argument(
        "--logout",
        action="store_true",
        help="Clear saved credentials and exit"
    )

    parser.add_argument(
        "--message",
        help="Send a single message and exit"
    )

    parser.add_argument(
        "--files",
        nargs="+",
        help="Local files to upload and process"
    )

    parser.add_argument(
        "--show-metadata",
        action="store_true",
        help="Show execution time and token usage"
    )

    args = parser.parse_args()

    # Handle logout
    if args.logout:
        AccountingChatCLI.clear_credentials()
        return

    # Try to get authentication token
    auth_token = None
    user_email = None
    creds = None  # Initialize creds variable

    # 1. Check command-line argument
    if args.token:
        auth_token = args.token

    # 2. Check environment variable
    elif os.getenv("ACCOUNTING_API_TOKEN"):
        auth_token = os.getenv("ACCOUNTING_API_TOKEN")

    # 3. Try to load saved credentials (if not forcing login)
    elif not args.login:
        creds = AccountingChatCLI.load_credentials()
        if creds:
            auth_token = creds.get("access_token")
            user_email = creds.get("user_email")
            print(f"✅ Using saved credentials for {user_email}")

    # Create CLI instance
    cli = AccountingChatCLI(api_url=args.api_url, auth_token=auth_token)
    cli.user_email = user_email

    # Load expiration time if credentials exist
    if creds:
        try:
            cli.token_expires_at = datetime.fromisoformat(creds.get("expires_at", ""))
        except:
            cli.token_expires_at = None

    # 4. If no token, prompt for OTP login
    if not auth_token or args.login:
        if not cli.login_with_otp():
            print("\n❌ Authentication failed. Exiting.")
            sys.exit(1)

    # Single message mode
    if args.message:
        # Use SSE chat for progress if available
        if SSE_AVAILABLE:
            response = cli.chat_with_progress(args.message, file_paths=args.files, show_metadata=args.show_metadata)
        else:
            response = cli.chat(args.message, file_paths=args.files, show_metadata=args.show_metadata)
        cli.format_response(response, show_metadata=args.show_metadata)
    elif args.files:
        # Files provided without message
        print("❌ Error: --files requires --message")
        print("\nExample:")
        print('  python cli/chat.py --message "import these transactions" --files data.csv')
        sys.exit(1)
    else:
        # Interactive mode
        cli.run_interactive(show_metadata=args.show_metadata)


if __name__ == "__main__":
    main()
