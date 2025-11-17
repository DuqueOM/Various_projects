import re
import unicodedata
from pathlib import Path

import pandas as pd

# === CONFIG ===
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "BANJIO.csv"
OUTPUT_FILE = BASE_DIR / "extractos_limpios.csv"
DESCRIPTION_COL = "Descripción"

# === REGLAS (sin la regla "cargo", con regla RAW específica añadida) ===
raw_rules = [
    (
        r"\(\d{1,3}(?:,\d{3})*\.\d{2}\)\s*mxn\s*Nro\.?\s*Ref/Docto\.?\s*#\s*\d{7}",
        "RAW_MATCH",
        "RAW_PATTERN_AMOUNT_REF_7",
    ),
    (r"TRASPASO\s+DE\s+SALDOS\s", "TRASPASO DE SALDOS", "TRASPASO DE SALDOS"),
    (
        r"\scuota\s+obrero\s+patronal\s",
        "CUOTA OBRERO PATRONAL",
        "CUOTA OBRERO PATRONAL",
    ),
    (
        r"mxn\s+numero\s+de\s+cheque.*\|\s*(\d{4})\s*\|",
        "CHEQUE ****",
        "mxn numero de cheque con dígitos",
    ),
    (
        r"(?s)spei\s+enviado[:\s]*\|.*?beneficiario:\s*(.*?)\s*\(dato\s+no\s+verificado",
        "SPEI Enviado",
        "SPEI Enviado con Beneficiario",
    ),
    (
        r"(?s)spei\s+recibido[:\s]*\|.*?ordenante:\s*(.*?)\s*cuenta\s+ordenante",
        "SPEI Recibido",
        "SPEI Recibido con Ordenante",
    ),
    (
        r"(?s)devoluci[oó]n\s+de\s+spei[:\s]*\|.*?ordenante:\s*(.+?)\s*cuenta\s+ordenante",
        "Devolución de SPEI",
        "Devolución de SPEI con Ordenante",
    ),
    (
        r"(?s)retiro\s+de\s+recursos.*?beneficiario\s*(?:\|\s*)?(.*?)\s*\|\s*hora:",
        "Retiro de Recursos",
        "Retiro de Recursos con Beneficiario",
    ),
    (
        r"(?s)entrega\s+de\s+recursos\s+por.*?ordenante\s*\|?\s*(.+?)\s*\|\s*hora:",
        "Entrega de Recursos",
        "Entrega de Recursos con Ordenante",
    ),
    (
        r"^\s*comision\s*\|\s*dispersion\s+grupo\b.*por\s*\(?[\d,]+\.\d{2}\)?\s*mxn.*recibo\s*#\s*\d+",
        "Comisión",
        "Comisión | Dispersion Grupo con monto y Recibo",
    ),
    (
        r"^\s*comision\s*\|\s*numero\s+de\s+referencia\b.*",
        "Comisión",
        "Comisión | Número de Referencia (exacto)",
    ),
    (r"^\s*comisi[oó]n\s+por\b", "Comisión", "^Comisión por"),
    (r"dep[oó]sito\s+en\s+efectivo\b", "Depósito en Efectivo", "Depósito en Efectivo"),
    (
        r"dep[oó]sito\s+negocios\s+afiliados\b",
        "Depósito Negocios Afiliados",
        "Depósito Negocios Afiliados",
    ),
    (
        r"dep[oó]sito\s+sbc\s+de\s+cobro\s+inmediato\b",
        "Depósito SBC de Cobro Inmediato",
        "Depósito SBC de Cobro Inmediato",
    ),
    (
        r"^\s*deposito\s+para\s+eliminacion\s+de\s+sobregiro\s+por\s*\(?[\d,]+\.\d{2}\)?\s*mxn\b.*",
        "Depósito para Eliminación de Sobregiro",
        "Depósito para Eliminación de Sobregiro con monto",
    ),
    (r"^\s*(spei enviado)[:\s]?.*", "SPEI Enviado", "SPEI Enviado"),
    (r"^\s*(spei recibido)[:\s]?.*", "SPEI Recibido", "SPEI Recibido"),
    (
        r"^\s*devoluci[oó]n\s+de\s+spei[:\s]?.*",
        "Devolución de SPEI",
        "Devolución de SPEI",
    ),
    (
        r"^\s*entrega\s+de\s+recursos\s+por",
        "Entrega de Recursos",
        "Entrega de Recursos",
    ),
    (r"^\s*retiro\s+de\s+recursos\s+por", "Retiro de Recursos", "Retiro de Recursos"),
    (r"^\s*iva\s+comision\s+por\s+administracion\s*.*", "IVA", "IVA"),
    (r"^\s*iva\s+comision\s+por\s+penalizacion\s*.*", "IVA", "IVA"),
    (r"^\s*iva\s+comision\s+por\s+transferencia\s*.*", "IVA", "IVA"),
    (r"^\s*iva\s+comision\b.*numero\s+de\s+autorizacion\b.*", "IVA", "IVA"),
    (
        r"telefono-?telmex",
        "Pago de Servicios TELMEX EN LINEA",
        "Pago de Servicios TELMEX EN LINEA",
    ),
    (r"n[oó]mina\b", "Nómina", "Nómina"),
    (
        r"por\s*\(?[\d,]+\.\d{2}\)?\s*mxn\s*\|\s*recibo\s*#\s*\d+\b",
        "por *",
        "por (monto) mxn | Recibo # (caso general estricto)",
    ),
    # 🚩 ESTA ES LA QUE CAMBIA
    (
        r"por\s*\(?[\d,]+\.\d{2}\)?\s*mxn\s*cargo",
        "__RAW__por_mxn_cargo",
        "por (xx) mxn Cargo",
    ),
]

