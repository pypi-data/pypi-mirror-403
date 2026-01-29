
import wmi
import copy
import pythoncom
from ..SHRMACE_ErrorBase import SHRMACEException

def get_cpu_id(var) -> None:
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        cpuid : str = ''
        for cpu in c.Win32_Processor():
            cpuid += cpu.ProcessorId.strip() + ' '
        var.SHRMACEResult['CPUID'] = copy.deepcopy(cpuid.strip().upper())
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2003] unable to get CPU id. | {''.join(e.args)}')
    finally:
        pythoncom.CoUninitialize()