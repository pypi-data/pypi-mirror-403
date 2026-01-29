# Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import logging
from typing import Tuple, Dict

import numpy as np
import trimesh
import trimesh.transformations as tra
from tqdm import tqdm

logger = logging.getLogger(__name__)


def _pairwise_distances(X: np.ndarray, Y: np.ndarray, norm: int) -> np.ndarray:
    if norm == 1:
        return np.sum(np.abs(X[:, None, :] - Y[None, :, :]), axis=2)
    if norm == 2:
        diff = X[:, None, :] - Y[None, :, :]
        return np.sqrt(np.sum(diff * diff, axis=2))
    diff = X[:, None, :] - Y[None, :, :]
    return np.linalg.norm(diff, ord=norm, axis=2)


def knn_points(X: np.ndarray, K: int, norm: int):
    """
    Computes the K-nearest neighbors for each point in the point cloud X.

    Args:
        X: (N, 3) array representing the point cloud.
        K: Number of nearest neighbors.

    Returns:
        dists: (N, K) array containing distances to the K nearest neighbors.
        idxs: (N, K) array containing indices of the K nearest neighbors.
    """
    X = np.asarray(X, dtype=np.float32)
    if X.ndim != 2 or X.shape[1] != 3:
        raise ValueError("X must be a (N, 3) array")
    if K <= 0:
        raise ValueError("K must be positive")
    N, _ = X.shape
    if K >= N:
        raise ValueError("K must be smaller than number of points")

    dists_out = np.empty((N, K), dtype=np.float32)
    idxs_out = np.empty((N, K), dtype=np.int64)

    max_bytes = 64 * 1024 * 1024
    bytes_per_row = N * X.dtype.itemsize
    chunk_size = max(1, min(N, max_bytes // max(bytes_per_row, 1)))

    for start in range(0, N, chunk_size):
        end = min(start + chunk_size, N)
        chunk = X[start:end]
        dist_matrix = _pairwise_distances(chunk, X, norm=norm)

        row_idx = np.arange(end - start)
        col_idx = row_idx + start
        dist_matrix[row_idx, col_idx] = np.inf

        idx_part = np.argpartition(dist_matrix, K, axis=1)[:, :K]
        dist_part = np.take_along_axis(dist_matrix, idx_part, axis=1)
        order = np.argsort(dist_part, axis=1)
        idxs = np.take_along_axis(idx_part, order, axis=1)
        dists = np.take_along_axis(dist_part, order, axis=1)

        dists_out[start:end] = dists
        idxs_out[start:end] = idxs

    return dists_out, idxs_out


def point_cloud_outlier_removal(
    obj_pc: np.ndarray, threshold: float = 0.014, K: int = 20
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Remove outliers from a point cloud. K-nearest neighbors is used to compute
    the distance to the nearest neighbor for each point. If the distance is
    greater than a threshold, the point is considered an outlier and removed.

    Args:
        obj_pc (np.ndarray): (N, 3) array representing the point cloud.
        threshold (float): Distance threshold for outlier detection. Points with mean distance to
            K nearest neighbors greater than this threshold are removed.
        K (int): Number of nearest neighbors to consider for outlier detection.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Tuple containing filtered and removed point clouds.
    """
    obj_pc = np.asarray(obj_pc, dtype=np.float32)
    if obj_pc.ndim != 2 or obj_pc.shape[1] != 3:
        raise ValueError("obj_pc must be a (N, 3) array")

    nn_dists, _ = knn_points(obj_pc, K=K, norm=1)

    mask = nn_dists.mean(axis=1) < threshold
    filtered_pc = obj_pc[mask]
    removed_pc = obj_pc[~mask]

    logger.info(
        "Removed %s points from point cloud",
        obj_pc.shape[0] - filtered_pc.shape[0],
    )
    return filtered_pc, removed_pc


def point_cloud_outlier_removal_with_color(
    obj_pc: np.ndarray,
    obj_pc_color: np.ndarray,
    threshold: float = 0.014,
    K: int = 20,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Remove outliers from a point cloud with colors.

    Args:
        obj_pc (np.ndarray): (N, 3) array representing the point cloud.
        obj_pc_color (np.ndarray): (N, 3) array representing the point cloud color.
        threshold (float): Distance threshold for outlier detection. Points with mean distance to
            K nearest neighbors greater than this threshold are removed.
        K (int): Number of nearest neighbors to consider for outlier detection.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]: Tuple containing filtered and
            removed point clouds and colors.
    """
    obj_pc = np.asarray(obj_pc, dtype=np.float32)
    obj_pc_color = np.asarray(obj_pc_color, dtype=np.float32)
    if obj_pc.ndim != 2 or obj_pc.shape[1] != 3:
        raise ValueError("obj_pc must be a (N, 3) array")
    if obj_pc_color.shape != obj_pc.shape:
        raise ValueError("obj_pc_color must match obj_pc shape")

    nn_dists, _ = knn_points(obj_pc, K=K, norm=1)

    mask = nn_dists.mean(axis=1) < threshold
    filtered_pc = obj_pc[mask]
    removed_pc = obj_pc[~mask]

    filtered_pc_color = obj_pc_color[mask]
    removed_pc_color = obj_pc_color[~mask]

    logger.info(
        "Removed %s points from point cloud",
        obj_pc.shape[0] - filtered_pc.shape[0],
    )
    return filtered_pc, removed_pc, filtered_pc_color, removed_pc_color


def depth2points(
    depth: np.array,
    fx: int,
    fy: int,
    cx: int,
    cy: int,
    xmap: np.array = None,
    ymap: np.array = None,
    rgb: np.array = None,
    seg: np.array = None,
    mask: np.arange = None,
) -> Dict:
    """Compute point cloud from a depth image."""
    if rgb is not None:
        assert rgb.shape[0] == depth.shape[0] and rgb.shape[1] == depth.shape[1]
    if xmap is not None:
        assert xmap.shape[0] == depth.shape[0] and xmap.shape[1] == depth.shape[1]
    if ymap is not None:
        assert ymap.shape[0] == depth.shape[0] and ymap.shape[1] == depth.shape[1]

    im_height, im_width = depth.shape[0], depth.shape[1]

    if xmap is None or ymap is None:
        ww = np.linspace(0, im_width - 1, im_width)
        hh = np.linspace(0, im_height - 1, im_height)
        xmap, ymap = np.meshgrid(ww, hh)

    pt2 = depth
    pt0 = (xmap - cx) * pt2 / fx
    pt1 = (ymap - cy) * pt2 / fy

    mask_depth = np.ma.getmaskarray(np.ma.masked_greater(pt2, 0))
    if mask is None:
        mask = mask_depth
    else:
        mask_semantic = np.ma.getmaskarray(np.ma.masked_equal(mask, 1))
        mask = mask_depth * mask_semantic

    index = mask.flatten().nonzero()[0]

    pt2_valid = pt2.flatten()[:, np.newaxis].astype(np.float32)
    pt0_valid = pt0.flatten()[:, np.newaxis].astype(np.float32)
    pt1_valid = pt1.flatten()[:, np.newaxis].astype(np.float32)
    pc_xyz = np.concatenate((pt0_valid, pt1_valid, pt2_valid), axis=1)
    if rgb is not None:
        r = rgb[:, :, 0].flatten()[:, np.newaxis]
        g = rgb[:, :, 1].flatten()[:, np.newaxis]
        b = rgb[:, :, 2].flatten()[:, np.newaxis]
        pc_rgb = np.concatenate((r, g, b), axis=1)
    else:
        pc_rgb = None

    if seg is not None:
        pc_seg = seg.flatten()[:, np.newaxis]
    else:
        pc_seg = None

    return {"xyz": pc_xyz, "rgb": pc_rgb, "seg": pc_seg, "index": index}


def depth_and_segmentation_to_point_clouds(
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
    """
    Convert depth image and instance segmentation mask to scene and object point clouds.

    Args:
        depth_image: HxW depth image in meters
        segmentation_mask: HxW instance segmentation mask with integer labels
        fx, fy, cx, cy: Camera intrinsic parameters
        rgb_image: HxWx3 RGB image (optional, for colored point clouds)
        target_object_id: ID of the target object in the segmentation mask
        remove_object_from_scene: If True, removes object points from scene point cloud

    Returns:
        scene_pc: Nx3 point cloud of the entire scene (excluding object if remove_object_from_scene=True)
        object_pc: Mx3 point cloud of the target object only
        scene_colors: Nx3 RGB colors for scene points (or None)
        object_colors: Mx3 RGB colors for object points (or None)

    Raises:
        ValueError: If no target object found or multiple objects detected
    """
    unique_ids = np.unique(segmentation_mask)
    if target_object_id not in unique_ids:
        raise ValueError(
            f"Target object ID {target_object_id} not found in segmentation mask. Available IDs: {unique_ids}"
        )

    non_background_ids = unique_ids[unique_ids != 0]
    if len(non_background_ids) > 1:
        raise ValueError(
            "Multiple objects detected in segmentation mask: "
            f"{non_background_ids}. Please ensure only one object is present."
        )

    pts_data = depth2points(
        depth=depth_image,
        fx=int(fx),
        fy=int(fy),
        cx=int(cx),
        cy=int(cy),
        rgb=rgb_image,
        seg=segmentation_mask,
    )

    xyz = pts_data["xyz"]
    rgb = pts_data["rgb"]
    seg = pts_data["seg"]
    index = pts_data["index"]

    xyz_valid = xyz[index]
    seg_valid = seg[index] if seg is not None else None
    rgb_valid = rgb[index] if rgb is not None else None

    scene_pc = xyz_valid
    scene_colors = rgb_valid

    if seg_valid is not None:
        object_mask = seg_valid.flatten() == target_object_id
        object_pc = xyz_valid[object_mask]
        object_colors = rgb_valid[object_mask] if rgb_valid is not None else None

        if remove_object_from_scene:
            scene_mask = ~object_mask
            scene_pc = xyz_valid[scene_mask]
            scene_colors = rgb_valid[scene_mask] if rgb_valid is not None else None
            logger.info(
                "Removed %s object points from scene point cloud",
                np.sum(object_mask),
            )
    else:
        raise ValueError("Segmentation data not available from depth2points")

    if len(object_pc) == 0:
        raise ValueError(f"No points found for target object ID {target_object_id}")

    logger.info("Scene point cloud: %s points", len(scene_pc))
    logger.info("Object point cloud: %s points", len(object_pc))

    return scene_pc, object_pc, scene_colors, object_colors


def filter_colliding_grasps(
    scene_pc: np.ndarray,
    grasp_poses: np.ndarray,
    gripper_collision_mesh: trimesh.Trimesh,
    collision_threshold: float = 0.002,
    num_collision_samples: int = 2000,
) -> np.ndarray:
    """
    Filter grasps based on collision detection with scene point cloud.

    Args:
        scene_pc: Nx3 scene point cloud
        grasp_poses: Kx4x4 array of grasp poses
        gripper_collision_mesh: Trimesh of gripper collision geometry
        collision_threshold: Distance threshold for collision detection (meters)
        num_collision_samples: Number of points to sample from gripper mesh surface

    Returns:
        collision_mask: K-length boolean array, True if grasp is collision-free
    """
    gripper_surface_points, _ = trimesh.sample.sample_surface(
        gripper_collision_mesh, num_collision_samples
    )
    gripper_surface_points = np.array(gripper_surface_points)

    scene_pc = np.asarray(scene_pc, dtype=np.float32)
    collision_free_mask = []

    logger.info(
        "Checking collision for %s grasps against %s scene points...",
        len(grasp_poses),
        len(scene_pc),
    )

    for _, grasp_pose in tqdm(
        enumerate(grasp_poses), total=len(grasp_poses), desc="Collision checking"
    ):
        gripper_points_transformed = tra.transform_points(
            gripper_surface_points, grasp_pose
        ).astype(np.float32, copy=False)

        min_distances_sq = []
        batch_size = 100
        for j in range(0, len(gripper_points_transformed), batch_size):
            batch_gripper_points = gripper_points_transformed[j : j + batch_size]
            diff = batch_gripper_points[:, None, :] - scene_pc[None, :, :]
            dist_sq = np.einsum("ijk,ijk->ij", diff, diff)
            batch_min_dist_sq = np.min(dist_sq, axis=1)
            min_distances_sq.append(batch_min_dist_sq)

        all_min_distances_sq = np.concatenate(min_distances_sq, axis=0)
        collision_detected = np.any(
            all_min_distances_sq < collision_threshold * collision_threshold
        )
        collision_free_mask.append(not bool(collision_detected))

    collision_free_mask = np.array(collision_free_mask)
    num_collision_free = np.sum(collision_free_mask)
    logger.info("Found %s/%s collision-free grasps", num_collision_free, len(grasp_poses))

    return collision_free_mask


__all__ = [
    "knn_points",
    "point_cloud_outlier_removal",
    "point_cloud_outlier_removal_with_color",
    "depth2points",
    "depth_and_segmentation_to_point_clouds",
    "filter_colliding_grasps",
]
