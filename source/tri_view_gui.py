from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLineEdit, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
import os
import subprocess
import time
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

class TriVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set up logger
        self.logger = logging.getLogger('nebula_viewer.TriVisualizer')
        self.logger.info("Initializing TriVisualizer")
        
        self.setWindowTitle("Tri File Visualization Tool")
        self.setGeometry(100, 100, 800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
                
        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText("File path will be displayed here")
        self.layout.addWidget(self.file_path_display)
        
        self.button = QPushButton("Selectfile")
        self.button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.button)
        
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Enable JavaScript and plugins
        settings = self.web_view.settings()
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(settings.WebAttribute.PluginsEnabled, True)
        
        # Set user agent，simulate Chrome browser
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setDefaultTextEncoding("utf-8")
        
        # Enable开发者工具
        
        
        # Set自定义 WebEnginePage 以拦截链接点击和处理控制台消息
        custom_page = WebEnginePage(self.web_view)
        self.web_view.setPage(custom_page)
        
        # 无需手动连接信号，WebEnginePage 类已处理 JavaScript 控制台消息
        
        self.layout.addWidget(self.web_view)
        
        # 保存开发服务器进程对象
        self.dev_server_process = None
        
        # 启动时直接加载本地开发服务器页面
        from PyQt6.QtCore import QUrl
        self.web_view.load(QUrl("http://localhost:5173/"))
        self.label.setText("正on加载可视化页面...")
        self.logger.info("Loading visualization page")
        
    # 定义 JavaScript 控制台消息信号
    javaScriptConsoleMessage = pyqtSignal(int, str, int, str)

    def handle_console_message(self, level, message, line, source_id):
        """处理 JavaScript 控制台消息"""
        try:
            level_str = ["Info", "Warning", "Error"][level] if isinstance(level, int) and 0 <= level < 3 else "Unknown"
            log_msg = f"JS Console ({level_str}): {message} [line: {line}, source: {source_id}]"
            
            # 根据日志级别Select不同of日志方法
            if level_str == "Error":
                self.logger.error(log_msg)
            elif level_str == "Warning":
                self.logger.warning(log_msg)
            else:
                self.logger.debug(log_msg)
                
            self.javaScriptConsoleMessage.emit(level, message, line, source_id)
        except Exception as e:
            self.logger.error(f"Error handling console message: {str(e)}")

    def open_file_dialog(self):
        """
        打开fileSelect对话框并加载可视化页面
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .tri file", "", "Tri file (*.tri);;所有file (*)")
        if file_path:
            self.file_path_display.setText(file_path)
            self.load_visualization(file_path)
    
    def load_visualization(self, file_path):
        """
        加载 .tri file内容并可视化
        """
        if not os.path.exists(file_path):
            self.label.setText(f"错误: file {file_path} 不存on")
            return
        
        try:
            # Readfile内容
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            
            # 直接加载file内容并Set MIME 类型
            # 完整ofMIME类型映射
            mime_map = {
                '.json': 'application/json',
                '.tri': 'text/plain',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.hdr': 'text/plain',
                '.dat': 'application/octet-stream'
            }
            mime_type = 'application/octet-stream'  # 默认类型
            for ext in mime_map:
                if file_path.lower().endswith(ext):
                    mime_type = mime_map[ext]
                    break
            
            self.web_view.setContent(file_content.encode('utf-8'), mime_type)
            self.label.setText(f"已加载file: {os.path.basename(file_path)}")
            
            # 优化of服务器检查(带重试)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with urlopen("http://localhost:5173", timeout=5) as response:
                        if response.status == 200:
                            break
                        elif attempt == max_retries - 1:
                            self.label.setText("错误: 开发服务器异常")
                            return
                except Exception as e:
                    if attempt == max_retries - 1:
                        self.label.setText(f"错误: 无法连接开发服务器 ({str(e)})")
                        return
                    time.sleep(1)
            
            try:
                self.label.setText("开发服务器已启动")
            except Exception as e:
                self.label.setText(f"错误: 无法启动开发服务器。请确保已安装 Node.js 并运行 `npm install`。详细信息: {str(e)}")
                print(f"DEBUG - 开发服务器启动失败: {str(e)}")
                return
            
            # 加载本地开发服务器页面
            from PyQt6.QtCore import QUrl
            from urllib.parse import quote
            import mimetypes
            
            # 确保 MIME 类型已正确Initialize
            mimetypes.init()
            
            # 正确编码filepath，确保特殊字符被正确处理
            encoded_path = quote(file_path)
            
            # 安全offile内容Read(限制大小和验证内容)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            try:
                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_SIZE:
                    self.label.setText(f"错误: file过大 ({file_size} > {MAX_FILE_SIZE} bytes)")
                    return
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    
                # 基本内容验证
                if not file_content.strip():
                    self.label.setText("错误: file内容为空")
                    return
                
                # 构建 URL，包含filename
                file_name = os.path.basename(file_path)
                url = f"http://localhost:5173/?fileName={quote(file_name)}"
                
                # 加载 URL
                self.web_view.load(QUrl(url))
                
                # Set自定义 HTTP 头，传递file内容
                self.web_view.page().profile().setHttpAcceptLanguage("en-US,en;q=0.9")
                self.web_view.page().profile().setHttpUserAgent("Mozilla/5.0 NebulaViewer/1.0")
                
                # Convertfile内容存储on本地存储中，以便前端访问
                # 使用分块存储方式处理大file
                self.logger.debug(f"Storing file content in localStorage, size: {len(file_content)} bytes")
                script = f"""
                try {{
                    // 清除之前of内容
                    localStorage.removeItem('triFileContent');
                    localStorage.removeItem('triFileChunks');
                    
                    // 分块存储大file内容，避免超出 localStorage 限制
                    const content = `{file_content}`;
                    const maxChunkSize = 512 * 1024; // 512KB chunks
                    
                    if (content.length <= maxChunkSize) {{
                        // 小file直接存储
                        localStorage.setItem('triFileContent', JSON.stringify(content));
                        console.log('File content stored in localStorage, size: ' + content.length + ' bytes');
                    }} else {{
                        // 大file分块存储
                        const chunks = Math.ceil(content.length / maxChunkSize);
                        console.log(`File too large (${content.length} bytes), splitting into ${chunks} chunks`);
                        
                        // 存储块数量
                        localStorage.setItem('triFileChunks', chunks.toString());
                        
                        // 存储每个块
                        for (let i = 0; i < chunks; i++) {{
                            const start = i * maxChunkSize;
                            const end = Math.min(start + maxChunkSize, content.length);
                            const chunk = content.substring(start, end);
                            localStorage.setItem(`triFileContent_${i}`, JSON.stringify(chunk));
                            console.log(`Chunk ${i} stored, size: ${chunk.length} bytes`);
                        }}
                        
                        console.log('All chunks stored in localStorage');
                    }}
                }} catch (error) {{
                    console.error('Error storing file content in localStorage:', error);
                }}
                """
                self.web_view.page().runJavaScript(script)
                
                self.label.setText(f"正on加载file: {file_path}...")
            except Exception as e:
                self.label.setText(f"错误: 无法Readfile内容: {str(e)}")
                print(f"DEBUG - fileRead错误: {str(e)}")
            
            # on页面加载完成后更新状态
            def on_load_finished(ok):
                if ok:
                    self.label.setText("页面加载完成")
                    self.logger.info("Page loaded successfully")
                    
                    # 执行额外of JavaScript 来验证file内容是否正确加载
                    verify_script = """
                    (function() {
                        try {
                            const chunks = localStorage.getItem('triFileChunks');
                            if (chunks) {
                                return `File content loaded in ${chunks} chunks`;
                            } else {
                                const content = localStorage.getItem('triFileContent');
                                if (content) {
                                    return `File content loaded, size: ${content.length} bytes`;
                                } else {
                                    return 'No file content found in localStorage';
                                }
                            }
                        } catch (error) {
                            return `Error verifying file content: ${error.message}`;
                        }
                    })();
                    """
                    
                    def handle_verification(result):
                        self.logger.debug(f"File content verification: {result}")
                    
                    self.web_view.page().runJavaScript(verify_script, 0, handle_verification)
                else:
                    self.label.setText("错误: 页面加载失败")
                    self.logger.error("Page failed to load")
            
            self.web_view.loadFinished.connect(on_load_finished)
        except Exception as e:
            self.label.setText(f"错误: {str(e)}")
            print(f"DEBUG - Exception: {str(e)}")


class WebEnginePage(QWebEnginePage):
    """
    自定义 WebEnginePage 以拦截链接点击、导航请求和 JavaScript 错误
    """
    javaScriptConsoleMessage = pyqtSignal(int, str, int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('nebula_viewer.WebEnginePage')
        self.logger.info("Initializing custom WebEnginePage")
    
    def acceptNavigationRequest(self, url, type_, isMainFrame):
        """
        拦截所有导航请求
        """
        self.logger.debug(f"Navigation request: {url.toString()}, type: {type_}, isMainFrame: {isMainFrame}")
        
        if type_ == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            self.logger.info(f"Link clicked: {url.toString()}")
            self.parent().load(url)
            return False
        return super().acceptNavigationRequest(url, type_, isMainFrame)
    
    def createWindow(self, type_):
        """
        拦截新窗口或标签页of打开请求
        """
        self.logger.debug(f"Create window request, type: {type_}")
        return WebEnginePage(self.parent())
    
    def javaScriptAlert(self, securityOrigin, msg):
        """
        拦截 JavaScript alert 对话框
        """
        self.logger.info(f"JavaScript alert: {msg}")
        return super().javaScriptAlert(securityOrigin, msg)
    
    def javaScriptConsoleMessage(self, level, message, line, sourceID):
        """
        拦截 JavaScript 控制台消息并发射信号
        """
        level_str = ["Info", "Warning", "Error"][level.value] if level.value >= 0 and level.value < 3 else "Unknown"
        self.logger.debug(f"JS Console ({level_str}): {message} [line: {line}, source: {sourceID}]")
        # 传递给父类处理
        super().javaScriptConsoleMessage(level, message, line, sourceID)

if __name__ == "__main__":
    import sys
    import os
    import logging
    
    # configuration日志记录
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('nebula_viewer.log')
        ]
    )
    logger = logging.getLogger('nebula_viewer')
    logger.info("Starting Nebula Viewer application")
    
    # Set字体环境变量
    os.environ["FONTCONFIG_PATH"] = "/etc/fonts"
    os.environ["FONTCONFIG_FILE"] = "/etc/fonts/fonts.conf"
    logger.debug("Font environment variables set")
    
    # 忽略 MIME 缓存file错误
    os.environ["QT_LOGGING_RULES"] = "xdg.mime=false;qt.webenginecontext.warning=false"
    logger.debug("QT logging rules set")
    
    try:
        app = QApplication(sys.argv)
        window = TriVisualizer()
        window.show()
        logger.info("Main window displayed")
        
        # 确保程序退出时终止开发服务器进程
        def on_about_to_quit():
            if window.dev_server_process:
                logger.info("Terminating dev server process")
                window.dev_server_process.terminate()
        
        app.aboutToQuit.connect(on_about_to_quit)
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)