import os
import bpy
import mathutils
import math
from ..gnd.importer import Options as GndOptions, Importer as GndImporter
from ..rsm.importer import Options as RsmOptions, Importer as RsmImporter

from ..ver.version import Version
from ..utils.utils import get_data_path

NORMALIZING_FACTOR = 5

offsetMatrix = mathutils.Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))

def recenterbyBoundBox(obj):
    cornerCoordinates = [mathutils.Vector(cornerCoordinate) for cornerCoordinate in obj.bound_box]
    boundBoxCenter = sum(cornerCoordinates, mathutils.Vector()) / len(cornerCoordinates)
    minZ = min([z for x, y, z in cornerCoordinates])
    resetVec = mathutils.Vector((-boundBoxCenter.x, -boundBoxCenter.y, -minZ))

    translationMatrix = mathutils.Matrix.Translation(resetVec)
    obj.matrix_basis @= translationMatrix

def applyTransform(rsw_model, modelObj):
    # translation
    pos = offsetMatrix @ mathutils.Vector(rsw_model.position)
    modelObj.location = pos

    # scale
    scale = offsetMatrix @ mathutils.Vector(rsw_model.scale)
    modelObj.scale.x *= scale.x
    modelObj.scale.y *= scale.y
    modelObj.scale.z *= -scale.z

    # rotation
    rotation = offsetMatrix @ mathutils.Vector([math.radians(deg) for deg in rsw_model.rotation])
    rotationEuler = mathutils.Euler(rotation, 'XYZ')

    modelObj.rotation_euler.rotate_axis("X", rotationEuler.x)
    modelObj.rotation_euler.rotate_axis("Y", rotationEuler.y)
    modelObj.rotation_euler.rotate_axis("Z", rotationEuler.z)

    recenterbyBoundBox(modelObj)
    bpy.context.view_layer.update()

def duplicateObjUtil(obj, newObj, collection=None):
    for childObj in obj.children:
        newChildObj = childObj.copy()
        newChildObj.parent = newObj
        if collection:
            collection.objects.link(newChildObj)
            duplicateObjUtil(childObj, newChildObj, collection)

def duplciateObj(obj, collection=None):
    newObj = obj.copy()
    if collection:
        collection.objects.link(newObj)
        duplicateObjUtil(obj, newObj, collection)
    return newObj

def handleGND(gnd_path, collection):
    options = GndOptions(toCreateCollection=False)
    gndObj, width, height = GndImporter.import_gnd(gnd_path, options, collection)
    translation = mathutils.Vector((-width * NORMALIZING_FACTOR, -width * NORMALIZING_FACTOR, 0))
    # translationMatrix = mathutils.Matrix.Translation(translation)
    gndObj.location = translation

def handleRSM(models_path, rswFile, collectionName):
    rsm_options = RsmOptions(toCreateCollection=False)

    fileNameToObjsMap = dict()
    for rsw_model in rswFile.models:
        filename = rsw_model.filename.replace('\\', os.path.sep)

        # if (filename.startswith("라헬\마을외벽04.rsm") or 
        #     filename.startswith("사막도시\집정관") or 
        #     filename.startswith("사막도시\민가")):
            
        modelCollection = bpy.data.collections.new(filename)
        bpy.data.collections[collectionName].children.link(modelCollection)
        # copy existing objects
        if rsw_model.filename in fileNameToObjsMap:
            bpy.ops.object.select_all(action='DESELECT')
            obj = fileNameToObjsMap[rsw_model.filename]
            modelObj = duplciateObj(obj, collection=modelCollection)
        else:
            # Converts Windows filename separators to the OS's path separator
            rsm_path = os.path.join(models_path, filename)
            modelObj = RsmImporter.import_rsm(rsm_path, rsm_options, modelCollection)
            fileNameToObjsMap[rsw_model.filename] = duplciateObj(modelObj)

        applyTransform(rsw_model, modelObj)


def create(rswFile, filePath, options):
    # Find the data path.
    data_path = get_data_path(filePath)

    # TODO: create an EMPTY object that is the RSW parent object
    collectionName = os.path.basename(filePath)

    collection = bpy.data.collections.new(collectionName)
    bpy.context.scene.collection.children.link(collection)

    # Load the GND file and import it into the scene.
    if options.toImportGND:
        gnd_path = os.path.join(data_path, rswFile.gnd_file)
        handleGND(gnd_path, collection)

    if options.toImportRSM:
        # Load up all the RSM files and import them into the scene.
        models_path = os.path.join(data_path, 'model')
        handleRSM(models_path, rswFile, collectionName)
        
    bpy.context.view_layer.update()