from skimage.transform import resize

def resize_image(image, ratio):
    assert 0 <= ratio <= 1, "Please provide a ratio between 0 and 1."

    height = round(image.shape[0] * ratio)
    width = round(image.shape[1] * ratio)
    resized_image = resize(image, (height, width), anti_aliasing = True)

    return resized_image
