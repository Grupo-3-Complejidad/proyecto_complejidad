from flask import Flask, render_template, request
import csv

app = Flask(__name__)

# Ruta principal y búsqueda
@app.route('/')
def index():
    # Leer los datos del archivo CSV
    productos = []
    with open('csv_Test.csv', 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='@')
        for row in csv_reader:
            productos.append(row)

    # Obtener el texto de búsqueda de la solicitud
    query = request.args.get('query', '')

    # Filtrar los productos según el texto de búsqueda
    productos_filtrados = []
    if query:
        for producto in productos:
            if query.lower() in producto[1].lower():
                productos_filtrados.append(producto)
    else:
        productos_filtrados = productos

    return render_template('index.html', productos=productos_filtrados)

if __name__ == '__main__':
    app.run()