compiled_rules = [
    (re.compile(pat, re.IGNORECASE | re.UNICODE), label, debug)
    for pat, label, debug in raw_rules
]


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace(":", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def apply_rules_vectorized(df: pd.DataFrame, text_col: str):
    df["label"] = None
    # df['method'] = None
    # df['score'] = None

    norm_col = f"{text_col}_norm"
    raw_col = f"{text_col}_raw"
    df[norm_col] = df[text_col].fillna("").astype(str).map(normalize_text)
    df[raw_col] = df[text_col].fillna("").astype(str)

    RAW_LABEL_SET = {"por *", "__RAW__por_mxn_cargo"}

    for pattern, label, debug in compiled_rules:
        mask_unassigned = df["label"].isna()
        if not mask_unassigned.any():
            break

        has_group = pattern.groups > 0

        if has_group:
            extracted = df.loc[mask_unassigned, raw_col].str.extract(
                pattern, expand=True
            )
            if extracted.dropna(how="all").empty:
                extracted = df.loc[mask_unassigned, norm_col].str.extract(
                    pattern, expand=True
                )

            idx = extracted.dropna(how="all").index
            if not idx.empty:
                first_group = extracted.loc[idx, 0]

                def build_label(g):
                    if pd.isna(g):
                        return label
                    gstr = str(g).strip()
                    gstr = re.sub(r"\s*\|\s*", " ", gstr)
                    gstr = re.sub(r"\s+", " ", gstr).strip()

                    if "****" in label:
                        return label.replace("****", gstr)
                    if label.lower().startswith(
                        "spei enviado"
                    ) or label.lower().startswith("spei recibido"):
                        return f"{label}: {gstr}"
                    if label.lower().startswith("devolución de spei"):
                        return f"{label}: {gstr}"
                    if label.lower().startswith("retiro de recursos"):
                        return f"{label} Beneficiario {gstr}"
                    if label.lower().startswith("entrega de recursos"):
                        return f"{label} {gstr}"
                    return f"{label} {gstr}"

                df.loc[idx, "label"] = first_group.map(build_label)
                # df.loc[idx, 'method'] = f"rule:{debug}"
                # df.loc[idx, 'score'] = 100

        else:
            if label in RAW_LABEL_SET:
                mask_match_series = df.loc[mask_unassigned, raw_col].str.contains(
                    pattern, na=False
                )
                idx = mask_match_series[mask_match_series].index
                if not idx.empty:
                    fixed = df.loc[idx, raw_col].astype(str)
                    if label == "__RAW__por_mxn_cargo":
                        # 🚩 limpieza especial: quitar "Cargo a cuenta..." hasta el primer "|"
                        fixed = fixed.str.replace(
                            r"Cargo a cuenta por deposito con cheque .*?\|",
                            "",
                            regex=True,
                            flags=re.IGNORECASE,
                        )
                    df.loc[idx, "label"] = fixed.str.strip()
                    # df.loc[idx, 'method'] = f"rule:{debug}"
                    # df.loc[idx, 'score'] = 100
            else:
                mask_match_series = df.loc[mask_unassigned, norm_col].str.contains(
                    pattern, na=False
                )
                idx = mask_match_series[mask_match_series].index
                if not idx.empty:
                    df.loc[idx, "label"] = label
                    # df.loc[idx, 'method'] = f"rule:{debug}"
                    # df.loc[idx, 'score'] = 100

    df["label"] = df["label"].fillna("UNKNOWN")
    # df['method'] = df['method'].fillna("none")
    # df['score'] = df['score'].fillna(0).astype(int)
    return df


def main():
    df = pd.read_csv(INPUT_FILE, encoding="latin1")
    if DESCRIPTION_COL not in df.columns:
        raise ValueError(f"La columna '{DESCRIPTION_COL}' no existe en el archivo CSV")

    df = apply_rules_vectorized(df, DESCRIPTION_COL)

    norm_col = f"{DESCRIPTION_COL}_norm"
    raw_col = f"{DESCRIPTION_COL}_raw"
    df = df.drop(columns=[c for c in (norm_col, raw_col) if c in df.columns])

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"✅ Limpieza completada. Archivo guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
