import torch
import torch.nn as nn
from math import floor
from huggingface_hub import PyTorchModelHubMixin # Import mixin for Hugging Face Hub compatibility

def calculate_after_conv(height, kernel_size, stride, padding,):
    return floor((height + 2 * padding - kernel_size) / stride) + 1

class MyCNN(nn.Module, PyTorchModelHubMixin):
    '''Custom CNN to classify the shape or color of an object in an image'''

    def __init__(self,
                    num_classes: int = 2,
                    height: int = 224,
                    width: int = 224,
                    num_input_channels = 3,
                    num_cnn_channels = 32,
                    num_cnn_layers = 0,
                    hidden_dim: int = 16,
                    num_layers: int = 0,
                    kernel_size: int = 3,
                    stride: int = 1,
                    padding: int = 1,
                    pooling: int = 2,
                    dropout: float = 0.2,
                ):
        '''Initialize the model

        Parameters
        ----------
        num_classes : int
            Number of prediction classes,
            which is the output dimension
        width : int
            Dimensions of image
        height : int
            Dimensions of image
        num_input_channels : int
            Number of channels in input (3 for RGB color)
        num_cnn_channels : int
            Number of channels for all Conv2d() layers
        num_cnn_layers : int
            Number of Conv2d() layers on on top of
            an initial layer and an average pooling final layer
        hidden_dim : int
            Number of hidden units in Linear() layer
        num_layers : int
            Number of Linear() layers on top of an
            initial layer and a final layer
        kernel_size : int
        stride : int
        padding : int
        pooling : int
        dropout : float
            The probability of dropout 
        '''

        super(MyCNN, self).__init__()

        linear_activation = nn.ReLU

        self.config = {
            "num_classes": num_classes,
            "height": height,
            "width": width,
            "num_input_channels": num_input_channels,
            "num_cnn_channels": num_cnn_channels,
            "num_cnn_layers": num_cnn_layers,
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "kernel_size": kernel_size,
            "stride": stride,
            "padding": padding,
            "pooling": pooling,
            "dropout": dropout
        }

        # convolutional layers

        cnn_layers = []

        cnn_layers.append(
            nn.Conv2d(
                num_input_channels,
                num_cnn_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                )
        )
        cnn_layers.append(nn.BatchNorm2d(num_cnn_channels))
        cnn_layers.append(
            nn.MaxPool2d(pooling,)
        )

        for _ in range(num_cnn_layers):
            cnn_layers.append(
            nn.Conv2d(
                num_cnn_channels,
                num_cnn_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                )
            )
            cnn_layers.append(nn.BatchNorm2d(num_cnn_channels))
            cnn_layers.append(
                nn.MaxPool2d(pooling,)
            )

        cnn_layers.append(
            nn.Conv2d(
                num_cnn_channels,
                num_cnn_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                )
        )
        cnn_layers.append(nn.BatchNorm2d(num_cnn_channels))
        cnn_layers.append(
            nn.AvgPool2d(pooling,)
        )

        self.conv_block = nn.Sequential(*cnn_layers)

        # update the dimension
        height = calculate_after_conv(height, kernel_size, stride, padding)
        height = calculate_after_conv(height, pooling, pooling, 0)
        width = calculate_after_conv(width, kernel_size, stride, padding)
        width = calculate_after_conv(width, pooling, pooling, 0)
        for _ in range(num_cnn_layers):
            height = calculate_after_conv(height, kernel_size, stride, padding)
            height = calculate_after_conv(height, pooling, pooling, 0)
            width = calculate_after_conv(width, kernel_size, stride, padding)
            width = calculate_after_conv(width, pooling, pooling, 0)
        height = calculate_after_conv(height, kernel_size, stride, padding)
        height = calculate_after_conv(height, pooling, pooling, 0)
        width = calculate_after_conv(width, kernel_size, stride, padding)
        width = calculate_after_conv(width, pooling, pooling, 0)

        # linear layers
        linear_layers = []

        linear_layers.append(
            nn.Linear(
                width * height * num_cnn_channels,
                hidden_dim,
            )
        )
        linear_layers.append(nn.BatchNorm1d(hidden_dim))
        linear_layers.append(linear_activation())
        linear_layers.append(nn.Dropout(dropout))

        for _ in range(num_layers):
            linear_layers.append(
                nn.Linear(hidden_dim, hidden_dim)
            )        
            linear_layers.append(nn.BatchNorm1d(hidden_dim))
            linear_layers.append(linear_activation())
            linear_layers.append(nn.Dropout(dropout))

        self.linear_block = nn.Sequential(*linear_layers)

        # final layer
        self.output_block = nn.Linear(hidden_dim,
            num_classes,
        )

    def forward(self, x):
        '''Where we specify the order of neural network layers

        Parameters
        ----------
        x : torch.Tensor
            Tensor of shape (batch_size, num_input_channels, height, width)
        
        Returns
        -------
        torch.Tensor
            Output is (batch_size, num_classes)
        '''

        # cnn layers
        x = self.conv_block(x)
        
        # flatten
        x = x.view(x.size(0), -1)

        # linear layers
        x = self.linear_block(x)

        # linear layer to output
        x = self.output_block(x)

        return x