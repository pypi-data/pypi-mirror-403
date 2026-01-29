import torch
import torch.nn as nn
from huggingface_hub import PyTorchModelHubMixin # Import mixin for Hugging Face Hub compatibility

class MyRNN(nn.Module, PyTorchModelHubMixin):
    '''Recurrent neural network to predict the next point in a sine wave'''

    def __init__(self, 
                    input_size, 
                    output_size, 
                    hidden_dim, 
                    class_=nn.RNN, 
                    num_layers=1,
                    dropout=0.2,
                    ):
        """Initialize the model

        Parameters
        ----------
        input_size : int
            Size of the input features.
        output_size : int
            Size of the output features.
        hidden_dim : int
            Size of the hidden state.
        num_layers : int
            Number of recurrent layers (default is 1).
        dropout : float
            Dropout probability for generalizability (default is 0.2)
        """
        super(MyRNN, self).__init__()

        self.num_layers = num_layers
        self.hidden_dim = hidden_dim

        # Define the RNN layer
        # class_ could be nn.RNN or nn.LSTM
        # may need to add cell state for LSTM version
        self.rnn = class_(input_size, hidden_dim, num_layers, dropout=dropout, batch_first=True)

        # Define the output layer
        self.fc = nn.Linear(hidden_dim, output_size)

    def forward(self, x, hidden):
        # Pass through RNN layer
        out, hidden = self.rnn(x, hidden)

        # Pass the output of the last time step to the fully connected layer
        out = self.fc(out[:, -1, :])
        return out, hidden

    def init_hidden(self, batch_size):
        # Initialize hidden state with zeros
        return torch.zeros(self.num_layers, batch_size, self.hidden_dim)