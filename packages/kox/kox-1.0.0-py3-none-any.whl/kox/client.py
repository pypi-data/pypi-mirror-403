import requests
import os
import json
import zipfile
import shutil
from pathlib import Path
from decimal import Decimal
from typing import Optional
from tqdm import tqdm
import tempfile
import sys


# 配置文件路径
CONFIG_DIR = Path.home() / '.kox'
CONFIG_FILE = CONFIG_DIR / 'config.json'


def get_config():
    """获取配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


class Kox:
    """Kox客户端库"""
    
    # ANSI 颜色代码
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    
    def __init__(self, host: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None, port: Optional[int] = None):
        """
        初始化客户端
        
        Args:
            host: 服务器地址（可选，如果未提供则从配置文件读取）
            user: 用户名（可选，如果未提供则从配置文件读取）
            password: 密码（可选，如果未提供则从配置文件读取）
            port: 服务器端口（可选，如果未提供则从配置文件读取，默认8000）
        """
        # 从配置文件读取配置
        config = get_config()
        
        # 使用参数或配置中的值
        host = host or config.get('host') or 'localhost'
        user = user or config.get('username')
        password = password or config.get('password')
        port = port if port is not None else config.get('port')
        
        # 如果仍然没有用户名或密码，抛出错误
        if not user:
            raise ValueError("Username is required. Please provide it as parameter or set it using 'kox set-username <username>'")
        if not password:
            raise ValueError("Password is required. Please provide it as parameter or set it using 'kox set-password <password>'")
        
        self.host = host.rstrip('/')
        # 如果host包含http://或https://，解析端口
        if '://' in self.host:
            from urllib.parse import urlparse
            parsed = urlparse(self.host)
            self.base_url = self.host
            if port is None and parsed.port:
                port = parsed.port
        else:
            if port is None:
                port = 8000
            self.base_url = f"http://{self.host}:{port}"
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        self._login()
    
    def _login(self):
        """登录并获取CSRF token"""
        # 先获取CSRF token（如果需要）
        try:
            # 尝试从登录页面获取CSRF token
            login_page = self.session.get(f"{self.base_url}/login/")
            if login_page.status_code == 200:
                # 从cookie中获取csrftoken
                if 'csrftoken' in self.session.cookies:
                    self.csrf_token = self.session.cookies['csrftoken']
        except:
            pass
        
        # 登录
        response = self.session.post(
            f"{self.base_url}/api/login/",
            json={'username': self.user, 'password': self.password},
            headers={'X-CSRFToken': self.csrf_token} if self.csrf_token else {}
        )
        if response.status_code != 200:
            raise Exception(f"登录失败: {response.json().get('error', '未知错误')}")
        
        # 登录后再次尝试获取CSRF token
        if 'csrftoken' in self.session.cookies:
            self.csrf_token = self.session.cookies['csrftoken']
    
    def show_projects(self):
        """展示所有项目（仅显示最新版本）"""
        response = self.session.get(f"{self.base_url}/api/projects/")
        if response.status_code != 200:
            raise Exception(f"获取项目列表失败: {response.json().get('error', '未知错误')}")
        
        projects = response.json()
        if not projects:
            print("暂无项目")
            return
        
        # 打印表头
        print(f"{'项目名称':<30} {'版本':<15} {'更新时间':<20} {'大小':<15}")
        print("=" * 80)
        
        for project in projects:
            name = project['name']
            latest = project.get('latest_version')
            if latest:
                version = f"v{latest['version_number']}"
                upload_time = latest['uploaded_at'].replace('T', ' ').split('.')[0]
                size = self._format_size(project['total_size'])
            else:
                version = "无版本"
                upload_time = "-"
                size = "0B"
            
            print(f"{name:<30} {version:<15} {upload_time:<20} {size:<15}")
    
    def show_histories(self, project: str):
        """展示项目的历史版本"""
        response = self.session.get(f"{self.base_url}/api/projects/{project}/versions/")
        if response.status_code != 200:
            raise Exception(f"获取版本历史失败: {response.json().get('error', '未知错误')}")
        
        versions = response.json()
        if not versions:
            print(f"项目 '{project}' 暂无版本")
            return
        
        # 打印表头
        print(f"{'项目名称':<30} {'版本':<15} {'更新时间':<20} {'大小':<15}")
        print("=" * 80)
        
        for version in versions:
            version_num = f"v{version['version_number']}"
            upload_time = version['uploaded_at'].replace('T', ' ').split('.')[0]
            size = version['size_display']
            
            print(f"{project:<30} {version_num:<15} {upload_time:<20} {size:<15}")
    
    def clone(self, project: str, version: Optional[str] = None, path: str = './'):
        """下载项目"""
        # 获取版本信息
        version_info = None
        if not version:
            try:
                response = self.session.get(f"{self.base_url}/api/projects/{project}/versions/")
                if response.status_code == 200:
                    versions = response.json()
                    if versions:
                        version_info = versions[0]  # 最新版本
                        version = str(version_info['version_number'])
            except:
                pass
        
        # 打印开始信息
        print(f"\n{self.BOLD}{self.CYAN}{'='*60}{self.RESET}")
        print(f"{self.BOLD}{self.BLUE}📥 下载项目{self.RESET}")
        print(f"{self.BOLD}{self.CYAN}{'='*60}{self.RESET}")
        print(f"{self.GREEN}项目名称:{self.RESET} {self.BOLD}{project}{self.RESET}")
        if version:
            print(f"{self.GREEN}版本号:{self.RESET}   {self.BOLD}{self.YELLOW}v{version}{self.RESET}")
        if version_info:
            uploader = version_info.get('uploader_username', 'N/A')
            upload_time = version_info.get('uploaded_at', '').replace('T', ' ').split('.')[0]
            size = version_info.get('size_display', 'N/A')
            print(f"{self.GREEN}上传者:{self.RESET}   {uploader}")
            print(f"{self.GREEN}上传时间:{self.RESET} {upload_time}")
            print(f"{self.GREEN}文件大小:{self.RESET} {size}")
        print(f"{self.BOLD}{self.CYAN}{'='*60}{self.RESET}\n")
        
        if version:
            url = f"{self.base_url}/api/projects/{project}/download/{version}/"
        else:
            url = f"{self.base_url}/api/projects/{project}/download/"
        
        response = self.session.get(url, stream=True)
        if response.status_code != 200:
            error = response.json().get('error', '未知错误') if response.headers.get('content-type', '').startswith('application/json') else '未知错误'
            print(f"{self.RED}❌ 下载失败: {error}{self.RESET}")
            raise Exception(f"下载失败: {error}")
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            total_size = int(response.headers.get('content-length', 0))
            
            print(f"{self.BLUE}正在下载...{self.RESET}")
            with tqdm(total=total_size, unit='B', unit_scale=True, 
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                     desc=f"{self.CYAN}下载进度{self.RESET}") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                        pbar.update(len(chunk))
            
            tmp_path = tmp_file.name
        
        # 解压到目标目录
        target_path = Path(path) / project
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{self.BLUE}正在解压到: {self.BOLD}{target_path.absolute()}{self.RESET}")
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            # 获取所有文件列表
            file_list = zip_ref.namelist()
            with tqdm(total=len(file_list), unit='文件', 
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                     desc=f"{self.CYAN}解压进度{self.RESET}") as pbar:
                for file in file_list:
                    zip_ref.extract(file, target_path)
                    pbar.update(1)
        
        # 删除临时文件
        os.unlink(tmp_path)
        
        print(f"\n{self.BOLD}{self.GREEN}✓ 下载完成！{self.RESET}")
        print(f"{self.GREEN}项目已保存到: {self.BOLD}{target_path.absolute()}{self.RESET}\n")
    
    def upload(self, project: str, version: Optional[str] = None, path: str = './', 
               project_description: Optional[str] = None, version_description: Optional[str] = None):
        """上传项目
        
        Args:
            project: 项目名称（必填）
            version: 版本号（可选，默认自动递增）
            path: 上传路径（可选，默认当前目录）
            project_description: 项目描述（可选）
            version_description: 版本描述（可选）
        """
        upload_path = Path(path)
        if not upload_path.exists():
            raise Exception(f"路径不存在: {path}")
        
        # 创建zip文件
        print(f"{self.BLUE}正在压缩文件...{self.RESET}")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            zip_path = tmp_zip.name
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if upload_path.is_file():
                    # 单个文件
                    zipf.write(upload_path, upload_path.name)
                    file_count = 1
                else:
                    # 文件夹
                    files = list(upload_path.rglob('*'))
                    file_count = sum(1 for f in files if f.is_file())
                    with tqdm(total=file_count, unit='文件',
                             bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                             desc=f"{self.CYAN}压缩进度{self.RESET}") as pbar:
                        for file_path in files:
                            if file_path.is_file():
                                arcname = file_path.relative_to(upload_path)
                                zipf.write(file_path, arcname)
                                pbar.update(1)
            
            # 获取文件大小用于显示
            file_size = os.path.getsize(zip_path)
            file_size_display = self._format_size(file_size)
            
            # 打印开始信息
            print(f"\n{self.BOLD}{self.CYAN}{'='*60}{self.RESET}")
            print(f"{self.BOLD}{self.BLUE}📤 上传项目{self.RESET}")
            print(f"{self.BOLD}{self.CYAN}{'='*60}{self.RESET}")
            print(f"{self.GREEN}项目名称:{self.RESET} {self.BOLD}{project}{self.RESET}")
            if version:
                print(f"{self.GREEN}版本号:{self.RESET}   {self.BOLD}{self.YELLOW}v{version}{self.RESET}")
            else:
                print(f"{self.GREEN}版本号:{self.RESET}   {self.YELLOW}自动递增{self.RESET}")
            print(f"{self.GREEN}文件大小:{self.RESET} {file_size_display}")
            print(f"{self.GREEN}源路径:{self.RESET}   {upload_path.absolute()}")
            print(f"{self.BOLD}{self.CYAN}{'='*60}{self.RESET}\n")
            
            data = {'project': project}
            if version:
                data['version'] = version
            if project_description:
                data['project_description'] = project_description
            if version_description:
                data['version_description'] = version_description
            
            # 使用requests的流式上传显示进度
            class ProgressFile:
                def __init__(self, file_path, pbar):
                    self.file_obj = open(file_path, 'rb')
                    self.pbar = pbar
                    self.size = os.path.getsize(file_path)
                
                def read(self, size=-1):
                    chunk = self.file_obj.read(size)
                    if chunk:
                        self.pbar.update(len(chunk))
                    return chunk
                
                def seek(self, pos, whence=0):
                    return self.file_obj.seek(pos, whence)
                
                def tell(self):
                    return self.file_obj.tell()
                
                def __enter__(self):
                    return self
                
                def __exit__(self, *args):
                    self.file_obj.close()
            
            print(f"{self.BLUE}正在上传到服务器...{self.RESET}")
            with tqdm(total=file_size, unit='B', unit_scale=True,
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                     desc=f"{self.CYAN}上传进度{self.RESET}") as pbar:
                with ProgressFile(zip_path, pbar) as progress_file:
                    files = {'file': (f'{project}.zip', progress_file, 'application/zip')}
                    headers = {}
                    if self.csrf_token:
                        headers['X-CSRFToken'] = self.csrf_token
                    response = self.session.post(
                        f"{self.base_url}/api/upload/",
                        files=files,
                        data=data,
                        headers=headers
                    )
            
            if response.status_code == 200:
                result = response.json()
                uploaded_version = result.get('version', 'N/A')
                uploaded_size = self._format_size(result.get('size', 0))
                
                print(f"\n{self.BOLD}{self.GREEN}✓ 上传成功！{self.RESET}")
                print(f"{self.GREEN}项目名称: {self.BOLD}{project}{self.RESET}")
                print(f"{self.GREEN}版本号:   {self.BOLD}{self.YELLOW}v{uploaded_version}{self.RESET}")
                print(f"{self.GREEN}文件大小: {uploaded_size}\n")
            else:
                error = response.json().get('error', '未知错误')
                print(f"\n{self.RED}❌ 上传失败: {error}{self.RESET}\n")
                raise Exception(f"上传失败: {error}")
        
        finally:
            # 删除临时zip文件
            if os.path.exists(zip_path):
                os.unlink(zip_path)
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f}TB"
