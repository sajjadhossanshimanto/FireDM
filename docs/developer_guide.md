### Developer Guide

This Guide for developer who want to contribute or understand how this project work, feel free to improve this guide anytime


### Purpose of this project:
Basically, I made this project to help myself download some youtube
videos, then decided to share it thinking it might be useful for someone
else, so please don't put your fire on me if you find a mistake in code
or stupid approach to solve a problem, or an ugly gui design, instead
try to help fix it.  
Unfortunately, I didn't document the code well enough and it will take a
lot of effort to make a proper comments inside the code.  
This project is never made to compete with other download managers, it
is just a "hopefully useful" tool.


---


### Current project logic:
Generally PyIDM is using Libcurl as a download engine via threads to
achieve multi-connections, for videos, youtube-dl is our player, where
its sole role is to extract video information from a specific url "No
other duties for youtube-dl".  
FFMPEG will be used for post processing e.g. mux audio and video, merge
HLS video segments into one video file, and other useful media
manipulation.  
A plan in progress to implement "MVC" design, currently done basic
controller in controller.py and Model in observables.py, which will give
us a good chance to make different gui designs without affecting
application logic currently there is cmdview.py which run interactively
in terminal which depend on controller


---


### Files:

- **PyIDM.py:** main file, it will start "clipboard monitor thread",
  "sys tray icon", then it will start application in either interactive
  terminal mode or in gui mode.

- **config.py:** Contains all shared variables and settings.

- **utils.py:** all helper functions.

- **gui.py:** This module has application gui, unfortunately the gui and
  some application logic are mixed together in this module which makes
  it a total mess.

- **settings.py:** this where we save / load
  settings, and download items list

- **brain.py:** every download item obect will be sent to brain to
  download it, this module has thread manager, and file manager

- **cmdview.py:** an interactive user interface in terminal

- **controller.py:** a part of "MVC" design, where it will contain the
  application logic and communicate to both Model and view

- **observables.py:** contains "ObservableDownloadItem",
  "ObservableVideo" which acts as Model in "MVC" design with "observer"
  design

- **downloaditem.py:** It has DownloadItem class which contains
  information for a download item, and you will find a lot of
  DownloadItem objects in this project code named shortly as "d" or
  "self.d".

- **video.py:** it contains Video class which is subclassed from
  DownloadItem, for video objects. also this file has most video related
  function, e.g. merge_video_audio, pre_process_hls, etc...

- **worker.py:** Worker class object acts as a standalone workers, every
  worker responsible for downloading a chunk or file segment

- **update.py:** contains functions for updating PyIDM frozen version
  "currently cx_freeze windows portable version", also update
  youtube-dl.

- **version.py:** contains version number, which is date based, example
  content, __version__ = '2020.8.13'

- **dependency.py:** contains a list of required external packages for
  PyIDM to run and has "install_missing_pkgs" function to install the
  missing packages automatically.

- **ChangeLog.txt:** Log changes to each new version, note that format
  should be consistent, where PyIDM depend on this file to check for new
  versions.

---

### Documentation format:
  code documentation if found doesn't follow a specific format,
  something that should be fixed, the selected project format should
  follow Google Python Style Guide, resources:

- [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google)
- ["Google Python Style Guide"](http://google.github.io/styleguide/pyguide.html)


---

### How can I contribute to this project:
- check open issues in this project and find something that you can fix.
- It's recommended that you open an issue first to discuss what you want
  to do, this will create a better communication with other developer
  working on the project.
- pull request, and add a good description of your modification.
- it doesn't matter how small the change you make, it will make a
  difference.



