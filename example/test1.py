# from hot_reload.__main__ import object_saver

# @object_saver
class Player:
    def __init__(self):
        self.x = 1000000
        self.spawned = False
    
    def hello(self):
        print("sdfssdf")
    

    def spawn(self):
        self.spawned = True
        print("Spawned")


