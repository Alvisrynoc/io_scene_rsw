import os
import bpy
import bpy_extras
import mathutils
import math
import copy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from ..utils.utils import get_data_path
from ..rsw.reader import RswReader
from ..gnd.importer import GndImportOptions, GND_OT_ImportOperatorXXX
from ..rsm.importer import RsmImportOptions, RSM_OT_ImportOperatorXXX
from ..semver.version import Version
from collections import Counter
from ..rsm.reader import recenterByBoundBoxNewLocal, calculateResetVector, printBound

NORMALIZING_FACTOR = 5

# def applyLocalRotation(obj):

def useOffsetTransformAndfixed(rsw_model, modelObj, modelCollection):
    # if (modelCollection.name.startswith("라헬\마을외벽04.rsm") or 
    #     modelCollection.name.startswith("사막도시\집정관") or 
    #     modelCollection.name.startswith("사막도시\민가")):
    #     print(f"{modelObj.name=}")
    #     print(f"{rsw_model.position=}")
    #     print(f"{rsw_model.rotation=}")
    #     print(f"{rsw_model.scale=}")

    offsetMatrix = mathutils.Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
    pos = offsetMatrix @ mathutils.Vector(rsw_model.position)

    # if (modelCollection.name.startswith("라헬\마을외벽04.rsm") or 
    #     modelCollection.name.startswith("사막도시\집정관") or 
    #     modelCollection.name.startswith("사막도시\민가")):
    #     print(f"{modelObj.location=}")
    #     print(f"{pos=}")
    modelObj.location = pos

    scale = offsetMatrix @ mathutils.Vector(rsw_model.scale)
    modelObj.scale.x *= scale.x
    modelObj.scale.y *= scale.y
    modelObj.scale.z *= -scale.z

    # if rsw_model.rotation[2] == 90:
    #     vec = mathutils.Vector(rsw_model.rotation)
    #     simulatedRotation = offsetMatrix @ vec
    #     simulatedrotationEuler = mathutils.Euler(simulatedRotation, 'XYZ')
    #     print(f"{modelCollection.name=}")
    #     print(f"{modelObj.name=}")
    #     print(f"{vec=}")
    #     print(f"{simulatedRotation=}")
    #     print(f"{simulatedrotationEuler=}")

    rotation = offsetMatrix @ mathutils.Vector([math.radians(deg) for deg in rsw_model.rotation])
    rotationEuler = mathutils.Euler(rotation, 'XYZ')
    # rotationMatrix = rotationEuler.to_matrix().to_4x4()
    # modelObj.matrix_basis @= rotationMatrix

    # modelObj.rotation_euler.rotate(rotationEuler)

    modelObj.rotation_euler.rotate_axis("X", rotationEuler.x)
    modelObj.rotation_euler.rotate_axis("Y", rotationEuler.y)
    modelObj.rotation_euler.rotate_axis("Z", rotationEuler.z)

    # rotationMatrix = mathutils.Matrix.Rotation(rotation)
    # rotationQu = rotationMatrix.to_quaternion()
    # modelObj.rotation_quaternion.rotate(rotationQu)

    resetVec = calculateResetVector(modelObj)
    recenterByBoundBoxNewLocal(modelObj, resetVec)
    bpy.context.view_layer.update()

def duplicateObjUtil(obj, newObj, collection):
    for childObj in obj.children:
        newChildObj = childObj.copy()
        newChildObj.parent = newObj
        collection.objects.link(newChildObj)
        duplicateObjUtil(childObj, newChildObj, collection)

def duplciateObj(obj, collection):
    newObj = obj.copy()
    collection.objects.link(newObj)
    duplicateObjUtil(obj, newObj, collection)
    return newObj

def duplicateObjUtilNoCollection(obj, newObj):
    for childObj in obj.children:
        newChildObj = childObj.copy()
        newChildObj.parent = newObj
        duplicateObjUtilNoCollection(childObj, newChildObj)

def duplicateObjNoCollection(obj):
    newObj = obj.copy()
    duplicateObjUtilNoCollection(obj, newObj)
    return newObj

class RSW_OT_ImportOperatorXXX(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
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

    should_import_gnd: BoolProperty(default=True)
    should_import_models: BoolProperty(default=True)

    def execute(self, context):
        # Load the RSW file
        rsw = RswReader.from_file(self.filepath)

        # Find the data path.
        data_path = get_data_path(self.filepath)

        # TODO: create an EMPTY object that is the RSW parent object
        collectionName = os.path.basename(self.filepath)

        collection = bpy.data.collections.new(collectionName)
        bpy.context.scene.collection.children.link(collection)

        # Load the GND file and import it into the scene.
        if self.should_import_gnd:
            gnd_path = os.path.join(data_path, rsw.gnd_file)
            try:
                options = GndImportOptions(createCollection=False)
                gndObj, width, height = GND_OT_ImportOperatorXXX.import_gnd(gnd_path, options, collection)
                translation = mathutils.Vector((-width * NORMALIZING_FACTOR, -width * NORMALIZING_FACTOR, 0))
                # translationMatrix = mathutils.Matrix.Translation(translation)
                gndObj.location = translation
            except FileNotFoundError:
                self.report({'ERROR'}, 'GND file ({}) could not be found in directory ({}).'.format(rsw.gnd_file, data_path))
                return {'CANCELLED'}

        if self.should_import_models:
            # Load up all the RSM files and import them into the scene.
            models_path = os.path.join(data_path, 'model')
            rsm_options = RsmImportOptions(createCollection=False)

            fileNameToObjsMap = dict()
            objs = []
            for rsw_model in rsw.models:
                filename = rsw_model.filename.replace('\\', os.path.sep)

                # if (filename.startswith("라헬\마을외벽04.rsm") or 
                #     filename.startswith("사막도시\집정관") or 
                #     filename.startswith("사막도시\민가")):
                    
                modelCollection = bpy.data.collections.new(filename)
                bpy.data.collections[collectionName].children.link(modelCollection)
                # print(rsw_model.filename)
                # copy existing objects
                if rsw_model.filename in fileNameToObjsMap:
                    bpy.ops.object.select_all(action='DESELECT')
                    obj = fileNameToObjsMap[rsw_model.filename]
                    modelObj = duplciateObj(obj, modelCollection)
                else:
                    # new object
                    # Converts Windows filename separators to the OS's path separator
                    rsm_path = os.path.join(models_path, filename)
                    try:
                        modelObj, version = RSM_OT_ImportOperatorXXX.import_rsm(rsm_path, rsm_options, modelCollection)
                        # recenterByBoundBoxNew(modelObj)
                        fileNameToObjsMap[rsw_model.filename] = duplicateObjNoCollection(modelObj)
                        # printBound(modelObj)
                    except FileNotFoundError:
                        self.report({'ERROR'}, 'RSM file ({}) could not be found in directory ({}).'.format(filename, models_path))
                        return {'CANCELLED'}
        
                useOffsetTransformAndfixed(rsw_model, modelObj, modelCollection)
                # print()
                # objs.append(modelObj)
            
            bpy.context.view_layer.update()

                
        return {'FINISHED'}

    @staticmethod
    def menu_func_import(self, context):
        self.layout.operator(RSW_OT_ImportOperatorXXX.bl_idname, text='Ragnarok Online RSW (.rsw)')
