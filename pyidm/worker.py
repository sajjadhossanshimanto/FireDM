"""
    PyIDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

# worker class

# todo: change docstring to google format and clean unused code

import os
import pycurl

from .config import Status, error_q, jobs_q, max_seg_retries
from .utils import log, set_curl_options, size_format, translate_server_code


class Worker:
    def __init__(self, tag=0, d=None):
        self.tag = tag
        self.d = d
        self.seg = None
        self.resume_range = None

        # writing data parameters
        self.file = None
        self.mode = 'wb'  # file opening mode default to new write binary

        self.downloaded = 0

        # connection parameters
        self.c = pycurl.Curl()
        self.speed_limit = 0
        self.headers = {}

        # minimum speed and timeout, abort if download speed slower than n byte/sec during n seconds
        self.minimum_speed = None
        self.timeout = None

        self.print_headers = True

    def __repr__(self):
        return f"worker_{self.tag}"

    def reuse(self, seg=None, speed_limit=0, minimum_speed=None, timeout=None):
        """Recycle same object again, better for performance as recommended by curl docs"""
        if seg.locked:
            log('Seg', self.seg.basename, 'segment in use by another worker', '- worker', {self.tag}, log_level=2)
            return False

        self.reset()

        self.seg = seg

        # set lock
        self.seg.locked = True

        self.speed_limit = speed_limit

        # minimum speed and timeout, abort if download speed slower than n byte/sec during n seconds
        self.minimum_speed = minimum_speed
        self.timeout = timeout

        msg = f'Seg {self.seg.basename} start, size: {size_format(self.seg.size)} - range: {self.seg.range}'
        if self.speed_limit:
            msg += f'- SL= {self.speed_limit}'
        if self.minimum_speed:
            msg += f'- minimum speed= {self.minimum_speed}, timeout={self.timeout}'

        log(msg, ' - worker', self.tag, log_level=2)

        self.check_previous_download()

        return True

    def reset(self):
        # reset curl options "only", other info cache stay intact, https://curl.haxx.se/libcurl/c/curl_easy_reset.html
        self.c.reset()

        # reset variables
        self.file = None
        self.mode = 'wb'  # file opening mode default to new write binary
        self.downloaded = 0
        self.resume_range = None
        self.headers = {}

        self.print_headers = True

    def check_previous_download(self):
        def overwrite():
            # reset start size and remove value from d.downloaded
            self.d.downloaded -= self.seg.current_size
            self.mode = 'wb'
            log('Seg', self.seg.basename, 'overwrite the previous part-downloaded segment', ' - worker', self.tag,
                log_level=3)

        # if file doesn't exist will start fresh
        if not os.path.exists(self.seg.name):
            self.mode = 'wb'
            return

        if self.seg.current_size == 0:
            self.mode = 'wb'
            return

        # if no seg.size, we will overwrite current file because resume is not possible
        if not self.seg.size:
            overwrite()
            return

        # at this point file exists and resume is possible
        # case-1: segment is completed before
        if self.seg.current_size == self.seg.size:
            log('Seg', self.seg.basename, 'already completed before', ' - worker', self.tag, log_level=3)
            self.seg.downloaded = True

        # Case-2: over-sized, in case the server sent extra bytes from last session by mistake, truncate file
        elif self.seg.current_size > self.seg.size:
            log('Seg', self.seg.basename, 'over-sized', self.seg.current_size, 'will be truncated to:',
                size_format(self.seg.size), ' - worker', self.tag, log_level=3)

            self.seg.downloaded = True
            self.d.downloaded -= self.seg.current_size - self.seg.size

            # truncate file
            with open(self.seg.name, 'rb+') as f:
                f.truncate(self.seg.size)

        # Case-3: Resume, with new range
        elif self.seg.range and self.seg.current_size < self.seg.size:
            # set new range and file open mode
            a, b = self.seg.range
            self.resume_range = [a + self.seg.current_size, b]
            self.mode = 'ab'  # open file for append

            # report
            log('Seg', self.seg.basename, 'resuming, new range:', self.resume_range,
                'current segment size:', size_format(self.seg.current_size), ' - worker', self.tag, log_level=3)

        # case-x: overwrite
        else:
            overwrite()

    def verify(self):
        """check if segment completed"""
        # Case-1, unknown segment size, will report done if there is any downloaded data > 0
        if self.seg.size == 0 and self.seg.current_size > 0:
            return True

        # Case-2, unknown segment size, and zero downloaded data, will retry a couple of times, ignore it if failed
        elif self.seg.size == 0 and self.seg.current_size == 0:
            if self.seg.retries < max_seg_retries:
                log('seg:', self.seg.basename, 'has zero size, will try again, number of retries:', self.seg.retries)
                return False
            else:
                log('seg:', self.seg.basename, 'exceeded max. retries:', self.seg.retries,
                    'it has zero size, and will be ignored')
                return True

        # Case-3, segment has a known size
        elif self.seg.current_size >= self.seg.size:
            return True

        # Case-x, report failed
        else:
            return False

    def report_not_completed(self):
        log('Seg', self.seg.basename, 'did not complete', '- done', size_format(self.seg.current_size), '- target size:',
            size_format(self.seg.size), '- left:', size_format(self.seg.size - self.seg.current_size), '- worker', self.tag, log_level=3)

    def report_completed(self):
        # self.debug('worker', self.tag, 'completed', self.seg.name)
        self.seg.downloaded = True

        # in case couldn't fetch segment size from headers
        if not self.seg.size:
            self.seg.size = self.seg.current_size
        # print(self.headers)

        log('downloaded segment: ',  self.seg.basename, self.seg.range, size_format(self.seg.size), '- worker', self.tag, log_level=2)

    def set_options(self):

        # set general curl options
        set_curl_options(self.c, http_headers=self.d.http_headers)

        self.c.setopt(pycurl.URL, self.seg.url)

        range_ = self.resume_range or self.seg.range
        if range_:
            self.c.setopt(pycurl.RANGE, f'{range_[0]}-{range_[1]}')  # download segment only not the whole file

        self.c.setopt(pycurl.NOPROGRESS, 0)  # will use a progress function

        # set speed limit selected by user
        self.c.setopt(pycurl.MAX_RECV_SPEED_LARGE, self.speed_limit)  # cap download speed to n bytes/sec, 0=disabled

        # verbose
        self.c.setopt(pycurl.VERBOSE, 0)

        # call back functions
        self.c.setopt(pycurl.HEADERFUNCTION, self.header_callback)
        self.c.setopt(pycurl.WRITEFUNCTION, self.write)
        self.c.setopt(pycurl.XFERINFOFUNCTION, self.progress)

        # set minimum speed and timeout, abort if download speed slower than n byte/sec during n seconds
        if self.minimum_speed:
            self.c.setopt(pycurl.LOW_SPEED_LIMIT, self.minimum_speed)

        if self.timeout:
            self.c.setopt(pycurl.LOW_SPEED_TIME, self.timeout)

    def header_callback(self, header_line):
        header_line = header_line.decode('iso-8859-1')
        header_line = header_line.lower()

        if ':' not in header_line:
            return

        name, value = header_line.split(':', 1)
        name = name.strip()
        value = value.strip()
        self.headers[name] = value

        # update segment size if not available
        if not self.seg.size and name == 'content-length':
            try:
                self.seg.size = int(self.headers.get('content-length', 0))
                # print('self.seg.size = ', self.seg.size)
            except:
                pass

    def progress(self, *args):
        """it receives progress from curl and can be used as a kill switch
        Returning a non-zero value from this callback will cause curl to abort the transfer
        """

        # check termination by user
        if self.d.status != Status.downloading:
            return -1  # abort

        if self.headers and self.headers.get('content-range') and self.print_headers:
            range_ = self.resume_range or self.seg.range
            log('Seg', self.seg.basename, 'range:', range_, 'server headers, range, size',
                self.headers.get('content-range'), self.headers.get('content-length'), log_level=3)
            self.print_headers = False

    def report_error(self, description='unspecified error'):
        # report server error to thread manager, to dynamically control connections number
        error_q.put(description)

    def run(self):
        try:

            # check if file completed before and exit
            if self.seg.downloaded:
                raise Exception('completed before')

            if not self.seg.url:
                log('Seg', self.seg.basename, 'segment has no valid url', '- worker', {self.tag}, log_level=2)
                raise Exception('invalid url')

            # record retries
            self.seg.retries += 1

            # set options
            self.set_options()

            # make sure target directory exist
            target_directory = os.path.dirname(self.seg.name)
            if not os.path.isdir(target_directory):
                os.makedirs(target_directory)  # it will also create any intermediate folders in the given path

            # open segment file
            self.file = open(self.seg.name, self.mode, buffering=0)

            # Main Libcurl operation
            self.c.perform()

            # get response code and check for connection errors
            response_code = self.c.getinfo(pycurl.RESPONSE_CODE)
            if response_code in range(400, 512):
                log('Seg', self.seg.basename, 'server refuse connection', response_code, translate_server_code(response_code),
                    'content type:', self.headers.get('content-type'), log_level=3)

                # send error to thread manager, it will reduce connections number to fix this error
                self.report_error(f'server refuse connection: {response_code}, {translate_server_code(response_code)}')

        except Exception as e:
            # this error generated when user cancel download, or write function abort
            if '23' in repr(e) or '42' in repr(e):  # ('Failed writing body', 'Callback aborted')
                error = f'terminated'
                log('Seg', self.seg.basename, error, 'worker', self.tag, log_level=3)
            else:
                error = repr(e)
                log('Seg', self.seg.basename, '- worker', self.tag, 'quitting ...', error, log_level=3)

                # report server error to thread manager
                self.report_error(repr(e))

        finally:
            # close segment file handle
            if self.file:
                self.file.close()

            # check if download completed
            completed = self.verify()
            if completed:
                self.report_completed()
            else:
                # if segment not fully downloaded send it back to thread manager to try again
                self.report_not_completed()

                # put back to jobs queue to try again
                jobs_q.put(self.seg)

            # remove segment lock
            self.seg.locked = False

    def write(self, data):
        """write to file"""

        content_type = self.headers.get('content-type')
        if content_type and 'text/html' in content_type:
            # some video encryption keys has content-type 'text/html'
            try:
                decoded_data = data.decode('utf-8').lower()
                if not self.d.accept_html and ('<html' in decoded_data or '<!doctype html' in decoded_data):
                    log('Seg', self.seg.basename, '- worker', self.tag, 'received html contents, aborting', log_level=3)

                    log('=' * 20, data, '=' * 20, sep='\n', start='', log_level=3)

                    # report server error to thread manager
                    self.report_error('received html contents')

                    return -1  # abort
            except Exception as e:
                pass
                # log('worker:', e)

        # write to file
        self.file.write(data)

        self.downloaded += len(data)

        # report to download item
        self.d.downloaded += len(data)

        # check if we getting over sized
        if self.seg.current_size > self.seg.size > 0:
            log('Seg', self.seg.basename, 'oversized:',
                'current segment size:', self.seg.current_size, ' - worker', self.tag, log_level=3)

            # re-adjust value of total downloaded data
            self.d.downloaded -= self.seg.current_size - self.seg.size
            return -1  # abort



