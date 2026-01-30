import hashlib
import os
import sqlite3 as sql
from multiprocessing import Pool
from typing import Iterable, Tuple, List
from skimage.feature import blob_log
from math import sqrt
import numpy as np
from IPython.core.display import clear_output
from numba import njit
from skimage import io


def get_image_blobs(image: np.ndarray,
                    md5: str,
                    channel: str,
                    min_sigma: float,
                    max_sigma: float,
                    threshold: float) -> List[Tuple]:
    """
    Function to extract blobs from an image
    :param image: The image to extract the blobs from
    :param md5: The md5 hash of the image
    :param channel: The channel of the image
    :param min_sigma: The minimum sigma to use
    :param max_sigma: The maximum sigma to use
    :param threshold: The threshold to use
    :return: The detected blobs
    """
    blobs = blob_log(image, min_sigma=min_sigma, max_sigma=max_sigma, threshold=threshold)
    blobs[:, 2] = blobs[:, 2] * sqrt(2)
    return [(md5,
             channel,
             min_sigma,
             max_sigma,
             threshold,
             p[0],
             p[1]) for p in blobs]

def calculate_image_id(path: str) -> str:
    """
    Function to calculate the md5 hash sum of the image described by path
    :param path: The URL of the image
    :return: The md5 hash sum as hex
    """
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_training_images_from_folder(path: str,
                                       dest: str,
                                       subimage_shape: Tuple[int, int],
                                       db_path: str,
                                       split_channels: bool = True,
                                       include_main: bool = False,
                                       use_only_manual: bool = False):
    """
    Function to create the training images from a given folder

    :param path: Path containing the images
    :param dest: Folder to save the created images to
    :param db_path: Path leading to the database
    :param subimage_shape: The shape of the sub images to create
    :param split_channels: If false, the image will only
    :param include_main: If false, the main channel will be ignored
    :param use_only_manual: If true, only the manually modified images will be processed
    :return: None
    """
    # Check if label path exists
    os.makedirs(dest, exist_ok=True)
    for root, dirs, files in os.walk(path):
        if not files:
            continue
        non_existing_files = check_if_images_already_exist(files, dest, subimage_shape)
        non_existing_files_with_path = [os.path.join(root, x) for x in non_existing_files]
        analysed_files = check_if_images_are_in_database(non_existing_files_with_path, db_path)
        manually_edited_files = filter_for_manual_images(analysed_files, db_path, use_only_manual)
        if not manually_edited_files:
            continue
        # Prepare files for processing
        data = [(x, subimage_shape,
                 dest, False, "", split_channels, include_main) for x in manually_edited_files]
        with Pool(16) as p:
            res = p.starmap(process_image, data)
            for _ in res:
                clear_output(wait=True)


def check_if_images_already_exist(files: List[str], dest: str,
                                  subimage_shape: Tuple[int, int],
                                  is_label: bool = False, multiple_channels: bool = True) -> List[str]:
    """
    Function to check if the given images already exist

    :param files: List of files that need to be checked
    :param dest: The folder that should be checked
    :param subimage_shape: The shape of created sub-images
    :param is_label: Should label or training images be checked
    :param multiple_channels: Were the original images split into multiple images?
    :return: List of files that need to be created
    """
    cfiles = []
    for file in files:
        # Create path
        f_name = f"{os.path.splitext(file)[0]}_{'red_' if multiple_channels else ''}{subimage_shape[0]}" \
                 f"-{subimage_shape[1]}_00{'_label' if is_label else''}.png"
        # Check if file already exists
        if not os.path.isfile(os.path.join(dest, f_name)):
            cfiles.append(file)
        else:
            print(f"Files for {file} already exist!")
            clear_output(wait=True)
    return cfiles


def check_if_images_are_in_database(imgs: List[str], db_path: str) -> List[str]:
    """
    FUnction to check if data is stored for the given image

    :param imgs: List of image paths
    :param db_path: Path leading to the database
    :return: List of MD5 hashes for images that have stored data
    """
    check = []
    for img in imgs:
        if check_if_image_is_in_database(img, db_path):
            check.append(img)
    return check


def check_if_image_is_in_database(img_path: str, db_path: str) -> bool:
    """
    FUnction to check if data for the given image is stored in the database

    :param img_hash: MD5 hash of the image
    :param db_path: Path leading to the database
    :return: If true, data is stored
    """
    # Connect to the database
    db = sql.connect(db_path)
    crs = db.cursor()
    # Calculate img hash
    img_hash = calculate_image_id(img_path)
    dbe = crs.execute("SELECT analysed FROM images WHERE md5=?", (img_hash,)).fetchall()
    if dbe:
        return bool(dbe[0][0])
    else:
        return False



