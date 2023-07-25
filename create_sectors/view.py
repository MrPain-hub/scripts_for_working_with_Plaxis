from plxscripting.easy import *
import numpy as np
import pandas as pd

s_i, g_i = new_server('localhost', 10000, password='qwerty123')


df_sectors = pd.read_excel(r".\sectorize_after_interpol_bad_points_v2.xls", sheet_name="sectorize_(2, 4)", engine="xlrd")
print(df_sectors)
print(df_sectors["E_bad"])
print(df_sectors["sector"])

materials_params = {"Name": [f"sector_{i}" for i in df_sectors["sector"]],
                    "Eref": list(df_sectors["E_bad"]),
                    "Eoed": list(df_sectors["E_bad"]),
                    "Einc": list(df_sectors["k"]),
                    "verticalRef": list(df_sectors["b"])
                    }
for i in range(df_sectors.shape[0]):
    params = [materials_params["Name"][i],
              materials_params["Eref"][i],
              materials_params["Einc"][i],
              materials_params["verticalRef"][i]
              ]

    soilmat_1 = g_i.soilmat("Comments", "",
                            "Identification", params[0],
                            "Colour", 15262369,
                            "SoilModel", 1,     # 1 - Linear Elastic; 2 - Mohr-Coulomb.
                            "Eref", params[1],
                            "Eoed", params[1],
                            "Vs", 0,
                            "Vp", 0,
                            "Einc", params[2],
                            "verticalRef", params[3]
                            )


g_i.gotostructures()
soil_params = ["sector_1", 28.075, -0.00721, 29.628]
"""
soilmat_1 = g_i.soilmat("Comments", "",
                        #"MaterialName", soil_params[0],
                        "Identification", soil_params[0],
                        "Colour", 15262369,
                        "SoilModel", 1,     # 1 - Linear Elastic; 2 - Mohr-Coulomb.
                        "Eref", soil_params[1],
                        "Eoed", soil_params[1],
                        "Vs", 0,
                        "Vp", 0,
                        "Einc", soil_params[2],
                        "verticalRef", soil_params[3]
                        #"CVRef", soil_params[3]
                        )"""
soilmat_1 = g_i.Materials[-1]
print(soilmat_1)
# soilmat_1.Name = "sector_7"
print(soilmat_1.Name)
#print(soilmat_1.commands())


"""
print(g_i.Polycurves[-1].echo())
g_i.Polycurves[-1].Offset2 = -38
print(g_i.Polycurves[-1].info())
print(g_i.Polycurves[-1].commands())
print(g_i.Polycurves[-1].reset("Arc", 0, 180, 38, "Arc", 0, 180, 38))"""
