"""
Tests unitaires de l'API Todo (Flask + SQLite).

Stratégie d'isolation :
- On définit la variable d'environnement DB_PATH vers un fichier temporaire
  AVANT d'importer `app`, car `app.py` lit DB_PATH au moment de l'import.
- La fixture `client` recrée une base vierge avant chaque test, ce qui garantit
  des tests indépendants et reproductibles (id auto-incrément reparti de 1).
"""
import os
import tempfile

import pytest

# Base de données temporaire dédiée aux tests (jamais le todos.db de prod)
TEST_DB = os.path.join(tempfile.gettempdir(), 'todos_test.db')
os.environ['DB_PATH'] = TEST_DB

import app as todo_app  # noqa: E402  (import après avoir fixé DB_PATH)


@pytest.fixture
def client():
    """Fournit un client de test Flask avec une base SQLite fraîche."""
    # Repartir d'une base vierge à chaque test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    todo_app.init_db()
    todo_app.app.config['TESTING'] = True

    with todo_app.app.test_client() as client:
        yield client

    # Nettoyage après le test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_get_todos_empty(client):
    """GET /todos renvoie une liste vide quand la base est vierge."""
    resp = client.get('/todos')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_todo(client):
    """POST /todos crée une tâche et renvoie 201 + l'objet créé."""
    resp = client.post('/todos', json={
        'title': 'Apprendre DevSecOps',
        'description': 'Module 4 TP'
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['id'] == 1
    assert data['title'] == 'Apprendre DevSecOps'
    assert data['description'] == 'Module 4 TP'
    assert data['done'] is False


def test_create_todo_missing_title(client):
    """POST /todos sans 'title' renvoie 400."""
    resp = client.post('/todos', json={'description': 'Sans titre'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()


def test_get_todo_by_id(client):
    """GET /todos/<id> renvoie la tâche correspondante."""
    client.post('/todos', json={'title': 'Tâche 1'})
    resp = client.get('/todos/1')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['id'] == 1
    assert data['title'] == 'Tâche 1'


def test_get_todo_not_found(client):
    """GET /todos/<id> sur un id inexistant renvoie 404."""
    resp = client.get('/todos/999')
    assert resp.status_code == 404
    assert 'error' in resp.get_json()


def test_update_todo(client):
    """PUT /todos/<id> met à jour la tâche et persiste les changements."""
    client.post('/todos', json={'title': 'Ancien titre'})
    resp = client.put('/todos/1', json={
        'title': 'Nouveau titre',
        'description': 'Mise à jour',
        'done': True
    })
    assert resp.status_code == 200
    assert resp.get_json()['message'] == 'Todo updated'

    # Vérifier la persistance
    check = client.get('/todos/1').get_json()
    assert check['title'] == 'Nouveau titre'
    assert check['done'] is True


def test_update_todo_not_found(client):
    """PUT /todos/<id> sur un id inexistant renvoie 404."""
    resp = client.put('/todos/999', json={'title': 'X'})
    assert resp.status_code == 404
    assert 'error' in resp.get_json()


def test_delete_todo(client):
    """DELETE /todos/<id> supprime la tâche (qui devient introuvable)."""
    client.post('/todos', json={'title': 'À supprimer'})
    resp = client.delete('/todos/1')
    assert resp.status_code == 200
    assert resp.get_json()['message'] == 'Todo deleted'

    # La tâche n'existe plus
    assert client.get('/todos/1').status_code == 404


def test_delete_todo_not_found(client):
    """DELETE /todos/<id> sur un id inexistant renvoie 404."""
    resp = client.delete('/todos/999')
    assert resp.status_code == 404
    assert 'error' in resp.get_json()
