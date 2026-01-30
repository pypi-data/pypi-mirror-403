import numpy as np
from skimage.color import rgb2gray
from skimage.exposure import match_histograms
from skimage.metrics import structural_similarity

def find_difference(img1, img2):
    assert img1.shape == img2.shape, "Please provide two images with the same format."

    gray_img1 = rgb2gray(img1)
    gray_img2 = rgb2gray(img2)

    (score, dif_image) = structural_similarity(gray_img1, gray_img2, full = True)
    print(f"Similarity of the images: {score}")

    normalized_dif_image = (np.min(dif_image)) / (np.max(dif_image) - np.min(dif_image))

    return normalized_dif_image

def transfer_histogram(img1, img2):
    corresponding_image = match_histograms(img1, img2, multichannel = True)
    return corresponding_image
