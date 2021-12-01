from ctypes import *
import os
import sys
import subprocess
import platform
from os.path import join, pathsep
from enum import Enum
import astropy.units as u
from astropy.io import fits
import time
import numpy as np
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from datetime import datetime, timedelta
import pytz
import astral as a
import ephem
from astropy.time import TimeISO
from astropy.time import Time
import serial
import io
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter


qhyccd=CDLL("qhyccd_x64.dll")
qhyccd.GetQHYCCDParam.restype=c_double
qhyccd.OpenQHYCCD.restype=ctypes.POINTER(c_uint32)

class CONTROL_ID(Enum):
    CONTROL_BRIGHTNESS = 0
    CONTROL_CONTRAST = 1       #!< image contrast
    CONTROL_WBR = 2            #!< red of white balance
    CONTROL_WBB = 3            #!< blue of white balance
    CONTROL_WBG = 4            #!< the green of white balance
    CONTROL_GAMMA = 5          #!< screen gamma
    CONTROL_GAIN = 6           #!< camera gain
    CONTROL_OFFSET = 7         #!< camera offset
    CONTROL_EXPOSURE = 8       #!< expose time (us)
    CONTROL_SPEED = 9          #!< transfer speed
    CONTROL_TRANSFERBIT = 10    #!< image depth bits
    CONTROL_CHANNELS = 11       #!< image channels
    CONTROL_USBTRAFFIC = 12     #!< hblank
    CONTROL_ROWNOISERE = 13     #!< row denoise
    CONTROL_CURTEMP = 14        #!< current cmos or ccd temprature
    CONTROL_CURPWM = 15         #!< current cool pwm
    CONTROL_MANULPWM = 16       #!< set the cool pwm
    CONTROL_CFWPORT = 17        #!< control camera color filter wheel port
    CONTROL_COOLER = 18         #!< check if camera has cooler
    CONTROL_ST4PORT = 19        #!< check if camera has st4port
    CAM_COLOR = 20
    CAM_BIN1X1MODE = 21         #!< check if camera has bin1x1 mode
    CAM_BIN2X2MODE = 22        #!< check if camera has bin2x2 mode
    CAM_BIN3X3MODE = 23         #!< check if camera has bin3x3 mode
    CAM_BIN4X4MODE = 24         #!< check if camera has bin4x4 mode
    CAM_MECHANICALSHUTTER = 25                   #!< mechanical shutter
    CAM_TRIGER_INTERFACE = 26                    #!< triger
    CAM_TECOVERPROTECT_INTERFACE = 27            #!< tec overprotect
    CAM_SINGNALCLAMP_INTERFACE = 28              #!< singnal clamp
    CAM_FINETONE_INTERFACE = 29                  #!< fine tone
    CAM_SHUTTERMOTORHEATING_INTERFACE = 30       #!< shutter motor heating
    CAM_CALIBRATEFPN_INTERFACE = 31              #!< calibrated frame
    CAM_CHIPTEMPERATURESENSOR_INTERFACE = 32     #!< chip temperaure sensor
    CAM_USBREADOUTSLOWEST_INTERFACE = 33        #!< usb readout slowest
    CAM_8BITS = 34                               #!< 8bit depth
    CAM_16BITS = 35                              #!< 16bit depth
    CAM_GPS = 36                                 #!< check if camera has gps
    CAM_IGNOREOVERSCAN_INTERFACE = 37            #!< ignore overscan area
    QHYCCD_3A_AUTOBALANCE = 38
    QHYCCD_3A_AUTOEXPOSURE = 39
    QHYCCD_3A_AUTOFOCUS = 40
    CONTROL_AMPV = 41                           #!< ccd or cmos ampv
    CONTROL_VCAM = 42                           #!< Virtual Camera on off
    CAM_VIEW_MODE = 43
    CONTROL_CFWSLOTSNUM = 44        #!< check CFW slots number
    IS_EXPOSING_DONE = 45
    ScreenStretchB = 46
    ScreenStretchW = 47
    CONTROL_DDR = 48
    CAM_LIGHT_PERFORMANCE_MODE = 49
    CAM_QHY5II_GUIDE_MODE = 50
    DDR_BUFFER_CAPACITY = 51
    DDR_BUFFER_READ_THRESHOLD = 52


