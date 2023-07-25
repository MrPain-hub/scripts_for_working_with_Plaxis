import numpy as np
import math


class SectorizationPolar_v2():
    """
    Класс для разбиения на сектора под параметры плиты
    """
    def __init__(self, center, R):
        self.R = R
        self.center = center


    def sectoral_cylinder(self, points, sector_size):

        if len(points.shape) > 2:
            points = points[:, :, 0]

        sector_angle = 2 * np.pi / sector_size[1]
        sector_radius = self.R / sector_size[0]
        # Расчитываем полярный радиус и секторизуем его
        polar_radius = np.linalg.norm(points - self.center, axis=1)
        del_index = np.where(polar_radius > self.R)
        polar_radius = np.delete(polar_radius, del_index)

        min_radius = np.min(polar_radius)
        sector_indices_radius = np.floor((polar_radius) / sector_radius).astype(int)


        points = np.delete(points, del_index, axis=0)

        # Преобразуем координаты точек в полярные координаты относительно центра
        polar_coords = np.arctan2(points[:,1] - self.center[1], points[:,0] - self.center[0])
        polar_coords = np.where(polar_coords < 0, polar_coords + 2*np.pi, polar_coords)

        # Нормализуем полярный угол в диапазоне [0, 2*np.pi) и секторизуем его
        sector_indices_angle = np.floor(polar_coords / sector_angle).astype(int)

        # Объединяем индексы угла и радиуса в один индекс сектора
        sector_indices = sector_indices_angle * sector_size[0] + sector_indices_radius
        self.sector_indices = np.reshape(sector_indices, (sector_indices.shape[0], 1))

        print(f"сектора радиуса: {np.unique(sector_indices_radius)}")
        print(f"сектора углов: {np.unique(sector_indices_angle * sector_size[0])}")

        self.points = points
        self.del_index = del_index

        return self.sector_indices


    def sectoral_sphere(self, points, sector_size):

        sector_angle = 2 * np.pi / sector_size[1]
        sector_radius = self.R / sector_size[0]
        # Расчитываем полярный радиус и секторизуем его
        polar_radius = np.linalg.norm(points - self.center, axis=1)
        del_index = np.where(polar_radius > self.R)
        polar_radius = np.delete(polar_radius, del_index)

        min_radius = np.min(polar_radius)
        sector_indices_radius = np.floor((polar_radius) / sector_radius).astype(int)


        points = np.delete(points, del_index, axis=0)

        # Преобразуем координаты точек в полярные координаты относительно центра
        polar_coords = np.arctan2(points[:,1] - self.center[1], points[:,0] - self.center[0])
        polar_coords = np.where(polar_coords < 0, polar_coords + 2*np.pi, polar_coords)

        # Нормализуем полярный угол в диапазоне [0, 2*np.pi) и секторизуем его
        sector_indices_angle = np.floor(polar_coords / sector_angle).astype(int)

        # Объединяем индексы угла и радиуса в один индекс сектора
        sector_indices = sector_indices_angle * sector_size[0] + sector_indices_radius
        self.sector_indices = np.reshape(sector_indices, (sector_indices.shape[0], 1))

        print(f"сектора радиуса: {np.unique(sector_indices_radius)}")
        print(f"сектора углов: {np.unique(sector_indices_angle * sector_size[0])}")

        self.points = points
        self.del_index = del_index

        return self.sector_indices

    def get_new_arr(self):
        return np.concatenate((self.points, self.sector_indices), axis=1)

    def get_bad_arr(self, sector_size):

        def polar_to_cartesian(r, theta, eps=0.01):
            x = r * math.cos(theta) - eps
            y = r * math.sin(theta) - eps

            return x, y

        sector_angle = 2 * np.pi / sector_size[1]
        sector_radius = self.R / sector_size[0]

        bad_points = None

        radius_start = sector_radius

        for i in range(sector_size[0]):
            angle_start = sector_angle / 2

            for j in range(sector_size[1]):
                x_i, y_i = polar_to_cartesian(radius_start, angle_start)
                point = np.array([x_i + self.center[0], y_i + self.center[1]]).reshape(1, -1)

                if bad_points is None:
                    bad_points = point.copy()
                else:
                    bad_points = np.append(bad_points, point, axis=0)

                angle_start += sector_angle

            radius_start += sector_radius

        z_i = np.array([self.center[2] for i in range(bad_points.shape[0])]).reshape(-1, 1)
        self.sector_list = np.array(range(sector_size[0] * sector_size[1])).reshape(-1, 1)

        return np.concatenate((bad_points, z_i), axis=1)


if __name__ == "__main__":
    plate_center = [0, 0]
    plate_R = 2
    sector_size = [1, 4]
    A = np.array([1, -1, -1, 1]).reshape(-1, 1)
    B = np.array([1, 1, -1, -1]).reshape(-1, 1)

    points_input = np.concatenate((A, B), axis=1)
    Sectorization = SectorizationPolar_v2(plate_center, plate_R)
    print(Sectorization.sectoral_cylinder(points_input, sector_size).reshape(-1))

