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

import asyncio
import os.path

from fastapi import FastAPI, File, Form, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from minjiang_client.com.organization import *
from minjiang_client.com.oss import *
from minjiang_client.com.user import get_user_info, get_user_list, reset_token
from minjiang_client.utility_manager import utility_manager
from minjiang_client.com.minio import MINIO_MAP
from minjiang_studio.function.client import *
from minjiang_studio.function.command import *
from minjiang_studio.function.download import *
from minjiang_studio.function.exp import *
from minjiang_studio.function.experiment import *
from minjiang_studio.function.file import *
from minjiang_studio.function.group import *
from minjiang_studio.function.log import *
from minjiang_studio.function.oss import api_get_global, api_get_oss_config
from minjiang_studio.function.plot import *
from minjiang_studio.function.plugin import *
from minjiang_studio.function.utility import *
from minjiang_studio.function.utils import *
from minjiang_studio.utils.resp import Resp
from minjiang_studio.utils.wrapper import exception_wrapper

# 配置 FastAPI 应用
app = FastAPI(
    title="Minjiang Studio API",
    description="岷江测控软件Studio API",
    version="1.0.0"
)

working_path = os.path.dirname(__file__)
cache_abs_path = get_cache_dir()

# ==================== 中间件配置 ====================

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件，记录请求处理时间"""

    async def dispatch(self, request, call_next):
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录慢请求（超过1秒）
        if process_time > 1.0:
            logging.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}s"
            )

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response


app.add_middleware(PerformanceMonitoringMiddleware)


@app.get("/api/get_client_status")
@exception_wrapper
def get_client_status():
    resp_config = api_get_local_config()
    resp = Resp(resp_config)
    return resp()


@app.post("/api/set_client_status")
@exception_wrapper
def set_client_status(local_config: LocalConfig):
    resp_config = api_set_local_config(local_config)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/login_config")
@exception_wrapper
def login_config():
    resp_config = api_login_config()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_groups")
@exception_wrapper
def list_groups(page: int = 1, per_page: int = 10, org_id: int = None, show_hidden: bool = True):
    resp_config = api_list_groups(page, per_page, org_id, show_hidden)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_group_detail")
@exception_wrapper
def get_group_detail(device_group_name: str):
    resp_config = api_get_group_detail(device_group_name)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/create_group")
@exception_wrapper
def create_group(group_desc: GroupDescription):
    resp_config = api_create_group(group_desc)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/set_group_hidden")
@exception_wrapper
def set_group_hidden(group_hidden: GroupHidden):
    resp_config = api_set_group_hidden(group_hidden)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/create_space")
@exception_wrapper
def create_space(space_desc: SpaceDescription):
    resp_config = api_create_space(space_desc)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_spaces")
@exception_wrapper
def list_spaces(device_group_name: str, page: int = 1, per_page: int = 10, show_hidden: bool = False):
    resp_config = api_list_spaces(device_group_name, page, per_page, show_hidden)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/hide_space")
@exception_wrapper
def hide_space(device_group_name: str, space_id: int):
    resp_config = api_hide_space(device_group_name, space_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/show_space")
@exception_wrapper
def show_space(device_group_name: str, space_id: int):
    resp_config = api_show_space(device_group_name, space_id)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/submit_space_parameter")
@exception_wrapper
def submit_space_parameter(space_param_submit: SpaceParameterSubmit):
    resp_config = api_submit_space_parameter(space_param_submit)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_exps")
@exception_wrapper
def list_exps(device_group_name: str, space_id: int = None, page: int = 1, per_page: int = 10):
    resp_config = api_exp_list(device_group_name, space_id, page, per_page)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_new_experiments")
@exception_wrapper
def list_new_experiments(device_group_name: str, space_id: int, since_exp_id: int, exp_folder_id: int = None,
                         limit: int = 50):
    resp_config = api_list_new_experiments(device_group_name, space_id, since_exp_id, exp_folder_id, limit)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/count_experiments_by_folder")
@exception_wrapper
def count_experiments_by_folder(device_group_name: str, space_id: int, exp_folder_id: int = None):
    resp_config = api_count_experiments_by_folder(device_group_name, space_id, exp_folder_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_active_experiments")
@exception_wrapper
def list_active_experiments(device_group_name: str):
    resp_config = api_list_active_experiments(device_group_name)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_recent_finished_exps")
@exception_wrapper
def list_recent_finished_exps(device_group_name: str, minutes: int = 10):
    resp_config = api_list_recent_finished_exps(device_group_name, minutes)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_fitting_img")
@exception_wrapper
def exp_fitting_img(group_name: str, exp_ids: str, create_timestamps: str):
    resp_config = api_exp_fitting_img(group_name, exp_ids, create_timestamps)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/mark_exp")
@exception_wrapper
def mark_sub_process(request: MarkSubProcessRequest):
    resp_config = api_mark_sub_process(request.exp_id, request.is_marked, request.mark_note)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/create_exp_folder")
@exception_wrapper
def create_exp_folder(request: CreateExpFolderRequest):
    resp_config = api_create_exp_folder(request.space_id, request.exp_folder_name,
                                        request.parent_exp_folder_id, request.exp_folder_description)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/rename_exp_folder")
@exception_wrapper
def rename_exp_folder(request: RenameExpFolderRequest):
    resp_config = api_rename_exp_folder(request.exp_folder_id, request.new_exp_folder_name,
                                        request.new_exp_folder_description)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/delete_exp_folder")
@exception_wrapper
def delete_exp_folder(request: DeleteExpFolderRequest):
    resp_config = api_delete_exp_folder(request.exp_folder_id)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/move_exp_folder")
@exception_wrapper
def move_exp_folder(request: MoveExpFolderRequest):
    resp_config = api_move_exp_folder(request.exp_folder_id, request.target_parent_exp_folder_id)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/move_experiments")
@exception_wrapper
def move_experiments(request: MoveExperimentsRequest):
    resp_config = api_move_experiments(request.space_id, request.sub_process_ids, request.target_exp_folder_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/batch_query_experiments")
@exception_wrapper
def batch_query_experiments(device_group_name: str, space_id: int, exp_ids: str):
    resp_config = api_batch_query_experiments(device_group_name, space_id, exp_ids)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_exp_folder_tree")
@exception_wrapper
def get_exp_folder_tree(space_id: int):
    resp_config = api_get_exp_folder_tree(space_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/check_exp_folder_empty")
@exception_wrapper
def check_exp_folder_empty(exp_folder_id: int):
    resp_config = api_check_exp_folder_empty(exp_folder_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_exps_by_folder")
@exception_wrapper
def list_exps_by_folder(device_group_name: str, space_id: int, exp_folder_id: int = None,
                        before_exp_id: int = None, limit: int = 10):
    resp_config = api_exp_list_by_folder(device_group_name, space_id, exp_folder_id, before_exp_id, limit)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_exp_folders_by_parent")
@exception_wrapper
def list_exp_folders_by_parent(device_group_name: str, space_id: int, parent_exp_folder_id: int = None):
    resp_config = api_list_exp_folders_by_parent(device_group_name, space_id, parent_exp_folder_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_latest_exp_id_by_folder")
@exception_wrapper
def get_latest_exp_id_by_folder(device_group_name: str, space_id: int, exp_folder_id: int = None):
    resp_config = api_get_latest_exp_id_by_folder(device_group_name, space_id, exp_folder_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_marked_exps")
@exception_wrapper
def list_marked_exps(organization_id: int = None, device_group_name: str = None, space_id: int = None, page: int = 1,
                     per_page: int = 10):
    resp_config = api_list_marked_exps(organization_id, device_group_name, space_id, page, per_page)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_exp_template_groups")
@exception_wrapper
def get_exp_template_groups():
    resp_config = api_get_exp_template_groups()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_exp_templates")
@exception_wrapper
def get_exp_templates(template_group_name: str):
    resp_config = api_get_exp_templates(template_group_name)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/get_exp_template_setup")
@exception_wrapper
def get_exp_template_setup(get_exp_temp_setup: GetExpTemplateSetupRequest):
    resp_config = api_get_exp_template_setup(
        get_exp_temp_setup.template_group_name, get_exp_temp_setup.template_name, get_exp_temp_setup.group_name,
        get_exp_temp_setup.space_id, get_exp_temp_setup.current_setup
    )
    resp = Resp(resp_config)
    return resp()


@app.post("/api/generate_exp")
@exception_wrapper
def generate_exp(generate_exp: GenerateExp):
    resp_config = api_generate_exp(generate_exp.group_name, generate_exp.space_id,
                                   generate_exp.template_group, generate_exp.template_name, generate_exp.setting,
                                   exp_folder_id=generate_exp.exp_folder_id,
                                   exp_folder_path=generate_exp.exp_folder_path,
                                   priority=generate_exp.priority)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_fitter_groups")
@exception_wrapper
def get_fitter_groups():
    resp_config = api_get_fitter_groups()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_fitters")
@exception_wrapper
def get_fitters(fitter_group_name: str):
    resp_config = api_get_fitters(fitter_group_name)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_fitter_setup")
@exception_wrapper
def get_fitter_setup(fitter_group_name: str, fitter_name: str, group_name: str, space_id: int):
    resp_config = api_get_fitter_setup(fitter_group_name, fitter_name, group_name, space_id)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/fitter_fit")
@exception_wrapper
def fitter_fit(fitter_fit: FitterFit):
    resp_config = api_fitter_fit(fitter_fit.fitter_group, fitter_fit.fitter_name, fitter_fit.group_name,
                                 fitter_fit.space_id, fitter_fit.setting)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/submit_fitting_result")
@exception_wrapper
def submit_fitting_result(submit_fit: SubmitFittingResult):
    resp_config = api_submit_fitting_result(
        submit_fit.group_name, submit_fit.space_id, submit_fit.exp_id, submit_fit.img_file,
        submit_fit.table_file, submit_fit.space_parameters, submit_fit.update_space_parameters
    )
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_cloud_fitting_result")
@exception_wrapper
def get_cloud_fitting_result(device_group_name: str, space_id: int, exp_id: int):
    resp_config = api_get_cloud_fitting_result(device_group_name, space_id, exp_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/open_cloud_plotter")
@exception_wrapper
async def open_cloud_plotter(device_group_name: str, exp_id: int):
    """打开云端绘图器"""
    api_open_cloud_plotter(device_group_name, exp_id)
    resp = Resp("ok")
    return resp()


@app.get("/api/get_exp_detail")
@exception_wrapper
def get_exp_detail(device_group_name: str, exp_id: int):
    resp_config = api_load_exp(device_group_name, exp_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_exp_attachment")
@exception_wrapper
def get_exp_attachment(device_group_name: str, exp_id: int):
    resp_config = api_get_exp_attachment(device_group_name, exp_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/preview_exp_attachment")
@exception_wrapper
def preview_exp_attachment(absolute_path: str, in_zip_path: str = None):
    resp_config = api_preview_exp_attachment(absolute_path, in_zip_path)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_exp_status")
@exception_wrapper
def get_exp_status(device_group_name: str, exp_id: int):
    resp_config = api_get_exp_status(device_group_name, exp_id)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/get_parameter_by_tree")
@exception_wrapper
def get_parameter_by_tree(parameter: GetParameterByTree):
    resp_config = api_get_parameter_by_tree(parameter.device_group_name, parameter.space_id, parameter.parent_tree,
                                            parameter.version)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/get_parameters_batch")
@exception_wrapper
def get_parameters_batch(parameter: GetParametersBatch):
    """批量查询参数值接口，输入是多个完整的参数key，查询最新版本"""
    resp_config = api_get_parameters_batch(parameter.device_group_name, parameter.space_id, parameter.keys)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_history_space_parameter")
@exception_wrapper
def get_history_space_parameter(device_group_name: str, space_id: int, version: str):
    resp_config = api_get_history_space_parameter(device_group_name, space_id, version)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_parameter_history")
@exception_wrapper
def get_parameter_history(device_group_name: str, space_id: int, key: str = None, page: int = 1, per_page: int = 10):
    resp_config = api_get_parameter_history(device_group_name, space_id, key, page, per_page)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/remove_space_parameter")
@exception_wrapper
def remove_space_parameter(get_parameter: GetParameter):
    resp_config = api_remove_space_parameter(get_parameter.device_group_name,
                                             get_parameter.space_id, get_parameter.key)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/create_plugin")
@exception_wrapper
def create_plugin(create_plugin: CreatePlugin):
    resp_config = api_create_plugin(create_plugin)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/modify_plugin")
@exception_wrapper
def modify_plugin(modify_plugin: ModifyPlugin):
    resp_config = api_modify_plugin(modify_plugin)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_plugin_config")
@exception_wrapper
def plugin_config(plugin_id: int):
    resp_config = api_get_plugin_config(plugin_id)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/set_plugin_global_visibility")
@exception_wrapper
def set_plugin_global_visibility(plugin_visible: PluginVisible):
    resp_config = api_set_plugin_global_visibility(plugin_visible)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_plugins")
@exception_wrapper
def list_plugins(page: int = 1, per_page: int = 10):
    resp_config = api_list_plugins(page, per_page)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_local_plugins")
@exception_wrapper
def list_local_plugins():
    resp_config = api_list_local_plugins()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_plugin_versions")
@exception_wrapper
def list_plugin_versions(plugin_id: int, page: int = 1, per_page: int = 10, os_type: Optional[str] = None,
                         python_version: Optional[str] = None):
    resp_config = api_list_plugin_versions(plugin_id, page, per_page, os_type, python_version)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/install_plugin")
@exception_wrapper
def install_plugin(version_id: int):
    resp_config = api_install_plugin(version_id)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/install_plugin_via_file")
async def install_plugin_via_file(plugin_file: UploadFile = File(...)):
    file_path = None
    try:
        # 安全地处理文件名，防止路径遍历攻击
        safe_filename = os.path.basename(plugin_file.filename) if plugin_file.filename else "plugin"
        # 使用更安全的临时文件命名方式
        timestamp = int(time.time() * 1000000)  # 使用微秒级时间戳避免冲突
        file_path = os.path.join(get_cache_dir(), f"upload_{timestamp}_{safe_filename}")

        # 确保目录存在
        cache_dir = get_cache_dir()
        if not cache_dir:
            raise RuntimeError("缓存目录未配置")
        os.makedirs(cache_dir, exist_ok=True)

        # 流式写入文件，避免大文件一次性加载到内存
        max_size = 100 * 1024 * 1024  # 100MB 限制
        total_size = 0
        chunk_size = 8192  # 8KB chunks

        with open(file_path, "wb") as buffer:
            while True:
                chunk = await plugin_file.read(chunk_size)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > max_size:
                    raise ValueError(f"文件大小超过限制 (最大 {max_size / 1024 / 1024}MB)")

                buffer.write(chunk)

        resp_config = api_install_plugin_via_file(file_path)
        resp = Resp(resp_config)
        return resp()
    except Exception as e:
        # 如果出错，需要清理临时文件
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logging.warning(f"Cannot remove temporary file {file_path}: {cleanup_error}")
        resp = Resp({}, msg=f"Upload plugin failed: {e}", status=1)
        return resp()
    # 注意：如果成功，文件会被移动到待安装目录，不需要在这里删除


@app.get("/api/uninstall_plugin")
@exception_wrapper
def uninstall_plugin(plugin_name: str):
    resp_config = api_uninstall_plugin(plugin_name)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/package_plugin_version")
@exception_wrapper
def package_plugin_version(plugin_dir: PluginDir):
    resp_config = api_package_plugin_version(plugin_dir.plugin_dir)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_plugin_error_log")
@exception_wrapper
def get_plugin_error_log():
    """获取插件安装错误日志"""
    resp_config = api_get_plugin_error_log()
    resp = Resp(resp_config)
    return resp()


@app.post("/api/clear_plugin_error_log")
@exception_wrapper
def clear_plugin_error_log():
    """清空插件安装错误日志"""
    resp_config = api_clear_plugin_error_log()
    resp = Resp(resp_config)
    return resp()


@app.post("/api/submit_plugin_version")
async def submit_plugin_version(plugin_id=Form(...), plugin_file=File(...), os_type=Form(None),
                                python_version=Form(None)):
    file_path = None
    try:
        # 验证和转换 plugin_id
        if isinstance(plugin_id, str):
            if plugin_id.isdigit():
                plugin_id = int(plugin_id)
            else:
                raise ValueError("Plugin id must be an integer")
        elif not isinstance(plugin_id, int):
            raise ValueError("Plugin id must be an integer")

        # 验证 os_type（如果提供）
        if os_type is not None and os_type.strip():
            if os_type not in ["Windows", "Linux", "MacOS"]:
                raise ValueError("os_type must be one of: Windows, Linux, MacOS")
            os_type = os_type.strip()
        else:
            os_type = None  # None表示通用插件，兼容所有系统

        # 验证 python_version（如果提供）
        if python_version is not None and python_version.strip():
            python_version = python_version.strip()
            # 简单验证格式：应该是 "主版本.次版本" 的格式
            try:
                parts = python_version.split('.')
                if len(parts) != 2 or not all(p.isdigit() for p in parts):
                    raise ValueError("python_version must be in format like '3.8', '3.9', '3.10'")
            except:
                raise ValueError("python_version must be in format like '3.8', '3.9', '3.10'")
        else:
            python_version = None  # None表示通用插件，兼容所有Python版本

        # 安全地处理文件名
        safe_filename = os.path.basename(plugin_file.filename) if plugin_file.filename else "plugin"
        timestamp = int(time.time() * 1000000)  # 使用微秒级时间戳避免冲突
        file_path = os.path.join(get_cache_dir(), f"upload_{timestamp}_{safe_filename}")

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            content = await plugin_file.read()
            buffer.write(content)

        resp_config = await api_submit_plugin_version(plugin_id, file_path, os_type, python_version)
        resp = Resp(resp_config)
        return resp()
    except ValueError as e:
        resp = Resp({}, msg=f"Invalid input: {e}", status=1)
        return resp()
    except Exception as e:
        resp = Resp({}, msg=f"Upload plugin failed: {e}", status=1)
        return resp()
    finally:
        # 确保临时文件被清理
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logging.warning(f"Cannot remove temporary file {file_path}: {e}")


@app.get("/api/exp_edit_get_entities")
@exception_wrapper
def exp_edit_get_entities(device_group_name: str, space_id: int):
    resp_config = api_exp_edit_get_entities(device_group_name, space_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_edit_get_gates")
@exception_wrapper
def exp_edit_get_gates(device_group_name: str, space_id: int):
    resp_config = api_exp_edit_get_gates(device_group_name, space_id)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_edit_get_script_templates")
@exception_wrapper
def exp_edit_get_script_templates():
    resp_config = api_exp_edit_get_script_templates()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_edit_get_wave_functions")
@exception_wrapper
def exp_edit_get_wave_functions():
    resp_config = api_exp_edit_get_wave_functions()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_edit_get_wave_compiler_setup")
@exception_wrapper
def exp_edit_get_wave_compiler_setup():
    resp_config = api_exp_edit_get_wave_compiler_setup()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_edit_get_default_gates")
@exception_wrapper
def exp_edit_get_default_gates():
    resp_config = api_exp_edit_get_default_gates()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_edit_get_gate_default_waveforms")
@exception_wrapper
def exp_edit_get_gate_default_waveforms(device_group_name: str, space_id: int, entities: str, gate_name: str):
    resp_config = api_exp_edit_get_gate_default_waveforms(device_group_name, space_id, entities, gate_name)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/exp_edit_get_wave_sequence")
@exception_wrapper
def exp_edit_get_wave_sequence(get_sequence: GetSequence):
    resp_config = api_exp_edit_get_wave_sequence(get_sequence.device_group_name, get_sequence.space_id,
                                                 get_sequence.waves, get_sequence.use_carrier)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/exp_edit_get_full_wave_sequence")
@exception_wrapper
def exp_edit_get_full_wave_sequence(submit_exp: SubmitExperiment):
    resp_config = api_exp_edit_get_full_wave_sequence(submit_exp)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_edit_get_exp_options")
@exception_wrapper
def exp_edit_get_exp_options():
    resp_config = api_exp_edit_get_exp_options()
    resp = Resp(resp_config)
    return resp()


@app.post("/api/exp_edit_submit_experiment")
@exception_wrapper
def exp_edit_submit_experiment(submit_exp: SubmitExperiment):
    resp_config = api_exp_edit_submit_experiment(submit_exp)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/terminate_exp")
@exception_wrapper
def terminate_exp(exp_id: int):
    data = api_terminate_exp(exp_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_space_initializer_list")
@exception_wrapper
def get_space_initializer_list():
    data = api_get_space_initializer_list()
    resp = Resp(data)
    return resp()


@app.get("/api/get_space_initializer_setup")
@exception_wrapper
def get_space_initializer_setup(initializer_name: str):
    resp_config = api_get_space_initializer_setup(initializer_name)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/space_initializer_preview")
@exception_wrapper
def space_initializer_preview(initializer_data: SpaceInitializer):
    resp_config = api_space_initializer_preview(initializer_data)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/space_initializer_submit")
@exception_wrapper
def space_initializer_submit(initializer_data: SpaceInitializer):
    resp_config = api_space_initializer_submit(initializer_data)
    resp = Resp(resp_config)
    return resp()


@app.post("/api/exp_query_plot")
@exception_wrapper
def exp_query_plot(plot_query: PlotQuery):
    resp_config = api_exp_query_plot(
        plot_query.device_group_name,
        plot_query.space_id,
        plot_query.exp_id,
        plot_query.fields,
        plot_query.latest_step
    )
    resp = Resp(resp_config)
    return resp()


@app.get("/api/exp_debug_plot")
@exception_wrapper
def exp_debug_plot():
    resp_config = api_exp_plot_debug()
    resp = Resp(resp_config)
    return resp()


@app.get("/api/list_sessions")
@exception_wrapper
def list_sessions(device_group_name: str, page: int = 1, per_page: int = 10):
    data = api_get_cali_session_list(device_group_name, page, per_page)
    resp = Resp(data)
    return resp()


@app.get("/api/search_space_parameters")
@exception_wrapper
def search_space_parameters(device_group_name: str, space_id: int, search_word: str):
    data = api_search_space_parameters(device_group_name, space_id, search_word)
    resp = Resp(data)
    return resp()


@app.get("/api/get_node_log")
@exception_wrapper
def get_node_log(node_id: int, session_id: int, last_record_id: Optional[int] = None):
    data = api_get_node_log(node_id, session_id, last_record_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_session_entities")
@exception_wrapper
def get_session_entities(device_group_name: str, space_id: int):
    data = api_get_session_entities(device_group_name, space_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_entity_log")
@exception_wrapper
def get_entity_result_log(session_id: int, entity: str, last_record_id: Optional[int] = None):
    data = api_get_entity_log(session_id, entity, last_record_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_session_json")
@exception_wrapper
def get_session_json(session_id: int, org_id: int):
    data = api_get_session_json(session_id, org_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_session_nodes")
@exception_wrapper
def get_session_nodes(session_id: int):
    data = api_get_session_nodes(session_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_session_info")
@exception_wrapper
def get_session_info(session_id: int):
    data = api_get_session_info(session_id)
    resp = Resp(data)
    return resp()


@app.get("/api/download_exp_file")
@exception_wrapper
def download_exp_file(group_name: str, exp_id: int):
    data = api_download_exp(group_name, exp_id)
    resp = Resp(data)
    return resp()


@app.get("/api/download_space_parameter_file")
@exception_wrapper
def download_space_parameter_file(group_name: str, space_id: int, version: Optional[int] = None):
    if version is None:
        version = int(time.time())
    data = api_download_space_parameter_file(group_name, space_id, version)
    resp = Resp(data)
    return resp()


@app.get("/api/global_search")
@exception_wrapper
def global_search(keyword: str):
    data = api_global_search(keyword)
    resp = Resp(data)
    return resp()


@app.get("/api/space_abstract")
@exception_wrapper
def space_abstract(device_group_name: str, space_id: int, entity_type: str = None):
    data = api_space_abstract(device_group_name, space_id, entity_type)
    resp = Resp(data)
    return resp()


@app.get("/api/get_space_cache")
@exception_wrapper
def get_space_cache(group_name: str, space_id: int):
    """获取space_cache的完整数据（sqlite数据库中的完整数据）"""
    data = api_get_space_cache(group_name, space_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_parameter_description")
@exception_wrapper
def get_parameter_description(full_key_list: str, language: str = "cn"):
    data = api_get_parameter_description(full_key_list.strip().split(","), language=language)
    resp = Resp(data)
    return resp()


@app.post("/api/generate_and_submit_experiment")
@exception_wrapper
def generate_and_submit_experiment(generate_exp: GenerateExp):
    resp_config = create_and_submit_exp(generate_exp.group_name, generate_exp.space_id,
                                        generate_exp.template_group, generate_exp.template_name, generate_exp.setting,
                                        exp_folder_id=generate_exp.exp_folder_id,
                                        exp_folder_path=generate_exp.exp_folder_path,
                                        priority=generate_exp.priority)
    resp = Resp(resp_config)
    return resp()


@app.get("/api/get_user_list")
@exception_wrapper
def user_list():
    data = get_user_list()
    resp = Resp(data)
    return resp()


@app.get("/api/get_user_info")
@exception_wrapper
def user_info():
    data = get_user_info()
    resp = Resp(data)
    return resp()


@app.post("/api/reset_token")
@exception_wrapper
def reset_user_token():
    """重置当前用户的token"""
    data = reset_token()
    resp = Resp({"token": data})
    return resp()


@app.get("/api/get_org_info")
@exception_wrapper
def org_info(org_id: int):
    data = get_org_info(org_id)
    resp = Resp(data)
    return resp()


@app.post("/api/create_organization")
@exception_wrapper
def create_org(org_data: OrgData):
    data = create_organization(org_data.name, org_data.admin_ids, org_data.user_ids)
    resp = Resp(data)
    return resp()


@app.get("/api/get_org_list")
@exception_wrapper
def org_list():
    data = get_org_list()
    resp = Resp(data)
    return resp()


@app.get("/api/get_admin_org_list")
@exception_wrapper
def admin_org_list():
    data = get_admin_org_list()
    resp = Resp(data)
    return resp()


@app.get("/api/get_all_org_users")
@exception_wrapper
def all_org_users():
    data = get_all_org_users()
    resp = Resp(data)
    return resp()


@app.get("/api/get_org_users")
@exception_wrapper
def org_users(organization_id: int):
    data = get_org_users(organization_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_org_devices")
@exception_wrapper
def org_devices(organization_id: int):
    data = get_org_devices(organization_id)
    resp = Resp(data)
    return resp()


@app.post("/api/add_org_user")
@exception_wrapper
def add_organization_user(org_user_query: AddOrgUserQuery):
    data = add_org_user(org_user_query.org_id, org_user_query.user_name, org_user_query.org_role)
    resp = Resp(data)
    return resp()


@app.post("/api/delete_org_user")
@exception_wrapper
def delete_organization_user(org_user_query: OrgUserQuery):
    data = delete_org_user(org_user_query.org_id, org_user_query.user_id)
    resp = Resp(data)
    return resp()


@app.post("/api/modify_org_user_role")
@exception_wrapper
def modify_user_role(org_user_query: OrgUserQuery):
    data = modify_org_user_role(org_user_query.org_id, org_user_query.user_id, org_user_query.org_role)
    resp = Resp(data)
    return resp()


@app.post("/api/modify_user_device_group_permission")
@exception_wrapper
def modify_group_permission(user_device_permission: UserDevicePermission):
    data = modify_user_device_group_permission(user_device_permission.org_id, user_device_permission.user_id,
                                               user_device_permission.device_group_id,
                                               user_device_permission.permission)
    resp = Resp(data)
    return resp()


@app.post("/api/batch_modify_permission_by_user")
@exception_wrapper
def batch_modify_by_user(batch_user_permission: BatchUserPermission):
    data = batch_modify_permission_by_user(batch_user_permission.org_id, batch_user_permission.user_id,
                                           batch_user_permission.permission)
    resp = Resp(data)
    return resp()


@app.post("/api/batch_modify_permission_by_device")
@exception_wrapper
def batch_modify_by_device(batch_device_permission: BatchDevicePermission):
    data = batch_modify_permission_by_device(batch_device_permission.org_id, batch_device_permission.device_group_id,
                                             batch_device_permission.permission)
    resp = Resp(data)
    return resp()


@app.get("/api/get_device_list_by_user")
@exception_wrapper
def device_list_by_user(organization_id: int, user_id: int):
    data = get_device_list_by_user(organization_id, user_id)
    resp = Resp(data)
    return resp()


@app.get("/api/get_user_list_by_device")
@exception_wrapper
def user_list_by_device(organization_id: int, device_group_id: int):
    data = get_user_list_by_device(organization_id, device_group_id)
    resp = Resp(data)
    return resp()


@app.post("/api/add_user")
@exception_wrapper
def add_user_org(user_data: UserData):
    data = add_user_to_org(user_data.user_name, user_data.org_id, user_data.org_role)
    resp = Resp(data)
    return resp()


@app.get("/api/get_global_oss")
@exception_wrapper
def get_global_oss():
    data = api_get_global()
    resp = Resp(data)
    return resp()


@app.get("/api/get_org_oss")
@exception_wrapper
def get_org_oss(organization_id: int):
    data = api_get_oss_config(organization_id)
    resp = Resp(data)
    return resp()


@app.post("/api/set_oss_auth")
@exception_wrapper
def set_oss(oss_data: OSSData):
    data = set_oss_auth(
        if_global=oss_data.if_global,
        disabled=oss_data.disabled,
        organization_id=oss_data.organization_id,
        auth_text=oss_data.auth_text,
    )
    resp = Resp(data)
    global MINIO_MAP
    if oss_data.if_global:
        MINIO_MAP["global"] = None
    else:
        MINIO_MAP[oss_data.organization_id] = None
    return resp()


@app.post("/api/file/create_directory")
@exception_wrapper
def create_directory_api(create_data: DirectoryCreateRequest):
    data = api_create_directory(
        organization_id=create_data.organization_id,
        parent_dir_id=create_data.parent_dir_id,
        dir_name=create_data.dir_name,
        description=create_data.description
    )
    resp = Resp(data)
    return resp()


@app.get("/api/file/get_directory_content")
@exception_wrapper
def get_directory_content_api(organization_id: int, parent_dir_id: Optional[int] = None):
    data = api_get_directory_content(
        organization_id=organization_id,
        parent_dir_id=parent_dir_id
    )
    resp = Resp(data)
    return resp()


@app.post("/api/file/move_directory")
@exception_wrapper
def move_directory_api(data: DirectoryMoveRequest):
    data = api_move_directory(data.dir_id, data.new_parent_dir_id)
    resp = Resp(data)
    return resp()


@app.post("/api/file/create_file")
@exception_wrapper
def create_file_api(
        organization_id: int = Form(...),
        dir_id: Optional[int] = Form(None),
        file_name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),
        file: UploadFile = File(...)
):
    try:
        data = handle_create_file(
            organization_id=organization_id,
            file=file,
            dir_id=dir_id,
            file_name=file_name,
            description=description,
            tags=tags
        )
        resp = Resp(data)
        return resp()
    except Exception as e:
        resp = Resp({}, msg=f"创建文件失败: {str(e)}", status=1)
        return resp()


@app.post("/api/file/upload_file_version")
@exception_wrapper
def upload_file_version_api(
        file_id: int = Form(...),
        version_name: Optional[str] = Form(None),
        change_log: Optional[str] = Form(None),
        file: UploadFile = File(...)
):
    try:
        data = handle_upload_file_version(
            file_id=file_id,
            file=file,
            version_name=version_name,
            change_log=change_log
        )
        resp = Resp(data)
        return resp()
    except Exception as e:
        resp = Resp({}, msg=f"上传文件版本失败: {str(e)}", status=1)
        return resp()


@app.get("/api/file/get_file_versions")
@exception_wrapper
def get_file_versions_api(file_id: int, page: int = 1, per_page: int = 10):
    data = api_get_file_versions(
        file_id=file_id,
        page=page,
        per_page=per_page
    )
    resp = Resp(data)
    return resp()


@app.get("/api/file/get_file_version_info")
@exception_wrapper
def get_file_version_info_api(version_id: int, file_id: int):
    """
    获取文件版本详情

    Args:
        version_id: 版本ID
        file_id: 文件ID（必需，server端会校验两者是否匹配）
    """
    data = api_get_file_version_info(version_id=version_id, file_id=file_id)
    resp = Resp(data)
    return resp()


@app.get("/api/file/fetch_file")
@exception_wrapper
def fetch_file_api(
        file_id: int,
        version_id: Optional[int] = None,
        disposition: str = 'attachment'
):
    """
    统一的文件获取接口，支持下载和预览

    Args:
        file_id: 文件ID（必需）
        version_id: 版本ID（可选，如果不提供则获取最新版本）
        disposition: 'inline'（预览）或 'attachment'（下载），默认 'attachment'
    """
    try:
        return handle_fetch_file(
            file_id=file_id,
            version_id=version_id,
            disposition=disposition
        )
    except Exception as e:
        action = "预览" if disposition == 'inline' else "下载"
        resp = Resp({}, msg=f"{action}文件失败: {str(e)}", status=1)
        return resp()


@app.post("/api/file/copy_file")
@exception_wrapper
def copy_file_api(copy_data: FileCopyRequest):
    data = api_copy_file(copy_data.file_id, copy_data.target_dir_id, copy_data.new_name)
    resp = Resp(data)
    return resp()


@app.post("/api/file/move_file")
@exception_wrapper
def move_file_api(move_data: FileMoveRequest):
    data = api_move_file(move_data.file_id, move_data.target_dir_id, move_data.new_name)
    resp = Resp(data)
    return resp()


@app.post("/api/file/delete_file")
@exception_wrapper
def delete_file_api(delete_data: FileDeleteRequest):
    data = api_delete_file(delete_data.file_id)
    resp = Resp(data)
    return resp()


@app.post("/api/file/delete_directory")
@exception_wrapper
def delete_directory_api(delete_data: DirectoryDeleteRequest):
    data = api_delete_directory(delete_data.dir_id)
    resp = Resp(data)
    return resp()


@app.post("/api/file/download_to_local")
@exception_wrapper
def download_file_to_local_api(download_data: FileDownloadRequest):
    """
    从脚本管理器下载文件到指定本地路径
    
    Args:
        download_data: 包含 script_manager_path（脚本管理器中的文件路径）、local_path（本地目录路径）和 file_name（可选的文件名）
    """
    try:
        data = handle_download_file_to_local(
            script_manager_path=download_data.script_manager_path,
            local_path=download_data.local_path,
            file_name=download_data.file_name
        )
        resp = Resp(data)
        return resp()
    except Exception as e:
        resp = Resp({}, msg=f"下载文件失败: {str(e)}", status=1)
        return resp()


# ==================== Command System API ====================

@app.post("/api/submit_command")
@exception_wrapper
def submit_command(request: SubmitCommandRequest):
    """提交指令"""
    data = api_submit_command(request)
    resp = Resp(data)
    return resp()


@app.post("/api/get_command_status")
@exception_wrapper
def get_command_status(request: CommandStatusRequest):
    """获取指令状态"""
    data = api_get_command_status(request)
    resp = Resp(data)
    return resp()


@app.post("/api/get_command_print")
@exception_wrapper
def get_command_print(request: CommandPrintRequest):
    """获取Print数据"""
    data = api_get_command_print(request)
    resp = Resp(data)
    return resp()


@app.post("/api/list_commands")
@exception_wrapper
def list_commands(request: CommandListRequest):
    """获取指令列表"""
    data = api_list_commands(request)
    resp = Resp(data)
    return resp()


@app.post("/api/cancel_command")
@exception_wrapper
def cancel_command(request: CancelCommandRequest):
    """取消指令"""
    data = api_cancel_command(request)
    resp = Resp(data)
    return resp()


# ==================== Utility Server API ====================

@app.post("/api/utility/start")
@exception_wrapper
def start_utility_api(request: StartUtilityRequest):
    """启动Utility Server"""
    data = api_start_utility(
        group_name=request.group_name,
        utility_name=request.utility_name,
        config=request.config
    )
    resp = Resp(data)
    return resp()


@app.post("/api/utility/stop")
@exception_wrapper
def stop_utility_api(request: StopUtilityRequest):
    """停止Utility Server"""
    data = api_stop_utility(request.server_id)
    resp = Resp(data)
    return resp()


@app.get("/api/utility/available")
@exception_wrapper
def get_available_utilities_api():
    """获取不需要group_name的插件列表，包含运行状态和地址"""
    data = api_get_available_utilities()
    resp = Resp(data)
    return resp()


@app.get("/api/utility/group_utilities")
@exception_wrapper
def get_group_utilities_api(group_name: str):
    """获取需要group_name的插件列表，包含运行状态和地址"""
    data = api_get_group_utilities(group_name)
    resp = Resp(data)
    return resp()


@app.get("/api/utility/running_utilities")
@exception_wrapper
def get_all_running_utilities_api():
    """获取所有正在运行的Utility Server，按分组返回"""
    data = api_get_all_running_utilities()
    resp = Resp(data)
    return resp()


@app.post("/api/utility/refresh_plugins")
@exception_wrapper
def refresh_utility_plugins_api():
    """刷新Utility Server插件"""
    data = api_refresh_utility_plugins()
    resp = Resp(data)
    return resp()


@app.get("/api/get_user_agreement")
@exception_wrapper
def get_user_agreement():
    """获取用户协议内容"""
    resp_config = api_get_user_agreement()
    resp = Resp(resp_config)
    return resp()


@app.get("/cache/{full_path:path}")
async def catch_cache(full_path: str):
    """处理缓存文件请求，支持动态缓存目录更新"""
    global cache_abs_path

    # 检查缓存目录是否已更改（避免每次请求都调用get_cache_dir）
    current_cache_dir = get_cache_dir()
    if not current_cache_dir:
        return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

    if current_cache_dir != cache_abs_path:
        cache_abs_path = current_cache_dir
        # 注意：FastAPI不支持动态卸载mount，这里只是更新路径
        # 实际挂载在应用启动时完成

    # 安全检查：防止路径遍历攻击
    safe_path = os.path.normpath(full_path).lstrip(os.sep)
    if ".." in safe_path or safe_path.startswith("/"):
        return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

    cache_file = os.path.join(cache_abs_path, safe_path)

    # 确保文件在缓存目录内（防止路径遍历）
    try:
        cache_file = os.path.abspath(cache_file)
        if not cache_file.startswith(os.path.abspath(cache_abs_path)):
            return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
    except (OSError, ValueError):
        return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

    if os.path.isfile(cache_file):
        return FileResponse(cache_file)

    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


# ==================== Utility Server 路由转发 ====================

# 全局HTTP客户端连接池，复用连接以提高性能
_http_client: Optional[httpx.AsyncClient] = None


def _get_http_client() -> httpx.AsyncClient:
    """获取全局HTTP客户端（连接池）"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=False  # 本地转发不需要HTTP/2
        )
    return _http_client


