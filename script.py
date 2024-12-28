import time
from itertools import permutations, product
from multiprocessing import Pool, cpu_count, Manager
from tqdm import tqdm

# Funzione per caricare il dizionario italiano
def carica_dizionario(file_path):
    try:
        with open(file_path, 'r') as f:
            return set(word.strip().lower() for word in f)
    except FileNotFoundError:
        print(f"Errore: Il file '{file_path}' non è stato trovato.")
        exit(1)

# Funzione per calcolare combinazioni da un batch di permutazioni
def calcola_combinazioni_batch(args):
    batch, file_path = args
    risultati_batch = set()  # Usa un set per rimuovere duplicati
    for permutazione in batch:
        for combo in product(*permutazione):
            risultati_batch.add(''.join(combo))

    if risultati_batch:
        # Scrivi solo combinazioni uniche nel file
        with open(file_path, 'a') as f:
            f.write('\n'.join(risultati_batch) + '\n')
    return len(risultati_batch)

# Funzione per gestire la barra di progresso
def aggiorna_progresso(queue, total):
    with tqdm(total=total, desc="Generazione combinazioni", unit="batch") as pbar:
        while True:
            aggiornamento = queue.get()
            if aggiornamento is None:
                break
            pbar.update(aggiornamento)

# Funzione per parallelizzare la generazione delle combinazioni
def genera_combinazioni_con_permutazioni_parallel(cubi, n, output_file):
    permutazioni = list(permutations(cubi, n))  # Convertiamo in lista per prevenire consumo accidentale
    batch_size = max(1, len(permutazioni) // (cpu_count() * 4))
    batches = [permutazioni[i:i + batch_size] for i in range(0, len(permutazioni), batch_size)]

    # Coda per la barra di progresso
    manager = Manager()
    progress_queue = manager.Queue()

    # Barra di progresso in un processo separato
    from multiprocessing import Process
    progresso = Process(target=aggiorna_progresso, args=(progress_queue, len(batches)))
    progresso.start()

    args = [(batch, output_file) for batch in batches]

    with Pool(processes=cpu_count()) as pool:
        for risultato in pool.imap_unordered(calcola_combinazioni_batch, args):
            progress_queue.put(1)  # Invia aggiornamenti alla barra di progresso

    progress_queue.put(None)
    progresso.join()

if __name__ == '__main__':
    # Lettere disponibili sui cubi
    cubi_base = [
        ['a', 'k', 'x', 'p', 'l', 'n', 'd', 'u'],      # Cubo 1
        ['t', 'k', 'i', 'o', 'r', 's'],                # Cubo 2
        ['i', 'd', 'v', 'b', 'e', 'f', 'p', 'q'],      # Cubo 3
        ['c', 'e', 'g', 'h', 'n', 'm', 'u']            # Cubo 4
    ]

    # Carica il dizionario italiano
    italian_words = carica_dizionario('ITA.txt')

    # Chiedi all'utente il numero di lettere
    while True:
        try:
            lunghezza_parola = int(input("Inserisci il numero di lettere delle parole da cercare (3-8): "))
            if 3 <= lunghezza_parola <= 8:
                break
            else:
                print("Inserisci un numero tra 3 e 8.")
        except ValueError:
            print("Inserisci un numero valido.")

    # Aggiorna i cubi in base alla lunghezza
    if lunghezza_parola > 4:
        cubi = cubi_base + cubi_base  # Raddoppia i cubi
    else:
        cubi = cubi_base

    # File di output
    output_file = f"parole_{lunghezza_parola}_lettere.txt"

    # Cancella il file di output esistente
    with open(output_file, 'w') as f:
        pass

    # Misura il tempo di esecuzione
    print("Elaborazione in corso...")
    start_time = time.time()

    genera_combinazioni_con_permutazioni_parallel(cubi, lunghezza_parola, output_file)

    elapsed_time = time.time() - start_time
    print(f"Tempo totale: {elapsed_time:.2f} secondi")

    print("Rimozione duplicati...")
    with open(output_file, 'r') as f:
        combinazioni_uniche = set(line.strip() for line in f)

    # Filtra le parole valide
    print(f"Filtraggio delle parole valide in corso...")
    parole_valide = sorted(word for word in combinazioni_uniche if word in italian_words)

    print(f"Combinazioni generate: {len(combinazioni_uniche)}")

    # Salva le parole valide su file
    valid_file = f"parole_valide_{lunghezza_parola}_lettere.txt"
    with open(valid_file, 'w') as f:
        f.write('\n'.join(parole_valide))

    print(f"Parole valide salvate in '{valid_file}' ({len(parole_valide)} in totale).")
