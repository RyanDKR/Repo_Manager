# pyrefly: ignore [missing-import]
import streamlit as st
import database as db
import pandas as pd
from datetime import date
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Charge les variables cachées du fichier .env
load_dotenv()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Suivi des Recommandations", page_icon="📊", layout="wide")

# --- FONCTION D'EXPORT EXCEL ---
def generer_excel_formate(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Synthèse des Recommandations')
        workbook = writer.book
        worksheet = writer.sheets['Synthèse des Recommandations']
        
        header_format = workbook.add_format({
            'bold': True, 'fg_color': '#2F5597', 'font_color': 'white', 'border': 1
        })
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, str(value).upper(), header_format)
            worksheet.set_column(col_num, col_num, 22)
            
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    return output.getvalue()

# --- NOUVEAU : FONCTION D'ENVOI D'EMAIL ---
def envoyer_notification(responsables_str, rubrique, type_action="Nouvelle"):
    """
    Prépare et envoie un email aux responsables concernés via SMTP.
    """
    # 1. Annuaire mis à jour avec le domaine de l'entreprise
    annuaire = {
        "Contrôle Permanent": "cyrille.fokam@afgassurances.cm",
        "Direction Générale": "theophile.tchio@afgassurances.cm", 
        "DSI": "clotaire.koungue@afgassurances.cm",               
        "Dir. Sinistres": "frederic.takou@afgassurances.cm",   
        "Ressources Humaines": "emilienne.kikolo@afgassurances.cm",
        "Finance": "katian.kone@afgassurances.cm",
        "Comité Médical": "theophile.misse@afgassurances.cm"
    }
    
    liste_resp = [r.strip() for r in responsables_str.split(",")]
    destinataires = [annuaire[r] for r in liste_resp if r in annuaire]
    
    if not destinataires:
        return False, "Aucune adresse email configurée pour ces responsables."

    # 2. Récupération ultra-sécurisée des identifiants via Streamlit Secrets
    try:
        smtp_server = st.secrets["SMTP_SERVER"]
        smtp_port = st.secrets["SMTP_PORT"]
        smtp_email = st.secrets["SMTP_EMAIL"]
        smtp_password = st.secrets["SMTP_PASSWORD"]
    except Exception as e:
        return False, "Les identifiants SMTP ne sont pas configurés dans les Secrets de Streamlit."

    # 3. Préparation du message
    sujet = f"[{type_action.upper()}] Action requise : Suivi des recommandations"
    corps = f"""Bonjour,

Une recommandation vous concernant a été mise à jour ou ajoutée par le Contrôle Permanent.

Thème : {rubrique}
Statut : {type_action}

Merci de vous connecter à l'application de suivi pour consulter les détails.

Cordialement,
Le Contrôle Permanent
    """
    
    msg = MIMEMultipart()
    msg['From'] = smtp_email
    msg['To'] = ", ".join(destinataires)
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps, 'plain'))

    # 4. Connexion et Envoi réel
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Sécurise la connexion
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True, f"Email envoyé avec succès à {', '.join(destinataires)}"
    except Exception as e:
        return False, f"Erreur de connexion SMTP : {str(e)}"

