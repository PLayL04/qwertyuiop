from dataclasses import dataclass
from tkinter import *
from tkinter import ttk, messagebox
import logging


# ЛОГИРОВАНИЕ
logging.basicConfig(
    filename="menu_errors.log",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


# ИСКЛЮЧЕНИЯ
class MenuError(Exception):
    pass


class ParseError(MenuError):
    pass


class TimeFormatError(ParseError):
    pass


class CostFormatError(ParseError):
    pass


# МОДЕЛЬ
@dataclass
class Time:
    hh: int
    mm: int

    def __post_init__(self):
        if not isinstance(self.hh, int) or not isinstance(self.mm, int):
            raise TimeFormatError("Часы и минуты должны быть целыми числами")
        if not (0 <= self.hh <= 23):
            raise TimeFormatError(f"Некорректный час: {self.hh}")
        if not (0 <= self.mm <= 59):
            raise TimeFormatError(f"Некорректные минуты: {self.mm}")

    def __str__(self):
        return f"{self.hh:02d}:{self.mm:02d}"


@dataclass
class Menu:
    name: str
    cost: float
    time: Time

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ParseError("Название блюда не может быть пустым")
        if not isinstance(self.cost, (int, float)):
            raise CostFormatError("Цена должна быть числом")
        if self.cost < 0:
            raise CostFormatError("Цена не может быть отрицательной")


class MenuParser:
    """Вспомогательный класс для разбора строк."""

    @staticmethod
    def get_name(line):
        first = line.find('"')
        last = line.rfind('"')

        if first == -1 or last == -1 or first == last:
            raise ParseError(f'Не найдено корректное название в кавычках: {line.strip()}')

        name = line[first + 1:last].strip()
        rest = line[last + 1:].strip()

        if not name:
            raise ParseError("Название блюда пустое")

        return name, rest

    @staticmethod
    def get_time(text):
        if ":" not in text:
            raise TimeFormatError(f"Некорректный формат времени: {text}")

        parts = text.split(":")
        if len(parts) != 2:
            raise TimeFormatError(f"Некорректный формат времени: {text}")

        try:
            hh = int(parts[0])
            mm = int(parts[1])
        except ValueError:
            raise TimeFormatError(f"Время должно содержать числа: {text}")

        return Time(hh, mm)

    @staticmethod
    def parse_line(line):
        line = line.strip()
        if not line:
            raise ParseError("Пустая строка")

        name, rest = MenuParser.get_name(line)
        parts = rest.split()

        if len(parts) != 2:
            raise ParseError(
                f"После названия должны идти цена и время. Получено: {rest}"
            )

        cost_str, time_str = parts

        try:
            cost = float(cost_str)
        except ValueError:
            raise CostFormatError(f"Некорректная цена: {cost_str}")

        time_obj = MenuParser.get_time(time_str)
        return Menu(name, cost, time_obj)


class MenuModel:
    """Модель приложения."""

    def __init__(self):
        self.menu_list = []

    def read_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return file.readlines()
        except FileNotFoundError:
            raise MenuError(f"Файл не найден: {filename}")
        except OSError as e:
            raise MenuError(f"Ошибка чтения файла: {e}")

    def load_from_file(self, filename):
        content = self.read_file(filename)
        self.menu_list = self.create_menu_list(content)

    def create_menu_list(self, content):
        menu_list = []
        for number, line in enumerate(content, start=1):
            try:
                dish = MenuParser.parse_line(line)
                menu_list.append(dish)
            except ParseError as e:
                logging.warning(
                    f"Строка {number} пропущена: {line.strip()} | Ошибка: {e}"
                )
        return menu_list

    def add_dish(self, name, cost_str, time_str):
        if not name.strip():
            raise ParseError("Название блюда не может быть пустым")

        try:
            cost = float(cost_str)
        except ValueError:
            raise CostFormatError("Цена должна быть числом")

        time_obj = MenuParser.get_time(time_str)
        new_dish = Menu(name.strip(), cost, time_obj)
        self.menu_list.append(new_dish)

    def delete_dish(self, index):
        if not (0 <= index < len(self.menu_list)):
            raise MenuError("Некорректный индекс блюда")
        del self.menu_list[index]

    def get_all(self):
        return self.menu_list


# ВИД
def create_window():
    root = Tk()
    root.title("MENU")
    root.geometry("600x400")
    return root



def create_main_frame(parent):
    frame = Frame(parent)
    frame.pack(fill=BOTH, expand=1)
    return frame



def create_table(parent):
    columns = ("name", "cost", "time")
    tree = ttk.Treeview(parent, columns=columns, show="headings")

    tree.heading("name", text="Название блюда")
    tree.heading("cost", text="Цена")
    tree.heading("time", text="Время приготовления")

    tree.column("name", width=250)
    tree.column("cost", width=100)
    tree.column("time", width=150)

    tree.pack(fill=BOTH, expand=1, padx=10, pady=10)
    return tree



def fill_table(tree, menu_list):
    for dish in menu_list:
        values = [dish.name, dish.cost, str(dish.time)]
        tree.insert("", END, values=values)



def refresh_table(tree, menu_list):
    for item in tree.get_children():
        tree.delete(item)
    fill_table(tree, menu_list)


def create_log_frame(parent):
    frame = Frame(parent)
    frame.pack(fill=BOTH, expand=0, padx=10, pady=5)

    Label(frame, text="Лог ошибок:").pack(anchor=W)

    text = Text(frame, height=8, wrap=WORD)
    text.pack(fill=BOTH, expand=1)

    return text


def load_log(text_widget):
    try:
        with open("menu_errors.log", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = "Лог пуст"

    text_widget.delete(1.0, END)
    text_widget.insert(END, content)


def create_button_frame(parent):
    frame = Frame(parent)
    frame.pack(fill=X, padx=10, pady=10)
    return frame



def create_add_button(parent, command):
    button = Button(parent, text="Добавить блюдо", command=command,
                    bg="lightgreen", width=20)
    button.pack(side=LEFT, padx=5)
    return button



def create_delete_button(parent, command):
    button = Button(parent, text="Удалить блюдо", command=command,
                    bg="lightcoral", width=20)
    button.pack(side=LEFT, padx=5)
    return button



def add_dish_dialog(parent, tree, model, size="300x250"):
    dialog = Toplevel(parent)
    dialog.title("Добавить блюдо")
    dialog.geometry(size)
    dialog.grab_set()

    Label(dialog, text="Название блюда:").pack(pady=5)
    name_entry = Entry(dialog, width=30)
    name_entry.pack(pady=5)

    Label(dialog, text="Цена:").pack(pady=5)
    cost_entry = Entry(dialog, width=30)
    cost_entry.pack(pady=5)

    Label(dialog, text="Время (ЧЧ:ММ):").pack(pady=5)
    time_entry = Entry(dialog, width=30)
    time_entry.pack(pady=5)

    def save_dish():
        try:
            model.add_dish(
                name_entry.get(),
                cost_entry.get(),
                time_entry.get()
            )
            refresh_table(tree, model.get_all())
            load_log(parent.log_widget)
            dialog.destroy()
        except MenuError as e:
            messagebox.showerror("Ошибка", str(e))

    Button(dialog, text="Сохранить", command=save_dish).pack(pady=10)
    Button(dialog, text="Отмена", command=dialog.destroy).pack(pady=5)



def delete_selected_dish(tree, model):
    selected = tree.selection()

    if not selected:
        messagebox.showwarning("Предупреждение", "Выберите блюдо для удаления")
        return

    try:
        indexes = sorted((tree.index(item) for item in selected), reverse=True)
        for index in indexes:
            model.delete_dish(index)
        refresh_table(tree, model.get_all())
        load_log(tree.master.master.log_widget)
    except MenuError as e:
        messagebox.showerror("Ошибка", str(e))



def setup_buttons(parent, tree, model, log_widget):
    button_frame = create_button_frame(parent)

    create_add_button(button_frame,
                      lambda: add_dish_dialog(parent, tree, model))
    create_delete_button(button_frame,
                         lambda: delete_selected_dish(tree, model))
    Button(button_frame, text="Обновить лог",
           command=lambda: load_log(log_widget),
           bg="lightblue", width=20).pack(side=LEFT, padx=5)


# ЗАПУСК ПРОГРАММЫ
def main():
    model = MenuModel()

    try:
        model.load_from_file("lab2_file")
    except MenuError as e:
        logging.warning(f"Ошибка загрузки файла: {e}")
        messagebox.showerror("Ошибка", str(e))

    root = create_window()
    main_frame = create_main_frame(root)
    tree = create_table(main_frame)

    log_widget = create_log_frame(root)
    root.log_widget = log_widget
    load_log(log_widget)

    fill_table(tree, model.get_all())
    setup_buttons(root, tree, model, log_widget)

    root.mainloop()


if __name__ == "__main__":
    main()