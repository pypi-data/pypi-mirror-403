from matplotlib import pyplot as plt

def plot_image(image):
    plt.imshow(image)
    plt.axis("off")
    plt.show()

def plot_result(*args):
    num_images = len(args)

    fig, axis = plt.subplots(nrows = 1, ncols = num_images, figsize=(5 * num_images, 5))
    names_l = ["Image {}".format(i) for i in range(1, num_images)]
    names_l.append("Result")

    for ax, name, img in zip(axis, names_l, args):
        ax.set_title(name)
        ax.imshow(img)
        ax.axis("off")

    fig.tight_layout()
    plt.show()

def plot_histogram(image):
    plt.hist(image.ravel(), bins=256, color='orange', )
    plt.hist(image[:, :, 0].ravel(), bins=256, color='red', alpha=0.5)
    plt.hist(image[:, :, 1].ravel(), bins=256, color='Green', alpha=0.5)
    plt.hist(image[:, :, 2].ravel(), bins=256, color='Blue', alpha=0.5)
    plt.xlabel('Intensity Value')
    plt.ylabel('Count')
    plt.legend(['Total', 'Red_Channel', 'Green_Channel', 'Blue_Channel'])
    plt.show()
