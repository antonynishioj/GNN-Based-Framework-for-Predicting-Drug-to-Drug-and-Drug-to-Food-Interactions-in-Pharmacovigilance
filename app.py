import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Load dataset
@st.cache_data
def load_data():
    # Replace 'drugbank_clean.csv' with your actual file path
    return pd.read_csv("drugbank_clean.csv")

# Build interaction graph with improved food matching
def build_interaction_graph_with_features(df, drugs, foods):
    G = nx.Graph()

    for drug in drugs:
        drug_data = df[df['name'].str.contains(drug, case=False, na=False)]
        st.write(f"Drug Data for '{drug}':", drug_data)  # Debugging output

        if not drug_data.empty:
            for _, row in drug_data.iterrows():
                # Add drug node with attributes
                G.add_node(drug, type="drug", 
                           pharmacodynamics=row['pharmacodynamics'],
                           pharmacokinetics=row['mechanism-of-action'],
                           side_effects=row['toxicity'],
                           molecular_structure=row['cas-number'])

                # Add food interactions with improved matching
                if pd.notna(row['food-interactions']):
                    interaction_text = row['food-interactions']
                    for food in foods:
                        if food.lower() in interaction_text.lower():  # Match food in description
                            severity = determine_severity(interaction_text)  # Get severity level
                            G.add_node(food, type="food", 
                                       composition=row.get('chemical-composition', "Unknown"),
                                       interaction_potential=interaction_text)
                            G.add_edge(drug, food, interaction=severity)
    return G

# Determine interaction severity
def determine_severity(interaction_text):
    if "severe" in interaction_text.lower() or "life-threatening" in interaction_text.lower():
        return "High"
    elif "moderate" in interaction_text.lower() or "caution" in interaction_text.lower():
        return "Medium"
    else:
        return "Low"

# Preprocessing: Match input drugs/foods with dataset
def preprocess_input(input_list, column, df):
    matched_items = []
    for item in input_list:
        matches = df[df[column].str.contains(item, case=False, na=False)]
        if not matches.empty:
            matched_items.append(item)
    return matched_items
    

# Visualize graph with detailed features
def visualize_graph_with_features(G):
    plt.figure(figsize=(14, 10))

    # Define node colors and attributes
    node_colors = []
    labels = {}
    for node, data in G.nodes(data=True):
        if data['type'] == "drug":
            node_colors.append("skyblue")
            labels[node] = f"Drug: {node}\nPharmacodynamics: {data['pharmacodynamics']}"
        else:
            node_colors.append("lightgreen")
            labels[node] = f"Food: {node}\nComposition: {data['composition']}"

    # Draw the graph
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, labels=labels, node_color=node_colors, node_size=3000, font_size=8)

    # Draw edge labels for interactions
    edge_labels = nx.get_edge_attributes(G, 'interaction')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    st.pyplot(plt)

# Generate safe consumption plan
def generate_safe_consumption_plan(df, drugs, foods):
    plan = []
    for drug in drugs:
        drug_data = df[df['name'].str.contains(drug, case=False, na=False)]
        if not drug_data.empty:
            for _, row in drug_data.iterrows():
                plan.append({
                    "Drug": row['name'],
                    "Pharmacodynamics": row['pharmacodynamics'],
                    "Suggested Timing": "Take with food" if "with food" in row['description'] else "Take without food",
                    "Foods to Avoid": row['food-interactions'] if pd.notna(row['food-interactions']) else "None"
                })
    return plan

# Streamlit App
st.title("Drug-Food Interaction Workflow with Features")

# Load data
st.write("Loading database...")
df = load_data()
st.success("Database loaded successfully!")

# Input Section
st.header("Input Data")
medicines = st.text_area("Enter Medicines (comma-separated):", placeholder="e.g., aspirin, metformin")
foods = st.text_area("Enter Foods (comma-separated):", placeholder="e.g., alcohol, high-fiber foods")

# Process Input and Build Graph
if st.button("Analyze Interactions"):
    drugs = [med.strip().lower() for med in medicines.split(",") if med.strip()]
    food_items = [food.strip().lower() for food in foods.split(",") if food.strip()]

    # Match input with database
    matched_drugs = preprocess_input(drugs, "name", df)
    matched_foods = preprocess_input(food_items, "food-interactions", df)

    # Debugging information
    st.write("Matched Drugs:", matched_drugs)
    st.write("Matched Foods:", matched_foods)

    if matched_drugs and matched_foods:
        # Build Interaction Graph
        G = build_interaction_graph_with_features(df, matched_drugs, food_items)

        # Check if graph has edges
        if G.number_of_edges() > 0:
            st.subheader("Interaction Graph with Features")
            visualize_graph_with_features(G)

            # Generate Safe Consumption Plan
            st.subheader("Safe Consumption Plan")
            plan = generate_safe_consumption_plan(df, matched_drugs, matched_foods)
            for item in plan:
                st.markdown(f"""
                - **Drug**: {item['Drug']}
                - **Pharmacodynamics**: {item['Pharmacodynamics']}
                - **Suggested Timing**: {item['Suggested Timing']}
                - **Foods to Avoid**: {item['Foods to Avoid']}
                """)
        else:
            st.warning("No interactions found in the graph. Please check your inputs.")
    else:
        st.warning("No valid drug or food interactions found.")
