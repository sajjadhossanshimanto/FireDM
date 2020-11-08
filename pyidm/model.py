"""
    PyIDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        this module contains an observables data models
"""
import os

from .downloaditem import DownloadItem
from .video import Video
from . import utils


class Observable:
    """super class for observable download item / Video"""
    def __init__(self, observer_callbacks=None):
        """initialize

        Args:
            observer_callbacks (iterable): list or tuple of callbacks that will be called when any property in
            watch_list changes
        """

        self.watch_list = ['uid', 'name', 'rendered_name', 'progress', 'speed', 'time_left', 'downloaded', 'size',
                           'total_size', 'status', 'busy', 'thumbnail', 'type', 'subtype_list', 'resumable', 'extension',
                           'errors', 'sched', 'remaining_parts', 'live_connections', 'total_parts']

        # list of callbacks to be executed on properties change
        self.observer_callbacks = observer_callbacks or []

        # unique name for download item, will be calculated based on name and target folder
        self.uid = None

    def setter(self, super_class, key, value):
        """intended to be used in subclass' __setattr__

        """

        try:
            old_value = super_class.__getattribute__(self, key)
        except:
            old_value = None

        # normalize folder path https://github.com/pyIDM/PyIDM/issues/185
        if key == 'folder':
            value = os.path.normpath(value)

        # set new value
        super_class.__setattr__(self, key, value)
        # self.__dict__[key] = value  # don't use this because it doesn't work well with decorated properties

        if value != old_value:
            # calculate uid if name or folder changed
            if key in ('name', 'folder'):
                self.calculate_uid()

            self.notify(key, value)

    def notify(self, key, value):
        if key in self.watch_list:
            self._notify(**{'uid': self.uid, key: value})

    def _notify(self, **kwargs):
        """execute registered callbacks"""

        try:
            for callback in self.observer_callbacks:
                callback(**kwargs)
        except:
            raise

    def register_callback(self, callback):
        if callback not in self.observer_callbacks:
            self.observer_callbacks.append(callback)

    def unregister_callback(self, callback):
        if callback in self.observer_callbacks:
            self.observer_callbacks.remove(callback)

    def calculate_uid(self):
        """calculate or update uid based on full file path"""
        self.uid = utils.generate_unique_name(self.folder, self.name, prefix='uid_')

    def add_to_saved_properties(self, key):
        """append to the list in original DownloadItem class, to be saved to disk"""
        self.saved_properties.append(key)


class ObservableDownloadItem(DownloadItem, Observable):
    """Observable DownloadItem data model"""

    def __init__(self, observer_callbacks=None, **kwargs):
        Observable.__init__(self, observer_callbacks=observer_callbacks)
        DownloadItem.__init__(self, **kwargs)

    def __setattr__(self, key, value):
        """Called when an attribute assignment is attempted."""
        self.setter(DownloadItem, key, value)


class ObservableVideo(Video, Observable):
    """Observable Video data model"""

    def __init__(self, url, vid_info=None, observer_callbacks=None):
        Observable.__init__(self, observer_callbacks=observer_callbacks)
        Video.__init__(self, url, vid_info=vid_info)

        self.thumbnail_size = (220, 115)

    def __setattr__(self, key, value):
        """Called when an attribute assignment is attempted."""
        self.setter(Video, key, value)

    def select_audio(self, audio_stream=None):
        """extend select audio in superclass 'Video' """
        # call superclass method
        Video.select_audio(self, audio_stream=audio_stream)

        # re-build segments
        self.build_segments()

        # re-calculate total size
        self.total_size = self.calculate_total_size()

    def get_thumbnail(self):
        """get video thumbnail and store it as base64 text in self.thumbnail"""
        if self.thumbnail_url and not self.thumbnail:
            buffer = utils.get_thumbnail(self.thumbnail_url)
            img = utils.resize_image(buffer=buffer, size=self.thumbnail_size)
            self.thumbnail = utils.image_to_base64(img)

    def prepare_subtitles(self):
        """merge subtitles and captions in one list and handle duplicated names

        # subtitles stored in download item in a dictionary format
        # template: subtitles = {language1:[sub1, sub2, ...], language2: [sub1, ...]}, where sub = {'url': 'xxx', 'ext': 'xxx'}
        # Example: {'en': [{'url': 'http://x.com/s1', 'ext': 'srv1'}, {'url': 'http://x.com/s2', 'ext': 'vtt'}], 'ar': [{'url': 'https://www.youtub}, {},...]

        Returns:
            (dict): one dict contains all subtitles
        """
        # build subtitles from self.d.subtitles and self.d.automatic_captions, and rename repeated keys
        all_subtitles = {}
        for k, v in self.subtitles.items():
            if k in all_subtitles:
                k = k + '_2'
            k = k + '_sub'
            all_subtitles[k] = v

        for k, v in self.automatic_captions.items():
            if k in all_subtitles:
                k = k + '_2'
            k = k + '_caption'
            all_subtitles[k] = v

        # sort subtitles
        sorted_keys = utils.natural_sort(all_subtitles.keys())
        all_subtitles = {k: all_subtitles[k] for k in sorted_keys}

        # add 'srt' extension
        for lang, ext_list in all_subtitles.items():

            for item in ext_list:  # item example: [{'url': 'http://x.com/s1', 'ext': 'srv1'}, {'url': 'http://x.com/s2', 'ext': 'vtt'}]
                item.setdefault('ext', 'txt')

            extensions = [item.get('ext') for item in ext_list]

            # add 'srt' extension if 'vtt' available
            if 'vtt' in extensions and 'srt' not in extensions:
                vtt_item = [item for item in ext_list if item.get('ext') == 'vtt'][-1]
                srt_item = vtt_item.copy()
                srt_item['ext'] = 'srt'
                ext_list.insert(0, srt_item)

        return all_subtitles

