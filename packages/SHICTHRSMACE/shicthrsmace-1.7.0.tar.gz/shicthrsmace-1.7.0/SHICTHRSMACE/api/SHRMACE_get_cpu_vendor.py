
import wmi
import pythoncom
from ..SHRMACE_ErrorBase import SHRMACEException

def get_cpu_vendor(var) -> None:
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        for processor in c.Win32_Processor():
            name = processor.Name.lower()
            manufacturer = processor.Manufacturer.lower()
            if 'intel' in manufacturer or 'intel' in name:
                var.SHRMACEResult['CPUVendor'] = 'intel'
            elif 'amd' in manufacturer or 'amd' in name:
                var.SHRMACEResult['CPUVendor'] = 'amd'
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2004] unable to get CPU vendor. | {''.join(e.args)}')
    finally:
        pythoncom.CoUninitialize()