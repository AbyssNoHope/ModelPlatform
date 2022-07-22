#!/bin/bash

apt update && apt install htop tmux -y

pip3 uninstall -y ml-essentials
pip3 uninstall -y tensorkit

pip3 install -r requirements.txt
pip3 install dgl-cu113 -f https://data.dgl.ai/wheels/repo.html
(
  pip3 uninstall -y ml-essentials ; pip3 install --upgrade git+https://gitee.com/haowen-xu/ml-essentials
  pip3 uninstall -y tensorkit ; pip3 install --upgrade git+https://gitee.com/haowen-xu/tensorkit
)
pip3 install torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 \
    -f https://download.pytorch.org/whl/cu113/torch_stable.html
#pip3 install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric \
#    -f https://data.pyg.org/whl/torch-1.10.0+cu113.html
