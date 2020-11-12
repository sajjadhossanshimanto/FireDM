"""
    pyIDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""
import base64
import datetime
import hashlib
import importlib
import os
import io
import webbrowser
from threading import Thread

import pycurl
import time
import plyer
import certifi
import shutil
import subprocess
import shlex
import re
import json
from PIL import Image


from . import config

# todo: change docstring to google format and clean unused code


def notify(message='', title='', timeout=5, app_icon='', ticker='', toast=False,  app_name=config.APP_TITLE):
    """
    show os notification at systray area

    :param title: Title of the notification
    :param message: Message of the notification
    :param app_name: Name of the app launching this notification
    :param app_icon: Icon to be displayed along with the message
    :param timeout: time to display the message for, defaults to 10
    :param ticker: text to display on status bar as the notification arrives
    :param toast: simple Android message instead of full notification

    :type title: str
    :type message: str
    :type app_name: str
    :type app_icon: str
    :type timeout: int
    :type ticker: str
    :type toast: bool

    .. note::
       When called on Windows, ``app_icon`` has to be a path to
       a file in .ICO format.
    """

    try:
        plyer.notification.notify(title=title, message=message, app_name=app_name, app_icon=app_icon, timeout=timeout,
                                  ticker='', toast=False)
    except Exception as e:
        log(f'plyer notification: {e}')


def handle_exceptions(error):
    if config.TEST_MODE:
        raise error
    else:
        log(error)


def set_curl_options(c, http_headers=None):
    """take pycurl object as an argument and set basic options"""

    # use default headers if no http-headers assigned or passed empty headers
    http_headers = http_headers or config.HEADERS

    # c.setopt(pycurl.USERAGENT, config.USER_AGENT)

    # http headers must be in a list format
    headers = [f'{k}:{v}' for k, v in http_headers.items()]

    c.setopt(pycurl.HTTPHEADER, headers)

    # set proxy, must be string empty '' means no proxy
    c.setopt(pycurl.PROXY, config.proxy)

    # referer
    if config.referer_url:
        c.setopt(pycurl.REFERER, config.referer_url)
    else:
        c.setopt(pycurl.AUTOREFERER, 1)

    # cookies
    if config.use_cookies:
        c.setopt(pycurl.COOKIEFILE, config.cookie_file_path)

    # website authentication
    if config.username or config.password:
        c.setopt(pycurl.USERNAME, config.username)
        c.setopt(pycurl.PASSWORD, config.password)

    # re-directions
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 10)

    c.setopt(pycurl.NOSIGNAL, 1)  # option required for multithreading safety
    c.setopt(pycurl.NOPROGRESS, 1)
    c.setopt(pycurl.CAINFO, certifi.where())  # for https sites and ssl cert handling
    c.setopt(pycurl.PROXY_CAINFO, certifi.where())

    # verifies SSL certificate
    # fix for pycurl.error: (43, 'CURLOPT_SSL_VERIFYHOST no longer supports 1 as value!'), issue #183
    # reference: https://curl.haxx.se/libcurl/c/CURLOPT_SSL_VERIFYHOST.html
    if not config.verify_ssl_cert:
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)

    # time out
    c.setopt(pycurl.CONNECTTIMEOUT, 10)  # limits the connection phase, it has no impact once it has connected.

    # abort if download speed slower than 1024 byte/sec during 10 seconds
    c.setopt(pycurl.LOW_SPEED_LIMIT, 1024)
    c.setopt(pycurl.LOW_SPEED_TIME, 10)

    # verbose
    if config.log_level >= 4:
        c.setopt(pycurl.VERBOSE, 1)
    else:
        c.setopt(pycurl.VERBOSE, 0)

    # it tells curl not to include headers with the body
    c.setopt(pycurl.HEADEROPT, 0)

    c.setopt(pycurl.TIMEOUT, 300)
    c.setopt(pycurl.AUTOREFERER, 1)


def get_headers(url, verbose=False, http_headers=None):
    """return dictionary of headers"""

    log('get_headers()> getting headers for:', url, log_level=3)

    curl_headers = {}

    def header_callback(header_line):
        # quit if main window terminated
        if config.terminate:
            return

        header_line = header_line.decode('iso-8859-1')
        header_line = header_line.lower()

        if ':' not in header_line:
            return

        name, value = header_line.split(':', 1)
        name = name.strip()
        value = value.strip()
        curl_headers[name] = value
        if verbose:
            print(name, ':', value)

    def write_callback(data):
        return -1  # send terminate flag

    def debug_callback(handle, type, data, size=0, userdata=''):
        """it takes output from curl verbose and pass it to my log function"""
        try:
            log(data.decode("utf-8"))
        except:
            pass
        return 0

    # region curl options
    c = pycurl.Curl()

    # set general curl options
    set_curl_options(c, http_headers)

    # set special curl options
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.WRITEFUNCTION, write_callback)
    c.setopt(pycurl.HEADERFUNCTION, header_callback)
    # endregion

    try:
        c.perform()
    except Exception as e:
        # write callback will terminate libcurl to discard the body, we only need the headers, an exception will be
        # raised e.g. (23, 'FFailed writing body') or (23, 'Failure writing output to destination')
        if '23' not in repr(e):
            log('get_headers()>', e)

    # add status code and effective url to headers
    curl_headers['status_code'] = c.getinfo(pycurl.RESPONSE_CODE)
    curl_headers['eff_url'] = c.getinfo(pycurl.EFFECTIVE_URL)

    # return headers
    return curl_headers


def download(url, file_name=None, verbose=True, http_headers=None):
    """
    simple file download, into bytesio buffer and store it on disk if file_name is given
    :param url: string url/link
    :param file_name: string type for file path
    :param verbose: bool, log events if true
    :param http_headers: key, value dict for http headers to be sent to the server
    :return: bytesIo buffer or None
    """

    if not url:
        log('download()> url not valid:', url)
        return None

    if verbose:
        log('download()> downloading', url)

    def set_options():
        # set general curl options
        set_curl_options(c, http_headers)

        # set special curl options
        c.setopt(pycurl.URL, url)

    # pycurl initialize
    c = pycurl.Curl()
    set_options()

    # create buffer to hold download data
    buffer = io.BytesIO()
    c.setopt(c.WRITEDATA, buffer)

    try:
        # run libcurl
        c.perform()

        if file_name:
            # save file name
            with open(file_name, 'wb') as file:
                # after PyCurl done writing download data into buffer the current "cursor" position is at end of buffer
                # bring position back to start of the buffer
                buffer.seek(0)
                file.write(buffer.read())
                file.close()

        # reset buffer stream position
        buffer.seek(0)
        return buffer

    except Exception as e:
        log('download():', e)
        return None
    finally:
        # close curl
        c.close()


def size_format(size, tail=''):
    # 1 kb = 1024 byte, 1MB = 1024 KB, 1GB = 1024 MB
    # 1 MB = 1024 * 1024 = 1_048_576 bytes
    # 1 GB = 1024 * 1024 * 1024 = 1_073_741_824 bytes

    try:
        if size == 0: return '...'
        """take size in num of byte and return representation string"""
        if size < 1024:  # less than KB
            s = f'{round(size)} bytes'

        elif 1_048_576 > size >= 1024:  # more than or equal 1 KB and less than MB
            s = f'{round(size / 1024)} KB'
        elif 1_073_741_824 > size >= 1_048_576:  # MB
            s = f'{round(size / 1_048_576, 1)} MB'
        else:  # GB
            s = f'{round(size / 1_073_741_824, 2)} GB'
        return f'{s}{tail}'
    except:
        return size


def time_format(t, tail=''):
    if t == -1:
        return '...'

    try:
        if t <= 60:
            s = f'{round(t)} seconds'
        elif 60 < t <= 3600:
            s = f'{round(t / 60)} minutes'
        elif 3600 < t <= 86400:
            s = f'{round(t / 3600, 1)} hours'
        elif 86400 < t <= 2592000:
            s = f'{round(t / 86400, 1)} days'
        elif 2592000 < t <= 31536000:
            s = f'{round(t / 2592000, 1)} months'
        else:
            s = f'{round(t / 31536000, 1)} years'

        return f'{s}{tail}'
    except:
        return t


def log(*args, log_level=1, start='>> ', end='\n', sep=' ', showpopup=False):
    """print messages to stdout and execute any function or method in config.log_callbacks

    Args:
        args: comma separated messages to be printed
        log_level (int): used to filter messages, 1 to 3 for verbose
        start (str): prefix appended to start of string
        end (str): tail of string
        sep (str): separator used to join text "args"
        showpopup (bool): if True will show popup gui message

    Returns:
        None
        """

    if log_level > config.log_level:
        return

    text = sep.join(map(str, args))

    try:
        print(start + text + end, end='')

        # execute registered log callbacks
        for f in config.log_callbacks:
            f(start, text, end)

        # popup
        if showpopup and config.log_popup_callback:
            config.log_popup_callback(start, text, end)

    except Exception as e:
        print(e)


def echo_stdout(func):
    """Copy stdout / stderr and send it to gui"""

    def echo(text):
        try:
            config.log_q.put(('log', text))
            return func(text)
        except:
            return func(text)

    return echo


def echo_stderr(func):
    """Copy stdout / stderr and send it to gui"""

    def echo(text):
        try:
            config.log_q.put(('log', text))
            return func(text)
        except:
            return func(text)

    return echo


def validate_file_name(f_name):
    # filter for tkinter safe character range
    f_name = ''.join([c for c in f_name if ord(c) in range(65536)])
    safe_string = str()
    char_count = 1
    for c in str(f_name):
        if c in ['\\', '/', ':', '?', '<', '>', '"', '|', '*']:
            safe_string += '_'
        else:
            safe_string += c

        if char_count >= 245:  # max. allowed filename length 255 on windows, https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file?redirectedfrom=MSDN
            safe_string += f_name[-10:]  # add last 10 characters "including file extension"
            break
        else:
            char_count += 1
    return safe_string


def size_splitter(size, part_size):
    """Receive file size and return a list of size ranges"""
    result = []

    if size == 0:
        result.append('0-0')
        return result

    # decide num of parts
    span = part_size if part_size <= size else size
    # print(f'span={span}, part size = {part_size}')
    parts = max(size // span, 1)  # will be one part if size < span

    x = 0
    size = size - 1  # when we start counting from zero the last byte number should be size - 1
    for i in range(parts):
        y = x + span - 1
        if size - y < span:  # last remaining bytes
            y = size
        result.append(f'{x}-{y}')
        x = y + 1

    return result


def delete_folder(folder, verbose=False):
    try:
        shutil.rmtree(folder)
        if verbose:
            log('done deleting folder:', folder)
        return True
    except Exception as e:
        if verbose:
            log('delete_folder()> ', e)
        return False


def delete_file(file, verbose=False):
    try:
        os.unlink(file)
        if verbose:
            log('done deleting file:', file)
        return True
    except Exception as e:
        if verbose:
            log('delete_file()> ', e)
        return False


def rename_file(oldname=None, newname=None, verbose=False):
    if oldname == newname:
        return True
    elif os.path.isfile(newname):
        log('rename_file()>  destination file already exist')
        return False
    try:
        os.rename(oldname, newname)
        log('done renaming file:', oldname, '... to:', newname, start='\n')
        return True
    except Exception as e:
        if verbose:
            log('rename_file()> ', e)
        return False


def get_seg_size(seg):
    # calculate segment size from segment name i.e. 200-1000  gives 801 byte
    try:
        a, b = int(seg.split('-')[0]), int(seg.split('-')[1])
        size = b - a + 1 if b > 0 else 0
        return size
    except:
        return 0


def run_command(cmd, verbose=True, shell=False, hide_window=True, d=None, nonblocking=False):
    """
    run command in a subprocess
    :param cmd: string of actual command to be executed
    :param verbose: if true will re-route subprocess output to log()
    :param shell: True or False
    :param hide_window: True or False, hide shell window
    :param d: DownloadItem object mainly use "status" property to terminate subprocess
    :param nonblocking: if True, run subprocess and exit in other words it will not block until finish subprocess
    :return: error (True or False), output (string of stdout/stderr output)
    """

    # override shell parameter currently can't kill subprocess if shell=True at least on windows, more investigation required
    shell = False

    if verbose:
        log('running command:', cmd)

    error, output = True, f'error running command {cmd}'

    try:

        # split command if shell parameter set to False
        if not shell:
            cmd = shlex.split(cmd)

        # startupinfo to hide terminal window on windows
        if hide_window and config.operating_system == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None

        # start subprocess using Popen instead of subprocess.run() to get a real-time output
        # since run() gets the output only when finished
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8',
                                   errors='replace', shell=shell, startupinfo=startupinfo)

        if nonblocking:
            return

        # update reference in download item, it will be cancelled with status, see DownloadItem.status property setter
        if d:
            d.subprocess = process

        output = ''

        for line in process.stdout:
            line = line.strip()
            output += line
            if verbose:
                log(line)

            # # monitor kill switch
            # if d and d.status == config.Status.cancelled:
            #     log('terminate run_command()>', cmd)
            #     process.kill()
                # return 1, 'Cancelled by user'

        # wait for subprocess to finish, process.wait() is not recommended
        process.communicate()

        # get return code
        process.poll()
        error = process.returncode != 0  # True or False

    except Exception as e:
        log('error running command: ', e, ' - cmd:', cmd)

    return error, output


def print_object(obj):
    if obj is None:
        print(obj, 'is None')
        return
    for k, v in vars(obj).items():
        try:
            print(k, '=', v)
        except:
            pass


def update_object(obj, new_values):
    """update an object attributes from a supplied dictionary"""
    # avoiding obj.__dict__.update(new_values) as it will set a new attribute if it doesn't exist

    for k, v in new_values.items():
        if hasattr(obj, k):
            try:
                setattr(obj, k, v)
            except AttributeError:  # in case of read only attribute
                log(f"update_object(): can't update property: {k}, with value: {v}")
            except Exception as e:
                log(f'update_object(): error, {e}, property: {k}, value: {v}')
    return obj


def truncate(string, length):
    """truncate a string to specified length by adding ... in the middle of the string"""
    # print(len(string), string)
    sep = '...'
    if length < len(sep) + 2:
        string = string[:length]
    elif len(string) > length:
        part = (length - len(sep)) // 2
        remainder = (length - len(sep)) % 2
        string = string[:part + remainder] + sep + string[-part:]
    # print(len(string), string)
    return string


def sort_dictionary(dictionary, descending=True):
    return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[0], reverse=descending)}


def translate_server_code(code):
    """Lookup server code and return a readable code description"""
    server_codes = {

        # Informational.
        100: ('continue',),
        101: ('switching_protocols',),
        102: ('processing',),
        103: ('checkpoint',),
        122: ('uri_too_long', 'request_uri_too_long'),
        200: ('ok', 'okay', 'all_ok', 'all_okay', 'all_good', '\\o/', '✓'),
        201: ('created',),
        202: ('accepted',),
        203: ('non_authoritative_info', 'non_authoritative_information'),
        204: ('no_content',),
        205: ('reset_content', 'reset'),
        206: ('partial_content', 'partial'),
        207: ('multi_status', 'multiple_status', 'multi_stati', 'multiple_stati'),
        208: ('already_reported',),
        226: ('im_used',),

        # Redirection.
        300: ('multiple_choices',),
        301: ('moved_permanently', 'moved', '\\o-'),
        302: ('found',),
        303: ('see_other', 'other'),
        304: ('not_modified',),
        305: ('use_proxy',),
        306: ('switch_proxy',),
        307: ('temporary_redirect', 'temporary_moved', 'temporary'),
        308: ('permanent_redirect',),

        # Client Error.
        400: ('bad_request', 'bad'),
        401: ('unauthorized',),
        402: ('payment_required', 'payment'),
        403: ('forbidden',),
        404: ('not_found', '-o-'),
        405: ('method_not_allowed', 'not_allowed'),
        406: ('not_acceptable',),
        407: ('proxy_authentication_required', 'proxy_auth', 'proxy_authentication'),
        408: ('request_timeout', 'timeout'),
        409: ('conflict',),
        410: ('gone',),
        411: ('length_required',),
        412: ('precondition_failed', 'precondition'),
        413: ('request_entity_too_large',),
        414: ('request_uri_too_large',),
        415: ('unsupported_media_type', 'unsupported_media', 'media_type'),
        416: ('requested_range_not_satisfiable', 'requested_range', 'range_not_satisfiable'),
        417: ('expectation_failed',),
        418: ('im_a_teapot', 'teapot', 'i_am_a_teapot'),
        421: ('misdirected_request',),
        422: ('unprocessable_entity', 'unprocessable'),
        423: ('locked',),
        424: ('failed_dependency', 'dependency'),
        425: ('unordered_collection', 'unordered'),
        426: ('upgrade_required', 'upgrade'),
        428: ('precondition_required', 'precondition'),
        429: ('too_many_requests', 'too_many'),
        431: ('header_fields_too_large', 'fields_too_large'),
        444: ('no_response', 'none'),
        449: ('retry_with', 'retry'),
        450: ('blocked_by_windows_parental_controls', 'parental_controls'),
        451: ('unavailable_for_legal_reasons', 'legal_reasons'),
        499: ('client_closed_request',),

        # Server Error.
        500: ('internal_server_error', 'server_error', '/o\\', '✗'),
        501: ('not_implemented',),
        502: ('bad_gateway',),
        503: ('service_unavailable', 'unavailable'),
        504: ('gateway_timeout',),
        505: ('http_version_not_supported', 'http_version'),
        506: ('variant_also_negotiates',),
        507: ('insufficient_storage',),
        509: ('bandwidth_limit_exceeded', 'bandwidth'),
        510: ('not_extended',),
        511: ('network_authentication_required', 'network_auth', 'network_authentication'),
    }

    return server_codes.get(code, ' ')[0]


def validate_url(url):
    # below pattern is not tested as a starter it doesn't recognize www. urls
    # improvement required
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    match = re.match(pattern, url)
    if match:
        return True
    else:
        return False


def open_file(file):
    try:
        if config.operating_system == 'Windows':
            os.startfile(file)

        elif config.operating_system == 'Linux':
            cmd = f'xdg-open "{file}"'
            subprocess.Popen(shlex.split(cmd))

        elif config.operating_system == 'Darwin':
            cmd = f'open "{file}"'
            subprocess.Popen(shlex.split(cmd))
    except Exception as e:
        log('open_file(): ', e, log_level=2)


def open_folder(path):
    """
    open target folder in file manager and select the file if path is file
    :param path: path to folder or file
    :return: None
    """

    log('utils> open_folder()> ', path, log_level=2)
    try:
        if os.path.isdir(path):
            file = None
            folder = path
        elif os.path.isfile(path):
            file = path
            folder = os.path.dirname(path)
        else:
            # try parent folder
            file = None
            folder = os.path.dirname(path)
            print(folder)

        if config.operating_system == 'Windows':
            if file:
                # open folder and select the file
                cmd = f'explorer /select, "{file}"'
                subprocess.Popen(shlex.split(cmd))
            else:
                os.startfile(folder)

        else:
            # linux
            cmd = f'xdg-open "{folder}"'
            subprocess.Popen(shlex.split(cmd))
    except Exception as e:
        log('utils> open_folder()> ', e, log_level=2)
        if config.TEST_MODE:
            raise e


def compare_versions(x, y):  # todo: use version_value instead
    """it will compare 2 version numbers and return the higher value
    example compare_versions('2020.10.6', '2020.3.7') will return '2020.10.6'
    return None if 2 versions are equal
    """
    try:
        a = [int(x) for x in x.split('.')[:3]]
        b = [int(x) for x in y.split('.')[:3]]

        for i in range(3):
            if a[i] > b[i]:
                return x
            elif a[i] < b[i]:
                return y
    except:
        pass

    return None


def load_json(file=None):
    try:
        with open(file, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        log('load_json() > error: ', e)
        return None


def save_json(file=None, data=None):
    try:
        with open(file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        log('save_json() > error: ', e)


def log_recorder():
    """write log to disk in real-time"""
    q = config.log_recorder_q
    buffer = ''
    file = os.path.join(config.sett_folder, 'log.txt')

    # clear previous file
    with open(file, 'w') as f:
        f.write(buffer)

    while True:
        time.sleep(0.1)
        if config.terminate:
            break

        # read log messages from queue
        for _ in range(q.qsize()):
            buffer += q.get()

        # write buffer to file
        if buffer:
            try:
                with open(file, 'a', encoding="utf-8", errors="ignore") as f:
                    f.write(buffer)
                    buffer = ''  # reset buffer
            except Exception as e:
                print('log_recorder()> error:', e)


def natural_sort(my_list):
    """ Sort the given list in the way that humans expect.
    source: https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/	"""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(my_list, key=alphanum_key)


def get_thumbnail(url):
    """download video thumbnail
    Args:
        url (str): http url of thumbnail image

    Returns:
        BytesIO object contains thumbnail image data
    """
    try:
        log('downloading Thumbnail', log_level=2)
        buffer = download(url, verbose=False)  # get BytesIO object

        return buffer
    except:
        log('downloading Thumbnail failed', log_level=2)


def download_thumbnail(url, fp):
    """download thumbnail

    Args:
        url (str): thumbnail url link
        fp (str): file path
    """

    try:
        buffer = get_thumbnail(url)
        img = Image.open(buffer)
        img.save(fp)
        log('Thumbnail saved to:', fp)
    except Exception as e:
        log('Saving Thumbnail failed', log_level=2)


def resize_image(img=None, buffer=None, size=None):
    """resize image
    Args:
        img (Image): pillow image object
        buffer (io.BytesIO): or any file like object
        size (2-tuple(int, int)): an image required size in a (width, height) tuple

    Returns:
        pillow image object
    """
    if not img and buffer:
        img = Image.open(buffer)

    if size:
        img = img.resize(size, resample=Image.LANCZOS)
    return img


def image_to_base64(img):
    """convert pillow image object to base64"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')

    return base64.b64encode(buffer.getvalue())


