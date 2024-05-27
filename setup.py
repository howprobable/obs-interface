from setuptools import setup, find_packages

setup(
    name='obs_interface',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        "obs-websocket-py",
        "pyautogui",
        "psutil",
    ],
    description='A simple Python module to record a Chrome window with OBS',
    author='Jannik Eggert',
    author_email='jannikeggert@gmail.com',
    url='https://github.com/howprobable/obs_interface',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
