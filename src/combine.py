import subprocess
import shutil
import open3d as o3d
from pathlib import Path

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
            "--image_path", self.image_dir
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
            "--output_path", self.dense_dir
        ])

        subprocess.run([
            self.COLMAP, "patch_match_stereo",
            "--workspace_path", self.dense_dir
        ])

        subprocess.run([
            self.COLMAP, "stereo_fusion",
            "--workspace_path", self.dense_dir,
            "--output_path", f"{self.dense_dir}/fused.ply"
        ])
    

    def remove_noise(self, nb_neighbors=20, std_ratio=2.0):
        """
        Removes noise from fused.ply point cloud.
        """

        pcd = o3d.io.read_point_cloud(f"{self.dense_dir}/fused.ply")
        cl, ind = pcd.remove_statistical_outlier(nb_neighbors, std_ratio)   # cl = cleaned point cloud, ind = indices of kept points
        return cl, ind

        
