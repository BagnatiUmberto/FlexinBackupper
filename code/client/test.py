"""
trova_minimi.py
---------------
Legge un file CSV con punti di un grafico (x, y), trova i minimi locali
e globale, e calcola le distanze euclidee tra di essi.

Uso:
    python trova_minimi.py dati.csv
    python trova_minimi.py dati.csv --col-x tempo --col-y valore
    python trova_minimi.py dati.csv --finestra 5 --soglia 0.1

Formato CSV atteso (header nella prima riga):
    x,y
    0.0,3.5
    1.0,2.1
    ...
"""

import argparse
import csv
import math
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# Lettura CSV
# ──────────────────────────────────────────────

def leggi_csv(percorso: str, col_x: str, col_y: str) -> list[tuple[float, float]]:
    """Legge il CSV e restituisce una lista di coppie (x, y)."""
    punti = []
    path = Path(percorso)
    if not path.exists():
        sys.exit(f"[ERRORE] File non trovato: {percorso}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            sys.exit("[ERRORE] Il file CSV è vuoto o privo di intestazione.")

        colonne = [c.strip() for c in reader.fieldnames]

        # Rilevazione automatica delle colonne se non specificate
        if col_x == "auto" or col_y == "auto":
            if len(colonne) < 2:
                sys.exit("[ERRORE] Il CSV deve avere almeno due colonne numeriche.")
            col_x, col_y = colonne[0], colonne[1]
            print(f"[INFO] Colonne rilevate automaticamente: x='{col_x}', y='{col_y}'")

        if col_x not in colonne:
            sys.exit(f"[ERRORE] Colonna '{col_x}' non trovata. Disponibili: {colonne}")
        if col_y not in colonne:
            sys.exit(f"[ERRORE] Colonna '{col_y}' non trovata. Disponibili: {colonne}")

        for i, riga in enumerate(reader, start=2):
            try:
                x = float(riga[col_x].strip())
                y = float(riga[col_y].strip())
                punti.append((x, y))
            except ValueError:
                print(f"[ATTENZIONE] Riga {i} ignorata (valori non numerici): {dict(riga)}")

    if len(punti) < 3:
        sys.exit("[ERRORE] Servono almeno 3 punti validi per trovare i minimi.")

    return punti


# ──────────────────────────────────────────────
# Ricerca dei minimi
# ──────────────────────────────────────────────

def trova_minimi_locali(
    punti: list[tuple[float, float]],
    finestra: int = 1,
    soglia: float = 0.0,
) -> list[tuple[int, float, float]]:
    """
    Trova i minimi locali nella serie y.

    Un punto i è un minimo locale se è il valore minimo
    all'interno di una finestra di ampiezza ±`finestra` e
    se è inferiore di almeno `soglia` rispetto ai vicini immediati.

    Restituisce lista di (indice, x, y).
    """
    n = len(punti)
    minimi = []

    for i in range(finestra, n - finestra):
        y_corrente = punti[i][1]
        vicini_y = [punti[j][1] for j in range(i - finestra, i + finestra + 1) if j != i]

        if all(y_corrente <= v for v in vicini_y):
            # Verifica soglia rispetto ai vicini diretti
            sx = punti[i - 1][1]
            dx = punti[i + 1][1]
            if (sx - y_corrente) >= soglia and (dx - y_corrente) >= soglia:
                minimi.append((i, punti[i][0], punti[i][1]))

    return minimi


def trova_minimo_globale(punti: list[tuple[float, float]]) -> tuple[int, float, float]:
    """Restituisce (indice, x, y) del punto con y minima."""
    idx = min(range(len(punti)), key=lambda i: punti[i][1])
    return idx, punti[idx][0], punti[idx][1]


# ──────────────────────────────────────────────
# Distanze
# ──────────────────────────────────────────────

def distanza_euclidea(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Distanza euclidea 2D tra due punti (x, y)."""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def distanza_x(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Distanza solo sull'asse x (utile per serie temporali)."""
    return abs(p2[0] - p1[0])


def calcola_distanze(
    minimi: list[tuple[int, float, float]]
) -> list[dict]:
    """
    Calcola distanze euclidee e sull'asse x tra tutte le coppie di minimi.
    Restituisce lista di dizionari con i dettagli.
    """
    risultati = []
    for i in range(len(minimi)):
        for j in range(i + 1, len(minimi)):
            p1 = (minimi[i][1], minimi[i][2])  # (x, y)
            p2 = (minimi[j][1], minimi[j][2])
            risultati.append({
                "da":      f"M{i+1} (x={p1[0]:.4g}, y={p1[1]:.4g})",
                "a":       f"M{j+1} (x={p2[0]:.4g}, y={p2[1]:.4g})",
                "dist_2d": distanza_euclidea(p1, p2),
                "dist_x":  distanza_x(p1, p2),
                "delta_y": p2[1] - p1[1],
            })
    return risultati


# ──────────────────────────────────────────────
# Output
# ──────────────────────────────────────────────

def stampa_separatore(char="─", n=60):
    print(char * n)


def stampa_risultati(
    punti: list[tuple[float, float]],
    minimi_locali: list[tuple[int, float, float]],
    minimo_globale: tuple[int, float, float],
    distanze: list[dict],
    col_x: str,
    col_y: str,
):
    stampa_separatore("═")
    print(f"  ANALISI DEI MINIMI — {len(punti)} punti totali")
    stampa_separatore("═")

    print(f"\n  Colonne usate : x='{col_x}'  y='{col_y}'")
    print(f"  Range x       : [{punti[0][0]:.4g}, {punti[-1][0]:.4g}]")
    y_vals = [p[1] for p in punti]
    print(f"  Range y       : [{min(y_vals):.4g}, {max(y_vals):.4g}]")

    # ── Minimo globale
    stampa_separatore()
    print("\n  MINIMO GLOBALE")
    stampa_separatore()
    ig, xg, yg = minimo_globale
    print(f"  Indice {ig:>5d} │ x = {xg:>12.6g} │ y = {yg:>12.6g}")

    # ── Minimi locali
    stampa_separatore()
    print(f"\n  MINIMI LOCALI ({len(minimi_locali)} trovati)")
    stampa_separatore()
    if not minimi_locali:
        print("  Nessun minimo locale trovato (prova a ridurre --finestra o --soglia).")
    else:
        print(f"  {'#':>4}  {'Indice':>7}  {'x':>14}  {'y':>14}")
        print(f"  {'─'*4}  {'─'*7}  {'─'*14}  {'─'*14}")
        for k, (idx, x, y) in enumerate(minimi_locali, 1):
            marker = " ◄ GLOBALE" if idx == ig else ""
            print(f"  M{k:<3d}  {idx:>7d}  {x:>14.6g}  {y:>14.6g}{marker}")

    # ── Distanze
    if distanze:
        stampa_separatore()
        print(f"\n  DISTANZE TRA I MINIMI LOCALI")
        stampa_separatore()
        print(f"  {'Coppia':<30}  {'Dist. 2D':>10}  {'Δx':>10}  {'Δy':>10}")
        print(f"  {'─'*30}  {'─'*10}  {'─'*10}  {'─'*10}")
        for d in distanze:
            coppia = f"{d['da'].split('(')[0].strip()} → {d['a'].split('(')[0].strip()}"
            print(f"  {coppia:<30}  {d['dist_2d']:>10.4g}  {d['dist_x']:>10.4g}  {d['delta_y']:>10.4g}")

        # Coppia più vicina e più lontana
        stampa_separatore()
        min_d = min(distanze, key=lambda d: d["dist_2d"])
        max_d = max(distanze, key=lambda d: d["dist_2d"])
        print(f"\n  Coppia più vicina  : {min_d['da']}  →  {min_d['a']}")
        print(f"  Distanza 2D        : {min_d['dist_2d']:.6g}")
        print(f"\n  Coppia più lontana : {max_d['da']}  →  {max_d['a']}")
        print(f"  Distanza 2D        : {max_d['dist_2d']:.6g}")

    stampa_separatore("═")
    print()


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Trova minimi locali e distanze in un grafico CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file_csv", help="Percorso del file CSV di input")
    parser.add_argument(
        "--col-x", default="auto",
        help="Nome della colonna x (default: prima colonna)"
    )
    parser.add_argument(
        "--col-y", default="auto",
        help="Nome della colonna y (default: seconda colonna)"
    )
    parser.add_argument(
        "--finestra", type=int, default=1,
        help="Ampiezza della finestra per il rilevamento dei minimi (default: 1)"
    )
    parser.add_argument(
        "--soglia", type=float, default=0.0,
        help="Differenza minima rispetto ai vicini per essere minimo (default: 0.0)"
    )
    parser.add_argument(
        "--salva", metavar="OUTPUT.CSV",
        help="Salva i minimi trovati in un file CSV"
    )

    args = parser.parse_args()

    # Lettura
    punti = leggi_csv(args.file_csv, args.col_x, args.col_y)

    # Rilevazione automatica: aggiorna i nomi colonna se serve
    col_x = args.col_x if args.col_x != "auto" else "x"
    col_y = args.col_y if args.col_y != "auto" else "y"

    # Analisi
    minimi_locali  = trova_minimi_locali(punti, args.finestra, args.soglia)
    minimo_globale = trova_minimo_globale(punti)
    distanze       = calcola_distanze(minimi_locali)

    # Stampa
    stampa_risultati(punti, minimi_locali, minimo_globale, distanze, col_x, col_y)

    # Salvataggio opzionale
    if args.salva:
        with open(args.salva, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["numero", "indice", col_x, col_y, "tipo"])
            ig = minimo_globale[0]
            for k, (idx, x, y) in enumerate(minimi_locali, 1):
                tipo = "globale" if idx == ig else "locale"
                writer.writerow([k, idx, x, y, tipo])
        print(f"[INFO] Minimi salvati in: {args.salva}")


if __name__ == "__main__":
    main()