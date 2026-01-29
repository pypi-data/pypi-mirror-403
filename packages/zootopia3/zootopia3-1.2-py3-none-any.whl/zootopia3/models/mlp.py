import torch
import torch.nn as nn
from huggingface_hub import PyTorchModelHubMixin # Import mixin for Hugging Face Hub compatibility

# build a model class
# https://docs.pytorch.org/docs/stable/nn.html

class MyMLP(nn.Module, PyTorchModelHubMixin):
    '''Multilayer perceptron to predict the next point in a sine wave'''

    def __init__(self, 
                input_dim, 
                output_dim, 
                num_layers, 
                hidden_dim, 
                dropout=0.2):
        '''
        Parameters
        ----------
        num_layers : int
            The depth of the neural network
        hidden_dim : int
            The height of the neural network
        dropout : int
            The dropout probability
        '''

        # must have this
        # inherits the internal attributes 
        # and methods of nn.Module
        # which is a lot of machinery
        # that we do not want to write
        # from scratch
        super(MyMLP, self).__init__()
        layers = []

        # What are the dimensions of the nn.Linear()
        layers.append(nn.Linear(input_dim, hidden_dim))
        layers.append(nn.BatchNorm1d(hidden_dim)) # play around without this
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(dropout))

        for _ in range(num_layers):
            # Extended the layers list to have repeating blocks
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim)) # play around without this
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))

        # What are the 
        layers.append(nn.Linear(hidden_dim, output_dim))
        
        self.block = nn.Sequential(*layers)
        
    # Usually, this method defines the computation graph
    # Telling us how to backpropagate the gradients
    # The nn.Sequential() class above already handles this
    def forward(self, x):
        return self.block(x)