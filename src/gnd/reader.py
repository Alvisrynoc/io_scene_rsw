from itertools import islice
import math

import mathutils
import bpy
import os
import bmesh
from ..utils.utils import get_data_path

# https://stackoverflow.com/a/22045226/2209008
def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def create(gndFile, filepath, options, collection):
    name = os.path.splitext(os.path.basename(filepath))[0]
    directory_name = os.path.dirname(filepath)

    mesh = bpy.data.meshes.new(name)

    handleMeshes(gndFile, mesh)

    ''' Create materials. '''
    materials = createMaterials(gndFile, directory_name)

        # if options.should_import_lightmaps:
        #     ''' Add light map texture slot to material.'''
        #     lightmap_texture_slot = material.texture_slots.add()
        #     lightmap_texture_slot.texture = lightmap_texture
        #     lightmap_texture_slot.diffuse_color_factor = options.lightmap_factor
        #     lightmap_texture_slot.blend_type = 'MULTIPLY'
        
    ''' Add materials to mesh. '''
    uv_layer = mesh.uv_layers.new()
    lightmap_uv_texture = mesh.uv_layers.new()

    for material in materials:
        ''' Create UV map. '''
        mesh.materials.append(material)
        # material.texture_slots[0].uv_layer = uv_layer.name
        # if options.should_import_lightmaps:
            # material.texture_slots[1].uv_layer = lightmap_uv_texture.name

    if options.should_import_lightmaps:
        lightmap_tiles_per_dimension = handleLightmap(gndFile)
    '''
    Assign texture coordinates.
    '''
    assignTextureCoordinates(options, gndFile, mesh, lightmap_tiles_per_dimension)

    obj = bpy.data.objects.new(name, mesh)

    if options.createCollection:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    elif collection == None:
        collection = bpy.context.scene.collection
    collection.objects.link(obj)

    # apply location transformation
    offset = mathutils.Vector((-obj.dimensions.x / 4, -obj.dimensions.y / 4, 0))
    obj.location = offset
    bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)

    # obj.dimension
    # bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')

    return obj, gndFile.width, gndFile.height


def handleLightmap(gndFile):
    '''
        Generate light map image.
        '''
    lightmap_size = int(math.ceil(math.sqrt(len(gndFile.lightmaps) * 64) / 8) * 8)
    lightmap_tiles_per_dimension = lightmap_size / 8
    pixel_count = lightmap_size * lightmap_size
    pixels = [0.0] * (pixel_count * 4)
    for i, lightmap in enumerate(gndFile.lightmaps):
        x, y = int(i % lightmap_tiles_per_dimension) * 8, int(i / lightmap_tiles_per_dimension) * 8
        for y2 in range(8):
            for x2 in range(8):
                idx = y2 * 8 + x2
                lum = lightmap.luminosity[idx]
                j = int(((y + y2) * lightmap_size) + (x + x2)) * 4
                r = lum / 255.0
                pixels[j + 0] = r
                pixels[j + 1] = r
                pixels[j + 2] = r
                pixels[j + 3] = 1.0
    lightmap_image = bpy.data.images.new('lightmap', lightmap_size, lightmap_size)
    lightmap_image.pixels = pixels

    ''' Create light map texture. '''
    lightmap_texture = bpy.data.textures.new('lightmap', type='IMAGE')
    lightmap_texture.image = lightmap_image
    return lightmap_tiles_per_dimension


