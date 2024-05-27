# obs-interface

A simple Python module to record a Chrome window with OBS

```
>>> from obs_interface import obs

>>> obs_client = obs()
>>> obs_client.start_recording(filename="C:/Users/gerde/Desktop/test.mkv")

>>> time.sleep(10)

>>> obs_client.stop_recording()
>>> obs_client.clean_up()

```
