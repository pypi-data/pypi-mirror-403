
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

        headers = [h.strip() for h in lines[0].split('  ') if h.strip()]
        modules = []

        for line in lines[1:]:
            values = []
            remaining = line
            for i in range(len(headers)):
                if i == len(headers) - 1:
                    values.append(remaining.strip())
                else:
                    parts = remaining.strip().split('  ', 1)
                    if len(parts) > 0:
                        values.append(parts[0].strip())
                        remaining = parts[1] if len(parts) > 1 else ''
                    else:
                        values.append('')

            if len(values) == len(headers):
                module_info = {}
                for h, v in zip(headers, values):
                    module_info[h] = v
                modules.append(module_info)

        var.SHRMACEResult['MemeroyINFO'] = copy.deepcopy(modules)

    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2011] unable to get memory info. | {"".join(e.args)}')