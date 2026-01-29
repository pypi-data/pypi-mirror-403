# cad_api.py
from __future__ import annotations

import os
import sys
import traceback
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
import math, random, string
from collections import namedtuple
from contextlib import redirect_stderr
import io

from .env import ensure_env_inited



@dataclass
class BuildResult:
    ok: bool
    out_path: Optional[str] = None
    error: Optional[str] = None


def build_doc_from_script(script_code: str, *, global_scope: Optional[Dict[str, Any]] = None):
    """
    执行建模脚本，返回 doc 对象（不弹 UI）。
    脚本里可直接使用 doc / NCTI。
    """
    NCTI = ensure_env_inited()
    import builtins
    builtins.sys = sys
    builtins.os = os
    doc = NCTI.Document()
    doc.New("OCC", "DCM", 0, "GMSH")

    # 兼容常见命名差异：允许脚本使用 doc.add_box(...)
    if not hasattr(doc, "add_box"):
        for _cand in ("AddBox", "addBox", "Add_Box", "MakeBox", "Box"):
            if hasattr(doc, _cand):
                try:
                    setattr(doc, "add_box", getattr(doc, _cand))
                    break
                except Exception:
                    pass

    # 如果仍然找不到可用的 box 接口，提供更友好的报错（而不是“莫名其妙没这个方法”）
    if not hasattr(doc, "add_box"):
        def _missing_add_box(*_args, **_kwargs):
            raise AttributeError(
                "Document 对象没有 add_box/相关 Box 创建接口。"
                "请改用你们项目里已验证可用的建模 API（例如调用 NCTI/OCC 的真实建模函数）。"
            )
        try:
            setattr(doc, "add_box", _missing_add_box)
        except Exception:
            pass

    # ✅ 默认把 sys/os 注入脚本执行环境，避免脚本里用到 sys 直接 NameError
    scope = {
        "NCTI": NCTI,
        "doc": doc,
        "sys": sys,
        "os": os,
        "math": math,
        "random": random,
        "string": string,
    }
    if global_scope:
        scope.update(global_scope)

    try:
        exec(script_code, scope)
    except Exception as e:
        raise RuntimeError("脚本执行失败（exec script_code）") from e

    # Zoom 在无 UI 环境可能报错，建议吞掉
    try:
        doc.Zoom()
    except Exception:
        pass

    return doc


def _is_scalar(x) -> bool:
    return isinstance(x, (int, float))


def _to_list(x):
    """
    把 numpy array / tuple 等转成 list，尽量兼容 GetMesh 返回类型
    """
    try:
        # numpy array
        if hasattr(x, "tolist"):
            return x.tolist()
    except Exception:
        pass
    if isinstance(x, list):
        return x
    if isinstance(x, tuple):
        return list(x)
    return x


def _get_vertex(vertices, vidx: int) -> Tuple[float, float, float]:
    """
    兼容两种 vertices:
      1) [(x,y,z), (x,y,z), ...]
      2) [x0,y0,z0,x1,y1,z1,...]  (扁平)
    """
    vertices = _to_list(vertices)

    if not vertices:
        raise ValueError("GetMesh 返回的 vertices 为空")

    first = vertices[0]

    # 情况2：扁平 float 列表
    if _is_scalar(first):
        base = vidx * 3
        if base + 2 >= len(vertices):
            raise IndexError(f"顶点索引越界: vidx={vidx}, len(vertices)={len(vertices)}（扁平数组）")
        return (float(vertices[base]), float(vertices[base + 1]), float(vertices[base + 2]))

    # 情况1：list of triplets
    v = vertices[vidx]
    v = _to_list(v)
    if _is_scalar(v):
        # 极端异常：居然取出来还是标量
        raise TypeError(f"顶点数据异常：vertices[{vidx}] 是标量 {v}")
    if len(v) < 3:
        raise ValueError(f"顶点数据长度不足3：vertices[{vidx}]={v}")
    return (float(v[0]), float(v[1]), float(v[2]))


def _iter_faces(faces):
    """
    兼容两种 faces:
      1) [(i,j,k), ...]
      2) [i0,j0,k0,i1,j1,k1,...]  (扁平)
    """
    faces = _to_list(faces)
    if not faces:
        return []

    first = faces[0]

    # list of triplets
    if isinstance(first, (list, tuple)) and len(first) >= 3:
        return [(int(f[0]), int(f[1]), int(f[2])) for f in faces]

    # numpy ndarray (n,3) 可能 tolist 后变成 list[list]
    if isinstance(first, list) and len(first) >= 3:
        return [(int(f[0]), int(f[1]), int(f[2])) for f in faces]

    # 扁平
    out = []
    for i in range(0, len(faces), 3):
        if i + 2 >= len(faces):
            break
        out.append((int(faces[i]), int(faces[i + 1]), int(faces[i + 2])))
    return out


