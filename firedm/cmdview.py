"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        This is a command line / Terminal view, as a layer between user and controller
        it must inherit from IView and implement all its abstract methods, see view.py
        currently it runs in interactive mode and not suitable for automated jobs.

"""


import shutil

if not __package__:
    __package__ = 'firedm'

from .view import IView
from .utils import *


def get_terminal_size():
    """get terminal window size, return 2-tuple (width, height)"""
    try:
        size = shutil.get_terminal_size()
    except:
        # default fallback values
        size = (100, 20)
    return size


def print_progress_bar(percent, suffix='', bar_length=20, fill='█'):
    """print progress bar to screen, percent is number between 0 and 100"""
    try:

        scale = bar_length / 100
        filled_length = int(percent * scale)
        bar = fill * filled_length + ' '*(bar_length - filled_length)

        # get screen size
        terminal_width = get_terminal_size()[0]

        line = f'\r {percent}% [{bar}] {suffix}'
        end_spaces = terminal_width - len(line)
        line += ' '*end_spaces

        # truncate line 
        line = line[:terminal_width]

        print(f'\r{line}', end='')
        
    except:
        pass


class CmdView(IView):
    """concrete class for terminal user interface"""
    def __init__(self, controller=None):
        self.controller = controller
        self.total_size = None
        self.progress = 0

    def run(self):
        """intended to be used in gui as a mainloop not in terminal views"""
        pass

    def quit(self):
        """intended to be used in gui as a mainloop not in terminal views"""
        pass

    def update_view(self, total_size=None, **kwargs):
        """update view"""

        progress = kwargs.get('progress', 0)
        speed = kwargs.get('speed')
        eta = kwargs.get('eta')
        downloaded = kwargs.get('downloaded')
        if total_size:
            self.total_size = total_size

        # in terminal view, it will be only one download takes place in a time
        # since there is no updates coming from d_list items, it is easier to identify the currently downloading item
        # by checking progress
        if 0 < progress < 100 <= self.progress:
            self.progress = progress

        if progress > 0 and self.progress < 100:
            # print progress bar on screen

            suffix = f'{format_bytes(downloaded, sep="", percision=1)}'
            if self.total_size:
                suffix += f'/{format_bytes(self.total_size, sep="", percision=1)}'
            suffix += f" {format_bytes(speed, tail='/s', percision=1)}" if speed else ''
            suffix += f', {format_seconds(eta, percision=0, fullunit=True)}' if eta else ''

            print_progress_bar(progress, suffix=suffix, fill='=')

            if progress >= 100:
                print()  # print empty line

            # to ignore repeated updates after 100%
            self.progress = progress

    def get_user_response(self, msg, options, **kwargs):
        """a mimic for a popup window in terminal, to get user response, 
        example: if msg =   "File with the same name already exists\n
                            /home/mahmoud/Downloads/7z1900.exe\n
                            Do you want to overwrite file? "

        and option = ['Overwrite', 'Cancel download']
        the resulting box will looks like:

        *******************************************
        * File with the same name already exists  *
        * /home/mahmoud/Downloads/7z1900.exe      *
        * Do you want to overwrite file?          *
        * --------------------------------------- *
        * Options:                                *
        *   1: Overwrite                          *
        *   2: Cancel download                    *
        *******************************************
        Select Option Number: 

        """
        # map options to numbers starting from 1
        options_map = {i + 1: x for i, x in enumerate(options)}

        # split message to list of lines
        msg_lines = msg.split('\n')

        # format options in lines example: "  1: Overwrite",  and "  2: Cancel download"  
        options_lines = [f'  {k}: {str(v)}' for k, v in options_map.items()]

        # get the width of longest line in msg body or options
        max_line_width = max(max([len(line) for line in msg_lines]), max([len(line) for line in options_lines])) 
        
        # get current terminal window size (width)
        terminal_width = get_terminal_size()[0]

        # the overall width of resulting msg box including border ('*' stars in our case)
        box_width = min(max_line_width + 4, terminal_width)

        # build lines without border
        output_lines = []
        output_lines += msg_lines
        separator = '-' * (box_width - 4)
        output_lines.append(separator)
        output_lines.append("Options:")
        output_lines += options_lines

        # add stars and space padding for each line
        for i, line in enumerate(output_lines):
            allowable_line_width = box_width - 4

            # calculate the required space to fill the line
            delta = allowable_line_width - len(line) if allowable_line_width > len(line) else 0

            # add stars
            line = '* ' + line + ' ' * delta + ' *'

            output_lines[i] = line
        
        # create message string
        msg = '\n'.join(output_lines)
        msg = '\n' + '*' * box_width + '\n' + msg + '\n' + '*' * box_width
        msg += '\n Select Option Number: '

        while True:
            txt = input(msg)
            try:
                # get user selection
                # it will raise exception if user tries to input number not in options_map
                response = options_map[int(txt)]  
                print() # print empty line
                break  # exit while loop if user entered a valid selection
            except:
                print('\n invalid entry, try again.\n')

        return response


if __name__ == '__main__':
    import time

    for i in range(101):
        print_progress_bar(i, suffix=100 - i, fill='=')
        time.sleep(1)