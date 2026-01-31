#!/usr/bin/python3
# -*- coding: utf8 -*-

# Copyright (c) 2025 ZWDX, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import getpass
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from minjiang_client.utility_manager import utility_manager
from minjiang_client.utils.local import get_gui_addr, get_user_temp_token
from minjiang_client.com.user import login

try:
    from minjiang_host_client.utils.local import get_cache_dir as get_host_cache_dir
except ImportError:
    get_host_cache_dir = None


def cmd_login(token: str = None):
    """登录命令"""
    if token is None:
        token = getpass.getpass("请输入您的 token: ").strip()

    if not token:
        print("错误: token 不能为空")
        sys.exit(1)

    try:
        print("正在登录...")
        user_name = login(token)
        print(f"✓ 登录成功！用户名: {user_name}")
        return user_name
    except Exception as e:
        print(f"登录失败: {e}")
        sys.exit(1)


def _get_log_file_path(group_name: str) -> str:
    """获取日志文件路径"""
    try:
        if get_host_cache_dir:
            host_cache_root = get_host_cache_dir()
        else:
            host_cache_root = str(Path.home() / "minjiang_host_client_cache")
    except Exception:
        host_cache_root = str(Path.home() / "minjiang_host_client_cache")

    # 创建日志目录：{host_cache_root}/{group_name}/log/
    log_dir = Path(host_cache_root) / group_name / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 按日期命名日志文件：dashboard_YYYYMMDD.log
    today = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"dashboard_{today}.log"

    # 如果文件已存在且较大（比如超过10MB），创建新的文件（添加序号）
    if log_file.exists():
        file_size = log_file.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            counter = 1
            while True:
                new_log_file = log_dir / f"dashboard_{today}_{counter}.log"
                if not new_log_file.exists():
                    log_file = new_log_file
                    break
                counter += 1

    return str(log_file)


