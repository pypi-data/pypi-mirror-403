import torch
import torch.nn as nn
from torch.nn.utils.parametrizations import weight_norm

from spikingjelly.activation_based import neuron, functional, surrogate, layer

class TemporalBlock(nn.Module):
    def __init__(
        self,
        C_in,
        C_out,
        kernel_size,
        stride,
        dilation,
        padding,
        dropout
    ):
        super().__init__()

        self.conv1 = weight_norm(
            layer.Conv1d(
                C_in,
                C_out,
                kernel_size,
                stride=stride,
                padding=padding,
                dilation=dilation
            )
        )
        self.relu1 = nn.ReLU() # todo
        self.dropout1 = layer.Dropout(dropout)

        self.conv2 = weight_norm(
            layer.Conv1d(
                C_out,
                C_out,
                kernel_size,
                stride=stride,
                padding=padding,
                dilation=dilation
            )
        )
        self.relu2 = nn.ReLU() # todo
        self.dropout2 = layer.Dropout(dropout)

        self.padding = padding  # 用于裁剪
        self.downsample = (
            layer.Conv1d(C_in, C_out, kernel_size=1)
            if C_in != C_out else None
        )
        self.relu = nn.ReLU() # todo

    def _chomp1d(self, x):
        """
        裁剪多余的 padding
        x: Tensor, shape [T, batch, channels, seq_len]
        """
        if self.padding == 0:
            return x
        return x[:, :, :, :-self.padding].contiguous()

    def forward(self, x):
        out = self.conv1(x)
        out = self._chomp1d(out)
        out = self.relu1(out)
        out = self.dropout1(out)

        out = self.conv2(out)
        out = self._chomp1d(out)
        out = self.relu2(out)
        out = self.dropout2(out)

        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)



class TemporalConvNet(nn.Module):
    ''' TemporalConvNet '''
    def __init__(self, C_in, num_channels, kernel_size=2, dropout=0.2):
        super().__init__()

        layers = []
        for i in range(len(num_channels)):
            dilation_size = 2 ** i
            in_channels = C_in if i == 0 else num_channels[i - 1]
            out_channels = num_channels[i]
            padding = (kernel_size - 1) * dilation_size

            layers.append(
                TemporalBlock(
                    in_channels,
                    out_channels,
                    kernel_size,
                    stride=1,
                    dilation=dilation_size,
                    padding=padding,
                    dropout=dropout
                )
            )

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class TCN(nn.Module):
    """TCN + 分类头"""
    def __init__(self, T, input_shape, num_channels, num_classes, kernel_size=2, dropout=0.2):
        super().__init__()
        # 使用你已有的 TemporalConvNet
        self.tcn = TemporalConvNet(
            C_in=input_shape[0],
            num_channels=num_channels,
            kernel_size=kernel_size,
            dropout=dropout
        )
        self.num_channels = num_channels[-1]  # TCN 最后一层输出通道数
        # 分类头
        self.fc = layer.Linear(self.num_channels, num_classes)

        functional.set_step_mode(self, step_mode='m')

    def forward(self, x):
        """
        x: [batch, in_channels, seq_len]
        """
        x = self.tcn(x)        # [T, batch, channels, seq_len]
        x = x[:, :, :, -1]        # 取序列最后一个时间步作为特征
        x = self.fc(x)         # [T, batch, num_classes]
        x = x.mean(0)
        return x


if __name__ == "__main__":
    batch_size = 8
    in_channels = 4
    seq_len = 100
    num_classes = 10
    T = 4

    x = torch.randn(T, batch_size, in_channels, seq_len)
    print("Input shape:", x.shape)

    tcn_model = TCN(
        T=T,
        input_shape=(in_channels, seq_len),
        num_channels=[16, 32, 64],
        num_classes=num_classes,
        kernel_size=3,
        dropout=0.2
    )

    y = tcn_model(x)
    print("Output shape:", y.shape)
