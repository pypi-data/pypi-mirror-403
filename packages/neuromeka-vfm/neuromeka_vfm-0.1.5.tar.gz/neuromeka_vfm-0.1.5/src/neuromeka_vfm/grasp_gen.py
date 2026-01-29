from typing import Tuple

import numpy as np
import trimesh

from . import point_cloud_utils


class GraspPoseGeneration:
    """
    Wrapper class for point cloud utilities used in grasp pose workflows.
    """

    def knn_points(self, X: np.ndarray, K: int, norm: int):
        return point_cloud_utils.knn_points(X=X, K=K, norm=norm)

    def point_cloud_outlier_removal(
        self, obj_pc: np.ndarray, threshold: float = 0.014, K: int = 20
    ) -> Tuple[np.ndarray, np.ndarray]:
        return point_cloud_utils.point_cloud_outlier_removal(
            obj_pc=obj_pc, threshold=threshold, K=K
        )

    def point_cloud_outlier_removal_with_color(
        self,
        obj_pc: np.ndarray,
        obj_pc_color: np.ndarray,
        threshold: float = 0.014,
        K: int = 20,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        return point_cloud_utils.point_cloud_outlier_removal_with_color(
            obj_pc=obj_pc,
            obj_pc_color=obj_pc_color,
            threshold=threshold,
            K=K,
        )

    def depth_and_segmentation_to_point_clouds(
        self,
        depth_image: np.ndarray,
        segmentation_mask: np.ndarray,
        fx: float,
        fy: float,
        cx: float,
        cy: float,
        rgb_image: np.ndarray = None,
        target_object_id: int = 1,
        remove_object_from_scene: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        return point_cloud_utils.depth_and_segmentation_to_point_clouds(
            depth_image=depth_image,
            segmentation_mask=segmentation_mask,
            fx=fx,
            fy=fy,
            cx=cx,
            cy=cy,
            rgb_image=rgb_image,
            target_object_id=target_object_id,
            remove_object_from_scene=remove_object_from_scene,
        )

    def filter_colliding_grasps(
        self,
        scene_pc: np.ndarray,
        grasp_poses: np.ndarray,
        gripper_collision_mesh: trimesh.Trimesh,
        collision_threshold: float = 0.002,
        num_collision_samples: int = 2000,
    ) -> np.ndarray:
        return point_cloud_utils.filter_colliding_grasps(
            scene_pc=scene_pc,
            grasp_poses=grasp_poses,
            gripper_collision_mesh=gripper_collision_mesh,
            collision_threshold=collision_threshold,
            num_collision_samples=num_collision_samples,
        )


__all__ = ["GraspPoseGeneration"]
