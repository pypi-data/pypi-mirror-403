
import wmi
import pythoncom
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

def get_mb_id(var) -> None:
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        MB_ID = ''
        for board_id in c.Win32_BaseBoard():
            MB_ID += board_id.SerialNumber + ' '
        var.SHRMACEResult['MotherBoardID'] = copy.deepcopy(MB_ID.strip().upper())
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2006] unable to get MotherBoard id. | {''.join(e.args)}')
    finally:
        pythoncom.CoUninitialize()