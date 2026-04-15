#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║      RED TEAM TOOLKIT — Email Harvester Pro  (PyQt6 Edition)        ║
║      OSINT / Recon  |  Multi-URL  |  Crawler  |  Export             ║
╚══════════════════════════════════════════════════════════════════════╝

Install dependencies:
    pip install PyQt6 requests colorama playwright
    playwright install chromium   (optional, for JS-rendered pages)

Run:
    python email_extractor_gui.py
"""

import re
import sys
import csv
import json
import time
import random
import sqlite3
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── PyQt6 ────────────────────────────────────────────────────────────────────
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QTabWidget, QFileDialog, QProgressBar,
    QCheckBox, QSpinBox, QComboBox, QGroupBox, QSplitter,
    QHeaderView, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSortFilterProxyModel,
    QAbstractTableModel, QModelIndex, QVariant
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QAction, QTextCursor,
    QSyntaxHighlighter, QTextCharFormat, QBrush
)

# ── Optional deps ─────────────────────────────────────────────────────────────
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False


# ═════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & THEME
# ═════════════════════════════════════════════════════════════════════════════

APP_NAME    = "Email Harvester Pro"
APP_VERSION = "2.0.0"
DB_PATH     = Path.home() / ".redteam_emailharvester.db"

# Dark red-team theme palette
PALETTE = {
    "bg":           "#0D0D0D",
    "bg2":          "#141414",
    "bg3":          "#1A1A1A",
    "panel":        "#111111",
    "border":       "#2A2A2A",
    "border2":      "#333333",
    "accent":       "#CC2200",
    "accent2":      "#FF3311",
    "accent_dim":   "#661100",
    "text":         "#E8E8E8",
    "text2":        "#999999",
    "text3":        "#555555",
    "green":        "#22AA55",
    "green_dim":    "#114422",
    "amber":        "#CC8800",
    "amber_dim":    "#443300",
    "cyan":         "#11AACC",
    "cyan_dim":     "#0A3344",
    "purple":       "#8855CC",
    "red_dim":      "#330A00",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {PALETTE['bg']};
    color: {PALETTE['text']};
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
}}
QTabWidget::pane {{
    border: 1px solid {PALETTE['border']};
    background: {PALETTE['bg2']};
}}
QTabBar::tab {{
    background: {PALETTE['bg']};
    color: {PALETTE['text2']};
    padding: 8px 20px;
    border: 1px solid {PALETTE['border']};
    border-bottom: none;
    font-size: 11px;
    letter-spacing: 1px;
}}
QTabBar::tab:selected {{
    background: {PALETTE['bg2']};
    color: {PALETTE['accent2']};
    border-top: 2px solid {PALETTE['accent']};
}}
QTabBar::tab:hover {{
    color: {PALETTE['text']};
    background: {PALETTE['bg3']};
}}
QGroupBox {{
    border: 1px solid {PALETTE['border']};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    color: {PALETTE['text2']};
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}
QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background: {PALETTE['bg3']};
    border: 1px solid {PALETTE['border']};
    border-radius: 3px;
    color: {PALETTE['text']};
    padding: 6px 8px;
    selection-background-color: {PALETTE['accent_dim']};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {{
    border: 1px solid {PALETTE['accent_dim']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {PALETTE['bg3']};
    border: 1px solid {PALETTE['border']};
    color: {PALETTE['text']};
    selection-background-color: {PALETTE['accent_dim']};
}}
QPushButton {{
    background: {PALETTE['bg3']};
    border: 1px solid {PALETTE['border2']};
    border-radius: 3px;
    color: {PALETTE['text']};
    padding: 7px 16px;
    font-family: 'Consolas', monospace;
    font-size: 11px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background: {PALETTE['border']};
    border-color: {PALETTE['text3']};
}}
QPushButton:pressed {{
    background: {PALETTE['bg']};
}}
QPushButton#btn_scan {{
    background: {PALETTE['accent_dim']};
    border: 1px solid {PALETTE['accent']};
    color: {PALETTE['accent2']};
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 10px 24px;
}}
QPushButton#btn_scan:hover {{
    background: {PALETTE['accent']};
    color: #FFFFFF;
}}
QPushButton#btn_scan:disabled {{
    background: {PALETTE['bg3']};
    border-color: {PALETTE['border']};
    color: {PALETTE['text3']};
}}
QPushButton#btn_stop {{
    border: 1px solid {PALETTE['amber']};
    color: {PALETTE['amber']};
}}
QPushButton#btn_stop:hover {{
    background: {PALETTE['amber_dim']};
}}
QTableWidget {{
    background: {PALETTE['bg2']};
    alternate-background-color: {PALETTE['bg3']};
    gridline-color: {PALETTE['border']};
    border: 1px solid {PALETTE['border']};
    border-radius: 3px;
    color: {PALETTE['text']};
}}
QTableWidget::item:selected {{
    background: {PALETTE['accent_dim']};
    color: {PALETTE['text']};
}}
QHeaderView::section {{
    background: {PALETTE['bg']};
    color: {PALETTE['text2']};
    border: none;
    border-right: 1px solid {PALETTE['border']};
    border-bottom: 1px solid {PALETTE['border']};
    padding: 6px 10px;
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QProgressBar {{
    background: {PALETTE['bg3']};
    border: 1px solid {PALETTE['border']};
    border-radius: 2px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {PALETTE['accent']};
    border-radius: 2px;
}}
QCheckBox {{
    spacing: 8px;
    color: {PALETTE['text2']};
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {PALETTE['border2']};
    border-radius: 2px;
    background: {PALETTE['bg3']};
}}
QCheckBox::indicator:checked {{
    background: {PALETTE['accent']};
    border-color: {PALETTE['accent']};
}}
QScrollBar:vertical {{
    background: {PALETTE['bg']};
    width: 8px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {PALETTE['border2']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {PALETTE['text3']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QStatusBar {{
    background: {PALETTE['bg']};
    color: {PALETTE['text3']};
    border-top: 1px solid {PALETTE['border']};
    font-size: 11px;
}}
QMenuBar {{
    background: {PALETTE['bg']};
    color: {PALETTE['text2']};
    border-bottom: 1px solid {PALETTE['border']};
}}
QMenuBar::item:selected {{
    background: {PALETTE['bg3']};
    color: {PALETTE['text']};
}}
QMenu {{
    background: {PALETTE['bg2']};
    border: 1px solid {PALETTE['border']};
    color: {PALETTE['text']};
}}
QMenu::item:selected {{
    background: {PALETTE['accent_dim']};
}}
QSplitter::handle {{
    background: {PALETTE['border']};
    width: 1px;
}}
QLabel#lbl_title {{
    color: {PALETTE['accent2']};
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 3px;
}}
QLabel#lbl_subtitle {{
    color: {PALETTE['text3']};
    font-size: 10px;
    letter-spacing: 2px;
}}
QLabel#stat_val {{
    color: {PALETTE['accent2']};
    font-size: 22px;
    font-weight: bold;
}}
QLabel#stat_lbl {{
    color: {PALETTE['text3']};
    font-size: 9px;
    letter-spacing: 2px;
}}
"""

