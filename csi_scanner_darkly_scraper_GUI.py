from sharedfunctions import get_current_timestamp, auditme
import sys, os
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QMessageBox, QDesktopWidget, QLabel, QProgressDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QElapsedTimer
from sharedfunctions import auditme, get_current_timestamp, cases_folder, create_case_folder, ChromeThread, csitoolsinit
import argparse

csitoolname = "CSI Scanner Darkly Scraper GUI"
case = None
case_directory = None
username = None

parser = argparse.ArgumentParser(description=f'{csitoolname} usage: csi_adult_user_search --case "CaseName" --user "UserName"')
parser.add_argument('--case', type=str, help="Path to the case directory")
parser.add_argument('--user', type=str, help="username to search")
args = parser.parse_args()
config_file = "agency_data.json"
case = args.case



# Call csitoolsinit and capture the returned values
(case_name, investigator_name, case_type, case_priority, case_classification, case_date, cases_folder,
 case_directory, timestamp, notes_file_path, icon) = csitoolsinit(case, csitoolname)

evidence_dir = os.path.join(case_directory, f"Evidence/Online/Domain")    # Change "Folder" to the appropriate evidence sub-folder
os.makedirs(evidence_dir, exist_ok=True)



class csi_scanner_darkly_scraperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSI Scanner Darkly Scraper GUI")
        self.resize(800, 600)
        self.setWindowIcon(QIcon(icon))
        self.center_window()
        self.setup_ui()

    def center_window(self):
        # Get the application window's dimensions
        window_rect = self.frameGeometry()
        # Get the screen's center point
        center_point = QDesktopWidget().availableGeometry().center()
        # Move the window's center to the screen's center
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())

    def setup_ui(self):
        layout = QVBoxLayout()
        d_label = QLabel("Enter the domain you want to scrape and click 'Scrape'")
        d_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(d_label)
        url_layout = QHBoxLayout()
        self.url_entry = QLineEdit()
        url_layout.addWidget(self.url_entry)

        self.execute_button = QPushButton("Scrape")
        self.execute_button.clicked.connect(self.execute_csi_scanner_darkly_scraper)
        url_layout.addWidget(self.execute_button)
        self.openscreen = QPushButton("Screenshot")
        # self.openscreen.clicked.connect(self.openscreen)
        url_layout.addWidget(self.openscreen)        
        self.openurl = QPushButton("Broswer")
        self.openurl.clicked.connect(self.open_with_chrome)
        url_layout.addWidget(self.openurl)

        layout.addLayout(url_layout)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def execute_csi_scanner_darkly_scraper(self):
        self.output_text.append(f"Processing...")
        QApplication.processEvents()  # Update the GUI before executing the operation
        url = self.url_entry.text()
        
        # Check if the URL is empty
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL.")
            return

        url = url.replace(" ", "")  # Remove all spaces from the URL

        # Start the elapsed timer
        timer = QElapsedTimer()
        timer.start()

        # Get the current working directory
        current_directory = os.getcwd()
        
        # Construct the path to the executable file
        executable_path = os.path.join(current_directory, "csi_scanner_darkly_scraper")
        
        # Verify the path is correct
        if not os.path.exists(executable_path):
            print(f"Error: Could not find csi_scanner_darkly_scraper at path: {executable_path}")
            sys.exit(1)
        
        # Execute the csi_scanner_darkly_scraper.py script with the provided URL
        command = [executable_path, "--case", case, "-edir", "Domain", "-d", url, "-o" , "n"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            self.output_text.append(output)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Error executing csi_scanner_darkly_scraper: {e.stderr}")

        elapsed_time = timer.elapsed()
        self.output_text.append(f"Elapsed Time: {elapsed_time / 1000:.2f} seconds")

    def open_with_chrome(self, url):
        print(evidence_dir)
        url = self.url_entry.text()
        thread = ChromeThread(url, evidence_dir)
        thread.finished.connect(app.quit)
        thread.start()   
    
        timestamp = get_current_timestamp()
        auditme(case_directory, f"{timestamp}: Adult User Search - Opening {url} in Chrome")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    csi_scanner_darkly_scraper_gui = csi_scanner_darkly_scraperGUI()
    csi_scanner_darkly_scraper_gui.show()
    sys.exit(app.exec_())

