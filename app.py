from flask import Flask, render_template, request
import csv
import heapq
import graphviz as gv
import io
import base64
import tempfile

app = Flask(__name__)

class Product:
    def __init__(self, id, name, quantity, brand, category, price, url):
        self.id = id
        self.name = name
        self.quantity = quantity
        self.brand = brand
        self.category = category
        self.price = price
        self.url = url

    def get_id(self):
        return self.id
    
    def get_name(self):
        return self.name

    def get_quantity(self):
        return self.quantity

    def get_brand(self):
        return self.brand

    def get_category(self):
        return self.category

    def get_price(self):
        return self.price

    def get_url(self):
        return self.url

class Graph():
    def __init__(self):
        self.nodes = {}
        self.edges = set()

    def add_node(self, node):
        self.nodes[node.id] = node

    def add_edge(self, node1_id, node2_id, weight):
        edge = tuple(sorted([node1_id, node2_id]))  # Ordenar los nodos de la arista
        self.edges.add((edge, weight))

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def get_edges(self):
        return self.edges

    def get_shortest_edges(self, start_node_name, count=4):
        start_node = None
        for node in self.nodes.values():
          if node.name == start_node_name:
              start_node = node
              break

        if start_node is None:
          print("No se encontró ningún nodo con ese nombre.")
          return []

        distances = {node.id: float('inf') for node in self.nodes.values()}
        distances[start_node.id] = 0

        priority_queue = [(0, start_node.id)]
        visited = set()

        while priority_queue:
          current_distance, current_node_id = heapq.heappop(priority_queue)

          if current_node_id in visited:
              continue

          current_node = self.get_node(current_node_id)
          visited.add(current_node_id)

          for edge, weight in self.edges:
              node1_id, node2_id = edge
              if node1_id == current_node.id and node2_id not in visited:
                neighbor_node1 = self.get_node(node1_id)
                neighbor_node2 = self.get_node(node2_id)
                new_distance = current_distance + weight
                if new_distance < distances[neighbor_node2.id]:
                    distances[neighbor_node2.id] = new_distance
                    heapq.heappush(priority_queue, (new_distance, neighbor_node2.id))
              elif node2_id == current_node.id and node1_id not in visited:
                  neighbor_node1 = self.get_node(node1_id)
                  neighbor_node2 = self.get_node(node2_id)
                  new_distance = current_distance + weight
                  if new_distance < distances[neighbor_node1.id]:
                      distances[neighbor_node1.id] = new_distance
                      heapq.heappush(priority_queue, (new_distance, neighbor_node1.id))

            # Optimización: Remover duplicados en la cola de prioridad
          while priority_queue and priority_queue[0][1] in visited:
              heapq.heappop(priority_queue)

          sorted_distances = sorted(distances.items(), key=lambda x: x[1])[:count]
          shortest_edges = []
          for node_id, distance in sorted_distances:
            if node_id != start_node.id:
                node = self.get_node(node_id)
                shortest_edges.append((node, distance))

          return shortest_edges 


@app.route('/')
def index():
    # Leer los datos del archivo CSV y construir el grafo
    graph = build_graph_from_csv('csv_Products.csv')

    # Obtener el texto de búsqueda de la solicitud
    query = request.args.get('query', '')

    # Obtener los productos filtrados según el texto de búsqueda
    productos_filtrados = filter_products(graph, query)

    return render_template('index.html', productos=productos_filtrados)


def build_graph_from_csv(csv_filename):
    graph = Graph()

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csv_handle:
        csv_products = csv.reader(csv_handle, delimiter='@')
        row_number = 0
        for line in csv_products:
            try:
                if len(line) >= 7:  # Verificar que la línea tenga al menos 7 elementos
                    id = line[0]
                    name = line[1]
                    quantity = line[2]
                    brand = line[3]
                    category = line[4]
                    price = float(line[5])
                    url = line[6]
                    product = Product(id, name, quantity, brand, category, price, url)
                    graph.add_node(product)
                else:
                    print("Error: la línea no tiene suficientes elementos")
                    input("Presione Enter para continuar...")
                    print(f"Error: en la línea {row_number}")
            except ValueError as e:
                print(f"Error: {e} en la línea {row_number}")
                input("Presione Enter para continuar...")
            row_number += 1
        print(f"Se leyeron {row_number} filas")

    add_edges(graph)
    return graph


def add_edges(graph):
    for id1, product1 in graph.nodes.items():
        for id2, product2 in graph.nodes.items():
            if id1 != id2:
                if product1.category == product2.category:
                    weight = 5
                    if product1.brand == product2.brand:
                        weight -= 2
                        if (product1.price - product2.price < 5800 and product1.price - product2.price > 0):
                            weight -= 2
                else:
                    weight = 10

                graph.add_edge(id1, id2, weight)


def filter_products(graph, query):
    productos = []
    with open('csv_Products.csv', 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='@')
        for row in csv_reader:
            productos.append(row)

    productos_filtrados = []
    if query:
        for producto in productos:
            if query.lower() in producto[1].lower():
                productos_filtrados.append(producto)
    else:
        productos_filtrados = productos

    return productos_filtrados

def print_graph(start_node, recommended_nodes):
    # Crear un objeto Digraph
    graph_image = gv.Graph()

    graph_image.node(start_node.id, label=start_node.id)
    for node in recommended_nodes:
        graph_image.node(node[0], label=node[0])

    # Agregar aristas al gráfico
    for node in recommended_nodes:
        node_id = node[0]
        edge = tuple(sorted([start_node.id, node_id]))
        weight = node[7]
        edge_color = 'green' if weight == 3 else 'yellow' if weight == 5 else 'blue' if weight == 1 else 'red'
        graph_image.edge(edge[0], edge[1], label=str(weight), color=edge_color)

    # Guardar el gráfico en memoria como PNG
    image_data = graph_image.pipe(format='png')

    # Codificar los datos de la imagen en base64
    import base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')

    return image_base64

@app.route('/recomendacion/<producto_id>')
def recomendacion(producto_id):
    graph = build_graph_from_csv('csv_Products.csv')
    producto_seleccionado = get_producto_por_id(producto_id)

    if producto_seleccionado:
        shortest_edges = graph.get_shortest_edges(producto_seleccionado.name, count=4)
        recomendaciones = []
        print(shortest_edges)
        for node, distance in shortest_edges:
            recomendaciones.append((node.get_id(), node.get_name(), node.get_quantity(), node.get_brand(), node.get_category(), node.get_price(), node.get_url(), distance))
        
        graph_data = print_graph(producto_seleccionado, recomendaciones)

        return render_template('recomendation.html', producto_seleccionado=producto_seleccionado, recomendaciones=recomendaciones, graph_data=graph_data)
    else:
        return "Producto no encontrado"

def get_producto_por_id(producto_id):
    with open('csv_Products.csv', 'r', newline='', encoding='utf-8') as csv_handle:
        csv_products = csv.reader(csv_handle, delimiter='@')
        for line in csv_products:
            if len(line) >= 7:
                if line[0] == producto_id:
                    id = line[0]
                    name = line[1]
                    quantity = line[2]
                    brand = line[3]
                    category = line[4]
                    price = float(line[5])
                    url = line[6]
                    return Product(id, name, quantity, brand, category, price, url)
    return None


if __name__ == '__main__':
    app.run()