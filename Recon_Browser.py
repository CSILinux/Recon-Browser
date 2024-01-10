from PySide6.QtCore import (
    QThread, Signal, QUrl, Qt, QSize, QRect, QMetaObject, QCoreApplication, 
    QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QAction, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QFileDialog,
    QPushButton, QStatusBar, QLabel, QTextEdit, QPlainTextEdit, QLineEdit, QInputDialog,
     QScrollArea, QDialog, QTabWidget,  QMenuBar, QMenu, QCompleter, QSizePolicy,
      QDockWidget, QRadioButton, QCheckBox, QSpacerItem, QFormLayout, QSpinBox, QComboBox, QSlider, QDoubleSpinBox, QStackedLayout
      )
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
import qdarktheme



from csilibs.utils import pathme, CaseDirMe
from csilibs.gui import percentSize, BrowseMe

from Recon_Tools import *

import os, sys, subprocess
from urllib.parse import urlparse
from functools import partial
from CSI_Constants import *

import importlib.util



#---------------------------------------------- TOOL Setting DialogBox ------------------------------------------------#

class ToolConfigs(QDialog):
    def __init__(self,main_window, tool_name, *args, **kwargs):
        super().__init__()
        self.setWindowTitle(f"Settings")
        self.main_window = main_window
        self.main_layout = QVBoxLayout()
        self.setMaximumHeight(percentSize(main_window,0,100)[1])

        self.Heading = QLabel(f'{tool_name} Settings')
        self.Heading.setMaximumHeight(percentSize(main_window,0,5)[1])
        font = QFont()
        font.setFamily("Bahnschrift")
        font.setPointSize(14)
        self.Heading.setFont(font)
        self.Heading.setLayoutDirection(Qt.LeftToRight)
        self.Heading.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.Heading)
        
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(10,10,10,10)

        self.tool_settings = ReconTools.tools_list[tool_name]['settings_dialog']
        self.tool_configs = ReconTools.tools_list[tool_name]['configs']
        for i, setting in enumerate(self.tool_settings):
            self.label = QLabel(setting)
            self.widget = eval(self.tool_settings[setting][0])
            
            if len(self.tool_settings[setting]) > 1:
                for i in range(1, len(self.tool_settings[setting])):
                    eval(f"self.widget.{self.tool_settings[setting][i]}")

            self.configValue('get',self.widget, setting)
            self.connectSlot(self.widget, setting)

            self.form_layout.setWidget(i, QFormLayout.LabelRole, self.label)
            self.form_layout.setWidget(i, QFormLayout.FieldRole, self.widget)


        self.main_layout.addLayout(self.form_layout)
        self.setLayout(self.main_layout)


    def connectSlot(self, widget, setting_name):
        config_partial = partial(self.configValue, 'set', widget, setting_name)
        
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(config_partial)
        
        elif isinstance(widget, QTextEdit):
            widget.textChanged.connect(config_partial)
        
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(config_partial)
        
        elif isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(config_partial)
        
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(config_partial)
        
        elif isinstance(widget, QRadioButton):
            widget.toggled.connect(config_partial)
        
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(config_partial)
        
        elif isinstance(widget, QSlider):
            widget.valueChanged.connect(config_partial)


    def configValue(self, operation, widget, setting_name, dummy=0):
        if isinstance(widget, QLineEdit):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.text()
            elif operation == 'get':
                value = self.tool_configs[setting_name]
                widget.setText(value)
        
        elif isinstance(widget, QTextEdit):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.toPlainText()
            elif operation == 'get':
                value = self.tool_configs[setting_name]
                widget.setPlainText(value)
        
        elif isinstance(widget, QSpinBox):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.value()

            elif operation == 'get':
                value = self.tool_configs[setting_name]
                widget.setValue(value)
        
        elif isinstance(widget, QDoubleSpinBox):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.value()
            elif operation == 'get':
                value = self.tool_configs[setting_name]
                widget.setValue(value)
        
        elif isinstance(widget, QCheckBox):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.isChecked()
            elif operation == 'get':
                value = self.tool_configs[setting_name]
                widget.setChecked(value)
        
        elif isinstance(widget, QRadioButton):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.isChecked()
            elif operation == 'get':
                value = self.tool_configs[setting_name]
                widget.setChecked(value)
        
        elif isinstance(widget, QComboBox):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.currentText()
            elif operation == 'get':
                value = self.tool_configs[setting_name]
                index = widget.findText(value)
                if index != -1:
                    widget.setCurrentIndex(index)
                    
        elif isinstance(widget, QSlider):
            if operation == 'set':
                self.tool_configs[setting_name] = widget.value()
            elif operation == 'get':
                value = self.tool_configs[setting_name]
                widget.setValue(value)


