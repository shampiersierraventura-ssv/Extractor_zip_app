# 📦 Extractor Masivo de ZIPs → XMLs

App de Streamlit que extrae archivos XML desde carpetas comprimidas (`.zip`) aplicando estas reglas:

| Caso | Contenido del ZIP | Acción |
|------|-------------------|--------|
| **1** | Un solo archivo XML | Extrae ese archivo |
| **2** | Varios archivos (XML + otros) | Extrae solo los XML |
| **3** | Exactamente dos archivos XML | Extrae el que **NO** empieza con `R` |

## 🚀 Uso

1. Sube uno o más archivos `.zip`
2. Haz clic en **Extraer XMLs**
3. Descarga el `.zip` con todos los XML extraídos

## 🗂️ Estructura del proyecto

```
extractor_zip_app/
├── app.py              # App principal de Streamlit
├── requirements.txt    # Dependencias
└── README.md           # Este archivo
```

## ▶️ Correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy en Streamlit Community Cloud

1. Sube este repositorio a GitHub (puede ser público o privado).
2. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con tu cuenta de GitHub.
3. Haz clic en **"New app"**.
4. Selecciona tu repositorio, rama (`main`) y archivo principal (`app.py`).
5. Haz clic en **"Deploy"** — listo, en ~1 minuto tendrás la URL pública.

> **Nota:** La app procesa los archivos completamente en memoria, sin guardar nada en disco.  
> No necesitas configurar secretos ni variables de entorno.
