"""
    pyIDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2020 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""
import os
import time
from threading import Thread
import concurrent.futures

from .video import merge_video_audio, pre_process_hls, post_process_hls, \
    convert_audio, download_subtitles, write_metadata
from . import config
from .config import Status, APP_NAME
from .utils import (log, size_format, notify, delete_file, rename_file, calc_md5_sha256, run_command)
from .worker import Worker
from .downloaditem import Segment


def brain(d=None):
    """main brain for a single download, it controls thread manger, file manager
    """

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
    log(f'start downloading file: "{d.name}", size: {size_format(d.total_size)}, to: {d.folder} \n')

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
            log(f'brain {d.uid}: Cancelled download')
            break
        elif d.status == Status.error:
            log(f'brain {d.uid}: download error')
            break

    # report quitting
    log(f'brain {d.uid}: quitting', log_level=2)

    if d.status == Status.completed:
        if config.checksum:
            log()
            log(f'Calculating MD5 and SHA256 for {d.target_file} .....')
            md5, sha256 = calc_md5_sha256(fp=d.target_file)
            log(f'MD5: {md5} - for {d.name}')
            log(f'SHA256: {sha256} - for {d.name}')

        # uncomment to debug segments ranges
        # segments = sorted([seg for seg in d.segments], key=lambda seg: seg.range[0])
        # print('d.size:', d.size)
        # for seg in segments:
        #     print(seg.basename, seg.range, seg.range[1] - seg.range[0], seg.size, seg.remaining)

    log('=' * 106, '\n')


def file_manager(d, keep_segments=True):
    """write downloaded segments to a single file, and report download completed"""

    # create temp folder if it doesn't exist
    if not os.path.isdir(d.temp_folder):
        os.mkdir(d.temp_folder)

    # create temp files, needed for future opening in 'rb+' mode otherwise it will raise file not found error
    temp_files = set([seg.tempfile for seg in d.segments])
    for file in temp_files:
        open(file, 'ab').close()

    while True:
        time.sleep(0.1)

        job_list = [seg for seg in d.segments if not seg.completed]

        # sort segments based on ranges, faster in writing to target file
        if job_list and job_list[0].range:
            job_list = sorted(job_list, key=lambda seg: seg.range[0])

        for seg in job_list:

            # for segments which have no range, it must be appended to temp file in order, or final file will be
            # corrupted, therefore if the first non completed segment is not "downloaded", will exit loop
            if not seg.downloaded:
                if not seg.range:
                    break
                else:
                    continue

            # append downloaded segment to temp file, mark as completed
            try:
                if seg.merge:

                    # use 'rb+' mode if we use seek, 'ab' doesn't work, 'rb+' will raise error if file doesn't exist
                    # open/close target file with every segment will avoid operating system buffering,
                    # which cause almost 90 sec wait on some windows machine to be able to rename the file, after close it
                    # fd.flush() and os.fsync(fd) didn't solve the problem
                    with open(seg.name, 'rb') as src_file:
                        if seg.range:
                            target_file = open(seg.tempfile, 'rb+')
                            # must seek exact position, segments are not in order for simple append
                            target_file.seek(seg.range[0])

                            # read the exact segment size, sometimes segment has extra data as a side effect from auto segmentation
                            contents = src_file.read(seg.size)
                        else:
                            target_file = open(seg.tempfile, 'ab')
                            contents = src_file.read()

                        # write data
                        target_file.write(contents)

                        # close file
                        target_file.close()

                seg.completed = True
                log('completed segment: ',  seg.basename, log_level=2)

                if not keep_segments and not config.keep_temp:
                    delete_file(seg.name)

            except Exception as e:
                log('failed to merge segment', seg.name, ' - ', e)
                if config.TEST_MODE:
                    raise e

        # all segments already merged
        if not job_list:

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
                output_file = d.target_file 

                # set status to processing
                d.status = Status.processing
                error, output = merge_video_audio(d.temp_file, d.audio_file, output_file, d)

                if not error:
                    log('done merging video and audio for: ', d.target_file)

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
                # final / target file might be created by ffmpeg in case of dash video for example
                if os.path.isfile(d.target_file):
                    # delete temp files
                    d.delete_tempfiles()
                else:
                    # rename temp file
                    success = rename_file(d.temp_file, d.target_file)
                    if success:
                        # delete temp files
                        d.delete_tempfiles()

            # download subtitles
            if d.selected_subtitles:
                Thread(target=download_subtitles, args=(d.selected_subtitles, d)).start()

            # if type is subtitle, will convert vtt to srt
            if d.type == 'subtitle' and 'hls' not in d.subtype_list and d.name.endswith('srt'):
                # ffmpeg file full location
                ffmpeg = config.ffmpeg_actual_path

                input_file = d.target_file
                output_file = f'{d.target_file}2.srt'  # must end with srt for ffmpeg to recognize output format

                log('verifying "srt" subtitle:', input_file)
                cmd = f'"{ffmpeg}" -y -i "{input_file}" "{output_file}"'

                error, _ = run_command(cmd, verbose=True)
                if not error:
                    delete_file(d.target_file)
                    rename_file(oldname=output_file, newname=input_file)
                    log('verified subtitle successfully:', input_file)
                else:
                    # if failed to convert
                    log("couldn't convert subtitle to srt, check file format might be corrupted")

            # write metadata
            if d.metadata_file_content and config.write_metadata:
                log('file manager()> writing metadata info to:', d.name)
                # create metadata file
                metadata_filename = d.target_file + '.meta'

                try:
                    with open(metadata_filename, 'w') as f:
                        f.write(d.metadata_file_content)

                    # let ffmpeg write metadata to file
                    write_metadata(d.target_file, metadata_filename)

                except Exception as e:
                    log('file manager()> writing metadata error:', e)

                finally:
                    # delete meta file
                    delete_file(metadata_filename)

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
    log(f'file_manager {d.uid}: quitting', log_level=2)


def thread_manager(d):
    """create multiple worker threads to download file segments"""

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

    log('Thread Manager()> concurrency method:', 
        'ThreadPoolExecutor' if config.use_thread_pool_executor else 'Individual Threads', 
        log_level=2)

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
                log('Errors:', errors_descriptions, 'Total:', total_errors)
                # log('Errors descriptions:', errors_descriptions, log_level=3)

            if total_errors >= 1 and limited_connections > 1:
                limited_connections -= 1
                conn_increase_interval += 0.5
                log('Thread Manager: received server errors, connections limited to:', limited_connections)

            else:
                if limited_connections < config.max_connections and time.time() - error_timer2 >= conn_increase_interval:
                    error_timer2 = time.time()
                    limited_connections += 1
                    log('Thread Manager: allowable connections:', limited_connections, log_level=2)

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

                        # range boundaries
                        start = current_seg.range[0]
                        middle = start + current_seg.remaining // 2
                        end = current_seg.range[1]

                        # assign new range for current segment
                        current_seg.range = [start, middle]

                        # create new segment
                        seg = Segment(name=os.path.join(d.temp_folder, f'{len(d.segments)}'), url=current_seg.url,
                                      tempfile=current_seg.tempfile, range=[middle + 1, end],
                                      media_type=current_seg.media_type)

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
    log(f'thread_manager {d.uid}: quitting', log_level=2)
