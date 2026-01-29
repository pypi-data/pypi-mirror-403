
import threading
from ..SHRMACE_ErrorBase import SHRMACEException
from ..SHRMACE_Data import SHRMACEData
from ..api.SHRMACE_get_system_info import get_system_info
from ..api.SHRMACE_get_uuid import get_uuid
from ..api.SHRMACE_get_pdc_id import get_pdc_id
from ..api.SHRMACE_get_cpu_info import get_cpu_info
from ..api.SHRMACE_get_cpu_id import get_cpu_id
from ..api.SHRMACE_get_cpu_vendor import get_cpu_vendor
from ..api.SHRMACE_get_mb_info import get_mb_info
from ..api.SHRMACE_get_mb_id import get_mb_id
from ..api.SHRMACE_get_gpu_info import get_gpu_info
from ..api.SHRMACE_get_gpu_id import get_gpu_id
from ..api.SHRMACE_get_disk_info import get_disk_info
from ..api.SHRMACE_get_mem_info import get_mem_info
from ..api.SHRMACE_get_mac_info import get_mac_info

MACE_PROCESS_LIST : list = [get_system_info , get_uuid , get_pdc_id , get_cpu_info ,
                            get_cpu_id , get_cpu_vendor , get_mb_info ,
                            get_mb_id , get_gpu_info , get_gpu_id ,
                            get_disk_info , get_mem_info , get_mac_info]

def SHRMACE_mace_info_dispatcher() -> dict:

    def SHRMACE_Function_Launcher(func , var):
        try:
            func(var)
        except Exception as e:
            print(''.join(e.args))

    try:
        var = SHRMACEData()
        thread_pool : list = []
        
        for func in MACE_PROCESS_LIST:
            thread = threading.Thread(target = SHRMACE_Function_Launcher , args=(func , var ,))
            thread.daemon = True
            thread_pool.append(thread)

        for thread in thread_pool:
            thread.start()

        for thread in thread_pool:
            thread.join()
        
        return var.SHRMACEResult

    except SHRMACEException as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2013] error occurred while getting creating threads pool. | {''.join(e.args)}')
    