def start_dashboard(group_name: str, lang: str = None, script_path: str = None, script_source: str = "local",
                    direct_link_port: int = 6887, daemon: bool = False):
    """启动 host_client_dashboard utility"""
    print("group_name", group_name)
    # 检查登录状态
    if get_user_temp_token() is None:
        print("错误: 尚未登录，请先使用 'login' 命令进行登录")
        print("示例: python -m minjiang_client login")
        sys.exit(1)

    # 检查脚本路径是否提供
    if not script_path:
        print("错误: 必须提供脚本路径 (--script-path)")
        print(
            "示例: python -m minjiang_client start-dashboard --group-name ZWDX_test_group --script-path /path/to/script.py")
        sys.exit(1)

    utility_name = "host_client_dashboard"
    utility_config = {}

    if lang:
        utility_config["_lang"] = lang

    gui_addr = get_gui_addr()
    host = gui_addr.get("server_addr", "127.0.0.1")
    port = gui_addr.get("port", 6886)
    studio_url = f"http://{host}:{port}"
    utility_config["_studio_url"] = studio_url

    # 添加脚本相关配置（script_path 已确保不为空）
    utility_config["_base_path"] = f"/group_utility/{utility_name}/{group_name}"
    utility_config["_script_path"] = script_path
    utility_config["_script_source"] = script_source
    utility_config["_direct_link_port"] = direct_link_port
    utility_config["_daemon"] = daemon  # 传递 daemon 标志

    try:
        print(f"正在启动 {utility_name} utility (group_name: {group_name})...")

        # 获取 utility 信息以获取 default_route
        result = utility_manager.start_utility_server(
            group_name=group_name,
            utility_name=utility_name,
            utility_config=utility_config
        )

        print(f"\n✓ Dashboard 启动成功！")
        print(f"  Server ID: {result['server_id']}")
        print(f"  端口: {result['port']}")
        print(f"  本地访问地址: {result['local_url']}")
        print(f"  进程 ID: {result['pid']}")

        # 如果以后台方式启动，启动日志保存线程后退出
        if daemon:
            if requests is None:
                print("警告: requests 库未安装，无法保存日志。请安装: pip install requests")
                print("\nDashboard 已在后台运行")
                return result

            # 获取日志文件路径
            try:
                log_file_path = _get_log_file_path(group_name)
                print(f"  日志文件: {log_file_path}")
            except Exception as e:
                print(f"警告: 无法创建日志文件: {e}")
                print("\nDashboard 已在后台运行（日志未保存）")
                return result

            # 构建日志 API URL
            log_api_url = f"{result['local_url']}/api/host-client/logs"

            # 等待 utility 完全启动
            max_wait_time = 30
            wait_interval = 0.5
            waited_time = 0
            server_ready = False

            while waited_time < max_wait_time:
                try:
                    health_url = f"{result['local_url']}/health"
                    health_response = requests.get(health_url, timeout=2)
                    if health_response.status_code == 200:
                        server_ready = True
                        break
                except:
                    pass
                time.sleep(wait_interval)
                waited_time += wait_interval

            # 日志保存功能已集成到 utility 中，通过线程方式运行
            # 不需要在这里启动独立的进程
            try:
                log_file_path = _get_log_file_path(group_name)
                print(f"\nDashboard 已在后台运行")
                print(f"日志正在保存到: {log_file_path}")
                print(f"使用 'stop-dashboard --group-name {group_name}' 停止 Dashboard")
            except Exception as e:
                print(f"\nDashboard 已在后台运行")
                print(f"警告: 无法获取日志文件路径: {e}")

            return result

        # 前台模式：持续轮询日志并打印
        print(f"\n正在等待脚本启动并获取日志...")
        print(f"按 Ctrl+C 退出日志查看（Dashboard 将继续运行）\n")

        # 持续轮询日志 API
        if requests is None:
            print("警告: requests 库未安装，无法获取日志。请安装: pip install requests")
            return result

        # 构建日志 API URL
        log_api_url = f"{result['local_url']}/api/host-client/logs"
        status_api_url = f"{result['local_url']}/api/host-client/status"

        cursor = 0
        last_running_status = None

        def signal_handler(sig, frame):
            print("\n\n停止日志查看（Dashboard 将继续运行）")
            sys.exit(0)

        # 注册信号处理器，处理 Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)

        # 等待 utility 完全启动，并检查服务器是否就绪
        max_wait_time = 30
        wait_interval = 0.5
        waited_time = 0
        server_ready = False

        while waited_time < max_wait_time:
            try:
                # 尝试访问健康检查端点
                health_url = f"{result['local_url']}/health"
                health_response = requests.get(health_url, timeout=2)
                if health_response.status_code == 200:
                    server_ready = True
                    break
            except:
                pass
            time.sleep(wait_interval)
            waited_time += wait_interval

        if not server_ready:
            print(f"[WARN] Utility 服务器可能未完全启动，但将继续尝试获取日志...")

        # 持续轮询日志
        consecutive_errors = 0
        max_consecutive_errors = 10

        while True:
            try:
                # 获取日志
                response = requests.get(log_api_url, params={"cursor": cursor}, timeout=5)
                if response.status_code == 200:
                    consecutive_errors = 0  # 重置错误计数
                    data = response.json()
                    logs = data.get("logs", [])
                    cursor = data.get("cursor", cursor)
                    running = data.get("running", False)

                    # 打印新日志（去重处理）
                    seen_logs = set()  # 用于去重
                    for log_entry in logs:
                        level = log_entry.get("level", "info")
                        line = log_entry.get("line", "")
                        timestamp = log_entry.get("timestamp", "")
                        seq = log_entry.get("seq", 0)

                        # 使用 seq 和 line 的组合作为唯一标识符去重
                        log_key = (seq, line)
                        if log_key in seen_logs:
                            continue
                        seen_logs.add(log_key)

                        # 检查日志内容是否已经包含时间戳（格式如 [Server main]@[2026-01-09 18:17:21]）
                        # 如果已经包含时间戳，直接使用原内容，不再添加时间戳
                        if '@[' in line and ']' in line.split('@[')[-1]:
                            # 日志内容已经包含时间戳，直接使用
                            if level == "error":
                                print(f"[ERROR] {line}", flush=True)
                            elif level == "warning":
                                print(f"[WARN] {line}", flush=True)
                            else:
                                print(line, flush=True)
                        else:
                            # 日志内容不包含时间戳，添加时间戳（转换为本地时间）
                            if timestamp:
                                try:
                                    # 处理 UTC 时间戳（带 Z）
                                    if timestamp.endswith('Z'):
                                        dt_utc = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                        dt_local = dt_utc.astimezone()
                                        time_str = dt_local.strftime('%Y-%m-%d %H:%M:%S')
                                    elif '+' in timestamp or timestamp.count('-') > 2:
                                        # 带时区信息
                                        dt = datetime.fromisoformat(timestamp)
                                        dt_local = dt.astimezone()
                                        time_str = dt_local.strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        # 假设已经是本地时间
                                        time_str = timestamp
                                except Exception:
                                    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            # 根据日志级别选择输出格式
                            if level == "error":
                                print(f"[{time_str}] [ERROR] {line}", flush=True)
                            elif level == "warning":
                                print(f"[{time_str}] [WARN] {line}", flush=True)
                            else:
                                print(f"[{time_str}] {line}", flush=True)

                    # 检查运行状态变化
                    if last_running_status is None:
                        last_running_status = running
                    elif last_running_status and not running:
                        print("\n[INFO] Host Client 进程已停止", flush=True)
                        # 继续获取剩余日志
                        time.sleep(1)
                        continue

                    last_running_status = running
                else:
                    consecutive_errors += 1
                    if consecutive_errors <= 3:
                        print(f"[WARN] 获取日志失败，HTTP {response.status_code}", flush=True)
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"[ERROR] 连续 {max_consecutive_errors} 次获取日志失败，停止轮询", flush=True)
                        break

                # 等待一段时间后再次轮询
                time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                # 网络错误，继续重试
                consecutive_errors += 1
                if consecutive_errors <= 3:
                    print(f"[WARN] 网络错误: {e}", flush=True)
                if consecutive_errors >= max_consecutive_errors:
                    print(f"[ERROR] 连续 {max_consecutive_errors} 次网络错误，停止轮询", flush=True)
                    break
                time.sleep(1)
                continue
            except KeyboardInterrupt:
                # Ctrl+C 被按下
                signal_handler(None, None)
                break
            except Exception as e:
                print(f"[ERROR] 获取日志时出错: {e}", flush=True)
                time.sleep(1)
                continue

    except KeyboardInterrupt:
        print("\n\n停止日志查看（Dashboard 将继续运行）")
        sys.exit(0)
    except Exception as e:
        print(f"启动 Dashboard 失败: {e}")
        sys.exit(1)


