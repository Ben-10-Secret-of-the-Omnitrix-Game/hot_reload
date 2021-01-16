from demo_isometric_level.main import load
import logging
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from inspect import getmembers, isclass, isfunction, getmodule
from importlib import import_module, reload
from os.path import join, dirname

import pickle
import coloredlogs
import sys


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

storage_manager = object

class CustomMonitor(FileSystemEventHandler):
    def __init__(self, loader, manager):
        self.loader = loader
        self.manager = manager
    

    def on_modified(self, event):
        print("Event: ", event)
        self.loader.pass_event(event)
        # self.manager.try_load_objects(event.src_path)

    def on_moved(self, event):
        # TODO check instance
        print("Event: ", event)
        self.loader.pass_event(event)
        # self.manager.try_load_objects(event.src_path)


class StorageManager:

    def __init__(self):
        # objects -> {__class__: pickle.dumps(obj), ...}
        # self.objects = {}
        # files -> {absolute_path: [class1.__class__, class2.__class__], {"/home/usr/test/test1": ["__main__.Test1", "__main__.Test2"]}}
        self.files = {}

    def add_file(self, module_path):
        loaded_module = import_module(module_path)
        # if module_path not in self.files:
        #     self.files[module_path] = {}
        #     print("Cleaned add_file")
        return loaded_module
    
    def add_object(self, obj_instance):
        print("Fullname", self.fullname(obj_instance))
        obj_path = self.fullname(obj_instance)
        module_path = '.'.join(obj_path.split('.')[:-1])
        print("Fullname-modulepath", module_path)
        if module_path not in self.files:
            self.files[module_path] = {}
            print("Cleaned add_object")

        self.files[module_path][obj_path] = pickle.dumps(obj_instance)
        print("files", self.files)
        

    @staticmethod
    def fullname(o):
        # o.__module__ + "." + o.__class__.__qualname__ is an example in
        # this context of H.L. Mencken's "neat, plausible, and wrong."
        # Python makes no guarantees as to whether the __module__ special
        # attribute is defined, so we take a more circumspect approach.
        # Alas, the module name is explicitly excluded from __qualname__
        # in Python 3.

        module = o.__class__.__module__
        if module is None or module == str.__class__.__module__:
            return o.__class__.__name__  # Avoid reporting __builtin__
        else:
            return module + '.' + o.__class__.__name__

    # def add_object(self, obj_instance):
    #     # logging.debug("Obj instance __class__ is: ", fullname(obj_instance))
    #     print("add object", obj_instance.__class__)
    #     # self.files[obj_instance.__class__.__name__] = pickle.dumps(obj_instance)
    #     logging.info(f"Got object: {obj_instance} -> dumped")

    # def add_file(self, module_path):
        # loaded_module = import_module(module_path)
    #     # m_classes = getmembers(loaded_module, isclass)

    #     path = loaded_module.__file__
    #     self.files[path] = []
    #     logging.info(f"Loaded path: ")
    #     return loaded_module
    
    def _load_object(self, obj):
        logging.info(f"Trying load object!")

        return pickle.loads(obj)

    def try_load_objects(self, file_path):
        offset = file_path.find("hot_reload")
        module_path = file_path[offset::].replace('.py', '').replace('/', '.').replace('\\', '.')
        print("Module path", module_path)
        if module_path not in self.files:
            print("Didn't find module")
            return
        print(self.files)
        for obj_path, dump in self.files[module_path].items():
            print(self._load_object(dump))
    

def saver(attr):
    print("[Attribute]", attr)
    print("[All functions]", getmembers(attr, isfunction))
    def wrapper(*args, **kwargs):
        loader = Loader()
        loader.storage_manager.add_object(args[0])
        print("[Arguments]", args, kwargs)
        print("Executing")
        ret = attr(*args, **kwargs)
        print("Complete; Result:]", ret)
        return ret
    return wrapper

def member_saver(attr):
    print("member_saver ...; attr is: ", attr)
    def wrapper(*args, **kwargs):
        loader = Loader()
        loader.storage_manager.add_object(args[0])

        print("Trying set value: ", args, kwargs)
        args[0].__dict__[args[1]] = args[2]
        return
    return wrapper

def object_saver(cls):
    print("cls.__dict__", cls.__dict__)
    for attr in cls.__dict__:
        if callable(getattr(cls, attr)):
            print(f"[Hooking] {attr}")
            setattr(cls, attr, saver(getattr(cls, attr)))

    # setattr(cls, '__set_name__', member_saver("__set_name__"))
    # setattr(cls, '__set__', member_saver("__set__"))
    setattr(cls, '__setattr__', member_saver("__setattr__"))
    return cls    


class Loader(metaclass=SingletonMeta):
    def __init__(self):
        logger = logging.getLogger(__name__)
        coloredlogs.install(level='DEBUG', logger=logger)

        self.storage_manager = StorageManager()
        self.monitor = CustomMonitor(self, self.storage_manager)
        self.changed = False
        observer = Observer()
        observer.schedule(self.monitor, "./demo_isometric_level/", recursive=True)
        observer.start()

        self.module = import_module("demo_isometric_level.main")

    def pass_event(self, event):
        print(event.src_path.split('/')[-1].split('.'))
        if len(event.src_path.split('/')[-1].split('.')) >= 2 and event.src_path.split('/')[-1].split('.')[-1] == 'py':
            self.changed = True
        # offset = event.dst_path.find("hot_reload")
        # module_path = event.dst_path[offset::].replace('.py', '').replace('/', '.').replace('\\', '.')
        # event.src_path
    
    def is_changed(self):
        if self.changed:
            self.changed = False
            self.module = reload(self.module)
            return True
        return False


# def main():
#     global storage_manager

#     storage_manager = StorageManager()

#     # logging.basicConfig(level=logging.INFO,
#     #                     format='%(asctime)s - %(message)s',
#     #                     datefmt='%Y-%m-%d %H:%M:%S')
    # logger = logging.getLogger(__name__)
    # coloredlogs.install(level='DEBUG', logger=logger)
#     monitor = CustomMonitor(storage_manager)

#     observer = Observer()
#     observer.schedule(monitor, "./", recursive=True)
#     observer.start()
#     try:
#         while True:
#             time.sleep(0.1)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()
#     return


if __name__ == '__main__':
    loader = Loader()
    
    # self.manager.add_file("hot_reload.example.demo1.level")
    # test1_module = loader.storage_manager.add_file("hot_reload.example.test1")

    # p = test1_module.Player()
    # p.hello()

    # while True:
    #     if loader.is_changed():
    #         print("Changed!!!")

    
    