def main():
    db.init_db()
    st.title("📊 Application de Suivi des Recommandations")
    
    liste_responsables = ["DG", "IT", "DT", "DAF", "DCPC", "RH", "DC"]
    liste_statuts = ["Non démarrée", "En cours", "Réalisée", "En retard"]
    liste_priorites = ["Moyenne", "Haute", "Critique"]

    df_recos = db.obtenir_recommandations()
    
    if df_recos.empty:
        st.info("Aucune recommandation enregistrée pour le moment. Utilisez le formulaire sur la gauche pour commencer.")
    else:
        st.subheader("🔍 Recherche et Filtres")
        col_rech1, col_rech2, col_rech3 = st.columns(3)
        
        recherche_texte = col_rech1.text_input("Mot-clé (Thème, Reco, Observation...)")
        filtre_statut = col_rech2.multiselect("Filtrer par Statut", liste_statuts)
        filtre_responsable = col_rech3.multiselect("Filtrer par Responsable", liste_responsables)
        
        df_filtre = df_recos.copy()
        
        if recherche_texte:
            masque_texte = (
                df_filtre['rubrique'].astype(str).str.contains(recherche_texte, case=False, na=False) |
                df_filtre['recommandation'].astype(str).str.contains(recherche_texte, case=False, na=False) |
                df_filtre['observation'].astype(str).str.contains(recherche_texte, case=False, na=False)
            )
            df_filtre = df_filtre[masque_texte]
            
        if filtre_statut:
            df_filtre = df_filtre[df_filtre['statut'].isin(filtre_statut)]
            
        if filtre_responsable:
            masque_resp = df_filtre['responsable'].apply(lambda x: any(resp in str(x) for resp in filtre_responsable))
            df_filtre = df_filtre[masque_resp]

        st.divider()

        total_recos = len(df_filtre)
        recos_realisees = len(df_filtre[df_filtre['statut'] == 'Réalisée'])
        recos_retard = len(df_filtre[df_filtre['statut'] == 'En retard'])
        taux_realisation = int((recos_realisees / total_recos) * 100) if total_recos > 0 else 0
        
        st.markdown("### 📈 Tableau de Bord")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="Total Recommandations", value=total_recos)
        col2.metric(label="Taux de Réalisation", value=f"{taux_realisation} %")
        col3.metric(label="Réalisées", value=recos_realisees)
        col4.metric(label="En Retard", value=recos_retard, delta="- À surveiller" if recos_retard > 0 else None, delta_color="inverse")
        
        st.divider() 
        
        st.subheader("📋 Liste des recommandations")
        if df_filtre.empty:
            st.warning("Aucune recommandation ne correspond à vos critères de recherche.")
        else:
            st.dataframe(df_filtre, use_container_width=True, hide_index=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            excel_data = generer_excel_formate(df_filtre)
            st.download_button(
                label="📥 Télécharger le rapport Excel (Filtré)",
                data=excel_data,
                file_name=f"Suivi_Recommandations_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    mode = st.sidebar.radio("Que souhaitez-vous faire ?", ["➕ Nouvelle Recommandation", "✏️ Modifier une Recommandation"])
    st.sidebar.divider()

    if mode == "➕ Nouvelle Recommandation":
        st.sidebar.header("Créer une fiche")
        with st.sidebar.form(key="form_ajout", clear_on_submit=True):
            rubrique = st.text_input("Rubrique / Thème *")
            recommandation = st.text_area("Recommandation *")
            responsables = st.multiselect("Responsable(s) *", liste_responsables)
            statut = st.selectbox("Statut", liste_statuts)
            priorite = st.selectbox("Priorité", liste_priorites)
            echeance = st.date_input("Échéance", value=date.today())
            date_mise_en_place = st.date_input("Date de mise en place", value=date.today())
            avancement = st.slider("% Avancement", min_value=0, max_value=100, value=0, step=5)
            observation = st.text_area("Observations (Optionnel)")
            
            # NOUVEAU : Case à cocher pour envoyer le mail
            envoyer_mail = st.checkbox("✉️ Notifier les responsables par e-mail")
            
            if st.form_submit_button("Enregistrer"):
                if not rubrique.strip() or not recommandation.strip() or not responsables:
                    st.sidebar.error("❌ Les champs avec * sont obligatoires.")
                else:
                    db.ajouter_recommandation(rubrique, recommandation, ", ".join(responsables), statut, priorite, echeance, avancement, date_mise_en_place, observation)
                    
                    # Logique d'envoi d'email
                    if envoyer_mail:
                        succes, msg = envoyer_notification(", ".join(responsables), rubrique, "Création")
                        if succes:
                            st.sidebar.success(f"✅ Recommandation ajoutée et {msg}")
                        else:
                            st.sidebar.warning(f"✅ Recommandation ajoutée, mais échec de l'email : {msg}")
                    else:
                        st.sidebar.success("✅ Recommandation ajoutée (sans notification).")
                        
                    st.rerun()

    elif mode == "✏️ Modifier une Recommandation":
        st.sidebar.header("Mettre à jour une fiche")
        
        if df_recos.empty:
            st.sidebar.info("Aucune donnée à modifier.")
        else:
            options_recos = df_recos.apply(lambda row: f"N°{row['id']} - {row['rubrique']}", axis=1).tolist()
            choix_reco = st.sidebar.selectbox("Sélectionnez la ligne à modifier :", options_recos)
            
            if choix_reco:
                id_selectionne = int(choix_reco.split(" - ")[0].replace("N°", ""))
                donnees_actuelles = df_recos[df_recos['id'] == id_selectionne].iloc[0]
                
                resp_actuels = [r.strip() for r in str(donnees_actuelles['responsable']).split(",")] if pd.notna(donnees_actuelles['responsable']) else []
                statut_index = liste_statuts.index(donnees_actuelles['statut']) if donnees_actuelles['statut'] in liste_statuts else 0
                priorite_index = liste_priorites.index(donnees_actuelles['priorite']) if donnees_actuelles['priorite'] in liste_priorites else 0
                date_actuelle = pd.to_datetime(donnees_actuelles['echeance']).date() if pd.notna(donnees_actuelles['echeance']) else date.today()
                
                date_mep_actuelle = pd.to_datetime(donnees_actuelles['date_mise_en_place']).date() if 'date_mise_en_place' in donnees_actuelles and pd.notna(donnees_actuelles['date_mise_en_place']) else date.today()
                obs_actuelle = donnees_actuelles['observation'] if 'observation' in donnees_actuelles and pd.notna(donnees_actuelles['observation']) else ""
                
                with st.sidebar.form(key="form_modif"):
                    rubrique = st.text_input("Rubrique / Thème *", value=donnees_actuelles['rubrique'])
                    recommandation = st.text_area("Recommandation *", value=donnees_actuelles['recommandation'])
                    
                    valeurs_defaut_resp = [r for r in resp_actuels if r in liste_responsables]
                    responsables = st.multiselect("Responsable(s) *", liste_responsables, default=valeurs_defaut_resp)
                    
                    statut = st.selectbox("Statut", liste_statuts, index=statut_index)
                    priorite = st.selectbox("Priorité", liste_priorites, index=priorite_index)
                    echeance = st.date_input("Échéance", value=date_actuelle)
                    
                    date_mise_en_place = st.date_input("Date de mise en place", value=date_mep_actuelle)
                    avancement = st.slider("% Avancement", min_value=0, max_value=100, value=int(donnees_actuelles['avancement']), step=5)
                    observation = st.text_area("Observations", value=obs_actuelle)
                    
                    # NOUVEAU : Case à cocher pour la modification
                    envoyer_mail = st.checkbox("✉️ Alerter les responsables de la mise à jour")
                    
                    if st.form_submit_button("Mettre à jour"):
                        if not rubrique.strip() or not recommandation.strip() or not responsables:
                            st.sidebar.error("❌ Les champs avec * sont obligatoires.")
                        else:
                            db.mettre_a_jour_recommandation(
                                id_selectionne, rubrique, recommandation, ", ".join(responsables), 
                                statut, priorite, echeance, avancement, date_mise_en_place, observation
                            )
                            
                            if envoyer_mail:
                                succes, msg = envoyer_notification(", ".join(responsables), rubrique, "Mise à jour")
                                if succes:
                                    st.sidebar.success(f"✅ Mise à jour effectuée et {msg}")
                                else:
                                    st.sidebar.warning(f"✅ Mise à jour effectuée, mais échec de l'email : {msg}")
                            else:
                                st.sidebar.success("✅ Mise à jour effectuée (sans notification).")
                            st.rerun()

if __name__ == '__main__':
    main()