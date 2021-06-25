import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import Parameter
import math


class ArcNet(nn.Module):
    r"""Implement of large margin arc distance: :
        Args:
            in_features: size of each input sample
            num_classes: size of each output sample
            s: norm of input feature
            m: margin

            cos(theta + m)
        """
    def __init__(self, feature_dim, class_dim, s=64.0, m=0.50):
        super(ArcNet, self).__init__()
        self.s = s
        self.m = m
        self.weight = Parameter(torch.FloatTensor(feature_dim, class_dim))
        nn.init.xavier_uniform_(self.weight)
        self.class_dim = class_dim
        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)
        self.threshold = math.cos(math.pi - m)
        self.mm = self.sin_m * m

    def forward(self, feature, label):
        cos_theta = torch.mm(F.normalize(feature), F.normalize(self.weight, dim=0))
        sin_theta = torch.sqrt(torch.clip(1.0 - torch.pow(cos_theta, 2), min=0, max=1))
        cos_theta_m = cos_theta * self.cos_m - sin_theta * self.sin_m
        cos_theta_m = torch.where(cos_theta > self.threshold, cos_theta_m, cos_theta - self.mm)
        one_hot = torch.nn.functional.one_hot(label, self.class_dim)
        output = (one_hot * cos_theta_m) + (torch.abs((1.0 - one_hot)) * cos_theta)
        output *= self.s
        # 简单的分类方法，学习率需要设置为0.1
        # cosine = self.cosine_sim(feature, self.weight)
        # one_hot = torch.nn.functional.one_hot(label, self.class_dim)
        # output = self.s * (cosine - one_hot * self.m)
        return output

    @staticmethod
    def cosine_sim(feature, weight, eps=1e-8):
        ip = torch.mm(feature, weight)
        w1 = torch.norm(feature, 2, dim=1)
        w2 = torch.norm(weight, 2, dim=0)
        return ip / torch.outer(w1, w2).clip(min=eps, max=1e3)
