
import subprocess
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

MEM_INFO_COMMAND : str = 'wmic memorychip get Manufacturer, PartNumber, SerialNumber, Capacity, Speed, DeviceLocator, MemoryType, FormFactor'

def get_mem_info(var) -> None:
    try:
        output = subprocess.check_output(
            MEM_INFO_COMMAND, 
            shell=True, 
            text=True, 
            stderr=subprocess.STDOUT,
            encoding='utf-8'
        )
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        if len(lines) < 2:
            return []
        
        headers = [h.strip() for h in lines[0].split() if h.strip()]
        modules = []
        
        for line in lines[1:]:
            values = [v.strip() for v in line.split(None, len(headers) - 1)]
            if len(values) != len(headers):
                continue
                
            module_info = dict(zip(headers, values))
            modules.append(module_info)
        
        var.SHRMACEResult['MemeroyINFO'] = copy.deepcopy(modules)

    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2011] unable to get memory info. | {''.join(e.args)}')