def parse_bytes(bytestr):
    """Parse a string indicating a byte quantity into an integer., example format: 536.71KiB, 31.5 mb, etc...
    modified from original source at youtube-dl.common"""

    try:
        # if input value is int return it as it is
        if isinstance(bytestr, int):
            return bytestr

        # remove spaces from string
        bytestr = bytestr.replace(' ', '').lower()

        matchobj = re.match(r'(?i)^(\d+(?:\.\d+)?)([kMGTPEZY]\S*)?$', bytestr)
        if matchobj is None:
            return 0
        number = float(matchobj.group(1))
        unit = matchobj.group(2).lower()[0:1] if  matchobj.group(2) else ''
        multiplier = 1024.0 ** 'bkmgtpezy'.index(unit)
        return int(round(number * multiplier))
    except:
        return 0


def version_value(text):
    """
    convert date based version number into date object for comparision purpose
    :param text: version with dot separated digits i.e. "2020.4.27"
    :return: datetime.date
    """

    try:
        # calculate how many days as a value
        year, month, day = [int(x) for x in text.split('.')]
        # return year * 366 + month * 30.5 + day
        return datetime.date(year, month, day)
    except:
        return 0


def reset_queue(q):
    """clear all contents of queue by dummy reading contents"""
    for _ in range(q.qsize()):
        _ = q.get()


