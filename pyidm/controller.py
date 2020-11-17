"""
    pyIDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    module description:
        This is the controller module as a part of MVC design, which will replace the old application design
        in attempt to isolate logic from gui / view
        old design has gui and logic mixed together
        The Model has DownloadItem as a base class and located at model.py module
        Model and controller has an observer system where model will notify controller when changed, in turn
        controller will update the current view
"""
from datetime import datetime
import os, sys, time
from copy import copy
from threading import Thread
from queue import Queue
from datetime import date

from . import update
from .utils import *
from . import setting
from . import config
from .config import Status, MediaType
from .brain import brain
from . import video
from .video import get_ytdl_options, import_ytdl
from .model import ObservableDownloadItem, ObservableVideo


def set_option(**kwargs):
    """set global setting option(s) in config.py"""
    try:
        config.__dict__.update(kwargs)
        # log('Settings:', kwargs)
    except:
        pass


def get_option(key, default=None):
    """get global setting option(s) in config.py"""
    try:
        return config.__dict__.get(key, default)
    except:
        return None


def check_ffmpeg():
    """check for ffmpeg availability, first: current folder, second config.global_sett_folder,
    and finally: system wide"""

    log('check ffmpeg availability?')
    found = False

    # search in current app directory then default setting folder
    try:
        for folder in [config.current_directory, config.global_sett_folder]:
            for file in os.listdir(folder):
                # print(file)
                if file == 'ffmpeg.exe':
                    found = True
                    config.ffmpeg_actual_path = os.path.join(folder, file)
                    break
            if found:  # break outer loop
                break
    except:
        pass

    # Search in the system
    if not found:
        cmd = 'where ffmpeg' if config.operating_system == 'Windows' else 'which ffmpeg'
        error, output = run_command(cmd, verbose=False)
        if not error:
            found = True

            # fix issue 47 where command line return \n\r with path
            output = output.strip()
            config.ffmpeg_actual_path = os.path.realpath(output)

    if found:
        log('ffmpeg checked ok! - at: ', config.ffmpeg_actual_path)
        return True
    else:
        log(f'can not find ffmpeg!!, install it, or add executable location to PATH, or copy executable to ',
            config.global_sett_folder, 'or', config.current_directory)


