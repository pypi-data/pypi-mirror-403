import numpy as np
import numpy.typing as npt

def create_sinusoid(amplitude: float, 
                    frequency: float, 
                    phase: float, 
                    vertical_shift: float, 
                    length: int) -> npt.NDArray[np.uint8]:
    """
    Create a sine wave.
    
    Args:
        amplitude: The amplitude of the sine wave.
        frequency: The frequency of the sine wave.
        phase: The phase shift of the sine wave in radians.
        vertical_shift: The vertical shift of the sine wave.
        length: The length of the sine wave.

    Returns:
        1-dimensional numpy array representing a sine wave.
    """
    
    # Create x values
    x = np.linspace(0, 2 * np.pi * frequency, length)
    
    # Calculate y values for sine wave
    y = (amplitude * np.sin(x + phase)) + vertical_shift
    
    return y