import numpy as np
import numpy.typing as npt
from random import randint
from .triangle import Triangle
from .rectangle import Rectangle
from .circle import Circle
from .diamond import Diamond

__all__ = ['Triangle', 'Rectangle', 'Circle', 'Diamond']

# The file serves as a central import point for shape classes.
# It imports the shape classes from their respective modules
# and defines the __all__ variable to specify the public API of the shapes package.

def create_shape_image(shape, dim1, dim2, *args, **kwargs) -> npt.NDArray[np.uint8]:
    """
    Create an image of a shape superimposed on a white noise background.
    
    Args:
        shape: The shape class (Triangle, Rectangle, Circle, Diamond).
        dim1: size of the horizontal axis of the image
        dim2: size of the vertical axis of the image
        *args: Positional arguments for the shape constructor.
        **kwargs: Keyword arguments for the shape constructor.

    Returns:
        Numpy array representing the image of the shape.
    """
    image_array = np.random.randint(0, 256, (max(dim1, dim2), max(dim1, dim2), 3), dtype=np.uint8)
    shape_instance = shape(*args, **kwargs)
    shape_image = shape_instance.get_image()
    # Overlay the shape image onto the background
    size = max(shape_image.shape[0], shape_image.shape[1])
    x_start = randint(0, image_array.shape[0] - size)
    y_start = randint(0, image_array.shape[1] - size)
    image_array[x_start:x_start+size, y_start:y_start+size] = shape_image
    return image_array

class Shape():
    def __init__(self, 
                    shape_type: str, 
                    dim1: int, 
                    dim2: int, 
                    *args, 
                    **kwargs
                    ):
        shape_classes = {
            'triangle': Triangle,
            'rectangle': Rectangle,
            'circle': Circle,
            'diamond': Diamond
        }
        if shape_type.lower() not in shape_classes:
            raise ValueError(f"Unsupported shape type: {shape_type}")
        self.shape_instance = shape_classes[shape_type.lower()](*args, **kwargs)
        self.shape_name = shape_type.lower()
        self.image = create_shape_image(shape_classes[shape_type.lower()], dim1, dim2, *args, **kwargs)
    def __repr__(self) -> str:
        return f"Shape(shape_type='{self.shape_name}', shape_instance={self.shape_instance.__repr__()})"
    def __str__(self) -> str:
        return f"Shape of type {self.shape_name} embedded in noise background"
    def get_image(self) -> npt.NDArray[np.uint8]:
        """Access array representing RGB pixelated image"""
        return self.image
    def get_rgb_color(self) -> tuple:
        """Access RGB color tuple of primary shape in image"""
        return self.shape_instance.get_rgb_color()
    def get_rgb_name(self) -> str:
        """Access name of color of primary shape in image"""
        return self.shape_instance.get_rgb_name()
    def get_shape_name(self) -> str:
        """Access name of the primary shape in the image"""
        return self.shape_name