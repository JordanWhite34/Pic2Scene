import numpy as np

class OctreeNode:
    def __init__(self, center, size, points):
        self.center = center
        self.size = size
        self.points = points
        self.children = []

    def subdivide(self):
        if len(self.points) <= 100: # arbitrary threshold
            return
        
        new_size = self.size / 2
        for i in range(8):
            new_center = self.center + new_size * np.array([
                (i & 1) - 0.5,
                ((i >> 1) & 1) - 0.5,
                ((i >> 2) & 1) - 0.5
            ])
            mask = np.all(np.abs(self.points - new_center) <= new_size, axis=1)
            self.children.append(OctreeNode(new_center, new_size, self.points[mask]))
    
    def build_octree(points):
        center = np.mean(points, axis=0)
        size = np.max(np.abs(points - center)) * 2
        root = OctreeNode(center, size, points)
        root.subdivide()
        return root