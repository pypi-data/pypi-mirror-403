from tgzr.shell.app_sdk.host_app import ShellHostApp, DefaultShellAppInfo
from tgzr.shell.session import Session

from . import run_blender


class BlenderHostApp(ShellHostApp):

    def exe_path(self, session: Session, version: str) -> str:
        if version is not None:
            raise ValueError(f"Unsupported blender {version=}")
        return "/snap/bin/blender"


blender = BlenderHostApp(
    "blender",
    run_module=run_blender,
    app_groups={"3D", "Anim"},
    default_app_info=DefaultShellAppInfo(icon="blender", color="grey-9"),
)
