# src/ncti_cad/env.py
import sys, os, ctypes, importlib

_inited = False
_NCTI = None

def ensure_env_inited():
    """只初始化一次 CAD/NCTI 环境（dllpath 仍写死 D:\GEPlab）"""
    global _inited, _NCTI
    if _inited:
        return _NCTI

    dllpath = r"D:\GEPlab"
    Ncti_api_path = dllpath + r"\OCC"

    sys.path.insert(0, dllpath)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(Ncti_api_path)

    ctypes.CDLL(dllpath + r"\ncti_command.dll")
    ctypes.CDLL(dllpath + r"\ncti_occ_plugin.dll")
    ctypes.CDLL(dllpath + r"\ncti_render_vulkan.dll")

    _NCTI = importlib.import_module("ncti_python")
    _NCTI.Init(dllpath)

    _inited = True
    return _NCTI
