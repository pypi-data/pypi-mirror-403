from nmk_base.version import VersionResolver

from nmk_vscode import __version__


class NmkVSCodeVersionResolver(VersionResolver):
    """
    Version resolver for **${nmkVSCodePluginVersion}**
    """

    def get_version(self) -> str:
        """
        Module version accessor

        :return: current module version
        """
        return __version__
