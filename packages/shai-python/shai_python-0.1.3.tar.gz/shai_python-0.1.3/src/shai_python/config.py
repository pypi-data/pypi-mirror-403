import importlib.resources as pkg_resources
import os
import platform
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

# ANSI color codes for colored output
GREEN = "\033[92m"  # Green for safe
YELLOW = "\033[93m"  # Yellow for caution
RED = "\033[91m"  # Red for danger
RESET = "\033[0m"  # Reset color
BOLD = "\033[1m"  # Bold text


class ProviderConfig(BaseModel):
    api_key: str = Field(..., min_length=1, description="API key cannot be empty")
    base_url: str | None = None


class ModelConfig(BaseModel):
    id: str = Field(..., min_length=1, description="Model ID cannot be empty")
    provider: str = Field(..., min_length=1, description="Provider name cannot be empty")
    alias: str | None = None


class GlobalConfig(BaseModel):
    default_model: str = Field(..., min_length=1, description='effective model')
    providers: dict[str, ProviderConfig]
    models: list[ModelConfig]


class ShellCommand(BaseModel):
    """Shell command structure returned by the model"""
    command: str = Field(..., description="Generated shell command")
    explanation: str = Field(..., description="Command explanation")
    risk: str = Field(..., description="Risk levels (low risk: 'safe', harmless commands), 'caution' (medium risk, may have side effects), or 'danger' (high risk, potentially harmful).")


class ConfigManager:
    APP_NAME = "shai"
    # 使用当前工作目录下的配置目录，避免权限问题
    CONFIG_DIR = Path.home() / ".config" / APP_NAME
    CONFIG_FILE = CONFIG_DIR / "config.yaml"

    @classmethod
    def ensure_config(cls) -> bool:
        """初始化配置，如果不存在则从模版复制"""
        if not cls.CONFIG_FILE.exists():
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            try:
                # 使用 importlib.resources 从包内读取模版
                # 假设模版在 shai_python 包下
                template_data = pkg_resources.read_text("shai_python", "config.template.yaml")
                with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                    f.write(template_data)
                return True  # 表示是第一次初始化
            except Exception as e:
                print(f"Error initializing config: {e}")
        return False

    @classmethod
    def get_edit_command(cls) -> ShellCommand:
        """获取编辑配置的 ShellCommand 对象"""
        system = platform.system()
        config_path = str(cls.CONFIG_FILE)

        if system == "Windows":
            cmd = f"notepad {config_path}"
        else:
            # 优先使用环境变量 $EDITOR，默认为 vim
            editor = os.environ.get("EDITOR", "vim")
            cmd = f"{editor} {config_path}"

        explanation = (
            "该命令将使用您的默认编辑器打开配置文件。\n"
            "需要在此配置服务商的api key及相关参数，以便程序能够正常调用模型接口。\n"
            f"任何时候可以通过{YELLOW}'shai config'{RESET}显示此命令。"
        )

        return ShellCommand(
            command=cmd,
            explanation=explanation,
            risk="safe"
        )

    @classmethod
    def load_and_validate(cls) -> GlobalConfig:
        """加载并校验配置"""
        if not cls.CONFIG_FILE.exists():
            raise FileNotFoundError("Configuration file missing.")

        with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
            # 简单的环境变量替换支持 (可选)
            content = f.read()
            # 匹配 ${VAR} 并替换
            import re

            content = re.sub(r"\${(\w+)}", lambda m: os.getenv(m.group(1), m.group(0)), content)

            data = yaml.safe_load(content)
            return GlobalConfig(**data)
