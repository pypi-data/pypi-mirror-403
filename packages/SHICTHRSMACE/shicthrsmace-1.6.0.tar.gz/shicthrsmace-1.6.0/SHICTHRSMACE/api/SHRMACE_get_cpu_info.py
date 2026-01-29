
import subprocess
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

def get_cpu_info(var) -> None:
    try:
        output = subprocess.check_output('wmic cpu get name' , shell=True).decode().split('\n')[1].strip()
        var.SHRMACEResult['CPUINFO'] = copy.deepcopy(output if output else None)
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2002] unable to get CPU info. | {''.join(e.args)}')