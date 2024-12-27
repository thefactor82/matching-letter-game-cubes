import time
from itertools import product, permutations, islice
from multiprocessing import Pool, cpu_count, Manager
from math import ceil
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
def calcola_combinazioni_batch(batch):
    combinazioni = set()
    for permutazione in batch:
        combinazioni.update(''.join(combo) for combo in product(*permutazione))
    return combinazioni

# Funzione per aggiornare la barra di progresso
def aggiorna_progresso(queue, total):
    with tqdm(total=total, desc="Generazione combinazioni", unit="batch") as pbar:
        while True:
            aggiornamento = queue.get()
            if aggiornamento is None:
                break
            pbar.update(aggiornamento)

# Funzione per generare i batch come un generatore
def genera_batches(permutazioni, batch_size):
    iterator = iter(permutazioni)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            break
        yield batch

# Funzione per parallelizzare la generazione delle combinazioni
def genera_combinazioni_con_permutazioni_parallel(cubi, n):
    combinazioni = set()
    permutazioni = permutations(cubi, n)  # Generatore di permutazioni
    num_permutazioni = sum(1 for _ in permutations(cubi, n))  # Calcolo totale permutazioni
    batch_size = max(1, num_permutazioni // (cpu_count() * 4))  # Dividi in batch proporzionati
    batches = genera_batches(permutazioni, batch_size)  # Generatore per i batch

    # Usa una coda per gestire il progresso
    manager = Manager()
    progress_queue = manager.Queue()
    
    # Processo per la barra di progresso
    from multiprocessing import Process
    progresso = Process(target=aggiorna_progresso, args=(progress_queue, ceil(num_permutazioni / batch_size)))
    progresso.start()

    with Pool(processes=cpu_count()) as pool:
        for risultato in pool.imap_unordered(calcola_combinazioni_batch, batches):  # Iteriamo su batch generato
            combinazioni.update(risultato)
            progress_queue.put(1)  # Invia aggiornamenti per la barra

    progress_queue.put(None)  # Segnale di fine per la barra di progresso
    progresso.join()  # Attendi la chiusura della barra
    return combinazioni

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

    # Misura il tempo di esecuzione
    print("Elaborazione in corso...")
    start_time = time.time()

    combinazioni = genera_combinazioni_con_permutazioni_parallel(cubi, lunghezza_parola)

    elapsed_time = time.time() - start_time
    print(f"Tempo totale: {elapsed_time:.2f} secondi")

    # Filtra le parole valide
    parole_valide = sorted(word for word in combinazioni if word in italian_words)

    # Stampa le parole trovate e il numero totale
    print(f"\nParole di {lunghezza_parola} lettere trovate ({len(parole_valide)} in totale):")
    for parola in parole_valide:
        print(parola)
