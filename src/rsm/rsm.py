import pathlib
from ..io.reader import BinaryFileReader
from ..semver.version import Version
import math

class ScaleKeyFrame(object):
    def __init__(self, reader: BinaryFileReader, version: Version):
        # self.frame = 0
        # self.rotation = (0.0, 0.0, 0.0, 0.0)
        self.time = reader.read_s('i')
        self.frames = reader.read('3f')
        self.scale = reader.read('f')
        # to be removed??
        # if version >= Version(2, 2):
        #     self.time = math.ceil(self.time * fps)

class RotationKeyFrame(object):
    def __init__(self, reader: BinaryFileReader, version: Version):
        # self.frame = 0
        # self.rotation = (0.0, 0.0, 0.0, 0.0)
        self.time = reader.read_s('i')
        self.frames = reader.read('4f')

        # to be removed??
        # if version >= Version(2, 2):
        #     self.time = math.ceil(self.time * fps)

class LocationKeyFrame(object):
    def __init__(self, reader: BinaryFileReader):
        # self.frame = 0
        # self.location = (0.0, 0.0, 0.0)
        self.time = reader.read_s('i')
        self.frames = reader.read('3f')
        self.data = reader.read('f')
        # to be removed??
        # if version >= Version(2, 2):
        #     self.time = math.ceil(self.time * fps)

class Face(object):
    def __init__(self, reader: BinaryFileReader, version: Version):
        # self.vertex_indices = (0, 0, 0)
        # self.texcoord_indices = (0, 0, 0)
        # self.unk1 = None

        length = -1
        if version >= Version(2, 2):
            length = reader.read_s('i')

        self.vertex_indices = reader.read('3H')
        self.texcoord_indices = reader.read('3H')
        self.texture_index = reader.read_s('H')
        self.padding = reader.read_s('H')
        self.twoSided = reader.read_s('I')
        
        # smooth group
        if version >= Version(1, 2):
            smoothGroup = [-1] * 3
            smoothGroup[0] = reader.read_s('I')
            if length > 24:
                smoothGroup[1] = reader.read_s('I')
            if length > 28:
                smoothGroup[2] = reader.read_s('I')
            if length > 32:
                raise RuntimeWarning("too many smooth groups")
            self.smoothGroup = tuple(group for group in smoothGroup if group != -1)

class Node:
    def __init__(self, reader: BinaryFileReader, version: Version):
        # self.name = ''
        # self.parent_name = ''
        # self.texture_indices = [] # = textures
        # self.vertices = []
        # self.texcoords = []
        # self.faces = []
        # self.location_keyframes = []
        # self.rotation_keyframes = []

        if version >= Version(2, 2):
            nameLength = reader.read_s('I')
            self.name = reader.read_s(f'{nameLength}c')
            parentNameLength = reader.read_s('I')
            self.parent_name = reader.read(f'{parentNameLength}c')
        else:
            self.name = reader.read_fixed_length_null_terminated_string()
            self.parent_name = reader.read_fixed_length_null_terminated_string()

        # read texture
        self.texture_indices = []
        if version >= Version(2, 3):
            textureCount = reader.read_s('I')
            for _ in range(textureCount):
                textureFileNameLength = reader.read_s('I')
                if textureFileNameLength < 0 or textureFileNameLength > 1024:
                    raise RuntimeError("errorneous texture file name Length")
                textureFileName = reader.read_s(f'{textureFileNameLength}c')
                # remember textureFileName
                # texture in node class needs to remmeber textureFileName
                # texture RSM class needs to remember textureFileNameLength ? Rsm.cpp line 247-260
        else:
            textureCount = reader.read_s('I')
            self.texture_indices = reader.read(f'{textureCount}I')
        
        self.offsetMatrix = (reader.read('3f'), reader.read('3f'), reader.read('3f'))
        self.offset = reader.read('3f') # displacement of mesh

        # process location, rotation and scale
        if version >= Version(2, 2):
            self.position = (0, 0, 0)
            # rotation_angle = 0
            # rotation_axis = (0, 0, 0)
            self.rotation = (0, 0, 0, 0) # angle-axis
            self.scale = (0, 0, 0)
        else:
            self.position = reader.read('3f') # displacement of object
            self.rotation = reader.read('4f')
            self.scale = reader.read('3f')

        # process vertex count
        self.vertices = []
        vertexCount = reader.read_s('I')
        for _ in range(vertexCount):
            self.vertices.append(reader.read('3f'))
            # vertex = np.array(reader.read('3f'))
            # vertex = np.append(vertex, [1])
            # self.vertices.append(tuple(offsetMatrix @ vertex)[:-1])

        # process texture coordinate
        textureCoordinateCount = reader.read_s('I')
        self.texcoords = []
        for _ in range(textureCoordinateCount):
            if version >= Version(1, 2):
                color = reader.read_s('f')
            textureCoordinate = reader.read('2f')
            self.texcoords.append(textureCoordinate)

        # process faces
        faceCount = reader.read_s('I')
        self.faces = []
        for _ in range(faceCount):
            face = Face(reader, version)
            if any([vertex >= vertexCount for vertex in face.vertex_indices]):
                continue
            # apply normalize on face???
            self.faces.append(face)

        # handle shade type?? rsm.cpp line 382-384
        # handle shade type: smooth line 386-411

        # handle scaleKeyFrames
        if version >= Version(1, 6):
            scaleKeyFrameCount = reader.read_s('i')
            self.scaleKeyFrames = [ScaleKeyFrame(reader, version) for _ in range(scaleKeyFrameCount)]

        # handle rotationKeyFrames
        rotationKeyFrameCount = reader.read_s('i')
        self.rotationKeyFrames = [RotationKeyFrame(reader, version) for _ in range(rotationKeyFrameCount)]

        # handle locationKeyFrames
        if version >= Version(2, 2):
            locationKeyFrameCount = reader.read_s('i')
            self.locationkeyFrames = [LocationKeyFrame(reader) for _ in range(locationKeyFrameCount)]
            
        # if version >= Version(2, 3):
        #     textureAnimCount = reader.read_s('i')
        #     for _ in range(textureAnimCount):
        #         textureID = reader.read_s('i')
        #         textureIDAnimCount = reader.read_s('i')
        #         for _ in range(textureIDAnimCount):
        #             type_ = reader.read_s('i')
        #             amountFrames = reader.read_s('i')
        #             for _ in range(amountFrames):
        #                 frame = reader.read_s('i')
        #                 offset = reader.read_s('f')

