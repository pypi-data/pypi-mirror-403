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

"""
Host Client 工具函数
"""

import threading
import time
from typing import Callable, Dict, Any, Optional
from minjiang_client.com.command import poll_command, update_command_status

class HostClientProcessManagerInterface:
    """
    Host Client 进程管理器接口
    用于重启功能，需要实现以下方法：
    - get_status() -> Dict[str, Any]: 获取当前运行状态
    - stop() -> bool: 停止进程
    - start(script_path: str, direct_link_port: int, group_name: str) -> Dict[str, Any]: 启动进程
    - get_group_name() -> str: 获取设备组名称（用于重启监控）
    """
    def get_status(self) -> Dict[str, Any]:
        """获取当前运行状态"""
        raise NotImplementedError

    def stop(self) -> bool:
        """停止进程"""
        raise NotImplementedError

    def start(self, script_path: str, direct_link_port: int, group_name: str) -> Dict[str, Any]:
        """启动进程"""
        raise NotImplementedError

    def get_group_name(self) -> str:
        """获取设备组名称（用于重启监控）"""
        raise NotImplementedError

    def restart(self) -> bool:
        """
        重启所有子进程（主进程不退出）
        如果实现类不支持此方法，可以抛出 NotImplementedError
        """
        raise NotImplementedError

    def enable_restart_monitoring(self) -> None:
        """
        启用重启指令监控功能
        实现类可以重写此方法来自定义监控行为
        """
        group_name = self.get_group_name()
        if not hasattr(self, '_restart_poll_thread') or self._restart_poll_thread is None:
            self._restart_poll_thread = start_host_client_restart_poll_thread(group_name, self)

    def disable_restart_monitoring(self) -> None:
        """
        禁用重启指令监控功能
        实现类可以重写此方法来自定义禁用行为
        """
        # 注意：由于轮询线程是 daemon 线程，当进程退出时会自动停止
        # 这里主要是清除引用，如果需要主动停止，可以在实现类中重写此方法
        if hasattr(self, '_restart_poll_thread'):
            self._restart_poll_thread = None


def handle_host_client_restart_command(
    group_name: str,
    process_manager: HostClientProcessManagerInterface
) -> bool:
    """
    处理 host_client_restart 指令

    Args:
        group_name: 设备组名称
        process_manager: 进程管理器实例，需要实现 HostClientProcessManagerInterface 接口

    Returns:
        bool: 是否成功处理指令（如果轮询到指令并处理成功返回 True，否则返回 False）
    """
    try:
        # 轮询 host_client_restart 指令
        command = poll_command(group_name, ['host_client_restart'])
        if not command:
            return False

        command_id = command.get('command_id')
        payload = command.get('payload', {})

        try:
            # 获取当前运行状态
            status = process_manager.get_status()
            if not status.get('running'):
                # 如果 host client 未运行，无法重启
                update_command_status(
                    command_id,
                    'failed',
                    error="Host Client 未运行，无法重启"
                )
                return True  # 已处理指令，只是失败了

            # 保存当前配置以便重启后使用
            script_path = status.get('script_path')
            direct_link_port = status.get('direct_link_port', 6887)

            if not script_path:
                update_command_status(
                    command_id,
                    'failed',
                    error="无法获取当前脚本路径"
                )
                return True  # 已处理指令，只是失败了

            # 尝试使用 restart() 方法重启（仅重启子进程，主进程不退出）
            try:
                if hasattr(process_manager, 'restart'):
                    # 使用 restart() 方法重启所有子进程
                    success = process_manager.restart()
                    if success:
                        update_command_status(
                            command_id,
                            'completed',
                            result={'message': 'Host Client 子进程重启成功'}
                        )
                    else:
                        update_command_status(
                            command_id,
                            'failed',
                            error="重启失败：restart() 方法返回 False"
                        )
                    return True
            except NotImplementedError:
                # 如果 restart() 方法未实现，回退到旧的逻辑
                pass
            except Exception as e:
                # restart() 方法执行出错
                error_msg = str(e)
                update_command_status(
                    command_id,
                    'failed',
                    error=f"重启失败: {error_msg}"
                )
                return True
            
            # 回退逻辑：如果 restart() 方法不可用，使用 stop() + start()
            # 停止当前进程
            process_manager.stop()
            
            # 检查 process_manager 是否能够自己重新启动
            # 如果 start() 方法会抛出 RuntimeError（如 Main 类），则只停止进程
            # 外部进程管理器会检测到进程退出后重新启动
            try:
                # 等待进程完全停止
                time.sleep(2)
                
                # 尝试重新启动
                process_manager.start(script_path, direct_link_port, group_name)
                
                update_command_status(
                    command_id,
                    'completed',
                    result={'message': 'Host Client 重启成功'}
                )
            except RuntimeError as e:
                # Main 类无法自己重新启动，只停止进程
                # 外部进程管理器会检测到进程退出后重新启动
                error_msg = str(e)
                if "无法自己重新启动" in error_msg or "cannot restart" in error_msg.lower() or "请使用 restart()" in error_msg:
                    # 这是预期的行为，Main 类会停止并退出，由外部进程管理器重新启动
                    update_command_status(
                        command_id,
                        'completed',
                        result={'message': 'Host Client 已停止，将由外部进程管理器重新启动'}
                    )
                else:
                    # 其他 RuntimeError，视为失败
                    update_command_status(
                        command_id,
                        'failed',
                        error=f"重启失败: {error_msg}"
                    )
            return True  # 成功处理指令
        except Exception as e:
            error_msg = str(e)
            update_command_status(
                command_id,
                'failed',
                error=f"重启失败: {error_msg}"
            )
            return True  # 已处理指令，只是失败了
    except Exception as e:
        # 静默处理错误，避免影响主循环
        print(f"[Host Client Restart Handler] Error: {e}")
        return False  # 处理失败，但可以继续尝试


def start_host_client_restart_poll_thread(
    group_name: str,
    process_manager: HostClientProcessManagerInterface
) -> threading.Thread:
    """
    启动轮询 host_client_restart 指令的后台线程

    Args:
        group_name: 设备组名称
        process_manager: 进程管理器实例，需要实现 HostClientProcessManagerInterface 接口

    Returns:
        threading.Thread: 启动的线程对象
    """
    def poll_loop():
        while True:
            try:
                handle_host_client_restart_command(group_name, process_manager)
                time.sleep(1.0)  # 轮询间隔
            except Exception as e:
                # 静默处理错误，避免影响主循环
                print(f"[Host Client Restart Poll Thread] Error: {e}")
                time.sleep(5.0)  # 出错后等待更长时间

    thread = threading.Thread(target=poll_loop, daemon=True)
    thread.start()
    return thread