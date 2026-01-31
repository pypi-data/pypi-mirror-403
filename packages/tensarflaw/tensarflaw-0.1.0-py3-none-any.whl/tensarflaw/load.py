import sys

def main():
    """Главная функция, которая обрабатывает команды"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "load11":
            load11()
        elif command == "load12":
            load12()
        elif command == "load31":
            load31()
        elif command == "load32":
            load32()
        elif command == "load41":
            load41()
        elif command == "load42":
            load42()
        elif command == "load51":
            load51()
        elif command == "load52":
            load52()
        else:
            print(f"Неизвестная команда: {command}")
            print_help()
    else:
        print_help()

def print_help():
    """Показать справку по командам"""
    help_text = """
Доступные команды:
    tensarflaw load11 - Вывести код для анализа файлов (часть 1)
    tensarflaw load12 - Вывести код для анализа файлов (часть 2)
    tensarflaw load31 - Вывести код для создания модели (часть 1)
    tensarflaw load32 - Вывести код для создания модели (часть 2)
    tensarflaw load41 - Вывести код для тестирования модели (часть 1)
    tensarflaw load42 - Вывести код для тестирования модели (часть 2)
    tensarflaw load51 - Вывести код для классификации изображений (часть 1)
    tensarflaw load52 - Вывести код для классификации изображений (часть 2)
    """
    print(help_text)

def load11():
    code = '''import os
import struct

# Запрашиваем путь к папке у пользователя
folder_path = input("Введите путь до анализируемой папки: ").strip()

# Словарь сигнатур для определения типа файла
signatures = {
    b"\\xff\\xd8\\xff": "JPEG",
    b"\\x89PNG\\r\\n\\x1a\\n": "PNG",
    b"BM": "BMP",
    b"GIF87a": "GIF87a",
    b"GIF89a": "GIF89a",
    b"II*\\x00": "TIFF",
    b"MM\\x00*": "TIFF",
    b"RIFF": "WEBP",
}

# Поддерживаемые расширения
extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

# Счетчик файлов
file_count = 0

print(f"\\nАнализ папки: {folder_path}")
print("-" * 50)'''
    print(code)

def load12():
    code = '''# Рекурсивный обход всех папок и подпапок
for root, dirs, files in os.walk(folder_path):
    for filename in files:
        # Проверяем расширение файла
        if os.path.splitext(filename)[1].lower() in extensions:
            file_path = os.path.join(root, filename)

            # Определяем тип файла по сигнатуре
            file_type = "Unknown"
            try:
                with open(file_path, "rb") as f:
                    header = f.read(12)

                for sig, ftype in signatures.items():
                    if header.startswith(sig):
                        file_type = ftype
                        break
            except:
                file_type = "Error"

            print(f"Файл: {filename}, Тип файла: {file_type}")
            file_count += 1

# Вывод общего количества файлов
print("-" * 50)
print(f"\\nОбщее количество проанализированных файлов: {file_count}")'''
    print(code)

def load31():
    code = '''import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt
import os

# Указание пути до папки с датасетом
data_dir = r"C:\\Users\\Miha\\Desktop\\ModulB1\\dataset"

# Параметры изображений и batch size
img_height = 180
img_width = 180
batch_size = 32

# Создание набора данных для обучения
train_ds = tf.keras.utils.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size,
)

# Создание набора данных для валидации
val_ds = tf.keras.utils.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size,
)

# Извлечение имен классов
class_names = train_ds.class_names
print("Классы в датасете:", class_names)

# Кэширование данных для оптимальной производительности
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# Определение количества классов
num_classes = len(class_names)

# Создание модели нейронной сети
model = keras.Sequential(
    [
        # Масштабирование значений пикселей к диапазону [0, 1]
        layers.Rescaling(1.0 / 255, input_shape=(img_height, img_width, 3)),
        # Аугментация данных
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.2),
        # Первая пара сверточный + пулинговый слои
        layers.Conv2D(16, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(),
        # Вторая пара сверточный + пулинговый слои
        layers.Conv2D(32, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(),
        # Третья пара сверточный + пулинговый слои
        layers.Conv2D(64, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(),
        # Регуляризация и преобразование в 1D
        layers.Dropout(0.2),
        layers.Flatten(),
        # Полносвязный слой
        layers.Dense(128, activation="relu"),
        # Выходной слой
        layers.Dense(num_classes),
    ]
)'''
    print(code)

def load32():
    code = '''# Компиляция модели
model.compile(
    optimizer="adam",
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=["accuracy"],
)

# Обучение модели
epochs = 40
history = model.fit(train_ds, validation_data=val_ds, epochs=epochs)

# Извлечение данных для визуализации
acc = history.history["accuracy"]
val_acc = history.history["val_accuracy"]
loss = history.history["loss"]
val_loss = history.history["val_loss"]

# Создание диапазона эпох
epochs_range = range(epochs)

# Создание графиков
plt.figure(figsize=(8, 8))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label="Точность обучения")
plt.plot(epochs_range, val_acc, label="Точность валидации")
plt.legend(loc="lower right")
plt.title("Точность тренировки и валидации")

plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label="Ошибка обучения")
plt.plot(epochs_range, val_loss, label="Ошибка валидации")
plt.legend(loc="upper right")
plt.title("Ошибка тренировки и валидации")

plt.show()

# Сохранение модели
model.save("modul_B_3.hdf5")
print("Модель успешно сохранена в формате HDF5 как 'modul_B_3.hdf5'")'''
    print(code)

def load41():
    code = '''import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

test_dir = r"C:\\Users\\Miha\\Desktop\\ModulB1"
img_height, img_width = 180, 180
model = load_model("modul_B_3.hdf5")
class_names = [
    "cows",
    "pigs",
    ]
class_counts = {class_name: 0 for class_name in class_names}

files = [f for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]'''
    print(code)

def load42():
    code = '''for img_name in files:
    img_path = os.path.join(test_dir, img_name)
    img = image.load_img(img_path, target_size=(img_height, img_width))
    img_array = np.expand_dims(image.img_to_array(img), axis=0)

    predictions = model.predict(img_array, verbose=0)
    score = tf.nn.softmax(predictions[0])

    class_index = np.argmax(score)
    class_name = class_names[class_index]
    confidence = 100 * np.max(score)

    class_counts[class_name] += 1
    print(
        f"Изображение '{os.path.relpath(img_path, test_dir)}' - класс '{class_name}' ({confidence:.2f}%)"
    )

print("Изображение '{}' - класс '{}' ({:.2f}%)".format(
    os.path.relpath(img_path, test_dir), 
    class_name, 
    confidence
))'''
    print(code)

def load51():
    code = '''import os
import shutil
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Пути
source_path = r"C:\\....uuuu"
target_path = r"Proverka_5_test"

# Классы и загрузка модели
classes = ["chicken", "cows", "geese", "goats", "horses", "pigs", "rabbits", "sheep"]
model = load_model("modul_B_3.h5")

# Фиксированный размер изображения
target_size = (180, 180)

# Создание подпапок
for class_name in classes:
    os.makedirs(os.path.join(target_path, class_name), exist_ok=True)'''
    print(code)

def load52():
    code = '''# Обработка изображений
for filename in os.listdir(source_path):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        img_path = os.path.join(source_path, filename)

        try:
            # Загрузка и предобработка изображения с размером 180x180
            img = image.load_img(img_path, target_size=target_size)
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)

            # Предсказание
            prediction = model.predict(img_array, verbose=0)
            class_idx = np.argmax(prediction)
            predicted_class = classes[class_idx]

            # Перемещение файла
            dest_path = os.path.join(target_path, predicted_class, filename)
            shutil.move(img_path, dest_path)

            # Вывод информации
            print(f"{filename} – перемещен в: {predicted_class}")

        except Exception as e:
            print(f"Ошибка при обработке {filename}: {e}")

print("\\nОбработка завершена!")'''
    print(code)