# Use the below class in order to create extension for recon browser
from PySide2.QtWidgets import QDialog

class Tool4Recon:
    """
To create a customized class based on Tool4Recon, follow these steps:
1. Inherit from the Tool4Recon class by creating a new class with the same name.
2(a). If you wish to design a custom options selection dialog box, provide a unique string name
   as the value for the 'setting_dialog' key in the 'tools_attribs' dictionary.
2(b). Within the customized class, create a nested class named 'dialogBox' that inherits from 'QDialog'.
   This nested class represents the custom dialog box for options selection.
    """
    tool_name = ''
    tool_attribs = {
        # for creating setting dialog GUI easily, Below is an example. 
        # Just overwrite with new value in your class
        # if wanna implement detailed dialog box then
        # 'settings_dialog' : '<toolName>' and implement the dialogbox class within this class
        'settings_dialog':{
            'Recursive Scraping':[
                'QCheckBox()'
            ],
            'Depth of Recursion':[
                'QSpinBox()',
                'setRange(0,100)'
            ],
            'Listdown':[
                'QComboBox()',
                'addItem("1asd")',
                'addItem("best")'
            ]
        },
        # for setting the value for scanning and default in the start of the program
        'configs':{
            'Recursive Scraping':False,
            'Depth of Recursion': 1,
            'Listdown': 'best'
        }
    }
    
    def tool_working(url:str, tool_configs:dict) -> str:
        '''This function should return output in html format string'''
        pass
        