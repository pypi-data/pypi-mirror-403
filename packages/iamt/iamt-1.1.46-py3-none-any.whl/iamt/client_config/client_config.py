
"""
客户端配置管理模块

提供 SSH 连接配置的加载、管理和主机信息收集功能：
创建 ClientConfig 实例  实例初始化的最后一步 回去寻找iamt配置文件 
如果找到配置文件 则读取配置文件中的所有host信息 同步到 self.hosts
找到配置文件之后 应当搜索配置文件同级别目录下是否存在 .artifacts 目录如果没有则创建  

connect 函数 就是链接 管理器 
如果发现 self.hosts 是空的则说明没有找到配置文件/或者配置文件是空配置 
则询问用户服务器信息 得到这个信息就能够 通过 _create_connection_from_info 创建Connection实例 
从配置文件读取信息之后同样需要 使用 _create_connection_from_info 创建 Connection 实例 
"""

from ..decorators.singleton import Singleton
from fabric import Connection, Config
from pathlib import Path
from rich.console import Console
import logging
import questionary
import yaml
import paramiko

logging.getLogger("paramiko").setLevel(logging.CRITICAL)


@Singleton
class ClientConfig():
    
    @staticmethod
    def _find_config_file() -> Path:
        """向上遍历目录查找 iamt.yaml，找不到则返回当前目录下的路径"""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            candidate = parent / "iamt.yaml"
            if candidate.exists():
                return candidate
        return current / "iamt.yaml"
    
    def __init__(self):
        self._console = Console()
        self.config_file = self._find_config_file()  # 实例化时查找配置文件
        self.hosts: dict[str, dict] = {}  # 所有 host 配置
        self.conn: Connection | None = None  # 当前连接
        self.hostvars: dict = {}  # 当前连接的主机信息
        self._current_host: str | None = None  # 当前连接的 host 名称
        
        if self.config_file.exists():
            self._load_all_hosts()
            self._ensure_artifacts_dir()
    
    # region 配置加载
    def _load_all_hosts(self) -> None:
        """从配置文件加载所有 host 信息"""
        try:
            content = self.config_file.read_text(encoding="utf-8")
            if not content.strip():
                self._console.print(f"[yellow]⚠[/yellow] 配置文件 {self.config_file} 为空")
                self.hosts = {}
                return
                
            config_data = yaml.safe_load(content)
            if config_data is None:
                self._console.print(f"[yellow]⚠[/yellow] 配置文件 {self.config_file} 内容无效")
                self.hosts = {}
                return
                
            if not isinstance(config_data, dict):
                self._console.print(f"[red]✗[/red] 配置文件 {self.config_file} 格式错误：根节点必须是字典")
                self.hosts = {}
                return
                
            hosts_data = config_data.get("hosts")
            if hosts_data is None:
                self._console.print(f"[yellow]⚠[/yellow] 配置文件 {self.config_file} 中未找到 'hosts' 字段")
                self.hosts = {}
                return
                
            if not isinstance(hosts_data, dict):
                self._console.print(f"[red]✗[/red] 配置文件 {self.config_file} 中 'hosts' 字段必须是字典")
                self.hosts = {}
                return
                
            self.hosts = hosts_data
            self._console.print(f"[green]✓[/green] 成功加载 {len(self.hosts)} 个主机配置")
            
        except yaml.YAMLError as e:
            self._console.print(f"[red]✗[/red] YAML 解析错误: {e}")
            self.hosts = {}
        except UnicodeDecodeError as e:
            self._console.print(f"[red]✗[/red] 文件编码错误: {e}")
            self.hosts = {}
        except Exception as e:
            self._console.print(f"[red]✗[/red] 加载配置文件失败: {e}")
            self.hosts = {}
    
    def _ensure_artifacts_dir(self) -> Path:
        """确保配置文件同级目录下存在 .artifacts 目录，用于临时存放下载的软件安装包"""
        artifacts_dir = self.config_file.parent / ".artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        return artifacts_dir
    
    @property
    def artifacts_dir(self) -> Path:
        """获取 .artifacts 目录路径，如不存在则创建"""
        return self._ensure_artifacts_dir()
    
    def get_host_names(self) -> list[str]:
        """获取所有可用的 host 名称"""
        return list(self.hosts.keys())
    
    def get_host_info(self, hostname: str) -> dict | None:
        """获取指定 host 的配置信息"""
        return self.hosts.get(hostname)
    # endregion
    
    # region 连接管理
    def connect(self, hostname: str | None = None) -> Connection | None:
        """
        建立到目标服务器的 SSH 连接，并收集主机信息。
        
        这是 ClientConfig 的核心方法，负责管理 SSH 连接的生命周期。
        连接成功后会自动调用 _gather_facts() 收集主机信息，并将其挂载到
        conn.hostvars 属性上，供后续 task 函数使用。
        
        连接策略：
        1. 复用检查：如果已连接到同一 host，直接返回现有连接（避免重复连接）
        2. 清理旧连接：建立新连接前先断开现有连接
        3. 主机选择：
           - 无配置文件：交互式收集服务器信息并创建连接
           - 有配置文件：根据 hostname 参数或交互选择确定目标主机
        4. 信息收集：连接成功后自动收集 hostvars（类似 Ansible 的 setup 模块）
        
        Args:
            hostname: 目标主机名称（对应 iamt.yaml 中 hosts 下的 key）
                     - 指定具体名称：直接连接该主机
                     - None 且只有一个主机：自动选择唯一主机
                     - None 且有多个主机：弹出交互式选择菜单
            
        Returns:
            Connection: fabric 的 Connection 对象，包含额外的 hostvars 属性
            None: 连接失败或用户取消时返回
            
        Side Effects:
            - 更新 self.conn: 当前活动的 Connection 对象
            - 更新 self.hostvars: 当前主机的收集信息
            - 更新 self._current_host: 当前连接的主机名称
            - 可能创建 iamt.yaml: 当无配置文件时通过交互收集信息
            
        Example:
            >>> config = ClientConfig()
            >>> conn = config.connect("my-server")  # 连接指定主机
            >>> conn = config.connect()  # 交互选择或自动选择
            >>> print(conn.hostvars["distribution"]["name"])  # 访问主机信息
        """
        # 复用检查：如果已连接到同一 host，直接返回现有连接
        # 这避免了重复建立 SSH 连接的开销
        if hostname and hostname == self._current_host and self.conn:
            return self.conn
        
        # 清理旧连接：确保同一时刻只维护一个活动连接
        self.disconnect()
        
        # 主机选择与连接建立
        if not self.hosts:
            # 无配置文件场景：交互式收集服务器信息
            # 这通常发生在首次使用或 iamt.yaml 不存在时
            info = self.collect_server_info()
            if info is None or not info.get("host"):
                self._console.print("[yellow]⚠[/yellow] 未提供服务器地址，退出")
                return None
            self.conn = self._create_connection_from_info(info)
        else:
            # 有配置文件场景：从 hosts 配置中选择目标主机
            hostname = self._resolve_hostname(hostname)
            if hostname is None:
                return None
            host_info = self.hosts[hostname]
            self.conn = self._create_connection_from_info(host_info)
            self._current_host = hostname
        
        # 连接失败检查
        if self.conn is None:
            return None
        
        # 收集主机信息并挂载到 Connection 对象
        # hostvars 类似 Ansible 的 hostvars，包含 OS、内存、网络等信息
        # task 函数可通过 conn.hostvars 访问这些预收集的数据
        self.hostvars = self._gather_facts()
        self.conn.hostvars = self.hostvars
        self.conn.artifacts_dir = self.artifacts_dir
        return self.conn
    
    def _resolve_hostname(self, hostname: str | None) -> str | None:
        """解析 hostname，为 None 时自动选择"""
        if hostname:
            if hostname not in self.hosts:
                self._console.print(f"[red]✗[/red] 未找到 host: [bold]{hostname}[/bold]，可用: {', '.join(self.hosts.keys())}")
                return None
            return hostname
        
        # 只有一个 host 时直接使用
        if len(self.hosts) == 1:
            return next(iter(self.hosts))
        
        # 多个 host 时交互选择，显示详细信息
        choices = []
        for name, info in self.hosts.items():
            host = info.get("host", "")
            user = info.get("user", "")
            port = info.get("port", "22")
            label = f"{name} ({user}@{host}:{port})"
            choices.append(questionary.Choice(title=label, value=name))
        
        selected = questionary.select("请选择要连接的服务器:", choices=choices).ask()
        return selected
    
    def disconnect(self) -> None:
        """断开当前连接"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
            self.hostvars = {}
            self._current_host = None
    
    def _load_private_key(self, key_filename: str, passphrase: str | None = None) -> paramiko.PKey | None:
        """
        尝试加载私钥，支持多种格式：RSA, ECDSA, Ed25519
        
        Args:
            key_filename: 私钥文件路径
            passphrase: 私钥密码（可选）
            
        Returns:
            paramiko.PKey: 成功加载的私钥对象
            None: 加载失败
        """
        key_path = Path(key_filename).expanduser()
        if not key_path.exists():
            return None
            
        # 尝试不同的私钥格式（只使用当前 paramiko 版本支持的）
        key_classes = [
            paramiko.RSAKey,
            paramiko.ECDSAKey,
            paramiko.Ed25519Key
        ]
        
        for key_class in key_classes:
            try:
                return key_class.from_private_key_file(str(key_path), password=passphrase)
            except paramiko.PasswordRequiredException:
                # 需要密码但未提供
                self._console.print(f"[yellow]⚠[/yellow] 私钥 {key_path} 需要密码")
                return None
            except (paramiko.SSHException, ValueError):
                # 格式不匹配，尝试下一种
                continue
            except Exception:
                # 其他错误，尝试下一种
                continue
                
        return None

    def _create_connection_from_info(self, host_info: dict) -> Connection | None:
        """根据 host_info 创建连接，支持密码和私钥两种认证方式"""
        # 构建 sudo 配置
        sudo_config = {}
        if host_info.get("sudo_password"):
            sudo_config["password"] = host_info["sudo_password"]
        
        config = Config(overrides={"sudo": sudo_config})
        
        try:
            # 构建连接参数
            connect_kwargs = {}
            auth_method = host_info.get("auth_method", "password")
            
            if auth_method == "password":
                # 密码认证
                connect_kwargs["password"] = host_info["password"]
            else:
                # 私钥认证 - 支持多种私钥格式
                key_filename = host_info["key_filename"]
                passphrase = host_info.get("key_passphrase")
                
                # 尝试加载私钥，支持多种格式
                pkey = self._load_private_key(key_filename, passphrase)
                if pkey:
                    connect_kwargs["pkey"] = pkey
                else:
                    # 如果无法加载私钥对象，回退到文件路径方式
                    connect_kwargs["key_filename"] = key_filename
                    if passphrase:
                        connect_kwargs["passphrase"] = passphrase
            
            conn = Connection(
                host=host_info["host"],
                port=int(host_info.get("port", 22)),
                user=host_info["user"],
                connect_kwargs=connect_kwargs,
                config=config,
            )
            conn.open()
            return conn
        except Exception as e:
            self._console.print(f"[red]✗[/red] 连接服务器失败: {e}")
            return None
    # endregion 
                
        
        
    # region 用户输入收集
    def collect_server_info(self) -> dict[str, str] | None:
        """通过交互式问答收集服务器连接信息并写入 iamt.yaml，用户取消时返回 None"""
        hostname = questionary.text("请输入主机名 (用于标识此服务器):").ask()
        if hostname is None:
            return None

        ip = questionary.text("请输入服务器IP地址:").ask()
        if ip is None:
            return None

        port = questionary.text("请输入SSH端口:", default="22").ask()
        if port is None:
            return None

        username = questionary.text("请输入用户名:").ask()
        if username is None:
            return None

        # 选择认证方式
        auth_method = questionary.select(
            "请选择认证方式:",
            choices=[
                questionary.Choice("密码认证", "password"),
                questionary.Choice("私钥认证", "key")
            ]
        ).ask()
        if auth_method is None:
            return None

        host_entry = {
            "host": ip,
            "port": port,
            "user": username,
            "auth_method": auth_method,
        }

        if auth_method == "password":
            password = questionary.password("请输入密码:", default="vagrant").ask()
            if password is None:
                return None
            host_entry["password"] = password
        else:  # key authentication
            key_path = questionary.path(
                "请输入私钥文件路径:",
                default="~/.ssh/id_rsa"
            ).ask()
            if key_path is None:
                return None
            
            # 展开用户目录
            key_path = Path(key_path).expanduser()
            if not key_path.exists():
                self._console.print(f"[red]✗[/red] 私钥文件不存在: {key_path}")
                return None
            
            host_entry["key_filename"] = str(key_path)
            
            # 检查私钥是否需要密码
            key_passphrase = questionary.password(
                "请输入私钥密码 (如无密码请直接回车):"
            ).ask()
            if key_passphrase is None:
                return None
            if key_passphrase:
                host_entry["key_passphrase"] = key_passphrase

        sudo_password = questionary.password("请输入SUDO密码 (留空则与登录密码相同):").ask()
        if sudo_password is None:
            return None
        
        # 设置 sudo 密码
        if auth_method == "password":
            host_entry["sudo_password"] = sudo_password or host_entry["password"]
        else:
            if sudo_password:
                host_entry["sudo_password"] = sudo_password
            else:
                self._console.print("[yellow]⚠[/yellow] 私钥认证时建议设置 sudo 密码")
                host_entry["sudo_password"] = ""
        
        confirm = questionary.confirm(f"是否将配置写入 {self.config_file}?", default=True).ask()
        if confirm is None or not confirm:
            self._console.print("[yellow]⚠[/yellow] 用户取消写入配置文件")
            return host_entry
        
        # 手动格式化为 flow style: hosts:\n  hostname: {key: value, ...}
        flow_entry = yaml.dump(host_entry, default_flow_style=True, allow_unicode=True).strip()
        yaml_content = f"hosts:\n  {hostname}: {flow_entry}\n"
        self.config_file.write_text(yaml_content, encoding="utf-8")
        return host_entry
    # endregion
    

    
    # region 主机信息收集
    def _gather_facts(self) -> dict:
        """收集主机基础信息，类似 Ansible setup 模块"""
        facts = {}
        
        # 发行版信息
        os_release = self._run_cmd("cat /etc/os-release 2>/dev/null || cat /etc/*-release 2>/dev/null | head -20")
        facts["distribution"] = self._parse_os_release(os_release)
        
        # 主机名
        facts["hostname"] = self._run_cmd("hostname").strip()
        facts["fqdn"] = self._run_cmd("hostname -f 2>/dev/null || hostname").strip()
        
        # 内核信息
        facts["kernel"] = self._run_cmd("uname -r").strip()
        facts["architecture"] = self._run_cmd("uname -m").strip()
        
        # 内存信息 (KB)
        meminfo = self._run_cmd("cat /proc/meminfo")
        facts["memory"] = self._parse_meminfo(meminfo)
        
        # CPU 信息
        facts["processor_count"] = int(self._run_cmd("nproc").strip() or "1")
        
        # 网络接口
        facts["default_ipv4"] = self._get_default_ipv4()
        
        # 用户信息
        facts["user"] = self._run_cmd("whoami").strip()
        facts["user_home"] = self._run_cmd("echo $HOME").strip()
        
        return facts
    
    def _run_cmd(self, cmd: str) -> str:
        """执行命令并返回输出，失败时返回空字符串"""
        try:
            result = self.conn.run(cmd, hide=True, warn=True)
            return result.stdout if result.ok else ""
        except Exception:
            return ""
    
    def _parse_os_release(self, content: str) -> dict:
        """解析 /etc/os-release 内容"""
        info = {"name": "", "version": "", "version_id": "", "codename": "", "id": "", "id_like": ""}
        for line in content.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                value = value.strip('"\'')
                key_lower = key.lower()
                if key_lower == "name":
                    info["name"] = value
                elif key_lower == "version":
                    info["version"] = value
                elif key_lower == "version_id":
                    info["version_id"] = value
                elif key_lower == "version_codename":
                    info["codename"] = value
                elif key_lower == "id":
                    info["id"] = value
                elif key_lower == "id_like":
                    info["id_like"] = value
        # 如果 id_like 为空，使用 id 作为回退
        if not info["id_like"]:
            info["id_like"] = info["id"]
        return info
    
    def _parse_meminfo(self, content: str) -> dict:
        """解析 /proc/meminfo 内容，返回 MB 单位"""
        mem = {"total_mb": 0, "free_mb": 0, "available_mb": 0}
        for line in content.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                key, value = parts[0].rstrip(":"), parts[1]
                if key == "MemTotal":
                    mem["total_mb"] = int(value) // 1024
                elif key == "MemFree":
                    mem["free_mb"] = int(value) // 1024
                elif key == "MemAvailable":
                    mem["available_mb"] = int(value) // 1024
        return mem
    
    def _get_default_ipv4(self) -> dict:
        """获取默认 IPv4 地址和网关"""
        info = {"address": "", "gateway": "", "interface": ""}
        route = self._run_cmd("ip route get 1.1.1.1 2>/dev/null | head -1")
        if route:
            parts = route.split()
            for i, p in enumerate(parts):
                if p == "src" and i + 1 < len(parts):
                    info["address"] = parts[i + 1]
                elif p == "via" and i + 1 < len(parts):
                    info["gateway"] = parts[i + 1]
                elif p == "dev" and i + 1 < len(parts):
                    info["interface"] = parts[i + 1]
        return info
    # endregion