# ═════════════════════════════════════════════════════════════════════════════
#  REGEX & FILTERS
# ═════════════════════════════════════════════════════════════════════════════

EMAIL_RE = re.compile(
    r"(?<![a-zA-Z0-9_.+-])"
    r"[a-zA-Z0-9._%+\-]+"
    r"@"
    r"[a-zA-Z0-9.\-]+"
    r"\."
    r"[a-zA-Z]{2,}"
    r"(?![a-zA-Z0-9_.+-])",
    re.IGNORECASE,
)

NOISE_RE = [
    re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|css|js|json|xml|woff|ttf)$", re.I),
    re.compile(r"^(noreply|no-reply|donotreply|do-not-reply|example|test|admin|root)@", re.I),
    re.compile(r"@(sentry\.|email\.example|placeholder|localhost)", re.I),
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


# ═════════════════════════════════════════════════════════════════════════════
#  DATABASE
# ═════════════════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init()

    def _init(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS scans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                target      TEXT,
                scan_date   TEXT,
                email_count INTEGER,
                status      TEXT
            );
            CREATE TABLE IF NOT EXISTS emails (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id   INTEGER,
                email     TEXT,
                domain    TEXT,
                source    TEXT,
                FOREIGN KEY(scan_id) REFERENCES scans(id)
            );
        """)
        self.conn.commit()

    def new_scan(self, target: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO scans(target, scan_date, email_count, status) VALUES(?,?,0,'running')",
            (target, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()
        return cur.lastrowid

    def add_emails(self, scan_id: int, emails: list[tuple]):
        self.conn.executemany(
            "INSERT INTO emails(scan_id, email, domain, source) VALUES(?,?,?,?)",
            [(scan_id, e, d, s) for e, d, s in emails]
        )
        self.conn.commit()

    def finish_scan(self, scan_id: int, count: int, status: str = "done"):
        self.conn.execute(
            "UPDATE scans SET email_count=?, status=? WHERE id=?",
            (count, status, scan_id)
        )
        self.conn.commit()

    def get_history(self) -> list:
        cur = self.conn.execute(
            "SELECT id, target, scan_date, email_count, status FROM scans ORDER BY id DESC LIMIT 100"
        )
        return cur.fetchall()

    def get_scan_emails(self, scan_id: int) -> list:
        cur = self.conn.execute(
            "SELECT email, domain, source FROM emails WHERE scan_id=?", (scan_id,)
        )
        return cur.fetchall()


# ═════════════════════════════════════════════════════════════════════════════
#  WORKER THREAD
# ═════════════════════════════════════════════════════════════════════════════

class ScanWorker(QThread):
    log         = pyqtSignal(str, str)   # (message, level)
    email_found = pyqtSignal(str, str, str)  # (email, domain, source_url)
    progress    = pyqtSignal(int, int)   # (current, total)
    finished    = pyqtSignal(int)        # total count
    status      = pyqtSignal(str)

    def __init__(self, urls, config):
        super().__init__()
        self.urls    = urls
        self.config  = config
        self._stop   = False
        self.all_emails: set[str] = set()

    def stop(self):
        self._stop = True

    def run(self):
        total_urls = len(self.urls)
        for i, url in enumerate(self.urls):
            if self._stop:
                self.log.emit("Scan stopped by user.", "warn")
                break
            self.status.emit(f"Scanning {i+1}/{total_urls}: {url[:60]}…")
            self.progress.emit(i, total_urls)
            self._process_url(url, depth=0)

            # Rate limiting
            if self.config.get("rate_limit") and i < total_urls - 1:
                delay = random.uniform(
                    self.config["delay_min"],
                    self.config["delay_max"]
                )
                self.log.emit(f"Rate limit: sleeping {delay:.1f}s…", "info")
                time.sleep(delay)

        self.progress.emit(total_urls, total_urls)
        self.finished.emit(len(self.all_emails))
        self.status.emit(f"Done — {len(self.all_emails)} unique emails found.")

    def _process_url(self, url: str, depth: int):
        url = self._normalise(url)
        if not url:
            return

        html = self._fetch(url)
        if html is None:
            return

        if self.config.get("decode_obfuscation"):
            html = self._decode(html)

        emails = self._extract(html)
        new_emails = [e for e in emails if e not in self.all_emails]

        for email in new_emails:
            self.all_emails.add(email)
            domain = email.split("@")[-1]
            self.email_found.emit(email, domain, url)
            self.log.emit(f"  ✔  {email}  ←  {url}", "email")

        if new_emails:
            self.log.emit(f"Found {len(new_emails)} new email(s) on {url}", "ok")

        # Crawler: follow internal links
        max_depth = self.config.get("crawl_depth", 0)
        if depth < max_depth:
            links = self._extract_links(html, url)
            self.log.emit(f"Crawling {len(links)} internal link(s) at depth {depth+1}…", "info")
            for link in links[:self.config.get("max_links", 10)]:
                if self._stop:
                    break
                if self.config.get("rate_limit"):
                    time.sleep(random.uniform(0.5, 1.5))
                self._process_url(link, depth + 1)

    def _fetch(self, url: str) -> Optional[str]:
        # JS-rendered fetch via Playwright
        if self.config.get("use_playwright") and PLAYWRIGHT_OK:
            return self._fetch_playwright(url)
        return self._fetch_requests(url)

    def _fetch_requests(self, url: str) -> Optional[str]:
        if not REQUESTS_OK:
            self.log.emit("'requests' not installed.", "error")
            return None
        try:
            session = requests.Session()
            ua = random.choice(USER_AGENTS) if self.config.get("rotate_ua") else USER_AGENTS[0]
            session.headers.update({
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
            })
            retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 502, 503])
            session.mount("https://", HTTPAdapter(max_retries=retry))
            session.mount("http://", HTTPAdapter(max_retries=retry))

            proxy = self.config.get("proxy") or None
            proxies = {"http": proxy, "https": proxy} if proxy else None

            resp = session.get(
                url,
                timeout=self.config.get("timeout", 15),
                proxies=proxies,
                allow_redirects=True,
                verify=False,
            )
            resp.raise_for_status()
            self.log.emit(f"[{resp.status_code}] {url} ({len(resp.content):,}B)", "info")
            return resp.text
        except Exception as exc:
            self.log.emit(f"Fetch error [{url}]: {exc}", "error")
            return None

    def _fetch_playwright(self, url: str) -> Optional[str]:
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=self.config.get("timeout", 15) * 1000)
                page.wait_for_load_state("networkidle")
                html = page.content()
                browser.close()
                self.log.emit(f"[JS] {url} rendered OK", "info")
                return html
        except Exception as exc:
            self.log.emit(f"Playwright error: {exc}", "error")
            return None

    def _extract(self, html: str) -> list[str]:
        raw = EMAIL_RE.findall(html)
        emails = {e.lower() for e in raw}
        if self.config.get("filter_noise"):
            emails = {e for e in emails if not any(p.search(e) for p in NOISE_RE)}
        return sorted(emails)

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        base = urllib.parse.urlparse(base_url)
        links = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
        internal = []
        for link in links:
            parsed = urllib.parse.urlparse(link)
            if not parsed.scheme:
                link = urllib.parse.urljoin(base_url, link)
                parsed = urllib.parse.urlparse(link)
            if parsed.netloc == base.netloc and parsed.path not in ("", "/"):
                full = parsed.scheme + "://" + parsed.netloc + parsed.path
                if full not in internal:
                    internal.append(full)
        return internal[:self.config.get("max_links", 10)]

    @staticmethod
    def _normalise(url: str) -> str:
        url = url.strip()
        if not url:
            return ""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    @staticmethod
    def _decode(html: str) -> str:
        html = re.sub(r"\s*[\[\(]\s*at\s*[\]\)]\s*", "@", html, flags=re.I)
        html = re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", html, flags=re.I)
        html = re.sub(r"&#\s*64\s*;", "@", html)
        html = re.sub(r"&\s*#\s*46\s*;", ".", html)
        return html


# ═════════════════════════════════════════════════════════════════════════════
#  HEADER WIDGET
# ═════════════════════════════════════════════════════════════════════════════

class HeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)

        left = QVBoxLayout()
        title = QLabel("EMAIL HARVESTER PRO")
        title.setObjectName("lbl_title")
        sub = QLabel(f"RED TEAM TOOLKIT  //  v{APP_VERSION}  //  OSINT / RECON")
        sub.setObjectName("lbl_subtitle")
        left.addWidget(title)
        left.addWidget(sub)

        layout.addLayout(left)
        layout.addStretch()

        # Stat cards
        self.stat_found   = self._stat("0",    "EMAILS FOUND")
        self.stat_scanned = self._stat("0",    "URLS SCANNED")
        self.stat_domains = self._stat("0",    "DOMAINS")

        for w in (self.stat_found, self.stat_scanned, self.stat_domains):
            layout.addWidget(w)

        self.setStyleSheet(f"""
            HeaderWidget {{
                background: {PALETTE['bg2']};
                border-bottom: 1px solid {PALETTE['border']};
            }}
        """)

    def _stat(self, val: str, label: str) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"""
            QFrame {{
                background: {PALETTE['bg3']};
                border: 1px solid {PALETTE['border']};
                border-radius: 4px;
                padding: 4px 14px;
            }}
        """)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)
        v = QLabel(val)
        v.setObjectName("stat_val")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l = QLabel(label)
        l.setObjectName("stat_lbl")
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(v)
        lay.addWidget(l)
        w._val_label = v
        return w

    def update_stats(self, found: int, scanned: int, domains: int):
        self.stat_found._val_label.setText(str(found))
        self.stat_scanned._val_label.setText(str(scanned))
        self.stat_domains._val_label.setText(str(domains))


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  —  Red Team Toolkit")
        self.resize(1280, 820)
        self.setMinimumSize(960, 640)

        self.db         = Database()
        self.worker     = None
        self.results    = []   # list of (email, domain, source)
        self.scan_count = 0
        self.scan_id    = None

        self._build_menu()
        self._build_ui()
        self._refresh_history()

    # ── Menu ──────────────────────────────────────────────────────────────
    def _build_menu(self):
        mb = self.menuBar()
        file_m = mb.addMenu("File")
        file_m.addAction("Import URL List…", self._import_urls)
        file_m.addSeparator()
        file_m.addAction("Export CSV…",  lambda: self._export("csv"))
        file_m.addAction("Export JSON…", lambda: self._export("json"))
        file_m.addAction("Export TXT…",  lambda: self._export("txt"))
        file_m.addSeparator()
        file_m.addAction("Exit", self.close)

        tools_m = mb.addMenu("Tools")
        tools_m.addAction("Clear Results", self._clear_results)
        tools_m.addAction("Clear History DB", self._clear_db)

        help_m = mb.addMenu("Help")
        help_m.addAction("About", self._about)

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self.header = HeaderWidget()
        root.addWidget(self.header)

        # Tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self._build_scan_tab()
        self._build_results_tab()
        self._build_history_tab()
        self._build_log_tab()

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.")

        # Progress bar in status
        self.prog = QProgressBar()
        self.prog.setFixedWidth(200)
        self.prog.setFixedHeight(8)
        self.prog.setValue(0)
        self.prog.setVisible(False)
        self.status_bar.addPermanentWidget(self.prog)

    # ── Scan Tab ──────────────────────────────────────────────────────────
    def _build_scan_tab(self):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ── Left: Input ──────────────────────────────────────────────────
        left = QVBoxLayout()

        grp_url = QGroupBox("TARGET URLs")
        url_lay = QVBoxLayout(grp_url)
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText(
            "Enter one URL per line:\n\nhttps://example.com\nhttps://target.org/contact\n…"
        )
        self.url_input.setMinimumHeight(140)
        url_lay.addWidget(self.url_input)

        row1 = QHBoxLayout()
        btn_clear_url = QPushButton("Clear")
        btn_import    = QPushButton("Import .txt")
        btn_clear_url.clicked.connect(lambda: self.url_input.clear())
        btn_import.clicked.connect(self._import_urls)
        row1.addWidget(btn_clear_url)
        row1.addWidget(btn_import)
        url_lay.addLayout(row1)
        left.addWidget(grp_url)

        # Options
        grp_opt = QGroupBox("SCAN OPTIONS")
        opt_grid = QVBoxLayout(grp_opt)

        # Row: timeout, delay
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Timeout (s):"))
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(5, 120)
        self.spin_timeout.setValue(15)
        r1.addWidget(self.spin_timeout)
        r1.addSpacing(16)
        r1.addWidget(QLabel("Crawl depth:"))
        self.spin_depth = QSpinBox()
        self.spin_depth.setRange(0, 3)
        self.spin_depth.setValue(0)
        self.spin_depth.setToolTip("0 = single page, 1 = follow internal links 1 level, etc.")
        r1.addWidget(self.spin_depth)
        r1.addStretch()
        opt_grid.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Max links/page:"))
        self.spin_links = QSpinBox()
        self.spin_links.setRange(1, 100)
        self.spin_links.setValue(15)
        r2.addWidget(self.spin_links)
        r2.addSpacing(16)
        r2.addWidget(QLabel("Delay min (s):"))
        self.spin_dmin = QSpinBox()
        self.spin_dmin.setRange(0, 30)
        self.spin_dmin.setValue(1)
        r2.addWidget(self.spin_dmin)
        r2.addWidget(QLabel("max:"))
        self.spin_dmax = QSpinBox()
        self.spin_dmax.setRange(0, 60)
        self.spin_dmax.setValue(3)
        r2.addWidget(self.spin_dmax)
        r2.addStretch()
        opt_grid.addLayout(r2)

        # Proxy
        rp = QHBoxLayout()
        rp.addWidget(QLabel("Proxy:"))
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080  (optional)")
        rp.addWidget(self.proxy_input)
        opt_grid.addLayout(rp)

        # Checkboxes
        rc = QHBoxLayout()
        self.chk_filter    = QCheckBox("Filter noise")
        self.chk_rotate_ua = QCheckBox("Rotate User-Agent")
        self.chk_rate      = QCheckBox("Rate limiting")
        self.chk_decode    = QCheckBox("Decode obfuscation")
        self.chk_playwright= QCheckBox(f"Playwright JS{'  ✔' if PLAYWRIGHT_OK else '  ✗ (not installed)'}")
        self.chk_playwright.setEnabled(PLAYWRIGHT_OK)

        self.chk_filter.setChecked(True)
        self.chk_rotate_ua.setChecked(True)
        self.chk_rate.setChecked(True)
        self.chk_decode.setChecked(True)

        for c in (self.chk_filter, self.chk_rotate_ua, self.chk_rate,
                  self.chk_decode, self.chk_playwright):
            rc.addWidget(c)
        rc.addStretch()
        opt_grid.addLayout(rc)
        left.addWidget(grp_opt)

        # Scan / Stop buttons
        btn_row = QHBoxLayout()
        self.btn_scan = QPushButton("▶  START SCAN")
        self.btn_scan.setObjectName("btn_scan")
        self.btn_scan.clicked.connect(self._start_scan)
        self.btn_stop = QPushButton("■  STOP")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_scan)
        btn_row.addWidget(self.btn_scan)
        btn_row.addWidget(self.btn_stop)
        left.addLayout(btn_row)
        left.addStretch()

        # ── Right: Live email feed ────────────────────────────────────────
        right = QVBoxLayout()
        grp_live = QGroupBox("LIVE EMAIL FEED")
        live_lay = QVBoxLayout(grp_live)

        # Filter bar
        frow = QHBoxLayout()
        frow.addWidget(QLabel("Filter:"))
        self.live_filter = QLineEdit()
        self.live_filter.setPlaceholderText("Filter by email or domain…")
        self.live_filter.textChanged.connect(self._filter_live)
        frow.addWidget(self.live_filter)
        live_lay.addLayout(frow)

        self.live_table = QTableWidget(0, 3)
        self.live_table.setHorizontalHeaderLabels(["Email", "Domain", "Source URL"])
        self.live_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.live_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.live_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.live_table.setAlternatingRowColors(True)
        self.live_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.live_table.setSortingEnabled(True)
        self.live_table.verticalHeader().setVisible(False)
        self.live_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        live_lay.addWidget(self.live_table)

        right.addWidget(grp_live)

        layout.addLayout(left, 1)
        layout.addLayout(right, 2)
        self.tabs.addTab(w, "  SCAN  ")

    # ── Results Tab ───────────────────────────────────────────────────────
    def _build_results_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)

        top = QHBoxLayout()
        self.res_filter = QLineEdit()
        self.res_filter.setPlaceholderText("Search results…")
        self.res_filter.textChanged.connect(self._filter_results)
        top.addWidget(QLabel("Search:"))
        top.addWidget(self.res_filter)
        top.addSpacing(16)

        btn_copy = QPushButton("Copy Selected")
        btn_copy.clicked.connect(self._copy_selected)
        btn_csv  = QPushButton("Export CSV")
        btn_json = QPushButton("Export JSON")
        btn_txt  = QPushButton("Export TXT")
        btn_csv.clicked.connect(lambda: self._export("csv"))
        btn_json.clicked.connect(lambda: self._export("json"))
        btn_txt.clicked.connect(lambda: self._export("txt"))
        for b in (btn_copy, btn_csv, btn_json, btn_txt):
            top.addWidget(b)
        lay.addLayout(top)

        self.res_table = QTableWidget(0, 3)
        self.res_table.setHorizontalHeaderLabels(["Email Address", "Domain", "Source URL"])
        self.res_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.res_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.res_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.res_table.setAlternatingRowColors(True)
        self.res_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.res_table.setSortingEnabled(True)
        self.res_table.verticalHeader().setVisible(False)
        self.res_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.res_table)

        self.tabs.addTab(w, "  RESULTS  ")

    # ── History Tab ───────────────────────────────────────────────────────
    def _build_history_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.hist_table = QTableWidget(0, 5)
        self.hist_table.setHorizontalHeaderLabels(["ID", "Target", "Date", "Emails", "Status"])
        self.hist_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hist_table.setAlternatingRowColors(True)
        self.hist_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hist_table.verticalHeader().setVisible(False)
        self.hist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.hist_table.clicked.connect(self._load_hist_emails)

        self.hist_emails = QTableWidget(0, 3)
        self.hist_emails.setHorizontalHeaderLabels(["Email", "Domain", "Source"])
        self.hist_emails.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.hist_emails.setAlternatingRowColors(True)
        self.hist_emails.verticalHeader().setVisible(False)
        self.hist_emails.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        splitter.addWidget(self.hist_table)
        splitter.addWidget(self.hist_emails)
        splitter.setSizes([300, 300])
        lay.addWidget(splitter)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._refresh_history)
        btn_clear_db = QPushButton("Clear DB")
        btn_clear_db.clicked.connect(self._clear_db)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_clear_db)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self.tabs.addTab(w, "  HISTORY  ")

    # ── Log Tab ───────────────────────────────────────────────────────────
    def _build_log_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 11))
        self.log_view.setStyleSheet(f"""
            QTextEdit {{
                background: {PALETTE['bg']};
                color: {PALETTE['text2']};
                border: 1px solid {PALETTE['border']};
                border-radius: 3px;
            }}
        """)
        lay.addWidget(self.log_view)

        row = QHBoxLayout()
        btn_clear_log = QPushButton("Clear Log")
        btn_clear_log.clicked.connect(self.log_view.clear)
        btn_save_log  = QPushButton("Save Log…")
        btn_save_log.clicked.connect(self._save_log)
        row.addWidget(btn_clear_log)
        row.addWidget(btn_save_log)
        row.addStretch()
        lay.addLayout(row)

        self.tabs.addTab(w, "  LOG  ")

    # ── Scan Logic ────────────────────────────────────────────────────────
    def _start_scan(self):
        raw_urls = self.url_input.toPlainText().strip()
        urls = [u.strip() for u in raw_urls.splitlines() if u.strip()]
        if not urls:
            QMessageBox.warning(self, "No URLs", "Please enter at least one URL.")
            return

        if not REQUESTS_OK:
            QMessageBox.critical(self, "Missing Dependency",
                "'requests' not installed.\nRun: pip install requests")
            return

        self._clear_results()
        self.scan_count = len(urls)
        self.btn_scan.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.prog.setVisible(True)
        self.prog.setValue(0)
        self.tabs.setCurrentIndex(0)

        config = {
            "timeout":          self.spin_timeout.value(),
            "crawl_depth":      self.spin_depth.value(),
            "max_links":        self.spin_links.value(),
            "delay_min":        self.spin_dmin.value(),
            "delay_max":        self.spin_dmax.value(),
            "proxy":            self.proxy_input.text().strip(),
            "filter_noise":     self.chk_filter.isChecked(),
            "rotate_ua":        self.chk_rotate_ua.isChecked(),
            "rate_limit":       self.chk_rate.isChecked(),
            "decode_obfuscation": self.chk_decode.isChecked(),
            "use_playwright":   self.chk_playwright.isChecked(),
        }

        target_label = urls[0] if len(urls) == 1 else f"{urls[0]} (+{len(urls)-1} more)"
        self.scan_id = self.db.new_scan(target_label)

        self._log(f"{'─'*60}", "dim")
        self._log(f"  SCAN STARTED  |  {len(urls)} URL(s)  |  {datetime.now().strftime('%H:%M:%S')}", "title")
        self._log(f"{'─'*60}", "dim")

        self.worker = ScanWorker(urls, config)
        self.worker.log.connect(self._log)
        self.worker.email_found.connect(self._on_email_found)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.status.connect(self.status_bar.showMessage)
        self.worker.start()

    def _stop_scan(self):
        if self.worker:
            self.worker.stop()
        self.btn_stop.setEnabled(False)

    def _on_email_found(self, email: str, domain: str, source: str):
        # Live table
        row = self.live_table.rowCount()
        self.live_table.insertRow(row)
        self.live_table.setItem(row, 0, self._colored_item(email, PALETTE['accent2']))
        self.live_table.setItem(row, 1, QTableWidgetItem(domain))
        self.live_table.setItem(row, 2, QTableWidgetItem(source))
        self.live_table.scrollToBottom()

        # Results table
        rrow = self.res_table.rowCount()
        self.res_table.insertRow(rrow)
        self.res_table.setItem(rrow, 0, self._colored_item(email, PALETTE['accent2']))
        self.res_table.setItem(rrow, 1, QTableWidgetItem(domain))
        self.res_table.setItem(rrow, 2, QTableWidgetItem(source))

        # Internal store
        self.results.append((email, domain, source))

        # Stats
        domains = len({r[1] for r in self.results})
        self.header.update_stats(len(self.results), self.scan_count, domains)

    def _on_progress(self, cur: int, total: int):
        if total > 0:
            self.prog.setValue(int(cur / total * 100))

    def _on_finished(self, total: int):
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.prog.setValue(100)

        # Save to DB
        if self.scan_id and self.results:
            self.db.add_emails(self.scan_id, self.results)
        if self.scan_id:
            self.db.finish_scan(self.scan_id, total)

        self._log(f"{'─'*60}", "dim")
        self._log(f"  SCAN COMPLETE  |  {total} unique email(s)  |  {datetime.now().strftime('%H:%M:%S')}", "title")
        self._log(f"{'─'*60}", "dim")
        self.status_bar.showMessage(f"Scan complete — {total} unique emails found.")
        self._refresh_history()

        QTimer.singleShot(3000, lambda: self.prog.setVisible(False))

    # ── Filtering ─────────────────────────────────────────────────────────
    def _filter_live(self, text: str):
        self._filter_table(self.live_table, text)

    def _filter_results(self, text: str):
        self._filter_table(self.res_table, text)

    def _filter_table(self, table: QTableWidget, text: str):
        for row in range(table.rowCount()):
            match = any(
                text.lower() in (table.item(row, col).text().lower() if table.item(row, col) else "")
                for col in range(table.columnCount())
            )
            table.setRowHidden(row, not match)

    # ── History ───────────────────────────────────────────────────────────
    def _refresh_history(self):
        rows = self.db.get_history()
        self.hist_table.setRowCount(0)
        for r in rows:
            i = self.hist_table.rowCount()
            self.hist_table.insertRow(i)
            self.hist_table.setItem(i, 0, QTableWidgetItem(str(r[0])))
            self.hist_table.setItem(i, 1, QTableWidgetItem(r[1]))
            self.hist_table.setItem(i, 2, QTableWidgetItem(r[2]))
            self.hist_table.setItem(i, 3, self._colored_item(str(r[3]), PALETTE['accent2']))
            status_colors = {"done": PALETTE['green'], "running": PALETTE['amber'], "error": PALETTE['accent']}
            sc = status_colors.get(r[4], PALETTE['text2'])
            self.hist_table.setItem(i, 4, self._colored_item(r[4], sc))

    def _load_hist_emails(self):
        row = self.hist_table.currentRow()
        if row < 0:
            return
        scan_id = int(self.hist_table.item(row, 0).text())
        emails = self.db.get_scan_emails(scan_id)
        self.hist_emails.setRowCount(0)
        for e, d, s in emails:
            i = self.hist_emails.rowCount()
            self.hist_emails.insertRow(i)
            self.hist_emails.setItem(i, 0, self._colored_item(e, PALETTE['accent2']))
            self.hist_emails.setItem(i, 1, QTableWidgetItem(d))
            self.hist_emails.setItem(i, 2, QTableWidgetItem(s))

    # ── Export ────────────────────────────────────────────────────────────
    def _export(self, fmt: str):
        if not self.results:
            QMessageBox.information(self, "No Data", "No emails to export.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default = f"emails_{ts}.{fmt}"
        path, _ = QFileDialog.getSaveFileName(self, "Save As", default,
                                               f"{fmt.upper()} Files (*.{fmt})")
        if not path:
            return

        if fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["email", "domain", "source_url", "scan_date"])
                ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for e, d, s in self.results:
                    w.writerow([e, d, s, ts2])

        elif fmt == "json":
            data = [{"email": e, "domain": d, "source": s} for e, d, s in self.results]
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"scan_date": datetime.now().isoformat(),
                           "total": len(data), "emails": data}, f, indent=2)

        elif fmt == "txt":
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# Email Harvester Pro — {datetime.now()}\n")
                f.write(f"# Total: {len(self.results)}\n\n")
                for e, _, _ in self.results:
                    f.write(e + "\n")

        self._log(f"Exported {len(self.results)} emails → {path}", "ok")
        self.status_bar.showMessage(f"Exported to {path}")

    # ── Utils ─────────────────────────────────────────────────────────────
    def _log(self, msg: str, level: str = "info"):
        colors = {
            "info":  PALETTE['text2'],
            "ok":    PALETTE['green'],
            "warn":  PALETTE['amber'],
            "error": PALETTE['accent2'],
            "email": PALETTE['cyan'],
            "title": PALETTE['accent2'],
            "dim":   PALETTE['text3'],
        }
        color = colors.get(level, PALETTE['text2'])
        ts = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<span style="color:{PALETTE["text3"]}">[{ts}]</span> '
            f'<span style="color:{color}">{msg}</span>'
        )
        self.log_view.append(html)
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)

    def _colored_item(self, text: str, color: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setForeground(QBrush(QColor(color)))
        return item

    def _clear_results(self):
        self.results.clear()
        self.live_table.setRowCount(0)
        self.res_table.setRowCount(0)
        self.header.update_stats(0, 0, 0)

    def _import_urls(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import URL List", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        try:
            urls = Path(path).read_text(encoding="utf-8").strip()
            current = self.url_input.toPlainText().strip()
            combined = (current + "\n" + urls).strip() if current else urls
            self.url_input.setPlainText(combined)
            self._log(f"Imported URLs from {path}", "ok")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _copy_selected(self):
        rows = set(i.row() for i in self.res_table.selectedItems())
        text = "\n".join(self.res_table.item(r, 0).text() for r in sorted(rows) if self.res_table.item(r, 0))
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage(f"Copied {len(rows)} email(s) to clipboard.")

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Log", "scan_log.txt", "Text Files (*.txt)")
        if path:
            text = self.log_view.toPlainText()
            Path(path).write_text(text, encoding="utf-8")

    def _clear_db(self):
        if QMessageBox.question(self, "Confirm", "Clear entire scan history database?") \
                == QMessageBox.StandardButton.Yes:
            self.db.conn.executescript("DELETE FROM emails; DELETE FROM scans;")
            self.db.conn.commit()
            self._refresh_history()
            self.hist_emails.setRowCount(0)

    def _about(self):
        QMessageBox.about(self, f"About {APP_NAME}",
            f"<b>Email Harvester Pro</b><br>"
            f"Red Team Toolkit — v{APP_VERSION}<br><br>"
            f"OSINT email extraction with multi-URL batch,<br>"
            f"internal link crawler, UA rotation, export,<br>"
            f"and persistent scan history.<br><br>"
            f"<i>For authorized security testing only.</i>")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        event.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(STYLESHEET)

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(PALETTE['bg']))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(PALETTE['text']))
    palette.setColor(QPalette.ColorRole.Base,            QColor(PALETTE['bg2']))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(PALETTE['bg3']))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(PALETTE['bg3']))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(PALETTE['text']))
    palette.setColor(QPalette.ColorRole.Text,            QColor(PALETTE['text']))
    palette.setColor(QPalette.ColorRole.Button,          QColor(PALETTE['bg3']))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(PALETTE['text']))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(PALETTE['accent_dim']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(PALETTE['text']))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
