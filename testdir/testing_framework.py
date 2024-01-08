from Recon_Ext_framework import Tool4Recon


class Tool4Recon(Tool4Recon):
    tool_name = 'testing_framework'

    def tool_working(url: str, tool_configs:dict) -> str:
        print(f'testing url {url}')
        return '<html><body><h1>tester</h1></body></html>'