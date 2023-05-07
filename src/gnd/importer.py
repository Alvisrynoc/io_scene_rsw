import os
import bpy
import bpy_extras
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, FloatProperty
from . import reader
from . import gnd

class GndImportOptions(object):
    def __init__(self, should_import_lightmaps: bool = True, createCollection:bool=True, lightmap_factor: float = 0.5):
        self.should_import_lightmaps = should_import_lightmaps
        self.lightmap_factor = lightmap_factor
        self.createCollection = createCollection


class GND_OT_ImportOperatorXXX(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs X"""
    bl_idname = 'io_scene_rsw.gnd_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Ragnarok Online GNDXXX'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filename_ext = ".gnd"

    filter_glob: StringProperty(
        default="*.gnd",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    should_import_lightmaps: BoolProperty(
        default=True
    )

    createCollection: BoolProperty(
        default=False
    )

    lightmap_factor: FloatProperty(
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )

    @staticmethod
    def import_gnd(filePath, options: GndImportOptions, collection):
        gndFile = gnd.Gnd(filePath)
        obj, width, height = reader.create(gndFile, filePath, options, collection=collection)
        return obj, width, height

    def execute(self, context):
        options = GndImportOptions(
            should_import_lightmaps=self.should_import_lightmaps,
            lightmap_factor=self.lightmap_factor,
            createCollection=self.createCollection
        )
        GND_OT_ImportOperatorXXX.import_gnd(self.filepath, options, None)
        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(GND_OT_ImportOperatorXXX.bl_idname, text='Ragnarok Online GND (.gnd)')

