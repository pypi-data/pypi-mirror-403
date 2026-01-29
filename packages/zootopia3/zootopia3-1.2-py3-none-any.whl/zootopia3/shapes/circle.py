import numpy as np
import numpy.typing as npt

def create_circle_image(width: int, rgb_color: tuple) -> npt.NDArray[np.uint8]:
    """
    Create a circle with RGB color in a square pixel image.
    
    Args:
        width: The width/diameter of the circle in pixels.
        rgb_color: Tuple of (R, G, B) values (0-255)
    
    Returns:
        (diameter, diameter, 3) numpy array representing the image with a colored circle on black background.
    """
    # Create black background
    diameter = width
    radius = width // 2
    image_array = np.random.randint(0, 256, (diameter, diameter, 3), dtype=np.uint8)
    
    # Create coordinate grids
    y, x = np.ogrid[:diameter, :diameter]
    center = radius
    
    # Create mask for circle
    mask = (x - center) ** 2 + (y - center) ** 2 <= radius ** 2
    
    # Apply RGB color to circle area
    image_array[mask] = rgb_color
    
    return image_array

class Circle:
    '''Class representing a circle shape with various properties and methods.'''
    def __init__(self, 
                    width: int,
                    height: int, 
                    rgb_color: tuple, 
                    rgb_name: str,
                    upside_down: bool = False,
                    sideways: bool = False,
                    ) -> None:
        '''Initialize a Circle instance.

        Args:
            width: This is analogous to diameter.
            height: this does nothing
            rgb_color: Tuple of (R, G, B) values (0-255).
            rgb_name: Name of the RGB color.
            upside_down: this does nothing
            sideways: this does nothing
        '''
        self.width = width
        self.rgb_color = rgb_color
        self.rgb_name = rgb_name
        self.image = create_circle_image(width, rgb_color)
    def __repr__(self) -> str:
        return f"Circle(width={self.width}, rgb_color={self.rgb_color})"
    def __str__(self) -> str:
        return f"Circle of width {self.width} with color {self.rgb_name}"
    def get_image(self) -> npt.NDArray[np.uint8]:
        return self.image
    def get_width(self) -> int:
        """Get the diameter of the circle"""
        return self.width
    def get_rgb_color(self) -> tuple:
        """Get the (R,G,B) tuple encoding of color"""
        return self.rgb_color
    def get_rgb_name(self) -> str:
        """Get the user-specified name of the color"""
        return self.rgb_name
    def get_area(self) -> float:
        """Calculate the area of the circle."""
        return np.pi * (self.width / 2) ** 2
    def get_circumference(self) -> float:
        """Calculate the circumference of the circle."""
        return np.pi * self.width