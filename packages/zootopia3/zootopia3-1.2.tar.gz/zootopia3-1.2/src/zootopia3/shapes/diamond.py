import numpy as np
import numpy.typing as npt

def create_diamond_image(width: int, height: int, rgb_color: tuple) -> npt.NDArray[np.uint8]:
    """
    Create a diamond (diamond shape) with RGB color in a square pixel image.
    
    Args:
        width: The length of the horizontal diagonal in pixels.
        height: The length of the vertical diagonal in pixels.
        rgb_color: Tuple of (R, G, B) values (0-255)

    Returns:
        (max(width, height), max(width, height), 3) numpy array representing 
        the image with a colored diamond on black background.
    """
    # Create black background
    square_length = max(width, height)  
    image_array = np.random.randint(0, 256, (square_length, square_length, 3), dtype=np.uint8)
    
    # Create coordinate grids
    y, x = np.ogrid[:square_length, :square_length]
    center_x = square_length // 2
    center_y = square_length // 2
    
    # Create mask for diamond
    mask = (np.abs(x - center_x) * (height / 2) + np.abs(y - center_y) * (width / 2) <= (width * height) / 4)
    
    # Apply RGB color to diamond area
    image_array[mask] = rgb_color
    
    return image_array

class Diamond:
    '''Class representing a diamond shape with various properties and methods.'''
    def __init__(self, 
                    width: int, 
                    height: int, 
                    rgb_color: tuple, 
                    rgb_name: str,
                    upside_down: bool = False,
                    sideways: bool = False,
                    ) -> None:
        '''Initialize a Diamond instance.

        Args:
            width: The length of the horizontal diagonal in pixels.
            height: The length of the vertical diagonal in pixels.
            rgb_color: Tuple of (R, G, B) values (0-255).
            rgb_name: Name of the RGB color.
            upside_down: this does nothing
            sideways: this does nothing
        '''
        self.width = width
        self.height = height
        self.rgb_color = rgb_color
        self.rgb_name = rgb_name
        self.image = create_diamond_image(width, height, rgb_color)
    def __repr__(self) -> str:
        return f"Diamond(width={self.width}, height={self.height}, rgb_color={self.rgb_color})"
    def __str__(self) -> str:
        return f"Diamond of horizontal diagonal {self.width}, vertical diagonal {self.height} with color {self.rgb_name}"
    def get_image(self) -> npt.NDArray[np.uint8]:
        return self.image
    def get_width(self) -> int:
        """Get the size of the horizontal axis side"""
        return self.width
    def get_height(self) -> int:
        """Get the size of the vertical axis side"""
        return self.height
    def get_rgb_color(self) -> tuple:
        """Get the (R,G,B) tuple encoding of color"""
        return self.rgb_color
    def get_rgb_name(self) -> str:
        """Get the user-specified name of the color"""
        return self.rgb_name
    def get_area(self) -> float:
        """Calculate the area of the diamond."""
        return (self.width * self.height) / 2