#---------------------------------------------- MainWindow ------------------------------------------------#
class ReconMainWindow(QMainWindow):
    """The main window class for the CSI application."""

    def __init__(self, case_directory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_directory = case_directory
        self.setWindowTitle(f"ReconBrowser")
        self.setWindowIcon(QIcon(CSI_WIN_ICO))
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.application = None

     
        self.setGeometry(0,0, *percentSize(app,95,90))
        
        self.center()

        #-------------------------- MENU BAR --------------------------#
        
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, *percentSize(app,95,10)))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        
        # menu list
        self.menuList = QMenu(self.menubar)
        self.menuList.setTitle("Menu List")
        
        self.themeMenu = QMenu(self.menubar)
        self.themeMenu.setTitle("Themes")
        
        # menu options within menu list
        self.fullscreenOption = QAction(self)
        self.fullscreenOption.setShortcut("Ctrl+F")
        self.fullscreenOption.setText("FullScreen Toggle")
        self.fullscreenOption.setStatusTip("Click to move to and from FullScreen")
    
        self.menuList.addAction(self.fullscreenOption)

        self.menubar.addAction(self.menuList.menuAction())

        self.darkTheme = QAction(self)
        self.darkTheme.setText("Dark Theme")
        self.darkTheme.setStatusTip("Enable Dark theme")
        self.themeMenu.addAction(self.darkTheme)
        self.lightTheme = QAction(self)
        self.lightTheme.setText("Light Theme")
        self.lightTheme.setStatusTip("Enable Light theme")
        self.themeMenu.addAction(self.lightTheme)

        self.menubar.addAction(self.themeMenu.menuAction())

        self.darkTheme.triggered.connect(lambda: self.theme_change("dark"))
        self.lightTheme.triggered.connect(lambda: self.theme_change("light"))
        print("fullscreen",self.isFullScreen())
        self.fullscreenOption.triggered.connect(lambda: self.showFullScreen() if not self.isFullScreen() else self.showNormal())

         # Create a toolbar
        toolbar = self.addToolBar("Main Toolbar")

        # Create actions for the toolbar
        action_new = QAction("Add Tool Extension", self)

        # Add actions to the toolbar
        toolbar.addAction(action_new)

        # Connect actions to functions (optional)
        action_new.triggered.connect(self.new_action_triggered)

    def new_action_triggered(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # Use Qt's file dialog

        file_dialog = QFileDialog(self)
        file_dialog.setOptions(options)
        file_dialog.setWindowTitle("Open Python File")
        file_dialog.setNameFilter("Python Files (*.py)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)  # Set mode to select an existing file

        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                selected_file = selected_files[0]
                print(f"Selected file: {selected_file}")
                
                # Load the selected Python file as a module
                spec = importlib.util.spec_from_file_location("dynamic_module", selected_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check if the Tool4Recon class is available in the module
                if hasattr(module, "Tool4Recon"):
                    if os.path.basename(selected_file) == module.Tool4Recon.tool_name + '.py':
                        print("Tool4Recon class is available in the selected file.")
                        class_msg = 'Installation of the extension completed! Restart the Recon Browser'
                        with open(pathme('recon_extensions.txt'), 'a') as f:
                            f.write(f'{selected_file}\n')
                        QMessageBox.information(self, "Success", class_msg)
                        response = QMessageBox.question(self, "Restart Application", "Do you want to close the application?",
                                            QMessageBox.No | QMessageBox.Yes,QMessageBox.Yes)

                        if response == QMessageBox.Yes:                        
                            os.execv(sys.executable, ['python'] + sys.argv)
                    else:       
                        print("Recon tool name and extension file name should be same.")
                        class_msg = 'Recon tool name and extension file name should be same.'
                        QMessageBox.warning(self, "Invalid filename", class_msg)
                else:
                    print("Tool4Recon class is not available in the selected file.")
                    class_msg = 'This is not the python file for recon tool extension'
                    QMessageBox.warning(self, "Invalid Tool Extension", class_msg)
                    
                    



    def theme_change(self, theme_color):
        qdarktheme.setup_theme(theme_color)

    def center(self):
        qRect = self.frameGeometry()
        center_point = QGuiApplication.primaryScreen().availableGeometry().center()
        qRect.moveCenter(center_point)
        self.move(qRect.topLeft())

    def set_application(self, application):
        """Set the application instance."""
        self.application = application
        
        

    def update_status(self, message):
        """Update the status bar with the given message."""
        self.status_bar.showMessage(message)  

class infoSectionGUI(QWidget):
    def __init__(self, dock, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dock = dock
        self.main_layout = QHBoxLayout()
        self.side_width = percentSize(self.dock,15,0)[0]
        
        scroll_area = QScrollArea()  # Create a scroll area widget
        scroll_widget = QWidget()  # Create a widget to hold the scrollable contents
        self.sideLayout = QVBoxLayout(scroll_widget)  # Set QVBoxLayout for the scrollable contents
        self.sideLayout.setSpacing(0)

        scroll_area.setWidgetResizable(True)  # Allow the scroll area to resize its content widget
        scroll_area.setWidget(scroll_widget)  # Set the scrollable contents to the scroll area
        self.main_layout.addWidget(scroll_area, 1)  # Add the scroll area to the cmd_layout
        # self.main_layout.addLayout(self.sideLayout,1)


        self.browser = QWebEngineView(self)
        # self.browser.setUrl(QUrl('https://google.com'))
        web_settings = self.browser.settings()
        web_settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        web_settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)


        self.main_layout.addWidget(self.browser,3)

        self.setLayout(self.main_layout)

    def addToolGatheredInfo(self, tool_name, html_path):
        psh_btn = QPushButton(tool_name)
        psh_btn.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        psh_btn.clicked.connect(partial(self.setPage, html_path))
        self.sideLayout.addWidget(psh_btn)
    
    def setPage(self, html_path):
        image_path = os.path.abspath(pathme(html_path))
        url = QUrl.fromLocalFile(image_path)
        self.browser.setUrl(url)

    def empty_page(self):
        pass
    # Future implementation for animated sidebar closing/opening
    # def toggle(self):
    #     self.anim = QPropertyAnimation(self.sidemenu,b"size")
    #     self.anim.setEasingCurve(QEasingCurve.OutBounce)
    #     if self.sidemenu.width() == self.side_width: 
    #         self.anim.setEndValue(QSize(0, 600))
    #     else:
    #         self.anim.setEndValue(QSize(self.side_width, 600))
            
    #     self.anim.setDuration(1500)
    #     self.anim.start()

class ReconBrowserGUI(QWidget):
    def __init__(self, main_window, case_directory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.case_name = os.path.split(case_directory)[1]
        self.case_directory = case_directory
        evidence_dir = os.path.join(self.case_directory, f"Evidence/Online/")    # Change "Folder" to the appropriate evidence sub-folder
        self.main_layout = QHBoxLayout()
        self.website_gathered_info=[]
        self.info_tabs = []
        ReconTools(init_ext = True)
        
        # Dock will be fixed for every tabs.
        # RECON TOOLS SETTING SECTION
        #----------------------------------- LEFT DOCK -------------------------------------#
        self.leftDock = QDockWidget(main_window)
        self.leftDock.setAllowedAreas(Qt.NoDockWidgetArea)
        self.leftDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.leftDock.setWindowTitle(QCoreApplication.translate("main_window", u"Recon Tools", None))
        self.leftDock.setMinimumWidth(percentSize(main_window,30,0)[0])
        self.leftDockContent = QWidget()
        self.leftDockContent.setObjectName("leftDockContent")
        self.leftDock.setWidget(self.leftDockContent)
        main_window.addDockWidget(Qt.DockWidgetArea(1), self.leftDock)

        self.tools_widget = QWidget(self.leftDockContent)
        self.tools_layout = QVBoxLayout()
        self.tools_widget.setMinimumWidth(percentSize(self.leftDock,98,0)[0])
        self.tools_widget.setLayout(self.tools_layout)

        self.start_btn = QPushButton("Start RECON")
        font = QFont()
        font.setFamily("Bahnschrift")
        font.setPointSize(14)
        self.start_btn.setFont(font)
        self.start_btn.clicked.connect(self.start_gather)

        self.layout_btns1 = QHBoxLayout()
        self.check_all_btn = QPushButton("Check All")
        self.uncheck_all_btn = QPushButton("UnCheck All")
        self.check_all_btn.clicked.connect(partial(self.toggleAll, True))
        self.uncheck_all_btn.clicked.connect(partial(self.toggleAll, False))
        self.layout_btns1.addWidget(self.check_all_btn)
        self.layout_btns1.addWidget(self.uncheck_all_btn)

        self.tools_layout.addWidget(self.start_btn)
        self.tools_layout.addLayout(self.layout_btns1)

        self.hor_spacer = QSpacerItem(percentSize(self.leftDock,98,0)[0],20)
        self.tools_layout.addItem(self.hor_spacer)
        
        self.push_btns = [QPushButton() for i in ReconTools.tools_list]
        
        # adding context menu to buttons
        self.context_menus = [QMenu(self) for i in self.push_btns]

        for i, (tool_name, settings) in enumerate(ReconTools.tools_list.items()):
            push_btn = self.push_btns[i]
            push_btn.setText(tool_name)
            push_btn.setCheckable(True)
            push_btn.setChecked(settings['checked'])
            push_btn.setIcon(QIcon(QPixmap(settings['icon'])))
            push_btn.toggled.connect(partial(self.check_btn,push_btn))            
            self.tools_layout.addWidget(push_btn)

            if settings.get('settings_dialog') != None:
                push_btn.setContextMenuPolicy(Qt.CustomContextMenu)
                push_btn.customContextMenuRequested.connect(partial(self.on_context_menu,i,push_btn))
                self.context_menus[i].addAction(QAction(f"{tool_name} Settings", self, triggered=partial(self.openSettings,i)))

    
        # GATHERED INFO SECTION
        #----------------------------------- BOTTOM DOCK -------------------------------------#
        self.bottomDock = QDockWidget(main_window)
        self.bottomDock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.bottomDock.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.bottomDock.setWindowTitle(QCoreApplication.translate("main_window", u"Gathered Information", None))
        self.bottomDock.setMinimumHeight(percentSize(main_window,0,40)[1])

        self.bottomDockContent = QWidget()
        self.bottomDockContent.setObjectName("bottomDockContent")
        self.bottomDock.setWidget(self.bottomDockContent)
        main_window.addDockWidget(Qt.BottomDockWidgetArea, self.bottomDock)

        # Create a QVBoxLayout for the bottomDockContent
        self.bottomDockContentLayout = QVBoxLayout(self.bottomDockContent)
        self.bottomDockContentLayout.setContentsMargins(0, 0, 0, 0)

        self.infoTabWidget  = QTabWidget()
        self.infoTabWidget.setTabsClosable(True)
        self.infoTabWidget.tabCloseRequested.connect(self.close_tab)
        self.bottomDockContentLayout.addWidget(self.infoTabWidget)

        #----------------------------------- Web Browser -------------------------------------#
        self.browser_widget = QWidget()
        self.image_layout = QVBoxLayout()
        self.browser_widget.setLayout(self.image_layout)
        self.scroll_area2 = QScrollArea()
        self.scroll_area2.setWidgetResizable(True)
        self.scroll_content_widget2 = QWidget()
        self.scroll_layout2 = QVBoxLayout(self.scroll_content_widget2)
        
        self.browse_me = BrowseMe(self, evidence_dir)  # Pass evidence_dir argument
        print("reached here")
        
        self.scroll_layout2.addWidget(self.browse_me)
        self.scroll_area2.setWidget(self.scroll_content_widget2)
        self.image_layout.addWidget(self.scroll_area2)
        # Load the file URL "Images/Adult_Content.jpg"
        # image_path = os.path.abspath(pathme("assets/fingerprint_banner.jpg"))
        # url = QUrl.fromLocalFile(image_path)
        # url = "https://johnhammond.org/"
        url = "http://localhost"
        self.browse_me.browser.setUrl(url)

        self.main_layout.addWidget(self.browser_widget)

        self.setLayout(self.main_layout)
    
    def on_context_menu(self,index,btn, point):
        # show context menu
        self.context_menus[index].exec_(btn.mapToGlobal(point))

    def openSettings(self,index):
        tool_name  = self.push_btns[index].text()
        # testcase
        if type(ReconTools.tools_list[tool_name]['settings_dialog']) is not str: 
            dialog = ToolConfigs(self.main_window,tool_name)
        else:
            tool_dialog_name = ReconTools.tools_list[tool_name]['settings_dialog']
            dialog = eval(f"{tool_dialog_name}(self.main_window,tool_name)")

        dialog.exec_()

    def check_btn(self, btn, is_check):
        ReconTools.tools_list[btn.text()]['checked'] = is_check

    def start_gather(self):
        url = self.browse_me.browser.url().toString()
        domain = urlparse(url).netloc
        start_scan = False
        if domain != '':
            if domain.endswith('.onion') or domain.endswith('.i2p') or domain.endswith('.loki') or domain.startswith('localhost') or domain.startswith('127.0.0.1'):
                self.push_btns[0].setChecked(False)
            for push_btn in self.push_btns:
                if push_btn.isChecked():
                    start_scan = True
                    break
            if start_scan == True:
                recon = ReconTools(url, self.case_directory)
                self.website_gathered_info.append(recon)
                recon.start()
                info_tab = infoSectionGUI(self.bottomDockContent)
                self.info_tabs.append(info_tab)
                self.infoTabWidget.addTab(info_tab,f'Recon {len(self.info_tabs)}')
                recon.data_fetched.connect(partial(self.showInfo,len(self.info_tabs)))
                recon.progress.connect(self.showStatus)
        else:
            print("enter valid url")
            

    def toggleAll(self, check):    # to uncheck or check all tools

        for tool_name in ReconTools.tools_list:
            ReconTools.tools_list[tool_name]['checked'] = check

        for btn in self.push_btns:
            btn.setChecked(check)

    def close_tab(self, index):
        self.infoTabWidget.removeTab(index)
        recon_tab = self.website_gathered_info.pop(index)
        recon_tab.quit()
    
    def showInfo(self, index, tool_name, html_path):
        self.info_tabs[index - 1].addToolGatheredInfo(tool_name, html_path)

    def showStatus(self, msg, timeout):
        self.main_window.status_bar.showMessage(msg, timeout)



def reconMain(case):
    # global case_name,case_directory
    case_name = case
    global app
    app = QApplication(sys.argv + ['--no-sandbox'])
    # qdarktheme.setup_theme()
    qdarktheme.setup_theme()
    case_directory = CaseDirMe(case_name,create=True).case_dir      
    # Create the main window
    main_window = ReconMainWindow(case_directory)
    
    widget = ReconBrowserGUI(main_window, case_directory)
    
    main_window.setCentralWidget(widget)
    main_window.set_application(app)
    
    print(f"checking {main_window}")
    print(f"checking app {app}")
    print(f"checking win {widget}")
    
    # Show the main window
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(f"Usage:\n \033[32m python {sys.argv[0]} <case_name> \033[39m")
        print(f'If case_name doesn\'t exist then it will open New Case Wizard')
        exit()
    casename = sys.argv[1]
   # reconMain to integrate into another py program
   # reconMainWindow to integrate into another Application GUI
    reconMain(casename)