def ASInitCamera():

    global ISizeX
    global ISizeY
    global QHYhandle
    global fnt

    ret=qhyccd.InitQHYCCDResource();
    if ret==0:
        print("InitSDK success\n")
    else:
        print("No camera\n")
    num=qhyccd.ScanQHYCCD();
    if num>0:
        print("found camera\n")
    else:
        print("No QHY camera found\n")

    i=c_int=0;
    type_char_array_32=c_char*32
    id=type_char_array_32()
    ret=qhyccd.GetQHYCCDId(i,id)

    print(id.value)

    QHYhandle=qhyccd.OpenQHYCCD(id)

    print("Handle = "+ str(QHYhandle))
    SetOK=qhyccd.SetQHYCCDStreamMode(QHYhandle,0)
    print('Stream = '+str(SetOK))
    SetOK=qhyccd.InitQHYCCD(QHYhandle)
    print('Init = '+str(SetOK))

    ChipW=ctypes.c_double()
    ChipH=ctypes.c_double()
    ImageW=ctypes.c_uint32()
    ImageH=ctypes.c_uint32()
    PixelW=ctypes.c_double()
    PixelH=ctypes.c_double()
    bpp=ctypes.c_uint32()

    qhyccd.GetQHYCCDChipInfo(QHYhandle,ctypes.byref(ChipW),ctypes.byref(ChipH),ctypes.byref(ImageW),ctypes.byref(ImageH)
                             ,ctypes.byref(PixelH),ctypes.byref(PixelW),ctypes.byref(bpp))

    print("ChipW = "+str(ChipW))
    print("ChipH = "+str(ChipH))
    print("ImageW = "+str(ImageW))
    print("ImageH = "+str(ImageH))
    print("PixelW = "+str(PixelW))
    print("PixelH = "+str(PixelH))
    StartX=ctypes.c_uint32()
    StartY=ctypes.c_uint32()
    SizeX=ctypes.c_uint32()
    SizeY=ctypes.c_uint32()

    qhyccd.GetQHYCCDEffectiveArea(QHYhandle,ctypes.byref(StartX),ctypes.byref(StartY),ctypes.byref(SizeX),ctypes.byref(SizeY))

    ISizeX=SizeX
    ISizeY=SizeY
    ImageSize=qhyccd.GetQHYCCDMemLength(QHYhandle)
    fnt = ImageFont.truetype("c:\\windows\\fonts\micross.ttf",20)


imgdata = np.ndarray(np.int32(ISizeX) * np.int32(ISizeY), dtype=np.uint8)

GetOK = qhyccd.GetQHYCCDSingleFrame(QHYhandle, ctypes.byref(ImageW),ctypes.byref(ImageH),ctypes.byref(bpp),ctypes.byref(channels),
                                    ctypes.c_void_p(imgdata.ctypes.data))

x = imgdata.reshape(ImageH.value, ImageW.value)
hdu = fits.PrimaryHDU(x)
hdul = fits.HDUList([hdu])
# add time, sqm, gain and exposure to fits
hdr = hdul[0].header
hdr.set('DATE-OBS', FITS_Stamp)
hdr.set('DATE-LOC', LOC_Stamp)
hdr.set('SQM', str(SQMSegment))
hdr.set('EXPOSURE', str(exp_seconds))
hdr.set('GAIN', str(qhyGain))
hdr.set('SUNEL', str(SunEl))
hdr.set('MOONEL', str(MoonEl))
hdr.set('MNPHASE', str(MoonPhase))
hdr.set('CCDTEMP', str(CCDTemp))
hdul.writeto(FITS_FileName)

print('median filter')
mfx = median_filter(x, size=3)
print('mf done')
im = Image.fromarray(mfx)
d = ImageDraw.Draw(im)
d.text((50, ImageH.value - 80), Pic_DateStamp, font=fnt, fill='rgb(255,255,255)')
# d.text((50,ImageH.value-40),"Tebbutt Observatory",font=fnt,fill='rgb(255,255,255)')
d.text((50, ImageH.value - 40), "Gain " + str(qhyGain) + " Exposure " + str(exp_seconds), font=fnt,
       fill='rgb(255,255,255)')
d.text((ImageW.value / 2, ImageH.value - 80), str(SunString) + str(SQMInsertString), font=fnt, fill='rgb(255,255,255)')
d.text((ImageW.value / 2, ImageH.value - 40), str(MoonString), font=fnt, fill='rgb(255,255,255)')
# plt.imshow(im, cmap='gray')
im.save(JPEG_FileName)
print("done")
print('Gain ' + str(qhyGain) + ' Exp ' + str(exp_seconds) + ' SunEl ' + str(SunEl) + ' MoonEl ' + str(MoonEl) + ' Phase ' + str(MoonPhase))
# image=Image.open(JPEG_FileName)
# image.show()
# qhyccd.CloseQHYCCD(QHYhandle)