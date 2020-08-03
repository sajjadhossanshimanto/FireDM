# All views / guis should implement this interface

from abc import ABC, abstractmethod

class IView(ABC):
    @abstractmethod
    def run(self):
        """run view mainloop if any"""
        pass

    @abstractmethod
    def update(self, *args, **kwargs):
        """act as an observer to model changes
        update view, it will be called automatically by controller
        this method shouldn't block
        :param d: DownloadItem Object which has been updated/changed "observable model"
        """
        pass

    @abstractmethod
    def get_user_response(self, msg, options):
        """get user choice and send it back to controller, 
        mainly this is a popup window or input() method in terminal"""
        pass