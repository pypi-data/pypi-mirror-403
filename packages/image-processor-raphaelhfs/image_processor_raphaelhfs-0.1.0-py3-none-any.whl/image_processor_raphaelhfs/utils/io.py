from skimage.io import imread, imsave

def read_image(file_path: str, is_gray: bool = False):
    image_data = imread(file_path, as_gray=is_gray)
    return image_data

def save_image(file_path: str, image_data):
    imsave(file_path, image_data)
