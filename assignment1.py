# These are all the modules we'll be using later. Make sure you can import them
# before proceeding further.
from __future__ import print_function
from __future__ import division
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import tarfile
from IPython.display import display, Image
from scipy import ndimage
from sklearn.linear_model import LogisticRegression
from six.moves.urllib.request import urlretrieve
from six.moves import cPickle as pickle
from matplotlib.pyplot import imshow
from PIL import Image

url = 'http://yaroslavvb.com/upload/notMNIST/'


def maybe_download(filename, expected_bytes, force=False):
    """Download a file if not present, and make sure it's the right size."""
    if force or not os.path.exists(filename):
        filename, _ = urlretrieve(url + filename, filename)
    statinfo = os.stat(filename)
    if statinfo.st_size == expected_bytes:
        print('Found and verified', filename)
    else:
        raise Exception(
                'Failed to verify' + filename + '. Can you get to it with a browser?')
    return filename


train_filename = maybe_download('notMNIST_large.tar.gz', 247336696)
test_filename = maybe_download('notMNIST_small.tar.gz', 8458043)

num_classes = 10


def maybe_extract(filename, force=False):
    root = os.path.splitext(os.path.splitext(filename)[0])[0]  # remove .tar.gz
    if os.path.isdir(root) and not force:
        # You may override by setting force=True.
        print('%s already present - Skipping extraction of %s.' % (root, filename))
    else:
        print('Extracting data for %s. This may take a while. Please wait.' % root)
        tar = tarfile.open(filename)
        sys.stdout.flush()
        tar.extractall()
        tar.close()
    data_folders = [
        os.path.join(root, d) for d in sorted(os.listdir(root))
        if os.path.isdir(os.path.join(root, d))]
    if len(data_folders) != num_classes:
        raise Exception(
                'Expected %d folders, one per class. Found %d instead.' % (
                    num_classes, len(data_folders)))
    print(data_folders)
    return data_folders


train_folders = maybe_extract(train_filename)
test_folders = maybe_extract(test_filename)

# Problem 1
# images = os.listdir(train_folders[0])
# image_file = os.path.join(train_folders[0], images[0])
# print(image_file)
# pil_im = Image.open(image_file, mode="r")
# pil_im.show()
# myImage = Image(filename = image_file)
# display(myImage)

image_size = 28  # Pixel width and height.
pixel_depth = 255.0  # Number of levels per pixel.


def load_letter(folder, min_num_images):
    """Load the data for a single letter label."""
    image_files = os.listdir(folder)
    dataset = np.ndarray(shape=(len(image_files), image_size, image_size),
                         dtype=np.float32)
    image_index = 0
    print(folder)
    for image in os.listdir(folder):
        image_file = os.path.join(folder, image)
        try:
            image_data = (ndimage.imread(image_file).astype(float) -
                          pixel_depth / 2) / pixel_depth
            if image_data.shape != (image_size, image_size):
                raise Exception('Unexpected image shape: %s' % str(image_data.shape))
            dataset[image_index, :, :] = image_data
            image_index += 1
        except IOError as e:
            print('Could not read:', image_file, ':', e, '- it\'s ok, skipping.')

    num_images = image_index
    dataset = dataset[0:num_images, :, :]
    if num_images < min_num_images:
        raise Exception('Many fewer images than expected: %d < %d' %
                        (num_images, min_num_images))

    print('Full dataset tensor:', dataset.shape)
    print('Mean:', np.mean(dataset))
    print('Standard deviation:', np.std(dataset))
    return dataset