def _find_utility_server_port(utility_name: str, group_name: Optional[str] = None) -> Optional[int]:
    """
    查找Utility Server的端口号（直接查询utility_manager）
    
    Args:
        utility_name: Utility名称
        group_name: 设备组名称（可选）
    
    Returns:
        端口号，如果未找到则返回None
    """
    try:
        server_info = utility_manager._find_running_utility(utility_name, group_name)
        if server_info and "port" in server_info:
            return server_info["port"]
    except Exception as e:
        logging.warning(f"查找Utility Server失败: {e}")

    return None


async def _wait_for_server_ready(port: int, max_wait_time: float = 30.0, check_interval: float = 0.5) -> bool:
    """
    等待服务器就绪（通过尝试连接来判断）
    
    Args:
        port: 端口号
        max_wait_time: 最大等待时间（秒）
        check_interval: 检查间隔（秒）
    
    Returns:
        如果服务器就绪返回True，否则返回False
    """
    client = _get_http_client()
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        try:
            # 尝试连接服务器（使用HEAD请求，避免下载内容）
            response = await client.request(
                method="HEAD",
                url=f"http://localhost:{port}/",
                timeout=2.0
            )
            # 任何HTTP响应都表示服务器已就绪
            return True
        except (httpx.RequestError, httpx.TimeoutException):
            # 连接失败，继续等待
            await asyncio.sleep(check_interval)
        except Exception:
            # 其他异常，继续等待
            await asyncio.sleep(check_interval)

    return False


