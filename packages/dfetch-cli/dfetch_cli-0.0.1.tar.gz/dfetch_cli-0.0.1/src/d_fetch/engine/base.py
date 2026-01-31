class BaseDownloader:
    async def download(self, url, connections, output_path, force):
        raise NotImplementedError
