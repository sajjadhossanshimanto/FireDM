![PyPI - Format](https://img.shields.io/pypi/format/pyidm?color=grey&label=PyPI) [![Downloads](https://pepy.tech/badge/pyidm)](https://pepy.tech/project/pyidm)

![GitHub All Releases](https://img.shields.io/github/downloads/pyidm/pyidm/total?color=blue&label=GitHub%20Releases)

![GitHub issues](https://img.shields.io/github/issues-raw/pyidm/pyidm?color=blue) - ![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/pyidm/pyidm?color=blue)


PyIDM is a python open source (Internet Download Manager) 
with multi-connections, high speed engine, 
it downloads general files and videos from youtube and tons of other streaming websites . <br>
Developed in Python, based on "LibCurl", and "youtube_dl".

![screenshot](https://user-images.githubusercontent.com/58998813/92564079-e4fcee00-f278-11ea-83e1-9a272bc06b0f.png)

---
**Features**:
* High download speeds "based on LibCurl" -
  [See Speed test of: aria2 vs PyIDM](https://user-images.githubusercontent.com/58998813/74993622-361bd080-5454-11ea-8bda-173bfcf16349.gif)
* Multi-connection downloading "Multithreading"
* Automatic file segmentation.
* Resume uncompleted downloads, and Refresh expired urls.
* Support for Youtube, and a lot of stream websites "using youtube-dl to fetch info and libcurl to download data".
* download entire video playlist or selected videos.
* download fragmented video streams, and encrypted/nonencrypted HLS media streams.
* watch videos while downloading* "some videos will have no audio until
  finish downloading".
* download video subtitles.
* write video metadata to downloaded files.
* check for application updates.
* Scheduling downloads
* Re-using existing connection to remote server.
* Clipboard Monitor.
* proxy support (http, https, socks4, and socks5).
* user/pass authentication, referee link, use cookies, video thumbnail, subtitles, MD5 and SHA256 checksums
* user can control a lot of options:
    - select theme.
    - set proxy.
    - Speed limit.
    - Max. Concurrent downloads.
    - Max. connections per download.

---
# How to use PyIDM:
Refer to user guide at https://github.com/pyIDM/PyIDM/blob/master/docs/user_guide.md

----------------------
# How to install PyIDM?
You have 3 options to run PyIDM on your operating system:

1. **Windows portable version**:  
   Latest Windows portable version available
   [here](https://github.com/pyIDM/PyIDM/releases/latest).  
   unzip, and run from PyIDM.exe, no installation required.

2. **PyPi**:<br>
    `python -m pip install pyidm --upgrade --no-cache`
    
    then you can run application from Terminal by:  
    `python -m pyidm`          note pyidm name in small letters

    or just  
    `pyidm` an executable "i.e. pyidm.exe on windows" will be
    located at "python/scripts", if it doesn't work append
    "python/scripts" folder to PATH.


3. **run from github source code**:<br>
PyIDM is a python app. so, it can run on any platform that can run python, 
To run from source, you have to have a python installed, "supported python versions is 3.6, 3.7, and 3.8", then download or clone this repository, and run PyIDM.py (it will install the other required python packages automatically if missing)
if PyIDM failed to install required packages, you should install it manually, refer to "Dependencies" section below.

4. **Build PyIDM yourself**:
   -  get the source code from github: (recommended for latest updated
      version, also shallow clone is preferred)  
      `git clone --depth 1 https://github.com/pyIDM/PyIDM.git`

   - or get the source code from PyPi:  
   navigate to https://pypi.org/project/pyIDM/#files and download a tar
   ball, example file name "pyIDM-2020.3.22.tar.gz", then extract it

   - open your terminal or command prompt and navigate to pyidm folder then type below command  
        `python setup.py install`

   - run PyIDM from Terminal by typing:  
        `python -m pyidm`     or  just `pyidm`

5. **Examples:**

    -**Linux ubuntu:**

    download source (shallow clone is preferred):  
    `git clone --depth 1 https://github.com/pyIDM/PyIDM.git`

    install dependencies:  
    ```
    sudo apt install ffmpeg fonts-symbola libcurl4-openssl-dev
    libssl-dev python3-pip python3-pil python3-pil.imagetk python3-tk
    ```

    install PyIDM:
    `python3 setup.py install --user`

    run PyIDM: `python3 -m pyidm`


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
- [youtube_dl](https://github.com/ytdl-org/youtube-dl): famous youtube downloader, limited use for meta information extraction only but videos are downloaded using pycurl
- [certifi](https://github.com/certifi/python-certifi): required by 'pycurl' for validating the trustworthiness of SSL certificates,
- [plyer](https://github.com/kivy/plyer): for systray area notification.


** please read notes below


PyIDM application will do its best to install missing packages automatically once you run it. or you can install required packages manually using:

```
pip install -r requirements.txt
```
or
```
python -m pip install --user --upgrade certifi plyer youtube_dl pycurl pillow pystray awesometkinter
```



---

**more screenshots**

![Main_tab](https://user-images.githubusercontent.com/58998813/92562020-939f2f80-f275-11ea-94ea-fe41c9c72abc.png)
![sett_tab](https://user-images.githubusercontent.com/58998813/92562130-bfbab080-f275-11ea-990d-c869522ecbaa.png)


---
# Why another download manager?:
Originally, I made this project to help myself download some youtube
videos, then decided to share it thinking it might be useful for someone
else, so please don't put your fire on me if you find a mistake in code
or stupid approach to solve a problem, or an ugly gui design, instead
try to fix it (this is the soul of open source software, it is open for
everyone to participate and improve).

what is the benefit of open source, compared to
closed-source/Proprietary software if both are free?  
I believe that, **"if the product is free, then you are the product"**,
most free closed-source software collect data about you, some of them
are toxic and plant trojans and spy-wares in your system, with open
source, nothing hidden, and source code exposed to thousands of
programmers, no one can play dirty games.


Need to mention that, during working on this project I found a lot of
amazing open source "download managers" projects, which are more
professional than this one, and this project is never made to compete
with other download managers, it is just a "hopefully useful" addition.



-----------------------------------------------------------------------------------------------------------------------------------------------------------------

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
1- by testing the application and opening
[new issue](https://github.com/pyIDM/PyIDM/issues/new) for bug
reporting, feature request, or suggestions.  
2- check
[developer guidelines](https://github.com/pyIDM/PyIDM/blob/master/docs/developer_guide.md).  
3- check
[todo list](https://github.com/pyIDM/PyIDM/blob/master/todo.md).  
4- check open issues, see if you can help.  
5- fork this repo and pull request

<br><br>

---

# Some recent articles/reviews on this project*:
- [ghacks](https://www.ghacks.net/2020/08/13/pyidm-is-an-open-source-download-manager-that-can-download-videos-and-playlists/)
- [softpedia](https://www.softpedia.com/get/Internet/Download-Managers/PyIDM.shtml)

  *help edit this list by writing a comment in
  [this issue](https://github.com/pyIDM/PyIDM/issues/136)

---

# Feedback:
your feedback is most welcomed by filling a
[new issue](https://github.com/pyIDM/PyIDM/issues/new)  
or email to: info.pyidm@gmail.com <br>

Author:  
Mahmoud Elshahat  
2019-2020


---