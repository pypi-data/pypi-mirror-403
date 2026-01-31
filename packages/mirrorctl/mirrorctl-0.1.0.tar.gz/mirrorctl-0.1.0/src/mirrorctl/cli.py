"""Command-line interface for mirrorctl."""

from __future__ import annotations

import argparse
import configparser
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple
import xml.etree.ElementTree as ET


@dataclass
class Tool:
    name: str
    description: str
    apply: Callable[[str], None]
    current: Callable[[], Optional[str]]


OFFICIAL_PROVIDERS: Dict[str, Dict[str, str]] = {
    "official": {
        "pip": "https://pypi.org/simple",
        "npm": "https://registry.npmjs.org/",
        "pnpm": "https://registry.npmjs.org/",
        "yarn": "https://registry.npmjs.org/",
        "cargo": "https://github.com/rust-lang/crates.io-index",
        "gem": "https://rubygems.org/",
        "go": "https://proxy.golang.org,direct",
        "maven": "https://repo.maven.apache.org/maven2",
        "conda": "https://repo.anaconda.com/pkgs/main,https://repo.anaconda.com/pkgs/r",
    },
    "tuna": {
        "pip": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "npm": "https://registry.npmmirror.com/",
        "pnpm": "https://registry.npmmirror.com/",
        "yarn": "https://registry.npmmirror.com/",
        "cargo": "https://mirrors.tuna.tsinghua.edu.cn/git/crates.io-index.git",
        "gem": "https://mirrors.tuna.tsinghua.edu.cn/rubygems/",
        "go": "https://mirrors.tuna.tsinghua.edu.cn/goproxy/,direct",
        "maven": "https://mirrors.tuna.tsinghua.edu.cn/maven",
        "conda": "https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main,https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free,https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r",
    }
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "mirrorctl"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "mirrorctl"


def _config_path() -> Path:
    return _config_dir() / "config.json"


def _load_state() -> Dict[str, Dict[str, Dict[str, str]]]:
    path = _config_path()
    if not path.exists():
        return {"tools": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"tools": {}}


def _save_state(state: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")


def _set_state(tool: str, provider: str, url: str) -> None:
    state = _load_state()
    state.setdefault("tools", {})[tool] = {
        "provider": provider,
        "url": url,
        "updated_at": _now_iso(),
    }
    _save_state(state)


def _pip_config_path() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "pip" / "pip.ini"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pip" / "pip.conf"


def _npmrc_path() -> Path:
    return Path.home() / ".npmrc"


def _yarnrc_path() -> Path:
    return Path.home() / ".yarnrc"


def _yarnrc_yaml_path() -> Path:
    return Path.home() / ".yarnrc.yml"


def _cargo_config_path() -> Path:
    return Path.home() / ".cargo" / "config.toml"


def _gemrc_path() -> Path:
    return Path.home() / ".gemrc"


def _go_env_path() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "go" / "env"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "go" / "env"


def _maven_settings_path() -> Path:
    return Path.home() / ".m2" / "settings.xml"


def _conda_config_path() -> Path:
    return Path.home() / ".condarc"


def _read_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")


def _set_key_value_line(lines: List[str], key: str, value: str) -> List[str]:
    updated = False
    for idx, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[idx] = f"{key}={value}"
            updated = True
    if not updated:
        lines.append(f"{key}={value}")
    return lines


def _remove_key_value_line(lines: List[str], key: str) -> List[str]:
    return [line for line in lines if not line.strip().startswith(f"{key}=")]


def _pip_apply(url: str) -> None:
    path = _pip_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser()
    if path.exists():
        parser.read(path, encoding="utf-8")
    if not parser.has_section("global"):
        parser.add_section("global")
    parser.set("global", "index-url", url)
    with path.open("w", encoding="utf-8") as handle:
        parser.write(handle)


def _pip_current() -> Optional[str]:
    path = _pip_config_path()
    if not path.exists():
        return None
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    if parser.has_section("global") and parser.has_option("global", "index-url"):
        return parser.get("global", "index-url")
    return None


def _npm_apply(url: str) -> None:
    path = _npmrc_path()
    lines = _read_lines(path)
    lines = _set_key_value_line(lines, "registry", url)
    _write_lines(path, lines)


def _npm_current() -> Optional[str]:
    path = _npmrc_path()
    lines = _read_lines(path)
    for line in lines:
        if line.strip().startswith("registry="):
            return line.split("=", 1)[1].strip()
    return None


def _pnpm_apply(url: str) -> None:
    _npm_apply(url)


def _pnpm_current() -> Optional[str]:
    return _npm_current()


def _yarn_apply(url: str) -> None:
    yaml_path = _yarnrc_yaml_path()
    yaml_lines = _read_lines(yaml_path)
    updated = False
    for idx, line in enumerate(yaml_lines):
        if line.strip().startswith("npmRegistryServer:"):
            yaml_lines[idx] = f"npmRegistryServer: \"{url}\""
            updated = True
    if not updated:
        yaml_lines.append(f"npmRegistryServer: \"{url}\"")
    _write_lines(yaml_path, yaml_lines)

    rc_path = _yarnrc_path()
    rc_lines = _read_lines(rc_path)
    updated = False
    for idx, line in enumerate(rc_lines):
        if line.strip().startswith("registry"):
            rc_lines[idx] = f'registry "{url}"'
            updated = True
    if not updated:
        rc_lines.append(f'registry "{url}"')
    _write_lines(rc_path, rc_lines)


def _yarn_current() -> Optional[str]:
    yaml_path = _yarnrc_yaml_path()
    yaml_lines = _read_lines(yaml_path)
    for line in yaml_lines:
        if line.strip().startswith("npmRegistryServer:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    rc_path = _yarnrc_path()
    rc_lines = _read_lines(rc_path)
    for line in rc_lines:
        striped = line.strip()
        if striped.startswith("registry"):
            parts = striped.split(None, 1)
            if len(parts) == 2:
                return parts[1].strip().strip('"').strip("'")
    return None


def _cargo_apply(url: str) -> None:
    path = _cargo_config_path()
    lines = _read_lines(path)
    lines = _remove_toml_sections(lines, {"source.crates-io", "source.mirrorctl"})
    lines.append("[source.crates-io]")
    lines.append("replace-with = \"mirrorctl\"")
    lines.append("")
    lines.append("[source.mirrorctl]")
    lines.append(f"registry = \"{url}\"")
    _write_lines(path, lines)


def _cargo_current() -> Optional[str]:
    path = _cargo_config_path()
    lines = _read_lines(path)
    capture = False
    for line in lines:
        if line.strip() == "[source.mirrorctl]":
            capture = True
            continue
        if line.strip().startswith("["):
            capture = False
        if capture and line.strip().startswith("registry"):
            return line.split("=", 1)[1].strip().strip("\"")
    return None


def _gem_apply(url: str) -> None:
    path = _gemrc_path()
    lines = _read_lines(path)
    lines = _remove_gem_sources(lines)
    lines.append(":sources:")
    lines.append(f"- {url}")
    _write_lines(path, lines)


def _gem_current() -> Optional[str]:
    path = _gemrc_path()
    lines = _read_lines(path)
    capture = False
    for line in lines:
        if line.strip() == ":sources:":
            capture = True
            continue
        if capture:
            if line.strip().startswith("-"):
                return line.strip().lstrip("-").strip()
            if line.strip().startswith(":"):
                return None
    return None


def _go_apply(url: str) -> None:
    path = _go_env_path()
    lines = _read_lines(path)
    lines = _set_key_value_line(lines, "GOPROXY", url)
    _write_lines(path, lines)


def _go_current() -> Optional[str]:
    path = _go_env_path()
    lines = _read_lines(path)
    for line in lines:
        if line.strip().startswith("GOPROXY="):
            return line.split("=", 1)[1].strip()
    return None


def _maven_apply(url: str) -> None:
    path = _maven_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        tree = ET.parse(path)
        root = tree.getroot()
    else:
        root = ET.Element("settings")
        tree = ET.ElementTree(root)

    ns = _xml_ns(root.tag)
    mirrors = root.find(_xml_tag(ns, "mirrors"))
    if mirrors is None:
        mirrors = ET.SubElement(root, _xml_tag(ns, "mirrors"))

    mirror = None
    for item in mirrors.findall(_xml_tag(ns, "mirror")):
        mirror_id = item.find(_xml_tag(ns, "id"))
        if mirror_id is not None and mirror_id.text == "mirrorctl":
            mirror = item
            break

    if mirror is None:
        mirror = ET.SubElement(mirrors, _xml_tag(ns, "mirror"))

    _ensure_xml_text(mirror, ns, "id", "mirrorctl")
    _ensure_xml_text(mirror, ns, "name", "mirrorctl")
    _ensure_xml_text(mirror, ns, "url", url)
    _ensure_xml_text(mirror, ns, "mirrorOf", "central")

    tree.write(path, encoding="utf-8", xml_declaration=True)


def _maven_current() -> Optional[str]:
    path = _maven_settings_path()
    if not path.exists():
        return None
    tree = ET.parse(path)
    root = tree.getroot()
    ns = _xml_ns(root.tag)
    mirrors = root.find(_xml_tag(ns, "mirrors"))
    if mirrors is None:
        return None
    for mirror in mirrors.findall(_xml_tag(ns, "mirror")):
        mirror_id = mirror.find(_xml_tag(ns, "id"))
        if mirror_id is not None and mirror_id.text == "mirrorctl":
            url = mirror.find(_xml_tag(ns, "url"))
            if url is not None:
                return url.text
    return None


def _conda_apply(url: str) -> None:
    path = _conda_config_path()
    channels = [item.strip() for item in url.split(",") if item.strip()]
    lines = ["channels:"]
    for channel in channels:
        lines.append(f"  - {channel}")
    lines.append("show_channel_urls: true")
    _write_lines(path, lines)


def _conda_current() -> Optional[str]:
    path = _conda_config_path()
    lines = _read_lines(path)
    channels: List[str] = []
    capture = False
    for line in lines:
        striped = line.strip()
        if striped.startswith("channels:"):
            capture = True
            continue
        if capture:
            if striped.startswith("-"):
                channels.append(striped.lstrip("-").strip())
                continue
            if striped and not striped.startswith("#") and not striped.startswith("-"):
                break
    if channels:
        return ",".join(channels)
    return None


def _xml_ns(tag: str) -> Optional[str]:
    if tag.startswith("{") and "}" in tag:
        return tag[1 : tag.index("}")]
    return None


def _xml_tag(ns: Optional[str], tag: str) -> str:
    if not ns:
        return tag
    return f"{{{ns}}}{tag}"


def _ensure_xml_text(parent: ET.Element, ns: Optional[str], tag: str, value: str) -> None:
    element = parent.find(_xml_tag(ns, tag))
    if element is None:
        element = ET.SubElement(parent, _xml_tag(ns, tag))
    element.text = value


def _remove_toml_sections(lines: List[str], sections: set) -> List[str]:
    trimmed: List[str] = []
    skip = False
    for line in lines:
        striped = line.strip()
        if striped.startswith("[") and striped.endswith("]"):
            name = striped.strip("[]")
            skip = name in sections
        if not skip:
            trimmed.append(line)
    return trimmed


def _remove_gem_sources(lines: List[str]) -> List[str]:
    trimmed: List[str] = []
    skip = False
    for line in lines:
        striped = line.strip()
        if striped == ":sources:":
            skip = True
            continue
        if skip and striped.startswith(":"):
            skip = False
        if not skip:
            trimmed.append(line)
    return trimmed


def _tools() -> Dict[str, Tool]:
    return {
        "pip": Tool("pip", "Python (pip) index-url", _pip_apply, _pip_current),
        "npm": Tool("npm", "Node.js (npm) registry", _npm_apply, _npm_current),
        "pnpm": Tool("pnpm", "pnpm registry (uses .npmrc)", _pnpm_apply, _pnpm_current),
        "yarn": Tool("yarn", "Yarn registry", _yarn_apply, _yarn_current),
        "cargo": Tool("cargo", "Rust (cargo) registry", _cargo_apply, _cargo_current),
        "gem": Tool("gem", "RubyGems sources", _gem_apply, _gem_current),
        "go": Tool("go", "Go GOPROXY", _go_apply, _go_current),
        "maven": Tool("maven", "Maven central mirror", _maven_apply, _maven_current),
        "conda": Tool("conda", "Conda channels", _conda_apply, _conda_current),
    }


def _resolve_provider(tool: str, provider: Optional[str], url: Optional[str]) -> Tuple[str, str]:
    if url:
        return "custom", url
    if not provider:
        raise ValueError("必须指定 --provider 或 --url")
    provider_map = OFFICIAL_PROVIDERS.get(provider)
    if not provider_map:
        raise ValueError(f"未知 provider: {provider}")
    if tool not in provider_map:
        raise ValueError(f"provider {provider} 不支持 {tool}")
    return provider, provider_map[tool]


def cmd_list(_: argparse.Namespace) -> int:
    tools = _tools()
    state = _load_state().get("tools", {})
    for name in sorted(tools):
        tool = tools[name]
        current = tool.current() or "-"
        provider = state.get(name, {}).get("provider", "-")
        print(f"{name:8} {provider:10} {current}")
    return 0


def cmd_providers(_: argparse.Namespace) -> int:
    tools = _tools()
    names = sorted(OFFICIAL_PROVIDERS)
    if not names:
        print("没有内置 provider")
        return 0
    header = "provider".ljust(12) + "tools"
    print(header)
    for name in names:
        supported = [t for t in tools if t in OFFICIAL_PROVIDERS[name]]
        print(f"{name:12} {', '.join(sorted(supported))}")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    tools = _tools()
    tool = tools.get(args.tool)
    if not tool:
        print(f"未知工具: {args.tool}", file=sys.stderr)
        return 2
    try:
        provider, url = _resolve_provider(args.tool, args.provider, args.url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    tool.apply(url)
    _set_state(args.tool, provider, url)
    print(f"{args.tool} 已设置为 {url}")
    return 0


def cmd_current(args: argparse.Namespace) -> int:
    tools = _tools()
    tool = tools.get(args.tool)
    if not tool:
        print(f"未知工具: {args.tool}", file=sys.stderr)
        return 2
    current = tool.current()
    if not current:
        print("未设置")
        return 1
    print(current)
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    args.provider = "official"
    args.url = None
    return cmd_set(args)


def cmd_set_all(args: argparse.Namespace) -> int:
    tools = _tools()
    supported = OFFICIAL_PROVIDERS.get(args.provider, {})
    if not supported:
        print(f"未知 provider: {args.provider}", file=sys.stderr)
        return 2
    failures = []
    for name, tool in tools.items():
        if name not in supported:
            continue
        try:
            provider, url = _resolve_provider(name, args.provider, None)
        except ValueError as exc:
            failures.append(f"{name}: {exc}")
            continue
        tool.apply(url)
        _set_state(name, provider, url)
        print(f"{name} 已设置为 {url}")
    if failures:
        print("部分工具设置失败：", file=sys.stderr)
        for item in failures:
            print(item, file=sys.stderr)
        return 1
    return 0


def cmd_tuna(_: argparse.Namespace) -> int:
    args = argparse.Namespace(provider="tuna")
    return cmd_set_all(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mirrorctl", description="管理开发工具镜像源")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="列出已支持工具及当前镜像")
    list_parser.set_defaults(func=cmd_list)

    providers_parser = sub.add_parser("providers", help="列出内置 provider")
    providers_parser.set_defaults(func=cmd_providers)

    set_parser = sub.add_parser("set", help="设置某个工具的镜像")
    set_parser.add_argument("tool", help="工具名称")
    set_parser.add_argument("--provider", help="内置 provider 名称")
    set_parser.add_argument("--url", help="自定义镜像 URL")
    set_parser.set_defaults(func=cmd_set)

    current_parser = sub.add_parser("current", help="查看某个工具的当前镜像")
    current_parser.add_argument("tool", help="工具名称")
    current_parser.set_defaults(func=cmd_current)

    reset_parser = sub.add_parser("reset", help="恢复为官方镜像")
    reset_parser.add_argument("tool", help="工具名称")
    reset_parser.set_defaults(func=cmd_reset)

    set_all_parser = sub.add_parser("set-all", help="批量设置 provider 的镜像")
    set_all_parser.add_argument("--provider", required=True, help="内置 provider 名称")
    set_all_parser.set_defaults(func=cmd_set_all)

    tuna_parser = sub.add_parser("tuna", help="一键设置清华 TUNA 镜像")
    tuna_parser.set_defaults(func=cmd_tuna)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
