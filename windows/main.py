import ctypes
from ctypes import *
from PIL import Image


qhyccd = CDLL("driver/qhyccd.dll")

e = qhyccd.InitQHYCCDResource()
if e == 0:
    print("init SDK success!")

    num = qhyccd.ScanQHYCCD()
    if num > 0:
        print("QHYCCD camera found. total:", num)

        i = ctypes.c_int = 0
        type_char_array_32 = ctypes.c_char * 32
        id = type_char_array_32()
        found = 0
        for x in range(i, num):
            e = qhyccd.GetQHYCCDId(x, id)
            if e == 0:
                print("camera", x, "-> ID:", id.value)
                if x == 0:
                    found = 1
            break

        if found == 1:
            QHYhandle = qhyccd.OpenQHYCCD(id)
            if QHYhandle is None:
                print("open QHYCCD fail")
            else:
                print("open QHYCCD success!")

                e = qhyccd.SetQHYCCDStreamMode(QHYhandle, 0)
                if e == 0:
                    print("SetQHYCCDStreamMode success!")

                    e = qhyccd.InitQHYCCD(QHYhandle)
                    if e == 0:
                        print("init QHYCCD success!")

                        ChipW = ctypes.c_double()
                        ChipH = ctypes.c_double()
                        ImageW = ctypes.c_uint32()
                        ImageH = ctypes.c_uint32()
                        PixelW = ctypes.c_double()
                        PixelH = ctypes.c_double()
                        bpp = ctypes.c_uint32()
                        qhyccd.GetQHYCCDChipInfo(QHYhandle, ctypes.byref(ChipW), ctypes.byref(ChipH),
                                                 ctypes.byref(ImageW), ctypes.byref(ImageH), ctypes.byref(PixelH),
                                                 ctypes.byref(PixelW), ctypes.byref(bpp))
                        print("CCD/CMOS chip information:")
                        print(" |-> chip width", ChipW.value, "mm, chip height", ChipH.value, "mm")
                        print(" |-> chip pixel width", PixelW.value, "um, chip pixel height", PixelH.value, "um")
                        print(" |-> chip max resolution is", ImageW.value, "x", ImageH.value, ", depth is", bpp.value)

                        x = ctypes.c_uint32(1)
                        y = ctypes.c_uint32(1)
                        qhyccd.SetQHYCCDBinMode(QHYhandle, x, y)
                        qhyccd.SetQHYCCDResolution(QHYhandle, 0, 0, ImageW, ImageH) #ImageW/x, ImageH/y
                        qhyccd.SetQHYCCDBitsMode(QHYhandle, 16)

                        qhyccd.ExpQHYCCDSingleFrame(QHYhandle)

                        channels = ctypes.c_uint32()
                        ImageSize = qhyccd.GetQHYCCDMemLength(QHYhandle)
                        imgdata = (ctypes.c_uint8 * ImageSize)()
                        e = qhyccd.GetQHYCCDSingleFrame(QHYhandle, ctypes.byref(ImageW), ctypes.byref(ImageH),
                                                        ctypes.byref(bpp), ctypes.byref(channels), imgdata)
                        if e == 0:
                            print("GetQHYCCDSingleFrame succeess!")
                            im = Image.frombuffer('L', (ImageW.value, ImageW.value), bytearray(imgdata), 'raw', 'L', 0, 1)
                            im.save("result.jpeg")
                        else:
                            print("GetQHYCCDSingleFrame fail. Code:", e)

                        e = qhyccd.CloseQHYCCD(QHYhandle)
                        if e == 0:
                            print("close QHYCCD success!")
                        else:
                            print("close QHYCCD fail. Code:", e)

                        e = qhyccd.ReleaseQHYCCDResource()
                        if e == 0:
                            print("release SDK Resource success!")
                        else:
                            print("release SDK Resource fail. Code:", e)
                    else:
                        print("init QHYCCD fail. Code:", e)
                else:
                    print("SetQHYCCDStreamMode fail. Code:", e)
    else:
        print("no QHYCCD camera found")
else:
    print("init SDK error")