async def _ensure_utility_running(utility_name: str, group_name: Optional[str] = None) -> Optional[int]:
    """
    确保Utility Server正在运行，如果未运行则启动它并等待就绪
    
    Args:
        utility_name: Utility名称
        group_name: 设备组名称（可选）
    
    Returns:
        端口号，如果启动失败则返回None
    """
    # 先检查是否已经在运行
    port = _find_utility_server_port(utility_name, group_name)
    if port is not None:
        return port

    # 如果未运行，尝试启动
    try:
        # 获取Utility信息以判断是否需要group_name
        utility_info = utility_manager._get_utility_info(utility_name)
        if not utility_info:
            logging.warning(f"Utility '{utility_name}' is not registered, cannot auto-start")
            return None

        require_group_name = utility_info.get("require_group_name", False)

        # 如果需要group_name但未提供，无法启动
        if require_group_name and not group_name:
            logging.warning(f"Utility '{utility_name}' requires group_name, but group_name was not provided")
            return None

        # 启动Utility Server（使用默认配置）
        # 使用 asyncio.to_thread 在后台线程中运行，避免阻塞事件循环
        result = await asyncio.to_thread(
            api_start_utility,
            group_name=group_name,
            utility_name=utility_name,
            config={}
        )

        if result and "port" in result:
            port = result["port"]
            # 等待服务器就绪
            if await _wait_for_server_ready(port):
                return port
            else:
                logging.warning(f"Utility '{utility_name}' started but did not become ready within timeout")
                return None
        else:
            logging.warning(f"Failed to start utility '{utility_name}': no port returned")
            return None
    except Exception as e:
        logging.error(f"Failed to auto-start utility '{utility_name}': {e}")
        return None


