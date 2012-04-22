import os, ctypes, time

PCO_api = ctypes.oledll.LoadLibrary("SC2_Cam")
"""Requires sc2_cl_me4.dll to be in the same directory.
If you get a WindowsError, read PCO_err.h to decypher it."""

libc = ctypes.cdll.msvcrt
libc.fopen.restype = ctypes.c_void_p

def open_camera():
    camera_handle = ctypes.c_ulong()
    print "Opening camera..."
    PCO_api.PCO_OpenCamera(ctypes.byref(camera_handle), 0)
    wRecState = ctypes.c_uint16(0) #Turn off recording
    PCO_api.PCO_SetRecordingState(camera_handle, wRecState)
    print " Camera handle:", camera_handle.value
    return camera_handle

def apply_settings(camera_handle, trigger='auto trigger'):
    PCO_api.PCO_ResetSettingsToDefault(camera_handle)

    wSensor = ctypes.c_uint16(0)
    print "Setting sensor format..."
    PCO_api.PCO_SetSensorFormat(camera_handle, wSensor)
    PCO_api.PCO_GetSensorFormat(camera_handle, ctypes.byref(wSensor))
    mode_names = {0: "standard", 1:"extended"}
    print " Sensor format is", mode_names[wSensor.value]

    print "Getting camera health status..."
    dwWarn, dwErr, dwStatus = (
        ctypes.c_uint32(), ctypes.c_uint32(), ctypes.c_uint32())
    PCO_api.PCO_GetCameraHealthStatus(
        camera_handle,
        ctypes.byref(dwWarn), ctypes.byref(dwErr), ctypes.byref(dwStatus))
    print " Camera health status (0 0 0 means healthy):",
    print dwWarn.value, dwErr.value, dwStatus.value

    print "Reading temperatures..."
    ccdtemp, camtemp, powtemp = (
        ctypes.c_short(), ctypes.c_short(), ctypes.c_short())
    PCO_api.PCO_GetTemperature(
        camera_handle,
        ctypes.byref(ccdtemp), ctypes.byref(camtemp), ctypes.byref(powtemp))
    print " CCD temperature:", ccdtemp.value * 0.1, "C"
    print " Camera temperature:", camtemp.value, "C"
    print " Power supply temperature:", powtemp.value, "C"

    """
    0x0000 = [auto trigger]
    A new image exposure is automatically started best possible
    compared to the readout of an image. If a CCD is used and the
    images are taken in a sequence, then exposures and sensor readout
    are started simultaneously. Signals at the trigger input (<exp
    trig>) are irrelevant.
    - 0x0001 = [software trigger]:
    An exposure can only be started by a force trigger command.
    - 0x0002 = [extern exposure & software trigger]:
    A delay / exposure sequence is started at the RISING or FALLING
    edge (depending on the DIP switch setting) of the trigger input
    (<exp trig>).
    - 0x0003 = [extern exposure control]:
    The exposure time is defined by the pulse length at the trigger
    input(<exp trig>). The delay and exposure time values defined by
    the set/request delay and exposure command are ineffective.
    (Exposure time length control is also possible for double image
    mode; exposure time of the second image is given by the readout
    time of the first image.)
    """
    mode_names = {0: "auto trigger",
                  1: "software trigger",
                  2: "external trigger/software exposure control",
                  3: "external exposure control"}
    mode_name_to_number = dict((v,k) for k, v in mode_names.iteritems())
    print "Setting trigger mode..."
    wTriggerMode = ctypes.c_uint16(mode_name_to_number[trigger])
    PCO_api.PCO_SetTriggerMode(camera_handle, wTriggerMode)
    PCO_api.PCO_GetTriggerMode(camera_handle, ctypes.byref(wTriggerMode))
    print " Trigger mode is", mode_names[wTriggerMode.value]

    wStorageMode = ctypes.c_uint16()
    PCO_api.PCO_GetStorageMode(camera_handle, ctypes.byref(wStorageMode))
    mode_names = {0: "Recorder", 1: "FIFO buffer"} #Not critical for pco.edge
    print "Storage mode:", mode_names[wStorageMode.value]

    print "Setting recorder submode..."
    wRecSubmode = ctypes.c_uint16(0)
    PCO_api.PCO_SetRecorderSubmode(camera_handle, wRecSubmode)
    PCO_api.PCO_GetRecorderSubmode(camera_handle, ctypes.byref(wRecSubmode))
    mode_names = {0: "sequence", 1: "ring buffer"}
    print " Recorder submode:", mode_names[wRecSubmode.value]

    print "Setting acquire mode..."
    wAcquMode = ctypes.c_uint16(0)
    PCO_api.PCO_SetAcquireMode(camera_handle, wAcquMode)
    PCO_api.PCO_GetAcquireMode(camera_handle, ctypes.byref(wAcquMode))
    mode_names = {0: "auto", 1:"external (static)", 2:"external (dynamic)"}
    print " Acquire mode:", mode_names[wAcquMode.value]

    print "Setting pixel rate..."
    dwPixelRate = ctypes.c_uint32(286000000)
    PCO_api.PCO_SetPixelRate(camera_handle, dwPixelRate)
    PCO_api.PCO_GetPixelRate(camera_handle, ctypes.byref(dwPixelRate))
    print " Pixel rate:", dwPixelRate.value

    print "Setting delay and exposure time..."
    dwDelay = ctypes.c_uint32(0)
    wTimeBaseDelay = ctypes.c_uint16(0)
    dwExposure = ctypes.c_uint32(2200)
    wTimeBaseExposure = ctypes.c_uint16(1)
    PCO_api.PCO_SetDelayExposureTime(
        camera_handle, dwDelay, dwExposure, wTimeBaseDelay, wTimeBaseExposure)
    PCO_api.PCO_GetDelayExposureTime(
        camera_handle,
        ctypes.byref(dwDelay), ctypes.byref(dwExposure),
        ctypes.byref(wTimeBaseDelay), ctypes.byref(wTimeBaseExposure))
    mode_names = {0: "nanoseconds", 1: "microseconds", 2: "milliseconds"}
    print " Exposure:", dwExposure.value, mode_names[wTimeBaseExposure.value]
    print " Delay:", dwDelay.value, mode_names[wTimeBaseDelay.value]

    wRoiX0, wRoiY0, wRoiX1, wRoiY1 = (
        ctypes.c_uint16(961), ctypes.c_uint16(841),
        ctypes.c_uint16(1440), ctypes.c_uint16(1320))
    print "Setting sensor ROI..."
    PCO_api.PCO_SetROI(camera_handle, wRoiX0, wRoiY0, wRoiX1, wRoiY1)
    PCO_api.PCO_GetROI(camera_handle,
                       ctypes.byref(wRoiX0), ctypes.byref(wRoiY0),
                       ctypes.byref(wRoiX1), ctypes.byref(wRoiY1))
    print " Camera ROI:"
    """We typically use 841 to 1320 u/d, 961 to 1440 l/r"""
    print "  From pixel", wRoiX0.value, "to pixel", wRoiX1.value, "(left/right)"
    print "  From pixel", wRoiY0.value, "to pixel", wRoiY1.value, "(up/down)"
    print

    return None

