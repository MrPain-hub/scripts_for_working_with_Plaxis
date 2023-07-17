from plxscripting.easy import *

import tkinter as tk
from tkinter import filedialog

import pandas as pd
from xlsxwriter import Workbook

import datetime


PORT_o = 10001
PASSWORD = "qwerty123"
s_o, g_o = None, None

"""
Функции для Plaxis
"""
def get_embeddedbeam(beam_o, phase_o):
    """
    Получить данные по EmbeddedBeam для конкретного объекта на конкретной фазе
    """
    beam_X = g_o.getresults(beam_o, phase_o, g_o.ResultTypes.EmbeddedBeam.X, "node")
    beam_Y = g_o.getresults(beam_o, phase_o, g_o.ResultTypes.EmbeddedBeam.Y, "node")
    beam_Z = g_o.getresults(beam_o, phase_o, g_o.ResultTypes.EmbeddedBeam.Z, "node")
    beam_N = g_o.getresults(beam_o, phase_o, g_o.ResultTypes.EmbeddedBeam.N, "node")
    beam_Uz = g_o.getresults(beam_o, phase_o, g_o.ResultTypes.EmbeddedBeam.Uz, "node")

    phase_name = str(phase_o.Identification).split(" [")[0]
    col2 = 'N [kN]'+'_'+phase_name
    col3 = 'Uz [m]'+'_'+phase_name

    results = {"X": beam_X,
               'Y': beam_Y,
               "Z": beam_Z,
               col2: beam_N,
               col3: beam_Uz
               }

    beam_results = pd.DataFrame(results)
    beam_results = beam_results.sort_values(by=["Z"], ascending=False)
    return beam_results


def save_for_embeddedbeams_in_xlsx(phase_list, filename="result_lahta_2_3.xlsx"):
    """
    Собрать в df, только значения EmbeddedBeam с максимальной Z
    И отдельно создать сводную с MAX, MIN, MEAN
    """
    phase_set = set(phase_list)
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')

    pivot_table_dict = {}
    pivot_index = ["N_min [kN]", "N_max [kN]", "N_mean [kN]"]

    for phase_o in g_o.Phases:
        phase_name = str(phase_o.Identification).split(" [")[0]

        if phase_name in phase_set:
            df_embeddedbeam = None

            for embeddedbeam_o in g_o.EmbeddedBeams:
                df_now = get_embeddedbeam(embeddedbeam_o, phase_o)
                df_now = df_now.dropna(subset="Z")
                row_zmax = df_now[df_now["Z"] == df_now["Z"].max()]

                if df_embeddedbeam is None:
                    df_embeddedbeam = row_zmax.copy()
                else:
                    df_embeddedbeam = pd.concat([df_embeddedbeam, row_zmax], axis=0)
            """
            Добавление в сводную таблицу
            """
            N_min = df_embeddedbeam[f"N [kN]_{phase_name}"].min()
            N_max = df_embeddedbeam[f"N [kN]_{phase_name}"].max()
            N_mean = df_embeddedbeam[f"N [kN]_{phase_name}"].mean()
            pivot_table_dict[phase_name] = [N_min, N_max, N_mean]
            """
            Создание имя листа
            """
            sheet_name = f"phase_{phase_name}"
            if len(sheet_name) > 31:    # Имя листа Excel должно быть <= 31 символа
                sheet_name = sheet_name[:31]
            """
            Запись на лист
            """
            df_embeddedbeam.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Фаза {phase_name} завершена")

    pd.DataFrame(pivot_table_dict, index=pivot_index).to_excel(writer, sheet_name="pivot_table")  # Сводная по всем фазам

    writer.close()  # Выход из редактирования таблицы


def run_script(file_input, phase_list, file_output):

    """
    Открытие файла
    """
    print("\033[32m Файл открывается... \033[0m")
    try:
        s_o.open(file_input)
    except:
        print(f"Была ошибка")

    print("\033[32m Файл открыт \033[0m")

    print("-" * 30)
    print(f"\033[1m\033[33m Файл: {file_input}")
    print(f"Фазы: {phase_list}")
    print(f"Сохранение в файл: {file_output}")
    print("\033[32m Выполняется сбор и запись данных... \033[0m")
    """
    script
    """
    save_for_embeddedbeams_in_xlsx(phase_list, file_output)

    print("\033[32m Завершено")
    print(f"Результаты в файле: {file_output} \033[0m")
    input("Нажмите ENTER, чтобы выйти")


