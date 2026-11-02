#!/usr/bin/env python3
"""Read and search the internal Yunxin DokuWiki."""

from __future__ import annotations

import argparse
import ctypes
import getpass
import html
import http.cookiejar
import json
import os
import platform
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


DEFAULT_BASE_URL = "http://192.168.0.112:8800"
USER_AGENT = "Codex-YunxinWikiSkill/1.0"
LOGIN_FORM_ID = "dw__login"
DPAPI_DESCRIPTION = "Yunxin Wiki credentials"
DPAPI_UI_FORBIDDEN = 0x1


class WikiError(RuntimeError):
    """A user-actionable Wiki error."""


@dataclass(frozen=True)
class CredentialRecord:
    username: str
    password: str
    base_url: str


def normalize_base_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise WikiError("base URL must be an absolute http(s) URL")
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path.rstrip("/") or "", "", "", "")
    )


def url_origin(value: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(normalize_base_url(value))
    return parsed.scheme.lower(), parsed.netloc.lower()


def page_url_for(base_url: str, page_id: str) -> str:
    query = urllib.parse.urlencode({"id": page_id})
    return f"{normalize_base_url(base_url)}/doku.php?{query}"


def _runtime_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    if not root:
        root = str(Path.home() / "AppData" / "Local")
    return Path(root) / "Codex" / "yunxin-wiki"


def credentials_path() -> Path:
    return _runtime_dir() / "credentials.dpapi"


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_uint32),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _blob_from_bytes(value: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = (ctypes.c_ubyte * len(value)).from_buffer_copy(value)
    blob = _DataBlob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    return blob, buffer


def _blob_bytes(blob: _DataBlob) -> bytes:
    if blob.cbData == 0:
        return b""
    return ctypes.string_at(blob.pbData, blob.cbData)


def _dpapi_libraries() -> tuple[ctypes.CDLL, ctypes.CDLL]:
    if platform.system() != "Windows":
        raise WikiError("DPAPI credential storage is available only on Windows")
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.c_wchar_p,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = ctypes.c_bool
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.POINTER(ctypes.c_wchar_p),
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = ctypes.c_bool
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    return crypt32, kernel32


def dpapi_encrypt(value: bytes) -> bytes:
    crypt32, kernel32 = _dpapi_libraries()
    input_blob, input_buffer = _blob_from_bytes(value)
    output_blob = _DataBlob()
    if not crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        DPAPI_DESCRIPTION,
        None,
        None,
        None,
        DPAPI_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise WikiError("Windows could not protect the Wiki credentials")
    try:
        return _blob_bytes(output_blob)
    finally:
        kernel32.LocalFree(output_blob.pbData)
        del input_buffer


def dpapi_decrypt(value: bytes) -> bytes:
    crypt32, kernel32 = _dpapi_libraries()
    input_blob, input_buffer = _blob_from_bytes(value)
    output_blob = _DataBlob()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        DPAPI_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise WikiError(
            "Windows could not decrypt the Wiki credentials; save them again with "
            "`wiki.py auth --store`"
        )
    try:
        return _blob_bytes(output_blob)
    finally:
        kernel32.LocalFree(output_blob.pbData)
        del input_buffer


def save_credentials(username: str, password: str, base_url: str) -> None:
    username = username.strip()
    if not username or not password:
        raise WikiError("username and password must not be empty")
    payload = json.dumps(
        {
            "username": username,
            "password": password,
            "base_url": normalize_base_url(base_url),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    encrypted = dpapi_encrypt(payload)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(encrypted)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        temporary.unlink(missing_ok=True)


def load_credentials() -> CredentialRecord:
    username = os.environ.get("YUNXIN_WIKI_USERNAME", "").strip()
    password = os.environ.get("YUNXIN_WIKI_PASSWORD", "")
    if username and password:
        return CredentialRecord(
            username=username,
            password=password,
            base_url=normalize_base_url(
                os.environ.get("YUNXIN_WIKI_BASE_URL", DEFAULT_BASE_URL)
            ),
        )

    path = credentials_path()
    if not path.exists():
        raise WikiError(
            "Wiki credentials are not configured; run "
            "`python wiki.py auth --store --username <name> --password-stdin`"
        )
    try:
        payload = json.loads(dpapi_decrypt(path.read_bytes()).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WikiError(f"Could not read the protected Wiki credentials: {exc}") from exc
    stored_username = str(payload.get("username", "")).strip()
    stored_password = str(payload.get("password", ""))
    if not stored_username or not stored_password:
        raise WikiError("The protected Wiki credential file is incomplete")
    return CredentialRecord(
        username=stored_username,
        password=stored_password,
        base_url=normalize_base_url(str(payload.get("base_url", DEFAULT_BASE_URL))),
    )


@dataclass
class Response:
    url: str
    status: int
    content_type: str
    body: bytes

    def text(self) -> str:
        charset = "utf-8"
        match = re.search(r"charset=([^;\s]+)", self.content_type, re.IGNORECASE)
        if match:
            charset = match.group(1).strip("\"'")
        try:
            return self.body.decode(charset, errors="replace")
        except LookupError:
            return self.body.decode("utf-8", errors="replace")


class DokuWikiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = normalize_base_url(base_url)
        self.origin = url_origin(self.base_url)
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def url_for(self, path: str, params: dict[str, str | int] | None = None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            clean = {key: str(value) for key, value in params.items() if value != ""}
            url = f"{url}?{urllib.parse.urlencode(clean)}"
        return url

    def request(
        self,
        url: str,
        *,
        data: dict[str, str] | None = None,
        timeout: float = 20.0,
    ) -> Response:
        encoded = None
        if data is not None:
            encoded = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=encoded,
            method="POST" if encoded is not None else "GET",
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,text/plain,application/xhtml+xml",
            },
        )
        try:
            with self.opener.open(request, timeout=timeout) as response:
                return Response(
                    url=response.geturl(),
                    status=response.status,
                    content_type=response.headers.get("Content-Type", ""),
                    body=response.read(),
                )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            detail = re.sub(r"<[^>]+>", " ", detail)
            detail = re.sub(r"\s+", " ", html.unescape(detail)).strip()
            raise WikiError(
                f"Wiki request failed with HTTP {exc.code}: {detail[:300]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise WikiError(f"Could not reach the Wiki: {exc.reason}") from exc

    def _assert_same_origin(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        origin = (parsed.scheme.lower(), parsed.netloc.lower())
        if origin != self.origin:
            raise WikiError("refusing to submit credentials to a different origin")

    def login(self, username: str, password: str) -> None:
        login_url = self.url_for("doku.php", {"id": "start", "do": "login"})
        page = self.request(login_url).text()
        if _looks_authenticated(page):
            return

        parser = LoginFormParser(LOGIN_FORM_ID)
        parser.feed(page)
        if not parser.action:
            raise WikiError("could not find the DokuWiki login form")
        action = urllib.parse.urljoin(login_url, html.unescape(parser.action))
        self._assert_same_origin(action)
        fields = dict(parser.fields)
        fields.update({"u": username, "p": password, "r": "1", "do": "login"})
        result = self.request(action, data=fields).text()
        if not _looks_authenticated(result):
            message = _plain_text(result)
            if re.search(r"login failed|incorrect|wrong", message, re.IGNORECASE):
                raise WikiError("Wiki login failed; check the saved credentials")
            raise WikiError(
                "Wiki login did not produce an authenticated page; the site login "
                "flow may have changed"
            )

    def search(self, query: str, limit: int) -> list[dict[str, str]]:
        url = self.url_for(
            "doku.php", {"id": "start", "do": "search", "q": query, "srt": "score"}
        )
        page = self.request(url)
        parser = SearchResultsParser(self.base_url)
        parser.feed(page.text())
        return parser.results[:limit]

    def page_text(self, page_id: str) -> tuple[str, str]:
        url = self.url_for("doku.php", {"id": page_id, "do": "export_xhtml"})
        response = self.request(url)
        document = response.text()
        if _looks_access_denied(document):
            raise WikiError(
                "the Wiki denied access or returned a login page instead of page content"
            )
        parser = PageTextParser()
        parser.feed(document)
        title = parser.title or page_id
        return title, parser.content

    def page_raw(self, page_id: str) -> str:
        url = self.url_for("doku.php", {"id": page_id, "do": "export_raw"})
        response = self.request(url)
        text = response.text()
        if "text/html" in response.content_type.lower():
            raise WikiError(
                "the Wiki returned HTML instead of raw markup; access may have expired"
            )
        return text


class LoginFormParser(HTMLParser):
    def __init__(self, form_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.form_id = form_id
        self.in_form = False
        self.action: str | None = None
        self.fields: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "form" and values.get("id") == self.form_id:
            self.in_form = True
            self.action = values.get("action")
            return
        if self.in_form and tag == "input":
            name = values.get("name")
            if name:
                self.fields.append((name, values.get("value") or ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self.in_form:
            self.in_form = False


class SearchResultsParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.element_depth = 0
        self.quick_depth = 0
        self.full_depth = 0
        self.meta_depth = 0
        self.current_links: list[tuple[str, str]] = []
        self.current_text: list[str] = []
        self.in_anchor = False
        self.anchor_href = ""
        self.anchor_id = ""
        self.anchor_text: list[str] = []
        self.results: list[dict[str, str]] = []
        self.seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.element_depth += 1
        values = dict(attrs)
        classes = (values.get("class") or "").split()
        if tag == "ul" and "search_quickhits" in classes:
            self.quick_depth = self.element_depth
        if tag == "dd" and self.full_depth and "meta" in classes:
            self.meta_depth = self.element_depth
        if tag == "div":
            if self.full_depth:
                self.full_depth += 1
            elif "search_fullpage_result" in classes:
                self.full_depth = 1
                self.current_links = []
                self.current_text = []
        elif tag == "a" and (self.full_depth or self.quick_depth):
            self.in_anchor = True
            self.anchor_href = values.get("href") or ""
            self.anchor_id = values.get("data-wiki-id") or ""
            self.anchor_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_anchor:
            text = _clean_text("".join(self.anchor_text))
            if text and self.anchor_href:
                self.current_links.append((text, self.anchor_href))
                if self.quick_depth and self.anchor_id:
                    self._add_result(text, self.anchor_href, "")
            self.in_anchor = False
        elif tag == "div":
            if self.full_depth:
                self.full_depth -= 1
                if self.full_depth == 0:
                    self._finish_full_result()
        if self.meta_depth == self.element_depth:
            self.meta_depth = 0
        if self.quick_depth == self.element_depth:
            self.quick_depth = 0
        self.element_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.full_depth and not self.meta_depth:
            self.current_text.append(data)
        if self.in_anchor:
            self.anchor_text.append(data)

    def _finish_full_result(self) -> None:
        for title, href in self.current_links:
            page_id = extract_page_id(
                urllib.parse.urljoin(self.base_url.rstrip("/") + "/", href)
            )
            if not page_id:
                continue
            snippet = _clean_text("".join(self.current_text))
            if title in snippet:
                snippet = snippet.replace(title, "", 1).strip(" -:")
            self._add_result(title, href, snippet[:500])
            break

    def _add_result(self, title: str, href: str, snippet: str) -> None:
        page_id = extract_page_id(
            urllib.parse.urljoin(self.base_url.rstrip("/") + "/", href)
        )
        if not page_id or page_id in self.seen:
            return
        self.seen.add(page_id)
        self.results.append(
            {
                "id": page_id,
                "title": title,
                "url": page_url_for(self.base_url, page_id),
                "snippet": snippet,
            }
        )


class PageTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.pre_depth = 0
        self.heading_depth = 0
        self.heading_parts: list[str] = []
        self.headings: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
        elif tag == "pre":
            self.pre_depth += 1
            self.text.append("\n")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_depth += 1
            if self.heading_depth == 1:
                self.heading_parts = []
            self.text.append("\n" + "#" * int(tag[1]) + " ")
        elif tag in {"p", "div", "br", "li", "tr", "table"}:
            self.text.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        elif tag == "pre" and self.pre_depth:
            self.pre_depth -= 1
            self.text.append("\n")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.heading_depth:
            self.heading_depth -= 1
            if self.heading_depth == 0:
                heading = _clean_text("".join(self.heading_parts))
                if heading:
                    self.headings.append(heading)
            self.text.append("\n")
        elif tag in {"p", "div", "li", "tr", "table"}:
            self.text.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.pre_depth:
            value = data.replace("\r\n", "\n").replace("\r", "\n")
            if self.heading_depth:
                self.heading_parts.append(value)
            if value:
                self.text.append(value)
            return
        cleaned = re.sub(r"\s+", " ", data).strip()
        if not cleaned:
            return
        if self.heading_depth:
            self.heading_parts.append(cleaned)
        self.text.append(cleaned)
        if not self.heading_depth:
            self.text.append(" ")

    @property
    def title(self) -> str:
        for heading in self.headings:
            if heading.casefold() not in {"table of contents", "目录"}:
                return heading
        return self.headings[0] if self.headings else ""

    @property
    def content(self) -> str:
        value = "".join(self.text)
        value = re.sub(r"[ \t]+\n", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _plain_text(document: str) -> str:
    parser = PageTextParser()
    parser.feed(document)
    return parser.content


def _looks_authenticated(document: str) -> bool:
    lowered = document.lower()
    return "logged in as:" in lowered or (
        "log out" in lowered and f'id="{LOGIN_FORM_ID}"' not in lowered
    )


def _looks_access_denied(document: str) -> bool:
    lowered = document.casefold()
    return any(
        marker in lowered
        for marker in (
            "permission_denied",
            "permission denied",
            "you don't have enough rights",
            f'id="{LOGIN_FORM_ID}"',
        )
    )


def extract_page_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    values = query.get("id", [])
    if values:
        return values[0].strip()
    match = re.search(r"/doku\.php/([^?#]+)", parsed.path)
    return urllib.parse.unquote(match.group(1)) if match else ""


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_auth(args: argparse.Namespace) -> int:
    path = credentials_path()
    if not args.store and (args.username or args.password_stdin):
        raise WikiError("--username and --password-stdin require --store")
    if args.clear:
        path.unlink(missing_ok=True)
        print("Protected Wiki credentials removed.")
        return 0
    if args.store:
        username = args.username or input("Wiki username: ").strip()
        if args.password_stdin:
            password = sys.stdin.readline().rstrip("\r\n")
        else:
            password = getpass.getpass("Wiki password: ")
        save_credentials(username, password, args.base_url)
        print(f"Protected Wiki credentials saved for {username}.")
        print(f"Bound Wiki origin: {normalize_base_url(args.base_url)}")
        return 0
    if not path.exists():
        print("Wiki credentials are not configured.")
        return 1
    record = load_credentials()
    print(f"Wiki credentials configured for {record.username}.")
    print(f"Bound Wiki origin: {record.base_url}")
    print(f"Credential file: {path}")
    return 0


def make_client(args: argparse.Namespace) -> DokuWikiClient:
    record = load_credentials()
    requested_base = normalize_base_url(args.base_url)
    if url_origin(requested_base) != url_origin(record.base_url):
        raise WikiError(
            "the protected credentials are bound to "
            f"{record.base_url}; refusing to send them to {requested_base}. "
            "Re-run auth --store with the intended --base-url if this change is deliberate"
        )
    client = DokuWikiClient(requested_base)
    client.login(record.username, record.password)
    return client


def cmd_doctor(args: argparse.Namespace) -> int:
    record = load_credentials()
    client = make_client(args)
    response = client.request(client.url_for("doku.php", {"id": "start"}))
    result = {
        "ok": True,
        "base_url": client.base_url,
        "user": record.username,
        "status": response.status,
        "credentials": str(credentials_path()),
    }
    print_json(result)
    return 0

def cmd_search(args: argparse.Namespace) -> int:
    client = make_client(args)
    results = client.search(args.query, args.limit)
    if args.json:
        print_json({"query": args.query, "count": len(results), "results": results})
        return 0
    if not results:
        print(f'No Wiki pages matched "{args.query}".')
        return 1
    for item in results:
        print(f"{item['id']}\t{item['title']}")
        if item.get("snippet"):
            print(f"  {item['snippet']}")
    return 0


def cmd_page(args: argparse.Namespace) -> int:
    client = make_client(args)
    page_id = urllib.parse.unquote(args.page_id)
    if args.raw:
        content = client.page_raw(page_id)
        title = page_id
        mode = "raw"
    else:
        title, content = client.page_text(page_id)
        mode = "text"
    if args.max_chars > 0:
        content = content[: args.max_chars]
    if args.json:
        print_json(
            {
                "id": page_id,
                "title": title,
                "mode": mode,
                "url": page_url_for(client.base_url, page_id),
                "content": content,
            }
        )
    elif args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(args.output)
    else:
        print(content)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search and read the internal Yunxin DokuWiki."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("YUNXIN_WIKI_BASE_URL", DEFAULT_BASE_URL),
        help=f"Wiki base URL (default: {DEFAULT_BASE_URL})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth = subparsers.add_parser("auth", help="manage protected Wiki credentials")
    auth_action = auth.add_mutually_exclusive_group()
    auth_action.add_argument("--store", action="store_true", help="store credentials")
    auth_action.add_argument("--clear", action="store_true", help="delete credentials")
    auth_action.add_argument("--status", action="store_true", help="show credential status")
    auth.add_argument("--username", help="Wiki username for --store")
    auth.add_argument(
        "--password-stdin",
        action="store_true",
        help="read the password from stdin instead of prompting",
    )
    auth.set_defaults(func=cmd_auth)

    doctor = subparsers.add_parser("doctor", help="verify login and connectivity")
    doctor.set_defaults(func=cmd_doctor)

    search = subparsers.add_parser("search", help="full-text search Wiki pages")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--json", action="store_true")
    search.set_defaults(func=cmd_search)

    page = subparsers.add_parser("page", help="read one Wiki page")
    page.add_argument("page_id", help="DokuWiki page ID, for example cmd:msg:outmsg")
    page.add_argument("--raw", action="store_true", help="return DokuWiki raw markup")
    output_group = page.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true")
    output_group.add_argument("--output", help="write content to a UTF-8 file")
    page.add_argument(
        "--max-chars",
        type=int,
        default=0,
        help="truncate output to this many characters; 0 means no limit",
    )
    page.set_defaults(func=cmd_page)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if getattr(args, "limit", 1) <= 0:
        parser.error("--limit must be positive")
    if getattr(args, "max_chars", 0) < 0:
        parser.error("--max-chars must be zero or positive")
    try:
        return int(args.func(args))
    except WikiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
