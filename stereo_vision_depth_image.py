# -*- coding: utf-8 -*-
"""stereo_vision_depth_image.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Sdt26pP3Byv3pzvboBY_ONLFyvf8CWx9

ENPM673: Perception for Autonomous Robots

By: Shivam Dhakad

Problem1 Dataset: https://drive.google.com/drive/folders/1QRWZaUvkLn_vJQq0bPVQhtoK0c44-Otx?usp=sharing
"""

# Commented out IPython magic to ensure Python compatibility.
#mounting the drive
try:
    from google.colab import drive
    drive.mount('/content/drive', force_remount=True)
    FOLDERNAME =  "ENPM673/project3/"
    assert FOLDERNAME is not None, "[!] Enter the foldername."
#     %cd drive/My\ Drive
#     %cd $FOLDERNAME
except ModuleNotFoundError as ex:
    print("Please run this snippet in Google Colab")

# Import Libraries
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import os
import glob
from time import sleep

"""##Pipeline for Stereo Vision System

"""

# input camera properties

# classroom camera
# K camera matrix for classroom dataset
C_K1=np.array([[1746.24, 0, 14.88],[ 0, 1746.24 , 534.11],[0, 0 ,1]])     # input
C_K2=np.array([[1746.24 ,0 ,14.88],[0, 1746.24 , 534.11],[ 0 ,0, 1]])  # input

doffs=0
C_baseline=678.37   #input
width=1920
height=1080
C_ndisp=310 # input  #conservative bound on the number of disparity levels
C_vmin=60 # input    # tight bound on minimum and maximum disparities
C_vmax=280  # input    #tight bound on minimum and maximum disparities
C_dataset_no = 1
C_calib_properties = [C_K1,C_K2,C_baseline, C_ndisp,C_vmin, C_vmax,1]

# storage camera
S_K1 = np.array([[1742.11 , 0 ,804.90],[ 0 ,1742.11, 541.22],[ 0 ,0, 1]])# input
S_K2 = np.array([[1742.11, 0 ,804.90],[ 0 ,1742.11, 541.22],[ 0 ,0 ,1]])# input

doffs=0
S_baseline=221.76
width=1920
height=1080
S_ndisp=100
S_vmin=29
S_vmax=61
S_dataset_no = 1
S_calib_properties = [S_K1, S_K2, S_baseline, S_ndisp, S_vmin, S_vmax,2]

# trapzone camera
T_K1 = np.array([[1769.02, 0 ,1271.89],[0 ,1769.02, 527.17],[ 0, 0 ,1]]) # input
T_K2 = np.array([[1769.02 ,0, 1271.89],[ 0, 1769.02 ,527.17],[0 ,0, 1]])# input

doffs=0
T_baseline=295.44
T_width=1920
T_height=1080
T_ndisp=140
T_vmin=25
T_vmax=118
T_dataset_no = 3
T_calib_properties = [T_K1, T_K2, T_baseline, T_ndisp, T_vmin, T_vmax,3]

calib_properties_list=[C_calib_properties,S_calib_properties,T_calib_properties]

# load images from dataset

# Define the base folder path (replace with yours)
base_folder1 = "problem2_dataset/classroom"
base_folder2 = "problem2_dataset/traproom"
base_folder3 = "problem2_dataset/storageroom"

Cimage1_path = f"{base_folder1}/im0.png"  # Combine path with filename
Cimage2_path = f"{base_folder1}/im1.png"

Simage1_path = f"{base_folder2}/im1.png"
Simage2_path = f"{base_folder2}/im0.png"

Timage1_path = f"{base_folder3}/im0.png"
Timage2_path = f"{base_folder3}/im1.png"
image_list = []  # list to store image dataset

dataset_list = [Cimage1_path,Cimage2_path],[Simage1_path,Simage2_path],[Timage1_path,Timage2_path]
for dataset in dataset_list:
    image1_path,image2_path = dataset
    # print("")
    img1 = cv.imread(image1_path)[:,:,:3]  # Read ignoring alpha channel
    img1 = cv.cvtColor(img1, cv.COLOR_BGR2GRAY)
    img2 = cv.imread(image2_path)[:,:,:3]
    img2 = cv.cvtColor(img2, cv.COLOR_BGR2GRAY)
    image_list.append([img1,img2])
    # plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
    # plt.subplot(121),plt.imshow(img1)
    # plt.subplot(122),plt.imshow(img2)
    # plt.show()

