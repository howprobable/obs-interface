from __future__ import annotations
from obswebsocket import obsws, requests

import subprocess
import pyautogui
import psutil
import shutil
import time
import os

class TooManyGoogleChromes(Exception): pass

class TooLessGoogleChromes(Exception): pass

class obs_interface: 
    port: int = 4444
    password: str = "password"
    host: str = "localhost"
    process_name: str = "obs64.exe"
    file_type : str = ".mkv"
    chrome_process_title: str = "- Google Chrome"

    #defaults
    
    def __init__(self, verbose : bool = False): 
        self.client: obsws = None 
        self.clean: bool = False
        self.started_process: bool = False
        self.output_path : str = None
        self.verbose = verbose

        self._start_server()
        self._connect()


    def __del__(self, ): 
        if not self.clean: self.clean_up() 


    #publics
    def clean_up(self, ) -> None: 
        if self.client: self._disconnect() 
        time.sleep(0.1)
        if self.started_process: self._stop_server() 
    
        self.clean = True

    def start_recording(self, filename: str = None) -> None: 
        if filename: 
            if not filename.endswith(obs_interface.file_type): filename += obs_interface.file_type
            self.output_path = filename

        if len(pyautogui.getWindowsWithTitle(obs_interface.chrome_process_title)) == 0: raise TooLessGoogleChromes()
        if len(pyautogui.getWindowsWithTitle(obs_interface.chrome_process_title)) > 1: raise TooManyGoogleChromes()

        chrome_window = pyautogui.getWindowsWithTitle(obs_interface.chrome_process_title)[0]
        height, width = chrome_window.height-10, chrome_window.width-20

        req = requests.SetVideoSettings(baseWidth=width, outputWidth=width, baseHeight=height, outputHeight=height) 
        self.client.call(req)
        time.sleep(.5)
        self.client.call(requests.StartRecord())
        time.sleep(1)

    def stop_recording(self, filename: str = None) -> None: 
        if filename: 
            if not filename.endswith(obs_interface.file_type): filename += obs_interface.file_type
            self.output_path = filename

        time.sleep(2)

        req = requests.StopRecord()
        self.client.call(req)

        time.sleep(1)

        path = req.datain["outputPath"]
        shutil.move(path, self.output_path)


    #privates
    def _set_output_path(self, path: str):
        if not path.endswith(obs_interface.file_type): path += obs_interface.file_type
        self.output_path = path

    def _set_window(self, window_name: str): 
        self.window_name = window_name

    def _start_server(self, path: str = None, port: int= None, password: str=None) -> None: 
        path = path or "C:\Program Files\obs-studio\\bin\\64bit\obs64.exe"
        port = port or obs_interface.port
        password = password or obs_interface.password

        obs_running = any(obs_interface.process_name in p.name() for p in psutil.process_iter())
        params = [f"--websocket_port={port}", f"--websocket_password={password}", "--disable-shutdown-check"]
        cwd = os.path.dirname(path)

        if not obs_running: 
            if self.verbose: print("[OBS] Starting obs_interface....")
            subprocess.Popen([path]+params, close_fds=True, cwd=cwd)
            if self.verbose: print("[OBS] Started obs_interface.... waiting...")
            time.sleep(6)
            if self.verbose: print("[OBS] Starting obs_interface.... done")
            self.started_process = True
        else: 
            self.started_process = False
            if self.verbose: print("[OBS] Obs already running...")

    def _stop_server(self, process_name: str = None) -> None:
        process_name = process_name or obs_interface.process_name
        if self.verbose: print("[OBS] Stopping obs_interface...")

        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == process_name:
                proc.terminate()  # Gracefully terminate the process
                proc.wait()  # Wait for the process to actually terminate
                if self.verbose: print("[OBS] Stopping obs_interface... done")
                return
            
        if self.verbose: print("[OBS] Stopping obs_interface... process not found.")

    def _connect(self, host: str = None, port: int = None, password: str = None) -> None:
        host = host or obs_interface.host
        port = port or obs_interface.port
        password = password or obs_interface.password

        print(f"Trying to connect to {host}:{port} with {password}...")    
        self.client = obsws(host, port, password, legacy=False)
        self.client.connect()
        print(f"Trying to connect to {host}:{port} with {password}... done")    
        
    def _disconnect(self,) -> None: 
        if self.verbose: print("[OBS] Disconnecting server...")
        self.client.disconnect() 
        if self.verbose: print("[OBS] Disconnecting server... done")


if __name__ == "__main__": 
    obs_client = obs_interface()
    obs_client.start_recording(filename="C:/Users/gerde/Desktop/test.mkv")

    time.sleep(10)

    obs_client.stop_recording()
    obs_client.clean_up()