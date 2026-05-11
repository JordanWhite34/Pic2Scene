# Pic2Scene
The desire of this project is to eventually get to the point where I can feed in any 2d image and I will get back a 3d stl file that I can use for my 3d printer.

4/30/2026

- I want to use images with multiple angles to create the 3d model. If I can get this working well I may look to generative AI methods to fill gaps / improve these models.
- I think I have noise removal working alongside using colmap to turn images to a point cloud. Next I want to go through the textbook more and implement (3D Data Preparation):
  - Subsampling (helps with computation amount while preserving important details)
  - feature extraction (normals, local features, global features - this is helpful for turning raw data into meaningful descriptors AI models can use!!)
- Then I will want to do 3D Data Modeling:
  - 3D Mesh Reconstruction (converting point cloud to mesh)
  - Voxelization of 3D Digital Environments (helpful for tasks that need volumetric representation)
  - k-d Trees (help computation for nearest neighbor search, normal estimation, feature computation, and local neighborhood analysis. Might want to see where in the workflow is best to implement this.)
  - Octrees (another data structure for 3D datasets, great for level-of-detail rendering and hierarchical spatial queries - need to look up what that means lol)
- And then Semantic Extraction:
  - Clustering, Unsupervised Segmentation
  - Semantic Segmentation
  - 3D Object Classification
- And lastly, 3D Data Visualization and Analysis:
  - 3D Shape Recognition
  - 3D Data Analytical Tools
  - 3D Multimodal Python Viewer

All this stuff is accessible between pages 587 - 610 in the textbook, **aka chapter 17**


5/5/2026
I added everything up to converting point cloud to mesh. I had some quality issues when taking images with my iPhone but they were mitigated by manually setting "--ImageReader.single_camera", "1" (this tells COLMAP there is only 1 camera so all intrinsics were saved and it didnt try to recompute camera settings for each image). Next I will work on Data Modeling.

5/7/2026
I have decided the next thing I want to work on is to look into how to get rid of more noise