import os
from collections import defaultdict

import bpy
import bmesh
import mathutils

from ..utils import utils

def createTexture(material):
    bsdf = material.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Specular'].default_value = 0.0
    texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
    material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    return texImage

def loadTexture(texImage, texturePath):
    try:
        texImage.image = bpy.data.images.load(texturePath, check_existing=True)
    except RuntimeError:
        print(f"loading texture fails for {texturePath}!")

def handleTexture(dataPath, texturePaths):
    materials = []
    for subTexturePath in texturePaths:
        material = bpy.data.materials.new(subTexturePath)
        material.specular_intensity = 0.0
        material.use_nodes = True
        materials.append(material)

        texImage = createTexture(material)
        loadTexture(texImage, os.path.join(dataPath, 'texture', subTexturePath))
    return materials

def buildSmoothGroup(bm, node, importSmoothGroups: bool):
    smoothGroupFaces = defaultdict(lambda: [])
    for faceIndex, face in enumerate(node.faces):
        try:
            bmface = bm.faces.new([bm.verts[x] for x in face.vertex_indices])
            bmface.material_index = face.texture_index
        except ValueError as e:
            # TODO: we need more solid error handling here as a duplicate face throws off the UV assignment.
            raise NotImplementedError
        if importSmoothGroups:
            bmface.smooth = True
            for smoothGroup in face.smoothGroup:
                smoothGroupFaces[smoothGroup].append(faceIndex)

    bm.faces.ensure_lookup_table()
    return smoothGroupFaces

def assignTextureCoordinates(node, UVtexture):
    for faceIndex, face in enumerate(node.faces):
        uvs = [node.texcoords[x] for x in face.texcoord_indices]
        for i, uv in enumerate(uvs):
            # UVs have to be V-flipped (maybe)
            uv = uv[0], 1.0 - uv[1]
            UVtexture.data[faceIndex * 3 + i].uv = uv

def applySmoothGroup(mesh, smoothGroupFaces):
    for _, faceIndices in smoothGroupFaces.items():
        '''
        Select all faces in the smoothing group.
        '''
        bpy.ops.object.mode_set(mode='OBJECT')
        for faceIndex in faceIndices:
            mesh.polygons[faceIndex].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        '''
        Mark boundary edges as sharp.
        '''
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.mark_sharp()
    bpy.ops.object.mode_set(mode='OBJECT')

def addEdgeSplitModifier(obj):
    edge_split_modifier = obj.modifiers.new('EdgeSplit', type='EDGE_SPLIT')
    edge_split_modifier.use_edge_angle = False
    edge_split_modifier.use_edge_sharp = True

def handleMesh(node, materials, importSmoothGroups: bool):
    mesh = bpy.data.meshes.new(node.name)
    mesh.uv_layers.new()

    bm = bmesh.new()
    bm.from_mesh(mesh)

    for textureIndex in node.texture_indices:
        mesh.materials.append(materials[textureIndex])

    for vertex in node.vertices:
        bm.verts.new(vertex)
    bm.verts.ensure_lookup_table()

    smoothGroupFaces = buildSmoothGroup(bm, node, importSmoothGroups)
    bm.to_mesh(mesh)

    offsetMatrix = mathutils.Matrix(node.offsetMatrix)
    offset = offsetMatrix @ mathutils.Vector(node.offset)
    TMatrix = mathutils.Matrix.Translation(offset)
    mesh.transform(TMatrix)

    assignTextureCoordinates(node, mesh.uv_layers[0])
    return mesh, smoothGroupFaces

def recenterByBoundBox(obj):
    cornerCoordinates = [mathutils.Vector(cornerCoordinate) for cornerCoordinate in obj.bound_box]
    boundBoxCenter = sum(cornerCoordinates, mathutils.Vector()) / len(cornerCoordinates)
    for ele in obj.bound_box:
        print(mathutils.Vector(ele))
    minZ = min([z for x, y, z in cornerCoordinates])
 
    # obj.location -= mathutils.Vector((boundBoxCenter.x, boundBoxCenter.y, obj.location.z + minZ))
    obj.location = mathutils.Vector((-boundBoxCenter.x, -boundBoxCenter.y, -minZ))
    print(f"{boundBoxCenter=}")
    print(f"{minZ=}")

def printBound(obj):
    cornerCoordinates = [mathutils.Vector(cornerCoordinate) for cornerCoordinate in obj.bound_box]
    boundBoxCenter = sum(cornerCoordinates, mathutils.Vector()) / len(cornerCoordinates)
    for ele in obj.bound_box:
        print(mathutils.Vector(ele))
    minZ = min([z for x, y, z in cornerCoordinates])
    print(f"{boundBoxCenter=}")
    print(f"{minZ=}")

