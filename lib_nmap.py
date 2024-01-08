import os,sys,subprocess,shlex, xmltodict, json
from sharedfunctions import checkpass
from PyQt5.QtWidgets import QApplication
def get_nmap_path():
    """
    Returns the location path where nmap is installed
    by calling which nmap
    """
    os_type = sys.platform
    if os_type == 'win32':
        cmd = "where nmap"
    else:
        cmd = "which nmap"
    args = shlex.split(cmd)
    sub_proc = subprocess.Popen(args, stdout=subprocess.PIPE)

    try:
        output, errs = sub_proc.communicate(timeout=15)
    except Exception as e:
        print(e)
        sub_proc.kill()
    else:
        if os_type == 'win32':
            return output.decode('utf8').strip().replace("\\", "/")
        else:
            return output.decode('utf8').strip()


def nmapCmd(command, target, password=''):
    password = ''    
    nmaptool = get_nmap_path()
    command = f"{nmaptool} -oX - {command} {target}"
    sh_cmd = shlex.split(command)
    if (os.path.exists(nmaptool)):
        while(True):
            if sh_cmd[0] == 'sudo':
                sub_proc = subprocess.Popen(sh_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # Pass the password to the subprocess as input
                sub_proc.stdin.write(password + '\n')
                sub_proc.stdin.flush()
            else:
                sub_proc = subprocess.Popen(sh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            try:
                output, errs = sub_proc.communicate(timeout=None)
                if isinstance(errs,bytes) and b'root privileges' in errs:
                    print('exe')
                    sh_cmd.insert(0,"sudo")
                    sh_cmd.insert(1,"-S")
                    password = checkpass()
                    if password == '':
                        return 'sudo permissions required for this scan!'
                    elif password == 0:   # sudo token already active right now
                        password = ''

                    continue
                break
            except Exception as e:
                sub_proc.kill()
                raise (e)

        return xmltodict.parse(output)
        
    # sub_proc = subprocess.Popen(sh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # output, errs = sub_proc.communicate(timeout=None)
