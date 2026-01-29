
import wmi
import pythoncom
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

def get_disk_id(var) -> None:
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        Disk_ID = ''
        for physical_disk in c.Win32_DiskDrive():
            Disk_ID += physical_disk.SerialNumber + ' '
        var.SHRMACEResult['DiskID'] = copy.deepcopy(Disk_ID.strip().upper())
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2010] unable to get disk id. | {''.join(e.args)}')
    finally:
        pythoncom.CoUninitialize()