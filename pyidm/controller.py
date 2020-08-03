"""
    pyIDM

    multi-connections internet download manager, based on "pyCuRL/curl", "youtube_dl", and "PySimpleGUI"

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

# This is the controller module as a part of MVC design, which will replace the old application design
# in attempt to isolate logic from gui / view 
# old design has gui and logic mixed together
# The Model has DownloadItem as a base class and located at observables.py module
# Model and conroller has an observer system where model will notify controller when changed, in turn
# controller will notify the current view

# region imports
import os, sys, time
from threading import Thread
from queue import Queue
import youtube_dl as ytdl

from .utils import *
from . import setting
from . import config
from .config import Status
from . import update
from .brain import brain
from . import video
from .video import (check_ffmpeg, download_ffmpeg, unzip_ffmpeg, get_ytdl_options, 
                    download_m3u8, parse_subtitles, download_sub)
from .observables import observableDownloadItem as DownloadItem, observableVideo as Video
# endregion


class Controller:
    """this is the controller which communicate with view / ui / gui and has the logic for downloading process"""
    def __init__(self, view_class, custom_settings={}):
        # create youtube-dl object
        self.ydl = ytdl.YoutubeDL(get_ytdl_options())

        self.d_list = []
        self.active_downloads = []
        self.pending_downloads = []

        # load application settings
        self._load_settings(custom_settings)

        self.url = ''
        self.playlist = []
        self._playlist_menu = []
        self._stream_menu = []
        self.d = None  # active download item which has self.url

        self.observer_q = Queue()  # queue to collect refrences for updated downloaditems 

        # create view
        self.view = view_class(controller=self)

        # notifier thread, it will run in a different thread waiting on observer_q and call self._notify
        Thread(target=self._notifier, daemon=True).start()

    def observer(self, d=None, *args, **kwargs):
        """This is an observer method which get notified when change/update properties in DownloadItem
        it should be as light as possible otherwise it will impact the whole app
        it will be rigestered by DownloadItem while creation"""

        self.observer_q.put(d)

    def _notifier(self):
        """run in a thread and update views once there is a change in any download item
        thread should be marked as daemon to get terminated when application quit"""

        while True:
            d = self.observer_q.get()  # it will block waiting for new values in queue
            self._notify(d)

    def _notify(self, d=None, *args, **kwargs):
        """update "view" by calling its update method"""
        try:
            if d:
                # add active keyword
                active = True if d == self.d else False 

                properties = ['id', 'name', 'rendered_name', 'progress', 'speed', 'time_left',
                              'downloaded', 'size', 'total_size', 'status', 'busy']
                info = {k: getattr(d, k, None) for k in properties}
                info['active'] = active
              
            else:
                info = kwargs
            
            self.view.update(**info)
        except Exception as e:
            log('controller._notify()> error, ', e)

    def _log_runtime_info(self):
        """Print useful information about the system"""
        log('-' * 50, 'PyIDM', '-' * 50)
        log('Starting PyIDM version:', config.APP_VERSION, 'Frozen' if config.FROZEN else 'Non-Frozen')
        log('operating system:', config.operating_system_info)
        log('Python version:', sys.version)
        log('current working directory:', config.current_directory)

    def _load_settings(self, custom_settings={}):
        # load stored setting from disk
        setting.load_setting()
        
        # update config module with custom settings
        config.__dict__.update(custom_settings)

        # load stored d_list from the disk
        self.d_list = config.d_list = setting.load_d_list()

    def _save_settings(self):
        # Save setting to disk
        setting.save_setting()
        setting.save_d_list(config.d_list)

    def _process_video_info(self, info):
        """process video info for a video object
        info: youtube-dl info dict
        """
        try:

            # process info
            processed_info = self.ydl.process_ie_result(info, download=False)

            return processed_info
        
        except Exception as e:
            log('_process_video_info()> error:', e)

    def _process_video(self, vid):
        """process video info and refresh Video object properties, 
        typically required when video is a part of unprocessed video playlist"""
        try:
            vid.busy = True  # busy flag will be used to show progress bar or a busy mouse cursor
            vid_info = self._process_video_info(vid.vid_info)
            
            if vid_info:
                vid.vid_info = vid_info
                vid.refresh()

                vid.get_thumbnail()

                log('_process_video_info()> processed url:', vid.url, log_level=3)
                vid.processed = True
            else:
                log('_process_video_info()> Failed,  url:', vid.url, log_level=3)
        except Exception as e:
            log('_process_video_info()> error:', e)
        finally:
            vid.busy = False

    def _create_video_playlist(self, url):
        """Process url and build video object(s) and return a video playlist"""
        log('start create video playlist')
        playlist = []

        # fetch info by youtube-dl
        info = self.ydl.extract_info(url, download=False, process=False)

        # print(info)

        if not info or info.get('direct'):
            log('youtube_func()> No streams found')
            return []

        result_type = info.get('_type', 'video')

        # check results if _type is a playlist / multi_video -------------------------------------------------
        if result_type in ('playlist', 'multi_video') or 'entries' in info:
            log('youtube-func()> start processing playlist')
            # log('Media info:', info)

            # videos info
            pl_info = list(info.get('entries'))  # info.get('entries') is a generator

            # create initial playlist with un-processed video objects
            for v_info in pl_info:
                v_info['formats'] = []

                # get video's url
                vid_url = v_info.get('webpage_url', None) or v_info.get('url', None) or v_info.get('id', None)

                # create video object
                vid = Video(vid_url, v_info, registered_callbacks=[self.observer])

                # update info
                vid.playlist_title = info.get('title', '')
                vid.playlist_url = url

                # add video to playlist
                playlist.append(vid)
        else:
            v_info = info

            processed_info = self._process_video_info(info)

            if processed_info and processed_info.get('formats'):
                
                # create video object
                vid = Video(url, processed_info, registered_callbacks=[self.observer])

                # get thumbnail
                vid.get_thumbnail()

                # report done processing
                vid.processed = True

                # add video to playlist
                playlist.append(vid)
            else:
                log('no video streams detected')

        return playlist

    def _pre_download_checks(self, d, silent=False):
        """do all checks required for this download"""
        """
         do all pre-download checks
        :param d: DownloadItem object
        :param silent: if True, hide all a warnning dialogues and select default
        :return: True on success, False on failure
        """

        if not d:
            log('Nothing to download', start='', showpopup=True)
            return False
        elif not d.url:
            log('Nothing to download, no url given', start='', showpopup=True)
            return False
        elif not d.type:
            response = self.get_user_response('None type or bad response code \nForce download?', options=['Ok', 'Cancel'])
            if response != 'Ok':
                return False
        elif d.type == 'text/html':
            response = self.get_user_response('Contents might be a web page / html, Download anyway?', options=['Ok', 'Cancel'])
            if response == 'Ok':
                d.accept_html = True
            else:
                return False

        # check unsupported protocols
        unsupported = ['f4m', 'ism']
        match = [item for item in unsupported if item in d.subtype_list]
        if match:
            log(f'unsupported protocol: \n"{match[0]}" stream type is not supported yet', start='', showpopup=True)
            return False

        # check for ffmpeg availability in case this is a dash video or hls video
        if 'dash' in d.subtype_list or 'hls' in d.subtype_list:
            # log('Dash or HLS video detected')
            if not check_ffmpeg():
                log('Download cancelled, FFMPEG is missing', start='', showpopup=True)
                return False

        # validate destination folder for existence and permissions
        # in case of missing download folder value will fallback to current download folder
        folder = d.folder or config.download_folder
        try:
            test_file_path = os.path.join(folder, 'test_file_.pyidm')
            with open(test_file_path, 'w') as f:
                f.write('0')
            delete_file(test_file_path)

            # update download item
            d.folder = folder
        except FileNotFoundError:
            log(f'destination folder {folder} does not exist', start='', showpopup=True)
            return False
        except PermissionError:
            log(f"you don't have enough permission for destination folder {folder}", start='', showpopup=True)
            return False
        except Exception as e:
            log(f'problem in destination folder {repr(e)}', start='', showpopup=True)
            return False

        # validate file name
        if d.name == '':
            log("File name can't be empty!!", start='', showpopup=True)
            return False

        # check if file with the same name exist in destination
        if os.path.isfile(d.target_file):
            # auto rename option
            if config.auto_rename:
                d.name = auto_rename(d.name, d.folder)
                log('File with the same name exist in download folder, generate new name:', d.name)
            else:
                #  show dialogue
                msg = 'File with the same name already exists \n' + d.target_file + '\nDo you want to overwrite file?'
                options = ['Overwrite', 'Cancel download']
                response = self.get_user_response(msg, options=options)
                # print('Model received:', response)

                if response != options[0]:
                    log('Download cancelled by user')
                    return False
                else:
                    delete_file(d.target_file)

        # search current list for previous item with same name, folder ---------------------------
        match = [x.id for x in self.d_list if x.target_file == d.target_file]
        if match:

            log('download item', d.num, 'already in list, check resume availability')
            
            match_id = match[0]
            d.id = match_id

            # get download item from the list
            d_from_list = self.d_list[match_id]

            # default
            response = 'Resume'

            if not silent:
                #  show dialogue
                msg = f'File with the same name: \n{d.name},\n already exist in download list\n' \
                      'Do you want to resume this file?\n' \
                      'Resume ==> continue if it has been partially downloaded ... \n' \
                      'Overwrite ==> delete old downloads and overwrite existing item... \n' \
                      'note: "if you need fresh download, you have to change file name \n' \
                      'or target folder or delete same entry from download list'

                response = self.get_user_response(msg, ['Resume', 'Overwrite', 'Cancel'])

            if response == 'Resume':
                log('check resuming?')

                # to resume, size must match, otherwise it will just overwrite
                if d.size == d_from_list.size and d.selected_quality == d_from_list.selected_quality:
                    log('resume is possible')
                    
                    d.downloaded = d_from_list.downloaded
                else:
                    if not silent:
                        msg = f'Resume not possible, New "download item" has differnet properties than existing one \n' \
                              f'New item    : size={size_format(d.size)}, selected quality={d.selected_quality}\n' \
                              f'current item: size={size_format(d_from_list.size)}, selected quality={d_from_list.selected_quality}\n' \
                              f'if you continue, previous download will be overwritten'
                        response = self.get_user_response(msg, ['Ok', 'Cancel'])
                        if response != 'Ok':
                            log('aborted by user')
                            return False
                    log('file:', d.name, 'has different properties and will be downloaded from beginning')
                    d.delete_tempfiles(force_delete=True)

                # replace old item in download list
                self.d_list[match_id] = d

            elif response == 'Overwrite':
                log('overwrite')
                d.delete_tempfiles(force_delete=True)

                # replace old item in download list
                self.d_list[match_id] = d

            else:
                log('Download cancelled by user')
                d.status = Status.cancelled
                return False

        else:  # new file
            log('fresh file download')
            # generate unique id number for each download
            d.id = len(self.d_list)

            # add to download list
            self.d_list.append(d)
        # ------------------------------------------------------------------

        # if max concurrent downloads exceeded, this download job will be added to pending queue
        if len(self.active_downloads) >= config.max_concurrent_downloads:
            d.status = Status.pending
            self.pending_downloads.append(d)
            return False

        # if above checks passed will return True
        return True

    def _pre_download_process(self, d, **kwargs):
        """take a DownloadItem object and process any missing information before download
        return a processed DownloadItem object"""

        # update user preferences
        d.__dict__.update(kwargs)

        # video 
        if d.type == 'video' and not d.processed:
                vid = d
                
                try:
                    vid.busy = False

                    # process info
                    processed_info = self.ydl.process_ie_result(vid.vid_info, download=False)

                    if processed_info:
                        vid.vid_info = processed_info
                        vid.refresh()

                        # get thumbnail
                        vid.get_thumbnail()

                        log('_process_video_info()> processed url:', vid.url, log_level=3)
                        vid.processed = True
                    else:
                        log('_process_video_info()> Failed,  url:', vid.url, log_level=3)
                
                except Exception as e:
                    log('_process_video_info()> error:', e)
                
                finally:
                    vid.busy = False
        
        return d

    def _download(self, d, **kwargs):
        """start downloading an item"""
        try:
            pre_checks = self._pre_download_checks(d)

            if pre_checks:
                # start brain in a separate thread
                t = Thread(target=brain, daemon=False, args=(d,))
                t.start()

                # wait thread to end
                t.join()

        except Exception as e:
            log('download()> error:', e)

    def _update_playlist_menu(self, pl_menu):
        """update playlist menu and send notification to view"""
        self.playlist_menu = pl_menu
        self._notify(playlist_menu=pl_menu)

    def _update_stream_menu(self, stream_menu):
        """update stream menu and send notification to view"""
        self.stream_menu = stream_menu
        self._notify(stream_menu=stream_menu)

    # public API ----------------------------------------------------------
    def process_url(self, url):
        """take url and return a a list of DownloadItem objects"""
        self.url = url
        playlist = []
        is_video_playlist = False

        self.d = d = DownloadItem(registered_callbacks=[self.observer])
        d.update(url)

        # searching for videos
        if d.type == 'text/html' or d.size < 1024 * 1024:  # 1 MB as a max size
            print('playlist here')
            playlist = self._create_video_playlist(url)

            if playlist:
                is_video_playlist = True
                
    
        if not playlist:
            playlist = [d]

        if url == self.url:
            log('controller> playlist ready')
            self.playlist = playlist

            if is_video_playlist:
                self._update_playlist_menu([str(i + 1) + '- ' + video.rendered_name for i, video in enumerate(self.playlist)])
                self.select_playlist_video(0)

        return playlist

    def select_playlist_video(self, idx):
        """
        select video from playlist menu and update stream menu
        idx: index in playlist menu
        expected notifications to "view": 
        dict containing  (idx, stream_menu list, selected_stream_idx), 
        and info of current selected video in playlist menu"""

        self.d = vid = self.playlist[idx]
        
        # process video
        if not vid.processed:
            self._process_video(vid)
        
        info = dict(idx=idx, stream_menu=vid.stream_menu, selected_stream_idx=vid.stream_menu_map.index(vid.selected_stream))
        self._update_stream_menu(info)
        self._notify(self.d)

    def select_stream(self, idx):
        """select stream for current selected video in playlist menu
        idx: index in stream menu
        expected notifications: info of current selected video in playlist menu"""

        self.d.select_stream(index=idx)
        self._notify(self.d)
        
    def interactive_download(self, url, **kwargs):
        """intended to be used with command line view and offer step by step choices to download an item"""
        playlist = self.process_url(url)

        d = playlist[0]

        if len(playlist) > 1:
            msg = 'The url you provided is a playlist of multi-files'
            options = ['Show playlist content', 'Cancel']
            response = self.get_user_response(msg, options)

            if response == options[1]:
                log('Cancelled by user')
                return

            elif response == options[0]:
                if len(playlist) > 50:
                    msg = f'This is a big playlist with {len(playlist)} files, \n' \
                          f'Are you sure?'
                    options = ['Continue', 'Cancel']
                    r = self.get_user_response(msg, options)
                    if r == options[1]:
                        log('Cancelled by user')
                        return
                    
                msg = 'Playlist files names, select item to download:'
                options = [d.name for d in playlist]
                response = self.get_user_response(msg, options)

                idx = options.index(response)
                d = playlist[idx]

        # pre-download process missing information, and update user preferences
        self._pre_download_process(d, **kwargs)

        # select format if video
        if d.type == 'video':
            if not d.all_streams:
                log('no streams available')
                return

            # ffmpeg check
            if not check_ffmpeg():
                log('ffmpeg missing, abort')
                return

            msg = f'Available streams:'
            options = [f'{s.mediatype} {"video" if s.mediatype != "audio" else "only"}: {str(s)}' for s in d.all_streams]
            selection = self.get_user_response(msg, options)
            idx = options.index(selection)
            d.selected_stream = d.all_streams[idx]

            if 'dash' in d.subtype_list:
                msg = f'Audio Formats:'
                options = d.audio_streams
                audio = self.get_user_response(msg, options)
                d.select_audio(audio)
        
        msg = f'Item: {d.name} with size {size_format(d.total_size)}\n'
        if d.type == 'video':
            msg += f'selected video stream: {d.selected_stream}\n'
            msg += f'selected audio stream: {d.audio_stream}\n'

        msg += 'folder:' + d.folder + '\n'
        msg += f'Start Downloading?'
        options = ['Ok', 'Cancel']
        r = self.get_user_response(msg, options)
        if r == options[1]:
            log('Cancelled by user')
            return

        # download
        self._download(d)
        self._notify(d)

        self._save_settings()
        config.shutdown = True

    def get_user_response(self, msg, options):
        """get user response from current view
        msg: a message to show
        options: a list of options, example: ['yes', 'no', 'cancel']"""

        response = self.view.get_user_response(msg, options)

        return response

    def run(self):
        """run current "view" main loop"""
        self.view.run()

