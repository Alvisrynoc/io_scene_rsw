import unittest
from src.gnd.reader import GndReader
from PIL import Image
import math
import os


# path = './data/prt_monk/data/prt_monk.gnd'
# path = './data/mjolnir_10/data/mjolnir_10.gnd'
path = r'C:\Users\Colin\Desktop\data\alberta.gnd'


class TestGndReader(unittest.TestCase):

    def test_reader(self):
        gnd = GndReader.from_file(path)
        self.assertTrue(gnd is not None)


class TestGndConsistency(unittest.TestCase):

    def setUp(self):
        self.gnd = GndReader.from_file(path)

    def test_face_texcoords(self):
        for face in self.gnd.faces:
            for texcoord in face.texcoords:
                self.assertTrue(0.0 <= texcoord <= 1.0)

    def test_face_texture_indices(self):
        for face in self.gnd.faces:
            self.assertLessEqual(face.texture_index, len(self.gnd.textures))

    def test_face_lightmap_indices(self):
        for face in self.gnd.faces:
            self.assertLessEqual(face.lightmap_index, len(self.gnd.lightmaps))

    def test_lightmaps(self):
        # TODO: export lightmap to a big lightmap atlas
        lightmap_count = len(self.gnd.lightmaps)
        dim = int(math.ceil(math.sqrt(lightmap_count * 64) / 8) * 8)
        num_dim = dim / 8
        image = Image.new('L', (dim, dim))
        for i, lightmap in enumerate(self.gnd.lightmaps):
            x, y = int(i % num_dim) * 8, int(i / num_dim) * 8
            for x2 in range(8):
                for y2 in range(8):
                    image.putpixel((x + x2, y + y2), lightmap.luminosity[y2 * 8 + x2])
        image.save('lightmap.bmp')
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
