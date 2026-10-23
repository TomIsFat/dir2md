import sys
import os
import re
import fnmatch
import zipfile
import tarfile
import tempfile
import shutil
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeView, QPlainTextEdit, QLabel, QMessageBox,
    QFileDialog, QListWidget, QListWidgetItem, QProgressDialog,
    QAbstractItemView, QSplitter, QLineEdit, QComboBox, QCheckBox,
    QDialog
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QSortFilterProxyModel,
    QFileSystemWatcher, QTimer
)
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QFont, QPalette,
    QColor, QTextCursor
)

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# ==================== 全局 UI 缩放 ====================
UI_BASE_SCALE = 0.85


# ==================== ★ 文本扩展名白名单（跳过二进制检测 IO） ====================
TEXT_EXTENSIONS = {
    'js', 'mjs', 'cjs', 'jsx', 'ts', 'tsx', 'vue', 'svelte', 'astro',
    'json', 'json5', 'jsonc', 'lock',
    'html', 'htm', 'xml', 'svg', 'css', 'scss', 'sass', 'less', 'styl',
    'md', 'markdown', 'mdx', 'txt', 'log', 'csv',
    'yml', 'yaml', 'toml', 'ini', 'conf', 'cfg', 'properties',
    'py', 'rb', 'go', 'rs', 'java', 'kt', 'c', 'h', 'cpp', 'hpp', 'cc', 'cs',
    'php', 'sh', 'bash', 'zsh', 'fish', 'ps1', 'sql',
}


# ==================== 常量定义 ====================
BINARY_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico', 'webp',
    'mp4', 'mp3', 'avi', 'mov', 'wmv', 'flv',
    'pdf', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip', 'rar', '7z', 'tar', 'gz',
    'exe', 'dll', 'so', 'dylib',
    'iso', 'img',
    'woff', 'woff2', 'ttf', 'eot',
    'psd', 'ai', 'eps',
    'bin', 'dat', 'db', 'sqlite', 'cur', 'icns'
}

IGNORE_DIR_NAMES = {
    '.git', '.svn', '.hg',
    '__pycache__', 'venv', '.venv', '.pytest_cache',
    'node_modules', 'target', 'bin', 'obj',
    'build', 'dist', '.idea', '.vscode', 'vendor', 'out'
}

IGNORE_FILE_EXTENSIONS = {
    'o', 'obj', 'exe', 'dll', 'so', 'dylib',
    'pyc', 'pyo', 'pkl', 'db', 'class',
    'log', 'tmp', 'swp', 'swo', 'csv'
}

IGNORE_FILE_NAMES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}

SENSITIVE_KEYWORDS = [
    '.env', '.key', '.pem', 'id_rsa', 'id_dsa',
    'password', 'secret', 'token', 'credential', 'aws', 'private'
]

# ★ 1.3：base64 阈值提到 80 且必须带 padding，避免误伤 git SHA / lock hash
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*\S+'), r'\1 = [REDACTED]'),
    (re.compile(r'(?i)(api[_-]?key|secret|token)\s*[=:]\s*\S+'), r'\1 = [REDACTED]'),
    (re.compile(r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----.*?-----END \1 PRIVATE KEY-----', re.DOTALL), '[REDACTED PRIVATE KEY]'),
    (re.compile(r'[A-Za-z0-9+/]{80,}={1,2}'), '[REDACTED BASE64]'),
]

# 多语言字符串
STRINGS = {
    'zh': {
        'window_title': 'repo2md - 项目转Markdown',
        'choose_folder': '📁 选择文件夹',
        'no_folder': '未选择文件夹（也可拖入文件夹或压缩包）',
        'ext_filter': '🔍 扩展名筛选',
        'file_tree': '📂 项目文件 (勾选所需文件)',
        'size_label': '📦 当前选中总大小: {}',
        'generate': '生成 Markdown',
        'copy': '📋 复制到剪贴板',
        'export_md': '💾 导出为 .md',
        'outline': '📑 大纲',
        'refresh': '🔄 刷新',
        'search_placeholder': '🔎 搜索文件名...',
        'language': '语言',
        'sensitive_filter': '🔒 过滤敏感内容',
        'gitignore': '📄 尊重 .gitignore',
        'scanning': '扫描文件中...',
        'generating': '生成 Markdown 中...',
        'extracting': '解压中...',
        'cancel': '取消',
        'warning': '提示',
        'error': '错误',
        'no_selection': '请至少勾选一个文件',
        'no_content': '请先生成 Markdown 内容',
        'sensitive_warning': '选中的文件包含可能敏感的信息：\n{}\n\n确定要继续生成吗？',
        'token_estimate_warning': '预计生成长度约 {} token，可能超过模型限制（128k）。是否继续？',
        'token_warning': '生成的文档大约包含 {} token，可能超过模型限制（128k）。',
        'generate_cancelled': '已取消生成',
        'copy_success': '已复制到剪贴板',
        'export_success': '已保存到 {}',
        'binary_skipped': '[二进制文件，已跳过: {}]',
        'read_failed': '[读取失败: {}]',
        'no_heading': '当前文档没有标题',
        'heading_not_found': '未找到标题：{}',
        'unsupported_archive': '不支持的压缩格式，仅支持 ZIP / TAR / GZ / TGZ',
        'drop_hint': '请拖入文件夹或压缩包 (ZIP/TAR/GZ/TGZ)',
        'extract_failed': '解压失败：{}',
    },
    'en': {
        'window_title': 'repo2md - Project to Markdown',
        'choose_folder': '📁 Choose Folder',
        'no_folder': 'No folder selected (drag folder or archive too)',
        'ext_filter': '🔍 Extension Filter',
        'file_tree': '📂 Project Files (check files)',
        'size_label': '📦 Total size: {}',
        'generate': 'Generate Markdown',
        'copy': '📋 Copy to Clipboard',
        'export_md': '💾 Export as .md',
        'outline': '📑 Outline',
        'refresh': '🔄 Refresh',
        'search_placeholder': '🔎 Search files...',
        'language': 'Language',
        'sensitive_filter': '🔒 Redact sensitive',
        'gitignore': '📄 Respect .gitignore',
        'scanning': 'Scanning files...',
        'generating': 'Generating Markdown...',
        'extracting': 'Extracting...',
        'cancel': 'Cancel',
        'warning': 'Warning',
        'error': 'Error',
        'no_selection': 'Please select at least one file',
        'no_content': 'Please generate Markdown first',
        'sensitive_warning': 'Selected files may contain sensitive information:\n{}\n\nContinue?',
        'token_estimate_warning': 'Estimated length ~{} tokens, may exceed model limit (128k). Continue?',
        'token_warning': 'The generated document contains approximately {} tokens, which may exceed the model limit (128k).',
        'generate_cancelled': 'Generation cancelled',
        'copy_success': 'Copied to clipboard',
        'export_success': 'Saved to {}',
        'binary_skipped': '[Binary file skipped: {}]',
        'read_failed': '[Read failed: {}]',
        'no_heading': 'Current document has no headings',
        'heading_not_found': 'Heading not found: {}',
        'unsupported_archive': 'Unsupported archive format, only ZIP / TAR / GZ / TGZ',
        'drop_hint': 'Please drop a folder or archive (ZIP/TAR/GZ/TGZ)',
        'extract_failed': 'Extract failed: {}',
    }
}


# ==================== 工具函数 ====================
def format_bytes(size):
    if size == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_extension(path):
    parts = path.split('/')
    file = parts[-1]
    dot = file.rfind('.')
    if dot == -1:
        return '[无后缀]'
    return file[dot + 1:].lower()


# ★ 1.1：编码顺序修复（UTF-16 BOM 优先，gb18030 兜底，最后 replace）
def read_text_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            head = f.read(4)
    except OSError:
        return ''

    # UTF-16 LE / BE
    if head.startswith(b'\xff\xfe') or head.startswith(b'\xfe\xff'):
        try:
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-16', errors='replace')
        except Exception:
            pass

    # UTF-8 家族 → GB18030 → Big5
    for enc in ('utf-8-sig', 'utf-8', 'gb18030', 'big5'):
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    # 最后兜底，永不抛错
    try:
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='replace')
    except Exception:
        return ''


