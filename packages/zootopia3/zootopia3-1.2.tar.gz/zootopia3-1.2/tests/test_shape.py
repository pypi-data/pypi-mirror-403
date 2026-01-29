from zootopia3 import Shape
from numpy import pi

class TestTriangle:
    def test_get_shape_name(self):
        shp = Shape(
            'triangle',
            224,
            224,
            50,
            50,
            (225,0,0),
            'red',
            True,
            True,
        )
        assert shp.get_shape_name() == 'triangle'

class TestRectangle:
    def test_get_image(self):
        shp = Shape(
            'rectangle',
            224,
            224,
            50,
            50,
            (225,0,0),
            'red',
        )
        assert shp.get_image().shape == (224, 224, 3)

class TestCircle:
    def test_get_rgb_name(self):
        shp = Shape(
            'circle',
            224,
            224,
            100,
            1,
            (255,0,0),
            'red',
        )
        assert shp.get_rgb_name() == 'red'

class TestDiamond:
    def test_get_rgb_color(self): 
        shp = Shape(
            'diamond',
            224,
            224,
            50,
            50,
            (255,0,0),
            'red',
        )
        assert shp.get_rgb_color() == (255, 0, 0)