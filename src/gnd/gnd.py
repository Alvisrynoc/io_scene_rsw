import pathlib
import itertools
from ..io.reader import BinaryFileReader
from ..ver.version import Version

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(itertools.islice(it, size)), ())

class Lightmap(object):
    def __init__(self, luminosity, color):
        self.luminosity = luminosity
        self.color = color

class Texture(object):
    def __init__(self, path=''):
        self.path = path
        self.data = None

class Tile(object):
    def __init__(self, height, faceIndices):
        self.heights = height
        self.face_indices = faceIndices

    def __getitem__(self, item):
        return self.heights[item]

class Face(object):
    def __init__(self, texcoords, textureIndex, lightmapIndex, lighting):
        self.texcoords = texcoords
        self.texture_index = textureIndex
        self.lightmap_index = lightmapIndex
        self.lighting = lighting

    @property
    def uvs(self):
        for i in range(4):
            yield (self.texcoords[i], self.texcoords[i + 4])

class Gnd(object):
    def handleTextures(self, reader):
        textureCount = reader.read_s('I')
        textureNameLength = reader.read_s('I')
        textures = []

        for _ in range(textureCount):
            texturePath = reader.read_fixed_length_null_terminated_string(textureNameLength)
            textures.append(Texture(texturePath))
        return textures

    def handleLightmaps(self, reader):
        lightmapCount = reader.read_s('I')
        lightmap_size = reader.read('3I')
        lightmaps = []

        # this is related, in some way, to the tile faces
        for _ in range(lightmapCount):
            luminosity = reader.read('64B')
            color = list(chunk(reader.read('192B'), 3))
            lightmap = Lightmap(luminosity, color)
            lightmaps.append(lightmap)
        return lightmap_size, lightmaps
    
    def handleFaces(self, reader):
        faceCount = reader.read_s('I')
        faces = []
        for _ in range(faceCount):
            texcoords = reader.read('8f')
            textureIndex = reader.read_s('H')
            lightmapIndex = reader.read_s('H')
            lighting = reader.read('4B') # colors and alpha, B, G, R and A
            faces.append(Face(texcoords, textureIndex, lightmapIndex, lighting))
        return faces

    def handleTiles(self, reader):
        tiles = []
        for _ in range(self.width):
            for _ in range(self.height):
                height = reader.read('4f')
                if self.version >= Version(1, 6):
                    faceIndices = reader.read('3i')
                    tiles.append(Tile(height, faceIndices))
                else:
                    faceIndices = reader.read('4i')
                    effectiveFaceIndices = (faceIndices[0], faceIndices[1], faceIndices[2])
                    tiles.append(Tile(height, effectiveFaceIndices))
        return tiles

    def __init__(self, path: pathlib.Path):
        with open(path, 'rb') as inputFile:
            reader = BinaryFileReader(inputFile)

            # magic
            magic = reader.read_s('4s')
            if magic != b'GRGN':
                raise RuntimeError('Unrecognized file format.')

            # version, width, height and scale
            self.version = Version(*reader.read('2B'))
            self.width, self.height = reader.read('2I')
            self.scale = reader.read_s('f')

            # textures, lightmaps, faces, tiles
            self.textures = self.handleTextures(reader)
            self.lightmap_size, self.lightmaps = self.handleLightmaps(reader)
            self.faces = self.handleFaces(reader)
            self.tiles = self.handleTiles(reader)