
from tkinter import E
import wmi
import sys

sys.coinit_flags = 0

import pythoncom
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

def get_disk_info(var) -> None:
    pythoncom.CoInitialize()
    result = []
    try:
        c = wmi.WMI()
        for physical_disk in c.Win32_DiskDrive():
            try:
                disk_info = {
                    "DISK_NAME" : physical_disk.Caption or "" ,
                    "DISK_ID" : physical_disk.SerialNumber.strip() if physical_disk.SerialNumber else None ,
                    "DISK_SIZE" : f"{int(physical_disk.Size) / (1024**3):.1f} GB" if physical_disk.Size else None ,
                    "DISK_PNPDEVICEID" : physical_disk.PNPDeviceID.split("\\")[-1] if physical_disk.PNPDeviceID else None ,
                    "DISK_PROTOCOL" : physical_disk.InterfaceType or None,
                    "DISK_PARTITION" : []
                }
            except Exception as e:
                raise SHRMACEException(f'SHRMACE [ERROR.2009.0] error occurred while getting disk info. | {''.join(e.args)}')
            
            try:
                for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
                    for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                        partition_size = int(logical_disk.Size) if logical_disk.Size else 0
                        partition_info = {
                            "DISK_LETTER" : logical_disk.DeviceID or "",
                            "DISK_SUB_SIZE" : f"{partition_size / (1024**3):.1f} GB",
                            "DISK_FILE_SYSTEM" : logical_disk.FileSystem or "",
                            "AVAILABLE_DISK_SIZE" : f"{int(logical_disk.FreeSpace) / (1024**3):.1f} GB" if logical_disk.FreeSpace else None
                        }
                        disk_info["DISK_PARTITION"].append(partition_info)
                
                result.append(disk_info)
                var.SHRMACEResult['DiskINFO'] = copy.deepcopy(result)
            except Exception as e:
                raise SHRMACEException(f'SHRMACE [ERROR.2009.1] error occurred while getting disk DISK_PARTITION info. | {''.join(e.args)}')
    
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2009] unable to get disk info. | {''.join(e.args)}')

    finally:
        pythoncom.CoUninitialize()