## pipeline

# FUNCTION: STEREO_VISION PIPELINE

def pipeline_stereovision(img1,img2,K1,K2,baseline, ndisp,vmin,vmax):

  #plotting origianl dataset images
  plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
  plt.subplot(121),plt.title('orignal_image1'),plt.imshow(img1)
  plt.subplot(122),plt.title('original_image2'),plt.imshow(img2)
  plt.show()

  # feature detector
  sift = cv.SIFT_create()

  # find the keypoints and descriptors with SIFT
  kp1, des1 = sift.detectAndCompute(img1,None)
  kp2, des2 = sift.detectAndCompute(img2,None)

  # FLANN parameters
  FLANN_INDEX_KDTREE = 1
  index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
  search_params = dict(checks=50)
  # feature points matching method
  flann = cv.FlannBasedMatcher(index_params,search_params)
  matches = flann.knnMatch(des1,des2,k=2)

  pts1 = [] #feature points of image1
  pts2 = []  #feature point of image2

  # ratio test as per Lowe's paper
  for i,(m,n) in enumerate(matches):
    if m.distance < 0.60*n.distance:
        pts2.append(kp2[m.trainIdx].pt)
        pts1.append(kp1[m.queryIdx].pt)

  # Now we have the list of best matches from both the images. Let's find the Fundamental Matrix.
  pts1 = np.int32(pts1)
  pts2 = np.int32(pts2)
  F, mask = cv.findFundamentalMat(pts1,pts2,cv.FM_LMEDS)
  print("Fundamental_matrix:","\n",F)

  # select inlier points
  pts1 = pts1[mask.ravel()==1]
  pts2 = pts2[mask.ravel()==1]


  # Function to draw corner points and line connecting them
  def drawlines(img1,img2,lines,pts1,pts2):
    ##''' img1 - image on which we draw the epilines for the points in img2 lines - corresponding epilines '''
    r,c = img1.shape
    img1 = cv.cvtColor(img1,cv.COLOR_GRAY2BGR)
    img2 = cv.cvtColor(img2,cv.COLOR_GRAY2BGR)
    for r,pt1,pt2 in zip(lines,pts1,pts2):
      color = tuple(np.random.randint(0,255,3).tolist())
      x0,y0 = map(int, [0, -r[2]/r[1] ])
      x1,y1 = map(int, [c, -(r[2]+r[0]*c)/r[1] ])
      img1 = cv.line(img1, (x0,y0), (x1,y1), color,1)
      img1 = cv.circle(img1,tuple(pt1),5,color,-1)
      img2 = cv.circle(img2,tuple(pt2),5,color,-1)
    return img1,img2


  # draw epilines corresponding to the points in image 2 and
  # draw epilines on image1 based on feature points in image2
  lines1 = cv.computeCorrespondEpilines(pts2.reshape(-1,1,2), 2,F)
  lines1 = lines1.reshape(-1,3)
  img5,img6 = drawlines(img1,img2,lines1,pts1,pts2)
  # draw epilines on image2 based on feature points in image1
  lines2 = cv.computeCorrespondEpilines(pts1.reshape(-1,1,2), 1,F)
  lines2 = lines2.reshape(-1,3)
  img3,img4 = drawlines(img2,img1,lines2,pts2,pts1)

  plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
  plt.subplot(121),plt.title('image1 feature point and epilines'),plt.imshow(img5)
  plt.subplot(122),plt.title('image1 feature point and epilines'),plt.imshow(img3)
  plt.show()


  # calculate essential matrix, rotational and translation matrix for two image planes
  # K1: Camera matrix for the first image.
  # K2: Camera matrix for the second image.
  # R: Rotation matrix between the cameras.
  # t1: Translation vector between the cameras.
  # baseline: distance between two cameras centers.

  # Essential matrix
  E = K1.T @ F @ K2
  print("Essential_matrix(E):","\n",E)
  # Perform SVD on the essential matrix
  U, S, VT = np.linalg.svd(E)

  # Enforce the smallest singular value to be close to zero
  S[2] = 0

  # Recover rotation matrix from SVD components
  W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
  R = U @ W @ VT.T

  # There are two possible solutions for translation due to depth ambiguity
  t1 = U[:, 2]  # first solution
  t2 = -U[:, 2]  # second solution (opposite direction)

  #print E , R, t1 matrix
  print("Rotation_matrix (R):")
  # R= np.reshape(R, (3, 3))
  R = np.array(R)
  print(R)
  print("\nTranslation_Vector (t1):")
  print(t1)
  if t1.shape != (3, 1):
    # print("t1_reshaped:",t1)
    t1 = np.reshape(t1, (3, 1))  # Reshape to (3x1)
  K1 = np.array(K1)
  print("K1_matrix",K1)
  K2 = np.reshape(K2, (3, 3))
  print("K2_matrix",K2)

  #calculating homegraphy matrix between image1 and image2
  imageSize = img1.shape[:2]
  # calculating homography matrix to rectify the image_set
  _, H1, H2 = cv.stereoRectifyUncalibrated(pts1, pts2, F, (1920, 1080))

  #visulaze the results
  print("Homography Matrix H1:", H1)
  print("Homography Matrix H2:",H2)


  # rectification tranformation map for both images
  image_size = img1.shape[:2]  # Extract width and height
  dist_coeffs=0

  # Rectify the image
  rectified_image1 = cv.warpPerspective(img1, H1, (1920, 1080))
  rectified_image2 = cv.warpPerspective(img2, H2, (1920, 1080))

  #visulaze the results
  plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
  plt.subplot(121),plt.title('rectified_image1'),plt.imshow(rectified_image1)
  plt.subplot(122),plt.title('rectified_image2'),plt.imshow(rectified_image2)
  plt.show()


  # Draw eplines on rectified image_set
  # draw epilines on image1 based on points in image2
  lines1 = cv.computeCorrespondEpilines(pts2.reshape(-1,1,2), 2,F)
  lines1 = lines1.reshape(-1,3)
  img5,img6 = drawlines(rectified_image1,rectified_image2,lines1,pts1,pts2)
  # draw epilines on image2 based on points in image1
  lines2 = cv.computeCorrespondEpilines(pts1.reshape(-1,1,2), 1,F)
  lines2 = lines2.reshape(-1,3)
  img3,img4 = drawlines(rectified_image2,rectified_image1,lines2,pts2,pts1)

  plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
  plt.subplot(121),plt.imshow(img5)
  plt.subplot(122),plt.imshow(img3)
  plt.show()

  #finding feature points in rectified images
  img1_rectified = rectified_image1
  img2_rectified = rectified_image2
  # finding feature points for rectified image
  sift = cv.SIFT_create()

  # find the keypoints and descriptors with SIFT
  kp1, des1 = sift.detectAndCompute(img1_rectified,None)
  kp2, des2 = sift.detectAndCompute(img2_rectified,None)

  # FLANN parameters
  FLANN_INDEX_KDTREE = 1
  index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
  search_params = dict(checks=50)

  flann = cv.FlannBasedMatcher(index_params,search_params)
  matches = flann.knnMatch(des1,des2,k=2)

  r_pts1 = []
  r_pts2 = []

  # ratio test as per Lowe's paper
  for i,(m,n) in enumerate(matches):
    if m.distance < 0.45*n.distance:
        r_pts2.append(kp2[m.trainIdx].pt)
        r_pts1.append(kp1[m.queryIdx].pt)

  # Now we have the list of best matches from both the images. Let's find the Fundamental Matrix.
  r_pts1 = np.int32(pts1)
  r_pts2 = np.int32(pts2)
  F, mask = cv.findFundamentalMat(pts1,pts2,cv.FM_LMEDS)

  print("Fundamental_matrix for rectified Images:","\n",F)

  # We select only inlier points
  r_pts1 = pts1[mask.ravel()==1]
  r_pts2 = pts2[mask.ravel()==1]

  ####################

  # Find epilines corresponding to points in right image (second image) and
  # drawing its lines on left image
  lines1 = cv.computeCorrespondEpilines(pts2.reshape(-1,1,2), 2,F)
  lines1 = lines1.reshape(-1,3)
  img5,img6 = drawlines(img1_rectified, img2_rectified,lines1,pts1,pts2)

  # Find epilines corresponding to points in left image (first image) and
  # drawing its lines on right image
  lines2 = cv.computeCorrespondEpilines(pts1.reshape(-1,1,2), 1,F)
  lines2 = lines2.reshape(-1,3)
  img3,img4 = drawlines(img2_rectified, img1_rectified,lines1,pts1,pts2)

  plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
  plt.subplot(121),plt.imshow(img5)
  plt.subplot(122),plt.imshow(img3)
  plt.show()

  #calculate depth map,disparity map
  def compute_depth_image(image1, image2, K1, K2, R, t, baseline):

    # Calculate disparity map
    # numDisparities=96 # INPUT
    numDisparities=number = (ndisp // 16) * 16 # INPUT
    print("ndisp:",numDisparities)

    stereo = cv.StereoBM_create(numDisparities, blockSize=5)
    disparity = stereo.compute(image1, image2)

    plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
    plt.subplot(121),plt.title('disparity_gray'),plt.imshow(disparity, 'gray')
    plt.subplot(122),plt.title('disparity_hot'),plt.imshow(disparity, 'hot')
    plt.show()

    # Rescale disparity map (assuming maximum disparity is known)

    min_val, max_val = 60, 280  # Adjust these values based on your expected disparity range   # INPUT

    disparity_scaled = cv.normalize(disparity, None, alpha=255, beta=0, norm_type=cv.NORM_MINMAX, dtype=cv.CV_8U)

    # Convert disparity map to color image using heat map conversion
    disparity_colored = cv.applyColorMap(disparity_scaled, cv.COLORMAP_JET)

    # Compute depth using the formula: depth = baseline * focal length / disparity
    f = K1[0, 0]  # Assuming focal length is the same for both cameras
    depth_image = baseline * f / (disparity + 1e-6)  # Add a small epsilon to avoid division by zero

    # Save disparity image (grayscale and color heatmap)
    cv.imwrite("disparity_grayscale.png", disparity_scaled)
    jet = cv.applyColorMap(disparity_scaled, cv.COLORMAP_JET)
    cv.imwrite("disparity_heatmap.png", jet)

    # Save depth image (grayscale and color heatmap)
    depth_image_scaled = cv.normalize(depth_image, None, alpha=255, beta=0, norm_type=cv.NORM_MINMAX, dtype=cv.CV_8U)
    cv.imwrite("depth_grayscale.png", depth_image_scaled)
    jet = cv.applyColorMap(depth_image_scaled, cv.COLORMAP_JET)
    cv.imwrite("depth_heatmap.png", jet)

    return depth_image, disparity_scaled, depth_image_scaled, disparity_colored

  depth_image, disparity_scaled, depth_image_scaled , disparity_colored = compute_depth_image(img1, img2, K1, K2, R, t1, baseline)

  # plot the disparity and depth images

  plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
  plt.subplot(121),plt.title('disparity_scaled_gray'),plt.imshow(disparity_scaled, 'gray')
  plt.subplot(122),plt.title('disparity_scaled_colored'),plt.imshow(disparity_colored)
  plt.show()

  plt.figure(figsize=(25 , 10))  # Adjust width and height as desired
  plt.subplot(121),plt.title('depth'),plt.imshow(depth_image, 'gray')
  plt.subplot(122),plt.title('depth_scaled'),plt.imshow(depth_image_scaled,'hot')
  plt.show()

# LOOP TO CALL PIPELINE FUNCTION FOR EACH IMAGE DATASET
i=0
for image in image_list:
    # print("length of image_list:",len(image_list))
    img1,img2 = image
    K1, K2 ,baseline, ndisp, vmin, vmax,dataset_no = calib_properties_list[i]
    # print("calib_data_set_list_no:",dataset_no)
    i+=1
    # call function
    print("Executing Image set:",i)
    pipeline_stereovision(img1,img2,K1,K2,baseline, ndisp,vmin,vmax)