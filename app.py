import streamlit as st
import zipfile
import shutil
import io
import zipfile as zf
from pathlib import Path

# ─────────────────────────────────────────
# Página y estilo
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Extractor Masivo de ZIPs",
    page_icon="📦",
    layout="centered",
)

st.markdown("""
<style>
    /* Fondo suave gris azulado */
    .stApp { background-color: #F0F4F8; }

    /* Título principal */
    h1 { color: #1A2E44; letter-spacing: -0.5px; }

    /* Tarjeta resumen */
    .resumen-card {
        background: #1A2E44;
        color: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-top: 1rem;
    }
    .resumen-card h3 { color: #7DD4FC; margin-bottom: 0.5rem; }
    .resumen-card .stat { font-size: 1.6rem; font-weight: 700; }
    .resumen-card .label { font-size: 0.8rem; opacity: 0.75; text-transform: uppercase; }

    /* Línea de log */
    .log-ok  { color: #22C55E; font-family: monospace; font-size: 0.85rem; }
    .log-warn{ color: #F59E0B; font-family: monospace; font-size: 0.85rem; }
    .log-err { color: #EF4444; font-family: monospace; font-size: 0.85rem; }
    .log-info{ color: #94A3B8; font-family: monospace; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Lógica de selección (idéntica al notebook)
# ─────────────────────────────────────────
def seleccionar_xml(archivos_en_zip: list[str]) -> list[str]:
    """
    Reglas de selección:
      Caso 1 – Un solo XML  → ese mismo.
      Caso 2 – Varios archivos, uno o más XML → todos los XML.
      Caso 3 – Exactamente dos XML → el que NO empieza con 'R'.
    """
    xmls = [
        f for f in archivos_en_zip
        if f.lower().endswith(".xml") and not f.endswith("/")
    ]

    if len(xmls) == 0:
        return []
    elif len(xmls) == 1:
        return xmls
    elif len(xmls) == 2:
        candidatos = [f for f in xmls if not Path(f).name.upper().startswith("R")]
        return candidatos if candidatos else [xmls[0]]
    else:
        return xmls


# ─────────────────────────────────────────
# Procesamiento en memoria
# ─────────────────────────────────────────
def procesar_zips(archivos_subidos) -> tuple[bytes, list[dict]]:
    """
    Recibe una lista de UploadedFile (ZIPs).
    Devuelve:
      - bytes de un ZIP de salida con todos los XMLs extraídos
      - lista de registros de log
    """
    buffer_salida = io.BytesIO()
    log = []
    nombres_usados: set[str] = set()

    with zf.ZipFile(buffer_salida, "w", compression=zf.ZIP_DEFLATED) as zip_out:
        for archivo in archivos_subidos:
            nombre_zip = archivo.name
            log.append({"tipo": "info", "msg": f"🗜️  {nombre_zip}"})

            try:
                with zf.ZipFile(io.BytesIO(archivo.read()), "r") as zip_in:
                    contenido = zip_in.namelist()
                    xmls = seleccionar_xml(contenido)

                    if not xmls:
                        log.append({"tipo": "warn", "msg": f"  ⚠️  Sin XML en este ZIP — se omite."})
                        continue

                    for xml_interno in xmls:
                        nombre_final = Path(xml_interno).name

                        # Evitar sobreescritura
                        nombre_unico = nombre_final
                        contador = 1
                        while nombre_unico in nombres_usados:
                            stem = Path(nombre_final).stem
                            nombre_unico = f"{stem}_{contador}.xml"
                            contador += 1
                        nombres_usados.add(nombre_unico)

                        data_xml = zip_in.read(xml_interno)
                        zip_out.writestr(nombre_unico, data_xml)
                        log.append({"tipo": "ok", "msg": f"  ✅ Extraído → {nombre_unico}"})

            except zf.BadZipFile:
                log.append({"tipo": "err", "msg": f"  ❌ ZIP corrupto — se omite."})
            except Exception as e:
                log.append({"tipo": "err", "msg": f"  ❌ Error: {e}"})

    return buffer_salida.getvalue(), log


# ─────────────────────────────────────────
# UI
# ─────────────────────────────────────────
st.title("📦 Extractor Masivo de ZIPs")
st.markdown("Sube tus archivos `.zip` y descarga todos los XML extraídos en un solo archivo comprimido.")

st.divider()

archivos = st.file_uploader(
    "Arrastra o selecciona los archivos ZIP",
    type=["zip"],
    accept_multiple_files=True,
    help="Puedes subir varios ZIPs a la vez.",
)

if archivos:
    st.markdown(f"**{len(archivos)} archivo(s) cargado(s)**")

    col1, col2 = st.columns([1, 2])
    with col1:
        btn = st.button("▶️  Extraer XMLs", use_container_width=True, type="primary")

    if btn:
        with st.spinner("Procesando ZIPs…"):
            zip_bytes, log = procesar_zips(archivos)

        # ── Estadísticas ──────────────────────
        n_ok   = sum(1 for r in log if r["tipo"] == "ok")
        n_warn = sum(1 for r in log if r["tipo"] == "warn")
        n_err  = sum(1 for r in log if r["tipo"] == "err")

        st.markdown(f"""
        <div class="resumen-card">
            <h3>📊 Resumen</h3>
            <div style="display:flex; gap:2rem; margin-top:0.5rem;">
                <div>
                    <div class="stat" style="color:#4ADE80;">{n_ok}</div>
                    <div class="label">XMLs extraídos</div>
                </div>
                <div>
                    <div class="stat" style="color:#FCD34D;">{n_warn}</div>
                    <div class="label">ZIPs sin XML</div>
                </div>
                <div>
                    <div class="stat" style="color:#F87171;">{n_err}</div>
                    <div class="label">Errores</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Botón de descarga ─────────────────
        if n_ok > 0:
            st.download_button(
                label="⬇️  Descargar XMLs extraídos (.zip)",
                data=zip_bytes,
                file_name="XMLs_extraidos.zip",
                mime="application/zip",
                use_container_width=True,
            )

        # ── Log detallado ─────────────────────
        with st.expander("📋 Ver log detallado", expanded=(n_warn + n_err > 0)):
            for r in log:
                css = {"ok": "log-ok", "warn": "log-warn", "err": "log-err", "info": "log-info"}[r["tipo"]]
                st.markdown(f'<div class="{css}">{r["msg"]}</div>', unsafe_allow_html=True)
else:
    st.info("👆 Sube uno o más archivos ZIP para comenzar.")

# ─────────────────────────────────────────
# 💖 Dedicatoria — al final de la app
# ─────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

st.markdown("""
<style>
@keyframes float {
  0%   { transform: translateY(0px);   }
  50%  { transform: translateY(-8px);  }
  100% { transform: translateY(0px);   }
}
@keyframes heartbeat {
  0%, 100% { transform: scale(1);    }
  25%       { transform: scale(1.18); }
  50%       { transform: scale(1);    }
  75%       { transform: scale(1.12); }
}
@keyframes blink {
  0%, 90%, 100% { transform: scaleY(1);    }
  95%            { transform: scaleY(0.08); }
}
@keyframes sparkle {
  0%, 100% { opacity: 0; transform: scale(0.5) rotate(0deg);   }
  50%       { opacity: 1; transform: scale(1.2) rotate(180deg); }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0);    }
}

.lili-card {
    background: linear-gradient(135deg, #FFF0F6 0%, #FFF5F0 50%, #F0F4FF 100%);
    border: 1.5px solid #FBBDCF;
    border-radius: 20px;
    padding: 2rem 2rem 1.5rem;
    text-align: center;
    box-shadow: 0 4px 24px rgba(251,113,133,0.12);
    animation: fadeUp 0.8s ease both;
    position: relative;
    overflow: hidden;
}
.lili-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #FB7185, #F472B6, #C084FC, #818CF8, #FB7185);
    background-size: 200% auto;
    animation: shimmer 3s linear infinite;
}

/* Ojitos SVG */
.eyes-wrap {
    display: inline-block;
    animation: float 3s ease-in-out infinite;
    margin-bottom: 0.6rem;
}

.lili-title {
    font-size: 1.05rem;
    color: #9D174D;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.lili-quote {
    font-size: 1.25rem;
    color: #1A2E44;
    font-weight: 400;
    line-height: 1.6;
    margin: 0.5rem 0 1rem;
    font-style: italic;
}
.lili-quote em {
    font-style: normal;
    font-weight: 700;
    background: linear-gradient(90deg, #FB7185, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.lili-firma {
    font-size: 0.82rem;
    color: #9CA3AF;
    margin-top: 0.8rem;
}
.sparkle {
    position: absolute;
    font-size: 1rem;
    animation: sparkle 2s ease-in-out infinite;
}
.sp1 { top: 18px;  left: 22px;  animation-delay: 0s;    }
.sp2 { top: 14px;  right: 28px; animation-delay: 0.7s;  }
.sp3 { bottom: 22px; left: 40px; animation-delay: 1.1s; }
.sp4 { bottom: 18px; right: 36px; animation-delay: 0.4s;}
</style>

<div class="lili-card">
  <span class="sparkle sp1">✨</span>
  <span class="sparkle sp2">💫</span>
  <span class="sparkle sp3">🌸</span>
  <span class="sparkle sp4">✨</span>

  <!-- Ojitos animados en SVG puro -->
  <div class="eyes-wrap">
    <svg width="120" height="64" viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg">
      <!-- Ojo izquierdo -->
      <g style="animation: blink 4s ease-in-out infinite; transform-origin: 34px 34px;">
        <!-- Blanco del ojo -->
        <ellipse cx="34" cy="34" rx="24" ry="22" fill="white" stroke="#FBBDCF" stroke-width="2"/>
        <!-- Iris -->
        <circle cx="34" cy="34" r="14" fill="#6366F1"/>
        <!-- Brillo iris -->
        <circle cx="34" cy="34" r="10" fill="#818CF8"/>
        <!-- Pupila -->
        <circle cx="34" cy="34" r="6"  fill="#1A2E44"/>
        <!-- Destello -->
        <circle cx="29" cy="29" r="3"  fill="white" opacity="0.8"/>
        <!-- Corazón en pupila -->
        <text x="31" y="37" font-size="7" fill="#FB7185" font-family="serif">♥</text>
      </g>
      <!-- Pestañas ojo izquierdo -->
      <line x1="18" y1="14" x2="22" y2="18" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="28" y1="10" x2="29" y2="15" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="38" y1="10" x2="37" y2="15" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="47" y1="14" x2="44" y2="18" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>

      <!-- Ojo derecho -->
      <g style="animation: blink 4s ease-in-out infinite 0.15s; transform-origin: 86px 34px;">
        <ellipse cx="86" cy="34" rx="24" ry="22" fill="white" stroke="#FBBDCF" stroke-width="2"/>
        <circle cx="86" cy="34" r="14" fill="#6366F1"/>
        <circle cx="86" cy="34" r="10" fill="#818CF8"/>
        <circle cx="86" cy="34" r="6"  fill="#1A2E44"/>
        <circle cx="81" cy="29" r="3"  fill="white" opacity="0.8"/>
        <text x="83" y="37" font-size="7" fill="#FB7185" font-family="serif">♥</text>
      </g>
      <!-- Pestañas ojo derecho -->
      <line x1="70" y1="14" x2="74" y2="18" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="80" y1="10" x2="81" y2="15" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="90" y1="10" x2="89" y2="15" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="99" y1="14" x2="96" y2="18" stroke="#1A2E44" stroke-width="1.5" stroke-linecap="round"/>

      <!-- Corazón flotando arriba -->
      <text x="55" y="12" font-size="11" fill="#FB7185"
            style="animation: heartbeat 1.4s ease-in-out infinite; transform-origin: 60px 8px;">♥</text>
    </svg>
  </div>

  <div class="lili-title">✦ con amor ✦</div>

  <div class="lili-quote">
    Esta app no nació de un algoritmo.<br>
    Nació de la inspiración de <em>unos ojitos muy bonitos</em>...<br>
    los de mi <em>Lili</em> 🌸
  </div>

  <div class="lili-firma">
    Desarrollado con 💜 · cada línea de código lleva tu nombre
  </div>
</div>
""", unsafe_allow_html=True)
