"""
The “Hur-MultiModal” is a multimodal architecture for large language models (LLMs/LMMs) that can be trained on modest hardware without GPU need.
When a GPU is connected to the “Hur-MultiModal” architecture, it will significantly boost the network's performance,
but this is not mandatory since the architecture itself was built with specific functions for training and tuning directly on the CPU.
The architecture also features support for infinite context window, which makes it possible to maintain conversations without any token limit.
The network's performance increase occurs thanks to the possibility of training the model without using backpropagation.
Since the architecture has training resources for direct calculations in a single step with semantic comparison and weights adjustment by division with HurNet networks,
this makes it significantly lighter and faster than traditional multimodal network architectures.
This is 100% original code developed by Sapiens Technology® to add multimodality support to neural networks of the HurModel architecture.
Any modification, sharing, or public comment on the technical specifications of this architecture is strictly prohibited,
and the author will be subject to legal action initiated by our legal team.
"""
# --------------------------> A SAPIENS TECHNOLOGY®️ PRODUCTION) <--------------------------
from .hur_multimodal import *
"""
The “Hur-MultiModal” is a multimodal architecture for large language models (LLMs/LMMs) that can be trained on modest hardware without GPU need.
When a GPU is connected to the “Hur-MultiModal” architecture, it will significantly boost the network's performance,
but this is not mandatory since the architecture itself was built with specific functions for training and tuning directly on the CPU.
The architecture also features support for infinite context window, which makes it possible to maintain conversations without any token limit.
The network's performance increase occurs thanks to the possibility of training the model without using backpropagation.
Since the architecture has training resources for direct calculations in a single step with semantic comparison and weights adjustment by division with HurNet networks,
this makes it significantly lighter and faster than traditional multimodal network architectures.
This is 100% original code developed by Sapiens Technology® to add multimodality support to neural networks of the HurModel architecture.
Any modification, sharing, or public comment on the technical specifications of this architecture is strictly prohibited,
and the author will be subject to legal action initiated by our legal team.
"""
# --------------------------> A SAPIENS TECHNOLOGY®️ PRODUCTION) <--------------------------
