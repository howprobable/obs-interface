from __future__ import annotations
from obswebsocket import obsws, requests
from typing import Any, Optional
from py_helpers import Rectangle

import subprocess
import psutil
import time
import os

class obs: 
    port: int = 4444
    password: str = "password"
    host: str = "localhost"
    process_name: str = "obs64.exe"

    #defaults
    
    def __init__(self, connect: bool = True): 
        self.client: obsws = None 
        self.clean: bool = False
        self.started_process: bool = False

        if connect: 
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

    def start_recording(self, filename: str = None, window_name: str = None) -> None:  
        print(self.client.call(requests.GetInputList()))
        print("---")
        print(self.client.call(requests.GetOutputList()))
        print("---")
        print(self.client.call(requests.GetOutputList()).datain["outputs"])
        print("---")
        print(self.client.call(requests.GetOutputSettings(outputName="simple_file_output")))
        print("---")
        print(self.client.call(requests.SetOutputSettings(
            outputName="simple_file_output", 
            outputSettings={
                'path': 'C:/Users/gerde/Desktop/Film.mkv'
            }
        )))
        print("---")
        print(self.client.call(requests.GetOutputSettings(outputName="simple_file_output")))
        print("---")

        #Set output here to outputactive 
        #https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#createinput

        #See if it writes to file

        #See if one can set the window either by .exe or by coords
        #


    def stop_recording(self, ) -> None: 
        self.client.call(requests.StopRecord())

    #privates
    def _set_output_path(self, path: str):
        pass

    def _set_window(self, window_name: str): 
        pass

    def _start_server(self, path: str = None, port: int= None, password: str=None) -> None: 
        path = path or "C:\Program Files\obs-studio\\bin\\64bit\obs64.exe"
        port = port or obs.port
        password = password or obs.password

        obs_running = any(obs.process_name in p.name() for p in psutil.process_iter())
        params = [f"--websocket_port={port}", f"--websocket_password={password}", "--disable-shutdown-check"]
        cwd = os.path.dirname(path)

        if not obs_running: 
            print("Starting Obs....")
            subprocess.Popen([path]+params, close_fds=True, cwd=cwd)
            print("Started Obs.... waiting...")
            time.sleep(6)
            print("Starting Obs.... done")
            self.started_process = True
        else: 
            self.started_process = False
            print("Obs already running...")

    def _stop_server(self, process_name: str = None) -> None:
        process_name = process_name or obs.process_name
        print("Stopping Obs...")

        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == process_name:
                proc.terminate()  # Gracefully terminate the process
                proc.wait()  # Wait for the process to actually terminate
                print("Stopping Obs... done")
                return
            
        print("Stopping Obs... process not found.")

    def _connect(self, host: str = None, port: int = None, password: str = None) -> None:
        host = host or obs.host
        port = port or obs.port
        password = password or obs.password

        print(f"Trying to connect to {host}:{port} with {password}...")    
        self.client = obsws(host, port, password, legacy=False)
        self.client.connect()
        print(f"Trying to connect to {host}:{port} with {password}... done")    
        
    def _disconnect(self,) -> None: 
        print("Disconnecting server...")
        self.client.disconnect() 
        print("Disconnecting server... done")


if __name__ == "__main__": 
    obs_client = obs()
    obs_client.start_recording()

    # obs_client.clean_up()