@app.api_route("/group_utility/{utility_name}/{group_name}/{path:path}",
               methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_utility_with_group(request: Request, utility_name: str, group_name: str, path: str):
    """
    转发需要group_name的Utility Server请求
    路由格式: /group_utility/{utility_name}/{group_name}/...
    """
    # 查找对应的Utility Server端口（使用缓存）
    port = _find_utility_server_port(utility_name, group_name)
    if port is None:
        # 如果未找到，尝试自动启动
        port = await _ensure_utility_running(utility_name, group_name)
        if port is None:
            raise HTTPException(status_code=404,
                                detail=f"Utility Server '{utility_name}' with group '{group_name}' not found or not running")

    # 构建目标URL
    target_url = f"http://localhost:{port}/{path}"

    # 构建查询参数
    if request.url.query:
        target_url += f"?{request.url.query}"

    try:
        # 使用全局连接池客户端
        client = _get_http_client()

        # 获取请求体
        body = await request.body()

        # 构建请求头（排除一些不需要的头部）
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)

        # 发送请求（复用连接）
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body if body else None,
        )

        # 构建响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Utility Server returned error: {str(e)}")
    except httpx.RequestError as e:
        # 连接错误，重试一次（可能服务器已重启）
        port = _find_utility_server_port(utility_name, group_name)
        if port is None:
            raise HTTPException(status_code=404,
                                detail=f"Utility Server '{utility_name}' with group '{group_name}' not found or not running")
        raise HTTPException(status_code=502, detail=f"Failed to proxy request to Utility Server: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.api_route("/utility/{utility_name}/{path:path}",
               methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_utility_without_group(request: Request, utility_name: str, path: str):
    """
    转发不需要group_name的Utility Server请求
    路由格式: /utility/{utility_name}/...
    """
    # 查找对应的Utility Server端口（不需要group_name，使用缓存）
    port = _find_utility_server_port(utility_name, None)

    if port is None:
        # 如果找不到不需要group_name的服务器，尝试将path的第一部分作为group_name
        path_parts = path.split("/", 1)
        if len(path_parts) > 1 and path_parts[0]:
            # 尝试将第一部分作为group_name
            potential_group_name = path_parts[0]
            remaining_path = path_parts[1] if len(path_parts) > 1 else ""
            port = _find_utility_server_port(utility_name, potential_group_name)
            if port is None:
                # 如果未找到，尝试自动启动
                port = await _ensure_utility_running(utility_name, potential_group_name)
            if port is not None:
                # 找到了需要group_name的服务器，使用剩余路径
                target_url = f"http://localhost:{port}/{remaining_path}"
                if request.url.query:
                    target_url += f"?{request.url.query}"

                try:
                    # 使用全局连接池客户端
                    client = _get_http_client()
                    body = await request.body()
                    headers = dict(request.headers)
                    headers.pop("host", None)
                    headers.pop("content-length", None)

                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        content=body if body else None,
                    )

                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.headers.get("content-type")
                    )
                except httpx.HTTPStatusError as e:
                    raise HTTPException(status_code=e.response.status_code,
                                        detail=f"Utility Server returned error: {str(e)}")
                except httpx.RequestError as e:
                    raise HTTPException(status_code=502, detail=f"Failed to proxy request to Utility Server: {str(e)}")

        # 如果还是找不到，尝试自动启动（不需要group_name）
        port = await _ensure_utility_running(utility_name, None)
        if port is None:
            raise HTTPException(status_code=404, detail=f"Utility Server '{utility_name}' not found or not running")

    # 构建目标URL
    target_url = f"http://localhost:{port}/{path}"

    # 构建查询参数
    if request.url.query:
        target_url += f"?{request.url.query}"

    try:
        # 使用全局连接池客户端
        client = _get_http_client()

        # 获取请求体
        body = await request.body()

        # 构建请求头（排除一些不需要的头部）
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)

        # 发送请求（复用连接）
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body if body else None,
        )

        # 构建响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Utility Server returned error: {str(e)}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to proxy request to Utility Server: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """处理所有静态文件请求，返回前端应用"""
    # 安全检查：防止路径遍历攻击
    safe_path = os.path.normpath(full_path).lstrip(os.sep)
    if ".." in safe_path:
        return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    static_file = os.path.join(static_dir, safe_path)

    # 确保文件在静态目录内（防止路径遍历）
    try:
        static_file = os.path.abspath(static_file)
        if not static_file.startswith(os.path.abspath(static_dir)):
            return FileResponse(os.path.join(static_dir, "index.html"))
    except (OSError, ValueError):
        return FileResponse(os.path.join(static_dir, "index.html"))

    if os.path.isfile(static_file):
        return FileResponse(static_file)

    return FileResponse(os.path.join(static_dir, "index.html"))


# 挂载静态文件目录
static_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if os.path.isdir(static_abs_path):
    app.mount("/static", StaticFiles(directory=static_abs_path, html=False), name="static")

# 挂载缓存目录（如果存在）
if cache_abs_path and os.path.isdir(cache_abs_path):
    try:
        app.mount("/cache", StaticFiles(directory=cache_abs_path, check_dir=True, html=False), name="cache")
    except Exception as e:
        logging.warning(f"Failed to mount cache directory {cache_abs_path}: {e}")


# ==================== Client端生命周期管理 ====================

@app.on_event("shutdown")
async def shutdown_event():
    """Client端关闭时，清理所有Utility Server和HTTP客户端"""
    global _http_client
    from minjiang_client.utility_manager import utility_manager
    utility_manager.cleanup_all_servers()

    # 关闭HTTP客户端连接池
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
