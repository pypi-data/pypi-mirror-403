import streamlit as st
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex

# 1. Konfigurácia stránky - nastavíme široký režim
st.set_page_config(page_title="Mongo Structure Viewer", layout="wide")


# 2. Definícia štýlov (CSS), aby to vyzeralo ako tvoj Tkinter
def local_css(bg_color):
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {bg_color};
        }}
        .tile-container {{
            background-color: white;
            border: 1px solid #C0C0C0;
            border-radius: 2px;
            padding: 10px;
            margin: 10px 0px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }}
        .tile-title {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14pt;
            font-weight: bold;
            color: #333333;
            border-bottom: 1px solid #EEEEEE;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }}
        .tile-body {{
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
            color: #000000;
            white-space: pre-wrap;
        }}
        </style>
    """, unsafe_allow_html=True)


# 3. Logika pre farby (rovnaká ako v tvojom kóde)
PASTEL_PALETTE = sns.color_palette("pastel")
PASTEL_HEX_PALETTE = [to_hex(c) for c in PASTEL_PALETTE]


def get_collection_color(collection_name, all_collections):
    idx = list(all_collections).index(collection_name) % len(PASTEL_HEX_PALETTE)
    return PASTEL_HEX_PALETTE[idx]


# 4. Hlavná funkcia aplikácie
def main(structures):
    st.title("Mongo Structure Viewer")

    # Header - Výber kolekcie
    all_collections = list(structures.keys())
    selected = st.selectbox("Vyberte kolekciu", all_collections)

    if selected:
        current_color = get_collection_color(selected, all_collections)
        local_css(current_color)  # Aplikujeme farbu pozadia

        collection_data = structures[selected]
        chart_labels = []
        chart_counts = []

        # Príprava mriežky pre dlaždice (3 stĺpce sú ideálne pre screen)
        st.subheader(f"Dokumenty v: {selected}")
        cols = st.columns(3)

        for i, struct in enumerate(collection_data):
            label_name = next((k for k in struct.keys() if k != "count"), "Document")
            chart_labels.append(label_name)
            chart_counts.append(struct['count'])

            # Vytvorenie textu tela dlaždice
            fields = struct[label_name]
            body_text = "\n".join([f"{field}: {types}" for field, types in fields.items()])

            # Vykreslenie dlaždice do stĺpca
            with cols[i % 3]:
                st.markdown(f"""
                    <div class="tile-container">
                        <div class="tile-title">{label_name} (Count: {struct['count']})</div>
                        <div class="tile-body">{body_text}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.divider()

        # 5. Graf (Matplotlib) - presne podľa tvojho dizajnu
        st.subheader("Frekvencia schém")
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor('#FAFAFA')
        ax.set_facecolor('#FAFAFA')

        x_pos = np.arange(len(chart_labels))
        bars = ax.bar(x_pos, chart_counts, color=current_color, alpha=0.8, edgecolor="#888888", linewidth=0.5)

        ax.set_ylabel('Frequency', fontsize=9)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(chart_labels, rotation=30, ha='right', fontsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height, f'{int(height)}', ha='center', va='bottom', fontsize=8)

        st.pyplot(fig)


# --- SPUSTENIE ---
if __name__ == "__main__":
    # Sem vlož tvoje reálne dáta namiesto tohto testu
    dummy_data = {
        "Collection_A": [
            {"User": {"name": "string", "age": "int"}, "count": 50},
            {"Admin": {"name": "string", "role": "string", "level": "int"}, "count": 10}
        ],
        "Collection_B": [
            {"Product": {"id": "oid", "price": "float"}, "count": 1000}
        ]
    }
    main(dummy_data)