def get_model_triangles(doc) -> List[Tuple[Tuple[float, float, float],
                                          Tuple[float, float, float],
                                          Tuple[float, float, float]]]:
    """
    从 doc.GetMesh(name) 取出 vertices/faces，组装成三角形列表。
    强兼容：vertices 支持扁平/三元组；faces 支持扁平/三元组。
    """
    triangles: List[Tuple[Tuple[float, float, float],
                          Tuple[float, float, float],
                          Tuple[float, float, float]]] = []

    names = doc.AllNames()
    for name in names:
        mesh_data = doc.GetMesh(name)
        if not mesh_data or len(mesh_data) < 2:
            continue

        vertices = mesh_data[0]
        faces = mesh_data[1]

        face_iter = _iter_faces(faces)
        if not face_iter:
            continue

        for (i, j, k) in face_iter:
            v1 = _get_vertex(vertices, i)
            v2 = _get_vertex(vertices, j)
            v3 = _get_vertex(vertices, k)
            triangles.append((v1, v2, v3))

    return triangles


def export_stl(triangles, out_path: str) -> None:
    """
    写 STL（binary STL）。
    依赖 numpy-stl：pip install numpy-stl
    """
    from stl import mesh  # numpy-stl
    import numpy as np

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    data = np.zeros(len(triangles), dtype=mesh.Mesh.dtype)
    for i, tri in enumerate(triangles):
        data["vectors"][i] = np.array(tri)

    m = mesh.Mesh(data)
    m.save(out_path)


def export_amf(triangles, out_path: str) -> None:
    """
    写 AMF（XML）。
    """
    import xml.etree.ElementTree as ET

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    amf = ET.Element("amf", unit="millimeter")
    obj = ET.SubElement(amf, "object", id="0")
    mesh_el = ET.SubElement(obj, "mesh")
    vertices_el = ET.SubElement(mesh_el, "vertices")
    volume_el = ET.SubElement(mesh_el, "volume")

    v_map = {}
    v_list = []

    def vid(v):
        if v not in v_map:
            v_map[v] = len(v_list)
            v_list.append(v)
        return v_map[v]

    for tri in triangles:
        a, b, c = tri
        ia, ib, ic = vid(a), vid(b), vid(c)

        tri_el = ET.SubElement(volume_el, "triangle")
        ET.SubElement(tri_el, "v1").text = str(ia)
        ET.SubElement(tri_el, "v2").text = str(ib)
        ET.SubElement(tri_el, "v3").text = str(ic)

    for v in v_list:
        vtx_el = ET.SubElement(vertices_el, "vertex")
        coord_el = ET.SubElement(vtx_el, "coordinates")
        ET.SubElement(coord_el, "x").text = str(v[0])
        ET.SubElement(coord_el, "y").text = str(v[1])
        ET.SubElement(coord_el, "z").text = str(v[2])

    tree = ET.ElementTree(amf)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)


def export_stp(doc, out_path: str) -> None:
    """
    导出 STP/STEP 格式。
    注意：cmd_ncti_export_file 可能只需要路径参数，不需要格式ID。
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # ✅ 修改点：去掉参数 2，只传递 out_path
    # 之前的 "invalid arguments" 错误说明它不需要第二个参数
    doc.RunCommand("cmd_ncti_export_file", out_path)

    # 检查文件是否生成
    if not os.path.exists(out_path):
        # 如果还是失败，可能是路径编码问题，尝试转为绝对路径
        abs_path = os.path.abspath(out_path)
        if abs_path != out_path:
            doc.RunCommand("cmd_ncti_export_file", abs_path)

        if not os.path.exists(out_path):
            raise RuntimeError(f"STP 文件导出失败，未生成文件: {out_path}")


def build_model_file(script_code: str, out_path: str, fmt: str = "stl",
                     *, global_scope: Optional[Dict[str, Any]] = None) -> BuildResult:
    """
    对外暴露的核心 API：
    输入脚本 -> 输出模型文件（stl/amf/ncti/stp）
    """
    buf_err = io.StringIO()
    try:
        with redirect_stderr(buf_err):
            fmt = fmt.lower().strip()
            doc = build_doc_from_script(script_code, global_scope=global_scope)

            if fmt == "ncti":
                os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
                doc.Save(out_path)
                return BuildResult(True, out_path, None)

            # =========== 新增 STP 支持开始 ===========
            elif fmt in ("stp", "step"):
                export_stp(doc, out_path)
                return BuildResult(True, out_path, None)
            # =========== 新增 STP 支持结束 ===========

            # 获取网格数据用于 STL/AMF
            triangles = get_model_triangles(doc)

            # 注意：STP 是几何导出，不需要离散化为 triangles，所以上面直接 return 了
            # 如果是 STL/AMF 才需要下面的逻辑

            if not triangles:
                return BuildResult(False, None, "模型为空或无网格数据（GetMesh 返回空 或 faces 为空）")

            if fmt == "stl":
                export_stl(triangles, out_path)
            elif fmt == "amf":
                export_amf(triangles, out_path)
            else:
                return BuildResult(False, None, f"不支持的格式: {fmt}（仅支持 stl/amf/ncti/stp）")

            return BuildResult(True, out_path, None)

    except Exception:
        extra = buf_err.getvalue()
        tb = traceback.format_exc()
        if extra.strip():
            tb = tb + "\n\n[stderr captured]\n" + extra
        return BuildResult(False, None, tb)

