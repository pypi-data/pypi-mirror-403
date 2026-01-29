import numpy as np
import numpy.typing as npt

def create_rectangle_image(width: int, 
                            height: int, 
                            rgb_color: tuple,
                            ) -> npt.NDArray[np.uint8]:
    """
    Create a rectangle with RGB color in a square pixel image.
    
    Args:
        width: The width of the rectangle in pixels.
        height: The height of the rectangle in pixels.
        rgb_color: Tuple of (R, G, B) values (0-255)

    Returns:
        (max(width, height), max(width, height), 3) numpy array representing 
        the image with a colored rectangle on black background.
    """
    # Create black background
    square_length = max(width, height)  
    image_array = np.random.randint(0, 256, (square_length, square_length, 3), dtype=np.uint8)
    
    # Create mask for rectangle
    mask = (np.arange(square_length).reshape(-1, 1) < height) & (np.arange(square_length).reshape(1, -1) < width)
    
    # Apply RGB color to rectangle area
    image_array[mask] = rgb_color
    
    return image_array

class Rectangle:
    '''Class representing a rectangle shape with various properties and methods.'''
    def __init__(self, 
                    width: int, 
                    height: int, 
                    rgb_color: tuple, 
                    rgb_name: str,
                    upside_down: bool = False,
                    sideways: bool = False,
                    ) -> None:
        '''Initialize a Rectangle instance.
        
        Args:
            width: The width of the rectangle in pixels.
            height: The height of the rectangle in pixels.
            rgb_color: Tuple of (R, G, B) values (0-255).
            rgb_name: Name of the RGB color.
            upside_name: this does nothing
            sideways: this does nothing
        '''
        self.width = width
        self.height = height
        self.rgb_color = rgb_color
        self.rgb_name = rgb_name
        self.image = create_rectangle_image(width, height, rgb_color)
    def __repr__(self) -> str:
        return f"Rectangle(width={self.width}, height={self.height}, rgb_color={self.rgb_color})"
    def __str__(self) -> str:
        return f"Rectangle of width {self.width}, height {self.height} with color {self.rgb_name}"
    def get_image(self) -> npt.NDArray[np.uint8]:
        return self.image
    def get_width(self) -> int:
        return self.width
    def get_height(self) -> int:
        return self.height
    def get_rgb_color(self) -> tuple:
        """Get the (R,G,B) tuple encoding of color"""
        return self.rgb_color
    def get_rgb_name(self) -> str:
        """Get the user-specified name of the color"""
        return self.rgb_name
    def get_area(self) -> int:
        """Calculate the area of the rectangle."""
        return self.width * self.height
    def get_perimeter(self) -> int:
        """Calculate the perimeter of the rectangle."""
        return 2 * (self.width + self.height)
    def is_square(self) -> bool:
        return self.width == self.height