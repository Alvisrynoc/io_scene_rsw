import bpy
import bpy_extras
from bpy.props import StringProperty, BoolProperty, FloatProperty

from . import rsw
from . import reader

class Options:
    def __init__(self, toImportGND: bool=True, toImportRSM: bool=True):
        self.toImportGND = toImportGND
        self.toImportRSM = toImportRSM

class Importer(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs X"""
    bl_idname = 'io_scene_rsw.rsw_import'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Import Ragnarok Online RSWXXX'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filename_ext = ".rsw"

    filter_glob: StringProperty(
        default="*.rsw",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    data_path: StringProperty(
        default='',
        maxlen=255,
        subtype='DIR_PATH'
    )

    toImportGND: BoolProperty(default=True)
    toImportRSM: BoolProperty(default=True)

    def execute(self, context):
        rswFile = rsw.Rsw(self.filepath)
        options = Options()
        try:
            reader.create(rswFile, self.filepath, options)
        except FileNotFoundError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        # except FileNotFoundError:
        #     self.report({'ERROR'}, 'GND file ({}) could not be found in directory ({}).'.format(rswFile.gnd_file, data_path))
        #     return {'CANCELLED'}
        # except FileNotFoundError:
        #     self.report({'ERROR'}, 'RSM file ({}) could not be found in directory ({}).'.format(rswFile.filename, models_path))
        #     return {'CANCELLED'}
                
        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(Importer.bl_idname, text='Ragnarok Online RSW (.rsw)')
