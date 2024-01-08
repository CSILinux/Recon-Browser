from PySide2.QtCore import (
    QThread, Signal, QUrl, Qt, QSize, QRect, QMetaObject, QCoreApplication, 
    QPropertyAnimation, QEasingCurve, QStringListModel
)
from PySide2.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
from PySide2.QtWidgets import (
    QApplication, QDesktopWidget, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QMessageBox,
    QPushButton, QStatusBar, QLabel, QTextEdit, QPlainTextEdit, QLineEdit, QInputDialog,
     QScrollArea, QDialog, QTabWidget, QAction, QMenuBar, QMenu, QCompleter, QSizePolicy,
      QDockWidget, QRadioButton, QCheckBox, QSpacerItem, QFormLayout, QSpinBox, QComboBox, QSlider, QDoubleSpinBox, QStackedLayout
      )
import os, sys, re
from yattag import Doc, indent
import whois as who_is

from csi_scanner_darkly_scraper import main_scraper
from CSI_Constants import *
from sharedfunctions import pathMe, CaseDirMe, percentSize, BrowseMe
from lib_nmap import nmapCmd

from urllib.parse import urlparse
import imp
import textwrap
import types


class ReconTools(QThread):
    data_fetched = Signal(str, str)
    progress = Signal(str, int)
    finished = Signal()
    exts_path = []
    
    tools_list = {
        'Whois':{
            'icon': '',
            'checked':False
        },


        'CSI-Scraper':{ 
            'icon': CSI_WIN_ICO,
            'checked':False,
            # for creating setting dialog GUI easily
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
            # for setting the value for scanning and default in the start
            'configs':{
                'Recursive Scraping':False,
                'Depth of Recursion': 1,
                'Listdown': 'best'
            }
        },


        'Nmap':{
            'icon': '',
            'checked':False, 
             # Custom to create own QDialogue widget
            'settings_dialog':'NmapDialog',
            # for setting the value for scanning and default in the start
            'configs':{
                'Ports Range':'top 100',
                'Scan Type': '(-sT) TCP Connect Scan',
                'NSE Scripts': '',
                'Listdown': 'best'
            }  
        },

        'Sublist3r':{
            'icon': '',
            'checked':False
        },
    }

    def __init__(self, url='', case_directory='', init_ext = False,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.case_name = os.path.split(case_directory)[1]
        self.recon_info_dir = os.path.join(case_directory,"Evidence/Online/ReconBrowser",urlparse(url).netloc)
        if not os.path.exists(self.recon_info_dir):
            os.makedirs(self.recon_info_dir)
        
        if init_ext == True:
            with open(pathMe('recon_extensions.txt'),'r') as f:
                ReconTools.exts_path  = f.read().split()
                
        if ReconTools.exts_path != [] :
            
            for i, ext_p in enumerate(ReconTools.exts_path):
                if init_ext == True:    
                    ReconToolExt = getattr(imp.load_source(f'extension_{i}', ext_p), 'Tool4Recon')
                    ReconToolExt.tool_attribs['checked'] = False
                    ReconToolExt.tool_attribs['icon'] = ''
                    ReconTools.tools_list[ReconToolExt.tool_name] = ReconToolExt.tool_attribs
                        
                method_name = os.path.basename(ext_p).split('.')[0].replace('-','_').replace(' ','_').lower()
                
                def dynamic_method(self, tool_name):
                    print('in func :',tool_name)
                    
                    def find_element_with_substring(input_list, substring):
                        for item in input_list:
                            if substring in item:
                                return item
                        return None
                    ext_path = find_element_with_substring(ReconTools.exts_path,tool_name)
                    ReconToolExt = getattr(imp.load_source(f'{tool_name}', ext_path), 'Tool4Recon')
                    
                    html_text = ReconToolExt.tool_working(self.url, self.tools_list[tool_name]['configs'])
                    print(html_text)
                    tool_dir = os.path.join(self.recon_info_dir, f'{tool_name}.html')
                    
                    with open(tool_dir,'w') as file:
                        file.write(html_text)

                    return tool_dir

                new_method_func = types.MethodType(dynamic_method, self)

                setattr(self, method_name, new_method_func)
                        
    def run(self):
        # print(self.testing_framework('tset'))
        for tool_name, settings in self.tools_list.items():
            if settings['checked'] == True:

                self.progress.emit(f"{tool_name} tool is running now...", 0) # 0 timeout to keep the message at status until it changes by another message
                tool_func_name = tool_name.replace('-','_').replace(' ','_').lower()
                print(tool_func_name)
                html_path = eval(f'self.{tool_func_name}(tool_name)')
                print(html_path)
                self.data_fetched.emit(tool_name,html_path)

        self.progress.emit(f"Recon completed successfully on {self.url}", 5)
        
    # If you want to add the method for the new tool then
    # name of method should be lowercase and identical to the tools_list name and use _ in place of -
    def whois(self, tool_name):
        try:
            data = who_is.whois(self.url)
        except who_is.parser.PywhoisError as e:
            print("Error: ", str(e))
        
        doc, tag, text, line = Doc().ttl()

        doc.asis('<!DOCTYPE html>')
        with tag('html'):
            with tag('head'):
                doc.asis('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma.min.css">')
            with tag('body'):
                with tag('section', klass='section'):
                    with tag('div', klass='container'):
                        
                        doc.asis(f"<section class='hero is-link'><div class='hero-body'><h1 class='title is-1'>{tool_name}</h1></div></section>")
                 
                        for i, (name, value) in enumerate(data.items()):
                            with tag('p'):
                                line('b',f'{name}: ')
                                if isinstance(value, list):
                                    with tag('ul'):
                                        for ele in value:
                                            line('li',str(ele))
                                elif isinstance(value, str) or isinstance(value, int):
                                    text(value)
        tool_dir = os.path.join(self.recon_info_dir, f'{tool_name}.html')
        with open(tool_dir,'w') as file:
            file.write(indent(doc.getvalue()))

        return tool_dir

        

    def nmap(self, tool_name):
        hostname = urlparse(self.url).netloc
        tool_config = self.tools_list[tool_name]['configs']
        ports_range = tool_config['Ports Range']
        scan_type = re.search(r'\((.*?)\)',tool_config['Scan Type']).group(1)
        port_range_args = ''
        
        if 'top' in ports_range.lower():
            temp = int(ports_range.replace('top','')) 
            port_range_args = f'--top-ports {temp}'
        elif ',' in ports_range:
            port_range_args = f'-p{ports_range}'
        elif '-' in ports_range:
            temp = [int(i) for i in ports_range.split('-')]
            port_range_args = f'-p{str(temp[0])}-{str(temp[1])}'
        elif ports_range.strip().isdigit():
            port_range_args = f'-p0-{ports_range.strip()}'
        elif ports_range == '':
            port_range_args = ''

        scripts_arg = f"--script={tool_config['NSE Scripts']}" if tool_config['NSE Scripts'] != '' else ''
        
        scan_results = nmapCmd(f"{scan_type} {port_range_args} {scripts_arg}",hostname)['nmaprun']
        data = ''
        # Filter data from scan_results
        hosts_info = scan_results["host"]
        ports_info = hosts_info['ports']['port']
        data += f'<h5 class="title is-5">Scan Started at: {scan_results["@startstr"]}</h5>'
        data += f'<h5 class="title is-5">Host is {hosts_info["status"]["@state"]}</h5>'
        data += f'<h5 class="title is-5">Address: {hosts_info["address"]["@addr"]} ({hosts_info["address"]["@addrtype"]})</h5>'
        
        data += f'<table>'
        data += '<tr><th>PORTS</th><th>STATE</th><th>SERVICE</th><th>VERSION</th></th>'
        for port in ports_info:
            service_list = ''
            if port['service']['@method'] != 'table':
                for key, value in port['service'].items():
                    if key != '@name':
                        service_list += f'<li>{key.strip("@")}: {value}</li>'
            else:
                service_list = 'None'
            data += f"<tr><td><b>{port['@portid']} / {port['@protocol']}</b></td><td>{port['state']['@state']}</td><td>{port['service']['@name']}</td><td><ul>{service_list}</ul></td></tr>"
            
            if port.get('script') != None: 
                if isinstance(port['script'],list):
                    for script in port['script']:
                        data += f"<tr><td>> {script['@id']}</td><td colspan=3><pre>{script['@output']}</pre></td></tr>"
                elif isinstance(port['script'],dict):
                    data += f"<tr><td>> {port['script']['@id']}</td><td colspan=3><pre>{port['script']['@output']}</pre></td></tr>"

        data += f'</table>'      
        data += f"<h5 class='title is-5'>Scan Summary: {scan_results['runstats'].get('finished').get('@summary')}</h5>"
 
        

        # This code block can be used with some other data 
        # def create_html_from_dict(data, doc, parent_tag=None, in_table=False, heading=3):
        #     if parent_tag is None:
        #         # Create a new parent <div> tag if it is not provided
        #         with doc.tag('div'):
        #             create_html_from_dict(data, doc, parent_tag=doc.tag)
        #     else:
        #         for key, value in data.items():
        #             if isinstance(value, dict):
        #                 doc.asis('</table>')
        #                 with doc.tag('details'):
        #                     with doc.tag('summary', klass=f'title is-{heading}'):
        #                         doc.text(key)
        #                     with doc.tag('table'):
        #                         create_html_from_dict(value, doc, parent_tag=doc.tag, in_table=True, heading=heading+1)
        #             elif isinstance(value, list):
        #                 doc.asis('</table>')
        #                 with doc.tag('ul'):
        #                     for item in value:
        #                         if isinstance(item, dict):
        #                             with doc.tag('li'):
        #                                 with doc.tag('details'):
        #                                     with doc.tag('summary', klass=f'title is-{heading}'):
        #                                         doc.text(key)
        #                                     with doc.tag('table'):
        #                                         create_html_from_dict(item, doc, parent_tag=doc.tag, in_table=True, heading=heading+1)
        #                         else:
        #                             with doc.tag('li'):
        #                                 doc.text(item)
        #             else:
        #                 if in_table == False:
        #                     doc.asis('<table>')
        #                     in_table = True
        #                 with doc.tag('tr'):
        #                     doc.line('td',key)
        #                     doc.line('td',value)
        
        # Rendering output to HTML
        doc, tag, text, line = Doc().ttl()
                            
        doc.asis('<!DOCTYPE html>')
        with tag('html'):
            with tag('head'):
                doc.asis('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma.min.css">')
            with tag('body'):
                with tag('section', klass='section'):
                    with tag('div', klass='container'):
                        
                        doc.asis(f"<section class='hero is-link'><div class='hero-body'><h1 class='title is-1'>{tool_name}</h1><p class='subtitle'>{scan_results['@args']}</p></div></section>")
                        
                        doc.asis(f"{data}")
                        with tag('script'):
                            doc.asis("""const tables = document.querySelectorAll('table');
                                    console.log(tables)
                                    tables.forEach(table => {
                                        table.classList.add('table','is-bordered', 'is-striped', 'is-narrow', 'is-hoverable', 'is-fullwidth');
                                    });
                                """)

        tool_dir = os.path.join(self.recon_info_dir, f'{tool_name}.html')
        with open(tool_dir,'w') as file:
            file.write(doc.getvalue())

        return tool_dir


    def sublist3r(self):
        pass

    def csi_scraper(self, tool_name):
        print('starting CSI Scraper')
        tool_config = self.tools_list[tool_name]['configs']
        recurse = tool_config['Recursive Scraping']
        depth = tool_config['Depth of Recursion']
        
        data = main_scraper(self.case_name,'csi-scraped',self.url, 'n', recurse, depth)

        doc, tag, text, line = Doc().ttl()
        count = 0   # for assigning different var names for recursive data charts
        def chart_script(chart_name, chart_values,count):
            with tag('script'):
                text(f"""// Get the canvas element
                    var ctx_{chart_name}{str(count)} = document.getElementById('{chart_name}{str(count)}').getContext('2d');

                    // Define the chart data
                    var chartData_{chart_name}{str(count)} = {{
                    labels: {str(list(chart_values.keys()))},
                    datasets: [{{
                        label: '{chart_name}',
                        data: {str(list(chart_values.values()))},
                        borderWidth: 1
                    }}]
                    }};
                """)
                text(f""" 
                    // Create the chart
                    var myChart_{chart_name}{str(count)} = new Chart(ctx_{chart_name}{str(count)}, {{
                    type: 'bar',
                    data: chartData_{chart_name}{str(count)},
                    options: {{
                            scales: {{
                                y: {{
                                    beginAtZero: true
                                }}
                            }}
                        }}
                    }});
                    """)
        def webpageData(data,count):
            count += 1
            for i, (name, value) in enumerate(data.items()):
                    if i != 0:
                        if not name.startswith('http'):
                            with tag('p'):
                                line('b',f'{name}: ')
                                if isinstance(value, list):
                                    with tag('ul'):
                                        for ele in value:
                                            line('li',ele)
                                elif isinstance(value, dict):
                                    if name == 'keywords':
                                        for chart_name, chart_vals in value.items():
                                            if chart_vals != {}:
                                                with tag('canvas', id=f"{chart_name}{str(count)}"):
                                                    pass
                                                chart_script(chart_name,chart_vals,count)

                                elif isinstance(value, str) or isinstance(value, int):
                                    text(value)
                        else:
                            with tag('details'):
                                line('summary',name)
                                webpageData(value, count)
    
        doc.asis('<!DOCTYPE html>')
        with tag('html'):
            with tag('head'):
                doc.asis('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma.min.css">')
                doc.asis('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
            with tag('body'):
                with tag('section', klass='section'):
                    with tag('div', klass='container'):
                        
                        doc.asis(f"<section class='hero is-link'><div class='hero-body'><h1 class='title is-1'>{tool_name}</h1><p class='subtitle'>{data['link']}</p></div></section>")
                       
                        webpageData(data,count)
                
        tool_dir = os.path.join(self.recon_info_dir, f'{tool_name}.html')
        with open(tool_dir,'w') as file:
            file.write(indent(doc.getvalue()))

        return tool_dir

    # Method structure for new tool integration
    # def <toolname_in_lowercase_useUnderscore>(self, tool_name):
    #     tool_config = self.tools_list[tool_name]['configs']
    #     doc, tag, text, line = Doc().ttl()

    #         doc.asis('<!DOCTYPE html>')
    #         with tag('html'):
    #             with tag('body'):
    #                 line('h1', tool_name)
    #     tool_dir = os.path.join(self.recon_info_dir, f'{tool_name}.html')
    #     with open(tool_dir,'w') as file:
    #         file.write(indent(doc.getvalue()))

    #     return tool_dir
class CommaCompleter(QCompleter):
    commaKeyPressed = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectedCompletion = ""

    def splitPath(self, path):
        if path[-1:] == ",":
            self.commaKeyPressed.emit()
            return [""]
        return path.split(",")[-1:]

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress and event.key() == Qt.Key_Enter:
            # Handle Enter key press to append the selected completion
            if self.popup().isVisible():
                print('current',self.popup().currentIndex())
                self.activated.emit(self.popup().currentIndex())
                return True

        return super().eventFilter(obj, event)

    def onCompletionSelected(self, completion):
        if self.widget() and isinstance(self.widget(), QLineEdit):
            current_text = self.widget().text()
            prefix = self.completionPrefix()
            if prefix:
                current_text = current_text.rsplit(",", 1)[0].strip()
            self.widget().setText(current_text + completion + ", ")
            self.widget().setCursorPosition(len(self.widget().text()))

    def setModel(self, model):
        if not isinstance(model, QStringListModel):
            model = QStringListModel(model, self)
        super().setModel(model)

    def pathFromIndex(self, index):
        # Override pathFromIndex to return only the completion without the prefix
        suggestion = index.data(Qt.DisplayRole)
        
        prefix = self.widget().text()
        items = [item.strip() for item in prefix.split(',')]

        # Join the items again with a comma and create a new list with the result
        result_list = ','.join(items[:-1])
        if result_list != '':
            result_list += ', '
        return f"{result_list}{suggestion}"


# If you want to create your own Settings Dialog box for a tool then
# Create a child class of QDialog for your tool and then
# add settings_dialog:<nameYourToolDialogClass> in tools_list
class NmapDialog(QDialog):
    def __init__(self,main_window, tool_name, *args, **kwargs):
        super().__init__()
        self.nmap_configs = ReconTools.tools_list['Nmap']['configs']
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

        self.tool_configs = ReconTools.tools_list[tool_name]['configs']


        # Ports Range
        self.port_label = QLabel('Ports Range :')
        self.port_label.setToolTip("""Help:
                              
• Scan ports upto: 1000
• Scan the range of ports: 20-500
• Scan selected ports: 21,22,80,443
• Scan single port: 443,                              
• Scan top commonly used ports: top 500
• Defaults no of ports (leave input empty)""")
        self.port_textbox = QLineEdit()
        self.port_textbox.setText(self.tool_configs['Ports Range'])
        self.port_textbox.setCompleter(QCompleter(['top 100', 'top 500', 'top 1000', '21,22,23,25,139,143,80,443,8000,8080', '80,443,8080,8000', '20-1024']))

        self.form_layout.setWidget(0, QFormLayout.LabelRole, self.port_label)
        self.form_layout.setWidget(0, QFormLayout.FieldRole, self.port_textbox)


        # Scan Type
        self.scans_label = QLabel('Scan Type :')
        self.scans_combobox = QComboBox()
        self.scans_combobox.addItems([
            '(-sT) TCP Connect Scan',
            '(-sS) SYN Scan',
            '(-sA) ACK Scan',
            '(-sU) UDP Scan',
            '(-sV) Version Detection Scan',
            '(-A) Aggressive Scan',
            ])
        # self.scans_combobox.
        self.scans_combobox.currentIndexChanged.connect(self.toolTip4Scans)
        self.form_layout.setWidget(1, QFormLayout.LabelRole, self.scans_label)
        self.form_layout.setWidget(1, QFormLayout.FieldRole, self.scans_combobox)
       
        
        # NSE Scripts
        self.scripts_label = QLabel('NSE Scripts :')
        self.scripts_label.setToolTip("""Use multiple NSE scripts simultaneously by separating them with a comma ','.

Explore the list of NSE scripts here: https://nmap.org/nsedoc/scripts/

To use all NSE scripts related to a specific pattern, employ the wildcard '', e.g., http for all HTTP-related NSE scripts.""")
        self.scripts_textbox = QLineEdit()
        self.scripts_textbox.setText(self.tool_configs['NSE Scripts'])
        completer = CommaCompleter(['acarsd-info', 'address-info', 'afp-brute', 'afp-ls', 'afp-path-vuln', 'afp-serverinfo', 'afp-showmount', 'ajp-auth', 'ajp-brute', 'ajp-headers', 'ajp-methods', 'ajp-request', 'allseeingeye-info', 'amqp-info', 'asn-query', 'auth-owners', 'auth-spoof', 'backorifice-brute', 'backorifice-info', 'bacnet-info', 'banner', 'bitcoin-getaddr', 'bitcoin-info', 'bitcoinrpc-info', 'bittorrent-discovery', 'bjnp-discover', 'broadcast-ataoe-discover', 'broadcast-avahi-dos', 'broadcast-bjnp-discover', 'broadcast-db2-discover', 'broadcast-dhcp-discover', 'broadcast-dhcp6-discover', 'broadcast-dns-service-discovery', 'broadcast-dropbox-listener', 'broadcast-eigrp-discovery', 'broadcast-hid-discoveryd', 'broadcast-igmp-discovery', 'broadcast-jenkins-discover', 'broadcast-listener', 'broadcast-ms-sql-discover', 'broadcast-netbios-master-browser', 'broadcast-networker-discover', 'broadcast-novell-locate', 'broadcast-ospf2-discover', 'broadcast-pc-anywhere', 'broadcast-pc-duo', 'broadcast-pim-discovery', 'broadcast-ping', 'broadcast-pppoe-discover', 'broadcast-rip-discover', 'broadcast-ripng-discover', 'broadcast-sonicwall-discover', 'broadcast-sybase-asa-discover', 'broadcast-tellstick-discover', 'broadcast-upnp-info', 'broadcast-versant-locate', 'broadcast-wake-on-lan', 'broadcast-wpad-discover', 'broadcast-wsdd-discover', 'broadcast-xdmcp-discover', 'cassandra-brute', 'cassandra-info', 'cccam-version', 'cics-enum', 'cics-info', 'cics-user-brute', 'cics-user-enum', 'citrix-brute-xml', 'citrix-enum-apps', 'citrix-enum-apps-xml', 'citrix-enum-servers', 'citrix-enum-servers-xml', 'clamav-exec', 'clock-skew', 'coap-resources', 'couchdb-databases', 'couchdb-stats', 'creds-summary', 'cups-info', 'cups-queue-info', 'cvs-brute', 'cvs-brute-repository', 'daap-get-library', 'daytime', 'db2-das-info', 'deluge-rpc-brute', 'dhcp-discover', 'dicom-brute', 'dicom-ping', 'dict-info', 'distcc-cve2004-2687', 'dns-blacklist', 'dns-brute', 'dns-cache-snoop', 'dns-check-zone', 'dns-client-subnet-scan', 'dns-fuzz', 'dns-ip6-arpa-scan', 'dns-nsec-enum', 'dns-nsec3-enum', 'dns-nsid', 'dns-random-srcport', 'dns-random-txid', 'dns-recursion', 'dns-service-discovery', 'dns-srv-enum', 'dns-update', 'dns-zeustracker', 'dns-zone-transfer', 'docker-version', 'domcon-brute', 'domcon-cmd', 'domino-enum-users', 'dpap-brute', 'drda-brute', 'drda-info', 'duplicates', 'eap-info', 'enip-info', 'epmd-info', 'eppc-enum-processes', 'fcrdns', 'finger', 'fingerprint-strings', 'firewalk', 'firewall-bypass', 'flume-master-info', 'fox-info', 'freelancer-info', 'ftp-anon', 'ftp-bounce', 'ftp-brute', 'ftp-libopie', 'ftp-proftpd-backdoor', 'ftp-syst', 'ftp-vsftpd-backdoor', 'ftp-vuln-cve2010-4221', 'ganglia-info', 'giop-info', 'gkrellm-info', 'gopher-ls', 'gpsd-info', 'hadoop-datanode-info', 'hadoop-jobtracker-info', 'hadoop-namenode-info', 'hadoop-secondary-namenode-info', 'hadoop-tasktracker-info', 'hbase-master-info', 'hbase-region-info', 'hddtemp-info', 'hnap-info', 'hostmap-bfk', 'hostmap-crtsh', 'hostmap-robtex', 'http-adobe-coldfusion-apsa1301', 'http-affiliate-id', 'http-apache-negotiation', 'http-apache-server-status', 'http-aspnet-debug', 'http-auth', 'http-auth-finder', 'http-avaya-ipoffice-users', 'http-awstatstotals-exec', 'http-axis2-dir-traversal', 'http-backup-finder', 'http-barracuda-dir-traversal', 'http-bigip-cookie', 'http-brute', 'http-cakephp-version', 'http-chrono', 'http-cisco-anyconnect', 'http-coldfusion-subzero', 'http-comments-displayer', 'http-config-backup', 'http-cookie-flags', 'http-cors', 'http-cross-domain-policy', 'http-csrf', 'http-date', 'http-default-accounts', 'http-devframework', 'http-dlink-backdoor', 'http-dombased-xss', 'http-domino-enum-passwords', 'http-drupal-enum', 'http-drupal-enum-users', 'http-enum', 'http-errors', 'http-exif-spider', 'http-favicon', 'http-feed', 'http-fetch', 'http-fileupload-exploiter', 'http-form-brute', 'http-form-fuzzer', 'http-frontpage-login', 'http-generator', 'http-git', 'http-gitweb-projects-enum', 'http-google-malware', 'http-grep', 'http-headers', 'http-hp-ilo-info', 'http-huawei-hg5xx-vuln', 'http-icloud-findmyiphone', 'http-icloud-sendmsg', 'http-iis-short-name-brute', 'http-iis-webdav-vuln', 'http-internal-ip-disclosure', 'http-joomla-brute', 'http-jsonp-detection', 'http-litespeed-sourcecode-download', 'http-ls', 'http-majordomo2-dir-traversal', 'http-malware-host', 'http-mcmp', 'http-method-tamper', 'http-methods', 'http-mobileversion-checker', 'http-ntlm-info', 'http-open-proxy', 'http-open-redirect', 'http-passwd', 'http-php-version', 'http-phpmyadmin-dir-traversal', 'http-phpself-xss', 'http-proxy-brute', 'http-put', 'http-qnap-nas-info', 'http-referer-checker', 'http-rfi-spider', 'http-robots.txt', 'http-robtex-reverse-ip', 'http-robtex-shared-ns', 'http-sap-netweaver-leak', 'http-security-headers', 'http-server-header', 'http-shellshock', 'http-sitemap-generator', 'http-slowloris', 'http-slowloris-check', 'http-sql-injection', 'http-stored-xss', 'http-svn-enum', 'http-svn-info', 'http-title', 'http-tplink-dir-traversal', 'http-trace', 'http-traceroute', 'http-trane-info', 'http-unsafe-output-escaping', 'http-useragent-tester', 'http-userdir-enum', 'http-vhosts', 'http-virustotal', 'http-vlcstreamer-ls', 'http-vmware-path-vuln', 'http-vuln-cve2006-3392', 'http-vuln-cve2009-3960', 'http-vuln-cve2010-0738', 'http-vuln-cve2010-2861', 'http-vuln-cve2011-3192', 'http-vuln-cve2011-3368', 'http-vuln-cve2012-1823', 'http-vuln-cve2013-0156', 'http-vuln-cve2013-6786', 'http-vuln-cve2013-7091', 'http-vuln-cve2014-2126', 'http-vuln-cve2014-2127', 'http-vuln-cve2014-2128', 'http-vuln-cve2014-2129', 'http-vuln-cve2014-3704', 'http-vuln-cve2014-8877', 'http-vuln-cve2015-1427', 'http-vuln-cve2015-1635', 'http-vuln-cve2017-1001000', 'http-vuln-cve2017-5638', 'http-vuln-cve2017-5689', 'http-vuln-cve2017-8917', 'http-vuln-misfortune-cookie', 'http-vuln-wnr1000-creds', 'http-waf-detect', 'http-waf-fingerprint', 'http-webdav-scan', 'http-wordpress-brute', 'http-wordpress-enum', 'http-wordpress-users', 'http-xssed', 'https-redirect', 'iax2-brute', 'iax2-version', 'icap-info', 'iec-identify', 'ike-version', 'imap-brute', 'imap-capabilities', 'imap-ntlm-info', 'impress-remote-discover', 'informix-brute', 'informix-query', 'informix-tables', 'ip-forwarding', 'ip-geolocation-geoplugin', 'ip-geolocation-ipinfodb', 'ip-geolocation-map-bing', 'ip-geolocation-map-google', 'ip-geolocation-map-kml', 'ip-geolocation-maxmind', 'ip-https-discover', 'ipidseq', 'ipmi-brute', 'ipmi-cipher-zero', 'ipmi-version', 'ipv6-multicast-mld-list', 'ipv6-node-info', 'ipv6-ra-flood', 'irc-botnet-channels', 'irc-brute', 'irc-info', 'irc-sasl-brute', 'irc-unrealircd-backdoor', 'iscsi-brute', 'iscsi-info', 'isns-info', 'jdwp-exec', 'jdwp-info', 'jdwp-inject', 'jdwp-version', 'knx-gateway-discover', 'knx-gateway-info', 'krb5-enum-users', 'ldap-brute', 'ldap-novell-getpass', 'ldap-rootdse', 'ldap-search', 'lexmark-config', 'llmnr-resolve', 'lltd-discovery', 'lu-enum', 'maxdb-info', 'mcafee-epo-agent', 'membase-brute', 'membase-http-info', 'memcached-info', 'metasploit-info', 'metasploit-msgrpc-brute', 'metasploit-xmlrpc-brute', 'mikrotik-routeros-brute', 'mmouse-brute', 'mmouse-exec', 'modbus-discover', 'mongodb-brute', 'mongodb-databases', 'mongodb-info', 'mqtt-subscribe', 'mrinfo', 'ms-sql-brute', 'ms-sql-config', 'ms-sql-dac', 'ms-sql-dump-hashes', 'ms-sql-empty-password', 'ms-sql-hasdbaccess', 'ms-sql-info', 'ms-sql-ntlm-info', 'ms-sql-query', 'ms-sql-tables', 'ms-sql-xp-cmdshell', 'msrpc-enum', 'mtrace', 'murmur-version', 'mysql-audit', 'mysql-brute', 'mysql-databases', 'mysql-dump-hashes', 'mysql-empty-password', 'mysql-enum', 'mysql-info', 'mysql-query', 'mysql-users', 'mysql-variables', 'mysql-vuln-cve2012-2122', 'nat-pmp-info', 'nat-pmp-mapport', 'nbd-info', 'nbns-interfaces', 'nbstat', 'ncp-enum-users', 'ncp-serverinfo', 'ndmp-fs-info', 'ndmp-version', 'nessus-brute', 'nessus-xmlrpc-brute', 'netbus-auth-bypass', 'netbus-brute', 'netbus-info', 'netbus-version', 'nexpose-brute', 'nfs-ls', 'nfs-showmount', 'nfs-statfs', 'nje-node-brute', 'nje-pass-brute', 'nntp-ntlm-info', 'nping-brute', 'nrpe-enum', 'ntp-info', 'ntp-monlist', 'omp2-brute', 'omp2-enum-targets', 'omron-info', 'openflow-info', 'openlookup-info', 'openvas-otp-brute', 'openwebnet-discovery', 'oracle-brute', 'oracle-brute-stealth', 'oracle-enum-users', 'oracle-sid-brute', 'oracle-tns-version', 'ovs-agent-version', 'p2p-conficker', 'path-mtu', 'pcanywhere-brute', 'pcworx-info', 'pgsql-brute', 'pjl-ready-message', 'pop3-brute', 'pop3-capabilities', 'pop3-ntlm-info', 'port-states', 'pptp-version', 'puppet-naivesigning', 'qconn-exec', 'qscan', 'quake1-info', 'quake3-info', 'quake3-master-getservers', 'rdp-enum-encryption', 'rdp-ntlm-info', 'rdp-vuln-ms12-020', 'realvnc-auth-bypass', 'redis-brute', 'redis-info', 'resolveall', 'reverse-index', 'rexec-brute', 'rfc868-time', 'riak-http-info', 'rlogin-brute', 'rmi-dumpregistry', 'rmi-vuln-classloader', 'rpc-grind', 'rpcap-brute', 'rpcap-info', 'rpcinfo', 'rsa-vuln-roca', 'rsync-brute', 'rsync-list-modules', 'rtsp-methods', 'rtsp-url-brute', 'rusers', 's7-info', 'samba-vuln-cve-2012-1182', 'servicetags', 'shodan-api', 'sip-brute', 'sip-call-spoof', 'sip-enum-users', 'sip-methods', 'skypev2-version', 'smb-brute', 'smb-double-pulsar-backdoor', 'smb-enum-domains', 'smb-enum-groups', 'smb-enum-processes', 'smb-enum-services', 'smb-enum-sessions', 'smb-enum-shares', 'smb-enum-users', 'smb-flood', 'smb-ls', 'smb-mbenum', 'smb-os-discovery', 'smb-print-text', 'smb-protocols', 'smb-psexec', 'smb-security-mode', 'smb-server-stats', 'smb-system-info', 'smb-vuln-conficker', 'smb-vuln-cve-2017-7494', 'smb-vuln-cve2009-3103', 'smb-vuln-ms06-025', 'smb-vuln-ms07-029', 'smb-vuln-ms08-067', 'smb-vuln-ms10-054', 'smb-vuln-ms10-061', 'smb-vuln-ms17-010', 'smb-vuln-regsvc-dos', 'smb-vuln-webexec', 'smb-webexec-exploit', 'smb2-capabilities', 'smb2-security-mode', 'smb2-time', 'smb2-vuln-uptime', 'smtp-brute', 'smtp-commands', 'smtp-enum-users', 'smtp-ntlm-info', 'smtp-open-relay', 'smtp-strangeport', 'smtp-vuln-cve2010-4344', 'smtp-vuln-cve2011-1720', 'smtp-vuln-cve2011-1764', 'sniffer-detect', 'snmp-brute', 'snmp-hh3c-logins', 'snmp-info', 'snmp-interfaces', 'snmp-ios-config', 'snmp-netstat', 'snmp-processes', 'snmp-sysdescr', 'snmp-win32-services', 'snmp-win32-shares', 'snmp-win32-software', 'snmp-win32-users', 'socks-auth-info', 'socks-brute', 'socks-open-proxy', 'ssh-auth-methods', 'ssh-brute', 'ssh-hostkey', 'ssh-publickey-acceptance', 'ssh-run', 'ssh2-enum-algos', 'sshv1', 'ssl-ccs-injection', 'ssl-cert', 'ssl-cert-intaddr', 'ssl-date', 'ssl-dh-params', 'ssl-enum-ciphers', 'ssl-heartbleed', 'ssl-known-key', 'ssl-poodle', 'sslv2', 'sslv2-drown', 'sstp-discover', 'stun-info', 'stun-version', 'stuxnet-detect', 'supermicro-ipmi-conf', 'svn-brute', 'targets-asn', 'targets-ipv6-map4to6', 'targets-ipv6-multicast-echo', 'targets-ipv6-multicast-invalid-dst', 'targets-ipv6-multicast-mld', 'targets-ipv6-multicast-slaac', 'targets-ipv6-wordlist', 'targets-sniffer', 'targets-traceroute', 'targets-xml', 'teamspeak2-version', 'telnet-brute', 'telnet-encryption', 'telnet-ntlm-info', 'tftp-enum', 'tls-alpn', 'tls-nextprotoneg', 'tls-ticketbleed', 'tn3270-screen', 'tor-consensus-checker', 'traceroute-geolocation', 'tso-brute', 'tso-enum', 'ubiquiti-discovery', 'unittest', 'unusual-port', 'upnp-info', 'uptime-agent-info', 'url-snarf', 'ventrilo-info', 'versant-info', 'vmauthd-brute', 'vmware-version', 'vnc-brute', 'vnc-info', 'vnc-title', 'voldemort-info', 'vtam-enum', 'vulners', 'vuze-dht-info', 'wdb-version', 'weblogic-t3-info', 'whois-domain', 'whois-ip', 'wsdd-discover', 'x11-access', 'xdmcp-discover', 'xmlrpc-methods', 'xmpp-brute', 'xmpp-info'] , self)
        completer.commaKeyPressed.connect(self.onCommaPressed)
        self.scripts_textbox.setCompleter(completer)

        self.form_layout.setWidget(2, QFormLayout.LabelRole, self.scripts_label)
        self.form_layout.setWidget(2, QFormLayout.FieldRole, self.scripts_textbox)


        self.main_layout.addLayout(self.form_layout)

        self.saveBtn = QPushButton("Save Configs & Exit")
        self.saveBtn.clicked.connect(self.saveConfigs)
        self.main_layout.addWidget(self.saveBtn)
        self.setLayout(self.main_layout)
    
    def saveConfigs(self):
        ports_range = self.port_textbox.text()
        self.nmap_configs['Scan Type'] = self.scans_combobox.currentText()
        self.nmap_configs['NSE Scripts'] = self.scripts_textbox.text()
        check_passed = False
        try:
            if 'top' in ports_range.lower():
                temp = int(ports_range.replace('top','')) 
                check_passed = True
            elif ',' in ports_range:
                temp = [int(i) if i != '' else None for i in ports_range.strip().split(',')]
                ports_range = ','.join([str(i) for i in temp])
                if temp[-1] == None:  
                    temp.pop()
                check_passed = True
            elif '-' in ports_range:
                temp = [int(i) for i in ports_range.split('-')]
                check_passed = True
            elif ports_range.strip().isdigit():
                check_passed = True
            elif ports_range == '':
                check_passed = True
            if check_passed != True:
                raise ValueError
            else:
                self.nmap_configs['Ports Range'] = ports_range
                self.close()
        except ValueError:
            QMessageBox(QMessageBox.Critical,"Error", f"Invalid Input Given to ports range", QMessageBox.Ok, self.main_window).exec_()


    def toolTip4Scans(self):
        scantype = self.scans_combobox.currentText().split()[0]
        if scantype == '(-sT)':
            self.scans_combobox.setToolTip('Complete 3-Way Handshake scan (TCP)')
        elif scantype == '(-sS)':
            self.scans_combobox.setToolTip('Stealthy SYN scan to avoid full session establishment (TCP)')
        elif scantype == '(-sA)':
            self.scans_combobox.setToolTip('ACK scan to detect stateful firewall (TCP)')
        elif scantype == '(-sU)':
            self.scans_combobox.setToolTip('Slower UDP scan for discovering open ports')
        elif scantype == '(-sV)':
            self.scans_combobox.setToolTip('Version detection scan (TCP)')
        elif scantype == '(-A)':
            self.scans_combobox.setToolTip('Aggressive scan - includes OS detection, version detection, script scanning, and traceroute')
    
    def onCommaPressed(self):
        current_text = self.scripts_textbox.text()
        if current_text:
            last_entry = current_text.split(",")[-1].strip()
            completer = self.scripts_textbox.completer()
            completer.setCompletionPrefix(last_entry)
            completer.complete()
        