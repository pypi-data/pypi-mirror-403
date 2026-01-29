
import subprocess
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

def get_gpu_info(var) -> None:
    try:
        output = subprocess.check_output('wmic path win32_VideoController get name' , shell=True, text=True, stderr=subprocess.DEVNULL)
        gpus = [line.strip() for line in output.splitlines() if line.strip() and 'Name' not in line]
        var.SHRMACEResult['GPUINFO'] = copy.deepcopy(gpus)
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2007] unable to get GPU info. | {''.join(e.args)}')