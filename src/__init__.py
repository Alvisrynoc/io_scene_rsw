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

# will have problem when submodule import other modules
# def recursiveRelaod(module):
#     """Recursively reload modules."""
#     importlib.reload(module)
#     print(dir(module), type(dir(module)))
#     for attribute_name in dir(module):
#         attribute = getattr(module, attribute_name)
#         if not attribute_name.startswith("__") and type(attribute) is types.ModuleType:
#             recursiveRelaod(attribute)

if 'bpy' in locals():
    if 'gnd'                in locals():
        importlib.reload(GND)
        importlib.reload(GND.gnd)
        importlib.reload(GND.reader)
        importlib.reload(GND.importer)
    # print(dir(GND), type(dir(GND)))
    if 'rsm'                in locals():
        importlib.reload(RSM)
        importlib.reload(RSM.rsm)
        importlib.reload(RSM.reader)
        importlib.reload(RSM.importer)
    if 'rsw'                in locals():
        importlib.reload(RSW)
        importlib.reload(RSW.rsw)
        importlib.reload(RSW.reader)
        importlib.reload(RSW.importer)
    # if 'gnd_importerxxx'    in locals(): importlib.reload(gnd_importerxxx)
    # if 'rsm_importerxxx'    in locals(): importlib.reload(rsm_importerxxx)
    # if 'rsw_importerxxx'    in locals(): importlib.reload(rsw_importerxxx)

import bpy
from . import gnd as GND
from . import rsm as RSM
from . import rsw as RSW

# from .gnd import gnd
# from .rsm import rsm
# from .rsw import rsw
# from .gnd import importer as gnd_importerxxx
# from .rsm import importer as rsm_importerxxx
# from .rsw import importer as rsw_importerxxx

classes = (
    GND.importer.GND_OT_ImportOperatorXXX,
    RSM.importer.RSM_OT_ImportOperatorXXX,
    RSW.importer.RSW_OT_ImportOperatorXXX,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(GND.importer.GND_OT_ImportOperatorXXX.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(RSM.importer.RSM_OT_ImportOperatorXXX.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(RSW.importer.RSW_OT_ImportOperatorXXX.menu_func_import)


def unregister():
    # bpy.utils.unregister_module(__name__)
    bpy.types.TOPBAR_MT_file_import.remove(GND.importer.GND_OT_ImportOperatorXXX.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(RSM.importer.RSM_OT_ImportOperatorXXX.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(RSW.importer.RSW_OT_ImportOperatorXXX.menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()