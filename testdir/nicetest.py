from Recon_Ext_framework import Tool4Recon

class Tool4Recon(Tool4Recon):
    tool_name = 'nicetest'

    #To easily create GUIs without worrying about layout, 
    # use the widget names the same as those in Pyside2, along with their respective methods.
    tool_attribs ={
        'settings_dialog':{
            'Just a text':[
                'QLineEdit()'
            ],
            'Simple checkbox':[
                'QCheckBox()'
            ],
            'Listdown':[
                'QComboBox()',
                'addItem("1")',
                'addItem("10")'
            ]
        },
        # for setting the value for scanning and default in the start of the program
        'configs':{
            'Just a text':'write something',
            'Simple checkbox':True,
            'Listdown': '10'
        }
    }
    def tool_working(url: str, tool_configs:dict) -> str:
        print(f'nice {url}')
        # Tool Implementation.
        return f"<html><body><h1>{tool_configs['Just a text']}</h1>is checked:{tool_configs['Simple checkbox']}<b>{tool_configs['Listdown']}<b></body></html>"