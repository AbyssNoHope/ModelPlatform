#!/bin/bash

apt update && apt install htop -y

pip3 install -r requirements.txt
pip3 install dgl -f https://data.dgl.ai/wheels/repo.html
pip3 uninstall -y ml-essentials ; pip3 install --upgrade git+https://gitee.com/haowen-xu/ml-essentials
pip3 uninstall -y tensorkit ; pip3 install --upgrade git+https://gitee.com/haowen-xu/tensorkit
pip3 install torch==1.10.0 torchvision==0.11.1 torchaudio==0.10.0 \
    -f https://download.pytorch.org/whl/cpu/torch_stable.html
#pip3 install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric \
#    -f https://data.pyg.org/whl/torch-1.10.0.html
