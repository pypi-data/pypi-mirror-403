from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal


class JSBridge(QObject):

    sceneChanged = pyqtSignal(str)

    def __init__(self, scene_manager):
        super().__init__()
        self.scene_manager = scene_manager

    @pyqtSlot(str)
    def loadScene(self, name):
        print("🎮 JS Requested Scene:", name)

        self.scene_manager.load_scene(name)
        self.sceneChanged.emit(name)
