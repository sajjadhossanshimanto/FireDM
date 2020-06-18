![PyPI - Format](https://img.shields.io/pypi/format/pyidm?color=grey&label=PyPI) [![Downloads](https://pepy.tech/badge/pyidm)](https://pepy.tech/project/pyidm)

![GitHub All Releases](https://img.shields.io/github/downloads/pyidm/pyidm/total?color=blue&label=GitHub%20Releases)

![GitHub issues](https://img.shields.io/github/issues-raw/pyidm/pyidm?color=blue) - ![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/pyidm/pyidm?color=blue)


PyIDM is a python open source (Internet Download Manager) 
with multi-connections, high speed engine, 
it downloads general files and videos from youtube and tons of other streaming websites . <br>
Developed in Python, based on "pyCuRL/libcurl", "youtube_dl", and "PySimpleGUI"

![main animation](https://user-images.githubusercontent.com/58998813/77242050-2d5d1c80-6c03-11ea-8151-b85a897ff9fb.gif)

---
**Features**:
* High download speeds "based on libcurl"   -  [See Speed test of: aria2 vs PyIDM](https://user-images.githubusercontent.com/58998813/74993622-361bd080-5454-11ea-8bda-173bfcf16349.gif).
* Multi-connection downloading "Multithreading"
* Automatic file segmentation.
* Resume uncompleted downloads, and Refresh expired urls.
* Support for Youtube, and a lot of stream websites "using youtube-dl to fetch info and libcurl to download data".
* download entire video playlist or selected videos.
* download fragmented video streams, and encrypted/nonencrypted HLS media streams.
* watch videos while downloading*   "some videos will have no audio until finish downloading"
* check for application updates.
* Scheduling downloads
* Re-using existing connection to remote server.
* Clipboard Monitor.
* Simple GUI interface with 140 themes available.
* proxy support (http, https, socks4, and socks5).
* user/pass authentication, referee link, use cookies, video thumbnail, subtitles, MD5 and SHA256 checksums
* user can control a lot of options:
    - select theme.
    - set proxy.
    - Speed limit.
    - Max. Concurrent downloads.
    - Max. connections per download.


---
# How to install PyIDM?
You have 3 options to run PyIDM on your operating system:

1. **Windows portable version**:<br>
Latest Windows portable version available [here](https://github.com/pyIDM/PyIDM/releases/latest). <br>
unzip, and run from PyIDM.exe, no installation required.

2. **PyPi**:<br>
    `python -m pip install pyidm --upgrade --no-cache`
    
    then you can run application from Terminal by:<br>
    `python -m pyidm`          note pyidm name in small letters 

    or just<br>
    `pyidm`        an exexutable "i.e. pyidm.exe on windows" will be located at "python/scripts", if it doesn't work append "python/scripts" folder to PATH. 


3. **run from github source code**:<br>
PyIDM is a python app. so, it can run on any platform that can run python, 
To run from source, you have to have a python installed, "supported python versions is 3.6, 3.7, and 3.8", then download or clone this repository, and run PyIDM.py (it will install the other required python packages automatically if missing)
if PyIDM failed to install required packages, you should install it manually, refer to "Dependencies" section below.

4. **Build PyIDM yourself**:
    - get the source code from github:<br>
        `git clone https://github.com/pyIDM/PyIDM.git` <br>

    - or get the source code from PyPi: <br>
        navigate to https://pypi.org/project/pyIDM/#files and download a tar ball, example file name "pyIDM-2020.3.22.tar.gz", then extract it

    - open your terminal or command prompt and navigate to pyidm folder then type below command <br>
        `python setup.py install`

    - run PyIDM from Terminal by typing:<br>
        `python -m pyidm`     or  just `pyidm`   


**important note on Tkinter for mac users**:<br>
- as mentioned in "python.org" the Apple-supplied Tcl/Tk 8.5 has serious bugs that can cause application crashes. If you wish to use Tkinter, do not use the Apple-supplied Pythons. Instead, install and use a newer version of Python from python.org or a third-party distributor that supplies or links with a newer version of Tcl/Tk. <br>
refer to [issue #113](https://github.com/pyIDM/PyIDM/issues/113)


---

# Dependencies:
below are the requirements to run from source:
- Python 3.6+: tested with python 3.6 on windows, and 3.7, 3.8 on linux
- [ffmpeg](https://www.ffmpeg.org/) : for merging audio with youtube DASH videos "it will be installed automatically on windows"

Required python packages: 
- [pycurl](http://pycurl.io/docs/latest/index.html): is a Python interface to libcurl / curl as our download engine,
- [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI): a beautiful gui builder, 
- [youtube_dl](https://github.com/ytdl-org/youtube-dl): famous youtube downloader, limited use for meta information extraction only but videos are downloaded using pycurl 
- [certifi](https://github.com/certifi/python-certifi): required by 'pycurl' for validating the trustworthiness of SSL certificates,
- [pyperclip](https://github.com/asweigart/pyperclip): A cross-platform clipboard module for monitoring url copied to clipboard, requires "xclip or xsel to be available on linux"
- [plyer](https://github.com/kivy/plyer): for systray area notification.


** please read notes below


PyIDM application will do its best to install missing packages automatically once you run it. or you can install required packages manually using:

```
pip install -r requirements.txt
```
or
```
python -m pip install --user --upgrade certifi PySimpleGUI pyperclip plyer youtube_dl pycurl pillow
```



---

**more snapshots**

![Main_tab](https://user-images.githubusercontent.com/58998813/77241027-b40afd00-6bf5-11ea-8854-c181d1f9c957.PNG)
![d_window](https://user-images.githubusercontent.com/58998813/77240959-ec5e0b80-6bf4-11ea-819e-83bd7bd13249.PNG)
![downloads_tab](https://user-images.githubusercontent.com/58998813/78214514-bb63bd80-74b5-11ea-8d13-e3fce537394d.PNG)
![playlist_window](https://user-images.githubusercontent.com/58998813/77242155-12d77300-6c04-11ea-9e57-e781e67aaa3b.PNG)
![setting_tab1](https://user-images.githubusercontent.com/58998813/78214405-75a6f500-74b5-11ea-838f-c7ad95b722ed.PNG)
![setting_tab2](https://user-images.githubusercontent.com/58998813/78214411-793a7c00-74b5-11ea-9179-68902d5cffff.PNG)
![setting_tab3](https://user-images.githubusercontent.com/58998813/78214419-7c356c80-74b5-11ea-869f-1560cf5e2f78.PNG)
![Multi_window](https://user-images.githubusercontent.com/37757246/71418548-a2a46a00-2673-11ea-8101-c95d29b6a0e4.png)


[view all screenshots with different themes](https://github.com/pyIDM/PyIDM/issues/13)


---
# Why another download manager?:
With all free and paid download manager why someone may need another one?
I believe in one term, **"if the product is free, then you are the product"**, most (if not all) free applications collect data about you, some of them are toxic and plant trojans and spyware in your system, then I decided to make my own download manager based on python with 👉 **"--GUI--"** relies only on open source tools and libraries, nothing hidden, with source code exposed to thousands of programmers, no one can play dirty games here 😉.

why not just use youtube-dl from command line? the answer is multithreading / multiconnection is not available in youtube-dl, most of the time streaming servers like youtube limit speed per connection and you end up with slow download speeds.

---

### note for pycurl: <br>
for windows users:
normal pip install i.e `python -m pip install pycurl` might fail on windows because you need to build libcurl on your system first which is a headache. 
your best choice if pip fail is to download exe file for pycurl from its official download [link](https://dl.bintray.com/pycurl/pycurl/), find the file that match your windows system and python version installed on your system, last checked on 12-06-2020, found available files for almost all Python versions upto version 3.8

example: if you have python 3.6 installed on windows 32bit, you should download "pycurl-7.43.0.2.win32-py3.6.exe" file and install it, 
another example: if you have python 3.7 running on windows 64 bit, you should choose and download "pycurl-7.43.0.3.win-amd64-py3.7.exe" file

other download options include a wheel, zip file, or even a windows installer

for linux users:
there is no issues, since most linux distros have curl preinstalled, so pycurl will link with libcurl library to get built with no issues, checked with python versions 3.6, 3.7, and 3.8 working with no problems.
<br>


### note for [Youtube-dl](https://github.com/ytdl-org/youtube-dl): <br>
youtube website changes frequently, if this application failed to retrieve video/playlist data
you should update youtube-dl module thru PyIDM setting tab or manually by
```
python -m pip install youtube_dl --upgrade
```

### note for pyperclip: <br>
Pyperclip is a cross-platform Python module for copy and paste clipboard functions. it is being used if you want to monitor clipboard for files urls and it will be processed automatically by the application.
On Linux, this module makes use of the xclip or xsel commands, which should come with the os. Otherwise run "sudo apt-get install xclip" on Debian like or "sudo pacman -S xclip" on archlinux

---

### Windows binaries: <br>
a standalone frozen version prepared by py2exe or cx_freeze is available at: [latest version](https://github.com/pyIDM/PyIDM/releases/latest) <br>
for all available build versions you can check https://github.com/pyIDM/PyIDM/releases



---

<br><br>

# Versions change log:
ChangeLog.txt is included in source code.




<br><br>

---
# How to contribute to this project:
1- by testing the application and opening [new issue](https://github.com/pyIDM/PyIDM/issues/new) for bug reporting, feature request, or suggestions. <br>
2- fork this repo and pull request

<br><br>

---


# Feedback:
your feedback is most welcomed by filling a [new issue](https://github.com/pyIDM/PyIDM/issues/new) <br>
or email me at: info.pyidm@gmail.com <br>

Author, <br>
Mahmoud Elshahat, <br>
2019-2020

---