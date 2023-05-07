import os
import bpy
import bpy_extras
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, FloatProperty
from . import reader
from . import gnd

class Options(object):
    def __init__(self, toImportLightmaps: bool = True, toCreateCollection:bool=True, lightmap_factor: float = 0.5):
        self.toImportLightmaps = toImportLightmaps
        self.lightmap_factor = lightmap_factor
        self.toCreateCollection = toCreateCollection


class Importer(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
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
    def import_gnd(filePath, options: Options, collection):
        gndFile = gnd.Gnd(filePath)
        obj, width, height = reader.create(gndFile, filePath, options, collection=collection)
        return obj, width, height

    def execute(self, context):
        options = Options(
            toImportLightmaps=self.toImportLightmaps,
            lightmap_factor=self.lightmap_factor,
            toCreateCollection=self.toCreateCollection
        )
        Importer.import_gnd(self.filepath, options, None)
        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(Importer.bl_idname, text='Ragnarok Online GND (.gnd)')

