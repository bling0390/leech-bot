from module.leech.constants.leech_file_tool import LeechFileSyncTool


class Prompt:
    def __init__(self, sync_tool: LeechFileSyncTool = None, storage_path: str = None, links: list[str] = None):
        self.sync_tool = sync_tool
        self.storage_path = storage_path
        self.links = links

    def update_links(self, links: list[str]):
        self.links = links

    def update_storage_path(self, storage_path: str | None):
        self.storage_path = storage_path

    def update_sync_tool(self, sync_tool: LeechFileSyncTool | None):
        self.sync_tool = sync_tool
