"""
https://www.learnopencv.com/head-pose-estimation-using-opencv-and-dlib/
"""
import cv2
import numpy as np
import open3d

from conv_test import create_cloud, backproject_camera
from conv_vertex_field import draw_axis_pose
from transforms3d.quaternions import quat2mat#, mat2quat

import numpy.linalg as la

def get_vector_angle(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'    """
    cosang = np.dot(v1, v2)
    sinang = np.linalg.norm(np.cross(v1, v2))
    return np.arctan2(sinang, cosang)

def draw_cuboid_2d(img2, cuboid, color):
    assert len(cuboid) == 8
    points = [tuple(pt) for pt in cuboid]
    for ix in range(len(points)):
        pt = points[ix]
        cv2.putText(img2, "%d"%(ix), pt, cv2.FONT_HERSHEY_COMPLEX, 0.5, color)
        cv2.circle(img2, pt, 3, (0,255,0), -1)

    lines = [[0,1],[0,2],[1,3],[2,3],
         [4,5],[4,6],[5,7],[6,7],
         [0,4],[1,5],[2,6],[3,7]]

    for line in lines:
        pt1 = points[line[0]]
        pt2 = points[line[1]]
        cv2.line(img2, pt1, pt2, color)

def get_data():
    im_file = "./datasets/FAT/data/mixed/temple_0/000295.right.jpg"
    # points indexed 3,4 are the front and back ones
    model_points = np.array([
        [-0.05080691, -0.041769,   -0.02880055],
        [-0.05080691,  0.04176 ,   -0.02880055],
        [-0.05080691, -0.041769,    0.02880038],
        [-0.05080691,  0.04176 ,    0.02880038],
        [ 0.0508229 , -0.041769,   -0.02880055],
        [ 0.0508229 ,  0.04176 ,   -0.02880055],
        [ 0.0508229 , -0.041769,    0.02880038],
        [ 0.0508229 ,  0.04176 ,    0.02880038],
    ])
    image_points = np.array([
        [569, 299],
        [526, 309],
        [589, 329],
        [546, 337],
        [538, 348],
        [495, 355],
        [561, 379],
        [517, 384],
    ], dtype=np.float32)
    # image_points = np.array([
    #     [575, 304],
    #     [530, 311],
    #     [580, 332],
    #     [540, 332],
    #     [533, 350],
    #     [496, 350],
    #     [564, 383],
    #     [514, 389],
    # ], dtype=np.float32)
    cls = 9
    pred_R = np.array([[-0.13374473, -0.39525998,  0.41382402],
         [ 0.60616624,  0.03293807,  0.56743467],
         [-0.33144197,  0.24944006,  0.50241154]],
    )

    im_file = "./datasets/FAT/data/mixed/temple_0/001600.right.jpg"
    model_points = np.array([
        [-0.10122322, -0.04362476, -0.00781424],
        [-0.10122322,  0.04369109, -0.00781424],
        [-0.10122322, -0.04362476,  0.00778602],
        [-0.10122322,  0.04369109,  0.00778602],
        [ 0.10129841, -0.04362476, -0.00781424],
        [ 0.10129841,  0.04369109, -0.00781424],
        [ 0.10129841, -0.04362476,  0.00778602],
        [ 0.10129841,  0.04369109,  0.00778602],
    ])
    image_points = np.array([
        [400, 457],
        [452, 446],
        [397, 445],
        [449, 435],
        [492, 414],
        [547, 404],
        [488, 401],
        [543, 392],
    ], dtype=np.float32)
    cls = 17
    pred_R = np.array([[ 0.8092772,   0.32167298, -0.07783523],
         [ 0.055264 ,   0.51261824, -0.32159093],
         [-0.04363448 , 0.5587809 ,  0.38377702]],
    )

    # im_file = "./datasets/FAT/data/mixed/temple_0/000127.left.jpg"
    # model_points = np.array([
    #     [-0.081932, -0.106709, -0.035852],
    #     [-0.081932,  0.106668, -0.035852],
    #     [-0.081932, -0.106709,  0.035837],
    #     [-0.081932,  0.106668,  0.035837],
    #     [ 0.081727, -0.106709, -0.035852],
    #     [ 0.081727,  0.106668, -0.035852],
    #     [ 0.081727, -0.106709,  0.035837],
    #     [ 0.081727,  0.106668,  0.035837]
    # ])
    # image_points = [[471, 395],
    #     [543, 477],
    #     [471, 355],
    #     [545, 432],
    #     [369, 424],
    #     [428, 517],
    #     [366, 382],
    #     [426, 470]]
    # cls = 2
    # pred_R = np.array([[-0.49625674, -0.07090731, -0.03685391],
    #      [-0.02566289, 0.2529236 , -0.552534  ],
    #      [-0.08301728, -0.07011836, -0.465668  ]])

    # im_file = "./datasets/FAT/data/mixed/temple_0/001600.right.jpg"
    # model_points = [
    #     [-0.05080691, -0.041769 ,  -0.02880055],
    #     [-0.05080691,  0.04176  ,  -0.02880055],
    #     [-0.05080691, -0.041769 ,   0.02880038],
    #     [-0.05080691,  0.04176  ,   0.02880038],
    #     [ 0.0508229 , -0.041769 ,  -0.02880055],
    #     [ 0.0508229 ,  0.04176  ,  -0.02880055],
    #     [ 0.0508229 , -0.041769 ,   0.02880038],
    #     [ 0.0508229 ,  0.04176  ,   0.02880038]
    #  ]
    # image_points = [[684, 341],
    #  [744, 323],
    #  [683, 345],
    #  [746, 325],
    #  [709, 411],
    #  [769, 394],
    #  [709, 419],
    #  [774, 401]]
    # cls = 9
    # pred_R = np.array([[ 0.04379589, 0.6991153 , -0.07654756],
    #      [ 0.41686264, 0.21312058, -0.37969974],
    #      [-0.30132285, 0.1908857 , -0.6128634 ]],
    # )

    im_file = "./datasets/FAT/data/mixed/temple_0/000127.left.jpg"
    model_points = [[-0.03359818, -0.050927,   -0.0338576 ],
     [-0.03359818,  0.050916 ,  -0.0338576 ],
     [-0.03359818, -0.050927 ,   0.03385666],
     [-0.03359818,  0.050916 ,   0.03385666],
     [ 0.03361415, -0.050927 ,  -0.0338576 ],
     [ 0.03361415,  0.050916 ,  -0.0338576 ],
     [ 0.03361415, -0.050927 ,   0.03385666],
     [ 0.03361415,  0.050916 ,   0.03385666]]
    image_points = [[730, 411],
     [722, 476],
     [699, 434],
     [691, 500],
     [685, 389],
     [679, 452],
     [653, 410],
     [648, 474]]
    cls = 4
    pred_R = np.array([[-0.790117  , -0.00430778, -0.34703857],
         [-0.04868058,  0.81629056,  0.26626855],
         [ 0.3662843 ,  0.54237545, -0.7064773 ]])

    # image_points = np.array(image_points)[[0, 4, 1, 5, 2, 6, 3, 7]]

    model_points = np.vstack((model_points, [0,0,0]))
    center = np.mean(image_points, axis=0)
    image_points = np.vstack((image_points, center)).astype(np.float32)
    pred_R = np.array(pred_R)

    return model_points, image_points, im_file, cls, pred_R

from transforms3d.euler import euler2mat

def get_rotate_mat(angle, axis=0):
    rad = np.radians(angle)
    axes = [0,0,0]
    axes[axis] = rad
    return euler2mat(*axes)

def get_rotate(R_array, init_R=np.identity(3)):
    RR = init_R.copy()
    for R in R_array:
        RR = np.dot(R, RR)
    return RR


if __name__ == '__main__':

    points_file = "./datasets/FAT/points_all_orig.npy"
    points = np.load(points_file)

    # Read Image
    model_points, image_points, im_file, cls, pred_R = get_data()
    depth_file = im_file.replace(".jpg",".depth.png")


    intrinsics = np.array([[768.1605834960938, 0.0, 480.0], [0.0, 768.1605834960938, 270.0], [0.0, 0.0, 1.0]])
    factor_depth=10000

    img = cv2.imread(im_file)
    # img = np.zeros((800,800,3), dtype=np.uint8) #cv2.imread("headPose.jpg")
    H,W,_ = img.shape

    # load depth and cloud
    depth = cv2.imread(depth_file, cv2.IMREAD_UNCHANGED)

    rgb = img.copy()[:,:,::-1]
    if rgb.dtype == np.uint8:
        rgb = rgb.astype(np.float32) / 255
    X = backproject_camera(depth, intrinsics, factor_depth)
    scene_cloud = create_cloud(X.T, colors=rgb.reshape((H*W,3)))

    ordering = np.array([0,1,2,3,4,5,6,7,8])
    # ordering = np.array([6,7,4,5,2,3,0,1,8])  # rotate 180 by one axis
    # ordering = np.array([4,5,0,1,6,7,2,3,8])  # rotate 90 by one axis
    # ordering = np.array([3,2,1,0,7,6,5,4,8])  # rotate 180 by other axis
    # ordering = np.array([5,4,7,6,1,0,3,2,8])  # rotate 180 by other axis

    image_points = image_points[ordering]

    camera_matrix = intrinsics

    # print("Camera Matrix :\n %s"%(camera_matrix))
     
    dist_coeffs = np.zeros((4,1)) # Assuming no lens distortion
    pnp_algorithm = cv2.SOLVEPNP_ITERATIVE 
    success, rotation_vector, translation_vector = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=pnp_algorithm)
    # success, rotation_vector, translation_vector, inliers = cv2.solvePnPRansac(model_points, image_points, camera_matrix, dist_coeffs, flags=pnp_algorithm)#, iterationsCount=1000)
     
    # print("Rotation Vector:\n %s"%(rotation_vector))
    # print("Translation Vector:\n %s"%(translation_vector))

    R, j = cv2.Rodrigues(rotation_vector)
    im = img.copy()
    im = draw_axis_pose(im, R, translation_vector.squeeze(), camera_matrix, dist_coeffs)
     
    draw_cuboid_2d(im, image_points[:8], (255,0,0)) 
    cv2.circle(im, tuple(image_points[-1]), 4, (0,0,255), -1)

    # AAA
    theeight = np.array([
        [1,1,1],  # top right, back
        [1,-1,1],  # bottom right, back
        [1,1,-1],  # top right, front
        [1,-1,-1],  # bottom right, front
        
        [-1,1,1],  # top left, back
        [-1,-1,1],  # bottom left, back
        [-1,1,-1],  # top left, front
        [-1,-1,-1],  # bottom left, front

        [0,0,0]  # centroid
    ], dtype=np.float32)
    theeight_ordering = np.array([0,1,2,3,4,5,6,7,8])
    theeight_points = image_points[theeight_ordering] 
    side_mapping = [[0,4],[0,1],[0,2]] # x (left-right), y (bottom-top), z (front-back)
    sides = np.zeros((3), dtype=np.float32)
    for ix,m in enumerate(side_mapping):
        dist = np.linalg.norm(theeight_points[m[0]] - theeight_points[m[1]]) 
        sides[ix] = dist / 2
    theeight_model_points = theeight * sides
    s,rvec2,t = cv2.solvePnP(theeight_model_points, theeight_points, camera_matrix, dist_coeffs)
    R2, j = cv2.Rodrigues(rvec2)

    # thesix = np.array([
    #     [1,1,1],  # top right
    #     [1,-1,1],  # mid right
    #     [1,-1,-1],  # bottom right
    #     [-1,-1,-1],  # bottom left
    #     [-1,1,-1],  # mid left
    #     [-1,1,1],  # top left
    #     [0,0,0]  # centroid
    # ], dtype=np.float32)
    # thesix_ordering = np.array([0,2,6,7,5,1,8])
    # # thesix_ordering = np.array([0,2,6,7,5,1,8])
    # thesix_points = image_points[thesix_ordering] 

    # sides = np.zeros((3), dtype=np.float32)
    # for ix,o in enumerate(thesix_ordering[1:4]):
    #     p1i = thesix_ordering[ix]
    #     p2i = thesix_ordering[ix+1]
    #     dist = np.linalg.norm(image_points[p1i] - image_points[p2i]) 
    #     sides[ix] = dist / 2
    # sides = sides[[2,0,1]]
    # thesix_model_points = thesix * sides
    # # thesix_points = image_points[thesix_ordering]
    # s,rvec2,t = cv2.solvePnP(thesix_model_points, thesix_points, camera_matrix, dist_coeffs)
    # R2, j = cv2.Rodrigues(rvec2)
    # """
    # red direction: 2,3
    # blue direction: 3,4,5
    # green direction: 1,2,3

    # Need to change to:
    # red direction: 1,2,3
    # blue direction: 2,3
    # green direction: 3,4,5
    # """
    # for ix, pt in enumerate(thesix_points[:-1]):
    #     pt = tuple(pt)
    #     cv2.circle(im2, pt, 4, (0,255,0), -1)
    #     cv2.putText(im2, "%d"%(ix), pt, cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,255)) 
    #     cv2.line(im2, pt, tuple(thesix_points[(ix+1)%6]), (0,0,255))

    im2 = img.copy()
    draw_cuboid_2d(im2, theeight_points[:8], (255,0,0)) 
    R_init = pred_R #np.dot(R, get_rotate_mat(90,0))
    im2 = draw_axis_pose(im2, R_init, translation_vector.squeeze(), camera_matrix, dist_coeffs)

    # Display image
    cv2.imshow("GT", im)
    cv2.imshow("P", im2)
    cv2.waitKey(0)

    object_points = points[cls]
    M = np.identity(4)
    M[:3,:3] = R
    M[:3,-1] = translation_vector.squeeze()
    object_cloud = create_cloud(object_points, T=M)

    open3d.draw_geometries([scene_cloud, object_cloud])

    Rc = R_init.T
    R2c = R2.T
    angle_matrix = np.zeros((3,3), dtype=np.float32)
    for i in range(3):
        for j in range(3):
            angle_matrix[i,j] = get_vector_angle( Rc[i], R2c[j] )
    similarity_matrix = np.sin(angle_matrix)
    print(similarity_matrix)

    best = np.argsort(similarity_matrix.flatten()) # small to large  (smaller means more similar)
    assigned = 0
    axes = np.zeros((3), dtype=np.int32)
    last_axis_sign = 1
    for ix,b in enumerate(best):
        i = b // 3 
        j = b % 3
        # check if 
        if axes[i] != 0:
            continue
        # get the sign (+/-) of cosine similarity
        cos_similarity = np.cos(angle_matrix[i,j])
        sign = np.sign(cos_similarity)
        axes[i] = sign * (j+1)
        # last_axis_sign *= sign
        assigned += 1
        if assigned == 2: # np.sum(axes != 0) >= 2: # only need to know direction of 2 axes to know the third
            break

    aa = {
        (1,2,3): [get_rotate_mat(0,0)], # default
        (1,-2,-3): [get_rotate_mat(180,0)],  # rotated 180 around x
        (1,-3,2): [get_rotate_mat(270,0)],   # rotated 90 clockwise around x
        (1,3,-2): [get_rotate_mat(90,0)],  # rotated 270 clockwise around x

        # start with -1 (rotate 180 around y from default)
        (-1,2,-3): [get_rotate_mat(180,1)],   # 
        (-1,-2,3): [get_rotate_mat(180,1), get_rotate_mat(180,0)],   # then rotate 180 around x
        (-1,3,2): [get_rotate_mat(180,1), get_rotate_mat(90,0)],   # then rotate 90 clockwise around x
        (-1,-3,-2): [get_rotate_mat(180,1), get_rotate_mat(270,0)],   # then rotate 270 clockwise around x

        # start with 2 (rotate 270 clockwise around z from default)
        (2,-1,3): [get_rotate_mat(90,2)],   # 
        (2,1,-3): [get_rotate_mat(90,2),get_rotate_mat(180,1)],   # then rotate 180 around y
        (2,3,1): [get_rotate_mat(90,2),get_rotate_mat(90,1)],   # then rotate 90 clockwise around y
        (2,-3,-1): [get_rotate_mat(90,2),get_rotate_mat(270,1)],   # then rotate 270 clockwise around y

        # start with -2 (rotate 90 clockwise around z from default)
        (-2,1,3): [get_rotate_mat(270,2)],   # 
        (-2,-1,-3): [get_rotate_mat(270,2),get_rotate_mat(180,1)],   # then rotate 180 around y
        (-2,-3,1): [get_rotate_mat(270,2),get_rotate_mat(90,1)],   # then rotate 90 clockwise around y
        (-2,3,-1): [get_rotate_mat(270,2),get_rotate_mat(270,1)],   # then rotate 270 clockwise around y

        # start with 3 (rotate 270 clockwise around y from default)
        (3,2,-1): [get_rotate_mat(270,1)],   # 
        (3,-2,1): [get_rotate_mat(270,1),get_rotate_mat(180,2)],   # then rotate 180 around z
        (3,-1,-2): [get_rotate_mat(270,1),get_rotate_mat(90,2)],   # then rotate 90 clockwise around z
        (3,1,2): [get_rotate_mat(270,1),get_rotate_mat(270,2)],   # then rotate 270 clockwise around z

        # start with -3 (rotate 90 clockwise around y from default)
        (-3,2,1): [get_rotate_mat(90,1)],   # 
        (-3,-2,-1): [get_rotate_mat(90,1),get_rotate_mat(180,2)],   # then rotate 180 around z
        (-3,-1,2): [get_rotate_mat(90,1),get_rotate_mat(90,2)],   # then rotate 90 clockwise around z
        (-3,1,-2): [get_rotate_mat(90,1),get_rotate_mat(270,2)],   # then rotate 270 clockwise around z
    }


    hashx = dict((tuple(v), ix) for ix, v in enumerate(theeight))
    aa_order = {}
    for k in aa:
        x = np.dot(get_rotate(aa[k]), theeight.T).T 
        x = np.round(x)[:-1]
        aa_order[k] = [hashx[tuple(v)] for v in x]

    OLD = True
    if not OLD:
        newkeys = []
        for k in aa_order:
            k2 = np.array(k)
            ix = np.where(np.abs(k2) == 2)[0][0]
            k2[ix] *= -1
            v = aa_order[k]
            v2 = []
            for i in range(len(v) // 2):
                v2 += [v[i*2+1], v[i*2]]
            newkeys.append([tuple(k2), v2])

        for d in newkeys:
            k, v = d
            aa_order[k] = v

        last_axis = (1+2+3) - np.abs(axes).sum()
        i = np.where(axes==0)[0][0]
        cos_similarity = np.cos(angle_matrix[i,last_axis - 1])
        sign = np.sign(cos_similarity)            
        axes[i] = sign * last_axis
    else:
        valid_axes = np.where(axes!=0)[0]
        ax = axes[valid_axes]
        for k in aa:
            if k[valid_axes[0]] == ax[0]:
                if k[valid_axes[1]] == ax[1]:
                    axes = k
                    break

    axes2 = tuple(axes)
    print(axes2, aa_order[axes2])

    final_ordering = aa_order[axes2]
    final_ordering += [-1]
    final_image_points = image_points[final_ordering]
    s,rvec3,t = cv2.solvePnP(model_points, final_image_points, camera_matrix, dist_coeffs)
    R3, j = cv2.Rodrigues(rvec3)
    im3 = img.copy()
    draw_cuboid_2d(im3, final_image_points[:-1], (255,0,0)) 
    im3 = draw_axis_pose(im3, R3, translation_vector.squeeze(), camera_matrix, dist_coeffs)

    # Display image
    cv2.imshow("P2", im3)
    cv2.waitKey(0)