def recenterByBoundBoxNew(obj):
    cornerCoordinates = [mathutils.Vector(cornerCoordinate) for cornerCoordinate in obj.bound_box]
    boundBoxCenter = sum(cornerCoordinates, mathutils.Vector()) / len(cornerCoordinates)
    minZ = min([z for x, y, z in cornerCoordinates])
    obj.location = mathutils.Vector((-boundBoxCenter.x, -boundBoxCenter.y, -minZ))

def calculateResetVector(obj):
    cornerCoordinates = [mathutils.Vector(cornerCoordinate) for cornerCoordinate in obj.bound_box]
    boundBoxCenter = sum(cornerCoordinates, mathutils.Vector()) / len(cornerCoordinates)
    minZ = min([z for x, y, z in cornerCoordinates])
    return mathutils.Vector((-boundBoxCenter.x, -boundBoxCenter.y, -minZ))

def recenterByBoundBoxNewLocal(obj, resetVec):
    translationMatrix = mathutils.Matrix.Translation(resetVec)
    obj.matrix_basis @= translationMatrix

def applyMeshTransform(mesh, node):
    offsetMatrix = mathutils.Matrix(node.offsetMatrix)

    axisVec = offsetMatrix @ mathutils.Vector(node.rotation[1:])
    rotationMatrix = mathutils.Matrix.Rotation(node.rotation[0], 4, axisVec)
    rotationEuler = rotationMatrix.to_euler()

    mesh.rotation_euler.rotate(rotationEuler)


def applyTransform(obj, node):
    offsetMatrix = mathutils.Matrix(node.offsetMatrix)

    # rotation
    axisVec = offsetMatrix @ mathutils.Vector(node.rotation[1:])
    rotationMatrix = mathutils.Matrix.Rotation(node.rotation[0], 4, axisVec)
    rotationEuler = rotationMatrix.to_euler()
    obj.rotation_euler.rotate(rotationEuler)

    # translation
    position = offsetMatrix @ mathutils.Vector(node.position)
    obj.location += position

    # scale
    scale = offsetMatrix @ mathutils.Vector(node.scale)
    obj.scale.x *= scale.x
    obj.scale.y *= scale.y
    obj.scale.z *= -scale.z
    return obj

def create(rsmFile, filePath, options, collection = None):
    fileName = os.path.basename(filePath)
    dataPath = utils.get_data_path(filePath)

    materials = handleTexture(dataPath, rsmFile.texturePaths)

    # create collection
    if options.createCollection:
        collection = bpy.data.collections.new(fileName)
        bpy.context.scene.collection.children.link(collection)
        
    elif collection == None:
        collection = bpy.context.scene.collection

    # create root obj
    # rootObj = bpy.data.objects.new(fileName, None)
    # collection.objects.link(rootObj)

    objs = {}
    for node in rsmFile.nodes:
        mesh, smoothGroupFaces = handleMesh(node, materials, options.importSmoothGroups)

        obj = bpy.data.objects.new(node.name, mesh)
        collection.objects.link(obj)

        bpy.ops.object.select_all(action='DESELECT')
        if options.importSmoothGroups:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            applySmoothGroup(mesh, smoothGroupFaces)
            addEdgeSplitModifier(obj)
        bpy.ops.rigidbody.objects_add(type='PASSIVE')
        bpy.ops.rigidbody.shape_change(type='MESH')
        obj.select_set(True)

        bpy.ops.object.select_all(action='DESELECT')

        applyTransform(obj, node)
        objs[node.name] = obj

    for node in rsmFile.nodes:
        if node.parent_name != "":
            objs[node.name].parent = objs[node.parent_name]
        else:
            mainObj = objs[node.name]
        # objs[node.name] = obj

        # if node.parent_name == "":
        #     obj.parent = rootObj

    # # parent objects
    # for node in rsmFile.nodes:
    #     if node.parent_name == '':
    #         continue

    #     obj = objs[node.name]
    #     obj.parent = objs[node.parent_name].parent
    
    # # apply parent transform to children
    # for parent in rsmFile.nodes:
    #     if parent.parent_name != "":
    #         continue

    #     # node is a parent node
    #     for child in rsmFile.nodes:
    #         if child.parent_name != parent.name:
    #             continue

    #         obj = objs[child.name]
    #         applyTransform(obj, parent)

    bpy.context.view_layer.update()
    # return rootObj
    return mainObj
