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
import traceback

import minjiang_client
from minjiang_client.group.cloud_group import CloudGroup
from minjiang_host_client.server.main import MainServer
from minjiang_host_client.workers.compiler import CompilerWorker
from minjiang_host_client.workers.post_process import PostProcessWorker
from minjiang_host_client.workers.puller import PullerWorker
from minjiang_host_client.workers.pusher import PusherWorker
from minjiang_host_client.workers.qhal import QHALWorker
from minjiang_host_client.base.channel import Channel
from minjiang_host_client.utils import HostClientProcessManagerInterface, start_host_client_restart_poll_thread
from multiprocessing import shared_memory
from typing import Callable, Optional, Dict, Any

import sys
import os
import io
import threading
import time
import platform
import subprocess

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

IS_WINDOWS = platform.system() == "Windows"
if sys.version_info >= (3, 7):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)


__VERSION__ = minjiang_client.__VERSION__


class Main(HostClientProcessManagerInterface):

    def __init__(self, group_name: str, manual_compiler: Callable = None, manual_qhal: Callable = None,
                 manual_post_process: Callable = None, direct_link_addr: str = 'localhost',
                 direct_link_port: int = 6887, shared_memory_size_mb: int = 200,
                 enable_device_manager: bool = True, script_path: Optional[str] = None):

        self.group_name = group_name
        self.direct_link_port = direct_link_port
        self.direct_link_addr = direct_link_addr
        self.enable_device_manager = enable_device_manager
        # 保存启动参数，用于重启
        self._manual_compiler = manual_compiler
        self._manual_qhal = manual_qhal
        self._manual_post_process = manual_post_process
        self._shared_memory_size_mb = shared_memory_size_mb
        # 保存启动脚本路径，用于重启
        # 如果未提供，尝试从 sys.argv[0] 获取
        if script_path is None:
            # 尝试从 sys.argv[0] 获取脚本路径
            if len(sys.argv) > 0 and os.path.exists(sys.argv[0]):
                self._script_path = os.path.abspath(sys.argv[0])
            else:
                self._script_path = None
        else:
            self._script_path = os.path.abspath(script_path) if os.path.exists(script_path) else script_path
        self._running = True  # 标记是否正在运行
        self._restart_poll_thread: Optional[threading.Thread] = None  # 重启监控线程
        self._restart_lock = threading.RLock()  # 重启锁，防止并发重启

        # Channel - 简化后的worker to worker直接连接
        mem_size = shared_memory_size_mb * 1024 * 1024
        self.chl_puller_compiler = Channel("chl_pl_cp_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_compiler_qhal = Channel("chl_cp_qh_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_qhal_post_process = Channel("chl_qh_pp_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_post_process_pusher = Channel("chl_pp_ps_" + group_name, shared_memory_size=mem_size, create=True)

        # Server - MainServer现在包含了DirectLinkServer的功能
        self.main_server = MainServer("main", self.group_name, enable_device_manager=enable_device_manager,
                                     dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        # Worker - 直接worker to worker连接
        self.pull_worker = PullerWorker("puller", self.group_name, None, self.chl_puller_compiler,
                                        dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        self.push_worker = PusherWorker("pusher", self.group_name, self.chl_post_process_pusher, None,
                                        dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        if manual_compiler is None:
            self.compiler_worker = CompilerWorker("compiler", self.group_name, self.chl_puller_compiler, self.chl_compiler_qhal,
                                                  dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.compiler_worker = manual_compiler("compiler", self.group_name, self.chl_puller_compiler, self.chl_compiler_qhal,
                                                   dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        if manual_qhal is None:
            self.qhal_worker = QHALWorker("qhal", self.group_name, self.chl_compiler_qhal, self.chl_qhal_post_process,
                                          dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.qhal_worker = manual_qhal("qhal", self.group_name, self.chl_compiler_qhal, self.chl_qhal_post_process,
                                           dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        if manual_post_process is None:
            self.post_process_worker = PostProcessWorker("post_process", self.group_name,
                                                         self.chl_qhal_post_process, self.chl_post_process_pusher,
                                                         dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.post_process_worker = manual_post_process("post_process", self.group_name,
                                                           self.chl_qhal_post_process, self.chl_post_process_pusher,
                                                           dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        # Process
        self.main_server_process = None
        self.pull_worker_process = None
        self.compiler_worker_process = None
        self.qhal_worker_process = None
        self.post_process_worker_process = None
        self.push_worker_process = None

        self.compiler_worker.group = CloudGroup(group_name)
        self.qhal_worker.group = CloudGroup(group_name)
        self.post_process_worker.group = CloudGroup(group_name)

        # 父进程监控
        self.parent_monitor_thread: Optional[threading.Thread] = None
        self.parent_pid: Optional[int] = None
        self._monitoring = False
        
        # 启动时间
        self._started_at = time.time()

    def _get_parent_pid(self) -> Optional[int]:
        """获取父进程ID"""
        try:
            # 优先使用 os.getppid()（跨平台，但Windows上可能不准确）
            parent_pid = os.getppid()
            print("Host Client 父进程 PID (parent_pid):", parent_pid)
            return parent_pid
        except (AttributeError, OSError):
            # 如果 os.getppid() 不可用，尝试使用 psutil
            if PSUTIL_AVAILABLE:
                try:
                    current_process = psutil.Process()
                    parent_process = current_process.parent()
                    if parent_process:
                        print("Host Client 父进程 PID (parent_process.pid):", parent_process.pid)
                        return parent_process.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    pass
            return None

    def _is_process_running(self, pid: int) -> bool:
        """检查进程是否在运行"""
        if pid is None:
            return False

        # 使用 psutil 检查（最可靠）
        try:
            process = psutil.Process(pid)
            # 检查进程状态
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            # 如果没有权限访问，假设进程还在运行
            return True

    def _monitor_parent_process(self):
        """监控父进程的线程函数"""
        check_interval = 2.0  # 每2秒检查一次
        while self._monitoring:
            try:
                if self.parent_pid is None:
                    # 如果无法获取父进程ID，跳过检查
                    time.sleep(check_interval)
                    continue

                # 检查父进程是否还在运行
                is_running = self._is_process_running(self.parent_pid)
                if not is_running:
                    # 父进程已停止，强制终止所有子进程
                    self.terminate_all(timeout=2.0, force=True)
                    # 等待一段时间确保进程已终止，然后退出
                    time.sleep(1)
                    exit(0)

                # 等待检查间隔
                time.sleep(check_interval)

            except Exception as e:
                # 发生异常时，继续监控（避免监控线程崩溃）
                time.sleep(check_interval)

    def _start_parent_monitor(self):
        """启动父进程监控"""
        if self._monitoring:
            return

        # 获取父进程ID
        self.parent_pid = self._get_parent_pid()

        if self.parent_pid is None:
            # 无法获取父进程ID，静默跳过（可能是直接启动的进程）
            return

        # 启动监控线程
        self._monitoring = True
        self.parent_monitor_thread = threading.Thread(target=self._monitor_parent_process, daemon=True)
        self.parent_monitor_thread.start()

    def _stop_parent_monitor(self):
        """停止父进程监控"""
        self._monitoring = False
        if self.parent_monitor_thread and self.parent_monitor_thread.is_alive():
            self.parent_monitor_thread.join(timeout=1.0)

    def run(self):
        try:

            print("Host Client 主进程 PID:", os.getpid())

            # 启动父进程监控
            self._start_parent_monitor()
            
            # 启用重启监控功能
            self.enable_restart_monitoring()

            # 初始启动进程
            self._start_all_processes()
            
            # 主循环：持续运行，如果进程退出则重新启动
            while self._running:
                # Join - 等待所有进程退出
                # 如果进程因为重启而退出，restart() 方法会重新创建和启动它们
                # 这里我们只等待，如果进程退出且 _running 为 True，循环会继续
                self.main_server_process.join()
                self.pull_worker_process.join()
                self.compiler_worker_process.join()
                self.qhal_worker_process.join()
                self.post_process_worker_process.join()
                self.push_worker_process.join()
                
                # 如果进程退出但 _running 仍为 True，说明可能是重启导致的
                # 检查是否有进程仍在运行（可能是 restart() 已经重新启动了它们）
                if self._running:
                    # 等待一下，让 restart() 完成（如果正在重启）
                    time.sleep(0.5)
                    # 如果 restart() 已经重新启动了进程，继续循环
                    if self._is_any_process_alive():
                        continue
                    # 否则，重新启动所有进程
                    print("[Main] 检测到所有进程已退出，重新启动...")
                    self._start_all_processes()
                else:
                    # _running 为 False，正常退出
                    break
        finally:
            # 清理共享内存
            self.chl_puller_compiler.close()
            self.chl_compiler_qhal.close()
            self.chl_qhal_post_process.close()
            self.chl_post_process_pusher.close()

            # 在Unix系统上需要手动取消链接
            if hasattr(shared_memory, 'unlink'):
                try:
                    # 使用正确的Channel名称格式
                    shared_memory.SharedMemory(name="chl_pl_cp_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_cp_qh_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_qh_pp_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_pp_ps_" + self.group_name).unlink()
                except FileNotFoundError:
                    pass
                except Exception as e:
                    # 捕获其他可能的异常，避免影响清理流程
                    print(f"清理共享内存时发生错误: {e}")

            print("All processes stopped and shared memory cleaned up.")
            # 停止父进程监控
            self._stop_parent_monitor()
            
            # 禁用重启监控
            self.disable_restart_monitoring()
            
            # 标记为已停止
            self._running = False

    def stop(self) -> bool:
        """
        优雅停止所有进程（通过设置running标志）
        实现 HostClientProcessManagerInterface 接口
        """
        self.main_server.running.value = False
        self.pull_worker.running.value = False
        self.compiler_worker.running.value = False
        self.qhal_worker.running.value = False
        self.post_process_worker.running.value = False
        self.push_worker.running.value = False
        self._running = False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前运行状态
        实现 HostClientProcessManagerInterface 接口
        """
        return {
            "running": self._running and self._is_any_process_alive(),
            "pid": os.getpid(),
            "script_path": self._script_path,
            "direct_link_port": self.direct_link_port,
            "started_at": self._started_at,
        }
    
    def get_group_name(self) -> str:
        """
        获取设备组名称（用于重启监控）
        实现 HostClientProcessManagerInterface 接口
        """
        return self.group_name
    
    def start(self, script_path: str, direct_link_port: int, group_name: str) -> Dict[str, Any]:
        """
        启动进程
        实现 HostClientProcessManagerInterface 接口
        
        注意：Main 类无法自己重新启动自己，因为需要外部进程来启动。
        这个方法主要用于接口兼容性，实际重启应该使用 restart() 方法。
        """
        raise RuntimeError("Main 类无法自己重新启动，请使用 restart() 方法来重启子进程")
    
    def restart(self) -> bool:
        """
        重启所有子进程（主进程不退出）
        实现 HostClientProcessManagerInterface 接口
        
        注意：此方法会停止所有子进程，然后重新创建和启动它们。
        由于 run() 方法在主线程中等待进程 join，我们需要确保：
        1. 停止进程时，设置 running 标志为 False，让进程自然退出
        2. run() 方法检测到进程退出后，会重新创建和启动进程
        3. 或者，我们在后台线程中执行重启，但需要确保 run() 方法能够检测到新进程
        """
        with self._restart_lock:
            print("[Main] 开始重启所有子进程...")
            
            # 1. 停止所有子进程（通过设置 running 标志）
            print("[Main] 停止所有子进程...")
            self._stop_all_subprocesses()
            
            # 2. 等待所有进程退出（使用非阻塞方式）
            print("[Main] 等待所有子进程退出...")
            self._wait_all_subprocesses_exit(timeout=5.0)
            
            # 3. 重新创建 worker 和 server 对象
            print("[Main] 重新创建 worker 和 server 对象...")
            self._recreate_workers_and_server()
            
            # 4. 重新创建进程
            print("[Main] 重新创建进程...")
            self.main_server_process = self.main_server.make_process()
            self.pull_worker_process = self.pull_worker.make_process()
            self.compiler_worker_process = self.compiler_worker.make_process()
            self.qhal_worker_process = self.qhal_worker.make_process()
            self.post_process_worker_process = self.post_process_worker.make_process()
            self.push_worker_process = self.push_worker.make_process()
            
            # 5. 启动所有进程
            print("[Main] 启动所有子进程...")
            self.main_server_process.start()
            self.pull_worker_process.start()
            self.compiler_worker_process.start()
            self.qhal_worker_process.start()
            self.post_process_worker_process.start()
            self.push_worker_process.start()
            
            # 6. 更新运行状态
            self._running = True
            self._started_at = time.time()
            
            print("[Main] 所有子进程重启完成")
            return True
    
    def _stop_all_subprocesses(self):
        """停止所有子进程"""
        # 设置所有 worker 的 running 标志为 False
        self.main_server.running.value = False
        self.pull_worker.running.value = False
        self.compiler_worker.running.value = False
        self.qhal_worker.running.value = False
        self.post_process_worker.running.value = False
        self.push_worker.running.value = False
        
        # 如果进程仍在运行，发送 terminate 信号
        processes = [
            ("main_server", self.main_server_process),
            ("pull_worker", self.pull_worker_process),
            ("compiler_worker", self.compiler_worker_process),
            ("qhal_worker", self.qhal_worker_process),
            ("post_process_worker", self.post_process_worker_process),
            ("push_worker", self.push_worker_process),
        ]
        
        for name, proc in processes:
            if proc is not None and proc.is_alive():
                try:
                    proc.terminate()
                    print(f"[Main] 已发送 terminate 信号给 {name}")
                except Exception as e:
                    print(f"[Main] 终止 {name} 时出错: {e}")
    
    def _wait_all_subprocesses_exit(self, timeout: float = 5.0):
        """等待所有子进程退出"""
        processes = [
            ("main_server", self.main_server_process),
            ("pull_worker", self.pull_worker_process),
            ("compiler_worker", self.compiler_worker_process),
            ("qhal_worker", self.qhal_worker_process),
            ("post_process_worker", self.post_process_worker_process),
            ("push_worker", self.push_worker_process),
        ]
        
        end_time = time.time() + timeout
        for name, proc in processes:
            if proc is not None:
                remaining_time = end_time - time.time()
                if remaining_time <= 0:
                    break
                try:
                    proc.join(timeout=remaining_time)
                    print(f"[Main] {name} 已退出")
                except Exception as e:
                    print(f"[Main] 等待 {name} 退出时出错: {e}")
        
        # 如果还有进程未退出，强制 kill
        for name, proc in processes:
            if proc is not None and proc.is_alive():
                try:
                    proc.kill()
                    proc.join(timeout=1.0)
                    print(f"[Main] 强制终止 {name}")
                except Exception as e:
                    print(f"[Main] 强制终止 {name} 时出错: {e}")
    
    def _recreate_workers_and_server(self):
        """重新创建 worker 和 server 对象"""
        # 重新创建 Server
        self.main_server = MainServer("main", self.group_name, enable_device_manager=self.enable_device_manager,
                                     dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        
        # 重新创建 Worker
        self.pull_worker = PullerWorker("puller", self.group_name, None, self.chl_puller_compiler,
                                        dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        self.push_worker = PusherWorker("pusher", self.group_name, self.chl_post_process_pusher, None,
                                        dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        
        if self._manual_compiler is None:
            self.compiler_worker = CompilerWorker("compiler", self.group_name, self.chl_puller_compiler, self.chl_compiler_qhal,
                                                  dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.compiler_worker = self._manual_compiler("compiler", self.group_name, self.chl_puller_compiler, self.chl_compiler_qhal,
                                                         dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        
        if self._manual_qhal is None:
            self.qhal_worker = QHALWorker("qhal", self.group_name, self.chl_compiler_qhal, self.chl_qhal_post_process,
                                          dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.qhal_worker = self._manual_qhal("qhal", self.group_name, self.chl_compiler_qhal, self.chl_qhal_post_process,
                                                 dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        
        if self._manual_post_process is None:
            self.post_process_worker = PostProcessWorker("post_process", self.group_name,
                                                         self.chl_qhal_post_process, self.chl_post_process_pusher,
                                                         dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.post_process_worker = self._manual_post_process("post_process", self.group_name,
                                                                 self.chl_qhal_post_process, self.chl_post_process_pusher,
                                                                 dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        
        # 设置 CloudGroup
        self.compiler_worker.group = CloudGroup(self.group_name)
        self.qhal_worker.group = CloudGroup(self.group_name)
        self.post_process_worker.group = CloudGroup(self.group_name)
    
    def enable_restart_monitoring(self) -> None:
        """
        启用重启指令监控功能
        实现 HostClientProcessManagerInterface 接口
        """
        if not hasattr(self, '_restart_poll_thread') or self._restart_poll_thread is None:
            self._restart_poll_thread = start_host_client_restart_poll_thread(self.group_name, self)
    
    def disable_restart_monitoring(self) -> None:
        """
        禁用重启指令监控功能
        实现 HostClientProcessManagerInterface 接口
        """
        if hasattr(self, '_restart_poll_thread'):
            self._restart_poll_thread = None
    
    def _start_all_processes(self):
        """启动所有进程"""
        # Make server's process
        self.main_server_process = self.main_server.make_process()

        # Make worker's process
        self.pull_worker_process = self.pull_worker.make_process()
        self.compiler_worker_process = self.compiler_worker.make_process()
        self.qhal_worker_process = self.qhal_worker.make_process()
        self.post_process_worker_process = self.post_process_worker.make_process()
        self.push_worker_process = self.push_worker.make_process()

        # Start
        self.main_server_process.start()
        self.pull_worker_process.start()
        self.compiler_worker_process.start()
        self.qhal_worker_process.start()
        self.post_process_worker_process.start()
        self.push_worker_process.start()
    
    def _is_any_process_alive(self) -> bool:
        """检查是否有任何进程仍在运行"""
        processes = [
            self.main_server_process,
            self.pull_worker_process,
            self.compiler_worker_process,
            self.qhal_worker_process,
            self.post_process_worker_process,
            self.push_worker_process,
        ]
        return any(proc is not None and proc.is_alive() for proc in processes)

    def terminate_all(self, timeout: float = 5.0, force: bool = False):
        """
        主动终止所有进程
        
        Args:
            timeout: 等待进程退出的超时时间（秒），默认5秒
            force: 如果为True，超时后强制kill进程；如果为False，只发送terminate信号
        """
        # 先调用stop()设置停止标志
        self.stop()
        
        # 收集所有进程对象
        processes = []
        if self.main_server_process is not None:
            processes.append(("main_server", self.main_server_process))
        if self.pull_worker_process is not None:
            processes.append(("pull_worker", self.pull_worker_process))
        if self.compiler_worker_process is not None:
            processes.append(("compiler_worker", self.compiler_worker_process))
        if self.qhal_worker_process is not None:
            processes.append(("qhal_worker", self.qhal_worker_process))
        if self.post_process_worker_process is not None:
            processes.append(("post_process_worker", self.post_process_worker_process))
        if self.push_worker_process is not None:
            processes.append(("push_worker", self.push_worker_process))
        
        # 对所有进程发送terminate信号
        for name, proc in processes:
            if proc.is_alive():
                try:
                    proc.terminate()
                except Exception as e:
                    print(f"Failed to terminate {name}: {e}")
        
        # 等待进程退出
        if timeout > 0:
            end_time = time.time() + timeout
            for name, proc in processes:
                remaining_time = end_time - time.time()
                if remaining_time <= 0:
                    break
                try:
                    proc.join(timeout=remaining_time)
                except Exception as e:
                    print(f"Error waiting for {name} to exit: {e}")
        
        # 如果force=True，强制kill仍在运行的进程
        if force:
            for name, proc in processes:
                if proc.is_alive():
                    try:
                        proc.kill()
                        print(f"Force killed {name} process")
                    except Exception as e:
                        print(f"Failed to kill {name}: {e}")
        
        # 停止父进程监控
        self._stop_parent_monitor()
        
        # 禁用重启监控
        self.disable_restart_monitoring()
        
        # 标记为已停止
        self._running = False
