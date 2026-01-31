import cv2


def resize_image(image: str, percentual: int):
    src = cv2.imread(image, cv2.IMREAD_UNCHANGED)

    # calculate the percent of original dimensions
    width = int(src.shape[1] * percentual / 100)
    height = int(src.shape[0] * percentual / 100)

    # dsize
    dsize = (width, height)

    # resize image
    output = cv2.resize(src, dsize)
    cv2.imwrite(image, output)
