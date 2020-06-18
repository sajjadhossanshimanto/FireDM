"""
    pyIDM

    multi-connections internet download manager, based on "pyCuRL/curl", "youtube_dl", and "PySimpleGUI"

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""
import io
import os
import time
from threading import Thread
import concurrent.futures

from .video import merge_video_audio, unzip_ffmpeg, pre_process_hls, post_process_hls, \
    convert_audio, download_subtitles  # unzip_ffmpeg required here for ffmpeg callback
from . import config
from .config import Status, active_downloads, APP_NAME
from .utils import (log, size_format, popup, notify, delete_folder, delete_file, rename_file, load_json, save_json,
                    print_object, calc_md5, calc_sha256)
from .worker import Worker
from .downloaditem import Segment


def brain(d=None, downloader=None):
    """main brain for a single download, it controls thread manger, file manager, and get data from workers
    and communicate with download window Gui, Main frame gui"""

    # set status
    if d.status == Status.downloading:
        log('another brain thread may be running')
        return
    else:
        d.status = Status.downloading

    # first we will remove temp files because file manager is appending segments blindly to temp file
    delete_file(d.temp_file)
    delete_file(d.audio_file)

    # reset downloaded
    d.downloaded = 0

    log('\n')
    log('=' * 106)
    log(f'start downloading file: "{d.name}", size: {size_format(d.total_size)}, to: {d.folder}')

    # hls / m3u8 protocols
    if 'hls' in d.subtype_list:
        keep_segments = True  # don't delete segments after completed, it will be post-processed by ffmpeg
        try:
            success = pre_process_hls(d)
            if not success:
                d.status = Status.error
                return
        except Exception as e:
            d.status = Status.error
            log('pre_process_hls()> error: ', e, showpopup=True)
            if config.TEST_MODE:
                raise e
            return
    else:
        # for non hls videos and normal files
        keep_segments = True  # False

        # build segments
        d.build_segments()

    # load progress info
    d.load_progress_info()

    # run file manager in a separate thread
    Thread(target=file_manager, daemon=True, args=(d, keep_segments)).start()

    # run thread manager in a separate thread
    Thread(target=thread_manager, daemon=True, args=(d,)).start()

    while True:
        time.sleep(0.1)  # a sleep time to make the program responsive

        if d.status == Status.completed:
            # os notification popup
            notification = f"File: {d.name} \nsaved at: {d.folder}"
            notify(notification, title=f'{APP_NAME} - Download completed')
            log(f'File: "{d.name}", completed.')
            break
        elif d.status == Status.cancelled:
            log(f'brain {d.num}: Cancelled download')
            break
        elif d.status == Status.error:
            log(f'brain {d.num}: download error')
            break

    # todo: should find a better way to handle callback.
    # callback, a method or func "name" to call if download completed, it is stored as a string to be able to save it
    # on disk with other downloaditem parameters
    if d.callback and d.status == Status.completed:
        # d.callback()
        globals()[d.callback]()

    # report quitting
    log(f'brain {d.num}: quitting')

    if d.status == Status.completed:
        if config.checksum:
            log('MD5:', calc_md5(file_name=d.target_file))
            log('SHA256:', calc_sha256(file_name=d.target_file))

        # uncomment to debug segments ranges
        # segments = sorted([seg for seg in d.segments], key=lambda seg: seg.range[0])
        # print('d.size:', d.size)
        # for seg in segments:
        #     print(seg.basename, seg.range, seg.range[1] - seg.range[0], seg.size, seg.remaining)

    log('=' * 106, '\n')


def file_manager(d, keep_segments=True):
    # create temp files
    temp_files = set([seg.tempfile for seg in d.segments])
    for file in temp_files:
        open(file, 'ab').close()

    target_files = {}
    for file in temp_files:
        target_files[file] = open(file, 'rb+')

    while True:
        time.sleep(0.1)

        job_list = [seg for seg in d.segments if not seg.completed]

        # sort segments based on ranges, faster in writing to target file
        if job_list and job_list[0].range:
            job_list = sorted(job_list, key=lambda seg: seg.range[0])

        for seg in job_list:

            # for segments which have no range, it must be appended to temp file in order otherwise final file will be
            # corrupted, therefore if the first non completed segment is not "downloaded", will exit loop
            if not seg.downloaded:
                if not seg.range:
                    break
                else:
                    continue

            # append downloaded segment to temp file, mark as completed
            try:
                if seg.merge:
                    target_file = target_files[seg.tempfile]
                    with open(seg.name, 'rb') as src_file:
                        if seg.range:
                            # use 'rb+' mode if we use seek, 'ab' doesn't work, but it will raise error if file doesn't exist
                            target_file.seek(seg.range[0])
                            contents = src_file.read(seg.size)
                        else:
                            contents = src_file.read()

                    # write data
                    target_file.write(contents)

                    # flush contents, required for watching while downloading feature
                    target_file.flush()

                seg.completed = True
                log('completed segment: ',  seg.basename)

                if not keep_segments and not config.keep_temp:
                    delete_file(seg.name)

            except Exception as e:
                log('failed to merge segment', seg.name, ' - ', e)
                if config.TEST_MODE:
                    raise e

        # all segments already merged
        if not job_list:

            for file_handle in target_files.values():
                file_handle.close()

            # handle HLS streams
            if 'hls' in d.subtype_list:
                log('handling hls videos')
                # Set status to processing
                d.status = Status.processing

                success = post_process_hls(d)
                if not success:
                    d.status = Status.error
                    log('file_manager()>  post_process_hls() failed, file: \n', d.name, showpopup=True)
                    break

            # handle dash video
            if 'dash' in d.subtype_list:
                log('handling dash videos')
                # merge audio and video
                output_file = d.target_file.replace(' ', '_')  # remove spaces from target file

                # set status to processing
                d.status = Status.processing
                error, output = merge_video_audio(d.temp_file, d.audio_file, output_file, d)

                if not error:
                    log('done merging video and audio for: ', d.target_file)

                    rename_file(output_file, d.target_file)

                    # delete temp files
                    d.delete_tempfiles()

                else:  # error merging
                    d.status = Status.error
                    log('failed to merge audio for file: \n', d.name, showpopup=True)
                    break

            # handle audio streams
            if d.type == 'audio':
                log('handling audio streams')
                d.status = Status.processing
                success = convert_audio(d)
                if not success:
                    d.status = Status.error
                    log('file_manager()>  convert_audio() failed, file:', d.target_file, showpopup=True)
                    break
                else:
                    d.delete_tempfiles()

            else:
                rename_file(d.temp_file, d.target_file)
                # delete temp files
                d.delete_tempfiles()

            # download subtitles
            download_subtitles(d.selected_subtitles, d)

            # at this point all done successfully
            d.status = Status.completed
            # print('---------file manager done merging segments---------')
            break

        # change status
        if d.status != Status.downloading:
            # print('--------------file manager cancelled-----------------')
            break

    # save progress info for future resuming
    if os.path.isdir(d.temp_folder):
        d.save_progress_info()

    # Report quitting
    log(f'file_manager {d.num}: quitting')


def thread_manager(d):

    #   soft start, connections will be gradually increase over time to reach max. number
    #   set by user, this prevent impact on servers/network, and avoid "service not available" response
    #   from server when exceeding multi-connection number set by server.
    limited_connections = 1

    # create worker/connection list
    all_workers = [Worker(tag=i, d=d) for i in range(config.max_connections)]
    free_workers = set([w for w in all_workers])
    threads_to_workers = dict()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.max_connections)
    num_live_threads = 0

    # job_list
    job_list = [seg for seg in d.segments if not seg.downloaded]

    # reverse job_list to process segments in proper order use pop()
    job_list.reverse()

    d.remaining_parts = len(job_list)

    # error track, if receive many errors with no downloaded data, abort
    downloaded = 0
    total_errors = 0
    max_errors = 100
    errors_descriptions = set()  # store unique errors
    error_timer = 0
    error_timer2 = 0
    conn_increase_interval = 0.5
    errors_check_interval = 0.2  # in seconds

    # speed limit
    sl_timer = time.time()

    # for compatibility reasons will reset segment size
    config.segment_size = config.DEFAULT_SEGMENT_SIZE

    log('Thread Manager()> concurrency method:', 'ThreadPoolExecutor' if config.use_thread_pool_executor else 'Individual Threads')

    def clear_error_q():
        # clear error queue
        for _ in range(config.error_q.qsize()):
            errors_descriptions.add(config.error_q.get())

    def on_completion_callback(future):
        """add worker to free workers once thread is completed, it will be called by future.add_done_callback()"""
        try:
            free_worker = threads_to_workers.pop(future)
            free_workers.add(free_worker)
        except:
            pass

    while True:
        time.sleep(0.001)  # a sleep time to while loop to make the app responsive

        # Failed jobs returned from workers, will be used as a flag to rebuild job_list --------------------------------
        if config.jobs_q.qsize() > 0:
            # rebuild job_list
            job_list = [seg for seg in d.segments if not seg.downloaded and not seg.locked]
            job_list.reverse()

            # empty queue
            for _ in range(config.jobs_q.qsize()):
                _ = config.jobs_q.get()
                # job_list.append(job)

        # create new workers if user increases max_connections while download is running
        if config.max_connections > len(all_workers):
            extra_num = config.max_connections - len(all_workers)
            index = len(all_workers)
            for i in range(extra_num):
                index += i
                worker = Worker(tag=index, d=d)
                all_workers.append(worker)
                free_workers.add(worker)

            # redefine executor
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.max_connections)

        # allowable connections
        allowable_connections = min(config.max_connections, limited_connections)

        # dynamic connection manager ---------------------------------------------------------------------------------
        # check every n seconds for connection errors
        if time.time() - error_timer >= errors_check_interval:
            error_timer = time.time()
            errors_num = config.error_q.qsize()

            total_errors += errors_num
            d.errors = total_errors  # update errors property of download item

            clear_error_q()

            if total_errors:
                log('--------------------------------- errors ---------------------------------:', total_errors)
                log('Errors descriptions:', errors_descriptions, log_level=3)

            if total_errors >= 1 and limited_connections > 1:
                limited_connections -= 1
                conn_increase_interval += 0.5
                log('Thread Manager: received server errors, connections limited to:', limited_connections)

            else:
                if limited_connections < config.max_connections and time.time() - error_timer2 >= conn_increase_interval:
                    error_timer2 = time.time()
                    limited_connections += 1
                    log('Thread Manager: allowable connections:', limited_connections)

            # reset total errors if received any data
            if downloaded != d.downloaded:
                downloaded = d.downloaded
                # print('reset errors to zero')
                total_errors = 0
                clear_error_q()

            if total_errors >= max_errors:
                d.status = Status.error
                log('Thread manager: too many connection errors', 'maybe network problem or expired link',
                    start='', sep='\n', showpopup=True)

        # speed limit ------------------------------------------------------------------------------------------------
        # wait some time for dynamic connection manager to release all connections
        if time.time() - sl_timer < config.max_connections * errors_check_interval:
            worker_sl = (config.speed_limit // config.max_connections) if config.max_connections else 0
        else:
            # normal calculations
            worker_sl = (config.speed_limit // allowable_connections) if allowable_connections else 0

        # Threads ------------------------------------------------------------------------------------------------------
        if d.status == Status.downloading:
            if free_workers and num_live_threads < allowable_connections:
                seg = None
                if job_list:
                    seg = job_list.pop()
                else:
                    # share segments and help other workers
                    remaining_segs = [seg for seg in d.segments if seg.remaining > config.segment_size]
                    remaining_segs = sorted(remaining_segs, key=lambda seg: seg.remaining)
                    # log('x'*20, 'check remaining')

                    if remaining_segs:
                        current_seg = remaining_segs.pop()
                        size = current_seg.remaining // 2
                        end = current_seg.range[1]
                        current_seg.range = [current_seg.range[0], current_seg.range[0] + size]

                        # create new segment
                        start = current_seg.range[1] + 1
                        seg = Segment(name=os.path.join(d.temp_folder, f'{len(d.segments)}'), url=current_seg.url,
                                      tempfile=current_seg.tempfile, range=[start, end])

                        # add to segments
                        d.segments.append(seg)
                        log('-' * 10, f'new segment {seg.basename} created from {current_seg.basename} '
                                      f'with range {current_seg.range}', log_level=3)

                if seg and not seg.downloaded and not seg.locked:
                    worker = free_workers.pop()
                    # sometimes download chokes when remaining only one worker, will set higher minimum speed and
                    # less timeout for last workers batch
                    if len(job_list) + config.jobs_q.qsize() <= allowable_connections:
                        minimum_speed, timeout = 20 * 1024, 10  # worker will abort if speed less than 20 KB for 10 seconds
                    else:
                        minimum_speed = timeout = None  # default as in utils.set_curl_option

                    ready = worker.reuse(seg=seg, speed_limit=worker_sl, minimum_speed=minimum_speed, timeout=timeout)
                    if ready:
                        if config.use_thread_pool_executor:
                            thread = executor.submit(worker.run)
                            thread.add_done_callback(on_completion_callback)
                        else:
                            thread = Thread(target=worker.run, daemon=True)
                            thread.start()
                        threads_to_workers[thread] = worker

        # check thread completion
        if not config.use_thread_pool_executor:
            for thread in list(threads_to_workers.keys()):
                if not thread.is_alive():
                    worker = threads_to_workers.pop(thread)
                    free_workers.add(worker)

        # update d param -----------------------------------------------------------------------------------------------
        num_live_threads = len(all_workers) - len(free_workers)
        d.live_connections = num_live_threads
        d.remaining_parts = d.live_connections + len(job_list) + config.jobs_q.qsize()

        # Required check if things goes wrong --------------------------------------------------------------------------
        if num_live_threads + len(job_list) + config.jobs_q.qsize() == 0:
            # rebuild job_list
            job_list = [seg for seg in d.segments if not seg.downloaded]
            if not job_list:
                break
            else:
                # remove an orphan locks
                for seg in job_list:
                    seg.locked = False

        # monitor status change ----------------------------------------------------------------------------------------
        if d.status != Status.downloading:
            # shutdown thread pool executor
            executor.shutdown(wait=False)
            break

    # update d param
    d.live_connections = 0
    d.remaining_parts = num_live_threads + len(job_list) + config.jobs_q.qsize()
    log(f'thread_manager {d.num}: quitting')
