from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from pdf2image import convert_from_bytes
import re
import uvicorn
import os

app = FastAPI(title="API Extraction Avis de Distribution ONCF")

# ==========================================
# AUTORISATION CORS (Pour React)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Accepte les requêtes de n'importe quel site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# CONFIGURATION DES CHEMINS (Adaptatif Windows / Linux)
# ==========================================
# Si le code tourne sur votre PC Windows (local)
if os.name == 'nt':
    chemin_poppler = r"C:\Users\essab\Downloads\Compressed\Release-26.02.0-0\poppler-26.02.0\Library\bin"
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Si le code tourne sur le serveur Render (Linux)
else:
    chemin_poppler = None  # Linux le trouve tout seul
    # Pas besoin de spécifier le chemin pour Tesseract sur Linux

@app.post("/api/extraire-pdf")
async def extraire_donnees_pdf(fichier: UploadFile = File(...)):
    """
    Reçoit un fichier PDF, le convertit en images, extrait le texte via OCR
    et retourne les données structurées au format JSON.
    """
    pdf_bytes = await fichier.read()
    
    # Utilisation du chemin adapté (Windows ou Linux)
    if chemin_poppler:
        images = convert_from_bytes(pdf_bytes, poppler_path=chemin_poppler)
    else:
        images = convert_from_bytes(pdf_bytes)
    
    donnees_extraites = []
    
    for i, image_page in enumerate(images):
        # Remise à l'endroit (Rotation vers la gauche)
        image_endroit = image_page.rotate(90, expand=True)
        
        # Lecture OCR
        texte_brut = pytesseract.image_to_string(image_endroit, lang='eng', config='--psm 6') 
        
        ad_data = {"page": i + 1}
        
        # Expressions régulières
        match_no = re.search(r"NO\s*[:;.,]?\s*(\d{6})", texte_brut)
        ad_data["NO"] = match_no.group(1) if match_no else "Non trouvé"
        
        match_dm = re.search(r"D[\.\s]*M\s*[:;.,]?\s*[^\d\n]{0,5}(\d+)", texte_brut, re.IGNORECASE)
        ad_data["NUMERO D.M"] = match_dm.group(1) if match_dm else "Non trouvé"
        
        match_etab = re.search(r"DEST\.?\s*[:;.,]?\s*(\d{4})\b", texte_brut)
        ad_data["CODE ETAB DEST"] = match_etab.group(1) if match_etab else "Non trouvé"
        
        match_nre = re.search(r"\b(\d{5,7}[A-Z]\d{2})\b", texte_brut)
        if not match_nre: 
            match_nre = re.search(r"NRE\s*(?:ARTICLE)?\s*[:;.,]?\s*([A-Z0-9]{8,10})", texte_brut)
        ad_data["NRE ARTICLE"] = match_nre.group(1) if match_nre else "Non trouvé"
        
        match_qte = re.search(r"(?:PRETAXEE|QUANTITE)[^\d]*(\d{1,5}[,.]\d{2,3})", texte_brut)
        ad_data["QUANTITE PRETAXEE"] = match_qte.group(1) if match_qte else "Non trouvé"
        
        match_date = re.search(r"DATE\s*[:;.,]?\s*(\d{2}/\d{2}/\d{4})", texte_brut)
        ad_data["DATE"] = match_date.group(1) if match_date else "Non trouvé"

        donnees_extraites.append(ad_data)

    return {
        "succes": True,
        "fichier_analyse": fichier.filename,
        "nombre_pages": len(images),
        "resultats": donnees_extraites
    }

if __name__ == "__main__":
    uvicorn.run("api_extraction:app", host="0.0.0.0", port=8000, reload=True)