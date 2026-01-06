import streamlit as st
from pypdf import PdfReader
import re

st.set_page_config(page_title="Analiza ECTS", layout="centered")
st.title("📊 Analiza ocen i ECTS")

uploaded_file = st.file_uploader("Wgraj plik PDF z ocenami", type="pdf")

TYPE_MAP = {
    "c": "ćwiczenia",
    "d": "praca dyplomowa",
    "l": "laboratorium",
    "p": "projekt",
    "q": "praktyka",
    "s": "seminarium",
    "w": "wykład",
}

one_line_re = re.compile(
    r'^\(([^)]+)\)\s+(.*?)\s+([cdlpqsw])\s+(\d+)\s+([\d,]+)(?:\s+(\d+))?$'
)
code_re = re.compile(r'^\(([^)]+)\)\s*(.*)')
data_re = re.compile(r'^([cdlpqsw])\s+(\d+)\s+([\d,]+)(?:\s+(\d+))?$')

if uploaded_file:
    reader = PdfReader(uploaded_file)
    results = []

    current = None
    name_lines = []

    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue

        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.lower().startswith("semestr"):
                continue

            m1 = one_line_re.match(line)
            if m1:
                results.append({
                    "Kod": m1.group(1),
                    "Przedmiot": m1.group(2),
                    "Typ": TYPE_MAP[m1.group(3)],
                    "Godziny": int(m1.group(4)),
                    "Ocena": float(m1.group(5).replace(",", ".")),
                    "ECTS": int(m1.group(6)) if m1.group(6) else 0
                })
                continue

            m_code = code_re.match(line)
            if m_code:
                current = {"code": m_code.group(1)}
                name_lines = [m_code.group(2)] if m_code.group(2) else []
                continue

            m_data = data_re.match(line)
            if m_data and current:
                results.append({
                    "Kod": current["code"],
                    "Przedmiot": " ".join(name_lines).strip(),
                    "Typ": TYPE_MAP[m_data.group(1)],
                    "Godziny": int(m_data.group(2)),
                    "Ocena": float(m_data.group(3).replace(",", ".")),
                    "ECTS": int(m_data.group(4)) if m_data.group(4) else 0
                })
                current = None
                name_lines = []
                continue

            if current:
                name_lines.append(line)

    if results:
        total_ects = sum(r["ECTS"] for r in results if r["ECTS"] > 0)
        weighted_avg = sum(r["Ocena"] * r["ECTS"] for r in results if r["ECTS"] > 0) / total_ects

        st.success(f"✅ Suma ECTS: **{total_ects}**")
        st.success(f"📈 Średnia ważona: **{weighted_avg:.4f}**")

        st.dataframe(results)
