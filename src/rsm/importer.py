import bpy
import bpy_extras
# import math
from collections import defaultdict
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, FloatProperty
from . import rsm
from . import reader

class RsmImportOptions(object):
    def __init__(self, importSmoothGroups: bool=True, createCollection: bool=True):
        self.importSmoothGroups = importSmoothGroups
        self.createCollection = createCollection

class RSM_OT_ImportOperatorXXX(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs X"""
    bl_idname = 'io_scene_rsw.rsm_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Ragnarok Online RSMXXX'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filename_ext = ".rsm"

    filter_glob: StringProperty(
        default="*.rsm",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    importSmoothGroups: BoolProperty(
        default=True
    )
    createCollection: BoolProperty(
        default=False
    )

    @staticmethod
    def import_rsm(filePath, options, collection):
        rsmFile = rsm.Rsm(filePath)
        mainNode = reader.create(rsmFile, filePath, options, collection=collection)
        return mainNode, rsmFile.version

    def execute(self, context):
        options = RsmImportOptions(
            importSmoothGroups = self.importSmoothGroups,
            createCollection = self.createCollection
        )
        RSM_OT_ImportOperatorXXX.import_rsm(self.filepath, options, None)
        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(RSM_OT_ImportOperatorXXX.bl_idname, text='Ragnarok Online RSM Test (.rsm)')
