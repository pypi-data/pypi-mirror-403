"""Utilities for distributed applications"""
import os
from typing import Optional

def get_distributed_rank() -> Optional[int]:
    """ Get the rank of the current process in pytorch distributed setting.
    Returns:
        int: The rank of the current process. If not in a distributed setting, returns None.
    """
    rank = None
    if 'RANK' in os.environ:
        try:
            rank = int(os.environ['RANK'])
        except ValueError:  # not an integer
            pass
    
    return rank