class Controller:
    """controller class
     communicate with (view / gui) and has the logic for downloading process

    it will update GUI thru an update_view method "refer to view.py" by sending data when model changes
    data will be passed in key, value kwargs and must contain "command" keyword

    example:
        {command='new', 'uid': 'uid_e3345de206f17842681153dba3d28ee4', 'active': True, 'name': 'hello.mp4', ...}

    command keyword could have the value of:
        'new':              gui should create new entry in its download list
        'update':           update current download list item
        'playlist_menu':    data contains a video playlist
        'stream_menu'       data contains stream menu
        'd_list'            an item in d_list, useful for loading d_list at startup

    uid keyword:
        this is a unique id for every download item which should be used in all lookup operations

    active keyword:
        to tell if data belongs to the current active download item

    """
    def __init__(self, view_class, custom_settings=None):
        self.observer_q = Queue()  # queue to collect references for updated download items

        # youtube-dl object
        self.ydl = None

        # d_map is a dictionary that map uid to download item object
        self.d_map = {}

        self.pending_downloads_q = Queue()

        # load application settings
        self._load_settings(custom_settings)

        self.url = ''
        self.playlist = []
        self._playlist_menu = []
        self._stream_menu = []
        # self._d = None  # active download item which has self.url
        self.d = None  # active download item which has self.url

        # create view
        self.view = view_class(controller=self)

        # observer thread, it will run in a different thread waiting on observer_q and call self._update_view
        Thread(target=self._observer, daemon=True).start()

        # import youtube-dl in a separate thread
        Thread(target=video.import_ytdl, daemon=True).start()

        # handle pending downloads
        Thread(target=self._pending_downloads_handler, daemon=True).start()

        # handle scheduled downloads
        Thread(target=self._scheduled_downloads_handler, daemon=True).start()

        # check for ffmpeg and update file path "config.ffmpeg_actual_path"
        check_ffmpeg()

    def _process_url(self, url):
        """take url and return a a list of ObservableDownloadItem objects

        when a "view" call this method it should expect a playlist menu (list of names) to be passed to its update
        method,

        Examples:
            playlist_menu=['1- Nasa mission to Mars', '2- how to train your dragon', ...]
            or
            playlist_menu=[] if no video playlist

        """
        self.url = url
        playlist = []
        is_video_playlist = False

        d = ObservableDownloadItem()
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
            self.playlist = playlist

            if is_video_playlist:
                log('controller> playlist ready')
                self._update_playlist_menu([str(i + 1) + '- ' + video.rendered_name for i, video in enumerate(self.playlist)])
                self.select_playlist_video(0)
            else:
                self._update_playlist_menu([])

            if self.playlist:
                self.d = playlist[0]
                self._report_d(self.d, active=True)

        return playlist

    # region update view
    def observer(self, **kwargs):
        """This is an observer method which get notified when change/update properties in ObservableDownloadItem
        it should be as light as possible otherwise it will impact the whole app
        it will be registered by ObservableDownloadItem while creation"""

        self.observer_q.put(kwargs)

    def _observer(self):
        """run in a thread and update views once there is a change in any download item
        it will update gui/view only on specific time intervals to prevent flooding view with data"""

        buffer = {}  # key = uid, value = kwargs
        report_interval = 0.5  # sec

        while True:
            for i in range(self.observer_q.qsize()):
                item = self.observer_q.get()
                uid = item.get('uid')
                if uid:
                    if uid in buffer:
                        buffer[uid].update(**item)
                    else:
                        buffer[uid] = item
                else:
                    buffer[len(buffer)] = item

            for v in buffer.values():
                self._update_view(**v)

            buffer.clear()

            time.sleep(report_interval)

    def _update_view(self, **kwargs):
        """update "view" by calling its update method"""
        # print('controller._update_view:', kwargs)
        try:
            # set default command value
            kwargs.setdefault('command', 'update')

            uid = kwargs.get('uid')
            d = self.d_map.get(uid, None)

            if d is not None:
                # readonly properties will not be reported by ObservableDownloadItem
                downloaded = kwargs.get('downloaded', None)
                if downloaded:
                    extra = {k: getattr(d, k, None) for k in ['progress', 'speed', 'time_left']}
                    # print('extra:', extra)

                    kwargs.update(**extra)

            self.view.update_view(**kwargs)
            # print('controller._update_view:', kwargs)
        except Exception as e:
            log('controller._update_view()> error, ', e)
            # raise e

    def _report_d(self, d, **kwargs):
        """notify view of all properties of a download item

        Args:
            d (ObservableDownloadItem or ObservableVideo): download item
            kwargs: key, values to be included
        """

        properties = d.watch_list

        info = {k: getattr(d, k, None) for k in properties}
        info.update(**kwargs)

        self._update_view(**info)

    def _get_d_list(self):
        for d in self.d_map.values():
            time.sleep(0.1)
            self._report_d(d, command='d_list')
    # endregion

    # region settings
    def _load_settings(self, custom_settings=None):
        # load stored setting from disk
        setting.load_setting()
        
        # update config module with custom settings
        if custom_settings:
            config.__dict__.update(custom_settings)

        # load d_map
        self.d_map = setting.load_d_map()

        # register observer
        for d in self.d_map.values():
            d.register_callback(self.observer)

    def _save_settings(self):
        # Save setting to disk
        setting.save_setting()

        # save d_map
        setting.save_d_map(self.d_map)
    # endregion

    # region video
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
            if config.TEST_MODE:
                raise e

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
            if config.TEST_MODE:
                raise e
        finally:
            vid.busy = False

    def _create_video_playlist(self, url):
        """Process url and build video object(s) and return a video playlist"""
        log('start create video playlist')
        playlist = []

        # we import youtube-dl in separate thread to minimize startup time, will wait in loop until it gets imported
        if video.ytdl is None:
            log('youtube-dl module still not loaded completely, please wait')
            while not video.ytdl:
                time.sleep(1)  # wait until module gets imported

        if self.ydl is None:
            # override _download_webpage in Youtube-dl for captcha workaround -- experimental
            def download_webpage_decorator(func):
                # return data
                def newfunc(obj, *args, **kwargs):
                    print('-' * 20, "start download page")
                    content = func(obj, *args, **kwargs)

                    # search for word captcha in webpage content is not enough
                    # example webpage https://www.youtube.com/playlist?list=PLwvr71r_LHEXwKxel0_hECnTb75JHEwlf

                    if config.enable_captcha_workaround and isinstance(content, str) and 'captcha' in content:
                        print('-' * 20, "captcha here!!")
                        # get webpage offline file path from user
                        fp = self.view.get_offline_webpage_path()

                        if fp is None:
                            log('Cancelled by user')
                            return content

                        if not os.path.isfile(fp):
                            log('invalid file path:', fp)
                            return content

                        with open(fp, 'rb') as fh:
                            new_content = fh.read()
                            encoding = video.ytdl.extractor.common.InfoExtractor._guess_encoding_from_content('', new_content)
                            content = new_content.decode(encoding=encoding)

                    return content

                return newfunc

            video.ytdl.extractor.common.InfoExtractor._download_webpage = download_webpage_decorator(
                    video.ytdl.extractor.common.InfoExtractor._download_webpage)

            self.ydl = video.ytdl.YoutubeDL(get_ytdl_options())

        # reset abort flag
        config.ytdl_abort = False
        try:
            # fetch info by youtube-dl
            info = self.ydl.extract_info(url, download=False, process=False)

            # print(info)

            # don't process direct links, youtube-dl warning message "URL could be a direct video link, returning it as such."
            # refer to youtube-dl/extractor/generic.py
            if not info or info.get('direct'):
                log('controller._create_video_playlist()> No streams found')
                return []

            """
                _type key:

                _type "playlist" indicates multiple videos.
                    There must be a key "entries", which is a list, an iterable, or a PagedList
                    object, each element of which is a valid dictionary by this specification.
                    Additionally, playlists can have "id", "title", "description", "uploader",
                    "uploader_id", "uploader_url" attributes with the same semantics as videos
                    (see above).

                _type "multi_video" indicates that there are multiple videos that
                    form a single show, for examples multiple acts of an opera or TV episode.
                    It must have an entries key like a playlist and contain all the keys
                    required for a video at the same time.

                _type "url" indicates that the video must be extracted from another
                    location, possibly by a different extractor. Its only required key is:
                    "url" - the next URL to extract.
                    The key "ie_key" can be set to the class name (minus the trailing "IE",
                    e.g. "Youtube") if the extractor class is known in advance.
                    Additionally, the dictionary may have any properties of the resolved entity
                    known in advance, for example "title" if the title of the referred video is
                    known ahead of time.

                _type "url_transparent" entities have the same specification as "url", but
                    indicate that the given additional information is more precise than the one
                    associated with the resolved URL.
                    This is useful when a site employs a video service that hosts the video and
                    its technical metadata, but that video service does not embed a useful
                    title, description etc.
            """
            _type = info.get('_type', 'video')

            # handle types: url and url transparent
            if _type in ('url', 'url_transparent'):
                # handle youtube user links ex: https://www.youtube.com/c/MOTORIZADO/videos
                # issue: https://github.com/pyIDM/PyIDM/issues/146
                # info: {'_type': 'url', 'url': 'https://www.youtube.com/playlist?list=UUK32F9z7s_JhACkUdVoWdag',
                # 'ie_key': 'YoutubePlaylist', 'extractor': 'youtube:user', 'webpage_url': 'https://www.youtube.com/c/MOTORIZADO/videos',
                # 'webpage_url_basename': 'videos', 'extractor_key': 'YoutubeUser'}

                info = self.ydl.extract_info(info['url'], download=False, ie_key=info.get('ie_key'), process=False)
                # print(info)

            # check results if _type is a playlist / multi_video -------------------------------------------------
            if _type in ('playlist', 'multi_video') or 'entries' in info:
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
                    vid = ObservableVideo(vid_url, v_info)

                    # update info
                    vid.playlist_title = info.get('title', '')
                    vid.playlist_url = url

                    # add video to playlist
                    playlist.append(vid)

                    # vid.register_callback(self.observer)
            else:

                processed_info = self._process_video_info(info)

                if processed_info and processed_info.get('formats'):

                    # create video object
                    vid = ObservableVideo(url, processed_info) #, observer_callbacks=[self.observer])

                    # get thumbnail
                    vid.get_thumbnail()

                    # report done processing
                    vid.processed = True

                    # add video to playlist
                    playlist.append(vid)

                    # vid.register_callback(self.observer)
                else:
                    log('no video streams detected')
        except Exception as e:
            playlist = []
            log('controller._create_video_playlist:', e)
            if config.TEST_MODE:
                raise e

        return playlist

    def _pre_download_process(self, d, **kwargs):
        """take a ObservableDownloadItem object and process any missing information before download
        return a processed ObservableDownloadItem object"""

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
                if config.TEST_MODE:
                    raise e

            finally:
                vid.busy = False

        return d

    def _update_playlist_menu(self, pl_menu):
        """update playlist menu and send notification to view"""
        self.playlist_menu = pl_menu
        self._update_view(command='playlist_menu', playlist_menu=pl_menu)

    def _update_stream_menu(self, **info):
        """update stream menu and send notification to view
        """
        self.stream_menu = info.get('stream_menu')
        self._update_view(**info)

    def _select_playlist_video(self, idx, active=True):
        """
        select video from playlist menu and update stream menu
        idx: index in playlist menu

        expected notifications to "view":
        dict containing  (idx, stream_menu list, selected_stream_idx),
        and info of current selected video in playlist menu

        view should expect something like below:
        example:
            {'command': 'stream_menu',

            'stream_menu':
            ['● Video streams:                     ',
            '   › mp4 - 1080 - 29.9 MB - id:137 - 30 fps',
            '   › mp4 - 720 - 18.3 MB - id:22 - 30 fps',
            '● Audio streams:                 ',
            '   › aac - 128 - 4.6 MB - id:140',
            '   › webm - 50 - 1.9 MB - id:249', '',
            '● Extra streams:                 ',
            '   › mp4 - 720 - 13.7 MB - id:136 - 30 fps'],

            'video_idx': 0,
            'selected_stream_idx': 1}

        """

        self.d = vid = self.playlist[idx]

        # process video
        if not vid.processed:
            self._process_video(vid)

        self._update_stream_menu(command='stream_menu', stream_menu=vid.stream_menu, video_idx=idx,
                                 stream_idx=vid.stream_menu_map.index(vid.selected_stream))
        self._report_d(self.d, active=active)
    # endregion

    # region download
    def _pending_downloads_handler(self):
        """handle pending downloads, should run in a dedicated thread"""

        while True:
            active_downloads = len([d for d in self.d_map.values() if d.status in (Status.downloading, Status.processing)])
            if active_downloads < config.max_concurrent_downloads:
                d = self.pending_downloads_q.get()
                if d.status == Status.pending:
                    self._download(d, silent=True)

            time.sleep(3)

    def _scheduled_downloads_handler(self):
        """handle scheduled downloads, should run in a dedicated thread"""

        while True:
            sched_downloads = [d for d in self.d_map.values() if d.status == Status.scheduled]
            if sched_downloads:
                current_datetime = datetime.now()
                for d in sched_downloads:
                    if d.sched and datetime.fromisoformat(d.sched) <= current_datetime:
                        self._download(d, silent=True)

            time.sleep(60)

    def _pre_download_checks(self, d, silent=False):
        """do all checks required for this download

        Args:
        d: ObservableDownloadItem object
        silent: if True, hide all a warning dialogues and select default

        Returns:
            (bool): True on success, False on failure
        """

        if not d:
            log('Nothing to download', start='', showpopup=True)
            return False
        elif not d.url:
            log('Nothing to download, no url given', start='', showpopup=True)
            return False
        elif not d.type:
            response = self.get_user_response('None type or bad response code \nForce download?', ['Ok', 'Cancel'])
            if response != 'Ok':
                return False
        elif d.type == 'text/html':
            response = self.get_user_response('Contents might be a web page / html, Download anyway?', ['Ok', 'Cancel'])
            if response == 'Ok':
                d.accept_html = True
            else:
                return False

        if d.status in (Status.downloading, Status.processing):
            log('download is already in progress for this item')
            return False

        # check unsupported protocols
        unsupported = ['f4m', 'ism']
        match = [item for item in unsupported if item in d.subtype_list]
        if match:
            log(f'unsupported protocol: \n"{match[0]}" stream type is not supported yet', start='', showpopup=True)
            return False

        # check for ffmpeg availability
        if d.type in (MediaType.video, MediaType.audio, MediaType.key):
            if not check_ffmpeg():
                # log('Download cancelled, FFMPEG is missing', start='', showpopup=True)

                msg = '\n'.join(['"FFMPEG" is required to process media files',
                    'executable must be copied into PyIDM folder or add ffmpeg path to system PATH',
                    'you can download it manually from https://www.ffmpeg.org/download.html'])

                options = ['Ok']

                if config.operating_system == 'Windows':
                    msg += '\n\n'
                    msg += f'Press "Download" button to download ffmpeg executable into: {config.sett_folder}'

                    options = ['Download', 'Cancel']

                res = self.get_user_response(msg, options=options)
                if res == 'Download':
                    # download ffmpeg from github
                    self._download_ffmpeg()
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
            if config.TEST_MODE:
                raise
            return False
        except (PermissionError, OSError):
            log(f"you don't have enough permission for destination folder {folder}", start='', showpopup=True)
            if config.TEST_MODE:
                raise
            return False
        except Exception as e:
            log(f'problem in destination folder {repr(e)}', start='', showpopup=True)
            if config.TEST_MODE:
                raise e
            return False

        # validate file name
        if d.name == '':
            log("File name can't be empty!!", start='', showpopup=True)
            return False

        # search current list for previous item with same name, folder ---------------------------
        if d.uid in self.d_map:

            log('download item', d.uid, 'already in list, check resume availability')

            # get download item from the list
            d_from_list = self.d_map[d.uid]

            # default
            response = 'Resume'

            if not silent:
                #  show dialogue
                msg = f'File with the same name: \n{d.name},\n' \
                      f'already exist in download list,\n' \
                      'Do you want to resume this file?\n\n'

                response = self.get_user_response(msg, ['Resume', 'Overwrite', 'Cancel'])

            if response not in ('Resume', 'Overwrite'):
                log('Download cancelled by user')
                d.status = Status.cancelled
                return False

            elif response == 'Resume':
                log('check resuming?')

                # to resume, size must match, otherwise it will just overwrite
                if d.size == d_from_list.size and d.selected_quality == d_from_list.selected_quality:
                    log('resume is possible')

                    d.downloaded = d_from_list.downloaded
                else:
                    if not silent:
                        msg = f'Resume not possible, New "download item" has differnet properties than existing one \n' \
                              f'New item size={size_format(d.size)}, selected quality={d.selected_quality}\n' \
                              f'current item size={size_format(d_from_list.size)}, selected quality={d_from_list.selected_quality}\n' \
                              f'if you continue, previous download will be overwritten'
                        response = self.get_user_response(msg, ['Ok', 'Cancel'])
                        if response != 'Ok':
                            log('aborted by user')
                            return False
                    log('file:', d.name, 'has different properties and will be downloaded from the beginning')
                    d.delete_tempfiles(force_delete=True)

            elif response == 'Overwrite':
                log('overwrite')
                d.delete_tempfiles(force_delete=True)

        else:  # new file
            log('fresh file download')

        # check if file with the same name exist in destination
        if os.path.isfile(d.target_file):
            # auto rename option
            if config.auto_rename:
                d = copy(d)
                d.name = auto_rename(d.name, d.folder)
                d.calculate_uid()
                log('File with the same name exist in download folder, generate new name:', d.name)
                self._download(d)
                return False
            else:
                #  show dialogue
                msg = 'File with the same name already exists \n' + d.target_file + '\nDo you want to overwrite file?'
                options = ['Overwrite', 'Cancel download']
                response = self.get_user_response(msg, options)

                if response != options[0]:
                    log('Download cancelled by user')
                    return False
                else:
                    delete_file(d.target_file)
        # ------------------------------------------------------------------

        # if above checks passed will return True
        return True

    def download_simulator(self, d):
        print('start download simulator for id:', d.uid, d.name)

        speed = 200  # kb/s
        d.status = Status.downloading

        if d.downloaded >= d.total_size:
            d.downloaded = 0

        while True:
            time.sleep(1/2)
            # print(d.progress)

            d.downloaded += speed//2 * 1024
            if d.downloaded >= d.total_size:
                d.status = Status.completed
                d.downloaded = d.total_size
                print('download simulator completed for:', d.uid, d.name)

                break

            if d.status == Status.cancelled:
                print('download simulator cancelled for:', d.uid, d.name)
                break

    def _download(self, d, silent=False):
        """start downloading an item

        Args:
            d (ObservableDownloadItem): download item
            silent (bool): if True, hide all a warning dialogues and select default
        """

        try:
            pre_checks = self._pre_download_checks(d, silent=silent)

            if pre_checks:
                # update view
                self._report_d(d, command='new')

                # register observer
                d.register_callback(self.observer)

                # add to download map
                self.d_map[d.uid] = d

                # if max concurrent downloads exceeded, this download job will be added to pending queue
                active_downloads = len(
                    [d for d in self.d_map.values() if d.status in (Status.downloading, Status.processing)])
                if active_downloads >= config.max_concurrent_downloads:
                    d.status = Status.pending
                    self.pending_downloads_q.put(d)
                    return

                # start brain in a separate thread
                if config.SIMULATOR:
                    t = Thread(target=self.download_simulator, daemon=True, args=(d,))
                else:
                    t = Thread(target=brain, daemon=False, args=(d,))
                t.start()

                # wait thread to end
                t.join()

                # update view
                self._report_d(d)

                # post actions
                self._post_download(d)

        except Exception as e:
            log('download()> error:', e)
            if config.TEST_MODE:
                raise e

    def _post_download(self, d):
        """action required after done downloading

        Args:
            d (ObservableDownloadItem): download item
        """

        try:
            # download thumbnail
            if config.download_thumbnail and d.status == Status.completed and d.thumbnail_url:
                fp = os.path.splitext(d.target_file)[0] + '.png'
                download_thumbnail(d.thumbnail_url, fp)

        except Exception as e:
            log('controller._post_download()> error:', e)
            if config.TEST_MODE:
                raise e

    def _download_ffmpeg(self, destination=config.sett_folder):
        """download ffmpeg.exe for windows os

        Args:
            destination (str): download folder

        """

        # set download folder
        config.ffmpeg_download_folder = destination

        # first check windows 32 or 64
        import platform
        # ends with 86 for 32 bit and 64 for 64 bit i.e. Win7-64: AMD64 and Vista-32: x86
        if platform.machine().endswith('64'):
            # 64 bit link
            url = 'https://github.com/pyIDM/PyIDM/releases/download/extra/ffmpeg_64bit.exe'
        else:
            # 32 bit link
            url = 'https://github.com/pyIDM/PyIDM/releases/download/extra/ffmpeg_32bit.exe'

        log('downloading: ', url)

        # create a download object, will save ffmpeg in setting folder
        d = ObservableDownloadItem(url=url, folder=config.ffmpeg_download_folder)
        d.update(url)
        d.name = 'ffmpeg.exe'

        run_thread(self._download, d, silent=True)

    def _download_playlist(self, vsmap, subtitles=None):
        """download playlist
          Args:
              vsmap (dict): key=video idx, value=stream idx
              subtitles (dict): key=language, value=selected extension
        """
        for vid_idx, s_idx in vsmap.items():
            d = self.playlist[vid_idx]
            d.select_stream(index=s_idx)
            d.folder = config.download_folder
            run_thread(self._download, d, silent=True)
            time.sleep(0.1)

            if subtitles:
                self.download_subtitles(subtitles, video_idx=vid_idx)

    def _download_subtitle(self, lang_name, url, extension, d):
        """download one subtitle file"""
        try:
            file_name = f'{os.path.splitext(d.target_file)[0]}_{lang_name}.{extension}'

            # create download item object for subtitle
            sub_d = ObservableDownloadItem()
            sub_d.name = os.path.basename(file_name)
            sub_d.folder = os.path.dirname(file_name)
            sub_d.url = d.url
            sub_d.eff_url = url
            sub_d.type = 'subtitle'
            sub_d.http_headers = d.http_headers

            # if d type is hls video will download file to check if it's an m3u8 or not
            if 'hls' in d.subtype_list:
                log('downloading subtitle', file_name)
                buffer = download(url, http_headers=d.http_headers)

                if buffer:
                    # convert to string
                    buffer = buffer.getvalue().decode()

                    # check if downloaded file is an m3u8 file
                    if '#EXT' in repr(buffer):
                        sub_d.subtype_list.append('hls')

            self._download(sub_d)

        except Exception as e:
            log('download_subtitle() error', e)
    # endregion

    # region Application update
    def _check_for_ytdl_update(self):
        """check for new youtube-dl (or active video extractor backend) version"""

        pkg = config.active_video_extractor

        current_version = config.ytdl_VERSION
        if current_version is None:
            log(f'{pkg} not loaded yet, try again', showpopup=True)
            return

        latest_version, url = update.get_pkg_latest_version(pkg)
        if latest_version:
            config.ytdl_LATEST_VERSION = latest_version
            note = f'{pkg} version: {config.ytdl_VERSION}, Latest version: {config.ytdl_LATEST_VERSION}'
            log(note)

            if update.parse_version(latest_version) > update.parse_version(current_version):
                response = self.get_user_response(
                    f'Found new version of {pkg} on pypi \n'
                    f'new version     =  {latest_version}\n'
                    f'current version =  {current_version} \n'
                    'Install new version? (check Log Tab for progress)',  options=['Ok', 'Cancel'])

                if response == 'Ok':
                    try:
                        run_thread(update.update_pkg, pkg, url, daemon=True)
                    except Exception as e:
                        log(f'failed to update {pkg}:', e)
            else:
                log(f'{pkg} is up-to-date, current version = {current_version}', showpopup=True)

    def _rollback_ytdl_update(self):
        """delete last video extractor e.g. youtube-dl update and restore last one"""
        pkg = config.active_video_extractor

        response = self.get_user_response(f'Delete last {pkg} update and restore previous version?',
                                          options=['Ok', 'Cancel'])

        if response == 'Ok':
            try:
                run_thread(update.rollback_pkg_update, pkg, daemon=True)
            except Exception as e:
                log(f'failed to restore {pkg}:', e)

    def _check_for_pyidm_update(self):
        """
        check for new app version or update patch and show update window,
        this method is time consuming and should run from a thread
        """

        # check for new App. version
        changelog = update.check_for_new_version()
        if changelog:

            response = self.get_user_response(f'New pyidm version available, full change log:\n\n{changelog}',
                                              options=['Homepage', 'cancel'])
            if response == 'Homepage':
                update.open_update_link()

        else:
            log('No Update available', showpopup=True)

    def _auto_check_for_update(self):
        """auto check for pyidm update"""
        if config.check_for_update:
            today = date.today()
            try:
                last_check = date(*config.last_update_check)
            except:
                last_check = today

            delta = today - last_check
            if delta.days >= config.update_frequency:
                res = self.get_user_response(f'Check for PyIDM update?\nLast check was {delta.days} days ago',
                                             options=['Ok', 'Cancel'])
                if res == 'Ok':
                    self.check_for_pyidm_update()

            config.last_update_check = (today.year, today.month, today.day)
    # endregion

    # public API for  a view / GUI (it shouldn't block to prevent gui freeze) ------------------------------------------
    def log_runtime_info(self):
        """Print useful information about the system"""
        log('-' * 30, 'PyIDM', '-' * 30)
        log('Starting PyIDM version:', config.APP_VERSION, 'Frozen' if config.FROZEN else 'Non-Frozen')
        log('operating system:', config.operating_system_info)
        log('Python version:', sys.version)
        log('current working directory:', config.current_directory)
        log('FFMPEG:', config.ffmpeg_actual_path)

    def process_url(self, url):
        """take url and return a a list of ObservableDownloadItem objects

        when a "view" call this method it should expect a playlist menu (list of names) to be passed to its update
        method,

        Examples:
            playlist_menu=['1- Nasa mission to Mars', '2- how to train your dragon', ...]
            or
            playlist_menu=[] if no video playlist

        """
        self.url = url
        self.reset()

        if url:
            try:
                run_thread(self._process_url, url)
            except Exception as e:
                log("process_url:", e)
                if config.TEST_MODE:
                    raise e

    def reset(self):
        """reset controller and cancel ongoing operation"""
        # stop youyube-dl
        config.ytdl_abort = True
        self.d = None
        self.playlist = []

    def delete(self, uid):
        """delete download item from the list
        Args:
            uid (str): unique identifier property for a download item in self.d_map
        """

        d = self.d_map.pop(uid)

        d.status = Status.cancelled

        # delete files
        run_thread(d.delete_tempfiles())

    # region download
    def download(self, uid=None, **kwargs):
        """download an item

        Args:
            uid (str): unique identifier property for a download item in self.d_map, if none, self.d will be downloaded
            kwargs: key/value for any legit attributes in DownloadItem
        """

        if uid is None:
            d = self.d
            silent = False
        else:
            d = self.d_map[uid]
            silent = True

        if d is None:
            log('Nothing to download', showpopup=True)
            return

        # validate file name and extension
        name = kwargs.get('name', None)
        if name:
            title, ext = os.path.splitext(name)
            if ext != d.extension:
                kwargs['name'] = title + d.extension

        update_object(d, kwargs)

        run_thread(self._download, d, silent)
        # Thread(target=self._download, args=(d, silent)).start()

        return True

    def download_playlist(self, vsmap, subtitles=None):
        """download playlist
        Args:
            vsmap (dict): key=video idx, value=stream idx
            subtitles (dict): key=language, value=selected extension
        """

        run_thread(self._download_playlist, vsmap, subtitles)

    def stop_download(self, uid):
        """stop downloading
        Args:
            uid (str): unique identifier property for a download item in self.d_map
        """

        d = self.d_map.get(uid)

        if d and d.status in (Status.downloading, Status.processing, Status.pending):
            d.status = Status.cancelled
    # endregion

    # region video
    def select_playlist_video(self, idx, active=True):
        """
        select video from playlist menu and update stream menu
        idx: index in playlist menu

        to see expected notifications to "view" and example:
            *read _select_playlist_video() doc string
        """

        run_thread(self._select_playlist_video, idx, active=active)

    def select_stream(self, idx, active=True):
        """select stream for current selected video in playlist menu
        idx: index in stream menu
        expected notifications: info of current selected video in playlist menu
        """

        self.d.select_stream(index=idx)
        self._report_d(self.d, active=active)

    def select_audio(self, audio_idx, uid=None, video_idx=None):
        """select audio from audio menu
        Args:
            audio_idx (int): index of audio stream
            uid: unique video uid
            video_idx (int): index of video in self.playlist
        """
        # get download item
        d = self.get_d(uid, video_idx)

        if not d or not d.audio_streams:
            return None

        selected_audio_stream = d.audio_streams[audio_idx]

        d.select_audio(selected_audio_stream)
        log('Selected audio:', selected_audio_stream)

    def set_video_backend(self, extractor):
        """select video extractor backend, e.g. youtube-dl, youtube-dlc, ..."""
        config.ytdl_VERSION = None
        set_option(active_video_extractor=extractor)
        run_thread(import_ytdl, extractor, daemon=True)
    # endregion

    # region subtitles
    def get_subtitles(self, uid=None, video_idx=None):
        """send subtitles info for view
        # subtitles stored in download item in a dictionary format
        # template: subtitles = {language1:[sub1, sub2, ...], language2: [sub1, ...]}, where sub = {'url': 'xxx', 'ext': 'xxx'}
        # Example: {'en': [{'url': 'http://x.com/s1', 'ext': 'srv1'}, {'url': 'http://x.com/s2', 'ext': 'vtt'}], 'ar': [{'url': 'https://www.youtub}, {},...]

        Returns:
            (dict): e.g. {'en': ['srt', 'vtt', ...], 'ar': ['vtt', ...], ..}}
        """

        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        all_subtitles = d.prepare_subtitles()

        # required format {'en': ['srt', 'vtt', ...], 'ar': ['vtt', ...], ..}
        subs = {k: [item.get('ext', 'txt') for item in v] for k, v in all_subtitles.items()}

        if subs:
            return subs

    def download_subtitles(self, subs, uid=None, video_idx=None):
        """download multiple subtitles for the same download item
        Args:
            subs (dict): language name vs extension name
            uid (str): video uid
            video_idx (int): video index in self.playlist
        """

        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        all_subtitles = d.prepare_subtitles()

        for lang, ext in subs.items():
            items_list = all_subtitles.get(lang, [])

            match = [item for item in items_list if item.get('ext') == ext]
            if match:
                item = match[-1]
                url = item.get('url')

                if url:
                    run_thread(self._download_subtitle, lang, url, ext, d)
            else:
                log('subtitle:', lang, 'Not available for:', d.name)
    # endregion

    # region open file/folder
    def play_file(self, uid=None, video_idx=None):
        """open download item target file or temp file"""
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        if os.path.isfile(d.target_file):
            open_file(d.target_file)
        else:
            open_file(d.temp_file)

    def open_file(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        open_file(d.target_file)

    def open_temp_file(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        open_file(d.temp_file)

    def open_folder(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        open_folder(d.folder)
    # endregion

    # region get info
    def get_d_list(self):
        """update previous download list in view"""
        log('controller.get_d_list()> sending d_list')
        run_thread(self._get_d_list)

    def get_webpage_url(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        return d.url

    def get_direct_url(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        return d.eff_url

    def get_playlist_url(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return

        return d.playlist_url

    def get_properties(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d:
            return 'No properties available!'

        # General properties
        text = f'UID: {d.uid} \n' \
               f'Name: {d.rendered_name} \n' \
               f'Folder: {d.folder} \n' \
               f'Progress: {d.progress}% \n' \
               f'Downloaded: {size_format(d.downloaded)} of {size_format(d.total_size)} \n' \
               f'Status: {d.status} \n' \
               f'Resumable: {d.resumable} \n' \
               f'Type: {d.type}, {", ".join(d.subtype_list)}\n' \
               f'Remaining segments: {d.remaining_parts} of {d.total_parts}\n'

        if d.type == 'video':
            text += f'Protocol: {d.protocol} \n' \
                    f'Video stream: {d.selected_quality}\n'

            if 'dash' in d.subtype_list:
                text += f'Audio stream: {d.audio_quality}\n'

        if d.status == Status.scheduled:
            text += f'Scheduled: {d.sched}'

        return text

    def get_audio_menu(self, uid=None, video_idx=None):
        """get audio menu "FOR DASH VIDEOS ONLY"
        Args:
            uid: unique video uid
            video_idx (int): index of video in self.playlist

        Returns:
            (list): list of audio streams
        """
        # get download item
        d = self.get_d(uid, video_idx)

        if not d or d.type != 'video' or not d.audio_streams or 'dash' not in d.subtype_list:
            return None

        audio_menu = [stream.name for stream in d.audio_streams]
        return audio_menu

    def get_selected_audio(self, uid=None, video_idx=None):
        """send selected audio
        Args:
            uid: unique video uid
            video_idx (int): index of video in self.playlist

        Returns:
            (str): name of selected audio streams
        """
        # get download item
        d = self.get_d(uid, video_idx)

        if not d or not d.audio_streams:
            return None

        return d.audio_stream.name

    def get_d(self, uid=None, video_idx=None):
        """get download item reference

        Args:
            uid (str): unique id for a download item
            video_idx (int): index of a video download item in self.playlist

        Returns:
            (DownloadItem): if uid and video_idx omitted it will return self.d
        """

        if uid is not None:
            d = self.d_map.get(uid)
        elif video_idx is not None:
            d = self.playlist[video_idx]
        else:
            d = self.d

        return d
    # endregion

    # region schedul
    def schedule_start(self, uid=None, video_idx=None, target_date=None):
        """Schedule a download item
        Args:
            target_date (datetime.datetime object): target date and time to start download
        """
        # get download item
        d = self.get_d(uid, video_idx)

        if not d or not isinstance(target_date, datetime):
            return

        # validate target date should be greater than current date
        if target_date < datetime.now():
            log('Can not Schedule something in the past', 'Please select a Schedule time greater than current time',
                showpopup=True)
            return

        log(f'Schedule {d.name} at: {target_date}')
        d.sched = target_date.isoformat(sep=' ')
        d.status = Status.scheduled

    def schedule_cancel(self, uid=None, video_idx=None):
        # get download item
        d = self.get_d(uid, video_idx)

        if not d or d.status != Status.scheduled:
            return

        log(f'Schedule for: {d.name} has been cancelled')
        d.status = Status.cancelled
        d.sched = None
    # endregion

    # region Application update
    def auto_check_for_update(self):
        if not config.disable_update_feature:
            run_thread(self._auto_check_for_update)

    def check_for_pyidm_update(self):
        run_thread(self._check_for_pyidm_update)

    def check_for_ytdl_update(self):
        run_thread(self._check_for_ytdl_update)

    def rollback_ytdl_update(self):
        run_thread(self._rollback_ytdl_update)
    # endregion

    # region cmd view
    def interactive_download(self, url, **kwargs):
        """intended to be used with command line view and offer step by step choices to download an item"""
        playlist = self._process_url(url)

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
            options = [f'{s.mediatype} {"video" if s.mediatype != "audio" else "only"}: {str(s)}' for s in
                       d.all_streams]
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
        self._report_d(d)

        self._save_settings()
        config.shutdown = True
    # endregion

    def get_user_response(self, msg, options):
        """get user response from current view

        Args:
            msg(str): a message to show
            options (list): a list of options, example: ['yes', 'no', 'cancel']

        Returns:
            (str): response from user as a selected item from "options"
        """

        response = self.view.get_user_response(msg, options)

        return response

    def run(self):
        """run current "view" main loop"""
        self.view.run()
        config.shutdown = True  # set global shutdown flag
        config.ytdl_abort = True

        # cancel all current downloads
        print('Stop all downloads')
        for d in self.d_map.values():
            self.stop_download(d.uid)

        self._save_settings()