"""
Функции для tkinter
"""
def add_entry():
    global number_entry
    number_entry += 1

    if number_entry == 1:
        entry_1_text = tk.StringVar()
        entry_1_text.set("Расчетная нагрузка + ветер")
        globals()[f"entry_{number_entry}"] = tk.Entry(fra3, textvariable=entry_1_text)

    else:
        globals()[f"entry_{number_entry}"] = tk.Entry(fra3)

    globals()[f"entry_{number_entry}"].pack(fill='both')


def find_file():
    file_path = filedialog.askopenfilename()
    file_text.set(file_path)


def process_file():
    global PORT_o, PASSWORD, s_o, g_o


    file_input = file_text.get()
    PORT_o = int(var1_entry.get())
    PASSWORD = var2_entry.get()
    s_o, g_o = new_server('localhost', port=PORT_o, password=PASSWORD)
    file_output = var3_entry.get()

    phase_list = []

    for i in range(number_entry + 1):
        phase_list.append(globals()[f"entry_{i}"].get())

    print("Путь к файлу:", file_input)
    print("Порт:", PORT_o)
    print("Пароль:", PASSWORD)
    print("Фазы:", phase_list)

    run_script(file_input, phase_list, file_output)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Plaxis output - Получение нагрузок") #заголовок окна
    #root.geometry("300x500") # начальные размеры окна

    # Создание фреймов
    fra1 = tk.Frame(root, bd=10)
    fra2 = tk.Frame(root, bd=10)
    fra3 = tk.Frame(root, bd=10)
    fra4 = tk.Frame(root, bd=10)
    fra1.pack(fill='both')
    fra2.pack(fill='both')
    fra3.pack(fill='both')
    fra4.pack(fill='both')

    """
    Виджеты, путь к файлу
    """
    file_label = tk.Label(fra1, text="Введите путь к файлу:")
    file_label.pack(fill='both')
    search_file_button = tk.Button(fra1, text="выбрать файл", command=find_file)
    search_file_button.pack(side='right')
    file_text = tk.StringVar()
    file_text.set("для ввода")
    file_entry = tk.Entry(fra1, textvariable=file_text)
    file_entry.pack(expand=True)

    """
    Виджеты с портом
    """
    var1_label = tk.Label(fra2, text="Порт:")
    var1_label.pack(fill='both')
    var1_text = tk.StringVar()
    var1_text.set(PORT_o)
    var1_entry = tk.Entry(fra2, textvariable=var1_text)
    var1_entry.pack(fill='both')

    var2_label = tk.Label(fra2, text="Пароль:")
    var2_label.pack(fill='both')
    var2_text = tk.StringVar()
    var2_text.set(PASSWORD)
    var2_entry = tk.Entry(fra2, textvariable=var2_text)
    var2_entry.pack(fill='both')

    """
    Виджеты с нагрузкой
    """
    entry_label = tk.Label(fra3, text="Введите название фазы")
    entry_label.pack(fill='both')
    add_button = tk.Button(fra3, text="Добавить поле ввода", command=add_entry)
    add_button.pack(fill='both')

    entry_0_text = tk.StringVar()
    entry_0_text.set("Расчетная нагрузка")
    entry_0 = tk.Entry(fra3, textvariable=entry_0_text)
    entry_0.pack(fill='both')

    number_entry = 0

    """
    Виджеты для файла сохранения
    """
    var3_label = tk.Label(fra4, text="Имя файла для сохранения в формате .xlsx")
    var3_label.pack(fill='both')
    var3_text = tk.StringVar()
    var3_text.set(f"result_{datetime.date.today()}.xlsx")
    var3_entry = tk.Entry(fra4, textvariable=var3_text)
    var3_entry.pack(fill='both')

    # Кнопка для запуска обработки
    process_button = tk.Button(root, text="Запустить", height=3, bg="black", fg="white", command=process_file)
    process_button.pack(fill='both')

    root.mainloop()