def is_pkg_exist(pkg):
    if importlib.util.find_spec(pkg) is not None:
        return True
    else:
        return False


def auto_rename(file_name, parent_folder):
    """
    rename file to avoid clash with existing file name
    :param file_name: file name without path
    :param parent_folder: path to parent folder, used to verify name doesn't exist
    :return: new name without path
    """

    name, ext = os.path.splitext(file_name)

    file_list = os.listdir(parent_folder)

    new_name = file_name

    for i in range(2, 1000000):
        new_name = f'{name}_{i}{ext}'
        if new_name not in file_list:
            break

    return new_name


def calc_md5(file_name=None, buffer=None):
    try:
        if file_name:
            buffer = open(file_name, 'rb')

        md5 = hashlib.md5(buffer.read()).hexdigest()
        if file_name:
            buffer.close()

        return md5
    except Exception as e:
        return f'calc_md5()> error, {str(e)}'


def calc_sha256(file_name=None, buffer=None):
    try:
        if file_name:
            buffer = open(file_name, 'rb')

        sha256 = hashlib.sha256(buffer.read()).hexdigest()
        if file_name:
            buffer.close()

        return sha256
    except Exception as e:
        return f'calc_sha256()> error, {str(e)}'


def get_range_list(file_size):
    """
    return a list of ranges depend on config.segment_size and config.max_connections
    :param file_size: file size
    :return: list of ranges i.e. [[0, 100], [101, 2000], ... ]
    """

    if file_size == 0:
        return [None]

    range_list = []  # size_splitter(self.size, self.segment_size)
    max_seg_nums = file_size // config.segment_size or 1
    seg_nums = min(max_seg_nums, config.max_connections)
    seg_size = file_size // seg_nums

    start = 0
    end = 0
    for i in range(seg_nums):
        start = 0 if i == 0 else start + seg_size
        end = start + seg_size - 1 if i < seg_nums - 1 else file_size - 1

        range_list.append([start, end])

    return range_list