class Rsm:
    def __init__(self, path: pathlib.Path):
        # self.main_node = ''
        # self.shade_type = 0
        # self.alpha = 0xff
        # self.anim_length = 0
        # self.textures = []
        # self.nodes = []

        with open(path, 'rb') as inputFile:
            reader = BinaryFileReader(inputFile)
            
            # magic
            magic = reader.read_s('4s')
            if magic != b"GRSM":
                raise RuntimeError("Unrecognized header")
            
            self.version = Version(reader.read_s('B'), reader.read_s('B'))
            # print("version:", self.version.major, self.version.minor)

            self.anim_length = reader.read_s('I')

            self.shade_type = reader.read_s('I')

            if self.version >= Version(1, 4):
                self.alpha = reader.read_s('B')
            else:
                self.alpha = 0xFF
            
            self.rootMeshName = []
            # read mesh, texture
            if self.version >= Version(2, 3):
                # why does it read anim_length again?
                self.anim_length = math.ceil(self.anim_length * reader.read('f'))

                self.rootMeshCount = reader.read_s('I')
                if (self.rootMeshCount > 1):
                    raise RuntimeWarning("The file contains multiple root meshes, which is not supported!")
            
                for _ in range(self.rootMeshCount):
                    rootMeshNameLength = reader.read_s('I')
                    if rootMeshNameLength < 0 or rootMeshNameLength > 1024:
                        raise RuntimeError("erroneous root mesh name length")
                    rootMeshName = reader.read_s(f'{rootMeshNameLength}c')
                    self.rootMeshName.append(rootMeshName)
            
            elif self.version >= Version(2, 2):
                fps = reader.read_s('f')
                textureCount = reader.read_s('I')
                if textureCount < 0 or textureCount > 100:
                    raise RuntimeError("erroneous texture count")
                
                for idx in range(textureCount):
                    textureNameLength = reader.read_s('I')
                    self.texturePaths.append(reader.read_s(f'{textureNameLength}c'))

                self.rootMeshCount = reader.read_s('I')
                if (self.rootMeshCount > 1):
                    raise RuntimeWarning("The file contains multiple root meshes, which is not supported!")

                for _ in range(self.rootMeshCount):
                    rootMeshNameLength = reader.read_s('I')
                    if rootMeshNameLength < 0 or rootMeshNameLength > 1024:
                        raise RuntimeError("erroneous root mesh name length")
                    rootMeshName = reader.read_s(f'{rootMeshNameLength}c')
                    self.rootMeshName.append(rootMeshName)

            else:
                _ = reader.read_s('16B') # unknown field

                textureCount = reader.read_s('I')
                if textureCount < 0 or textureCount > 100:
                    raise RuntimeError("erroneous texture count")
                
                self.texturePaths = [reader.read_fixed_length_null_terminated_string() for _ in range(textureCount)]
                
                # should be named main node
                rootMeshName = reader.read_fixed_length_null_terminated_string()
                self.rootMeshName.append(rootMeshName)

            # read mesh
            self.main_node = self.rootMeshName[0]
            meshCount = reader.read_s('I')
            self.nodes = [Node(reader, self.version) for _ in range(meshCount)]