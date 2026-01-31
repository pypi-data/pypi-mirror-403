from pathlib import Path
from importlib import resources

try:
    import yaml
except ImportError:
    yaml = None


# 1. 基础配置（极简）
CONFIG_FILENAME = "anjia_config.yaml"  # 本地配置文件名（当前目录）
# 内置默认配置（用户要修改的字段）
_DEFAULT_CONFIG_RESOURCE = "default_config.yaml"


def _load_yaml_mapping_from_text(text: str) -> dict:
    if yaml is None:
        raise RuntimeError("缺少依赖 PyYAML，请先安装：pip install PyYAML")

    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("YAML 根节点必须是 key-value 映射")
    return data


def _read_default_config_text() -> str:
    return (
        resources.files(__package__)
        .joinpath(_DEFAULT_CONFIG_RESOURCE)
        .read_text(encoding="utf-8")
    )


DEFAULT_CONFIG = _load_yaml_mapping_from_text(_read_default_config_text())

# 全局配置实例（加载后直接用）
CONFIG = {}


# 2. 核心加载函数（无热更新、无多线程）
def load_config(config_file: str | Path | None = None):
    """加载配置：优先读取当前目录配置文件，可指定自定义配置"""
    global CONFIG
    if config_file is None:
        config_path = Path.cwd() / CONFIG_FILENAME  # 配置文件在当前工作目录
    else:
        config_path = Path(config_file).expanduser()

    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                local_text = f.read()
            local_config = _load_yaml_mapping_from_text(local_text)
            config.update(local_config)
            print(f"✅ 已加载配置文件：{config_path}")
        except (OSError, yaml.YAMLError, ValueError) as exc:
            if config_file is not None:
                raise ValueError(f"❌ 指定配置文件格式错误：{config_path}") from exc
            print(f"❌ 配置文件{config_path}格式错误，使用默认配置")
    elif config_file is not None:
        raise FileNotFoundError(f"❌ 指定配置文件不存在：{config_path}")

    CONFIG.clear()
    CONFIG.update(config)


def export_default_config(*, force: bool = False) -> Path:
    """导出包内默认配置到当前工作目录"""
    target_path = Path.cwd() / CONFIG_FILENAME
    if target_path.exists() and not force:
        raise FileExistsError(str(target_path))

    content = _read_default_config_text()
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return target_path


# 3. 初始化（运行时自动加载）
load_config()