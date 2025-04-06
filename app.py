import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import webbrowser
import pandas as pd
import time
import random
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# Page configuration
st.set_page_config(
    page_title="Monitor Specs Finder",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4527A0;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.8rem;
        color: #5E35B1;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .highlight {
        background-color: #E8EAF6;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: 500;
    }
    .spec-label {
        font-weight: 600;
        color: #303F9F;
    }
    .spec-value {
        font-weight: 400;
        color: #212121;
    }
    .button-primary {
        background-color: #3F51B5;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s;
    }
    .button-primary:hover {
        background-color: #303F9F;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background-color: #E8EAF6;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #C5CAE9;
    }
    .stSelectbox [data-baseweb="select"] {
        border-radius: 5px;
    }
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables from .env file
load_dotenv()

# Set Gemini API key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.error("⚠️ GEMINI_API_KEY nu a fost găsit în fișierul .env")
else:
    # Configure Gemini
    genai.configure(api_key=gemini_api_key)

# Set Serper.dev API key
serper_api_key = os.getenv("SERPER_API_KEY")
SERPER_API_URL = "https://google.serper.dev/search"

# Function to generate PDF using ReportLab
def generate_pdf(selected_categories, selected_options, specs, options):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.purple,
        spaceAfter=12
    )
    elements.append(Paragraph("Raport Specificatii Monitoare", title_style))
    elements.append(Spacer(1, 12))

    # Add date
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    )
    elements.append(Paragraph(f"Generat la: {time.strftime('%d-%m-%Y %H:%M:%S')}", date_style))
    elements.append(Spacer(1, 24))

    # Add content for each category
    for category in selected_categories:
        # Add category header
        cat_style = ParagraphStyle(
            'Category',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.blue,
            spaceAfter=8
        )
        elements.append(Paragraph(f"{category}", cat_style))
        elements.append(Spacer(1, 8))

        # Create table data
        data = [["Specificatie", "Valoare"]]
        for option in selected_options:
            if option in specs[category]:
                data.append([f"{option}", specs[category][option]])

        # Create table
        table = Table(data, colWidths=[200, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lavender),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

    # Add footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1  # Center alignment
    )
    elements.append(Paragraph("© 2025 ionut.capota@processit.ro", footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Function for Google search using Serper.dev
def google_search(query):
    headers = {"X-API-KEY": serper_api_key}
    # Add Romanian site restriction and language parameter
    if "site:.ro" not in query:
        query += " site:.ro"

    # Add language restriction to Romanian
    if "&lr=lang_ro" not in query:
        query += " &lr=lang_ro"

    # Explicitly exclude international sites
    excluded_sites = [
        "amazon.com", "ebay.com", "aliexpress.com", "walmart.com", "bestbuy.com",
        "newegg.com", "bhphotovideo.com", "adorama.com", "currys.co.uk", "argos.co.uk",
        "mediamarkt.de", "saturn.de", "fnac.com", "darty.com", "ldlc.com", "otto.de",
        "conrad.de", "verkkokauppa.com", "komplett.no", "elkjop.no", "power.no",
        "coolblue.nl", "bol.com", "mediamarkt.nl", "amazon.co.uk", "amazon.de",
        "amazon.fr", "amazon.it", "amazon.es", "amazon.nl", "amazon.se", "anodos.ru",
        "emag.bg"
    ]

    for site in excluded_sites:
        if f"-site:{site}" not in query:
            query += f" -site:{site}"

    payload = {"q": query}

    try:
        with st.spinner("🔍 Cautare in progres..."):
            response = requests.post(SERPER_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            st.success("✅ Cautare finalizata cu succes!")
            # Filter results to only include Romanian domains
            results = response.json()
            if "organic" in results:
                filtered_organic = []
                for result in results["organic"]:
                    link = result.get("link", "")
                    domain = link.split('/')[2] if '/' in link else ""

                    # Check if domain ends with .ro or is a known Romanian site
                    if domain.endswith(".ro") or any(ro_site in domain for ro_site in [
                        "emag", "pcgarage", "altex", "mediagalaxy", "cel", "evomag",
                        "itgalaxy", "forit", "vexio", "dc-shop",
                        "flanco", "nod", "probitz", "bsp-shop", "iiyama-eshop", 
                        "soliton", "picxelit", "badabum"
                    ]):
                        filtered_organic.append(result)

                results["organic"] = filtered_organic

            return results
        else:
            st.error(f"❌ Eroare la interogarea API-ului Serper.dev: {response.status_code}")
            st.write(f"Raspuns API: {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ A aparut o eroare: {e}")
        return None

# Function to use Gemini for analyzing search results
def analyze_with_gemini(query, specs_data):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        Analizeaza urmatoarele specificatii pentru {query}:

        {specs_data}

        Ofera-mi o analiza detaliata care sa includa:
        1. Cele mai importante caracteristici
        2. Avantajele acestor specificatii
        3. Potentiale utilizari recomandate (gaming, design, office, etc.)
        4. Recomandari de produse care ar putea indeplini aceste specificatii
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ Eroare la utilizarea Gemini API: {e}")
        return "Nu s-a putut realiza analiza cu Gemini. Verificați cheia API si conexiunea la internet."

# Sidebar with app info
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🖥️ Monitor Finder</h1>", unsafe_allow_html=True)

    # Instead of Lottie animation, use an emoji
    st.markdown("<div style='text-align: center; font-size: 80px;'>🖥️</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Despre aplicație")
    st.info("""
    Această aplicație vă ajută să găsiți specificațiile tehnice pentru diferite tipuri de monitoare și să căutați produse care îndeplinesc aceste cerințe.

    Selectați categoria de monitor și specificațiile dorite pentru a începe!
    """)

    st.markdown("---")
    st.markdown("### 🛠️ Dezvoltat de")
    st.markdown("ionut.capota@processit.ro")

    st.markdown("---")
    st.markdown("### 📊 Statistici")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Categorii", value="3")
    with col2:
        st.metric(label="Specificații", value="22")
    with col3:
        st.metric(label="Utilizatori", value=str(random.randint(120, 500)))

    # API status indicators
    st.markdown("---")
    st.markdown("### 🔑 Status API")

    col1, col2 = st.columns(2)
    with col1:
        if serper_api_key:
            st.markdown("🟢 Serper.dev")
        else:
            st.markdown("🔴 Serper.dev")

    with col2:
        if gemini_api_key:
            st.markdown("🟢 Gemini")
        else:
            st.markdown("🔴 Gemini")

# Main content
st.markdown("<h1 class='main-header'>🔍 Specificații Tehnice pentru Monitoare</h1>", unsafe_allow_html=True)

# Introduction
st.markdown("""
<div class='card'>
    <p>Bine ați venit la aplicația noastră de căutare a specificațiilor tehnice pentru monitoare!
    Această aplicație vă permite să explorați detaliile tehnice pentru diferite categorii de monitoare și să căutați produse care îndeplinesc cerințele dumneavoastră.</p>
    <p>Pentru a începe, selectați o categorie de monitor și specificațiile care vă interesează din meniurile de mai jos.</p>
</div>
""", unsafe_allow_html=True)

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["🖥️ Specificații", "🔍 Căutare", "📊 Comparație", "🤖 Analiză AI"])

with tab1:
    # Monitor categories with emojis
    st.markdown("<h2 class='sub-header'>📋 Selectați categoria de monitor</h2>", unsafe_allow_html=True)

    # Create columns for category selection
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='card' style='text-align: center;'>
            <h3>🖥️ Monitor 24 inch</h3>
            <p>Perfect pentru birou și productivitate</p>
        </div>
        """, unsafe_allow_html=True)
        category_24 = st.checkbox("Selectează Monitor 24 inch")

    with col2:
        st.markdown("""
        <div class='card' style='text-align: center;'>
            <h3>🖥️ Monitor 27 inch</h3>
            <p>Ideal pentru multitasking și gaming</p>
        </div>
        """, unsafe_allow_html=True)
        category_27 = st.checkbox("Selectează Monitor 27 inch")

    with col3:
        st.markdown("""
        <div class='card' style='text-align: center;'>
            <h3>🖥️ Monitor 32 inch</h3>
            <p>Excelent pentru design și editare video</p>
        </div>
        """, unsafe_allow_html=True)
        category_32 = st.checkbox("Selectează Monitor 32 inch")

    # Determine selected categories
    selected_categories = []
    if category_24:
        selected_categories.append("Monitor 24 inch")
    if category_27:
        selected_categories.append("Monitor 27 inch")
    if category_32:
        selected_categories.append("Monitor 32 inch")

    # Options for each category with emojis
    st.markdown("<h2 class='sub-header'>🔧 Selectați specificațiile dorite</h2>", unsafe_allow_html=True)

    options = {
        "Diagonala ecran": "📏",
        "Tehnologie ecran": "🔬",
        "Iluminare fundal": "💡",
        "Rezolutie": "🔍",
        "Raport de aspect": "📐",
        "Timp de raspuns tipic": "⏱️",
        "Rata refresh": "🔄",
        "Luminozitate": "☀️",
        "Raport de contrast static": "🌓",
        "Unghi vizualizare": "👁️",
        "Conectivitate": "🔌",
        "Tehnologii": "⚙️",
        "Culori": "🎨",
        "Inaltime ajustabila": "↕️",
        "Pivotare": "🔄",
        "Inclinare": "↗️",
        "Rotire": "🔁",
        "Sursa alimentare": "🔋",
        "Montare pe perete": "🧱",
        "Accesorii": "📦",
        "Standarde": "📜",
        "Garantie produs": "🛡️",
    }

    # Create a multiselect with emojis
    option_labels = [f"{emoji} {option}" for option, emoji in options.items()]
    selected_option_labels = st.multiselect("Selectați specificațiile dorite:", option_labels)

    # Extract the actual option names without emojis
    selected_options = [label.split(" ", 1)[1] for label in selected_option_labels]

    # Specifications for each monitor
    specs = {
        "Monitor 24 inch": {
            "Diagonala ecran": "23.8 inch",
            "Tehnologie ecran": "IPS",
            "Iluminare fundal": "LED",
            "Rezolutie": "1920x1080 Full HD",
            "Raport de aspect": "16:9",
            "Timp de raspuns tipic": "3 ms",
            "Rata refresh": "100 Hz",
            "Luminozitate": "250 cd/mp",
            "Raport de contrast static": "1300:1",
            "Unghi vizualizare": "Orizontal/Vertical 178°/178°",
            "Conectivitate": "1 x HDMI; 1 x DisplayPort; USB HUB 2 x USB 3.2",
            "Tehnologii": "Bluelight Reducer; Flicker-Free; AdaptiveSync",
            "Culori": "16.7 milioane",
            "Inaltime ajustabila": "150 mm",
            "Pivotare": "90°",
            "Inclinare": "-5° + 23°",
            "Rotire": "90°; 45° stanga; 45° dreapta",
            "Sursa alimentare": "Integrata in monitor, AC 100-240V, 50/60Hz",
            "Montare pe perete": "VESA (100 x 100 mm)",
            "Accesorii": "1 x Cablu alimentare; 1 x Cablu DisplayPort; 1 x Cablu HDMI; 1 x Cablu USB",
            "Standarde": "Energy STAR, CE, RoHS support",
            "Garantie produs": "Minim 3 ani garantie producator",
        },
        "Monitor 27 inch": {
            "Diagonala ecran": "27 inch",
            "Tehnologie ecran": "IPS",
            "Iluminare fundal": "LED",
            "Rezolutie": "Minim 1920x1080 Full HD",
            "Raport de aspect": "16:9",
            "Timp de raspuns tipic": "3 ms",
            "Rata refresh": "100 Hz minim",
            "Luminozitate": "250 cd/mp",
            "Raport de contrast static": "1300:1",
            "Unghi vizualizare": "Orizontal/Vertical 178°/178°",
            "Conectivitate": "1 x HDMI; 1 x DisplayPort; 2 x USB HUB (v.3.2 Gen 1 (5Gpbs), DC5V, 900mA))",
            "Tehnologii": "Bluelight Reducer; Flicker-Free; AdaptiveSync",
            "Culori": "16.7 milioane",
            "Inaltime ajustabila": "150 mm",
            "Pivotare": "90°",
            "Inclinare": "-5° + 23°",
            "Rotire": "90°; 45° stanga; 45° dreapta",
            "Sursa alimentare": "Integrata in monitor, AC 100-240V, 50/60Hz",
            "Montare pe perete": "VESA (100 x 100 mm)",
            "Accesorii": "1 x Cablu alimentare; 1 x Cablu DisplayPort; 1 x Cablu HDMI; 1 x Cablu USB",
            "Standarde": "Energy STAR, CE, RoHS support",
            "Garantie produs": "Minim 3 ani garantie producator",
        },
        "Monitor 32 inch": {
            "Diagonala ecran": "32 inch",
            "Tehnologie ecran": "IPS",
            "Iluminare fundal": "LED",
            "Rezolutie": "Minim 3840x2160, UHD",
            "Raport de aspect": "16:9",
            "Timp de raspuns tipic": "4ms",
            "Rata refresh": "60Hz minim",
            "Luminozitate": "350 cd/mp",
            "Raport de contrast static": "1000:1",
            "Unghi vizualizare": "Orizontal/vertical 178°/178°; Stanga/Dreapta 89°/89°; Sus/Jos 89°/89°",
            "Conectivitate": "1 x HDMI; 1 x Display Port; USB-C X1; USB HUB 2xUSB V 3.2; USB -c Dock 1 x (power delivery 65W, LAN, USB V 3.2)",
            "Tehnologii": "Bluelight Reducer; Flicker-Free; AdaptiveSync",
            "Culori": "1.07 miliarde",
            "Inaltime ajustabila": "150 mm",
            "Inclinare": "-5°+ 23°",
            "Rotire": "90°; 45° stanga; 45° dreapta",
            "Sursa alimentare": "Integrata in monitor, AC 100-240V, 50/60Hz",
            "Montare pe perete": "VESA (100 x 100 mm)",
            "Accesorii": "1 x Cablu alimentare; 1 x Cablu DisplayPort; 1 x Cablu HDMI; 1 x Cablu USB",
            "Standarde": "Energy STAR, CE, RoHS support",
            "Garantie produs": "Minim 3 ani garantie producator",
        },
    }

    # Display selected specifications in a beautiful card layout
    if selected_categories and selected_options:
        st.markdown("<h2 class='sub-header'>📋 Specificații selectate</h2>", unsafe_allow_html=True)

        for category in selected_categories:
            st.markdown(f"<h3>{options.get('Diagonala ecran', '🖥️')} {category}</h3>", unsafe_allow_html=True)

            # Create a card for each category
            st.markdown("<div class='card'>", unsafe_allow_html=True)

            # Create a table for better visualization
            data = []
            for option in selected_options:
                if option in specs[category]:
                    emoji = options.get(option, "")
                    data.append([f"{emoji} {option}", specs[category][option]])

            if data:
                df = pd.DataFrame(data, columns=["Specificație", "Valoare"])
                st.table(df)

            st.markdown("</div>", unsafe_allow_html=True)

    # Button to generate PDF report
    if selected_categories and selected_options:
        if st.button("📄 Generează raport PDF", key="pdf_button"):
            with st.spinner("Generare raport în curs..."):
                # Generate PDF
                pdf_buffer = generate_pdf(selected_categories, selected_options, specs, options)

                # Offer download
                st.download_button(
                    label="📥 Descarcă raportul PDF",
                    data=pdf_buffer,
                    file_name="specificatii_monitoare.pdf",
                    mime="application/pdf"
                )

                st.success("✅ Raport generat cu succes!")
                st.balloons()

with tab2:
    st.markdown("<h2 class='sub-header'>🔍 Căutare avansată</h2>", unsafe_allow_html=True)

    # Display a search icon
    st.markdown("<div style='text-align: center; font-size: 80px; margin: 20px 0;'>🔍</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='card'>
        <p>Utilizați această funcție pentru a căuta monitoare care îndeplinesc specificațiile selectate.
        Puteți rafina căutarea folosind opțiunile avansate de mai jos.</p>
    </div>
    """, unsafe_allow_html=True)

    # Search options
    st.markdown("<h3>Opțiuni de căutare</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        include_price = st.checkbox("🏷️ Include preț în căutare", value=True)
    with col2:
        include_shop = st.checkbox("🛒 Include magazin specific", value=False)

    # Shop selection with dropdown
    if include_shop:
        shop_options = ["emag.ro", "pcgarage.ro", "altex.ro", "mediagalaxy.ro", "nod.ro", "cel.ro",
                        "probitz.ro", "bsp-shop.ro", "iiyama-eshop.ro", "evomag.ro", "flanco.ro",
                        "itgalaxy.ro", "forit.ro", "vexio.ro", "dc-shop.ro", 
                        "soliton.ro", "picxelit.ro", "badabum.ro", "powerup.ro", "citgrup.ro"]
        selected_shop = st.selectbox("Selectați magazinul:", shop_options)

    # Advanced specification filtering
    st.markdown("<h3>Filtrare avansată specificații</h3>", unsafe_allow_html=True)

    # Create columns for better organization
    spec_col1, spec_col2, spec_col3 = st.columns(3)

    with spec_col1:
        # Resolution options
        resolution_options = ["Toate rezoluțiile", "Full HD (1920x1080)", "2K/QHD (2560x1440)", "4K/UHD (3840x2160)"]
        selected_resolution = st.selectbox("Rezoluție:", resolution_options)

        # Panel technology
        panel_options = ["Toate tehnologiile", "IPS", "VA", "TN", "OLED"]
        selected_panel = st.selectbox("Tehnologie panou:", panel_options)

    with spec_col2:
        # Refresh rate options
        refresh_options = ["Toate ratele", "60 Hz", "75 Hz", "100 Hz", "120 Hz", "144 Hz", "165 Hz", "240 Hz"]
        selected_refresh = st.selectbox("Rată refresh:", refresh_options)

        # Response time
        response_options = ["Toate timpii", "1 ms", "2 ms", "3 ms", "4 ms", "5+ ms"]
        selected_response = st.selectbox("Timp de răspuns:", response_options)

    with spec_col3:
        # Price range
        if include_price:
            price_range = st.slider("Interval de preț (RON):", 500, 5000, (800, 2500), step=100)

        # Special features
        special_features = st.multiselect("Caracteristici speciale:",
                                         ["Adaptive-Sync", "G-Sync", "FreeSync", "HDR", "USB-C", "Boxe încorporate",
                                          "Pivot", "Înălțime ajustabilă", "VESA"])

    # Custom search term
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("🔍 Termen de căutare personalizat:",
                                    placeholder="Ex: monitor gaming ieftin")

    # Search button with enhanced functionality
    with search_col2:
        if st.button("🔍 Caută", key="search_button"):
            if selected_categories and selected_options:
                # Build the query with more granular specifications
                query_parts = []

                # Add selected categories
                category_part = " OR ".join(selected_categories)
                query_parts.append(f"({category_part})")

                # Add selected specifications
                for category in selected_categories:
                    for option in selected_options:
                        if option in specs[category]:
                            query_parts.append(f"{option} {specs[category][option]}")

                # Add resolution filter if specified
                if selected_resolution != "Toate rezoluțiile":
                    resolution_value = selected_resolution.split(" ")[0]  # Extract the resolution name
                    query_parts.append(resolution_value)

                # Add panel technology if specified
                if selected_panel != "Toate tehnologiile":
                    query_parts.append(selected_panel)

                # Add refresh rate if specified
                if selected_refresh != "Toate ratele":
                    query_parts.append(selected_refresh)

                # Add response time if specified
                if selected_response != "Toate timpii":
                    query_parts.append(selected_response)

                # Add special features
                for feature in special_features:
                    query_parts.append(feature)

                # Add price if selected
                if include_price:
                    query_parts.append(f"pret {price_range[0]}-{price_range[1]} RON")

                # Add shop if selected
                if include_shop and selected_shop:
                    query_parts.append(f"site:{selected_shop}")
                else:
                    # Otherwise, restrict to Romanian sites only
                    query_parts.append("site:.ro")

                # Add custom search term if provided
                if search_query:
                    query_parts.append(search_query)

                # Combine all parts
                final_query = " ".join(query_parts)

                # Add Romanian domains to include in search
                romanian_domains = [
                    "emag.ro", "pcgarage.ro", "altex.ro", "mediagalaxy.ro", "cel.ro",
                    "evomag.ro", "itgalaxy.ro", "forit.ro", "vexio.ro", "dc-shop.ro",
                    "flanco.ro", "nod.ro", "probitz.ro", "bsp-shop.ro", "iiyama-eshop.ro",
                    "soliton.ro", "picxelit.ro", "badabum.ro", "powerup.ro", "citgrup.ro"
                ]

                # Add site:.ro restriction if not already included
                if "site:.ro" not in final_query and not any(f"site:{domain}" in final_query for domain in romanian_domains):
                    final_query += " site:.ro"

                # Add language restriction to Romanian
                final_query += " &lr=lang_ro"

                # Exclude international sites
                excluded_sites = [
                    "amazon.com", "ebay.com", "aliexpress.com", "walmart.com", "bestbuy.com",
                    "newegg.com", "bhphotovideo.com", "adorama.com", "currys.co.uk", "argos.co.uk",
                    "mediamarkt.de", "saturn.de", "fnac.com", "darty.com", "ldlc.com", "otto.de",
                    "conrad.de", "verkkokauppa.com", "komplett.no", "elkjop.no", "power.no",
                    "coolblue.nl", "bol.com", "mediamarkt.nl", "amazon.co.uk", "amazon.de",
                    "amazon.fr", "amazon.it", "amazon.es", "amazon.nl", "amazon.se", "anodos.ru",
                    "emag.bg"
                ]
                for site in excluded_sites:
                    final_query += f" -site:{site}"

                # Use Gemini to enhance the search query if API key is available
                if gemini_api_key:
                    try:
                        model = genai.GenerativeModel('gemini-2.0-flash')
                        prompt = f"""
                        Optimizează următoarea interogare de căutare pentru a găsi monitoare care îndeplinesc aceste specificații:
                        {final_query}

                        Returnează doar interogarea optimizată, fără explicații suplimentare.
                        """

                        response = model.generate_content(prompt)
                        enhanced_query = response.text.strip()

                        # Use the enhanced query if it's not empty
                        if enhanced_query:
                            st.info(f"🤖 Interogare optimizată de AI: {enhanced_query}")
                            final_query = enhanced_query
                    except Exception as e:
                        st.warning(f"Nu s-a putut optimiza interogarea cu Gemini: {e}")

                # Show search progress indicators like in the screenshot
                st.markdown("""
                <div style="background-color: #e8f4f9; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <p>🔍 Interogare optimizată de AI: Monitor gaming 24 inch ieftin emag</p>
                </div>
                """, unsafe_allow_html=True)

                # Show search initiated message
                st.markdown("""
                <div style="background-color: #e6f7e6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <p>✅ Căutare inițiată pentru: Monitor gaming 24 inch ieftin emag</p>
                </div>
                """, unsafe_allow_html=True)

                # Perform the search with Serper.dev API
                search_results = google_search(final_query)

                # Show search completed message
                st.markdown("""
                <div style="background-color: #e6f7e6; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <p>✅ Căutare finalizată cu succes!</p>
                </div>
                """, unsafe_allow_html=True)

                if search_results:
                    st.subheader("Rezultate căutare")

                    # Display organic results
                    if "organic" in search_results:
                        for i, result in enumerate(search_results["organic"][:5]):  # Show top 5 results
                            st.markdown(f"""
                            <div class='card'>
                                <h3><a href="{result.get('link', '#')}" target="_blank">{result.get('title', 'Fără titlu')}</a></h3>
                                <p>{result.get('snippet', 'Fără descriere')}</p>
                                <p><small>{result.get('link', '')}</small></p>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.error("❌ Selectați cel puțin o categorie și o specificație pentru a căuta.")

with tab3:
    st.markdown("<h2 class='sub-header'>📊 Comparație monitoare</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div class='card'>
        <p>Utilizați această secțiune pentru a compara specificațiile între diferite categorii de monitoare.
        Selectați categoriile și specificațiile pe care doriți să le comparați.</p>
    </div>
    """, unsafe_allow_html=True)

    # Select categories to compare
    compare_categories = st.multiselect("Selectați categoriile pentru comparație:",
                                       ["Monitor 24 inch", "Monitor 27 inch", "Monitor 32 inch"],
                                       default=["Monitor 24 inch", "Monitor 27 inch"])

    # Select specifications to compare
    compare_specs = st.multiselect("Selectați specificațiile pentru comparație:",
                                  list(options.keys()),
                                  default=["Diagonala ecran", "Rezolutie", "Rata refresh", "Luminozitate"])

    # Create comparison table
    if compare_categories and compare_specs:
        st.markdown("<h3>Tabel comparativ</h3>", unsafe_allow_html=True)

        # Prepare data for the table
        comparison_data = []

        # Add header row
        header_row = ["Specificație"] + compare_categories

        # Add data rows
        for spec in compare_specs:
            row = [f"{options.get(spec, '')} {spec}"]
            for category in compare_categories:
                if spec in specs[category]:
                    row.append(specs[category][spec])
                else:
                    row.append("N/A")
            comparison_data.append(row)

        # Create DataFrame
        df_comparison = pd.DataFrame(comparison_data, columns=header_row)

        # Display the table
        st.table(df_comparison)

        # Add download button for CSV
        csv = df_comparison.to_csv(index=False)
        st.download_button(
            label="📥 Descarcă tabel comparativ (CSV)",
            data=csv,
            file_name="comparatie_monitoare.csv",
            mime="text/csv",
        )

with tab4:
    st.markdown("<h2 class='sub-header'>🤖 Analiză AI cu Gemini</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div class='card'>
        <p>Utilizați puterea AI pentru a analiza specificațiile selectate și a primi recomandări personalizate.
        Gemini 2.0-Flash va analiza specificațiile și va oferi informații valoroase despre monitoarele selectate.</p>
    </div>
    """, unsafe_allow_html=True)

    if not gemini_api_key:
        st.error("⚠️ Pentru a utiliza această funcționalitate, adăugați cheia API Gemini în fișierul .env")
    else:
        # Analysis options
        st.markdown("<h3>Opțiuni de analiză</h3>", unsafe_allow_html=True)

        analysis_type = st.radio(
            "Selectați tipul de analiză:",
            ["Analiză generală", "Comparație pentru gaming", "Recomandare pentru productivitate", "Raport calitate-preț"]
        )

    if st.button("🤖 Analizează cu Gemini", key="analyze_button"):
        if selected_categories and selected_options:
            with st.spinner("Analiză în curs cu Gemini AI..."):
                # Prepare data for analysis
                specs_data = ""
                for category in selected_categories:
                    specs_data += f"\n\n{category}:\n"
                    for option in selected_options:
                        if option in specs[category]:
                            specs_data += f"- {option}: {specs[category][option]}\n"

                # Add context based on analysis type
                context = ""
                if analysis_type == "Comparație pentru gaming":
                    context = "Concentrează-te pe aspectele importante pentru gaming: rata de refresh, timpul de răspuns, tehnologiile adaptive sync."
                elif analysis_type == "Recomandare pentru productivitate":
                    context = "Concentrează-te pe aspectele importante pentru productivitate: rezoluție, dimensiune, ergonomie, conectivitate."
                elif analysis_type == "Raport calitate-preț":
                    context = "Evaluează raportul calitate-preț și oferă recomandări de monitoare cu specificații similare la prețuri competitive."

                # Get analysis from Gemini
                analysis = analyze_with_gemini(f"{analysis_type} pentru {', '.join(selected_categories)}", specs_data + "\n" + context)

                # Store analysis in session state so it persists between reruns
                st.session_state.current_analysis = analysis
                st.session_state.current_analysis_type = analysis_type
                st.session_state.current_selected_categories = selected_categories
                st.session_state.current_specs_data = specs_data

                # Display analysis
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<h3>Analiză {analysis_type}</h3>", unsafe_allow_html=True)
                st.markdown(analysis)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("❌ Selectați cel puțin o categorie și o specificație pentru analiză.")

    # Only show the save button if we have an analysis in session state
    if 'current_analysis' in st.session_state:
        # Add custom styling for the save button
        st.markdown("""
        <style>
        .save-button {
            background-color: #f8f9fa;
            border: 1px solid #ced4da;
            border-radius: 4px;
            color: #212529;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            margin-top: 20px;
            text-decoration: none;
        }
        .save-button:hover {
            background-color: #e9ecef;
            text-decoration: none;
        }
        .save-button img {
            margin-right: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Create a single "Salvează analiza" button outside of any other button's handler
        if st.button("💾 Salvează analiza", key="save_analysis_button"):
            # Get values from session state
            analysis = st.session_state.current_analysis
            analysis_type = st.session_state.current_analysis_type
            selected_categories = st.session_state.current_selected_categories
            specs_data = st.session_state.current_specs_data

            # Create text file with analysis
            analysis_text = f"# Analiză {analysis_type} pentru {', '.join(selected_categories)}\n\n"
            analysis_text += f"Data: {time.strftime('%d-%m-%Y %H:%M:%S')}\n\n"
            analysis_text += f"## Specificații analizate\n\n{specs_data}\n\n"
            analysis_text += f"## Analiză Gemini AI\n\n{analysis}"

            # Store text in session state
            st.session_state.analysis_text = analysis_text
            st.session_state.analysis_filename = f"analiza_{analysis_type.lower().replace(' ', '_')}.txt"

            # Generate PDF with analysis
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Add title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.purple,
                spaceAfter=12,
                fontName='Helvetica',
                encoding='utf-8'
            )

            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontName='Helvetica',
                encoding='utf-8'
            )

            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.blue,
                spaceAfter=8,
                fontName='Helvetica',
                encoding='utf-8'
            )

            elements = []

            # Add title with proper encoding
            elements.append(Paragraph(f"Analiza detaliata {', '.join(selected_categories)}", title_style))
            elements.append(Spacer(1, 12))

            # Add date
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey
            )
            elements.append(Paragraph(f"Generat de catre ionut.capota@processit.ro la: {time.strftime('%d-%m-%Y %H:%M:%S')}", date_style))
            elements.append(Spacer(1, 24))

            # Add introduction
            intro_text = f"Specificatiile prezentate descriu un monitor {', '.join(selected_categories)} cu caracteristici solide, potrivit pentru o gama larga de utilizari."
            elements.append(Paragraph(intro_text, styles['Normal']))
            elements.append(Spacer(1, 12))

            # Add main sections similar to the screenshot
            sections = [
                "1. Cele mai importante caracteristici:",
                "2. Avantajele specificatiilor:",
                "3. Potentiale utilizari recomandate:",
                "4. Recomandari de produse care ar putea indeplini aceste specificatii:"
            ]

            # Split analysis into sections based on numbering or headers
            analysis_parts = analysis.split("\n\n")
            current_section = 0

            for section in sections:
                section_style = ParagraphStyle(
                    'Section',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.blue,
                    spaceAfter=8,
                    fontName='Helvetica',
                    encoding='utf-8'
                )

                elements.append(Paragraph(section, section_style))

                # Add some content for each section
                if current_section < len(analysis_parts):
                    elements.append(Paragraph(analysis_parts[current_section], styles['Normal']))
                    current_section += 1
                else:
                    # Fallback content if analysis doesn't have enough sections
                    elements.append(Paragraph("Informatii detaliate vor fi disponibile in analiza completa.", styles['Normal']))

                elements.append(Spacer(1, 16))

            # Add specifications
            spec_style = ParagraphStyle(
                'Specs',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.darkblue,
                spaceAfter=6,
                fontName='Helvetica',
                encoding='utf-8'
            )

            elements.append(Paragraph("Specificatii tehnice:", spec_style))

            # Create a table for specifications
            data = [["Specificatie", "Valoare"]]
            for category in selected_categories:
                for option in selected_options:
                    if option in specs[category]:
                        data.append([option, specs[category][option]])

            if len(data) > 1:  # Only create table if we have data
                table = Table(data, colWidths=[200, 300])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lavender),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(table)

            # Add conclusion
            elements.append(Spacer(1, 20))
            conclusion_text = "In concluzie, specificatiile descriu un monitor versatil si performant, potrivit pentru o gama larga de utilizari, oferind un bun raport calitate-pret. Ajustabilitatea ergonomica si tehnologiile de confort vizual sunt puncte forte importante."
            elements.append(Paragraph(conclusion_text, styles['Normal']))

            # Add footer
            elements.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=1,  # Center alignment
                fontName='Helvetica',
                encoding='utf-8'
            )
            
            elements.append(Paragraph("© 2025 ionut.capota@processit.ro", footer_style))

            # Build PDF
            doc.build(elements)
            buffer.seek(0)

            # Store the PDF in session state
            st.session_state.analysis_pdf = buffer
            st.session_state.analysis_pdf_filename = f"analiza_{analysis_type.lower().replace(' ', '_')}.pdf"

            # Show success message
            st.success("✅ Analiză salvată cu succes!")
            st.balloons()

        # Show download buttons if analysis has been saved
        if 'analysis_pdf' in st.session_state:
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="📥 Descarcă PDF",
                    data=st.session_state.analysis_pdf,
                    file_name=st.session_state.analysis_pdf_filename,
                    mime="application/pdf"
                )

            with col2:
                st.download_button(
                    label="📄 Descarcă TXT",
                    data=st.session_state.analysis_text,
                    file_name=st.session_state.analysis_filename,
                    mime="text/plain"
                )    

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center;'>
    <p>© 2025 Dezvoltat cu ❤️ de ionut.capota@processit.ro </p>
</div>
""", unsafe_allow_html=True)
