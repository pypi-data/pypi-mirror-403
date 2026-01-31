import threading
from _typeshed import Incomplete
from minjiang_client.com.command import upload_print as upload_print
from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.base.server import Server as Server
from minjiang_host_client.utils.device_manager import DeviceManager as DeviceManager

class MainServer(Server):
    SUPPORTED_COMMAND_TYPES: list[str]
    enable_device_manager: Incomplete
    device_manager: DeviceManager | None
    dl_server: Incomplete
    dl_port: Incomplete
    direct_link_server_thread: threading.Thread | None
    direct_link_server_instance: Incomplete
    def __init__(self, name: str, group_name: str, in_chl: Channel = None, out_chl: Channel = None, enable_device_manager: bool = True, dl_server: str = 'localhost', dl_port: int = 6887) -> None: ...
    def finished_starting(self) -> None: ...
    def cleanup_direct_link(self) -> None: ...
    def run(self) -> None: ...