def process_image(file_path: str, subimage_shape: Tuple[int, int],
                  dest: str, is_label: bool = False, db_path: str = "",
                  separate_channels: bool = False,
                  include_main: bool = False,
                  main_index: int = 2) -> str:
    """
    Function to process a given image to use for machine learning

    :param file_path: The path leading to the file to load. Is ignored if is_label is True
    :param subimage_shape: The shape of the created sub-images
    :param dest: The folder to save the resulting images in
    :param is_label: If true, the function tries to create a label from the given database
    :param db_path: Path leading to the database
    :param separate_channels: If true, the channels of the image will be saved as individual files
    :param include_main: If false, the main channel will be ignored
    :param main_index: The index of the main channel
    :return: The md5 hash of the original image
    """
    # Load the image
    if is_label:
        md5 = calculate_image_id(file_path)
        img = get_label_for_image(md5, db_path)
    else:
        img = io.imread(file_path)
    # Get the subimages
    sf_name = os.path.splitext(file_path)[0].split(os.path.sep)[-1]
    subs = extract_subimages(img, subimage_shape)
    for sind, sub in enumerate(subs):
        if not separate_channels:
            # Create name for the given sub image
            name = f"{sf_name}_{subimage_shape[0]}-{subimage_shape[1]}_{sind:02d}{'_label.png' if is_label else '.png'}"
            # Create a file path
            sfpath = os.path.join(dest, name)
            # Check if sub image already exists
            io.imsave(sfpath, sub.astype("uint8"), check_contrast=False)
        else:
            channels = ("red", "green", "blue", "black", "white")
            for channel_index in range(sub.shape[2]):
                if not include_main and channel_index == main_index:
                    continue
                # Create name for the given sub image
                name = f"{sf_name}_{channels[channel_index]}_{subimage_shape[0]}-" \
                       f"{subimage_shape[1]}_{sind:02d}{'_label.png' if is_label else '.png'}"
                # Create a file path
                sfpath = os.path.join(dest, name)
                # Check if sub image already exists
                io.imsave(sfpath, sub[..., channel_index].astype("uint8"), check_contrast=False)
    return f"Created training images for:\t{sf_name}" if not is_label else f"Created labels for:\t{sf_name}"


def create_label_data_for_images(path: str,
                                 label_path: str,
                                 subimage_shape: Tuple[int, int],
                                 db_path: str,
                                 split_channels: bool = True,
                                 include_main: bool = False,
                                 use_only_manual: bool = False) -> None:
    """
    Function to get the label data for all images at the given path

    :param path: The path to the folder containing the images
    :param label_path: The folder where the label images should be saved
    :param subimage_shape: The shape of the subimages to create
    :param db_path: Path leading to the database
    :param split_channels: If true, the channels of the image will be saved as individual files
    :param include_main: If false, the main channel will be ignored
    :param use_only_manual: If true, only the manually modified images will be processed
    :return: A list containing lists of all labels for each channel
    """
    # Check if label path exists
    os.makedirs(label_path, exist_ok=True)
    for root, dirs, files in os.walk(path):
        files = check_if_images_already_exist(files, label_path, subimage_shape, True)
        files = [os.path.join(root, x) for x in files]
        files = check_if_images_are_in_database(files, db_path)
        files = filter_for_manual_images(files, db_path, use_only_manual)
        if not files:
            continue
        # Prepare files for processing
        data = [(x, subimage_shape, label_path, True,
                 db_path, split_channels, include_main) for x in files]
        with Pool(16) as p:
            res = p.starmap(process_image, data)
            for _ in res:
                clear_output(wait=True)

def filter_for_manual_images(files, db_path, use_only_manual) -> List[str]:
    """
    Method to filter out files that are not manually modified

    :param files: List of all file paths
    :param db_path: Path to the database
    :param use_only_manual: If True, only the manual images will be returned. Otherwise, all images will be returned
    :return: List of checked file paths
    """
    # Return if the files are not supposed to be checked
    if not use_only_manual:
        return files
    # Connect to the database
    db = sql.connect(db_path)
    crs = db.cursor()
    # Iterate over the file list
    mfiles = []
    for file in files:
        img_hash = calculate_image_id(file)
        # Check if the file was modified
        if crs.execute("SELECT modified FROM images WHERE md5=?",
                       (img_hash,)).fetchall()[0][0]:
            mfiles.append(file)
    return mfiles


