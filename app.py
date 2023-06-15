from flask import Flask, render_template
import csv

app = Flask(__name__)

@app.route('/')
def index():
    # Leer los datos del archivo CSV
    productos = []
    with open('csv_Test.csv', 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='@')
        for row in csv_reader:
            productos.append(row)

    return render_template('index.html', productos=productos)

if __name__ == '__main__':
    app.run()