def maybe_pickle(data_folders, min_num_images_per_class, force=False):
    dataset_names = []
    for folder in data_folders:
        set_filename = folder + '.pickle'
        dataset_names.append(set_filename)
        if os.path.exists(set_filename) and not force:
            # You may override by setting force=True.
            print('%s already present - Skipping pickling.' % set_filename)
        else:
            print('Pickling %s.' % set_filename)
            dataset = load_letter(folder, min_num_images_per_class)
            try:
                with open(set_filename, 'wb') as f:
                    pickle.dump(dataset, f, pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                print('Unable to save data to', set_filename, ':', e)

    return dataset_names


train_datasets = maybe_pickle(train_folders, 45000)
test_datasets = maybe_pickle(test_folders, 1800)

# Problem 2
# Display a sample image
import matplotlib.cm as cm

print("Problem 2")
train_dataset_name = train_datasets[1]
print(train_dataset_name)
dataset = pickle.load(open(train_dataset_name, "rb"))
plt.imshow(dataset[1], cmap=cm.Greys_r)
plt.show()

# Problem 3
for trainset_name in train_datasets:
    trainset = pickle.load(open(trainset_name, "rb"))
    print('train set name: %s, number of samples: %d' % (trainset_name, trainset.shape[0]))


def make_arrays(nb_rows, img_size):
    if nb_rows:
        dataset = np.ndarray((nb_rows, img_size, img_size), dtype=np.float32)
        labels = np.ndarray(nb_rows, dtype=np.int32)
    else:
        dataset, labels = None, None
    return dataset, labels


def merge_datasets(pickle_files, train_size, valid_size=0):
    num_classes = len(pickle_files)
    valid_dataset, valid_labels = make_arrays(valid_size, image_size)
    train_dataset, train_labels = make_arrays(train_size, image_size)
    vsize_per_class = valid_size // num_classes
    tsize_per_class = train_size // num_classes

    start_v, start_t = 0, 0
    end_v, end_t = vsize_per_class, tsize_per_class
    end_l = vsize_per_class + tsize_per_class
    for label, pickle_file in enumerate(pickle_files):
        try:
            with open(pickle_file, 'rb') as f:
                letter_set = pickle.load(f)
                if valid_dataset is not None:
                    valid_letter = letter_set[:vsize_per_class, :, :]
                    valid_dataset[start_v:end_v, :, :] = valid_letter
                    valid_labels[start_v:end_v] = label
                    start_v += vsize_per_class
                    end_v += vsize_per_class

                train_letter = letter_set[vsize_per_class:end_l, :, :]
                train_dataset[start_t:end_t, :, :] = train_letter
                train_labels[start_t:end_t] = label
                start_t += tsize_per_class
                end_t += tsize_per_class
        except Exception as e:
            print('Unable to process data from', pickle_file, ':', e)
            raise

    return valid_dataset, valid_labels, train_dataset, train_labels


train_size = 100000
valid_size = 1000
test_size = 1000

valid_dataset, valid_labels, train_dataset, train_labels = merge_datasets(train_datasets, train_size, valid_size)
_, _, test_dataset, test_labels = merge_datasets(test_datasets, test_size)

print('Training:', train_dataset.shape, train_labels.shape)
print('Validation:', valid_dataset.shape, valid_labels.shape)
print('Testing:', test_dataset.shape, test_labels.shape)

np.random.seed(133)

def randomize(dataset, labels):
    permutation = np.random.permutation(labels.shape[0])
    shuffled_dataset = dataset[permutation, :, :]
    shuffled_labels = labels[permutation]
    return shuffled_dataset, shuffled_labels


train_dataset, train_labels = randomize(train_dataset, train_labels)
test_dataset, test_labels = randomize(test_dataset, test_labels)

# Problem 4
print("Train label #0 is %d" % train_labels[0])
plt.imshow(train_dataset[0], cmap=cm.Greys_r)
plt.show()
print("Test label #0 is %d" % test_labels[0])
plt.imshow(test_dataset[0], cmap=cm.Greys_r)
plt.show()

pickle_file = 'notMNIST.pickle'

try:
    f = open(pickle_file, 'wb')
    save = {
        'train_dataset': train_dataset,
        'train_labels': train_labels,
        'valid_dataset': valid_dataset,
        'valid_labels': valid_labels,
        'test_dataset': test_dataset,
        'test_labels': test_labels,
    }
    pickle.dump(save, f, pickle.HIGHEST_PROTOCOL)
    f.close()
except Exception as e:
    print('Unable to save data to', pickle_file, ':', e)
    raise

statinfo = os.stat(pickle_file)
print('Compressed pickle size:', statinfo.st_size)

'''
# Problem 5
dup = 0
# Optional: Remove duplicated data sets between train and validation
# sanitized_valid_dataset = np.empty((0, image_size, image_size), dtype=np.float32)
# sanitized_valid_labels = np.empty(0, dtype=np.int32)
for i, valid_data in enumerate(valid_dataset):
    matchFlag = False
    for j, train_data in enumerate(train_dataset):
        if valid_labels[i] == train_labels[j]:
            if np.array_equal(train_data, valid_data):
                matchFlag = True
                dup += 1
                break

    #if matchFlag is False:
        #sanitized_valid_dataset = np.vstack([sanitized_valid_dataset, [valid_data]])
        #sanitized_valid_labels = np.append(sanitized_valid_labels, valid_labels[i])

print("Problme 5:")
print("Duplicated images between train data set and validation data set: %d" % dup)
print("Duplicated percentage in terms of train data set: %f, in terms of validation data set: %f" %
      (dup / train_size, dup / valid_size))

# Do the same for test set
dup = 0
#sanitized_test_dataset_temp = np.empty((0, image_size, image_size), dtype=np.float32)
#sanitized_test_labels_temp = np.empty(0, dtype=np.int32)
for i, test_data in enumerate(test_dataset):
    matchFlag = False
    for j, train_data in enumerate(train_dataset):
        if test_labels[i] == train_labels[j]:
            if np.array_equal(train_data, test_data):
                matchFlag = True
                dup += 1
                break

    #if matchFlag is False:
        #sanitized_test_dataset_temp = np.vstack([sanitized_test_dataset_temp, [test_data]])
        #sanitized_test_labels_temp = np.append(sanitized_test_labels_temp, test_labels[i])

print("Duplicated images between train data set and test data set: %d" % dup)
print("Duplicated percentage in terms of train data set: %f, in terms of test data set: %f" %
      (dup / train_size, dup / valid_size))

# Finally further sanitize between validation data set and test data set
dup = 0
#sanitized_test_dataset = np.empty((0, image_size, image_size), dtype=np.float32)
#sanitized_test_labels = np.empty(0, dtype=np.int32)
for i, test_data in enumerate(test_dataset):
    matchFlag = False
    for j, valid_data in enumerate(valid_dataset):
        if test_labels[i] == valid_labels[j]:
            if np.array_equal(valid_data, test_data):
                matchFlag = True
                dup += 1
                break

    #if matchFlag is False:
        #sanitized_test_dataset = np.vstack([sanitized_valid_dataset, [test_data]])
        #sanitized_test_labels = np.append(sanitized_valid_labels, test_labels[i])

print("Duplicated images between valid data set and test data set: %d" % dup)
print("Duplicated percentage in terms of valid data set: %f, in terms of test data set: %f" %
      (dup / train_size, dup / valid_size))
'''

# Problem 6
# Use LogisicRegession from sklearn.linear_model to train 50/100/1000/5000 samples
from sklearn.linear_model import LogisticRegression
lr = LogisticRegression(C=1000.0, random_state=0)

train_runs = (50, 100, 1000, 5000)
test_dataset = test_dataset.reshape(len(test_dataset), 784)
for train_size in train_runs:
    print("train_size: %d" % train_size)
    train_dataset_run = train_dataset[:train_size].reshape(train_size, 784)
    train_labels_run = train_labels[:train_size]
    lr.fit(train_dataset_run, train_labels_run)
    results = lr.predict(test_dataset)
    match_set = (results == test_labels)
    print("Prediction accuracy: %f" % (np.sum(match_set) / len(test_dataset)))