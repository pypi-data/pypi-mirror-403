
import wmi
import copy
import pythoncom
from ..SHRMACE_ErrorBase import SHRMACEException

def get_uuid(var) -> None:
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        for system in c.Win32_ComputerSystemProduct():
            var.SHRMACEResult['WindowsUUID'] = copy.deepcopy(system.UUID)
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2000] unable to get uuid. | {''.join(e.args)}')
    finally:
        pythoncom.CoUninitialize()