# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import database as db

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Tableau de Bord - Direction", page_icon="📈", layout="wide")

st.title("📈 Tableau de Bord des Recommandations")
st.markdown("Vue synthétique de l'état d'avancement pour la Direction.")
st.divider()

# --- RÉCUPÉRATION DES DONNÉES ---
# Streamlit accède automatiquement au fichier database.py qui est dans le dossier parent
df = db.obtenir_recommandations()

if df.empty:
    st.info("Aucune donnée disponible pour générer le tableau de bord.")
else:
    # --- LES MÉTRIQUES CLÉS (KPI) ---
    total_recos = len(df)
    recos_realisees = len(df[df['statut'] == 'Réalisée'])
    recos_retard = len(df[df['statut'] == 'En retard'])
    recos_en_cours = len(df[df['statut'] == 'En cours'])
    
    taux_realisation = int((recos_realisees / total_recos) * 100) if total_recos > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total Recommandations", value=total_recos)
    col2.metric(label="Taux de Réalisation", value=f"{taux_realisation} %")
    col3.metric(label="✅ Réalisées", value=recos_realisees)
    col4.metric(label="🚨 En Retard", value=recos_retard, delta="- À clôturer" if recos_retard > 0 else None, delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- LES GRAPHIQUES ---
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        st.subheader("Répartition par Statut")
        # On compte le nombre de recommandations par statut
        statut_counts = df['statut'].value_counts()
        # On utilise le graphique en barre natif de Streamlit
        st.bar_chart(statut_counts)
        
    with col_graph2:
        st.subheader("Priorité des Recommandations")
        priorite_counts = df['priorite'].value_counts()
        st.bar_chart(priorite_counts, color="#FF4B4B")

    st.divider()
    
    # --- VUE DÉTAILLÉE PAR DIRECTION ---
    st.subheader("📊 Avancement par Direction / Responsable")
    
    # Petite manipulation Pandas pour séparer les responsables multiples (ex: "DSI, RH")
    df_responsables = df.assign(responsable=df['responsable'].str.split(', ')).explode('responsable')
    
    # Calcul du nombre de recos par direction et par statut
    repartition_direction = pd.crosstab(df_responsables['responsable'], df_responsables['statut'])
    
    # Affichage d'un tableau croisé dynamique propre
    st.dataframe(repartition_direction, use_container_width=True)