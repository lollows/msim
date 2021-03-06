import sys
import time
import Queue
import multiprocessing as mp
import numpy as np

"""
Allows image_data_pipeline.py to use different cameras. For now, only
the pco.edge works. In the future, we'll have multiple definitions of
camera_child_process() depending on what camera we want to use.
"""

log = mp.get_logger()
info = log.info
debug = log.debug
if sys.platform == 'win32':
    clock = time.clock
else:
    clock = time.time

def camera_child_process(
    data_buffers,
    buffer_shape,
    input_queue,
    output_queue,
    commands,
    ):
    """
    This version's suitable for the pco.edge camera.
    """
    buffer_size = np.prod(buffer_shape)
    import pco
    camera = pco.Edge(pco_edge_type='4.2') #Change this if you're using a 5.5
    camera.apply_settings(trigger='auto trigger')
    camera.get_shutter_mode()
    camera.get_settings(verbose=False)
    camera.arm(num_buffers=3)
    camera._prepare_to_record_to_memory()
    preframes = 3
    status = 'Normal'
    timeout = 0
    while True:
        if commands.poll():
            cmd, args = commands.recv()
            if cmd == 'set_buffer_shape':
                buffer_shape = args['shape']
                buffer_size = np.prod(buffer_shape)
                commands.send(buffer_shape)
            elif cmd == 'apply_settings':
                settings = camera.apply_settings(**args)
                camera.arm()
                camera._prepare_to_record_to_memory()
                commands.send(settings)
            elif cmd == 'get_settings':
                commands.send(camera.get_settings(**args))
            elif cmd == 'get_status':
                commands.send(status)
            elif cmd == 'reset_status':
                status = 'Normal'
                commands.send(None)
            elif cmd == 'get_preframes':
                commands.send(preframes)
            elif cmd == 'set_preframes':
                preframes = args['preframes']
                commands.send(preframes)
            elif cmd == 'get_timeout':
                commands.send(timeout)
            elif cmd == 'set_timeout':
                timeout = args['timeout']
                commands.send(timeout)
            continue #ignore commands we don't recognize. Bad idea?
        try:
            permission_slip = input_queue.get_nowait()
        except Queue.Empty:
            time.sleep(0.001)
            continue
        if permission_slip is None:
            break #We're done
        else:
            time_received = clock()
            """Fill the buffer with something"""
            process_me = permission_slip['which_buffer']
            info("start buffer %i"%(process_me))
            with data_buffers[process_me].get_lock():
                a = np.frombuffer(data_buffers[process_me].get_obj(),
                                  dtype=np.uint16)[:buffer_size
                                                   ].reshape(buffer_shape)
                while True:
                    info('Start acquiring:%06f'%clock())
                    try:
                        camera.record_to_memory(
                            num_images=a.shape[0] + preframes,
                            preframes=preframes,
                            out=a)
                    except pco.TimeoutError as e:
                        info('TimeoutError, %i acquired'%(e.num_acquired))
                        status = 'TimeoutError'
                        time_elapsed = clock() - time_received
                        if time_elapsed > timeout:
                            raise UserWarning(
                                "No trigger received, timeout exceeded")
                    except pco.DMAError:
                        info('DMAError')
                        status = 'DMAError'
                        break
                    else:
                        info('Done acquiring:%06f'%clock())
                        status = 'Normal'
                        break
            info("end buffer %i"%(process_me))
            output_queue.put(permission_slip)
    camera.close()
    return None