@njit
def extract_subimages(img: np.ndarray, subimage_shape: Tuple[int, int]) -> List[np.ndarray]:
    """
    Function to extract subimages from a given image

    :param img: The image to extract the subimages from
    :param subimage_shape: The shape of each subimage
    :return: List of all extracted subimages
    """
    # Get the number of subimages for each axis
    svert, shor = get_number_of_subimages_per_dimension(img.shape, subimage_shape)
    sub_images = []
    for y in range(svert):
        for x in range(shor):
            extract = img[y * subimage_shape[0]: (y + 1) * subimage_shape[0],
                          x * subimage_shape[1]: (x + 1) * subimage_shape[1]]
            tile = np.zeros(shape=(subimage_shape[0], subimage_shape[1], extract.shape[2]))
            tile[0: extract.shape[0], 0: extract.shape[1]] = extract
            sub_images.append(tile)
    return sub_images


@njit
def get_number_of_subimages_per_dimension(img_shape: Tuple[int, int],
                                          sub_shape: Tuple[int, int]) -> Tuple[int, int]:
    """
    Function to get the number of sub-images per

    :param img_shape: The shape of the image
    :param sub_shape: The shape of the sub-images to extract
    :return: The vertical and horizontal sub-image count
    """
    hcheck = bool(img_shape[0] % sub_shape[0])
    wcheck = bool(img_shape[1] % sub_shape[1])
    # Get the number of tiles
    hcount = img_shape[0] // sub_shape[0] if not hcheck else img_shape[0] // sub_shape[0] + 1
    wcount = img_shape[1] // sub_shape[1] if not wcheck else img_shape[1] // sub_shape[1] + 1
    return hcount, wcount


@njit
def split_channels(img: np.ndarray) -> List[np.ndarray]:
    """
    Function to split the channels

    :param img: The image to split
    :return: List of all available channels
    """
    return [img[..., x] for x in range(img.shape[2])]


def get_label_for_image(img_hash: str, db_path: str) -> np.ndarray:
    """
    Function to get the label data for the given image

    :param img_hash: The md5 hash of the image
    :param dims: The dimensions of the given image
    :param db_path: The path leading to the database, where the label data is stored
    :return: The labels for each channel of the image
    """
    # Connect to database and create cursor
    db = sql.connect(db_path)
    crs = db.cursor()
    # Get the dimensions of the image
    dims = tuple(crs.execute("SELECT height, width FROM images WHERE md5=?", (img_hash,)).fetchall()[0])
    # Load the channel names of the given image
    channel_names = [x[0] for x in crs.execute("SELECT name FROM channels WHERE md5=?", (img_hash,)).fetchall()]
    binmap = np.zeros(shape=(dims[0], dims[1], len(channel_names)))
    # Fetch all associated ROI for each given channel
    for ind, channel in enumerate(channel_names):
        clear_output()
        print(f"Fetching label for: {img_hash} -> {channel}")
        cmap = np.zeros(shape=dims, dtype="uint8")
        # Fetch the roi
        rois = crs.execute("SELECT hash FROM roi WHERE image=? AND channel=?", (img_hash, channel)).fetchall()
        # Fetch each area
        for roi in rois:
            area = crs.execute("SELECT row, column_, width FROM points WHERE hash=?", roi).fetchall()
            imprint_area_into_array(area, cmap, 255)
        binmap[..., ind] = cmap
    return binmap


def imprint_area_into_array(area: Iterable[Tuple[int, int, int]], array: np.ndarray, ident: int) -> None:
    """
    Function to imprint the specified area into the specified area

    :param area: The run length encoced area to imprint
    :param array: The array to imprint into
    :param ident: The identifier to use for the imprint
    :return: None
    """
    # Get normalization factors
    for ar in area:
        array[ar[0], ar[1]: ar[1] + ar[2]] = ident
    # Check the surroundings of the area
    check_area_surroundings(area, array)

def check_area_surroundings(area: Iterable[Tuple[int, int, int]], array: np.ndarray) -> None:
    """
    Functions to check the surroundings of the given area to minimize overlap

    :param area: The area to check
    :param array: The array the area is located in
    :return: None
    """
    pass



