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
Функции для чтения крена плиты
"""
def get_soil_by_h(soil_o, phase_o, soil_h=-12.2, eps=0.1):

    soil_X = g_o.getresults(soil_o, phase_o, g_o.ResultTypes.Soil.X, "node")
    soil_Y = g_o.getresults(soil_o, phase_o, g_o.ResultTypes.Soil.Y, "node")
    soil_Z = g_o.getresults(soil_o, phase_o, g_o.ResultTypes.Soil.Z, "node")
    soil_Uz = g_o.getresults(soil_o, phase_o, g_o.ResultTypes.Soil.Uz, "node")   # Осадка плиты

    results = {"X": soil_X,
               'Y': soil_Y,
               'Z': soil_Z,
               "Uz": soil_Uz,
               }

    soil_results = pd.DataFrame(results)

    soil_results = soil_results.query(f'Z <={soil_h + eps}')
    soil_results = soil_results.query(f'Z >={soil_h - eps}')

    soil_results = soil_results.sort_values(by=["Z"], ascending=False)

    return soil_results


def filter_points_for_df(df, center, radius, eps=0.7):

    x0, y0 = center
    df["distance_2"] = df.apply(lambda node: (node["X"] - x0)**2 + (node["Y"] - y0)**2,
                                axis=1
                                )

    limit = [(radius - eps) ** 2,
             (radius + eps) ** 2
             ]

    result = df.query('@limit[0] <= distance_2 and distance_2 <= @limit[1]')
    return result


def building_roll_search_for_df(df):

    def point_search(df, x0, y0):

        df_now = df.copy()

        df_now["distance_2"] = df_now.apply(lambda row: (row["X"] - x0)**2 + (row["Y"] - y0)**2,
                                            axis=1
                                            )

        node_a = df_now[df_now["distance_2"] == df_now["distance_2"].min()].reset_index(drop=True)
        node_b = df_now[df_now["distance_2"] == df_now["distance_2"].max()].reset_index(drop=True)

        node_a.columns = [f"{col}_a" for col in node_a.columns]
        node_b.columns = [f"{col}_b" for col in node_b.columns]

        return pd.concat([node_a, node_b],
                         axis=1
                         )

    nodes = None

    for row in df.query('Y >= 100').index:
        x0 = df.loc[row, "X"]
        y0 = df.loc[row, "Y"]

        if nodes is None:
            nodes = point_search(df, x0, y0).copy()
        else:
            nodes = pd.concat([nodes, point_search(df, x0, y0)],
                              ignore_index=True,
                              axis=0
                              )

    nodes["dUz"] = abs(nodes["Uz_b"] - nodes["Uz_a"])
    nodes["distance"] = nodes["distance_2_b"] ** 0.5
    nodes["roll"] = nodes.apply(lambda row: row["dUz"] / row["distance"],
                                axis=1
                                )
    nodes = nodes.drop(columns=["distance_2_a", "distance_2_b"])

    return nodes


def body_script(phase_o):

    pile_by_soil = [g_o.Soil_9_Soil_13_Soil_18_1,
                    g_o.Soil_10_Soil_13_Soil_18_1,
                    g_o.Soil_11_Soil_13_Soil_18_1,
                    g_o.Soil_12_Soil_13_Soil_18_1
                    ]

    df_soils = None
    for soil_o in pile_by_soil:
        df_now = get_soil_by_h(soil_o, phase_o)

        if df_soils is None:
            df_soils = df_now

        else:
            df_soils = pd.concat([df_soils, df_now],
                                 ignore_index=True,
                                 axis=0
                                 )
    df_soils.drop_duplicates(inplace=True)  # удаление дубликатов

    df_new = filter_points_for_df(df_soils,
                                  center=[100, 100],
                                  radius=38
                                  )

    df_roll = building_roll_search_for_df(df_new)
    print(df_roll[df_roll["roll"] == df_roll["roll"].max()])
    return df_soils, df_roll


def run_script_by_roll(file_input, phase_list, file_output):
    """
    Открытие файла
    """

    try:
        s_o.open(file_input)
    except:
        print(f"Была ошибка")


    print("-" * 30)
    print("Определение крена")
    print(f"Файл: {file_input}")
    print(f"Фазы: {phase_list}")
    print(f"Сохранение в файл: {file_output}")
    # print("-" * 30)
    # print("Выполняется сбор и запись данных...")

    """
    script и запись в xlsx
    """
    writer = pd.ExcelWriter(file_output, engine='xlsxwriter')

    df_pivot_max = None
    pivot_index = []

    number_phase = 0

    for phase_o in g_o.Phases:

        phase_name = str(phase_o.Identification).split(" [")[0]

        if phase_name in set(phase_list):
            number_phase += 1
            df_soils, df_result = body_script(phase_o)
        else:
            continue

        sheet_name_for_df_soils = f"Uz_all_points_phase{number_phase}"
        sheet_name = f"phase{number_phase}_{phase_name}"
        if len(sheet_name) > 31:    # Имя листа Excel должно быть <= 31 символа
            sheet_name = sheet_name[:31]

        if df_pivot_max is None:
            df_pivot_max = df_result[df_result["roll"] == df_result["roll"].max()]
        else:
            df_pivot_max = pd.concat([df_pivot_max, df_result[df_result["roll"] == df_result["roll"].max()]],
                                     axis=0
                                     )
        pivot_index.append(phase_name)

        df_soils.to_excel(writer, sheet_name=sheet_name_for_df_soils, index=False)
        df_result.to_excel(writer, sheet_name=sheet_name, index=False)


    df_pivot_max.index = pivot_index
    df_pivot_max.to_excel(writer, sheet_name="roll_max")  # Сводная по всем фазам

    writer.close()  # Выход из редактирования таблицы
    print("Завершено")
    print(f"Результаты в файле: {file_output}")
    print("-" * 30)

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

    run_script_by_roll(file_input, phase_list, file_output)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Plaxis output - Получение Крена плиты") #заголовок окна
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

