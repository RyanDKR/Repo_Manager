import sqlite3
import pandas as pd

DB_NAME = "recommandations.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suivi_recos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rubrique TEXT,
            recommandation TEXT,
            responsable TEXT,
            statut TEXT,
            priorite TEXT,
            echeance DATE,
            avancement INTEGER,
            date_mise_en_place DATE,
            observation TEXT
        )
    ''')
    conn.commit()
    conn.close()

def ajouter_recommandation(rubrique, recommandation, responsable, statut, priorite, echeance, avancement, date_mise_en_place, observation):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO suivi_recos (rubrique, recommandation, responsable, statut, priorite, echeance, avancement, date_mise_en_place, observation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (rubrique, recommandation, responsable, statut, priorite, echeance, avancement, date_mise_en_place, observation))
    conn.commit()
    conn.close()

def obtenir_recommandations():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM suivi_recos", conn)
    conn.close()
    return df

def mettre_a_jour_recommandation(id_reco, rubrique, recommandation, responsable, statut, priorite, echeance, avancement, date_mise_en_place, observation):
    """La fonction a maintenant bien les 10 paramètres attendus (y compris id_reco)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE suivi_recos 
        SET rubrique=?, recommandation=?, responsable=?, statut=?, priorite=?, echeance=?, avancement=?, date_mise_en_place=?, observation=?
        WHERE id=?
    ''', (rubrique, recommandation, responsable, statut, priorite, echeance, avancement, date_mise_en_place, observation, id_reco))
    conn.commit()
    conn.close()

    # "DG", "IT", "DT", "DAF", "DCPC", "RH", "DC"