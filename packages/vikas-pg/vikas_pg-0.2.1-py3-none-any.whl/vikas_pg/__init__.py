#Public API surface 
#Infering api directly from here 


#Pool connection 
# max_queries = 10 -> pool opens new connection 
# ONE event loop
#   ├── create pool ONCE
#   ├── run many queries
#   └── close pool ONCE


from .Engine import Accelerate
import sys

__all__ = ["Accelerate"]



if sys.version_info >= (3, 14):
    raise RuntimeError(
        "vikas_pg does not support Python 3.14+ yet. "
        "Please use Python 3.8–3.13."
    )


classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Database",
    ]