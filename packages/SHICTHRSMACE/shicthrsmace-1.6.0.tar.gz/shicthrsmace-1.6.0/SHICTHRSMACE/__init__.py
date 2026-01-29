# *-* coding: utf-8 *-*
# src\__init__.py
# SHICTHRS MACE
# AUTHOR : SHICTHRS-JNTMTMTM
# Copyright : © 2025-2026 SHICTHRS, Std. All rights reserved.
# lICENSE : GPL-3.0

from colorama import init
init()
from .SHRMACE_ErrorBase import SHRMACEException
from .utils.SHRMACE_dispatcher import SHRMACE_mace_info_dispatcher
from .api.SHRMACE_get_system_info import get_win_platform

print('\033[1mWelcome to use SHRMACE - machine identity system\033[0m\n|  \033[1;34mGithub : https://github.com/JNTMTMTM/SHICTHRS_MACE\033[0m')
print('|  \033[1mAlgorithms = rule ; Questioning = approval\033[0m')
print('|  \033[1mCopyright : © 2025-2026 SHICTHRS, Std. All rights reserved.\033[0m\n')

__all__ = ['SHRMACE_get_mace_info' , 'SHRMACE_get_system_type']

def SHRMACE_get_mace_info() -> tuple:
    try:
        errro_list : list = []
        result : dict = SHRMACE_mace_info_dispatcher()
        for MACE_item in result.keys():
            if not result[MACE_item]:
                errro_list.append(MACE_item)
        return (result , errro_list)
    except SHRMACEException as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2014] error occurred while getting mace info. | {''.join(e.args)}')
    
def SHRMACE_get_system_type() -> str:
    try:
        return get_win_platform()
    except SHRMACEException as e:
        raise SHRMACEException(f'SHRMACE [ERROR.2015] unable to system info. | {''.join(e.args)}')