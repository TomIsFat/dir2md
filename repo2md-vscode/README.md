# Repo to Markdown

[中文](#中文) | [English](#english)

---

## 中文

### 📖 简介
**Repo to Markdown** 是一个 VS Code 插件，用于将当前打开的项目文件夹转换为结构化的 Markdown 文档。它自动生成目录树，并包含您所选文件的内容，非常适合用于代码审查、文档整理或与 AI 共享上下文。

> ⚠️ **注意**：本插件发布在 [Open VSX 市场](https://open-vsx.org/)，**无法在 VS Code 官方扩展市场直接搜索到**。请参考下方的“安装”说明进行安装。

### ✨ 功能特点
- 📂 **自动扫描**：打开插件即自动扫描当前工作区文件，无需手动选择文件夹。
- ✅ **灵活勾选**：通过复选框选择需要导出的文件，可全选、反选或按需勾选。
- 🔍 **后缀筛选**：按文件扩展名快速过滤，只关注您需要的文件类型。
- 🚫 **智能忽略**：自动跳过常见的构建输出、依赖和版本控制目录（如 `node_modules`、`.git`、`out`、`dist` 等）。
- 🔄 **实时刷新**：当项目文件新增、删除或修改时，文件树自动增量刷新，并尽量保留您之前的勾选状态。
- 🛡️ **二进制检测**：基于扩展名和文件头魔数自动检测二进制文件，避免乱码并提示跳过。
- 📜 **生成内容**：
  - 生成清晰的 ASCII 目录树。
  - 将所选文本文件的内容嵌入 Markdown 代码块，保留语法高亮标识。
- 🔔 **敏感词提示**：若选中文件路径包含常见敏感关键词（如 `.env`、`secret`），会弹出确认框以防意外泄露。
- 📋 **导出/复制**：一键复制生成的 Markdown 到剪贴板，或另存为 `.md` 文件。

### 📦 安装
由于插件仅发布在 **Open VSX** 市场，您可以通过以下方式安装：

#### 从 Open VSX 网站下载 VSIX
1. 访问 [Open VSX 上的 Repo to Markdown 页面](https://open-vsx.org/)（链接待补充，发布后提供）。
2. 点击 “Download” 下载 `.vsix` 文件。
3. 在 VS Code 中打开扩展视图（`Ctrl+Shift+X`），点击右上角 `…` 菜单，选择 **“从 VSIX 安装…”**，然后选择下载的文件。


### 🚀 使用方法
1. **打开项目**：在 VS Code 中打开您要导出为 Markdown 的文件夹（工作区）。
2. **启动插件**：
   - 按 `Ctrl+Shift+P` 打开命令面板。
   - 输入并执行命令：**`Repo to Markdown: Select Folder and Generate`**。
3. **等待扫描**：插件会自动扫描项目文件（首次扫描会显示进度提示）。
4. **选择文件**：
   - 在文件树中勾选需要导出的文件。
   - 使用上方的“后缀筛选”复选框，按扩展名隐藏/显示文件。
5. **生成 Markdown**：
   - 点击 **“生成 Markdown”** 按钮，下方文本框将实时显示生成的文档。
   - 如有敏感文件，会先弹出确认框。
6. **复制或导出**：
   - 点击 **“📋 复制到剪贴板”** 将内容复制。
   - 点击 **“💾 导出为 .md 文件”** 保存到本地。

### ⚙️ 配置与默认行为
- **忽略目录**：默认忽略以下目录（不可配置，如有需要请手动修改源码）：
  ```
  .git, node_modules, out, dist, build, .vscode, __pycache__, .cache, 等
  ```
- **二进制扩展名**：基于常见二进制格式（图片、视频、压缩包等）自动跳过。
- **敏感词列表**：`['.env', 'secret', 'password', 'key', 'token']`（仅检查路径名）。

### 🧑‍💻 贡献指南
欢迎提交 Issue 或 Pull Request！请确保代码通过 TypeScript 编译，并遵循现有风格。

### 📄 许可证
GPL

---

## English

### 📖 Introduction
**Repo to Markdown** is a VS Code extension that converts your currently opened project folder into a well-structured Markdown document. It automatically generates a directory tree and includes the content of selected files, ideal for code reviews, documentation, or sharing context with AI.

> ⚠️ **Note**: This extension is published on the [Open VSX Registry](https://open-vsx.org/). **It is not available in the official VS Code Marketplace**. Please refer to the installation instructions below.

### ✨ Features
- 📂 **Auto‑scan**: Automatically scans the current workspace when the extension starts.
- ✅ **Flexible selection**: Check/uncheck files via the tree; supports multi‑selection.
- 🔍 **Extension filters**: Quickly filter files by their suffix.
- 🚫 **Smart ignore**: Skips common build outputs, dependencies, and VCS directories (`node_modules`, `.git`, `out`, `dist`, etc.).
- 🔄 **Live refresh**: Watches file changes and updates the tree incrementally while preserving your selections when possible.
- 🛡️ **Binary detection**: Detects binary files using extension + magic numbers and skips them to avoid garbage output.
- 📜 **Generated content**:
  - A clean ASCII directory tree.
  - Content of text files inside fenced code blocks with language hints.
- 🔔 **Sensitive keyword warning**: Alerts if selected paths contain keywords like `.env` or `secret`.
- 📋 **Export/Copy**: Copy the Markdown to clipboard or save as a `.md` file.

### 📦 Installation
Because this extension is only published on **Open VSX**, use the method:

#### Download the VSIX from Open VSX
1. Visit the [Repo to Markdown page on Open VSX](https://open-vsx.org/) (link will be provided after publishing).
2. Click “Download” to get the `.vsix` file.
3. In VS Code, open the Extensions view (`Ctrl+Shift+X`), click the `…` menu at the top‑right, choose **“Install from VSIX…”**, and select the downloaded file.


### 🚀 How to Use
1. **Open a project**: In VS Code, open the folder you want to export.
2. **Launch the extension**:
   - Press `Ctrl+Shift+P` to open the command palette.
   - Run the command: **`Repo to Markdown: Select Folder and Generate`**.
3. **Wait for scanning**: The extension scans all files (progress is shown in a notification).
4. **Select files**:
   - Check the boxes next to files you want to include.
   - Use the “Extension filters” above the tree to show/hide files by suffix.
5. **Generate Markdown**:
   - Click **“Generate Markdown”**; the result appears in the text area below.
   - If any sensitive paths are detected, a confirmation dialog will appear.
6. **Copy or Export**:
   - Click **“📋 Copy to Clipboard”** to copy the Markdown.
   - Click **“💾 Export as .md file”** to save locally.

### ⚙️ Default Behavior
- **Ignored directories**: The following are always skipped (to customize, edit the source):
  ```
  .git, node_modules, out, dist, build, .vscode, __pycache__, .cache, etc.
  ```
- **Binary extensions**: Common binary formats (images, videos, archives) are automatically skipped.
- **Sensitive keywords**: `['.env', 'secret', 'password', 'key', 'token']` (path‑only check).

### 🧑‍💻 Contributing
Issues and pull requests are welcome! Please ensure code compiles with TypeScript and follows the existing style.

### 📄 License
GPL