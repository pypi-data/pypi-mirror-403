import numpy as np
import numpy.typing as npt

def create_triangle_image(width: int, 
                            height: int, 
                            rgb_color: tuple,
                            upside_down: bool = False,
                            sideways: bool = False, 
                            ) -> npt.NDArray[np.uint8]:
    """
    Create a triangle with RGB color in a square pixel image.
    
    Args:
        width: The width of the triangle base in pixels.
        height: The height of the triangle in pixels.
        midpoint: The x-coordinate of the midpoint of the base (0 to 1).
        upside_down: Whether the triangle is upside down.
        sideways: Whether the triangle is sideways.
        rgb_color: Tuple of (R, G, B) values (0-255)

    Returns:
        (max(width, height), max(width, height), 3) numpy array representing 
        the image with a colored triangle on black background.
    """
    # Create black background
    square_width = max(width, height)  
    image_array = np.random.randint(0, 256, (square_width, square_width, 3), dtype=np.uint8)
    
    # Create coordinate grids
    midpoint = 0.5
    y, x = np.ogrid[:square_width, :square_width]
    center_x = int(square_width * midpoint)
    
    # Create mask for triangle
    mask = (x >= center_x - width // 2) & (x <= center_x + width // 2) & (y <= height) & (y >= (height / (width / 2)) * np.abs(x - center_x))
    if upside_down:
        mask = (x >= center_x - width // 2) & (x <= center_x + width // 2) & (y >= 0) & (y <= height - (height / (width / 2)) * np.abs(x - center_x))
    if sideways:
        mask = (y >= center_x - width // 2) & (y <= center_x + width // 2) & (x <= height) & (x >= (height / (width / 2)) * np.abs(y - center_x))
        if upside_down:
            mask = (y >= center_x - width // 2) & (y <= center_x + width // 2) & (x >= 0) & (x <= height - (height / (width / 2)) * np.abs(y - center_x))
    
    # Apply RGB color to triangle area
    image_array[mask] = rgb_color
    
    return image_array

class Triangle:
    '''Class representing an equilateral triangle shape with various properties and methods.'''
    def __init__(self, 
                    width: int, 
                    height: int, 
                    rgb_color: tuple, 
                    rgb_name: str,
                    upside_down: bool = False,
                    sideways: bool = False, 
                    ) -> None:
        '''Initialize a Triangle instance.
        
        Args:
            width: The width of the triangle base in pixels.
            height: The height of the triangle in pixels.
            midpoint: The x-coordinate of the midpoint of the base (0 to 1).
            rgb_color: Tuple of (R, G, B) values (0-255).
            rgb_name: Name of the RGB color.
            upside_down: Whether the triangle is upside down.
            sideways: Whether the triangle is sideways.
        '''
        self.width = width
        self.height = height
        self.rgb_color = rgb_color
        self.rgb_name = rgb_name
        self.image = create_triangle_image(width, height, rgb_color, upside_down, sideways)
    def __repr__(self) -> str:
        return f"Triangle(width={self.width}, height={self.height}, rgb_color={self.rgb_color})"
    def __str__(self) -> str:
        return f"Equilaterial triangle of width {self.width}, height {self.height} with color {self.rgb_name}"
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
    def get_area(self) -> float:
        """Calculate the area of the triangle."""
        return 0.5 * self.width * self.height