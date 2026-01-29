
import winreg
import copy
from ..SHRMACE_ErrorBase import SHRMACEException

WindowsProductID_REG_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"

def get_pdc_id(var) -> None:
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE , WindowsProductID_REG_PATH)
        value , _ = winreg.QueryValueEx(key, "ProductId")
        winreg.CloseKey(key)
        var.SHRMACEResult['WindowsProductId'] = copy.deepcopy(value)
    except Exception as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2001] unable to get WindowsProductID. | {''.join(e.args)}')