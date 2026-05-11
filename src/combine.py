import subprocess
import shutil
import open3d as o3d
import numpy as np
from pathlib import Path
from sklearn.neighbors import KDTree

class run_colmap:
    def __init__(self, image_dir: str, output_dir: str, COLMAP=r"C:\Tools\COLMAP\COLMAP.bat"):
        """
        class used to run colmap on an image directory easily. make sure COLMAP is set to the location of your COLMAP download.
        If COLMAP is on your PATH, you can replace all instances of self.COLMAP with "colmap". This implementation assumes COLMAP is NOT on PATH.
        """

        self.COLMAP = COLMAP
        self.image_dir = Path(image_dir)
        self.output_dir = Path(output_dir)

        self.sparse_dir = self.output_dir / "sparse"
        self.dense_dir = self.output_dir / "dense"

        self.pcd = o3d.geometry.PointCloud()
        fused_path = self.dense_dir / "fused.ply"
        if fused_path.exists():
            self.pcd = o3d.io.read_point_cloud(str(fused_path))

    
    def run(self, clean_output=True):
        """
        Method for the whole pipeline. Overwrites old outputs if any exist.
        """

        # deleting remnants of any previous outputs in the output directory, then make folders for new outputs
        if clean_output:
            for path in (self.output_dir / "database.db", self.output_dir / "sparse", self.output_dir / "dense"):
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.exists():
                    path.unlink()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sparse_dir.mkdir(parents=True, exist_ok=True)
        self.dense_dir.mkdir(parents=True, exist_ok=True)

        # feature extraction
        subprocess.run([
            self.COLMAP, "feature_extractor",
            "--database_path", self.output_dir / "database.db",
            "--image_path", self.image_dir,
            "--ImageReader.single_camera", "1",
            "--SiftExtraction.max_num_features", "16384"
        ])

        # Feature matching
        subprocess.run([
            self.COLMAP, "exhaustive_matcher",
            "--database_path", self.output_dir / "database.db",
        ])

        # Sparse reconstruction
        subprocess.run([self.COLMAP, "mapper",
            "--database_path", self.output_dir / "database.db",
            "--image_path", self.image_dir,
            "--output_path", self.sparse_dir
        ])

        # Dense reconstruction
        subprocess.run([
            self.COLMAP, "image_undistorter",
            "--image_path", self.image_dir,
            "--input_path", f"{self.sparse_dir}/0",
            "--output_path", self.dense_dir,
            "--max_image_size", "2000"
        ])

        subprocess.run([
            self.COLMAP, "patch_match_stereo",
            "--workspace_path", self.dense_dir,
            "--PatchMatchStereo.max_image_size", "2000",
            "--PatchMatchStereo.num_threads", "4"
        ])

        subprocess.run([
            self.COLMAP, "stereo_fusion",
            "--workspace_path", self.dense_dir,
            "--input_type", "photometric",
            "--output_path", f"{self.dense_dir}/fused.ply",
            "--StereoFusion.min_num_pixels", "3",
            "--StereoFusion.max_reproj_error", "4",
            "--StereoFusion.max_depth_error", "0.03",
            "--StereoFusion.max_normal_error", "20",
            "--StereoFusion.max_image_size", "2000",
            "--StereoFusion.num_threads", "4"
        ])

        self.pcd = o3d.io.read_point_cloud(str(self.dense_dir / "fused.ply"))
    

    def remove_noise(self, nb_neighbors=20, std_ratio=2.0):
        """
        Removes noise from fused.ply point cloud, returns cleaned point cloud and indices of kept points.
        """

        cl, ind = self.pcd.remove_statistical_outlier(nb_neighbors, std_ratio)   # cl = cleaned point cloud, ind = indices of kept points
        return cl, ind
    
    
    def adaptive_subsample(self, voxel_size=0.05, detail_size=0.02):
        """
        Simple implementation to subsample point cloud, keeping detail in complex areas while simplifying flat / uniform areas.
        """
        # compute normals
        self.pcd.estimate_normals()

        # identify high-detail areas
        normals = np.asarray(self.pcd.normals)
        curvature = np.var(normals, axis=1)
        high_detail = curvature > np.percentile(curvature, 75)

        # separate high and low detail points
        points = np.asarray(self.pcd.points)
        high_detail_pcd = o3d.geometry.PointCloud()
        high_detail_pcd.points = o3d.utility.Vector3dVector(points[high_detail])
        low_detail_pcd = o3d.geometry.PointCloud()
        low_detail_pcd.points = o3d.utility.Vector3dVector(points[~high_detail])

        # downsample
        high_detail_down = high_detail_pcd.voxel_down_sample(detail_size)
        low_detail_down = low_detail_pcd.voxel_down_sample(voxel_size)

        # combine
        return high_detail_down + low_detail_down
    

    def extract_features(self, radius=0.1):
        """
        Computes Fast Point Feature Histograms, distance to centroid, and height for each point in the point cloud.
        """
        # compute normals
        self.pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=30))

        # compute local features
        fpfh = o3d.pipelines.registration.compute_fpfh_feature(self.pcd, o3d.geometry.KDTreeSearchParamHybrid(radius=radius*5, max_nn=100))

        # compute global features
        points = np.asarray(self.pcd.points)
        centroid = np.mean(points, axis=0)
        distances = np.linalg.norm(points - centroid, axis=1)

        features = {
            'fpfh': np.asarray(fpfh.data).T,
            'distance_to_centroid': distances,
            'height': points[:, 2] # assuming Z is up
        }

        return features
    

    def point_cloud_to_mesh(self, depth=12):
        """
        Create triangle mesh from the point cloud using Poisson surface reconstruction.
        """
        # estimate normals if not present
        if not self.pcd.has_normals():
            self.pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        
        # poisson surface reconstruction
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(self.pcd, depth=depth)

        # remove low-density vertices
        vertices_to_remove = densities < np.quantile(densities, 0.1)
        mesh.remove_vertices_by_mask(vertices_to_remove)

        return mesh
        
    
    def voxelize(self, voxel_size):
        """
        Discretizes the 3D space with voxels.
        """
        # compute bounds
        points = np.asarray(self.pcd.points)
        min_bound = np.min(points, axis=0)
        max_bound = np.max(points, axis=0)

        # compute voxel indices
        voxel_indices = np.floor((points - min_bound) / voxel_size).astype(int)
        
        # compute voxel grid
        grid_size = np.ceil((max_bound - min_bound) / voxel_size).astype(int)
        voxel_grid = np.zeros(grid_size, dtype=bool)

        # fill voxels
        voxel_grid[voxel_indices[:, 0], voxel_indices[:, 1], voxel_indices[:, 2]] = True

        # make it with open3d
        voxel_grid_o3d = o3d.geometry.VoxelGrid.create_from_point_cloud(self.pcd, voxel_size)

        return voxel_grid_o3d
    
    
    def radius_search(self, points, query_point, radius):
        """
        Uses a k-d tree for efficient radius search.
        Best for only chunks of a dataset when it has many points.
        """
        tree = KDTree(points)
        indices = tree.query_radius([query_point], r=radius)
        return points[indices]