def stop_dashboard(group_name: str):
    """停止 host_client_dashboard utility"""
    utility_name = "host_client_dashboard"

    try:
        # 获取所有运行中的 utility servers
        running_servers = utility_manager.list_utility_servers()

        # 查找匹配的 dashboard 实例
        matching_servers = [
            server for server in running_servers
            if server.get("utility_name") == utility_name
               and server.get("group_name") == group_name
        ]

        if not matching_servers:
            print(f"错误: 未找到运行中的 {utility_name} (group_name: {group_name})")
            print("\n当前运行中的 Dashboard 实例:")
            dashboard_servers = [
                server for server in running_servers
                if server.get("utility_name") == utility_name
            ]
            if dashboard_servers:
                for server in dashboard_servers:
                    print(f"  - group_name: {server.get('group_name', 'N/A')}, "
                          f"Server ID: {server.get('server_id')}, "
                          f"端口: {server.get('port')}")
            else:
                print("  （无）")
            sys.exit(1)

        # 停止所有匹配的实例（理论上应该只有一个）
        stopped_count = 0
        for server in matching_servers:
            server_id = server.get("server_id")
            if server_id:
                success = utility_manager.stop_utility_server(server_id)
                if success:
                    stopped_count += 1
                    print(f"✓ 已停止 Dashboard (group_name: {group_name}, Server ID: {server_id})")
                else:
                    print(f"✗ 停止失败 (Server ID: {server_id})")

        if stopped_count > 0:
            print(f"\n成功停止了 {stopped_count} 个 Dashboard 实例")
        else:
            print("\n未能停止任何 Dashboard 实例")
            sys.exit(1)

    except Exception as e:
        print(f"停止 Dashboard 失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Minjiang M&C Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
        """
        示例:
        
        # 登录
        python -m minjiang_client login
        
        # 使用 token 登录
        python -m minjiang_client login --token YOUR_TOKEN
        
        # 启动 host_client_dashboard（必须提供脚本路径）
        python -m minjiang_client start-dashboard --group-name ZWDX_test_group --script-path D:/qcs520_host.py
        
        # 启动 dashboard 并指定语言
        python -m minjiang_client start-dashboard --group-name ZWDX_test_group --script-path D:/qcs520_host.py --lang cn
        
        # 启动 dashboard 并启动云服务中的脚本
        python -m minjiang_client start-dashboard --group-name ZWDX_test_group --script-path /ZWDX/host_client/qcs520_host.py --script-source manager
        
        # 启动 dashboard 并启动脚本（指定 Direct Link 端口）
        python -m minjiang_client start-dashboard --group-name ZWDX_test_group --script-path D:/qcs520_host.py --direct-link-port 6888
        
        # 后台启动 dashboard（启动后立即退出，日志保存到文件）
        python -m minjiang_client start-dashboard --group-name ZWDX_test_group --script-path D:/qcs520_host.py --daemon
        
        # 停止运行中的 dashboard
        python -m minjiang_client stop-dashboard --group-name ZWDX_test_group
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # login 子命令
    login_parser = subparsers.add_parser(
        'login',
        help='用户登录'
    )
    login_parser.add_argument(
        '--token',
        help='用户 token（可选，如果不提供则会在命令行中提示输入）'
    )

    # start-dashboard 子命令
    dashboard_parser = subparsers.add_parser(
        'start-dashboard',
        help='启动 host_client_dashboard utility'
    )
    dashboard_parser.add_argument(
        '--group-name',
        required=True,
        help='设备组名称（必需）'
    )
    dashboard_parser.add_argument(
        '--lang',
        choices=['cn', 'en'],
        help='语言设置（cn 或 en）'
    )
    dashboard_parser.add_argument(
        '--script-path',
        required=True,
        help='要自动启动的脚本路径（本地文件或云服务中的文件，必需）'
    )
    dashboard_parser.add_argument(
        '--script-source',
        choices=['local', 'manager'],
        default='local',
        help='脚本来源（local: 本地文件, manager: 云服务中的文件，默认 local）'
    )
    dashboard_parser.add_argument(
        '--direct-link-port',
        type=int,
        default=6887,
        help='Direct Link 端口号（默认 6887）'
    )
    dashboard_parser.add_argument(
        '--daemon',
        action='store_true',
        help='后台模式启动（启动后立即退出，日志保存到文件）'
    )

    # stop-dashboard 子命令
    stop_dashboard_parser = subparsers.add_parser(
        'stop-dashboard',
        help='停止运行中的 host_client_dashboard utility'
    )
    stop_dashboard_parser.add_argument(
        '--group-name',
        required=True,
        help='设备组名称（必需）'
    )

    args = parser.parse_args()

    if args.command == 'login':
        # 登录
        cmd_login(token=args.token)
    elif args.command == 'start-dashboard':
        # 启动 dashboard
        start_dashboard(
            group_name=args.group_name,
            lang=args.lang,
            script_path=args.script_path,
            script_source=args.script_source,
            direct_link_port=args.direct_link_port,
            daemon=args.daemon
        )
    elif args.command == 'stop-dashboard':
        # 停止 dashboard
        stop_dashboard(group_name=args.group_name)
    else:
        # 如果没有指定命令，显示帮助信息
        parser.print_help()
