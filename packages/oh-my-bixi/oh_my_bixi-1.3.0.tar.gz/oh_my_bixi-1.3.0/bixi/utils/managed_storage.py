import logging

import resource
import pickle
from collections import UserDict
import torch
import numpy as np
from torch.multiprocessing import Manager
from multiprocessing.managers import SyncManager


class ProcessResourceSetting:
    """This class is used to get/set the maximum number of file descriptors for the process.
    It can be registered in a multiprocessing.Manager so that the manager process' ulimit
    can be changed"""

    @staticmethod
    def get_max_ulimit() -> int:
        """
        Get the maximum number of file descriptors for the process.
        This is useful to avoid hitting the limit when using shared memory.

        Returns:
            The maximum number of file descriptors that can be opened by the current process.
        """
        soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        return soft_limit

    @staticmethod
    def set_max_ulimit(max_file_descriptors: int):
        """
        Set the maximum number of file descriptors for the process.
        This is useful to avoid hitting the limit when using shared memory.
        Args:
            max_file_descriptors: the maximum number of file descriptors to set.

        Notes:
            Normally speaking, a containerd system environment has limited ulimit number (e.g. 1024 or 2048).
            If you are using a lot of shared memory item, you may need to increase this limit.
        """
        _, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (max_file_descriptors, hard_limit))


class ManagedSerializedDict(UserDict):
    """
    This class manages store elements in an inter-process shared dictionary with a serialized bytes
     format (unit8) using torch.Tensor. This class is designed to be used in a multiprocessing
     context where shared memory is required. Its concurrent-safety is guaranteed by a write lock.
    """

    CRITICAL_RATIO = 0.8
    """This is the ratio of the maximum number of file descriptors that can be opened by the process.
    If the current number of file descriptors is greater than this ratio, the class will raise an warning
    and trying to increase the maximum number of file descriptors to avoid hitting the limit.
    """

    def __init__(self, *args, manager: Manager = None, **kwargs):
        """
        Args:
            manager: the manager to use for shared memory. If None, a new Manager will be created.
                Note that for a given manager, the maximum number of file descriptors should be
                managed carefully, so that the number of stored items won't exceed the manager
                process' limit.
        """
        super().__init__()
        if manager is None:
            # Note: Registering ProcessResourceSetting is mandatory to change the ulimit settings
            # in the manager sever process. Regarding the registring method, it is generally recommended
            # to register on a subclass of SyncManager. But we did not find a way to register the functions
            # on the torch's Manager directly, so we use the SyncManager, which is its base class
            if not hasattr(SyncManager, ProcessResourceSetting.__name__):
                SyncManager.register(ProcessResourceSetting.__name__, ProcessResourceSetting)

            manager = Manager()
            manager_resource_setting = manager.ProcessResourceSetting()

        else:
            manager_resource_setting = None

        # Use the manager to create a shared dictionary. Note that the manager object itself is not picklable, so
        # we don't store it in the UserDict.
        self.data = manager.dict()
        self._lock = manager.Lock()
        self._manager_resource_setting = manager_resource_setting  # Proxied ProcessResourceSetting object

    def __setitem__(self, key, item):
        item_tensor = torch.tensor(np.frombuffer(pickle.dumps(item), dtype=np.uint8))

        with self._lock:
            if self._manager_resource_setting is not None:
                # Check the current number of file descriptors and increase the limit if necessary
                # to avoid hitting the limit when adding new items.
                current_size = len(self.data)
                current_limit = self._manager_resource_setting.get_max_ulimit()
                if current_size >= (current_limit * self.CRITICAL_RATIO):
                    logging.warning(f"The current number of file descriptors ({current_size}) is approaching the limit "
                                    f"({current_limit}). Trying to double the limit to avoid hitting it.")
                    self._manager_resource_setting.set_max_ulimit(current_limit * 2)
                    new_limit = self._manager_resource_setting.get_max_ulimit()
                    if new_limit <= current_limit:
                        logging.error("Failed to increase the maximum number of file descriptors. "
                                      "Please check your system settings.")
                    else:
                        logging.info(f"The maximum number of file descriptors has been increased to {new_limit}.")

            return super().__setitem__(key, item_tensor)

    def __getitem__(self, key):
        item_tensor = super().__getitem__(key)
        item = pickle.loads(item_tensor.numpy().tobytes())
        return item
