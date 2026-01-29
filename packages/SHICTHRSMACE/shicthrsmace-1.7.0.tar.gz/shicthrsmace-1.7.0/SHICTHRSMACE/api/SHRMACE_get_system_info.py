
import platform
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

MEM_INFO_COMMAND : str = 'wmic memorychip get Manufacturer, PartNumber, SerialNumber, Capacity, Speed, DeviceLocator, MemoryType, FormFactor'

def get_system_info(var) -> None:
    try:
        os_name : str = platform.system()
        os_version : str = platform.version()
        architecture : str = platform.architecture()[0]
        architecture_type : str = platform.architecture()[1]
        system_type : str = get_win_platform()
        result : dict = {'os_name' : os_name , 'os_version' : os_version ,
                            'architecture' : architecture , 'architecture_type' : architecture_type ,
                            'platform' : system_type}
        var.SHRMACEResult['WindowsSystemInfo'] = copy.deepcopy(result)
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2015] unable to system info | {''.join(e.args)}')


def get_win_platform() -> str:
    version = platform.version().split('.')

    if len(version) < 3:
        raise SHRMACEException(f'SHRMACE [ERROR.2015.0] windows version is not supported')
    
    major = int(version[0])
    minor = int(version[1])
    build = int(version[2])

    if major == 10 and minor == 0:
        if build >= 22000:
            return "windows 11"

        elif build >= 10240:
            return "windows 10"
    else:
        raise SHRMACEException(f'SHRMACE [ERROR.2015.1] windows version only support 10.0.22000 and above')