# ★ 2.4：白名单命中直接跳过 IO；其余再魔数检测
def is_binary_file(file_path, check_magic=True):
    ext = get_extension(file_path)
    if ext in TEXT_EXTENSIONS:
        return False, ''
    if ext in BINARY_EXTENSIONS:
        return True, f"扩展名 {ext} 在黑名单中"
    if not check_magic:
        return False, ''

    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
        if len(header) < 4:
            return False, ''
        if header.startswith(b'%PDF'):
            return True, '魔数 PDF'
        if header.startswith(b'\x89PNG'):
            return True, '魔数 PNG'
        if header.startswith(b'\xFF\xD8\xFF'):
            return True, '魔数 JPEG'
        if header.startswith(b'PK'):
            return True, '魔数 ZIP'
        if header.startswith(b'\x1F\x8B'):
            return True, '魔数 GZIP'
        if header.startswith(b'\x7FELF'):
            return True, '魔数 ELF'
    except Exception:
        return True, '读取失败'

    return False, ''


def redact_sensitive_content(text):
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def estimate_tokens(text):
    if TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            pass
    return len(text) // 4


# ★ 3.6：读取根目录 .gitignore 并做简化匹配
def load_gitignore_patterns(root):
    path = os.path.join(root, '.gitignore')
    patterns = []
    if not os.path.isfile(path):
        return patterns
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.rstrip('\n\r').strip()
                if not line or line.startswith('#'):
                    continue
                patterns.append(line)
    except Exception:
        pass
    return patterns


def is_gitignored(rel_path, is_dir, patterns):
    """简化版 gitignore 匹配（支持通配符、目录专用、! 否定、根锚定）"""
    if not patterns:
        return False
    rel_path = rel_path.replace('\\', '/')
    basename = rel_path.rsplit('/', 1)[-1]
    matched = False

    for pat in patterns:
        negate = pat.startswith('!')
        p = pat[1:] if negate else pat
        if not p:
            continue

        dir_only = p.endswith('/')
        if dir_only:
            p = p[:-1]

        anchored = p.startswith('/')
        if anchored:
            p = p[1:]
            hit = fnmatch.fnmatch(rel_path, p) or fnmatch.fnmatch(basename, p)
        else:
            hit = (
                fnmatch.fnmatch(basename, p)
                or fnmatch.fnmatch(rel_path, p)
                or fnmatch.fnmatch(rel_path, f'*/{p}')
            )

        if hit:
            matched = not negate

    return matched