def record_to_file(camera_handle, num_images, num_buffers=2,
                   file_name='image.raw', save_path=None, verbose=False):

    if save_path is None:
        save_path = os.getcwd()
    print "Arming camera..."        
    PCO_api.PCO_ArmCamera(camera_handle)
    wXRes, wYRes, wXResMax, wYResMax = (
        ctypes.c_uint16(), ctypes.c_uint16(),
        ctypes.c_uint16(), ctypes.c_uint16())
    PCO_api.PCO_GetSizes(camera_handle,
                         ctypes.byref(wXRes), ctypes.byref(wYRes),
                         ctypes.byref(wXResMax), ctypes.byref(wYResMax))
    if verbose:
        print "Camera ROI dimensions:",
        print wXRes.value, "(l/r) by", wYRes.value, "(u/d)"

    dwSize = ctypes.c_uint32(wXRes.value * wYRes.value * 2)
    sBufNr, wBuf, event_handle = [], [], []
    for i in range(num_buffers):
        sBufNr.append(ctypes.c_int16(-1))
        wBuf.append(ctypes.c_ulong(0))
        event_handle.append(ctypes.c_ulong(0))
        PCO_api.PCO_AllocateBuffer(
            camera_handle, ctypes.byref(sBufNr[i]), dwSize,
            ctypes.byref(wBuf[i]), ctypes.byref(event_handle[i]))
        if verbose:
            print "Buffer number", sBufNr[i].value, "is at address", wBuf[i],
            print "linked to an event containing:", event_handle[i].value

    PCO_api.PCO_CamLinkSetImageParameters(camera_handle, wXRes, wYRes)

    wRecState = ctypes.c_uint16(1)
    PCO_api.PCO_SetRecordingState(camera_handle, wRecState)

    dw1stImage, dwLastImage = ctypes.c_uint32(0), ctypes.c_uint32(0)
    wBitsPerPixel = ctypes.c_uint16(14) #14 bits for the pco.edge, right?
    dwStatusDll, dwStatusDrv = ctypes.c_uint32(), ctypes.c_uint32()
    file_pointer = ctypes.c_void_p(
        libc.fopen(os.path.join(save_path, file_name), "wb"))
    bytes_per_pixel = ctypes.c_uint32(2)
    pixels_per_image = ctypes.c_uint32(wXRes.value*wYRes.value)
    for which_im in range(num_images):
        which_buf = which_im % num_buffers
        PCO_api.PCO_AddBufferEx(
            camera_handle, dw1stImage, dwLastImage, sBufNr[which_buf],
            wXRes, wYRes, wBitsPerPixel)
        
        num_polls = 0
        while True:
            num_polls += 1
            PCO_api.PCO_GetBufferStatus(
                camera_handle, sBufNr[which_buf],
                ctypes.byref(dwStatusDll), ctypes.byref(dwStatusDrv))
            time.sleep(0.00005) #50 microseconds
            if dwStatusDll.value == 0xc0008000:
                if verbose:
                    print "After", num_polls, "polls, buffer",
                    print sBufNr[which_buf].value, "is ready."
                break

        response = libc.fwrite(
            wBuf[which_buf], bytes_per_pixel, pixels_per_image, file_pointer)
        if response != pixels_per_image.value:
            raise UserWarning("Not enough data written to image file.")

    libc.fclose(file_pointer)
    file_info = open(
        os.path.splitext(os.path.join(save_path, file_name))[0] + '.txt', 'wb')
    file_info.write('Left/right: %i pixels\r\n'%(wXRes.value))
    file_info.write('Up/down: %i pixels\r\n'%(wYRes.value))
    file_info.write('Number of images: %i\r\n'%(num_images))
    file_info.write('Data type: 16-bit unsigned integers\r\n')
    file_info.write('Byte order: Intel (little-endian)')
    file_info.close()

    print num_images, "images recorded. Ending recording..."
    wRecState = ctypes.c_uint16(0)
    PCO_api.PCO_SetRecordingState(camera_handle, wRecState)
    for buf in sBufNr:
        PCO_api.PCO_FreeBuffer(camera_handle, buf)


def close_camera(camera_handle):
    PCO_api.PCO_CloseCamera(camera_handle)
    print "Camera closed."

if __name__ == "__main__":
    camera_handle = open_camera()
    apply_settings(camera_handle)
    record_to_file(camera_handle, num_images=120)
    close_camera(camera_handle)