def assignTextureCoordinates(options, gndFile, mesh, lightmap_tiles_per_dimension):
    uv_layer = mesh.uv_layers[0]
    lightmap_uv_layer = mesh.uv_layers[1]
    for FaceIndex, face in enumerate(gndFile.faces):
        uvs = list(face.uvs)
        '''
        Since we are adding quads and not triangles, we need to
        add the UVs in quad clockwise winding order.
        '''
        uvs = [uvs[x] for x in [0, 1, 3, 2]]
        for i, uv in enumerate(uvs):
            # UVs have to be V-flipped
            uv = uv[0], 1.0 - uv[1]
            uv_layer.data[FaceIndex * 4 + i].uv = uv
        if options.should_import_lightmaps:
            x1 = (face.lightmap_index % lightmap_tiles_per_dimension) / lightmap_tiles_per_dimension
            y1 = int(face.lightmap_index / lightmap_tiles_per_dimension) / lightmap_tiles_per_dimension
            x2 = x1 + (1.0 / lightmap_tiles_per_dimension)
            y2 = y1 + (1.0 / lightmap_tiles_per_dimension)
            lightmap_uvs = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            for i, uv in enumerate(lightmap_uvs):
                lightmap_uv_layer.data[FaceIndex * 4 + i].uv = uv


def handleMeshes(gndFile, mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    for y in range(gndFile.height):
        for x in range(gndFile.width):
            tile_index = y * gndFile.width + x
            tile = gndFile.tiles[tile_index]
            if tile.face_indices[0] != -1:  # +Z
                bm.verts.new(((x + 0) * gndFile.scale, (y + 0) * gndFile.scale, -tile[0]))
                bm.verts.new(((x + 1) * gndFile.scale, (y + 0) * gndFile.scale, -tile[1]))
                bm.verts.new(((x + 1) * gndFile.scale, (y + 1) * gndFile.scale, -tile[3]))
                bm.verts.new(((x + 0) * gndFile.scale, (y + 1) * gndFile.scale, -tile[2]))
            if tile.face_indices[1] != -1:  # +Y
                adjacent_tile = gndFile.tiles[tile_index + gndFile.width]
                bm.verts.new(((x + 0) * gndFile.scale, (y + 1) * gndFile.scale, -tile[2]))
                bm.verts.new(((x + 1) * gndFile.scale, (y + 1) * gndFile.scale, -tile[3]))
                bm.verts.new(((x + 1) * gndFile.scale, (y + 1) * gndFile.scale, -adjacent_tile[1]))
                bm.verts.new(((x + 0) * gndFile.scale, (y + 1) * gndFile.scale, -adjacent_tile[0]))
            if tile.face_indices[2] != -1:  # +X
                adjacent_tile = gndFile.tiles[tile_index + 1]
                bm.verts.new(((x + 1) * gndFile.scale, (y + 1) * gndFile.scale, -tile[3]))
                bm.verts.new(((x + 1) * gndFile.scale, (y + 0) * gndFile.scale, -tile[1]))
                bm.verts.new(((x + 1) * gndFile.scale, (y + 0) * gndFile.scale, -adjacent_tile[0]))
                bm.verts.new(((x + 1) * gndFile.scale, (y + 1) * gndFile.scale, -adjacent_tile[2]))

    bm.verts.ensure_lookup_table()

    vertex_offset = 0
    for y in range(gndFile.height):
        for x in range(gndFile.width):
            tile_index = y * gndFile.width + x
            tile = gndFile.tiles[tile_index]
            for face_index in filter(lambda x: x >= 0, tile.face_indices):
                face = gndFile.faces[face_index]
                vertex_indices = [vertex_offset + i for i in range(4)]
                bmface = bm.faces.new([bm.verts[x] for x in vertex_indices])
                bmface.material_index = face.texture_index
                vertex_offset += 4

    bm.faces.ensure_lookup_table()
    bm.to_mesh(mesh)


def createMaterials(gndFile, directory_name):
    materials = []
    for texture in gndFile.textures:
        texture_path = texture.path
        material = bpy.data.materials.new(texture_path)
        material.specular_intensity = 0.0
        material.use_nodes = True
        materials.append(material)

        bsdf = material.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Specular'].default_value = 0.0
        texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
        material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

        ''' Load diffuse texture. '''
        diffuse_texture = bpy.data.textures.new(texture_path, type='IMAGE')
        data_path = get_data_path(directory_name)
        texpath = os.path.join(data_path, 'texture', texture_path)

        try:
            texImage.image = bpy.data.images.load(texpath, check_existing=True)
        except RuntimeError:
            pass
    return materials
