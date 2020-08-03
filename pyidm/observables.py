# this module contains an observables data models 

from .downloaditem import DownloadItem
from .video import Video


class observableDownloadItem(DownloadItem):

    def __init__(self, registered_callbacks=[], **kwargs):
        super().__init__(**kwargs)

        # list of callbacks to be executed on properties change
        self.registered_callbacks = registered_callbacks

    def __setattr__(self, name, value):
        """Called when an attribute assignment is attempted."""
        # self.__dict__[name] = value  # don't use this because it dosn't work well with decorated properties
        
        super().__setattr__(name, value)
   
        # properties names to be monitored for change
        watch_list = ['downloaded', 'name', 'type', 'subtype_list', 'busy']

        if name in watch_list:
            self.notify(name=value)

    def notify(self, *args, **kwargs):
        """execute registered callbacks"""
        try:
            for callback in self.registered_callbacks:
                callback(self, *args, **kwargs)
        except:
            pass

    def register_callback(self, callback):
        if callback not in self.registered_callbacks:
            self.registered_callbacks.append(callback)
    
    def unregister_callback(self, callback):
        if callback in self.registered_callbacks:
            self.registered_callbacks.remove(callback)


class observableVideo(Video):
    def __init__(self, url, vid_info=None, registered_callbacks=[], **kwargs):
        super().__init__(url, vid_info=vid_info, **kwargs)
        
        # list of callbacks to be executed on properties change
        self.registered_callbacks = registered_callbacks

    def __setattr__(self, name, value):
        """Called when an attribute assignment is attempted."""
        # self.__dict__[name] = value  # don't use this because it dosn't work well with decorated properties
        
        super().__setattr__(name, value)
   
        # properties names to be monitored for change
        watch_list = ['downloaded', 'name', 'type', 'subtype_list', 'busy']

        if name in watch_list:
            self.notify(name=value)

    def notify(self, *args, **kwargs):
        """execute registered callbacks"""
        try:
            for callback in self.registered_callbacks:
                callback(self, *args, **kwargs)
        except:
            pass

    def register_callback(self, callback):
        if callback not in self.registered_callbacks:
            self.registered_callbacks.append(callback)
    
    def unregister_callback(self, callback):
        if callback in self.registered_callbacks:
            self.registered_callbacks.remove(callback)

    def select_audio(self, audio_stream=None):
        super().select_audio(audio_stream=audio_stream)

        # re-build segments
        self.build_segments()

        # re-calculate total size
        self.total_size = self.calculate_total_size()
