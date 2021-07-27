# Purpose: Use channel attention layers with skip connections

# PyTorch lib
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from .DepthConv import CSDN_Tem


# Channel Residual Attention Layer
class CRALayer(nn.Module):
    def __init__(self, channel, reduction): # channel = 32, reduction = 16
        super(CRALayer, self).__init__()
        # Global Average Pooling
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        # Feature Channel Rescale
        self.conv_du = nn.Sequential(
            nn.Conv2d(channel, channel // reduction, 1, padding=0, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(channel // reduction, channel, 1, padding=0, bias=False),
        )
        # 1 X 1 Convolution inside Skip Connection
        self.conv_1_1 = nn.Conv2d(channel, channel, 1, padding=0, bias=False)
        # Sigmoid Activation
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        y = self.avg_pool(x)
        res = self.conv_1_1(y)
        y = self.conv_du(y)
        y += res
        y = self.sigmoid(y)
        return x * y



class SAPNet(nn.Module):
    def __init__(self, recurrent_iter=6, use_GPU=True):
        super(SAPNet, self).__init__()
        self.iteration = recurrent_iter
        self.use_GPU = use_GPU

        self.conv0 = nn.Sequential(
            #nn.Conv2d(6, 32, 3, 1, 1),
            CSDN_Tem(6, 32),
            nn.ReLU()
        )

        # Residual Attention block
        self.res_conv1 = nn.Sequential(
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU(),
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU()
        )

        self.res_conv2 = nn.Sequential(
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU(),
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU()
        )
        self.res_conv3 = nn.Sequential(
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU(),
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU()
        )
        self.res_conv4 = nn.Sequential(
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU(),
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU()
        )
        self.res_conv5 = nn.Sequential(
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU(),
            #nn.Conv2d(32, 32, 3, 1, 1),
            CSDN_Tem(32, 32),
            CRALayer(channel=32, reduction=16),
            nn.ReLU()
        )
        self.conv_i = nn.Sequential(
            #nn.Conv2d(32 + 32, 32, 3, 1, 1),
            CSDN_Tem(32 + 32, 32),
            nn.Sigmoid()
        )
        self.conv_f = nn.Sequential(
            #nn.Conv2d(32 + 32, 32, 3, 1, 1),
            CSDN_Tem(32 + 32, 32),
            nn.Sigmoid()
        )
        self.conv_g = nn.Sequential(
            #nn.Conv2d(32 + 32, 32, 3, 1, 1),
            CSDN_Tem(32 + 32, 32),
            nn.Tanh()
        )
        self.conv_o = nn.Sequential(
            #nn.Conv2d(32 + 32, 32, 3, 1, 1),
            CSDN_Tem(32 + 32, 32),
            nn.Sigmoid()
        )
        self.conv = nn.Sequential(
            #nn.Conv2d(32, 3, 3, 1, 1),
            CSDN_Tem(32, 3),
        )

    def forward(self, input):
        batch_size, row, col = input.size(0), input.size(2), input.size(3)

        x = input
        h = Variable(torch.zeros(batch_size, 32, row, col))
        c = Variable(torch.zeros(batch_size, 32, row, col))

        if self.use_GPU:
            h = h.cuda()
            c = c.cuda()

        x_list = []
        for i in range(self.iteration):
            x = torch.cat((input, x), 1)
            x = self.conv0(x)

            x = torch.cat((x, h), 1)
            i = self.conv_i(x)
            f = self.conv_f(x)
            g = self.conv_g(x)
            o = self.conv_o(x)
            c = f * c + i * g
            h = o * torch.tanh(c)

            x = h
            resx = x
            x = F.relu(self.res_conv1(x) + resx)
            resx = x
            x = F.relu(self.res_conv2(x) + resx)
            resx = x
            x = F.relu(self.res_conv3(x) + resx)
            resx = x
            x = F.relu(self.res_conv4(x) + resx)
            resx = x
            x = F.relu(self.res_conv5(x) + resx)
            x = self.conv(x)

            x = x + input
            x_list.append(x)

        return x, x_list



