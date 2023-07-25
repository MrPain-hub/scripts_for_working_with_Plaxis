from plxscripting.easy import *


def new_space(X, Y, H, port=10000, password='qwerty123'):
    s_i, g_i = new_server('localhost', port, password=password)

    s_i.new()
    g_i.SoilContour.initializerectangular(0, 0, X, Y)

    g_i.gotosoil()

    borehole_g = g_i.borehole(0, 0)
    borehole_volume_g = g_i.soillayer(borehole_g, abs(H))

    soilmat_g = g_i.soilmat("Comments", "тестовый грунт",
                            "Identification", "soilmat_test",
                            "SoilModel", 1,     # 1 - Linear Elastic; 2 - Mohr-Coulomb.
                            "Eref", 30
                            )

    list(borehole_volume_g.UserFeatures)[0].Material = soilmat_g


if __name__ == "__main__":
    pass