char_map = {
    # mapping for rendering arabic letters on linux
        '\u0628': '\ufe91',
        '\u062A': '\ufe97',
        '\u062B': '\ufe9b',
        '\u062C': '\ufe9f',
        '\u062d': '\ufea3',
        '\u062e': '\ufeA7',
        '\u0633': '\ufeb3',
        '\u0634': '\ufeb7',
        '\u0635': '\ufebb',
        '\u0636': '\ufebf',
        '\u0637': '\ufec3',
        '\u0638': '\ufec7',
        '\u0639': '\ufeCb',
        '\u063A': '\ufeCF',
        '\u0641': '\ufeD3',
        '\u0642': '\ufeD7',
        '\u0643': '\ufeDb',
        '\u0644': '\ufedf',
        '\u0645': '\ufee3',
        '\u0646': '\ufee7',
        '\u0647': '\ufeeb',
        '\u064A': '\ufef3',
        '\u0626': '\ufe8b'
        }


def arabic_renderer(msg):
    """Takes a mix of english and arabic sentences and render arabic only
    Parts of This fix is inspired by "Rani Fayez Ahmad" at
    https://wiki.tcl-lang.org/page/Arabic+Character+Renderer+For+Readability+In+TCL%2FTk"""

    def is_arabic_word(word):
        if [x for x in word if x in char_map]:
            return True
        else:
            return False

    def process_sentence(words):
        """takes list of arabic words and return it as a rendered joined sentence"""
        # handle each word
        for n, word in enumerate(words):
            letters = list(word)

            # replace letters with open type
            for i, letter in enumerate(letters[:-1]):
                letters[i] = char_map.get(letter) or letter
            
            # join word letters
            word = ''.join(reversed(letters)) 
            words[n] = word
        
        processed_msg = ' '.join(reversed(words)) 
        return processed_msg

    processed = []

    # split to words
    words = msg.split()

    # group sentences in case of mixing arabic with english
    buffer = []
    for word in words:
        if is_arabic_word(word):
            buffer.append(word)
        else:
            if buffer:
                processed.append(process_sentence(buffer))
                # sentences.append(buffer)
                buffer = []
      
            processed.append(word)
  
    # for arabic at the end
    if buffer:
        processed.append(process_sentence(buffer))

    return ' '.join(processed)


