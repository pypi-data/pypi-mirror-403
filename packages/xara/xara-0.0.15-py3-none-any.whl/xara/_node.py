

class Node:
    def __init__(self, model, tag):
        self._model = model
        self._tag = tag

    @property 
    def location(self):
        """Get the location of the node."""
        return self._model.nodeCoord(self._tag)
    
    