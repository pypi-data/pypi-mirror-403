import os
import hashlib
from collections import Counter, defaultdict

class DirectoryAnalyzer:

    def __init__(self, path):
        self.path = path #шляї
        self.files_count = 0 #кількість файлів
        self.dirs_count = 0 #кількість папок
        
        self.ext_stats = Counter() #розширення

        self.file_sizes = [] #розмфр файлів

        self.duplicates = defaultdict(list) #слоник дублів, дефдікт бо не викликає помилку коли звертатитись до ключа якого не існує


    def analyze_directory(self):

        #проходимось по файлам та папкам
        for root, dirs, files in os.walk(self.path):
            self.dirs_count += len(dirs)

            for file in files:
                file_path = os.path.join(root, file)

                try:
                    #намагаємося проаналізувати обрану дір
                    size = os.path.getsize(file_path)
                    self.files_count += 1
                    
                    ext = os.path.splitext(file)[1].lower() #спліт текст повкертає (назва файл, розширення) тому [1] берем розширення файлу
                    self.ext_stats[ext] += size #додаємо розмір файлу по кожному розширенню
                    
                    self.file_sizes.append((file_path, size))

                    file_hash = self._get_file_hash(file_path) #шукаємо хеш файлів для знаходження дублікатів
                    self.duplicates[file_hash].append(file_path) #додаємо дублікати

                except (OSError, PermissionError):
                    continue
                    #очікуємо помилку доступу

    def _get_file_hash(self, file_path):
        hasher = hashlib.md5()

        with open(file_path, 'rb') as f:

            chunk = f.read(4096) #читаємо перший блок 4096 байт (4 КБ) з файлу

            while chunk:
                hasher.update(chunk) #додаємо поточний блок до загального хешу
                chunk = f.read(4096) #читаємо наступний блок 4 КБ

        return hasher.hexdigest() #повертаємо фінальний символьний хеш


    def get_top_files(self, n=10):
        return sorted(self.file_sizes, key=lambda x: x[1], reverse=True)[:n]
        #йдемо по розмірах файлів(key=lambda x: x[1]) сортуємо від більшого(реверс тру) та виводимо все до н

    def find_duplicates(self):
        duplicates = {} #словник ток з тими хешами де більше одного файлу

        for hash_val, file_list in self.duplicates.items():
            if len(file_list) > 1: # більше одного файлу
                duplicates[hash_val] = file_list # додаємо до результату

        return duplicates

    def generate_report(self):
        report = []

        report.append(f"Файлів: {self.files_count}, Папок: {self.dirs_count}")
        report.append("Розподіл за розширеннями: ")

        for ext, size in sorted(self.ext_stats.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {ext}: {size}")

        report.append("\nТоп-10 найбільших файлів:")

        for path, size in self.get_top_files():
            report.append(f"  {size} байт: {path}")

        dups = self.find_duplicates()

        if dups:
            report.append("\nДублікати:")

            for hash_val, paths in dups.items():
                report.append(f"  Група: {paths}")

        else:
            report.append("\nДублікатів не знайдено.")

        return "\n".join(report)


