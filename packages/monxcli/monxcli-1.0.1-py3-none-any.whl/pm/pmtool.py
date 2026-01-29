from monxcli.mcp_bridge import monx_tool


class Pmtool():
    def __init__(self):
        '''power management tool'''
        pass
    @monx_tool(desc="this will list all")
    @staticmethod
    def list1(test: str):
        '''this will list all '''
        print(f"list{test}")
        return f"list{test}"
        
    @monx_tool(desc="this will get all")
    @staticmethod
    def get():
        ''' this will get all '''
        print("get")
