bl_info = {
    'name': 'Ragnarok Online ImportersXXX',
    'description': 'Import RSW, RSM and GND files from Ragnarok Online.',
    'author': 'Colin Basnett',
    'version': (1, 0, 0),
    'blender': (2, 80, 0),
    'location': 'File > Import-Export',
    'warning': 'This add-on is under development.',
    'wiki_url': 'https://github.com/cmbasnett/io_scene_rsw/wiki',
    'tracker_url': 'https://github.com/cmbasnett/io_scene_rsw/issues',
    'support': 'COMMUNITY',
    'category': 'Import-Export'
}

import importlib
import types

if 'bpy' in locals():
    if 'gnd' in locals():
        importlib.reload(GND)
        importlib.reload(GND.gnd)
        importlib.reload(GND.reader)
        importlib.reload(GND.importer)
    # print(dir(GND), type(dir(GND)))
    if 'rsm' in locals():
        importlib.reload(RSM)
        importlib.reload(RSM.rsm)
        importlib.reload(RSM.reader)
        importlib.reload(RSM.importer)
    if 'rsw' in locals():
        importlib.reload(RSW)
        importlib.reload(RSW.rsw)
        importlib.reload(RSW.reader)
        importlib.reload(RSW.importer)
    if 'io' in locals():
        importlib.reload(io.reader)
    if 'utils' in locals():
        importlib.reload(utils.utils)
    if 'ver' in locals():
        importlib.reload(ver.version)

import bpy
from . import gnd as GND
from . import rsm as RSM
from . import rsw as RSW
from . import io
from . import utils
from . import ver

classes = (
    GND.importer.Importer,
    RSM.importer.Importer,
    RSW.importer.Importer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(GND.importer.Importer.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(RSM.importer.Importer.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(RSW.importer.Importer.menu_func_import)

def unregister():
    # bpy.utils.unregister_module(__name__)
    bpy.types.TOPBAR_MT_file_import.remove(GND.importer.Importer.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(RSM.importer.Importer.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(RSW.importer.Importer.menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()