from ..io.reader import BinaryFileReader
import pathlib

from ..ver.version import Version
from enum import IntEnum

class RswObjectType(IntEnum):
    MODEL = 1
    LIGHT = 2
    SOUND = 3
    EFFECT = 4

class Water:
    def __init__(self, reader, version):
        self.height = 0.0
        self.type = 0
        self.amplitude = 0.0
        self.phase = 0.0
        self.surface_curve_level = 0.0
        self.texture_cycling = 0

        if version >= Version(1, 3):
            self.height = reader.read_s('f')
        if version >= Version(1, 8):
            self.type = reader.read_s('I')
            self.amplitude = reader.read_s('f')
            self.phase = reader.read_s('f')
            self.surface_curve_level = reader.read_s('f')
        if version >= Version(1, 9):
            self.texture_cycling = reader.read_s('I')

class Lighting:
    def __init__(self, reader, version):
        self.longitude = 45
        self.latitude = 45
        self.ambient = (0.0, 0.0, 0.0)
        self.diffuse = (0.0, 0.0, 0.0)
        self.shadow = (0.0, 0.0, 0.0)
        self.alpha = 0.0

        if version >= Version(1, 5):
            self.longitude, self.latitude = reader.read('2I')  # garbo? (45, 15)

        self.diffuse = reader.read('3f')
        self.ambient = reader.read('3f')
        self.alpha = reader.read('f')[0]

class Model(object):
    def __init__(self, reader, version):
        self.name = ''
        self.filename = ''
        self.reserved = ''
        self.type = ''
        self.sound = ''
        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0)
        self.scale = (1.0, 1.0, 1.0)

        if version >= Version(1, 3):
            self.name = reader.read_fixed_length_null_terminated_string()
            self.animation_type = reader.read_s('I')
            self.animation_speed = reader.read_s('f')
            self.block_type = reader.read_s('I')
        if version >= Version(2, 6): # and build number > 161
            _ = reader.read('c') # unknown field        
        self.filename = reader.read_fixed_length_null_terminated_string(80)
        self.node_name = reader.read_fixed_length_null_terminated_string(80)
        self.position = reader.read('3f')
        self.rotation = reader.read('3f')
        self.scale = reader.read('3f')

class LightSource:
    def __init__(self, reader):
        self.name = reader.read_fixed_length_null_terminated_string(80)
        self.position = reader.read('3f')
        self.color = reader.read('3I')
        self.range = reader.read_s('f')

class Sound:
    def __init__(self, reader, version):
        self.name = reader.read_fixed_length_null_terminated_string(80)
        self.file_name = reader.read_fixed_length_null_terminated_string(80)
        self.position = reader.read('3f')
        self.volume = reader.read_s('f')
        self.width = reader.read_s('I')
        self.height = reader.read_s('I')
        self.range = reader.read_s('I')
        if version >= Version(2, 0):
            self.cycle = reader.read_s('f')

class Effect:
    def __init__(self, reader):
        self.name = reader.read_fixed_length_null_terminated_string(80)
        self.position = reader.read('3f')
        self.type = reader.read('I')[0]
        self.emit_speed = reader.read_s('f')
        self.param = reader.read('4f')

class Rsw(object):
    def __init__(self, filePath: pathlib.Path):
        self.ini_file = ''
        self.gnd_file = ''
        self.gat_file = ''
        self.src_file = ''
        # self.water = Rsw.Water()
        # self.light = Rsw.Lighting()
        self.models = []
        self.light_sources = []
        self.sounds = []
        self.effects = []

        with open(filePath, 'rb') as f:
            reader = BinaryFileReader(f)
            magic = reader.read_s('4s')
            if magic != b'GRSW':
                raise RuntimeError('Invalid file type.')
            self.version = Version(*reader.read('2B'))
            self.ini_file = reader.read_fixed_length_null_terminated_string(40)
            self.gnd_file = reader.read_fixed_length_null_terminated_string(40)
            if self.version >= Version(1, 4):
                self.gat_file = reader.read_fixed_length_null_terminated_string(40)
            self.src_file = reader.read_fixed_length_null_terminated_string(40)
            
            # WATER
            self.water = Water(reader, self.version)

            # LIGHT
            self.light = Lighting(reader, self.version)

            # GROUND
            if self.version >= Version(1, 6):
                top, bottom, left, right = reader.read('4I')
            # unknown = reader.read('I')[0]
            object_count = reader.read_s('I')
            for _ in range(object_count):
                object_type = reader.read_s('I')
                if object_type == RswObjectType.MODEL:
                    model = Model(reader, self.version)
                    self.models.append(model)
                elif object_type == RswObjectType.LIGHT:
                    light = LightSource(reader)
                    self.light_sources.append(light)
                elif object_type == RswObjectType.SOUND:
                    sound = Sound(reader, self.version)
                    self.sounds.append(sound)
                elif object_type == RswObjectType.EFFECT:
                    effect = Effect(reader)
                    self.effects.append(effect)
                else:
                    raise RuntimeError('Invalid object type.')
            # QUAD TREE
            if self.version >= Version(2, 1):
                # Not necessary for our purposes, so just ignore it.
                pass
