from __future__ import annotations
from obswebsocket import obsws, requests
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, AudioFileClip
from dataclasses import dataclass

#silent movepy logs
import logging
logging.getLogger("moviepy").setLevel(logging.CRITICAL)

import subprocess
import pyautogui
import psutil
import shutil
import time
import os

class TooManyGoogleChromes(Exception): pass

class TooLessGoogleChromes(Exception): pass

@dataclass
class end_card_config: 
    image_path: str
    audio_path: str
    length: float
    background: tuple = (255, 255, 255)
    logo_position: tuple = (30, "center")


class obs_interface: 
    port: int = 4444
    password: str = "password"
    host: str = "localhost"
    process_name: str = "obs64.exe"
    file_type : str = ".mkv"
    chrome_process_title: str = "- Google Chrome"

    #defaults
    
    def __init__(self, verbose : bool = False, watermark_path: str = None, end_card_config: end_card_config = None): 
        self.client: obsws = None 
        self.clean: bool = False
        self.started_process: bool = False
        self.output_path : str = None
        self.verbose = verbose
        self.watermark_path : str = watermark_path or None
        self.end_card_config : end_card_config = end_card_config or None
        self.recording: bool = False

        self._start_server()
        self._connect()


    def __del__(self, ): 
        print("[OBS] Destructor called...")
        if not self.clean: self.clean_up() 


    #publics
    def clean_up(self, ) -> None: 
        if self.verbose: print("[OBS] Cleaning up...")

        if self.recording: self.stop_recording()

        time.sleep(1)
        if self.client: self._disconnect()

        time.sleep(2)
        if self.started_process: self._stop_server()
        self.clean = True

    def start_recording(self, filename: str = None, watermark_path : str = None, end_card_config: end_card_config = None) -> None: 
        if self.verbose: print("[OBS] Starting recording...")

        if filename: 
            self.set_output_path(filename)

        if watermark_path: self.watermark_path : str = watermark_path
        if end_card_config: self.end_card_config : end_card_config = end_card_config


        if len(pyautogui.getWindowsWithTitle(obs_interface.chrome_process_title)) == 0: raise TooLessGoogleChromes()
        if len(pyautogui.getWindowsWithTitle(obs_interface.chrome_process_title)) > 1: raise TooManyGoogleChromes()

        chrome_window = pyautogui.getWindowsWithTitle(obs_interface.chrome_process_title)[0]
        height, width = chrome_window.height-10, chrome_window.width-20
        

        req = requests.SetVideoSettings(baseWidth=width, outputWidth=width, baseHeight=height, outputHeight=height) 
        self.client.call(req)
        time.sleep(.5)
        self.recording = True

        self.client.call(requests.StartRecord())
        time.sleep(1)

    def stop_recording(self, filename: str = None, watermark_path : str = None, end_card_config: end_card_config = None) -> None: 
        if filename: 
            self.set_output_path(filename)

        if watermark_path: self.watermark_path : str = watermark_path
        if end_card_config: self.end_card_config : end_card_config = end_card_config

        if not self.recording: return

        time.sleep(2)

        req = requests.StopRecord()
        self.client.call(req)

        self.recording = False
        if self.verbose: print("[OBS] Stopping recording...")

        for _ in range(3): 
            time.sleep(2)
            try: 
                path = req.datain.get("outputPath", None)
                if not path: continue
                shutil.move(path, self.output_path)
                break
            except PermissionError: pass
            except Exception as e: raise e

        if self.verbose: print("[OBS] Recording stopped...")

        if self.watermark_path: 
            if self.verbose: print("[OBS] Adding watermark...")
            for _ in range(3): 
                time.sleep(3)
                try: 
                    self._add_watermark(video_path=self.output_path, watermark_path=self.watermark_path)
                    break
                except PermissionError: pass
                except Exception as e: raise e
            
        if self.end_card_config:
            if self.verbose: print("[OBS] Adding end card...") 
            for _ in range(3): 
                time.sleep(3)
                try: 
                    self._add_end_card(video_path=self.output_path, end_card_config=end_card_config)
                    break
                except PermissionError: pass
                except Exception as e: raise e

    def set_output_path(self, path: str):
        if not path.endswith(obs_interface.file_type): path += obs_interface.file_type
        self.output_path = path

    def set_watermark_path(self, path: str): 
        self.watermark_path : str = path

    def set_end_card_config(self, end_card_config: end_card_config): 
        self.end_card_config : end_card_config = end_card_config
    

    #privates
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

        if self.verbose: print(f"[OBS] Trying to connect to {host}:{port} with {password}...")    
        self.client = obsws(host, port, password, legacy=False)
        self.client.connect()
        if self.verbose: print(f"[OBS] Trying to connect to {host}:{port} with {password}... done")    
        
    def _disconnect(self,) -> None: 
        if self.verbose: print("[OBS] Disconnecting server...")
        self.client.disconnect()
        if self.verbose: print("[OBS] Disconnecting server... done")

    def _add_watermark(self, video_path: str, watermark_path: str) -> None: 
        new_path = os.path.splitext(video_path)[0] + ".mp4"
        video = VideoFileClip(video_path)
        logo = ImageClip(watermark_path)
        height = logo.h
        logo = logo.set_duration(video.duration).resize(height=height).margin(bottom=30, right=20, opacity=0).set_pos(("right", "bottom"))

        final = CompositeVideoClip([video, logo])
        final.write_videofile(new_path, codec="libx264")
        os.remove(video_path)

    def _add_end_card(self, video_path: str, end_card_config: end_card_config) -> None: 
        new_path = os.path.splitext(video_path)[0] + "_with_endcard.mp4"
        
        video = VideoFileClip(video_path)
          
        logo = ImageClip(end_card_config.image_path).set_duration(end_card_config.length)
        background = ColorClip(size=video.size, color=end_card_config.background, duration=end_card_config.length)
        logo = CompositeVideoClip([background, logo.set_pos(end_card_config.logo_position)])

        # Load and check the end card audio
        audio : AudioFileClip = AudioFileClip(end_card_config.audio_path)
        
        if audio.duration < end_card_config.length:
            raise ValueError("End Card audio is too short")
        
        audio = audio.subclip(0, end_card_config.length)
        logo = logo.set_audio(audio)

        final = concatenate_videoclips([video, logo])
        final.write_videofile(new_path, codec="libx264")

        os.remove(video_path)
        os.rename(new_path, video_path)



if __name__ == "__main__": 
    obs_client = obs_interface(verbose=True, )

    watermark_path = "C:\/Users\/gerde\/Desktop\/Schnell Gezeigt\/Logo\/Quer-klein.png"
    image_path = watermark_path
    audio_path = "C:/Users/gerde/Desktop/Schnell Gezeigt/outro.mp3"
    length = 10.0

    obs_client.start_recording(filename="C:/Users/gerde/Desktop/test2")
    
    time.sleep(5)

    obs_client.stop_recording(watermark_path=watermark_path, end_card_config=end_card_config(image_path=image_path, audio_path=audio_path, length=length))
    obs_client.clean_up()