# ==================== 扫描线程（自动忽略 + 可选 gitignore） ====================
class ScanThread(QThread):
    finished_scan = Signal(dict, list)   # {rel: (abs,size)}, extensions list

    def __init__(self, root_path, respect_gitignore=False):
        super().__init__()
        self.root_path = root_path
        self.respect_gitignore = respect_gitignore

    def run(self):
        file_map = {}
        extensions = set()

        gitignore_patterns = (
            load_gitignore_patterns(self.root_path)
            if self.respect_gitignore else []
        )

        for root, dirs, files in os.walk(self.root_path):
            rel_root = os.path.relpath(root, self.root_path).replace('\\', '/')
            if rel_root == '.':
                rel_root = ''

            # 过滤目录
            kept_dirs = []
            for d in dirs:
                if d.startswith('.'):
                    continue
                if d in IGNORE_DIR_NAMES:
                    continue
                rel_dir = f'{rel_root}/{d}' if rel_root else d
                if self.respect_gitignore and is_gitignored(rel_dir, True, gitignore_patterns):
                    continue
                kept_dirs.append(d)
            dirs[:] = kept_dirs

            # 处理文件
            for file in files:
                if file.startswith('.'):
                    continue
                if file in IGNORE_FILE_NAMES:
                    continue
                dot_idx = file.rfind('.')
                if dot_idx != -1:
                    ext_lower = file[dot_idx + 1:].lower()
                    if ext_lower in IGNORE_FILE_EXTENSIONS:
                        continue

                rel_path = f'{rel_root}/{file}' if rel_root else file
                if self.respect_gitignore and is_gitignored(rel_path, False, gitignore_patterns):
                    continue

                abs_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(abs_path)
                except OSError:
                    continue

                file_map[rel_path] = (abs_path, size)
                extensions.add(get_extension(rel_path))

        extensions = sorted(extensions, key=lambda x: (x == '[无后缀]', x))
        self.finished_scan.emit(file_map, extensions)


# ==================== 生成线程（支持中途取消） ====================
class GenerateThread(QThread):
    progress = Signal(str)
    result = Signal(str)
    cancelled = Signal()

    def __init__(self, root_path, selected_paths, file_map, lang, redact_sensitive):
        super().__init__()
        self.root_path = root_path
        self.selected_paths = selected_paths
        self.file_map = file_map
        self.lang = lang
        self.redact_sensitive = redact_sensitive

    def run(self):
        lines = []
        root_name = os.path.basename(self.root_path)
        s = STRINGS[self.lang]

        lines.append(f"# 项目概览：{root_name}\n")
        tree = self._build_tree(self.selected_paths)
        lines.append("## 📁 目录结构\n")
        lines.append("```\n" + tree + "```\n")

        if not self.selected_paths:
            lines.append("*(未选中任何文件)*")
        else:
            lines.append("## 📄 文件内容\n")
            total = len(self.selected_paths)
            for i, rel_path in enumerate(self.selected_paths):
                # ★ 3.4：每处理一个文件前检查中断
                if self.isInterruptionRequested():
                    self.cancelled.emit()
                    return

                self.progress.emit(f"({i + 1}/{total}) {rel_path}")
                abs_path, size = self.file_map[rel_path]

                is_bin, reason = is_binary_file(abs_path)
                if is_bin:
                    lines.append(
                        f"### `{rel_path}`\n```\n{s['binary_skipped'].format(reason)}\n```\n"
                    )
                    continue

                try:
                    content = read_text_file(abs_path)
                    if self.redact_sensitive:
                        content = redact_sensitive_content(content)
                    ext = get_extension(rel_path)
                    lang = ext if ext != '[无后缀]' else ''
                    lines.append(f"### `{rel_path}`\n```{lang}\n{content}\n```\n")
                except Exception as e:
                    lines.append(
                        f"### `{rel_path}`\n```\n{s['read_failed'].format(e)}\n```\n"
                    )

        self.result.emit('\n'.join(lines))

    def _build_tree(self, paths):
        if not paths:
            return f"{os.path.basename(self.root_path)}/\n└── (无选中文件)"

        tree_dict = {}
        for p in paths:
            parts = p.split('/')
            node = tree_dict
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = None

        def _render(subtree, prefix=''):
            if not subtree:
                return ''
            items = list(subtree.items())
            items.sort(key=lambda x: (0 if isinstance(x[1], dict) else 1, x[0].lower()))
            result = ''
            for i, (name, child) in enumerate(items):
                last = (i == len(items) - 1)
                line = prefix + ('└── ' if last else '├── ') + name
                if isinstance(child, dict):
                    line += '/'
                result += line + '\n'
                if isinstance(child, dict):
                    result += _render(child, prefix + ('    ' if last else '│   '))
            return result

        root_name = os.path.basename(self.root_path)
        return root_name + '/\n' + _render(tree_dict)


# ==================== 过滤代理模型 ====================
class FileFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.allowed_extensions = None
        self.search_text = ""

    def set_allowed_extensions(self, exts):
        self.allowed_extensions = set(exts) if exts is not None else None
        self.invalidate()

    def set_search_text(self, text):
        self.search_text = text.strip().lower()
        self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)

        ext = model.data(index, Qt.UserRole)
        if ext is not None and self.allowed_extensions is not None:
            if ext not in self.allowed_extensions:
                if model.hasChildren(index) and self._has_accepted_child(index):
                    return True
                return False

        if self.search_text:
            file_name = model.data(index, Qt.DisplayRole)
            if '(' in file_name and file_name.endswith(')'):
                file_name = file_name[:file_name.rfind('(')].strip()
            if self.search_text not in file_name.lower():
                if model.hasChildren(index) and self._has_accepted_child(index):
                    return True
                return False

        return True

    def _has_accepted_child(self, parent_index):
        model = self.sourceModel()
        for row in range(model.rowCount(parent_index)):
            child_index = model.index(row, 0, parent_index)
            if self.filterAcceptsRow(row, parent_index):
                return True
            if model.hasChildren(child_index) and self._has_accepted_child(child_index):
                return True
        return False


