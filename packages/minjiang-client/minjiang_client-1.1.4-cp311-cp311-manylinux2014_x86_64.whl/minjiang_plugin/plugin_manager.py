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
import importlib
import importlib.util
import json
import os
import platform
import shutil
import sys
import zipfile
from pathlib import Path
from typing import List, Optional

from minjiang_client.com.minio import get_minio_client
from minjiang_client.com.oss import add_plugin_resource, get_plugin_version_resource_info
from minjiang_client.com.plugin import (create_plugin, list_plugins, upload_plugin_version,
                                        get_plugin_detail, list_plugin_versions, modify_plugin,
                                        set_plugin_global_visibility, get_plugin_config, get_plugin_version_detail)
from minjiang_client.utils.local import get_cache_dir, get_plugin_dir, get_default_config_dir


def zip_directory(root_dir, to_file):
    root_dir = Path(root_dir).expanduser().resolve()
    output_zip = Path(to_file).expanduser().resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    exclude_dirs = ['__pycache__']

    with zipfile.ZipFile(to_file + ".zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            for excluded_dir in exclude_dirs:
                if excluded_dir in dirs:
                    dirs.remove(excluded_dir)
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(root_dir)
                zipf.write(file_path, arcname)

    with open(to_file + ".zip", 'rb') as f:
        return f.read()


class PluginManager(object):

    @staticmethod
    def list_local_plugins():
        plugin_dir = get_plugin_dir()
        sys.path.append(str(plugin_dir))
        root_path = Path(plugin_dir)
        json_data = dict()
        for f in root_path.iterdir():
            plugin_name = f.name
            current_dir = str(plugin_dir) + "/" + plugin_name
            try:
                if not os.path.isdir(current_dir):
                    continue
                module = importlib.import_module(plugin_name + ".main")
                if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
                if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
                if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
                plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
                plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
                plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
                if '__MJ_PLUGIN_DESC__' in module.__dict__.keys():
                    plugin_desc = module.__dict__['__MJ_PLUGIN_DESC__']
                else:
                    plugin_desc = "No description."
                json_data[plugin_name] = {
                    "full_path": current_dir,
                    "path": current_dir,
                    "plugin_version": plugin_version,
                    "plugin_hook": plugin_hook,
                    "desc": plugin_desc,
                    "uninstall_enable": True,
                    "update_enable": True
                }
            except Exception as e:
                print(f"Cannot import plugin in {current_dir}: {e}")

        if os.path.isfile(get_default_config_dir() + "/plugin_includes.txt"):
            with open(get_default_config_dir() + "/plugin_includes.txt", "r") as file:
                line = file.readline()
                while line:
                    line = line.strip()
                    normalized_path = os.path.normpath(line)
                    parent_dir = os.path.dirname(normalized_path)
                    current_dir = os.path.basename(normalized_path)
                    main_file = os.path.join(normalized_path, 'main.py')
                    if os.path.isfile(main_file):
                        sys.path.append(parent_dir)
                        module = importlib.import_module(f"{current_dir}.main")
                        importlib.reload(module)
                        if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                            raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
                        if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                            raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
                        if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                            raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
                        plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
                        plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
                        plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
                        if '__MJ_PLUGIN_DESC__' in module.__dict__.keys():
                            plugin_desc = module.__dict__['__MJ_PLUGIN_DESC__']
                        else:
                            plugin_desc = "No description."
                        json_data[plugin_name] = {
                            "full_path": f"{parent_dir}/{current_dir}",
                            "path": current_dir,
                            "plugin_version": plugin_version,
                            "plugin_hook": plugin_hook,
                            "desc": plugin_desc,
                            "uninstall_enable": False,
                            "update_enable": False
                        }

                    line = file.readline()
        else:
            with open(get_default_config_dir() + "/plugin_includes.txt", "w") as file:
                file.write("")

        return json_data

    @staticmethod
    def list_remote_plugins(page, per_page):
        data = list_plugins(page, per_page)
        for item in data['list']:
            if item['latest_version_hook'] is not None:
                item['latest_version_hook'] = json.loads(item['latest_version_hook'])
            else:
                item['latest_version_hook'] = []
        return data

    @staticmethod
    def list_plugin_versions(plugin_id: int, page: int = 1, per_page: int = 10, os_type: Optional[str] = None,
                             python_version: Optional[str] = None):
        if os_type is None:
            os_type = PluginManager._get_os_type()
        if python_version is None:
            python_version = PluginManager._get_python_version()
        data, count = list_plugin_versions(plugin_id, page, per_page, os_type=os_type, python_version=python_version)
        for item in data:
            item['hook'] = json.loads(item['hook'])
        return {"list": data, "total": count}

    @staticmethod
    def get_plugin_detail(plugin_id: int):
        return get_plugin_detail(plugin_id)

    @staticmethod
    def download_plugin(plugin_id: int, os_type: Optional[str] = None, python_version: Optional[str] = None):
        if os_type is None:
            os_type = PluginManager._get_os_type()
        if python_version is None:
            python_version = PluginManager._get_python_version()

        # Get plugin detail
        plugin_detail = PluginManager.get_plugin_detail(plugin_id)
        plugin_name = plugin_detail['plugin_name']

        # 获取当前系统类型和Python版本下最新的插件版本
        data = PluginManager.list_plugin_versions(plugin_id, page=1, per_page=1, os_type=os_type,
                                                  python_version=python_version)
        if data['total'] == 0:
            raise RuntimeError(
                "Cannot find plugin with plugin ID {} compatible with current system and Python version".format(
                    plugin_id))
        version = data['list'][0]
        plugin_version_id = version['plugin_version_id']
        plugin_version = version['full_version_code']

        return PluginManager._download(plugin_name, plugin_version_id, plugin_version)

    @staticmethod
    def download_plugin_by_version_id(plugin_version_id: int):
        """
        通过plugin_version_id下载对应的插件
        """

        # 获取版本详情
        version_detail = get_plugin_version_detail(plugin_version_id)
        if not version_detail:
            raise RuntimeError(f"Plugin version {plugin_version_id} not found")

        plugin_id = version_detail['plugin_id']
        plugin_version = version_detail['full_version_code']

        # 获取插件详情
        plugin_detail = PluginManager.get_plugin_detail(plugin_id)
        plugin_name = plugin_detail['plugin_name']
        return PluginManager._download(plugin_name, plugin_version_id, plugin_version)

    @staticmethod
    def _download(plugin_name: str, plugin_version_id: int, plugin_version: str):
        resource_info = get_plugin_version_resource_info(plugin_version_id)
        if not resource_info or not isinstance(resource_info, dict) or 'uri' not in resource_info:
            raise RuntimeError(f"Cannot find resource with plugin_version_id {plugin_version_id}")
        uri = resource_info['uri']

        # 下载文件
        minio = get_minio_client(is_global=True)
        raw_data = minio.download(uri)
        plugin_indicator = plugin_name + "_" + plugin_version.replace(".", "_") + ".zip"
        os.makedirs(get_cache_dir() + "/plugin_download/", exist_ok=True)
        filename = get_cache_dir() + "/plugin_download/" + plugin_indicator
        with open(filename, "wb") as fd:
            fd.write(raw_data)

        return filename

    @staticmethod
    def install_plugin(plugin_file: str, replace: bool = None):
        plugin_dir = get_plugin_dir()
        install_cache_dir = plugin_dir + "/plugin_install_cache"
        try:
            if not os.path.exists(plugin_file):
                raise FileNotFoundError(f"Cannot find the plugin package file {plugin_file}.")

            if os.path.exists(install_cache_dir):
                raise RuntimeError(f"Another plugin is installing now, please wait or "
                                   f"remove the cache dir {install_cache_dir} manually.")

            with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
                if 'main.py' not in [f.filename for f in zip_ref.filelist]:
                    filenames = [f.filename.lower() for f in zip_ref.filelist]
                    if 'main.py' not in filenames:
                        raise ValueError(f"main.py cannot be found in {plugin_file}, "
                                         f"it is not a valid plugin package.")
                print("Unpacking plugin...")
                os.makedirs(install_cache_dir, exist_ok=True)
                zip_ref.extractall(install_cache_dir)
                # Analyzing package
                print("Analysing plugin directory...")
                sys.path.append(plugin_dir)
                module = importlib.import_module(f"plugin_install_cache.main")
                module = importlib.reload(module)
                if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
                if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
                if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
                plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
                plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
                plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
                v1 = plugin_version[0]
                v2 = plugin_version[1]
                v3 = plugin_version[2]
                v_postfix = plugin_version[3] if len(plugin_version) == 4 else ""
                full_version = f"{v1}.{v2}.{v3}{v_postfix}"
                print(" - Plugin name:", plugin_name)
                print(" - Plugin version:", full_version)
                print(" - Plugin hook:", ", ".join(plugin_hook))
                # Check existing
                if os.path.exists(plugin_dir + "/" + plugin_name):
                    if replace is None:
                        yes_or_no = input(f"Plugin {plugin_name} is already installed, "
                                          f"do you want to replace it? [Y/n]")
                        replace = True if yes_or_no.lower() in ["yes", "y"] else False
                    if replace is True:
                        shutil.rmtree(plugin_dir + "/" + plugin_name)

                # Clear Cache
                print("Clearing cache...")
                os.rename(install_cache_dir, plugin_dir + "/" + plugin_name)
                print(f"Plugin {plugin_name} is installed.")

                try:
                    del sys.modules[module.__name__]
                except Exception as e:
                    pass

                return True

        except Exception as e:
            print("Clearing cache...")
            try:
                shutil.rmtree(install_cache_dir)
            except Exception as e:
                pass
            raise RuntimeError(f"Install plugin failed: {e}")

    @staticmethod
    def uninstall_plugin(plugin_name):
        plugin_dir = get_plugin_dir()
        if os.path.exists(plugin_dir + "/" + plugin_name):
            shutil.rmtree(plugin_dir + "/" + plugin_name)
        if f"{plugin_name}.main" in sys.modules:
            try:
                del sys.modules[f"{plugin_name}.main"]
            except Exception as e:
                print(f"Cannot delete module: {plugin_name}.main")

    @staticmethod
    def get_plugin_to_install_dir():
        """获取待安装插件目录"""
        mc_dir = get_default_config_dir()
        install_dir = os.path.join(mc_dir, "plugin_to_install")
        os.makedirs(install_dir, exist_ok=True)
        return install_dir

    @staticmethod
    def get_plugin_to_uninstall_file():
        """获取待卸载插件列表文件路径"""
        mc_dir = get_default_config_dir()
        uninstall_file = os.path.join(mc_dir, "plugin_to_uninstall.txt")
        return uninstall_file

    @staticmethod
    def get_plugin_name_from_file(plugin_file: str):
        """从插件文件中提取插件名称，不实际安装"""
        plugin_dir = get_plugin_dir()
        temp_extract_dir = plugin_dir + "/plugin_temp_extract"
        module = None
        try:
            if not os.path.exists(plugin_file):
                raise FileNotFoundError(f"Cannot find the plugin package file {plugin_file}.")
            
            with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
                if 'main.py' not in [f.filename for f in zip_ref.filelist]:
                    filenames = [f.filename.lower() for f in zip_ref.filelist]
                    if 'main.py' not in filenames:
                        raise ValueError(f"main.py cannot be found in {plugin_file}, "
                                         f"it is not a valid plugin package.")
                # 临时解压以读取插件信息
                if os.path.exists(temp_extract_dir):
                    shutil.rmtree(temp_extract_dir)
                os.makedirs(temp_extract_dir, exist_ok=True)
                zip_ref.extractall(temp_extract_dir)
                
                # 读取插件信息
                main_file = os.path.join(temp_extract_dir, "main.py")
                spec = importlib.util.spec_from_file_location("temp_plugin_main", main_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
                plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
                
                return plugin_name
        finally:
            # 清理模块
            if module is not None:
                try:
                    module_name = module.__name__
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                except Exception:
                    pass
            # 清理临时目录
            if os.path.exists(temp_extract_dir):
                try:
                    shutil.rmtree(temp_extract_dir)
                except Exception:
                    pass

    @staticmethod
    def is_plugin_installed(plugin_name: str):
        """检查插件是否已安装"""
        plugin_dir = get_plugin_dir()
        plugin_path = os.path.join(plugin_dir, plugin_name)
        return os.path.exists(plugin_path)

    @staticmethod
    def queue_plugin_for_installation(plugin_file: str):
        """将插件文件移动到待安装目录，等待下次启动时安装
        如果插件未安装过，则立即安装"""
        if not os.path.exists(plugin_file):
            raise FileNotFoundError(f"Cannot find the plugin package file {plugin_file}.")
        
        # 检查插件是否已安装
        plugin_name = None
        is_installed = False
        try:
            plugin_name = PluginManager.get_plugin_name_from_file(plugin_file)
            is_installed = PluginManager.is_plugin_installed(plugin_name)
        except Exception as e:
            # 如果检查失败，仍然延迟安装
            print(f"Warning: Cannot check plugin status, will delay installation: {e}")
        
        if not is_installed and plugin_name:
            # 如果未安装，立即安装
            try:
                PluginManager.install_plugin(plugin_file, replace=True)
                # 刷新插件注册
                from minjiang_client.plugin.plugin_register import plugin_register
                plugin_register.refresh_plugin_loading()
                from minjiang_client.utility_manager import utility_manager
                utility_manager.refresh_utility_registry()
                
                return {
                    "success": True,
                    "message": f"插件 {plugin_name} 安装成功。"
                }
            except Exception as e:
                # 如果立即安装失败，延迟安装
                print(f"Warning: Immediate installation failed, will delay installation: {e}")
        
        # 如果已安装或检查失败或立即安装失败，延迟安装
        install_dir = PluginManager.get_plugin_to_install_dir()
        # 使用时间戳和原文件名确保唯一性
        import time
        timestamp = int(time.time() * 1000000)
        filename = os.path.basename(plugin_file)
        target_path = os.path.join(install_dir, f"{timestamp}_{filename}")
        
        # 移动文件到待安装目录
        shutil.move(plugin_file, target_path)
        
        raise RuntimeError(f"插件将在下次启动时卸载/更新，请重启客户端以完成卸载/更新。"
                           f"Plugin will be uninstall/re-install after restarting.")

    @staticmethod
    def queue_plugin_for_uninstallation(plugin_name: str):
        """将插件名称添加到待卸载列表，等待下次启动时卸载"""
        uninstall_file = PluginManager.get_plugin_to_uninstall_file()
        
        # 读取现有列表
        plugin_names = set()
        if os.path.exists(uninstall_file):
            try:
                with open(uninstall_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            plugin_names.add(line)
            except Exception as e:
                print(f"Warning: Cannot read uninstall list: {e}")
        
        # 添加新插件名称
        plugin_names.add(plugin_name)
        
        # 写回文件
        try:
            with open(uninstall_file, 'w', encoding='utf-8') as f:
                for name in sorted(plugin_names):
                    f.write(f"{name}\n")
        except Exception as e:
            raise RuntimeError(f"Cannot write to uninstall list file: {e}")

        raise RuntimeError(f"插件已添加到待卸载/待更新列表，将在下次启动时卸载/更新。请退出客户端后重新启动以完成卸载/更新。"
                           f"Plugin is added to uninstall/re-install list, this plugin will be uninstall/re-install while restarting.")


    @staticmethod
    def get_plugin_error_log_file():
        """获取插件错误日志文件路径"""
        mc_dir = get_default_config_dir()
        error_log_file = os.path.join(mc_dir, "plugin_install_errors.txt")
        return error_log_file

    @staticmethod
    def write_error_log(errors):
        """将错误信息写入日志文件"""
        if not errors:
            return
        error_log_file = PluginManager.get_plugin_error_log_file()
        try:
            import datetime
            with open(error_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*60}\n")
                for error in errors:
                    f.write(f"{error}\n")
                f.write(f"{'='*60}\n\n")
        except Exception as e:
            print(f"Warning: Cannot write error log: {e}")

    @staticmethod
    def get_error_log():
        """读取错误日志"""
        error_log_file = PluginManager.get_plugin_error_log_file()
        if os.path.exists(error_log_file):
            try:
                with open(error_log_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading log file: {e}"
        return None

    @staticmethod
    def clear_error_log():
        """清空错误日志"""
        error_log_file = PluginManager.get_plugin_error_log_file()
        if os.path.exists(error_log_file):
            try:
                os.remove(error_log_file)
            except Exception as e:
                print(f"Warning: Cannot clear error log: {e}")

    @staticmethod
    def process_pending_plugin_operations():
        """处理待安装和待卸载的插件操作，在启动时调用"""
        errors = []
        
        # 处理待卸载的插件
        uninstall_file = PluginManager.get_plugin_to_uninstall_file()
        if os.path.exists(uninstall_file):
            try:
                with open(uninstall_file, 'r', encoding='utf-8') as f:
                    plugin_names = [line.strip() for line in f if line.strip()]
                
                for plugin_name in plugin_names:
                    try:
                        PluginManager.uninstall_plugin(plugin_name)
                        print(f"Plugin {plugin_name} uninstalled successfully.")
                    except Exception as e:
                        error_msg = f"Failed to uninstall plugin {plugin_name}: {e}"
                        print(error_msg)
                        errors.append(error_msg)
                
                # 清空卸载列表
                if plugin_names:
                    os.remove(uninstall_file)
            except Exception as e:
                error_msg = f"Error processing uninstall list: {e}"
                print(error_msg)
                errors.append(error_msg)
        
        # 处理待安装的插件
        install_dir = PluginManager.get_plugin_to_install_dir()
        if os.path.exists(install_dir):
            plugin_files = []
            for filename in os.listdir(install_dir):
                if filename.endswith('.zip'):
                    plugin_files.append(os.path.join(install_dir, filename))
            
            for plugin_file in sorted(plugin_files):
                try:
                    PluginManager.install_plugin(plugin_file, replace=True)
                    print(f"Plugin from {os.path.basename(plugin_file)} installed successfully.")
                    # 删除已安装的文件
                    os.remove(plugin_file)
                except Exception as e:
                    error_msg = f"Failed to install plugin from {os.path.basename(plugin_file)}: {e}"
                    print(error_msg)
                    errors.append(error_msg)
        
        # 如果有错误，写入错误日志
        if errors:
            PluginManager.write_error_log(errors)
            return {
                "success": False,
                "errors": errors,
                "message": f"部分插件操作失败，共 {len(errors)} 个错误。错误信息已保存到日志文件: {PluginManager.get_plugin_error_log_file()}"
            }
        else:
            return {
                "success": True,
                "message": "所有待处理的插件操作已完成。"
            }

    @staticmethod
    def package_plugin_release(root_dir: str):
        # Check
        log_text = ""
        if root_dir.endswith("main.py"):
            if not os.path.exists(root_dir):
                raise RuntimeError("File main.py is not found in the root directory.")

            plugin_name = os.path.basename(os.path.dirname(root_dir))
            plugin_dir = os.path.dirname(root_dir)

            # 指定模块的绝对路径
            module_path = Path(plugin_dir + "/main.py").resolve()
            module_name = plugin_name  # 自定义模块名（避免冲突）

            # 使用 importlib 加载模块
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        else:
            if not os.path.exists(root_dir + "/main.py"):
                raise RuntimeError("File main.py is not found in the root directory.")

            plugin_dir = root_dir
            plugin_name = os.path.basename(root_dir)

            # 指定模块的绝对路径
            module_path = Path(root_dir + "/main.py").resolve()
            module_name = plugin_name  # 自定义模块名（避免冲突）

            # 使用 importlib 加载模块
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
            raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
        if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
            raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
        if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
            raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
        plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
        plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
        plugin_hooks = module.__dict__['__MJ_PLUGIN_HOOKS__']

        # Package
        plugin_indicator = plugin_name + "_" + "_".join([str(_i) for _i in plugin_version])
        zip_file = get_cache_dir() + "/plugin_release/" + plugin_indicator
        zip_directory(plugin_dir, to_file=zip_file)
        log_text += "Plugin name: " + plugin_name + "\n"
        log_text += "Plugin version: " + '.'.join(map(str, plugin_version)) + "\n"
        log_text += "Plugin hooks: " + ','.join(plugin_hooks) + "\n"
        log_text += "==================================\n"
        log_text += "Save to file: " + zip_file + ".zip\n"
        return log_text

    @staticmethod
    async def submit_plugin_release(plugin_id: int, plugin_file: str, os_type: Optional[str] = None,
                                    python_version: Optional[str] = None):
        # os_type 和 python_version 为可选参数
        # 如果为 None，则视为通用插件（兼容所有系统/Python版本）
        if os_type is not None and os_type.strip():
            os_type = os_type.strip()
            if os_type not in ["Windows", "Linux", "MacOS"]:
                raise ValueError("os_type must be one of: Windows, Linux, MacOS, or None (for universal plugin)")
        else:
            os_type = None  # None表示通用插件，兼容所有系统

        if python_version is not None and python_version.strip():
            python_version = python_version.strip()
            # 验证格式：应该是 "主版本.次版本" 的格式
            try:
                parts = python_version.split('.')
                if len(parts) != 2 or not all(p.isdigit() for p in parts):
                    raise ValueError(
                        "python_version must be in format like '3.8', '3.9', '3.10', or None (for universal plugin)")
            except:
                raise ValueError(
                    "python_version must be in format like '3.8', '3.9', '3.10', or None (for universal plugin)")
        else:
            python_version = None  # None表示通用插件，兼容所有Python版本
        plugin_dir = get_plugin_dir()
        if not os.path.exists(plugin_file):
            raise FileNotFoundError(f"Cannot find the plugin package file {plugin_file}.")

        upload_cache_dir = plugin_dir + "/plugin_upload_cache"
        if os.path.exists(upload_cache_dir):
            raise RuntimeError(f"Another plugin is uploading now, please wait or "
                               f"remove the cache dir {upload_cache_dir} manually.")

        with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
            if 'main.py' not in [f.filename for f in zip_ref.filelist]:
                filenames = [f.filename.lower() for f in zip_ref.filelist]
                if 'main.py' not in filenames:
                    raise ValueError(f"main.py cannot be found in {plugin_file}, "
                                     f"it is not a valid plugin package.")
            os.makedirs(upload_cache_dir, exist_ok=True)
            zip_ref.extractall(upload_cache_dir)
            # Analyzing package
            sys.path.append(upload_cache_dir)
            module = importlib.import_module("plugin_upload_cache.main")
            importlib.reload(module)
            if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
            if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
            if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
            plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
            plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
            plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
            v1 = plugin_version[0]
            v2 = plugin_version[1]
            v3 = plugin_version[2]
            v_postfix = plugin_version[3] if len(plugin_version) == 4 else ""
            full_version = f"{v1}.{v2}.{v3}{v_postfix}"
            if os.path.exists(upload_cache_dir + "/update.txt"):
                with open(upload_cache_dir + "/update.txt", "r", encoding="utf-8") as f:
                    version_desc = f.read()
            else:
                version_desc = "No description."

        try:
            del module
            shutil.rmtree(upload_cache_dir)
        except Exception as e:
            print("Failed to remove the cache dir:", e)

        # Check plugin
        plugin_detail = PluginManager.get_plugin_detail(plugin_id)
        if plugin_detail['plugin_name'] != plugin_name:
            raise RuntimeError(f"Plugin name of plugin ID {plugin_id} is {plugin_detail['plugin_name']}, "
                               f"however, the submitting plugin is named by {plugin_name}.")
        # Upload
        minio = get_minio_client(is_global=True)
        with open(plugin_file, 'rb') as file:
            zip_data = file.read()
        plugin_indicator = plugin_name + "_" + "_".join([str(_i) for _i in plugin_version])
        uri = minio.upload(str(plugin_indicator), zip_data, "plugin", "zip")
        rid = add_plugin_resource("", "zip", json.dumps(uri), "")["resource_id"]
        print("Plugin uploaded.")
        # Submit
        upload = upload_plugin_version(plugin_id, v1, v2, v3, v_postfix, full_version, version_desc,
                                       json.dumps(plugin_hook), rid, os_type=os_type, python_version=python_version)
        print("Plugin submitted.")
        return upload

    @staticmethod
    def create_plugin(plugin_name: str, description: str, org_ids: List[int], manager_user_ids: List[int],
                      must_be_installed: bool, auto_upgrade: bool):
        return create_plugin(plugin_name, description, org_ids, manager_user_ids, must_be_installed, auto_upgrade)

    @staticmethod
    def modify_plugin(plugin_id: int, description: Optional[str], org_ids: List[int], manager_user_ids: List[int]):
        return modify_plugin(plugin_id, description, org_ids, manager_user_ids)

    @staticmethod
    def set_plugin_global_visibility(plugin_id: int, visible: bool):
        return set_plugin_global_visibility(plugin_id, visible)

    @staticmethod
    def get_plugin_config(plugin_id: int):
        return get_plugin_config(plugin_id)

    @staticmethod
    def _get_os_type() -> Optional[str]:
        """
        获取当前操作系统类型
        返回: 'Windows', 'Linux', 'MacOS', 或 None（表示兼容所有系统）
        """
        system = platform.system()
        if system == "Windows":
            return "Windows"
        elif system == "Linux":
            return "Linux"
        elif system == "Darwin":
            return "MacOS"  # macOS系统返回MacOS
        else:
            # 未知系统，返回None表示兼容所有系统
            return None

    @staticmethod
    def _get_python_version() -> Optional[str]:
        """
        获取当前Python版本（主版本号.次版本号，如 "3.8", "3.9", "3.10"）
        返回: Python版本字符串，或 None（表示兼容所有版本）
        """
        try:
            version_info = sys.version_info
            return f"{version_info.major}.{version_info.minor}"
        except Exception:
            return None
