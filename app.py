import sys
import requests
import folium
import polyline
import io
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QListWidget, QListWidgetItem, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from scipy.optimize import linear_sum_assignment

def get_osrm_route(start, end, server_url="http://router.project-osrm.org"):
    coords = f"{start[1]},{start[0]};{end[1]},{end[0]}"
    url = f"{server_url}/route/v1/driving/{coords}?overview=full"  # Ensure full geometry is requested
    response = requests.get(url)
    routes = response.json()
    if routes['code'] == 'Ok':
        route_summary = routes['routes'][0]['legs'][0]
        route_geometry = routes['routes'][0]['geometry']  # Get encoded polyline
        return route_summary['distance'], route_geometry
    else:
        raise Exception("OSRM API error: " + routes['code'])


def solve_tsp(dist_matrix):
    row_ind, col_ind = linear_sum_assignment(dist_matrix)
    total_cost = dist_matrix[row_ind, col_ind].sum()
    return col_ind, total_cost

class TSPMapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TSP Solver for Southern California")
        self.setGeometry(100, 100, 1280, 720)
        self.initUI()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.start_city_dropdown = QComboBox()
        self.start_city_dropdown.addItems(['Los Angeles', 'San Diego', 'Irvine', 'Santa Ana', 'Long Beach', 'Pasadena', 'Malibu', 'Ventura'])
        layout.addWidget(self.start_city_dropdown)

        self.destination_cities_list = QListWidget()
        self.destination_cities_list.addItems(['Los Angeles', 'San Diego', 'Irvine', 'Santa Ana', 'Long Beach', 'Pasadena', 'Malibu', 'Ventura'])
        self.destination_cities_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.destination_cities_list)

        self.calculate_button = QPushButton('Calculate Route')
        self.calculate_button.clicked.connect(self.calculate_route)
        layout.addWidget(self.calculate_button)

        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh_app)
        layout.addWidget(self.refresh_button)

        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        self.route_label = QLabel("Route will be displayed here.")
        layout.addWidget(self.route_label)

        self.show_map()

    def show_map(self):
        # Initialize a folium map with zoom controls
        self.map = folium.Map(location=[34.0522, -118.2437], zoom_start=8, zoom_control=True)
        data = io.BytesIO()
        self.map.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())

    def calculate_route(self):
        city_coords = {
            'Los Angeles': (34.0522, -118.2437),
            'San Diego': (32.7157, -117.1611),
            'Irvine': (33.6846, -117.8265),
            'Santa Ana': (33.7455, -117.8677),
            'Long Beach': (33.7701, -118.1937),
            'Pasadena': (34.1478, -118.1445),
            'Malibu': (34.0259, -118.7798),
            'Ventura': (34.2746, -119.2290)
        }
        cities = [self.start_city_dropdown.currentText()] + [item.text() for item in self.destination_cities_list.selectedItems()]

        n = len(cities)
        dist_matrix = np.zeros((n, n))
        geometries = [[None] * n for _ in range(n)]  # Correct initialization

        for i in range(n):
            for j in range(i + 1, n):
                dist, geom = get_osrm_route(city_coords[cities[i]], city_coords[cities[j]])
                dist_matrix[i][j] = dist_matrix[j][i] = dist
                geometries[i][j] = geometries[j][i] = geom  # Store geometries symmetrically

        route_indices, cost = solve_tsp(dist_matrix)
        route = [cities[i] for i in route_indices]
        route_text = " --> ".join(route) + f" | Total Distance: {cost} meters"
        self.update_map_and_label(route, city_coords, route_text, geometries)

    def update_map_and_label(self, route, city_coords, route_text, geometries):
        m = folium.Map(location=city_coords[route[0]], zoom_start=8)
        for i in range(len(route)-1):
            start_city = route[i]
            end_city = route[i+1]
            start_coords = city_coords[start_city]
            end_coords = city_coords[end_city]
            folium.Marker(start_coords, popup=start_city).add_to(m)

            # Correctly access and decode the polyline
            route_path = polyline.decode(geometries[route.index(start_city)][route.index(end_city)])
            folium.PolyLine(locations=route_path, color='blue', weight=5).add_to(m)

        # Close the loop to the start city
        start_coords = city_coords[route[-1]]
        end_coords = city_coords[route[0]]
        folium.Marker(end_coords, popup=route[0]).add_to(m)
        route_path = polyline.decode(geometries[route.index(route[-1])][route.index(route[0])])
        folium.PolyLine(locations=route_path, color='blue', weight=5).add_to(m)

        data = io.BytesIO()
        m.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())
        self.route_label.setText(route_text)

    def refresh_app(self):
        # Clear selections
        self.start_city_dropdown.setCurrentIndex(0)
        self.destination_cities_list.clearSelection()

        # Reset map and label
        self.show_map()
        self.route_label.setText("Route will be displayed here.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TSPMapApp()
    ex.show()
    sys.exit(app.exec_())
