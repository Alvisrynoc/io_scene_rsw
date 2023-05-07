import bpy
import bpy_extras
from bpy.props import StringProperty, BoolProperty, FloatProperty

from . import rsm
from . import reader

class Options(object):
    def __init__(self, toImportSmoothGroups: bool=True, toCreateCollection: bool=True):
        self.toImportSmoothGroups = toImportSmoothGroups
        self.toCreateCollection = toCreateCollection

class Importer(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
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

    toImportSmoothGroups: BoolProperty(
        default=True
    )
    toCreateCollection: BoolProperty(
        default=False
    )

    @staticmethod
    def import_rsm(filePath, options, collection):
        rsmFile = rsm.Rsm(filePath)
        mainObj = reader.create(rsmFile, filePath, options, collection=collection)
        return mainObj

    def execute(self, context):
        options = Options(
            toImportSmoothGroups = self.toImportSmoothGroups,
            toCreateCollection = self.toCreateCollection
        )
        Importer.import_rsm(self.filepath, options, None)
        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(Importer.bl_idname, text='Ragnarok Online RSM (.rsm)')
