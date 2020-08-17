### Developer Guide

This Guide for developer who want to contribute or understand how this project work, feel free to improve this guide anytime


**Purpose of this project:**
	I made this project to help me download youtube videos, then decided to share it thinking it might
	be useful for someone else, so please don't put your fire on me if you find a mistake in code or stupid
	approach to solve a problem, or an ugly gui design, instead try to help fix it.<br>
	Unfortunately, I didn't document the code well enough and it will take a lot of effort to make a proper 
	comments inside the code. <br>
	This project is never made to compete with other download managers, it is just a "hopefully useful" addition.


**current project logic:**
	Generally PyIDM is using Libcurl as a download engine via threads to achieve multi-connections,
	for videos, youtube-dl is our player, where its sole role is to extract video information from
	a specific url "No other duties for youtube-dl".
	FFMPEG will be used for post processing e.g. mux audio and video, merge HLS video segments 
	into one video file, and other useful media manipulation. <br>
	a plan in progress to implement "MVC" design, currently done basic controller in controller.py and Model in 
	observables.py, which will give us a good chance to make different gui designs without affecting application logic
	currently there is cmdview.py which run interactively in terminal which depend on controller

**Files:** <br>
	PyIDM.py: 	<br>
		main file, it will start "clipboard monitor thread", "sys tray icon", then it will start application 
		in either interactive terminal mode or in gui mode. <br><br>
	config.py:<br>
		Contains all shared variables and settings<br><br>
	utils.py:<br>
		all helper functions <br><br>
	gui.py:<br>
		This module has application gui, unfortunately the gui and some application logic are mixed together in this 
		module which makes it a total mess<br><br>
	settings.py:<br>
		this where we save / load settings, and download items list<br><br>
	brain.py:<br>
		every download item obect will be send to brain to download it, this module has thread manager, and file manager<br><br>
	cmdview.py:<br>
		an interactive user interface in terminal <br><br>
	controller.py:<br>
		a part of "MVC" design, where it will contain the application logic and communicate to both Model and view<br><br>
	observables.py:<br>
		contains "ObservableDownloadItem", "ObservableVideo" which acts as Model in "MVC" design with "observer" design<br><br>
	downloaditem.py:<br>
		It has DownloadItem class which contains information for a download item, and you will find a lot of DownloadItem objects in this 
		project code named shortly as "d" or "self.d".<br><br>
	video.py:<br>
		it contains Video class which is subclassed from DownloadItem, for video objects.<br>
		also this file has most video related function, e.g. merge_video_audio, pre_process_hls, etc...<br><br>
	worker.py:<br>
		Worker class object acts as a standalone workers, every worker responsible for downloading a chunk or file segment<br><br>
	update.py:<br>
		contains functions for updating PyIDM frozen version "currently cx_freeze windows portable version", also update youtube-dl<br><br>
	version.py:<br>
		contains version number, which is date based, example content, __version__ = '2020.8.13'<br><br>
	dependency.py:<br>
		contains a list of required external packages for PyIDM to run and has "install_missing_pkgs" function to install the missing pkgs
		automatically.<br><br>
	ChangeLog.txt:<br>
		Log changes to each new version, note that format should be consistent, where PyIDM depend on this file to check for new versions<br><br>


		