def run_thread(f, *args, daemon=True, **kwargs):
    """run a callable in a thread

    Args:
        f (callable): any callable need to be run in a thread
        args: f's args
        daemon (bool): Daemon threads are abruptly stopped at shutdown. Their resources (such as open files,
                      database transactions, etc.) may not be released properly. If you want your threads to stop
                      gracefully, make them non-daemonic and use a suitable signalling mechanism
        kwargs: f's kwargs

    Example:
        def foo(name, greetings='hello'):
            print(greetings, name)

        run_thread(foo, 'John', greetings='hi')

    Returns:
        a thread reference
    """

    t = Thread(target=f, args=args, kwargs=kwargs, daemon=daemon)
    t.start()

    return t


def generate_unique_name(*args, prefix='', suffix=''):
    """generate unique name from any number of parameters which have a string representation

    Args:
        args: any arguments that have a string representation
        prefix (str): concatenated at the begining of hashed value
        suffix (str): concatenated at the end of hashed value

    Example:
        generate_unique_name('duck can quack', 'cat', prefix='uid')
        >>  uid159e7e2ca7a89ee77348f97b4660e56e

    """

    def get_md5(binary_data):
        return hashlib.md5(binary_data).hexdigest()

    name = ''.join([str(x) for x in args])

    try:
        name = get_md5(name.encode())
    except:
        pass

    return prefix + name + suffix


def open_log_file():
    """open log file located in settings folder"""
    file = os.path.join(config.sett_folder, 'log.txt')
    open_file(file)


def open_webpage(url):
    """open webpage in default browser
    Args:
        url(str): webpage url
    """
    try:
        webbrowser.open_new(url)
    except Exception as e:
        log('utils.open_webpage()> error:', e)


__all__ = [
    'notify', 'handle_exceptions', 'get_headers', 'download', 'size_format', 'time_format', 'log', 'validate_file_name',
    'size_splitter', 'delete_folder', 'get_seg_size', 'run_command', 'print_object', 'update_object', 'truncate',
    'sort_dictionary', 'compare_versions', 'translate_server_code', 'validate_url', 'open_file', 'delete_file',
    'rename_file', 'load_json', 'save_json', 'echo_stdout', 'echo_stderr', 'log_recorder', 'natural_sort', 'is_pkg_exist',
    'parse_bytes', 'set_curl_options', 'version_value',
    'reset_queue', 'open_folder', 'auto_rename', 'calc_md5',
    'calc_sha256', 'get_range_list', 'arabic_renderer', 'get_thumbnail', 'resize_image', 'run_thread', 'generate_unique_name',
    'open_log_file', 'open_webpage', 'download_thumbnail'

]
