from plxscripting.easy import *
import numpy as np
import pandas as pd
import re

from creat_test_space import *
from sectorization_module import SectorizationPolar_v2


def open_file(path):
    try:
        s_i.open(filename=path)
    except Exception as ex:
        print(ex)


def read_CenterOfGravity(text, axis=None):
    """
    :param text: "X: 118.80; Y: 118.80; Z: -61.75"
    :return: [X, Y, Z], type->float
    """
    text_new = re.sub(r"[^;.0-9]", "", str(text))
    xyz = list(map(float, text_new.split(";")))

    if axis is None:
        return xyz

    return xyz[axis]

"""
Сервер
"""
PORT_i = 10000
PASSWORD = 'qwerty123'
"""
Параметры плиты
"""
X_plate = 100
Y_plate = 100
R_plate = 38
"""
Пути к файлам
"""
PATH_df = r".\sectorize_after_interpol_bad_points_v2.xls"
PATH_file = r"E:\Anydesk обмен\Л2_208_70-76_расчетная нагрузка от 230705_Един.p3d"
"""
Параметры секторов
"""
H = -21.75
DEPTH_sector = 80
sector_size = [2, 4]
quantity_sector = sector_size[0] * sector_size[1]
CENTER_point = [X_plate, Y_plate, H]

"""
Команды Plaxis
"""
s_i, g_i = new_server('localhost', PORT_i, password=PASSWORD)

new_space(X_plate*2, Y_plate*2, H - DEPTH_sector)

g_i.gotostructures()

"""
Создание точек и поверхностей
"""
points_np = np.array([
        [[X_plate - R_plate, Y_plate, H], [X_plate + R_plate, Y_plate, H]],
        [[X_plate, Y_plate - R_plate, H], [X_plate, Y_plate + R_plate, H]],
    ])
for i in range(points_np.shape[0]):

    globals()[f"line_i_{i}"] = g_i.line(list(points_np[i, 0]), list(points_np[i, 1]))[-1]
    globals()[f"polygon_i_{i}"] = g_i.extrude(globals()[f"line_i_{i}"], 0, 0, -DEPTH_sector)

"""
Создание окружностей
"""
polycurve_1 = g_i.polycurve(CENTER_point, (1, 0, 0), (0, 1, 0))
polycurve_1.Offset2 = -R_plate
polycurve_1.reset("Arc", 0, 180, R_plate, "Arc", 0, 180, R_plate)

polycurve_2 = g_i.polycurve(CENTER_point, (1, 0, 0), (0, 1, 0))
polycurve_2.Offset2 = -R_plate/2
polycurve_2.reset("Arc", 0, 180, R_plate/2, "Arc", 0, 180, R_plate/2)

"""
Создание цилиндра (Volume) 
"""
surface_1 = g_i.surface(polycurve_1)

volume_1 = g_i.extrude(surface_1, 0, 0, -DEPTH_sector)[0]
polygon_1 = g_i.extrude(polycurve_2, 0, 0, -DEPTH_sector)

"""
Разбиение Volume
"""
split_result = g_i.intersect(volume_1, polygon_1, *[globals()[f"polygon_i_{i}"] for i in range(points_np.shape[0])])

"""
Создание группы
"""
group_volume = []

for item in split_result:
    if item.TypeName == "Volume":
        group_volume.append(item)

group_1 = g_i.group(*group_volume)

"""
Объединение секторов с Volume_PLAXIS
"""
"""
    Информация о Volume в PLAXIS
"""
df_Plaxis = pd.DataFrame({"class_volume": group_volume})
df_Plaxis["X"] = df_Plaxis["class_volume"].apply(lambda V: read_CenterOfGravity(V.CenterOfGravity, axis=0))
df_Plaxis["Y"] = df_Plaxis["class_volume"].apply(lambda V: read_CenterOfGravity(V.CenterOfGravity, axis=1))
df_Plaxis["Name"] = df_Plaxis["class_volume"].apply(lambda V: V.Name)
"""
    Чтение информации о секторах и 
    Объединение
"""
X_np = df_Plaxis["X"].to_numpy().reshape(-1, 1)
Y_np = df_Plaxis["Y"].to_numpy().reshape(-1, 1)
points_input = np.concatenate((X_np, Y_np), axis=1)
"""
        Определение номера сектора для координат центра Volume
"""
Sectorization = SectorizationPolar_v2([X_plate, Y_plate], R_plate)
df_Plaxis["sector"] = Sectorization.sectoral_cylinder(points_input, sector_size).reshape(-1)

df_merge = pd.read_excel(PATH_df,
                         sheet_name="sectorize_(2, 4)",
                         engine="xlrd"
                         ).merge(df_Plaxis,
                                 on="sector",
                                 how="left",
                                 suffixes=("", "_PLAXIS")
                                 )
df_merge.to_excel("результат_присваивания.xlsx", index=False)

"""
Создание материала и присваивание к Volume
"""
materials_params = {"Name": [f"sector_{i}" for i in df_merge["sector"]],
                    "Eref": list(df_merge["E_bad"]),
                    "Eoed": list(df_merge["E_bad"]),
                    "Einc": list(df_merge["k"]),
                    "verticalRef": list(df_merge["b"]),
                    "class_PLAXIS": []
                    }

for i in range(df_merge.shape[0]):

    params = [materials_params["Name"][i],
              materials_params["Eref"][i],
              materials_params["Einc"][i],
              materials_params["verticalRef"][i]
              ]

    material_now = g_i.soilmat("Comments", "",
                               "Identification", params[0],
                               "SoilModel", 1,     # 1 - Linear Elastic; 2 - Mohr-Coulomb.
                               "Eref", params[1],
                               "Eoed", params[1],
                               "Vs", 0,
                               "Vp", 0,
                               "Einc", params[2],
                               "verticalRef", params[3]
                               )

    df_merge["class_volume"][i].Soil.Material = material_now
    materials_params["class_PLAXIS"].append(material_now)

"""
Переход к фазам и удаление фаз
"""
g_i.gotostages()

if len(g_i.Phases) > 1:
    for phase in g_i.Phases[1:]:
        g_i.delete(phase)



