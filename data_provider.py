from config import *
import tensorflow as tf
from sklearn.model_selection import train_test_split

# Set image and label paths
image_paths = glob.glob(IMAGES_PATH + '*.png')
label_paths = [LABELS_PATH + path.split('/')[-1].split('.')[0] + '.png' for path in image_paths]

# Define image size
IMAGE_SIZE = (INPUT_HEIGHT, INPUT_WIDTH)

# Function to convert RGB labels to class indices
def convert_rgb_to_class(rgb_label):
    int_label = tf.zeros((rgb_label.shape[0], rgb_label.shape[1]), dtype=tf.int32)
    for class_name, color in COLOR_MAP.items():
        class_idx = list(COLOR_MAP.keys()).index(class_name)
        mask = tf.reduce_all(tf.equal(rgb_label, color), axis=-1)
        int_label = tf.where(mask, class_idx, int_label)
    return int_label


def load_and_preprocess_data(image_path, label_path):

    image = tf.io.read_file(image_path)
    label = tf.io.read_file(label_path)

    image = tf.image.decode_png(image, channels=3)
    label = tf.image.decode_png(label, channels=3)

    image = tf.cast(image, dtype=tf.float32)
    label = tf.cast(label, dtype=tf.float32)

    image = tf.image.resize(image, IMAGE_SIZE)
    label = tf.image.resize(label, IMAGE_SIZE, method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

    image = image / 255.0

    label = convert_rgb_to_class(label)
    
    label = tf.one_hot(label, depth=NUMBER_OF_CLASSES)

    return image, label


# Function to perform data augmentation
def data_augmentation(image, label):
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_flip_up_down(image)
    image = tf.image.random_brightness(image, 0.05)
    image = tf.image.random_contrast(image, 0.7, 1.7)
    image = tf.clip_by_value(image, 0, 255)
    image = tf.image.random_saturation(image, lower=0.8, upper=1.2)
    image = tf.image.random_brightness(image, max_delta=0.05)
    image = tf.image.random_contrast(image, lower=0.7, upper=1.3)
    return image, label

# Split the data into training and testing sets (85/15 ratio)
train_image_paths, test_image_paths, train_label_paths, test_label_paths = train_test_split(
    image_paths, label_paths, test_size=0.15, random_state=42
)

# Create training dataset
train_dataset = tf.data.Dataset.from_tensor_slices((train_image_paths, train_label_paths))
train_dataset = train_dataset.map(load_and_preprocess_data, num_parallel_calls=tf.data.experimental.AUTOTUNE)
train_dataset = train_dataset.map(data_augmentation, num_parallel_calls=tf.data.experimental.AUTOTUNE)
train_dataset = train_dataset.shuffle(buffer_size=100).batch(BATCH_SIZE).prefetch(buffer_size=tf.data.experimental.AUTOTUNE)

# Create testing dataset
test_dataset = tf.data.Dataset.from_tensor_slices((test_image_paths, test_label_paths))
test_dataset = test_dataset.map(load_and_preprocess_data, num_parallel_calls=tf.data.experimental.AUTOTUNE)
test_dataset = test_dataset.batch(BATCH_SIZE).prefetch(buffer_size=tf.data.experimental.AUTOTUNE)





color_lookup_bgr = np.zeros((len(COLOR_MAP), 3), dtype=np.uint8)
for idx, (class_name, color) in enumerate(COLOR_MAP.items()):
    # Convert RGB color to BGR for OpenCV
    color_bgr = [color[2], color[1], color[0]]
    color_lookup_bgr[idx] = np.array(color_bgr, dtype=np.uint8)

def inspect_dataset(dataset, num_samples=20):
    """Inspect a few samples from the dataset to ensure they are correct."""
    for i, (image, label) in enumerate(dataset.take(num_samples)):

        image_np = image[0].numpy()
        label_np = label[0].numpy()
        

        if label_np.ndim > 2:
            label_indices = np.argmax(label_np, axis=-1)
        else:
            label_indices = label_np

        colored_label = color_lookup_bgr[label_indices]

        image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        
        cv2.imshow(f'Image {i + 1}', image_np)
        cv2.imshow(f'Label {i + 1}', colored_label)
        
        cv2.waitKey(0) 
        
        cv2.destroyAllWindows()

# inspect_dataset(train_dataset)