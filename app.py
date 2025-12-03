from flask import Flask, jsonify, request
from models.censoescolar2024 import load_json_to_db
from database.database import get_db_connection

app = Flask(__name__)

load_json_to_db()

@app.route('/escolas', methods=['GET'])
def get_escolas():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor()

    escolas = cursor.execute(
        'SELECT * FROM censoescolar2024 LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()

    total = cursor.execute('SELECT COUNT(*) FROM censoescolar2024').fetchone()[0]
    conn.close()

    result = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': (total + per_page - 1) // per_page,
        'data': [dict(escola) for escola in escolas]
    }
    return jsonify(result)

@app.route('/escolas/<codigo>', methods=['GET'])
def get_escola(codigo):
    conn = get_db_connection()
    escola = conn.execute(
        'SELECT * FROM censoescolar2024 WHERE codigo = ?', 
        (codigo,)
    ).fetchone()
    conn.close()

    if escola:
        return jsonify(dict(escola))

    return jsonify({'error': 'Escola não encontrada'}), 404

@app.route('/escolas', methods=['POST'])
def create_escola():
    data = request.json

    required_fields = [
        'codigo', 'nome', 'municipio', 'uf',
        'qt_mat_infantil', 'qt_mat_fundamental',
        'qt_mat_medio'
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo obrigatório ausente: {field}'}), 400

    qt_total = (
        data['qt_mat_infantil'] +
        data['qt_mat_fundamental'] +
        data['qt_mat_medio']
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO censoescolar2024 
            (codigo, nome, municipio, uf, qt_mat_infantil, qt_mat_fundamental, qt_mat_medio, qt_mat_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['codigo'],
            data['nome'],
            data['municipio'],
            data['uf'],
            data['qt_mat_infantil'],
            data['qt_mat_fundamental'],
            data['qt_mat_medio'],
            qt_total
        ))

        conn.commit()
        return jsonify({'message': 'Escola criada com sucesso'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    finally:
        conn.close()

@app.route('/escolas/<codigo>', methods=['PUT'])
def update_escola(codigo):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    escola = cursor.execute(
        'SELECT * FROM censoescolar2024 WHERE codigo = ?', 
        (codigo,)
    ).fetchone()

    if not escola:
        conn.close()
        return jsonify({'error': 'Escola não encontrada'}), 404

    updated = {
        'nome': data.get('nome', escola['nome']),
        'municipio': data.get('municipio', escola['municipio']),
        'uf': data.get('uf', escola['uf']),
        'qt_mat_infantil': data.get('qt_mat_infantil', escola['qt_mat_infantil']),
        'qt_mat_fundamental': data.get('qt_mat_fundamental', escola['qt_mat_fundamental']),
        'qt_mat_medio': data.get('qt_mat_medio', escola['qt_mat_medio']),
    }

    qt_total = (
        updated['qt_mat_infantil'] +
        updated['qt_mat_fundamental'] +
        updated['qt_mat_medio']
    )

    cursor.execute('''
        UPDATE censoescolar2024
        SET nome = ?, municipio = ?, uf = ?,
            qt_mat_infantil = ?, qt_mat_fundamental = ?, qt_mat_medio = ?, qt_mat_total = ?
        WHERE codigo = ?
    ''', (
        updated['nome'], updated['municipio'], updated['uf'],
        updated['qt_mat_infantil'], updated['qt_mat_fundamental'], updated['qt_mat_medio'],
        qt_total,
        codigo
    ))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Escola atualizada com sucesso'})

@app.route('/escolas/<codigo>', methods=['DELETE'])
def delete_escola(codigo):
    conn = get_db_connection()
    cursor = conn.cursor()

    escola = cursor.execute(
        'SELECT * FROM censoescolar2024 WHERE codigo = ?', 
        (codigo,)
    ).fetchone()

    if not escola:
        conn.close()
        return jsonify({'error': 'Escola não encontrada'}), 404

    cursor.execute('DELETE FROM censoescolar2024 WHERE codigo = ?', (codigo,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Escola deletada com sucesso'})

if __name__ == '__main__':
    app.run(debug=True)
