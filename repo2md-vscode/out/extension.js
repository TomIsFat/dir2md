"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs/promises"));
const path = __importStar(require("path"));
const crypto = __importStar(require("crypto"));
const iconv_lite_1 = __importDefault(require("iconv-lite"));
const ignore_1 = __importDefault(require("ignore"));
// ==================== 常量 ====================
const BINARY_EXTENSIONS = new Set([
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico', 'webp',
    'mp4', 'mp3', 'avi', 'mov', 'wmv', 'flv',
    'pdf', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip', 'rar', '7z', 'tar', 'gz',
    'exe', 'dll', 'so', 'dylib',
    'iso', 'img',
    'woff', 'woff2', 'ttf', 'eot',
    'psd', 'ai', 'eps',
    'bin', 'dat', 'db', 'sqlite', 'cur', 'icns',
]);
const IGNORED_DIRECTORIES = new Set([
    '.git', '.svn', '.hg', '.cvs',
    'node_modules', 'bower_components', 'jspm_packages', 'composer', 'vendor', 'packages',
    'out', 'dist', 'build', 'target', 'bin', 'obj', 'output', 'release', 'debug',
    '.cache', 'cache', 'tmp', 'temp', 'log', 'logs',
    'coverage', '.nyc_output',
    '.parcel-cache', '.cache-loader',
    '.serverless', '.serverless_nextjs',
    '.pytest_cache', '.mypy_cache', '.ipynb_checkpoints',
    '.sass-cache', '.scannerwork', '.sonar', '.trunk',
    '.docusaurus', '.expo',
    '.vscode', '.idea', '.vs', '.history', '.settings',
    '.project', '.classpath', '.factorypath',
    '.recommenders', '.sts4-cache', '.vertx', '.mvn',
    '.next', '.nuxt', '.output', '.vercel', '.netlify', '.now',
    '.dart_tool', '.packages', '.pub-cache',
    '.gradle', '.m2', '.ivy2', '.terraform',
    '.venv', 'venv', 'env', '__pycache__', '.hypothesis',
    '.spyderproject', '.spyproject', '.ropeproject',
    '.flutter-plugins', '.flutter-plugins-dependencies',
    '.trash', '.recycle', '.backup',
]);
const MAX_SCAN_DEPTH = 200;
const SENSITIVE_PATTERNS = [
    [/(password|passwd|pwd)\s*[=:]\s*\S+/gi, '$1 = [REDACTED]'],
    [/(api[_-]?key|secret|token)\s*[=:]\s*\S+/gi, '$1 = [REDACTED]'],
    [
        /-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----[\s\S]*?-----END \1 PRIVATE KEY-----/g,
        '[REDACTED PRIVATE KEY]',
    ],
    [/[A-Za-z0-9+/]{80,}={1,2}/g, '[REDACTED BASE64]'],
];
const I18N = {
    zh: {
        // 扩展侧
        openFolderFirst: '请先打开一个文件夹或工作区',
        scanning: '扫描项目 {0} 中...',
        readingTree: '读取目录结构...',
        scanFailed: '扫描失败: {0}',
        refreshFailed: '自动刷新失败: {0}',
        noFileSelected: '未选中任何文件',
        tokenWarning: '预计约 {0} tokens（{1} 个文件，{2}），可能超出模型上下文限制。是否继续？',
        continueLabel: '继续',
        cancelLabel: '取消',
        generatingTitle: '生成 Markdown ({0})',
        redactedCount: '已自动替换 {0} 个文件中的敏感信息为 [REDACTED]',
        genCancelled: '已取消生成',
        noContentToExport: '没有可导出的内容',
        exportSuccess: '导出成功: {0}',
        exportFailed: '导出失败: {0}',
        binarySkipped: '[二进制文件，已跳过]',
        readFailed: '[读取失败: {0}]',
        // webview 文案
        appTitle: '📘 项目转 Markdown',
        loadingProject: '正在加载项目...',
        projectLabel: '项目: {0}',
        selectAll: '全选',
        selectNone: '清空',
        invert: '反选',
        selectCode: '只选代码',
        searchPlaceholder: '🔎 搜索文件名或路径...',
        extFilter: '后缀筛选',
        selectedInfo: '📦 选中 {0} 个文件 ({1})',
        generateBtn: '生成 Markdown',
        copyBtn: '📋 复制',
        exportBtn: '💾 导出 .md',
        tocBtn: '📑 大纲',
        tocTitle: '📑 大纲',
        placeholder: 'Markdown 会显示在这里...',
        preparing: '准备中...',
        progressTemplate: '⏳ ({0}/{1}) {2}',
        pleaseSelectFile: '请至少勾选一个文件',
        sensitiveConfirm: '⚠️ 选中的文件可能包含敏感信息（已启用自动替换）。是否继续？',
        copied: '✅ 已复制到剪贴板',
        copyFailed: '❌ 复制失败',
        generateFirst: '请先生成内容',
        generateFirstMd: '请先生成 Markdown',
        noHeadings: '当前文档没有标题',
    },
    en: {
        openFolderFirst: 'Please open a folder or workspace first',
        scanning: 'Scanning {0}...',
        readingTree: 'Reading directory structure...',
        scanFailed: 'Scan failed: {0}',
        refreshFailed: 'Auto-refresh failed: {0}',
        noFileSelected: 'No files selected',
        tokenWarning: 'Estimated ~{0} tokens ({1} files, {2}), which may exceed model context limit. Continue?',
        continueLabel: 'Continue',
        cancelLabel: 'Cancel',
        generatingTitle: 'Generating Markdown ({0})',
        redactedCount: 'Auto-redacted sensitive info in {0} files as [REDACTED]',
        genCancelled: 'Generation cancelled',
        noContentToExport: 'No content to export',
        exportSuccess: 'Exported: {0}',
        exportFailed: 'Export failed: {0}',
        binarySkipped: '[Binary file, skipped]',
        readFailed: '[Read failed: {0}]',
        appTitle: '📘 Repo to Markdown',
        loadingProject: 'Loading project...',
        projectLabel: 'Project: {0}',
        selectAll: 'Select All',
        selectNone: 'Clear',
        invert: 'Invert',
        selectCode: 'Code only',
        searchPlaceholder: '🔎 Search file name or path...',
        extFilter: 'Extension filter',
        selectedInfo: '📦 Selected {0} files ({1})',
        generateBtn: 'Generate Markdown',
        copyBtn: '📋 Copy',
        exportBtn: '💾 Export .md',
        tocBtn: '📑 Outline',
        tocTitle: '📑 Outline',
        placeholder: 'Markdown will appear here...',
        preparing: 'Preparing...',
        progressTemplate: '⏳ ({0}/{1}) {2}',
        pleaseSelectFile: 'Please select at least one file',
        sensitiveConfirm: '⚠️ Selected files may contain sensitive information (auto-redaction enabled). Continue?',
        copied: '✅ Copied to clipboard',
        copyFailed: '❌ Copy failed',
        generateFirst: 'Please generate content first',
        generateFirstMd: 'Please generate Markdown first',
        noHeadings: 'Current document has no headings',
    },
};
function detectLang() {
    const lang = (vscode.env.language || 'en').toLowerCase();
    return lang.startsWith('zh') ? 'zh' : 'en';
}
function t(lang, key, ...args) {
    let s = I18N[lang][key] ?? key;
    args.forEach((a, i) => {
        s = s.split(`{${i}}`).join(String(a));
    });
    return s;
}
// ==================== 工具函数 ====================
function getExtension(filePath) {
    const parts = filePath.split('/');
    const fileName = parts[parts.length - 1];
    const dotIndex = fileName.lastIndexOf('.');
    return dotIndex === -1 ? '[无后缀]' : fileName.substring(dotIndex + 1).toLowerCase();
}
function formatBytes(bytes) {
    if (bytes === 0)
        return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
function estimateTokens(totalBytes) {
    return Math.floor(totalBytes / 3.5);
}
function redactSensitive(content) {
    let result = content;
    for (const [pattern, replacement] of SENSITIVE_PATTERNS) {
        result = result.replace(pattern, replacement);
    }
    return result;
}
function simpleHash(s) {
    return crypto.createHash('md5').update(s).digest('hex').substring(0, 16);
}
async function pMap(items, mapper, concurrency = 20) {
    const results = new Array(items.length);
    let cursor = 0;
    const workers = Array(Math.min(concurrency, items.length || 1))
        .fill(0)
        .map(async () => {
        while (true) {
            const i = cursor++;
            if (i >= items.length)
                break;
            results[i] = await mapper(items[i]);
        }
    });
    await Promise.all(workers);
    return results;
}
// ==================== .gitignore ====================
async function loadGitignore(rootPath) {
    const ig = (0, ignore_1.default)();
    ig.add(['node_modules/', '.git/', '.svn/', '.hg/']);
    try {
        const gitignoreUri = vscode.Uri.file(path.join(rootPath, '.gitignore'));
        const data = await vscode.workspace.fs.readFile(gitignoreUri);
        ig.add(Buffer.from(data).toString('utf-8'));
    }
    catch {
        // ignore
    }
    return ig;
}
// ==================== 扫描 ====================
async function scanLocal(dirPath, basePath, ig, depth) {
    if (depth > MAX_SCAN_DEPTH)
        return [];
    let entries;
    try {
        entries = await fs.readdir(dirPath, { withFileTypes: true });
    }
    catch {
        return [];
    }
    const results = [];
    for (const entry of entries) {
        if (entry.isSymbolicLink())
            continue;
        const fullPath = path.join(dirPath, entry.name);
        const relPath = path.relative(basePath, fullPath).replace(/\\/g, '/');
        if (entry.isDirectory()) {
            if (IGNORED_DIRECTORIES.has(entry.name))
                continue;
            if (ig.ignores(relPath + '/'))
                continue;
            const sub = await scanLocal(fullPath, basePath, ig, depth + 1);
            results.push(...sub);
        }
        else if (entry.isFile()) {
            if (ig.ignores(relPath))
                continue;
            try {
                const stat = await fs.stat(fullPath);
                results.push({ path: relPath, size: stat.size });
            }
            catch {
                // ignore
            }
        }
    }
    return results;
}
async function scanRemote(rootPath, ig) {
    const excludeGlob = '{' + [
        '**/node_modules/**',
        '**/.git/**',
        '**/.svn/**',
        '**/.hg/**',
        '**/__pycache__/**',
        '**/.venv/**',
        '**/dist/**',
        '**/build/**',
        '**/out/**',
        '**/target/**',
        '**/coverage/**',
        '**/.next/**',
    ].join(',') + '}';
    const uris = await vscode.workspace.findFiles(new vscode.RelativePattern(rootPath, '**/*'), excludeGlob, 100000);
    const rootUri = vscode.Uri.file(rootPath);
    const rootPrefix = rootUri.fsPath + '/';
    const collected = [];
    await pMap(uris, async (uri) => {
        const rel = uri.fsPath.substring(rootPrefix.length).replace(/\\/g, '/');
        if (!rel)
            return;
        if (ig.ignores(rel))
            return;
        try {
            const stat = await vscode.workspace.fs.stat(uri);
            collected.push({ path: rel, size: stat.size });
        }
        catch {
            // ignore
        }
    }, 30);
    return collected;
}
async function scanFiles(rootPath) {
    const config = vscode.workspace.getConfiguration('repo2md');
    const respectGitignore = config.get('respectGitignore', true);
    const ig = respectGitignore
        ? await loadGitignore(rootPath)
        : (0, ignore_1.default)().add(['node_modules/', '.git/']);
    if (vscode.env.remoteName)
        return await scanRemote(rootPath, ig);
    return await scanLocal(rootPath, rootPath, ig, 0);
}
async function isBinaryFile(uri, filePath) {
    const ext = getExtension(filePath);
    if (BINARY_EXTENSIONS.has(ext))
        return true;
    if (vscode.env.remoteName)
        return false;
    try {
        const fd = await fs.open(uri.fsPath, 'r');
        const buffer = Buffer.alloc(4);
        const { bytesRead } = await fd.read(buffer, 0, 4, 0);
        await fd.close();
        if (bytesRead < 4)
            return false;
        if (buffer[0] === 0x25 && buffer[1] === 0x50 && buffer[2] === 0x44 && buffer[3] === 0x46)
            return true;
        if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47)
            return true;
        if (buffer[0] === 0xFF && buffer[1] === 0xD8 && buffer[2] === 0xFF)
            return true;
        if (buffer[0] === 0x50 && buffer[1] === 0x4B)
            return true;
        if (buffer[0] === 0x1F && buffer[1] === 0x8B)
            return true;
        if (buffer[0] === 0x7F && buffer[1] === 0x45 && buffer[2] === 0x4C && buffer[3] === 0x46)
            return true;
        if (buffer[0] === 0x4D && buffer[1] === 0x5A)
            return true;
    }
    catch {
        return true;
    }
    return false;
}
async function readFileBuffer(uri) {
    if (vscode.env.remoteName) {
        const data = await vscode.workspace.fs.readFile(uri);
        return Buffer.from(data);
    }
    return await fs.readFile(uri.fsPath);
}
async function readTextFile(uri) {
    const buf = await readFileBuffer(uri);
    if (buf.length >= 2 && buf[0] === 0xFF && buf[1] === 0xFE)
        return buf.toString('utf16le');
    if (buf.length >= 2 && buf[0] === 0xFE && buf[1] === 0xFF)
        return iconv_lite_1.default.decode(buf, 'utf16-be');
    try {
        return new TextDecoder('utf-8', { fatal: true }).decode(buf);
    }
    catch {
        return iconv_lite_1.default.decode(buf, 'gb18030');
    }
}
function generateDirectoryTree(files, rootName) {
    const tree = {};
    files.forEach((filePath) => {
        const parts = filePath.split('/');
        let current = tree;
        parts.forEach((part, idx) => {
            if (!current[part])
                current[part] = { __children: {} };
            if (idx === parts.length - 1)
                current[part].__file = true;
            current = current[part].__children;
        });
    });
    function buildTreeString(node, prefix = '') {
        const entries = Object.entries(node).sort(([aName, aData], [bName, bData]) => {
            const aIsDir = !aData.__file;
            const bIsDir = !bData.__file;
            if (aIsDir !== bIsDir)
                return aIsDir ? -1 : 1;
            return aName.localeCompare(bName, undefined, { sensitivity: 'base' });
        });
        let result = '';
        entries.forEach(([name, data], index) => {
            const isLastEntry = index === entries.length - 1;
            const hasChildren = Object.keys(data.__children || {}).length > 0;
            const isFile = !!data.__file;
            result += prefix + (isLastEntry ? '└── ' : '├── ') + name;
            if (!isFile && hasChildren)
                result += '/';
            result += '\n';
            if (hasChildren) {
                const childPrefix = prefix + (isLastEntry ? '    ' : '│   ');
                result += buildTreeString(data.__children, childPrefix);
            }
        });
        return result;
    }
    let treeString = `${rootName}/\n`;
    if (files.length === 0) {
        treeString += '└── (无选中文件)\n';
    }
    else {
        treeString += buildTreeString(tree, '');
    }
    return treeString;
}
// ==================== 激活入口 ====================
function activate(context) {
    const lang = detectLang();
    const command = vscode.commands.registerCommand('repo2md.start', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage(t(lang, 'openFolderFirst'));
            return;
        }
        const rootPath = workspaceFolders[0].uri.fsPath;
        const projectName = path.basename(rootPath);
        const stateKey = `repo2md.selected.${simpleHash(rootPath)}`;
        const config = vscode.workspace.getConfiguration('repo2md');
        const rememberSelection = config.get('rememberSelection', true);
        const savedSelection = rememberSelection
            ? context.workspaceState.get(stateKey, [])
            : [];
        const panel = vscode.window.createWebviewPanel('repo2md', 'Repo to Markdown', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true, localResourceRoots: [] });
        panel.webview.html = getWebviewContent(lang);
        let currentFiles = [];
        let refreshTimer;
        let isFirstScan = true;
        const postFolderData = (files, includeSaved) => {
            const fileList = files.map((f) => ({
                path: f.path,
                size: f.size,
                extension: getExtension(f.path),
            }));
            panel.webview.postMessage({
                command: 'folderData',
                projectName,
                files: fileList,
                savedSelection: includeSaved ? savedSelection : undefined,
            });
        };
        const refreshFiles = async () => {
            try {
                currentFiles = await scanFiles(rootPath);
                postFolderData(currentFiles, isFirstScan);
                isFirstScan = false;
            }
            catch (err) {
                vscode.window.showErrorMessage(t(lang, 'refreshFailed', err.message));
            }
        };
        const watcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(rootPath, '**/*'));
        const shouldIgnoreUri = (uri) => {
            if (!uri || !uri.fsPath)
                return false;
            const rel = path.relative(rootPath, uri.fsPath).replace(/\\/g, '/');
            if (!rel)
                return false;
            const segments = rel.split('/');
            for (let i = 0; i < segments.length - 1; i++) {
                if (IGNORED_DIRECTORIES.has(segments[i]))
                    return true;
            }
            const fileName = segments[segments.length - 1];
            if (fileName.startsWith('.') && fileName !== '.env' && fileName !== '.gitignore')
                return true;
            return false;
        };
        const debouncedRefresh = (uri) => {
            if (uri && shouldIgnoreUri(uri))
                return;
            if (refreshTimer)
                clearTimeout(refreshTimer);
            refreshTimer = setTimeout(refreshFiles, 500);
        };
        watcher.onDidChange(debouncedRefresh);
        watcher.onDidCreate(debouncedRefresh);
        watcher.onDidDelete(debouncedRefresh);
        panel.onDidDispose(() => {
            watcher.dispose();
            if (refreshTimer)
                clearTimeout(refreshTimer);
        });
        panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'ready': {
                    try {
                        await vscode.window.withProgress({
                            location: vscode.ProgressLocation.Notification,
                            title: t(lang, 'scanning', projectName),
                            cancellable: false,
                        }, async (progress) => {
                            progress.report({ message: t(lang, 'readingTree') });
                            currentFiles = await scanFiles(rootPath);
                            postFolderData(currentFiles, isFirstScan);
                            isFirstScan = false;
                        });
                    }
                    catch (err) {
                        vscode.window.showErrorMessage(t(lang, 'scanFailed', err.message));
                    }
                    break;
                }
                case 'saveSelection': {
                    if (!rememberSelection)
                        break;
                    const paths = message.selectedPaths || [];
                    try {
                        await context.workspaceState.update(stateKey, paths);
                    }
                    catch {
                        // ignore
                    }
                    break;
                }
                case 'generateMarkdown': {
                    const selectedPaths = message.selectedPaths;
                    if (selectedPaths.length === 0) {
                        vscode.window.showWarningMessage(t(lang, 'noFileSelected'));
                        return;
                    }
                    const cfg = vscode.workspace.getConfiguration('repo2md');
                    const threshold = cfg.get('tokenWarningThreshold', 128000);
                    const enableRedact = cfg.get('enableSensitiveRedaction', true);
                    if (threshold > 0) {
                        const sizeMap = new Map();
                        for (const f of currentFiles)
                            sizeMap.set(f.path, f.size);
                        let totalBytes = 0;
                        for (const p of selectedPaths)
                            totalBytes += sizeMap.get(p) || 0;
                        const est = estimateTokens(totalBytes);
                        if (est > threshold) {
                            const choice = await vscode.window.showWarningMessage(t(lang, 'tokenWarning', est.toLocaleString(), selectedPaths.length, formatBytes(totalBytes)), { modal: true }, t(lang, 'continueLabel'), t(lang, 'cancelLabel'));
                            if (choice !== t(lang, 'continueLabel'))
                                return;
                        }
                    }
                    const result = await vscode.window.withProgress({
                        location: vscode.ProgressLocation.Notification,
                        title: t(lang, 'generatingTitle', projectName),
                        cancellable: true,
                    }, async (progress, token) => {
                        const mdParts = [];
                        mdParts.push(`# 项目概览：${projectName}\n`);
                        mdParts.push(`## 📁 目录结构\n`);
                        mdParts.push('```\n' + generateDirectoryTree(selectedPaths, projectName) + '```\n');
                        mdParts.push(`## 📄 文件内容\n`);
                        const total = selectedPaths.length;
                        let redactedCount = 0;
                        for (let i = 0; i < total; i++) {
                            if (token.isCancellationRequested)
                                return null;
                            const relPath = selectedPaths[i];
                            const uri = vscode.Uri.file(path.join(rootPath, relPath));
                            const ext = getExtension(relPath);
                            progress.report({
                                increment: 100 / total,
                                message: `(${i + 1}/${total}) ${relPath}`,
                            });
                            panel.webview.postMessage({
                                command: 'generateProgress',
                                current: i + 1,
                                total,
                                file: relPath,
                            });
                            try {
                                const isBinary = await isBinaryFile(uri, relPath);
                                if (isBinary) {
                                    mdParts.push(`### \`${relPath}\`\n\`\`\`\n${t(lang, 'binarySkipped')}\n\`\`\``);
                                }
                                else {
                                    let content = await readTextFile(uri);
                                    if (enableRedact) {
                                        const before = content;
                                        content = redactSensitive(content);
                                        if (before !== content)
                                            redactedCount++;
                                    }
                                    mdParts.push(`### \`${relPath}\`\n\`\`\`${ext === '[无后缀]' ? '' : ext}\n${content}\n\`\`\``);
                                }
                            }
                            catch (err) {
                                mdParts.push(`### \`${relPath}\`\n\`\`\`\n${t(lang, 'readFailed', err.message)}\n\`\`\``);
                            }
                        }
                        if (enableRedact && redactedCount > 0) {
                            vscode.window.showInformationMessage(t(lang, 'redactedCount', redactedCount));
                        }
                        return mdParts.join('\n\n');
                    });
                    if (result === null) {
                        vscode.window.showInformationMessage(t(lang, 'genCancelled'));
                        panel.webview.postMessage({
                            command: 'generateProgress',
                            current: 0,
                            total: 0,
                            file: '',
                        });
                        return;
                    }
                    panel.webview.postMessage({ command: 'markdownResult', markdown: result });
                    break;
                }
                case 'exportMarkdown': {
                    const content = message.content;
                    if (!content) {
                        vscode.window.showErrorMessage(t(lang, 'noContentToExport'));
                        return;
                    }
                    const defaultName = projectName || 'project';
                    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
                    const defaultFileName = `${defaultName}_${date}.md`;
                    const uri = await vscode.window.showSaveDialog({
                        defaultUri: vscode.Uri.file(defaultFileName),
                        filters: { Markdown: ['md'] },
                    });
                    if (uri) {
                        try {
                            await fs.writeFile(uri.fsPath, content, 'utf-8');
                            vscode.window.showInformationMessage(t(lang, 'exportSuccess', uri.fsPath));
                        }
                        catch (err) {
                            vscode.window.showErrorMessage(t(lang, 'exportFailed', err.message));
                        }
                    }
                    break;
                }
            }
        });
    });
    context.subscriptions.push(command);
}
function deactivate() { }
// ==================== Webview HTML ====================
function getWebviewContent(lang) {
    const dict = I18N[lang];
    const dictJson = JSON.stringify(dict)
        .replace(/</g, '\\u003c')
        .replace(/>/g, '\\u003e')
        .replace(/&/g, '\\u0026');
    return [
        '<!DOCTYPE html>',
        '<html lang="' + (lang === 'zh' ? 'zh-CN' : 'en') + '">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<title>' + dict.appTitle + '</title>',
        '<style>',
        '  * { box-sizing: border-box; }',
        '  body {',
        '    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;',
        '    padding: 0.75rem 1rem;',
        '    color: var(--vscode-foreground);',
        '    background: var(--vscode-editor-background);',
        '  }',
        '  h1 { font-size: 1.2rem; margin: 0 0 0.5rem 0; }',
        '  .project-info {',
        '    font-size: 1rem; margin-bottom: 0.75rem; padding: 0.4rem 0.75rem;',
        '    background: var(--vscode-badge-background, #f0f0f0);',
        '    color: var(--vscode-badge-foreground, #333);',
        '    border-radius: 4px; border: 1px solid var(--vscode-widget-border, transparent);',
        '  }',
        '  .toolbar { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; margin-bottom: 0.5rem; }',
        '  .toolbar input[type="search"] {',
        '    flex: 1; min-width: 150px; padding: 0.3rem 0.5rem;',
        '    border: 1px solid var(--vscode-input-border, #ccc); border-radius: 4px;',
        '    background: var(--vscode-input-background, #fff);',
        '    color: var(--vscode-input-foreground, #000); font-size: 0.85rem;',
        '  }',
        '  button {',
        '    padding: 0.3rem 0.75rem;',
        '    background: var(--vscode-button-background, #28a745);',
        '    color: var(--vscode-button-foreground, #fff);',
        '    border: 1px solid transparent; border-radius: 4px;',
        '    cursor: pointer; font-size: 0.85rem;',
        '  }',
        '  button:hover { opacity: 0.9; }',
        '  button:disabled { opacity: 0.4; cursor: not-allowed; }',
        '  button.secondary {',
        '    background: var(--vscode-button-secondaryBackground, #6c757d);',
        '    color: var(--vscode-button-secondaryForeground, #fff);',
        '  }',
        '  .ext-filters { margin: 0.5rem 0; font-size: 0.8rem; }',
        '  .ext-filters label { margin-right: 0.6rem; display: inline-block; }',
        '  #tree-container {',
        '    margin: 0.5rem 0; border: 1px solid var(--vscode-widget-border, #ddd);',
        '    border-radius: 4px; padding: 0.3rem; max-height: 400px; overflow: auto;',
        '    font-family: monospace; font-size: 0.85rem; line-height: 1.6;',
        '  }',
        '  .tree-node { white-space: nowrap; user-select: none; }',
        '  .tree-node.file { cursor: pointer; }',
        '  .tree-node.file:hover { background: var(--vscode-list-hoverBackground); }',
        '  .tree-node.dir { font-weight: 600; }',
        '  .tree-node .toggle {',
        '    display: inline-block; width: 1em; cursor: pointer; user-select: none;',
        '    color: var(--vscode-descriptionForeground);',
        '  }',
        '  #size-info { margin: 0.4rem 0; font-size: 0.85rem; color: var(--vscode-descriptionForeground); }',
        '  .actions { margin: 0.5rem 0; }',
        '  #progress-bar {',
        '    margin: 0.5rem 0; padding: 0.4rem 0.75rem;',
        '    background: var(--vscode-editor-inactiveSelectionBackground, #e3f2fd);',
        '    border-radius: 4px; font-size: 0.85rem;',
        '  }',
        '  textarea {',
        '    width: 100%; margin-top: 0.5rem; padding: 0.5rem;',
        '    border: 1px solid var(--vscode-input-border, #ccc); border-radius: 4px;',
        '    font-family: monospace; font-size: 0.85rem;',
        '    background-color: var(--vscode-input-background, #fff);',
        '    color: var(--vscode-input-foreground, #000); resize: vertical;',
        '  }',
        '  textarea:focus { outline: none; border-color: var(--vscode-focusBorder, #007acc); }',
        '  #toc-panel {',
        '    position: fixed; top: 40px; right: 20px; width: 280px; max-height: 70vh;',
        '    display: none; flex-direction: column;',
        '    background: var(--vscode-editor-background, #fff);',
        '    border: 1px solid var(--vscode-widget-border, #ccc); border-radius: 6px;',
        '    box-shadow: 0 4px 20px rgba(0,0,0,0.2); z-index: 100; overflow: hidden;',
        '  }',
        '  #toc-panel .toc-header {',
        '    display: flex; justify-content: space-between; align-items: center;',
        '    padding: 0.4rem 0.6rem;',
        '    border-bottom: 1px solid var(--vscode-widget-border, #ccc);',
        '    font-weight: 600; font-size: 0.9rem;',
        '  }',
        '  #toc-panel .toc-header button {',
        '    padding: 0.1rem 0.4rem; background: transparent;',
        '    color: var(--vscode-foreground); font-size: 1.1rem;',
        '  }',
        '  #toc-list { overflow-y: auto; padding: 0.3rem; }',
        '  .toc-item {',
        '    padding: 0.25rem 0.5rem; font-size: 0.85rem; cursor: pointer;',
        '    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;',
        '  }',
        '  .toc-item:hover { background: var(--vscode-list-hoverBackground); }',
        '  .toc-level-1 { font-weight: 700; padding-left: 0.5rem; }',
        '  .toc-level-2 { padding-left: 1.4rem; }',
        '  .toc-level-3 { padding-left: 2.2rem; font-size: 0.8rem; }',
        '  .toc-level-4, .toc-level-5, .toc-level-6 { padding-left: 3rem; font-size: 0.8rem; color: var(--vscode-descriptionForeground); }',
        '</style>',
        '</head>',
        '<body>',
        '  <h1>' + dict.appTitle + '</h1>',
        '  <div class="project-info"><span id="project-name">' + dict.loadingProject + '</span></div>',
        '',
        '  <div class="toolbar">',
        '    <button id="select-all-btn" class="secondary">' + dict.selectAll + '</button>',
        '    <button id="select-none-btn" class="secondary">' + dict.selectNone + '</button>',
        '    <button id="invert-btn" class="secondary">' + dict.invert + '</button>',
        '    <button id="select-code-btn" class="secondary">' + dict.selectCode + '</button>',
        '    <input id="search-input" type="search" placeholder="' + dict.searchPlaceholder + '">',
        '  </div>',
        '',
        '  <div class="ext-filters">',
        '    <div><strong>' + dict.extFilter + '</strong></div>',
        '    <div id="extension-filters"></div>',
        '  </div>',
        '',
        '  <div id="tree-container"></div>',
        '  <div id="size-info"></div>',
        '',
        '  <div class="actions">',
        '    <button id="generate-btn" disabled>' + dict.generateBtn + '</button>',
        '    <button id="copy-btn" class="secondary" disabled>' + dict.copyBtn + '</button>',
        '    <button id="export-btn" class="secondary" disabled>' + dict.exportBtn + '</button>',
        '    <button id="toc-btn" class="secondary" disabled>' + dict.tocBtn + '</button>',
        '  </div>',
        '',
        '  <div id="progress-bar" style="display:none;"><span id="progress-text"></span></div>',
        '',
        '  <textarea id="markdown-output" rows="20" placeholder="' + dict.placeholder + '"></textarea>',
        '',
        '  <div id="toc-panel">',
        '    <div class="toc-header"><span>' + dict.tocTitle + '</span><button id="toc-close">×</button></div>',
        '    <div id="toc-list"></div>',
        '  </div>',
        '',
        '  <script>window.__I18N__ = ' + dictJson + ';</script>',
        '  <script>',
        '  (function() {',
        '    var vscode = acquireVsCodeApi();',
        '    var T = window.__I18N__;',
        '    function fmt(tpl) {',
        '      for (var i = 1; i < arguments.length; i++) {',
        '        tpl = tpl.split("{" + (i - 1) + "}").join(String(arguments[i]));',
        '      }',
        '      return tpl;',
        '    }',
        '',
        '    var fileMap = {};',
        '    var selectedSet = new Set();',
        '    var allExtensions = new Set();',
        '    var extensionFilters = new Set();',
        '    var projectName = "";',
        '    var searchQuery = "";',
        '    var saveTimer = null;',
        '    var CODE_EXTS = new Set(["js","mjs","cjs","jsx","ts","tsx","vue","svelte","py","rb","go","rs","java","kt","c","h","cpp","hpp","cs","php","sh","bash","sql","json","yaml","yml","toml","xml","html","css","scss","less","md"]);',
        '',
        '    function getExtension(p) {',
        '      var parts = p.split("/");',
        '      var file = parts[parts.length - 1];',
        '      var dot = file.lastIndexOf(".");',
        '      return dot === -1 ? "[无后缀]" : file.substring(dot + 1).toLowerCase();',
        '    }',
        '',
        '    function formatBytes(bytes) {',
        '      if (bytes === 0) return "0 B";',
        '      var k = 1024, sizes = ["B","KB","MB","GB"];',
        '      var i = Math.floor(Math.log(bytes) / Math.log(k));',
        '      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];',
        '    }',
        '',
        '    function scheduleSaveSelection() {',
        '      if (saveTimer) clearTimeout(saveTimer);',
        '      saveTimer = setTimeout(function() {',
        '        vscode.postMessage({ command: "saveSelection", selectedPaths: Array.from(selectedSet) });',
        '      }, 500);',
        '    }',
        '',
        '    function updateSelectionUI() {',
        '      var count = selectedSet.size, totalBytes = 0;',
        '      selectedSet.forEach(function(p) { if (fileMap[p]) totalBytes += fileMap[p].size; });',
        '      document.getElementById("size-info").textContent = fmt(T.selectedInfo, count, formatBytes(totalBytes));',
        '      var has = count > 0;',
        '      ["generate-btn","copy-btn","export-btn","toc-btn"].forEach(function(id) {',
        '        document.getElementById(id).disabled = !has;',
        '      });',
        '    }',
        '',
        '    function refreshCheckboxes() {',
        '      document.querySelectorAll("#tree-container input[type=checkbox]").forEach(function(cb) {',
        '        var path = cb.getAttribute("data-path");',
        '        cb.checked = selectedSet.has(path);',
        '      });',
        '    }',
        '',
        '    function renderExtensionFilters() {',
        '      var container = document.getElementById("extension-filters");',
        '      container.innerHTML = "";',
        '      Array.from(allExtensions).sort().forEach(function(ext) {',
        '        var label = document.createElement("label");',
        '        var cb = document.createElement("input");',
        '        cb.type = "checkbox";',
        '        cb.checked = extensionFilters.has(ext);',
        '        cb.addEventListener("change", function() {',
        '          if (cb.checked) extensionFilters.add(ext); else extensionFilters.delete(ext);',
        '          applyFilters();',
        '        });',
        '        label.appendChild(cb);',
        '        label.appendChild(document.createTextNode(" " + ext));',
        '        container.appendChild(label);',
        '      });',
        '    }',
        '',
        '    function buildTreeData() {',
        '      var root = { name: projectName, path: "", isFile: false, children: {} };',
        '      Object.keys(fileMap).forEach(function(p) {',
        '        var parts = p.split("/");',
        '        var current = root;',
        '        parts.forEach(function(part, idx) {',
        '          if (!current.children[part]) {',
        '            current.children[part] = {',
        '              name: part,',
        '              path: parts.slice(0, idx + 1).join("/"),',
        '              isFile: idx === parts.length - 1,',
        '              size: idx === parts.length - 1 ? fileMap[p].size : 0,',
        '              children: {},',
        '            };',
        '          }',
        '          current = current.children[part];',
        '        });',
        '      });',
        '      return root;',
        '    }',
        '',
        '    function renderTree(node, container, depth) {',
        '      var keys = Object.keys(node.children).sort(function(a, b) {',
        '        var aDir = !node.children[a].isFile, bDir = !node.children[b].isFile;',
        '        if (aDir !== bDir) return aDir ? -1 : 1;',
        '        return a.localeCompare(b, undefined, { sensitivity: "base" });',
        '      });',
        '      keys.forEach(function(key) {',
        '        var child = node.children[key];',
        '        var nodeEl = document.createElement("div");',
        '        nodeEl.className = "tree-node " + (child.isFile ? "file" : "dir");',
        '        nodeEl.setAttribute("data-path", child.path);',
        '        nodeEl.setAttribute("data-is-file", child.isFile ? "1" : "0");',
        '        nodeEl.setAttribute("data-ext", child.isFile ? getExtension(child.path) : "");',
        '        nodeEl.style.paddingLeft = (depth * 16 + 4) + "px";',
        '        if (child.isFile) {',
        '          var cb = document.createElement("input");',
        '          cb.type = "checkbox";',
        '          cb.setAttribute("data-path", child.path);',
        '          cb.checked = selectedSet.has(child.path);',
        '          cb.addEventListener("change", function() {',
        '            if (cb.checked) selectedSet.add(child.path); else selectedSet.delete(child.path);',
        '            updateSelectionUI(); scheduleSaveSelection();',
        '          });',
        '          nodeEl.appendChild(cb);',
        '          nodeEl.appendChild(document.createTextNode(" " + child.name + " (" + formatBytes(child.size) + ")"));',
        '        } else {',
        '          var toggle = document.createElement("span");',
        '          toggle.className = "toggle";',
        '          toggle.textContent = "▼";',
        '          toggle.addEventListener("click", function(e) {',
        '            e.stopPropagation();',
        '            var cc = nodeEl.nextElementSibling;',
        '            if (cc && cc.className === "tree-children") {',
        '              var hidden = cc.style.display === "none";',
        '              cc.style.display = hidden ? "" : "none";',
        '              toggle.textContent = hidden ? "▼" : "▶";',
        '            }',
        '          });',
        '          nodeEl.appendChild(toggle);',
        '          nodeEl.appendChild(document.createTextNode(" " + child.name + "/"));',
        '        }',
        '        container.appendChild(nodeEl);',
        '        if (!child.isFile && Object.keys(child.children).length > 0) {',
        '          var childContainer = document.createElement("div");',
        '          childContainer.className = "tree-children";',
        '          renderTree(child, childContainer, depth + 1);',
        '          container.appendChild(childContainer);',
        '        }',
        '      });',
        '    }',
        '',
        '    function rebuildTree() {',
        '      var container = document.getElementById("tree-container");',
        '      container.innerHTML = "";',
        '      renderTree(buildTreeData(), container, 0);',
        '      applyFilters();',
        '      updateSelectionUI();',
        '    }',
        '',
        '    function applyFilters() {',
        '      var q = searchQuery.trim().toLowerCase();',
        '      document.querySelectorAll("#tree-container .tree-node").forEach(function(el) {',
        '        if (el.getAttribute("data-is-file") !== "1") { el.style.display = ""; return; }',
        '        var ext = el.getAttribute("data-ext");',
        '        var p = el.getAttribute("data-path").toLowerCase();',
        '        var extOk = extensionFilters.has(ext);',
        '        var searchOk = !q || p.indexOf(q) !== -1;',
        '        el.style.display = (extOk && searchOk) ? "" : "none";',
        '      });',
        '    }',
        '',
        '    window.addEventListener("message", function(event) {',
        '      var msg = event.data;',
        '      switch (msg.command) {',
        '        case "folderData":',
        '          if (msg.savedSelection && msg.savedSelection.length > 0 && selectedSet.size === 0) {',
        '            selectedSet = new Set(msg.savedSelection);',
        '          }',
        '          projectName = msg.projectName;',
        '          document.getElementById("project-name").textContent = fmt(T.projectLabel, projectName);',
        '          fileMap = {};',
        '          allExtensions.clear();',
        '          extensionFilters.clear();',
        '          msg.files.forEach(function(f) {',
        '            fileMap[f.path] = { size: f.size, extension: f.extension };',
        '            allExtensions.add(f.extension);',
        '          });',
        '          var valid = new Set();',
        '          selectedSet.forEach(function(p) { if (fileMap[p]) valid.add(p); });',
        '          selectedSet = valid;',
        '          extensionFilters = new Set(allExtensions);',
        '          renderExtensionFilters();',
        '          rebuildTree();',
        '          break;',
        '        case "generateProgress":',
        '          var bar = document.getElementById("progress-bar");',
        '          if (msg.total === 0) { bar.style.display = "none"; }',
        '          else {',
        '            bar.style.display = "block";',
        '            document.getElementById("progress-text").textContent = fmt(T.progressTemplate, msg.current, msg.total, msg.file);',
        '          }',
        '          break;',
        '        case "markdownResult":',
        '          document.getElementById("progress-bar").style.display = "none";',
        '          document.getElementById("markdown-output").value = msg.markdown;',
        '          document.getElementById("toc-btn").disabled = false;',
        '          break;',
        '      }',
        '    });',
        '',
        '    vscode.postMessage({ command: "ready" });',
        '',
        '    document.getElementById("select-all-btn").addEventListener("click", function() {',
        '      selectedSet.clear();',
        '      Object.keys(fileMap).forEach(function(p) { selectedSet.add(p); });',
        '      refreshCheckboxes(); updateSelectionUI(); scheduleSaveSelection();',
        '    });',
        '    document.getElementById("select-none-btn").addEventListener("click", function() {',
        '      selectedSet.clear();',
        '      refreshCheckboxes(); updateSelectionUI(); scheduleSaveSelection();',
        '    });',
        '    document.getElementById("invert-btn").addEventListener("click", function() {',
        '      Object.keys(fileMap).forEach(function(p) {',
        '        if (selectedSet.has(p)) selectedSet.delete(p); else selectedSet.add(p);',
        '      });',
        '      refreshCheckboxes(); updateSelectionUI(); scheduleSaveSelection();',
        '    });',
        '    document.getElementById("select-code-btn").addEventListener("click", function() {',
        '      selectedSet.clear();',
        '      Object.keys(fileMap).forEach(function(p) {',
        '        if (CODE_EXTS.has(getExtension(p))) selectedSet.add(p);',
        '      });',
        '      refreshCheckboxes(); updateSelectionUI(); scheduleSaveSelection();',
        '    });',
        '',
        '    document.getElementById("search-input").addEventListener("input", function(e) {',
        '      searchQuery = e.target.value || "";',
        '      applyFilters();',
        '    });',
        '',
        '    document.getElementById("generate-btn").addEventListener("click", function() {',
        '      var paths = Array.from(selectedSet);',
        '      if (paths.length === 0) { alert(T.pleaseSelectFile); return; }',
        '      var sensitive = [".env","secret","password","key","token"];',
        '      var hasSensitive = paths.some(function(p) {',
        '        var lp = p.toLowerCase();',
        '        return sensitive.some(function(s) { return lp.indexOf(s) !== -1; });',
        '      });',
        '      if (hasSensitive && !confirm(T.sensitiveConfirm)) return;',
        '      document.getElementById("progress-bar").style.display = "block";',
        '      document.getElementById("progress-text").textContent = T.preparing;',
        '      vscode.postMessage({ command: "generateMarkdown", selectedPaths: paths, projectName: projectName });',
        '    });',
        '',
        '    document.getElementById("copy-btn").addEventListener("click", function() {',
        '      var text = document.getElementById("markdown-output").value;',
        '      if (!text) { alert(T.generateFirst); return; }',
        '      navigator.clipboard.writeText(text).then(function() {',
        '        alert(T.copied);',
        '      }).catch(function() { alert(T.copyFailed); });',
        '    });',
        '',
        '    document.getElementById("export-btn").addEventListener("click", function() {',
        '      var content = document.getElementById("markdown-output").value;',
        '      if (!content.trim()) { alert(T.generateFirstMd); return; }',
        '      vscode.postMessage({ command: "exportMarkdown", content: content, projectName: projectName });',
        '    });',
        '',
        '    function buildToc(markdown) {',
        '      var lines = markdown.split("\\n");',
        '      var items = [];',
        '      var inCode = false;',
        '      lines.forEach(function(line, idx) {',
        '        if (/^```/.test(line)) { inCode = !inCode; return; }',
        '        if (inCode) return;',
        '        var m = line.match(/^(#{1,6})\\s+(.+)$/);',
        '        if (m) items.push({ level: m[1].length, title: m[2].trim(), line: idx });',
        '      });',
        '      return items;',
        '    }',
        '',
        '    function renderTocPanel(items) {',
        '      var list = document.getElementById("toc-list");',
        '      list.innerHTML = "";',
        '      items.forEach(function(item) {',
        '        var el = document.createElement("div");',
        '        el.className = "toc-item toc-level-" + item.level;',
        '        el.textContent = item.title;',
        '        el.title = item.title;',
        '        el.addEventListener("click", function() {',
        '          var ta = document.getElementById("markdown-output");',
        '          var lines = ta.value.split("\\n");',
        '          var offset = 0;',
        '          for (var i = 0; i < item.line && i < lines.length; i++) offset += lines[i].length + 1;',
        '          ta.focus();',
        '          ta.setSelectionRange(offset, offset);',
        '          var lh = parseFloat(getComputedStyle(ta).lineHeight) || 20;',
        '          ta.scrollTop = Math.max(0, item.line * lh - 40);',
        '        });',
        '        list.appendChild(el);',
        '      });',
        '    }',
        '',
        '    document.getElementById("toc-btn").addEventListener("click", function() {',
        '      var md = document.getElementById("markdown-output").value;',
        '      if (!md.trim()) { alert(T.generateFirstMd); return; }',
        '      var items = buildToc(md);',
        '      if (items.length === 0) { alert(T.noHeadings); return; }',
        '      renderTocPanel(items);',
        '      document.getElementById("toc-panel").style.display = "flex";',
        '    });',
        '',
        '    document.getElementById("toc-close").addEventListener("click", function() {',
        '      document.getElementById("toc-panel").style.display = "none";',
        '    });',
        '',
        '    ["generate-btn","copy-btn","export-btn","toc-btn"].forEach(function(id) {',
        '      document.getElementById(id).disabled = true;',
        '    });',
        '  })();',
        '  </script>',
        '</body>',
        '</html>',
    ].join('\n');
}
//# sourceMappingURL=extension.js.map