# ==================== 大纲对话框 ====================
class OutlineDialog(QDialog):
    jump_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('📑 文档大纲')
        self.resize(int(320 * UI_BASE_SCALE), int(460 * UI_BASE_SCALE))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_click)
        layout.addWidget(self.list_widget)

    def set_outline(self, items):
        self.list_widget.clear()
        for level, title in items:
            prefix = '    ' * (level - 1)
            mark = '▸ ' if level == 1 else ('· ' if level == 2 else '  ')
            item = QListWidgetItem(prefix + mark + title)
            item.setData(Qt.UserRole, title)
            self.list_widget.addItem(item)

    def _on_click(self, item):
        self.jump_requested.emit(item.data(Qt.UserRole))


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = 'zh'
        self.root_path = None
        self.file_map = {}
        self.selected_paths = []
        self.ext_list = []
        self._updating = False
        self.project_display_name = None          # ★ 1.2
        self.temp_dir = None
        self.outline_dialog = None

        # ★ 3.4：生成线程引用
        self.gen_thread = None
        self.scan_thread = None
        self.progress_dlg = None

        # ★ 2.3：合并 update_selected_size
        self._size_timer = QTimer(self)
        self._size_timer.setSingleShot(True)
        self._size_timer.timeout.connect(self.update_selected_size)

        self.setAcceptDrops(True)

        self.fs_watcher = QFileSystemWatcher(self)
        self.fs_watcher.directoryChanged.connect(self.on_directory_changed)
        self.fs_watcher.fileChanged.connect(self.on_file_changed)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.do_refresh)
        self.pending_refresh = False

        self.setup_ui()
        self.apply_light_theme()
        self.retranslate_ui()

    # ---------- 界面构建 ----------
    def setup_ui(self):
        self.setWindowTitle(STRINGS[self.current_lang]['window_title'])
        self.resize(int(1000 * UI_BASE_SCALE), int(700 * UI_BASE_SCALE))

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # ===== 左侧扩展名面板 =====
        left_panel = QWidget()
        left_panel.setMaximumWidth(int(200 * UI_BASE_SCALE))
        left_layout = QVBoxLayout(left_panel)

        self.ext_filter_label = QLabel()
        left_layout.addWidget(self.ext_filter_label)

        self.ext_list_widget = QListWidget()
        self.ext_list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        left_layout.addWidget(self.ext_list_widget)

        main_layout.addWidget(left_panel)

        # ===== 右侧主区域 =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 顶部工具栏
        top_layout = QHBoxLayout()
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.choose_btn = QPushButton()
        self.choose_btn.clicked.connect(self.choose_folder)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['中文', 'English'])
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)

        top_layout.addWidget(self.path_label, 1)
        top_layout.addWidget(self.choose_btn)
        top_layout.addWidget(QLabel(STRINGS[self.current_lang]['language']))
        top_layout.addWidget(self.lang_combo)
        right_layout.addLayout(top_layout)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_label = QLabel("🔎")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(STRINGS[self.current_lang]['search_placeholder'])
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_edit)
        right_layout.addLayout(search_layout)

        # 文件树标签 + 复选框
        tree_header_layout = QHBoxLayout()
        self.tree_label = QLabel()
        self.tree_label.setObjectName("treeLabel")
        tree_header_layout.addWidget(self.tree_label)

        self.sensitive_checkbox = QCheckBox()
        self.sensitive_checkbox.setObjectName("sensitiveCheckbox")
        tree_header_layout.addWidget(self.sensitive_checkbox)

        # ★ 3.6：尊重 .gitignore，默认开
        self.gitignore_checkbox = QCheckBox()
        self.gitignore_checkbox.setObjectName("gitignoreCheckbox")
        self.gitignore_checkbox.setChecked(True)
        self.gitignore_checkbox.stateChanged.connect(self.on_gitignore_changed)
        tree_header_layout.addWidget(self.gitignore_checkbox)

        tree_header_layout.addStretch()
        right_layout.addLayout(tree_header_layout)

        # 垂直分割器
        splitter = QSplitter(Qt.Vertical)

        # 文件树
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_model = QStandardItemModel()
        self.proxy_model = FileFilterProxy()
        self.proxy_model.setSourceModel(self.tree_model)
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.setSelectionMode(QAbstractItemView.NoSelection)
        tree_layout.addWidget(self.tree_view)
        splitter.addWidget(tree_widget)

        # 输出区
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.setContentsMargins(0, 0, 0, 0)

        # 按钮栏
        info_layout = QHBoxLayout()
        self.size_label = QLabel()

        self.generate_btn = QPushButton()
        self.generate_btn.clicked.connect(self.generate_markdown)
        self.copy_btn = QPushButton()
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.export_md_btn = QPushButton()
        self.export_md_btn.clicked.connect(self.export_markdown)
        self.outline_btn = QPushButton()
        self.outline_btn.clicked.connect(self.show_outline)

        # ★ 2.2：刷新兜底按钮
        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh_now)

        info_layout.addWidget(self.size_label, 1)
        info_layout.addWidget(self.refresh_btn)
        info_layout.addWidget(self.generate_btn)
        info_layout.addWidget(self.copy_btn)
        info_layout.addWidget(self.export_md_btn)
        info_layout.addWidget(self.outline_btn)
        output_layout.addLayout(info_layout)

        # ★ 2.1：QPlainTextEdit
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setFont(
            QFont("Courier New", max(9, int(round(10 * UI_BASE_SCALE))))
        )
        output_layout.addWidget(self.output_edit)
        splitter.addWidget(output_widget)

        splitter.setSizes([
            int(400 * UI_BASE_SCALE),
            int(200 * UI_BASE_SCALE)
        ])
        right_layout.addWidget(splitter)
        main_layout.addWidget(right_panel, 1)

        # 信号
        self.ext_list_widget.itemChanged.connect(self.on_extension_filter_changed)
        self.tree_model.itemChanged.connect(self.on_item_changed)

    # ==================== 浅绿护眼主题 ====================
    def apply_light_theme(self):
        QApplication.setStyle('Fusion')

        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor(232, 245, 233))
        palette.setColor(QPalette.WindowText,      QColor(27, 58, 42))
        palette.setColor(QPalette.Base,            QColor(247, 251, 248))
        palette.setColor(QPalette.AlternateBase,   QColor(236, 248, 240))
        palette.setColor(QPalette.ToolTipBase,     QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText,     QColor(27, 58, 42))
        palette.setColor(QPalette.Text,            QColor(27, 58, 42))
        palette.setColor(QPalette.Button,          QColor(200, 230, 201))
        palette.setColor(QPalette.ButtonText,      QColor(27, 58, 42))
        palette.setColor(QPalette.BrightText,      Qt.red)
        palette.setColor(QPalette.Highlight,       QColor(102, 187, 106))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)

        def px(n):
            return max(1, int(round(n * UI_BASE_SCALE)))

        def pt(n):
            return max(6, int(round(n * UI_BASE_SCALE)))

        font = QFont()
        font.setFamily('Microsoft YaHei' if sys.platform == 'win32' else 'Segoe UI')
        font.setPointSizeF(10 * UI_BASE_SCALE)
        QApplication.setFont(font)

        self.setStyleSheet(f"""
            QWidget {{ color: #1B3A2A; }}
            QTreeView {{
                background-color: #F7FBF8;
                alternate-background-color: #ECF8F0;
                color: #1B3A2A;
                selection-background-color: #66BB6A;
                selection-color: white;
                border: 1px solid #B2DFC0;
                border-radius: {px(4)}px;
                font-size: {pt(10)}pt;
            }}
            QTreeView::item {{ padding: {px(2)}px {px(4)}px; }}
            QTreeView::item:hover {{ background-color: #DDF0E2; }}
            QTreeView::item:selected {{ background-color: #66BB6A; color: white; }}
            QListWidget {{
                background-color: #F7FBF8;
                color: #1B3A2A;
                border: 1px solid #B2DFC0;
                border-radius: {px(4)}px;
                outline: none;
                font-size: {pt(10)}pt;
            }}
            QListWidget::item {{ padding: {px(3)}px {px(4)}px; }}
            QListWidget::item:hover {{ background-color: #DDF0E2; }}
            QListWidget::item:selected {{ background-color: #66BB6A; color: white; }}
            QPlainTextEdit {{
                background-color: #F7FBF8;
                color: #1B3A2A;
                border: 1px solid #B2DFC0;
                border-radius: {px(4)}px;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: {pt(10)}pt;
                selection-background-color: #A5D6A7;
                selection-color: #1B3A2A;
            }}
            QPushButton {{
                background-color: #C8E6C9;
                color: #1B3A2A;
                border: 1px solid #A5D6A7;
                padding: {px(6)}px {px(14)}px;
                font-size: {pt(11)}pt;
                border-radius: {px(4)}px;
            }}
            QPushButton:hover {{ background-color: #A5D6A7; border-color: #81C784; }}
            QPushButton:pressed {{ background-color: #81C784; }}
            QPushButton:disabled {{ background-color: #E8F5E9; color: #9CBBA5; border-color: #C8E6C9; }}
            QLineEdit {{
                background-color: #FFFFFF;
                color: #1B3A2A;
                border: 1px solid #B2DFC0;
                padding: {px(4)}px {px(6)}px;
                border-radius: {px(4)}px;
                font-size: {pt(10)}pt;
                selection-background-color: #A5D6A7;
                selection-color: #1B3A2A;
            }}
            QLineEdit:focus {{ border: 1px solid #66BB6A; }}
            QLabel {{ color: #1B3A2A; font-size: {pt(10)}pt; }}
            #treeLabel {{ font-size: {pt(11)}pt; font-weight: bold; }}
            #sensitiveCheckbox {{ font-size: {pt(10)}pt; }}
            #gitignoreCheckbox {{ font-size: {pt(10)}pt; }}
            QComboBox {{
                background-color: #FFFFFF;
                color: #1B3A2A;
                border: 1px solid #B2DFC0;
                padding: {px(3)}px {px(6)}px;
                border-radius: {px(4)}px;
                font-size: {pt(10)}pt;
                min-width: {px(60)}px;
            }}
            QComboBox::drop-down {{ border: none; width: {px(20)}px; }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                color: #1B3A2A;
                selection-background-color: #66BB6A;
                selection-color: white;
                border: 1px solid #B2DFC0;
                outline: none;
            }}
            QCheckBox {{ color: #1B3A2A; spacing: {px(6)}px; }}
            QCheckBox::indicator {{
                width: {px(14)}px;
                height: {px(14)}px;
                border: 1px solid #A5D6A7;
                border-radius: {px(3)}px;
                background-color: #FFFFFF;
            }}
            QCheckBox::indicator:checked {{ background-color: #66BB6A; border-color: #4CAF50; }}
            QProgressDialog {{ background-color: #E8F5E9; }}
            QProgressDialog QLabel {{ color: #1B3A2A; }}
            QMessageBox {{ background-color: #E8F5E9; }}
            QMessageBox QLabel {{ color: #1B3A2A; }}
            QSplitter::handle {{ background-color: #DDF0E2; height: {px(4)}px; }}
            QScrollBar:vertical {{
                background: #ECF8F0;
                width: {px(10)}px;
                border-radius: {px(5)}px;
            }}
            QScrollBar::handle:vertical {{
                background: #A5D6A7;
                border-radius: {px(5)}px;
                min-height: {px(24)}px;
            }}
            QScrollBar::handle:vertical:hover {{ background: #81C784; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: #ECF8F0;
                height: {px(10)}px;
                border-radius: {px(5)}px;
            }}
            QScrollBar::handle:horizontal {{
                background: #A5D6A7;
                border-radius: {px(5)}px;
                min-width: {px(24)}px;
            }}
        """)

    def retranslate_ui(self):
        s = STRINGS[self.current_lang]
        self.setWindowTitle(s['window_title'])
        self.ext_filter_label.setText(s['ext_filter'])
        self.tree_label.setText(s['file_tree'])
        self.choose_btn.setText(s['choose_folder'])
        self.path_label.setText(s['no_folder'] if not self.root_path else self.root_path)
        self.generate_btn.setText(s['generate'])
        self.copy_btn.setText(s['copy'])
        self.export_md_btn.setText(s['export_md'])
        self.outline_btn.setText(s['outline'])
        self.refresh_btn.setText(s['refresh'])
        self.search_edit.setPlaceholderText(s['search_placeholder'])
        self.size_label.setText(s['size_label'].format("0 B"))
        self.sensitive_checkbox.setText(s['sensitive_filter'])
        self.gitignore_checkbox.setText(s['gitignore'])

    def on_language_changed(self, index):
        self.current_lang = 'zh' if index == 0 else 'en'
        self.retranslate_ui()

    # ==================== 拖拽支持 ====================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if not path or not os.path.exists(path):
            return
        event.acceptProposedAction()

        s = STRINGS[self.current_lang]
        if os.path.isdir(path):
            self.load_folder(path)
        elif os.path.isfile(path):
            lower = path.lower()
            if lower.endswith(('.zip', '.tar', '.gz', '.tgz', '.tar.gz', '.gzip')):
                self.load_archive(path)
            else:
                QMessageBox.warning(self, s['warning'], s['drop_hint'])
        else:
            QMessageBox.warning(self, s['warning'], s['drop_hint'])

    # ==================== 文件夹 / 压缩包 ====================
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, STRINGS[self.current_lang]['choose_folder']
        )
        if not folder:
            return
        self.load_folder(folder)

    def load_folder(self, path):
        self.root_path = path
        self.project_display_name = None        # ★ 1.2：普通文件夹走目录名
        self.path_label.setText(path)
        self.setup_file_watcher()
        self.start_scan()

    def load_archive(self, archive_path):
        s = STRINGS[self.current_lang]
        try:
            if self.temp_dir is not None:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = tempfile.mkdtemp(prefix='repo2md_')

            # ★ 1.2：记录原始压缩包名，用于导出文件名
            name = os.path.basename(archive_path)
            for suffix in ('.tar.gz', '.tgz', '.zip', '.tar', '.gz'):
                if name.lower().endswith(suffix):
                    name = name[:-len(suffix)]
                    break
            self.project_display_name = name

            lower = archive_path.lower()
            if lower.endswith('.zip'):
                self._safe_extract_zip(archive_path, self.temp_dir)
            elif lower.endswith(('.tar', '.tar.gz', '.tgz', '.gz')):
                self._safe_extract_tar(archive_path, self.temp_dir)
            else:
                raise ValueError(s['unsupported_archive'])

            entries = [e for e in os.listdir(self.temp_dir) if not e.startswith('.')]
            if len(entries) == 1 and os.path.isdir(os.path.join(self.temp_dir, entries[0])):
                root = os.path.join(self.temp_dir, entries[0])
            else:
                root = self.temp_dir

            self.load_folder(root)
            # load_folder 会清空 project_display_name，此处恢复
            self.project_display_name = name
        except Exception as e:
            QMessageBox.critical(self, s['error'], s['extract_failed'].format(e))

    def _safe_extract_zip(self, path, dest):
        base = os.path.realpath(dest) + os.sep
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                target = os.path.realpath(os.path.join(dest, name))
                if not target.startswith(base):
                    raise ValueError(f'不安全路径：{name}')
            zf.extractall(dest)

    def _safe_extract_tar(self, path, dest):
        # ★ 1.4：Python 3.12+ 用 filter='data'，否则手动过滤 symlink/hardlink
        with tarfile.open(path) as tf:
            if hasattr(tarfile, 'data_filter'):
                tf.extractall(dest, filter='data')
                return
            base = os.path.realpath(dest) + os.sep
            safe_members = []
            for member in tf.getmembers():
                if member.issym() or member.islnk():
                    continue
                target = os.path.realpath(os.path.join(dest, member.name))
                if not target.startswith(base):
                    raise ValueError(f'不安全路径：{member.name}')
                safe_members.append(member)
            tf.extractall(dest, members=safe_members)

    def closeEvent(self, event):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().closeEvent(event)

    # ==================== 文件监视（★ 2.2 只监根 + 一级） ====================
    def setup_file_watcher(self):
        if not self.root_path:
            return
        if self.fs_watcher.directories():
            self.fs_watcher.removePaths(self.fs_watcher.directories())
        if self.fs_watcher.files():
            self.fs_watcher.removePaths(self.fs_watcher.files())

        # 根目录
        try:
            self.fs_watcher.addPath(self.root_path)
        except Exception:
            pass

        # 一级子目录（最多 ~50 个，不会触及句柄上限）
        try:
            for entry in os.scandir(self.root_path):
                if entry.is_dir() \
                        and not entry.name.startswith('.') \
                        and entry.name not in IGNORE_DIR_NAMES:
                    try:
                        self.fs_watcher.addPath(entry.path)
                    except Exception:
                        pass
        except Exception:
            pass

    def on_directory_changed(self, path):
        if self.root_path and os.path.exists(self.root_path):
            self.pending_refresh = True
            self.refresh_timer.start(500)

    def on_file_changed(self, path):
        self.on_directory_changed(path)

    def do_refresh(self):
        if not self.pending_refresh:
            return
        self.pending_refresh = False
        self.refresh_now()

    def refresh_now(self):
        if not self.root_path:
            return
        old_selected = self.selected_paths.copy()
        self.start_scan(restore_selected=old_selected)

    def on_gitignore_changed(self, state):
        # ★ 3.6：切换 .gitignore 开关时重新扫描
        if not self.root_path:
            return
        old_selected = self.selected_paths.copy()
        self.start_scan(restore_selected=old_selected)

    # ==================== 扫描 ====================
    def start_scan(self, restore_selected=None):
        if not self.root_path:
            return
        if self.scan_thread is not None and self.scan_thread.isRunning():
            return

        self.progress_dlg = QProgressDialog(
            STRINGS[self.current_lang]['scanning'],
            None, 0, 0, self
        )
        self.progress_dlg.setWindowModality(Qt.WindowModal)
        self.progress_dlg.show()

        respect = self.gitignore_checkbox.isChecked()
        self.scan_thread = ScanThread(self.root_path, respect_gitignore=respect)
        self.scan_thread.finished_scan.connect(
            lambda fm, ext: self.on_scan_finished(fm, ext, restore_selected)
        )
        self.scan_thread.start()

    def on_scan_finished(self, file_map, extensions, restore_selected=None):
        if self.progress_dlg:
            self.progress_dlg.close()

        self.file_map = file_map
        self.ext_list = extensions

        self.tree_model.clear()
        self.ext_list_widget.clear()
        self.build_tree_model()

        for ext in extensions:
            item = QListWidgetItem(ext)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.ext_list_widget.addItem(item)

        self.proxy_model.set_allowed_extensions(extensions)

        if restore_selected:
            self.restore_selected_paths(restore_selected)
        else:
            self.update_selected_size()

    def restore_selected_paths(self, paths):
        root = self.tree_model.invisibleRootItem()
        self._set_all_checked(root, False)
        for rel_path in paths:
            self._check_path(rel_path)
        self.update_selected_size()
        root = self.tree_model.invisibleRootItem()
        self._update_parent_tristate(root)

    def _set_all_checked(self, parent_item, checked):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row)
            if child.hasChildren():
                self._set_all_checked(child, checked)
            else:
                child.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def _check_path(self, rel_path):
        parts = rel_path.split('/')
        current = self.tree_model.invisibleRootItem()
        for part in parts:
            found = None
            for row in range(current.rowCount()):
                child = current.child(row)
                display = child.data(Qt.DisplayRole)
                if display.startswith(part + '/') or display.startswith(part + ' ('):
                    found = child
                    break
            if not found:
                return
            current = found
        if current and not current.hasChildren():
            current.setCheckState(Qt.Checked)

    # ==================== 构建树模型 ====================
    def build_tree_model(self):
        root_name = os.path.basename(self.root_path)
        root_item = QStandardItem(root_name + '/')
        root_item.setEditable(False)
        root_item.setCheckable(True)
        root_item.setData(None, Qt.UserRole)
        self.tree_model.appendRow(root_item)

        path_to_item = {'': root_item}

        all_paths = list(self.file_map.keys())
        dirs = set()
        for p in all_paths:
            parts = p.split('/')
            for i in range(1, len(parts)):
                dirs.add('/'.join(parts[:i]))

        for d in sorted(dirs, key=lambda x: (x.count('/'), x)):
            if d in path_to_item:
                continue
            parts = d.split('/')
            parent_path = '/'.join(parts[:-1])
            parent_item = path_to_item.get(parent_path, root_item)
            dir_item = QStandardItem(parts[-1] + '/')
            dir_item.setEditable(False)
            dir_item.setCheckable(True)
            dir_item.setData(None, Qt.UserRole)
            parent_item.appendRow(dir_item)
            path_to_item[d] = dir_item

        for rel_path, (abs_path, size) in self.file_map.items():
            parts = rel_path.split('/')
            parent_path = '/'.join(parts[:-1])
            parent_item = path_to_item.get(parent_path, root_item)
            file_name = parts[-1]
            display_text = f"{file_name} ({format_bytes(size)})"
            file_item = QStandardItem(display_text)
            file_item.setEditable(False)
            file_item.setCheckable(True)
            file_item.setData(get_extension(rel_path), Qt.UserRole)
            file_item.setData(rel_path, Qt.UserRole + 1)
            file_item.setData(size, Qt.UserRole + 2)
            parent_item.appendRow(file_item)

        self.tree_view.expandToDepth(1)

    # ==================== 扩展名筛选 ====================
    def on_extension_filter_changed(self, item):
        allowed = []
        for i in range(self.ext_list_widget.count()):
            it = self.ext_list_widget.item(i)
            if it.checkState() == Qt.Checked:
                allowed.append(it.text())
        self.proxy_model.set_allowed_extensions(allowed if allowed else None)

    # ==================== 搜索 ====================
    def on_search_text_changed(self, text):
        self.proxy_model.set_search_text(text)

    # ==================== 勾选联动（★ 2.3） ====================
    def on_item_changed(self, item):
        if self._updating:
            return
        self._updating = True

        if item.hasChildren():
            self._set_children_state(item, item.checkState())

        parent = item.parent()
        if parent:
            self._update_parent_tristate(parent)
        else:
            self._update_parent_tristate(self.tree_model.invisibleRootItem())

        self._updating = False

        # 合并连续勾选（50ms 内的多次变更只算一次）
        if not self._size_timer.isActive():
            self._size_timer.start(50)

    def _set_children_state(self, parent_item, state):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row)
            if child.isCheckable():
                child.setCheckState(state)
            if child.hasChildren():
                self._set_children_state(child, state)

    def _update_parent_tristate(self, parent_item):
        if not parent_item.hasChildren():
            return

        checked_count = 0
        unchecked_count = 0
        partially_count = 0
        total = 0

        for row in range(parent_item.rowCount()):
            child = parent_item.child(row)
            if not child.isCheckable():
                continue
            total += 1
            state = child.checkState()
            if state == Qt.Checked:
                checked_count += 1
            elif state == Qt.Unchecked:
                unchecked_count += 1
            else:
                partially_count += 1

        if total == 0:
            return

        if partially_count > 0 or (checked_count > 0 and unchecked_count > 0):
            new_state = Qt.PartiallyChecked
        elif checked_count == total:
            new_state = Qt.Checked
        else:
            new_state = Qt.Unchecked

        # ★ 2.3：状态未变 → 祖先状态也不会变，提前终止
        if parent_item.checkState() == new_state:
            return
        parent_item.setCheckState(new_state)

        grand_parent = parent_item.parent()
        if grand_parent:
            self._update_parent_tristate(grand_parent)
        else:
            root = self.tree_model.invisibleRootItem()
            if root != parent_item:
                self._update_parent_tristate(root)

    def update_selected_size(self):
        self.selected_paths = []
        root = self.tree_model.invisibleRootItem()
        total = self._accumulate_selected(root, self.selected_paths)
        s = STRINGS[self.current_lang]
        self.size_label.setText(s['size_label'].format(format_bytes(total)))

    def _accumulate_selected(self, parent_item, paths):
        total = 0
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row)
            if child.hasChildren():
                total += self._accumulate_selected(child, paths)
            else:
                if child.checkState() == Qt.Checked:
                    total += child.data(Qt.UserRole + 2)
                    rel_path = child.data(Qt.UserRole + 1)
                    if rel_path:
                        paths.append(rel_path)
        return total

    # ==================== 生成 Markdown ====================
    def generate_markdown(self):
        s = STRINGS[self.current_lang]
        if not self.selected_paths:
            QMessageBox.warning(self, s['warning'], s['no_selection'])
            return

        # 敏感文件提示
        sensitive = [
            p for p in self.selected_paths
            if any(k in p.lower() for k in SENSITIVE_KEYWORDS)
        ]
        if sensitive:
            msg = s['sensitive_warning'].format("\n".join(sensitive[:5]))
            reply = QMessageBox.question(
                self, s['warning'], msg,
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # ★ 3.3：生成前 token 预估
        total_bytes = sum(
            self.file_map[p][1]
            for p in self.selected_paths
            if p in self.file_map
        )
        est_tokens = total_bytes // 4
        if est_tokens > 128000:
            reply = QMessageBox.question(
                self, s['warning'],
                s['token_estimate_warning'].format(est_tokens),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # ★ 3.4：可取消进度对话框
        self.progress_dlg = QProgressDialog(
            s['generating'], s['cancel'], 0, 0, self
        )
        self.progress_dlg.setWindowModality(Qt.WindowModal)
        self.progress_dlg.setMinimumDuration(0)
        self.progress_dlg.show()

        self.gen_thread = GenerateThread(
            self.root_path,
            self.selected_paths,
            self.file_map,
            self.current_lang,
            self.sensitive_checkbox.isChecked()
        )
        self.gen_thread.progress.connect(self.on_generate_progress)
        self.gen_thread.result.connect(self.on_generate_finished)
        self.gen_thread.cancelled.connect(self.on_generate_cancelled)
        self.progress_dlg.canceled.connect(self.gen_thread.requestInterruption)
        self.gen_thread.start()

    def on_generate_progress(self, msg):
        if self.progress_dlg:
            self.progress_dlg.setLabelText(msg)

    def on_generate_finished(self, markdown):
        if self.progress_dlg:
            self.progress_dlg.close()
        if not markdown:
            return
        self.output_edit.setPlainText(markdown)

        token_count = estimate_tokens(markdown)
        if token_count > 128000:
            s = STRINGS[self.current_lang]
            QMessageBox.warning(
                self, s['warning'],
                s['token_warning'].format(token_count),
                QMessageBox.Ok
            )

    def on_generate_cancelled(self):
        if self.progress_dlg:
            self.progress_dlg.close()

    # ==================== 大纲 ====================
    def show_outline(self):
        s = STRINGS[self.current_lang]
        markdown = self.output_edit.toPlainText()
        if not markdown.strip():
            QMessageBox.information(self, s['warning'], s['no_content'])
            return

        items = []
        for line in markdown.splitlines():
            m = re.match(r'^(#{1,6})\s+(.+)$', line)
            if m:
                items.append((len(m.group(1)), m.group(2).strip()))

        if not items:
            QMessageBox.information(self, s['warning'], s['no_heading'])
            return

        if self.outline_dialog is None:
            self.outline_dialog = OutlineDialog(self)
            self.outline_dialog.jump_requested.connect(self.jump_to_heading)

        self.outline_dialog.set_outline(items)
        self.outline_dialog.show()
        self.outline_dialog.raise_()
        self.outline_dialog.activateWindow()

    def jump_to_heading(self, title):
        cursor = self.output_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.output_edit.setTextCursor(cursor)
        if self.output_edit.find(title):
            cursor = self.output_edit.textCursor()
            self.output_edit.setTextCursor(cursor)
            self.output_edit.ensureCursorVisible()
        else:
            s = STRINGS[self.current_lang]
            QMessageBox.information(
                self, s['warning'], s['heading_not_found'].format(title)
            )

    # ==================== 复制 / 导出 ====================
    def copy_to_clipboard(self):
        text = self.output_edit.toPlainText()
        s = STRINGS[self.current_lang]
        if not text.strip():
            QMessageBox.warning(self, s['warning'], s['no_content'])
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, s['warning'], s['copy_success'])

    def _default_filename(self, ext):
        # ★ 1.2：优先使用原始压缩包名，否则用目录名
        base = self.project_display_name \
            or (os.path.basename(self.root_path) if self.root_path else 'project')
        date_str = datetime.now().strftime('%Y%m%d')
        return f"{base}_{date_str}.{ext}"

    def export_markdown(self):
        text = self.output_edit.toPlainText()
        s = STRINGS[self.current_lang]
        if not text.strip():
            QMessageBox.warning(self, s['warning'], s['no_content'])
            return
        default_name = self._default_filename('md')
        file_path, _ = QFileDialog.getSaveFileName(
            self, s['export_md'], default_name, "Markdown (*.md)"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            QMessageBox.information(
                self, s['warning'], s['export_success'].format(file_path)
            )


# ==================== 启动 ====================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())