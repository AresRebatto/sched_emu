\# scheduler.py — Simulatore di scheduling CPU (OSTEP)



Versione estesa dello `scheduler.py` degli homework di OSTEP (\*CPU Scheduling\*).

Rispetto all'originale aggiunge:



\- \*\*arrival time\*\* per ogni job (`-a`, `-A`);

\- la policy \*\*STCF\*\* (\*Shortest Time-to-Completion First\*, SJF con preemption);

\- gestione della \*\*CPU idle\*\* quando nessun job è ancora arrivato;

\- metriche calcolate \*\*rispetto all'arrivo\*\* del job.



Compatibile con Python 2 e Python 3. Nessuna dipendenza esterna.



\---



\## Utilizzo base



```

python3 scheduler.py \[opzioni]

```



Senza `-c` il programma stampa il problema (lista dei job) e chiede di calcolare a mano

response, turnaround e wait. Rilanciandolo con \*\*gli stessi argomenti\*\* più `-c` stampa

la soluzione.



```bash

\# 1. genera il problema

python3 scheduler.py -p STCF -l 10,2,4 -a 0,1,3



\# 2. verifica la soluzione

python3 scheduler.py -p STCF -l 10,2,4 -a 0,1,3 -c

```



\---



\## Opzioni



| Opzione | Lunga | Default | Descrizione |

|---|---|---|---|

| `-s` | `--seed` | `0` | Seed del generatore casuale. |

| `-j` | `--jobs` | `3` | Numero di job (solo job casuali). |

| `-l` | `--jlist` | — | Lista di durate separate da virgola. Sostituisce i job casuali. |

| `-a` | `--alist` | — | Lista di arrival time separati da virgola, \*\*uno per job\*\*. Se omessa, tutti arrivano a `t=0`. |

| `-A` | `--maxarrival` | `0` | Arrival time massimo dei job \*\*casuali\*\*: ogni arrival è un intero in `\[0, maxarrival)`. Con `0` tutti arrivano a `t=0`. |

| `-m` | `--maxlen` | `10` | Durata massima di un job casuale. |

| `-p` | `--policy` | `FIFO` | Policy: `FIFO`, `SJF`, `STCF`, `RR`. |

| `-q` | `--quantum` | `1` | Lunghezza del time slice (solo `RR`). |

| `-c` | — | off | Calcola e stampa la soluzione. |



\### Note sulle opzioni



\- `-a` richiede \*\*esattamente tanti valori quanti sono i job\*\*, altrimenti il programma termina con errore.

\- `-a` ha la precedenza su `-A`. `-A` ha effetto solo con job casuali (cioè senza `-l`).

\- Le durate e gli arrival possono essere decimali quando si usa `-l` / `-a` (es. `-l 2.5,4`).

\- Gli arrival casuali vengono estratti \*\*dopo\*\* le durate: a parità di seed, le durate dei job

&#x20; sono identiche a quelle della versione originale.

\- Una policy non valida viene rifiutata subito (exit code `1`).



\---



\## Policy



| Policy | Preemptive | Criterio di scelta |

|---|---|---|

| `FIFO` | No | Ordine di arrivo. |

| `SJF` | No | Tra i job \*\*già arrivati\*\*, quello con durata minore. Una volta partito, un job finisce. |

| `STCF` | Sì | Tra i job già arrivati, quello con \*\*tempo rimanente\*\* minore. Ad ogni nuovo arrivo la scelta viene rivalutata. |

| `RR` | Sì | Round Robin con quantum `-q`. |



\### Regole di spareggio



\- `FIFO`: `(arrival, jobnum)`

\- `SJF`: `(durata, arrival, jobnum)`

\- `STCF`: `(tempo rimanente, arrival, jobnum)`

\- `RR`: i job che arrivano \*\*durante\*\* un quantum entrano in coda \*\*prima\*\* del job appena

&#x20; interrotto. È la convenzione più comune; se il tuo corso usa l'ordine opposto, basta invertire

&#x20; le istruzioni `admit(...)` e `runlist.append(job)` in `sim\_rr`.



\### CPU idle



Se la coda dei job pronti è vuota ma ci sono job che devono ancora arrivare, la CPU resta ferma

fino al prossimo arrivo e la traccia riporta una riga:



```

\[ time  5.00 ] CPU idle until 10.00

```



\---



\## Metriche



Tutte le metriche sono misurate a partire dall'\*\*arrival time\*\* del job:



```

response   = istante del primo run  - arrival

turnaround = istante di completamento - arrival

wait       = turnaround - durata

```



Con tutti gli arrival a `0` i risultati coincidono con quelli dello script originale.

`wait` è il tempo totale passato in coda pronti (escluso il tempo di esecuzione).



\---



\## Esempi



\### STCF con arrival diversi



```bash

python3 scheduler.py -p STCF -l 10,2,4 -a 0,1,3 -c

```



```

Execution trace:

&#x20; \[ time  0.00 ] Run job 0 for 1.00 secs

&#x20; \[ time  1.00 ] Run job 1 for 2.00 secs ( DONE at 3.00 )

&#x20; \[ time  3.00 ] Run job 2 for 4.00 secs ( DONE at 7.00 )

&#x20; \[ time  7.00 ] Run job 0 for 9.00 secs ( DONE at 16.00 )



Final statistics:

&#x20; Job   0 -- Response: 0.00  Turnaround 16.00  Wait 6.00

&#x20; Job   1 -- Response: 0.00  Turnaround 2.00  Wait 0.00

&#x20; Job   2 -- Response: 0.00  Turnaround 4.00  Wait 0.00



&#x20; Average -- Response: 0.00  Turnaround 7.33  Wait 2.00

```



Il job 0 parte per primo, viene interrotto all'arrivo del job 1 (più corto), poi del job 2,

e riprende solo quando entrambi sono terminati.



\### Round Robin con CPU idle



```bash

python3 scheduler.py -p RR -q 2 -l 5,3 -a 0,10 -c

```



```

Execution trace:

&#x20; \[ time  0.00 ] Run job   0 for 2.00 secs

&#x20; \[ time  2.00 ] Run job   0 for 2.00 secs

&#x20; \[ time  4.00 ] Run job   0 for 1.00 secs ( DONE at 5.00 )

&#x20; \[ time  5.00 ] CPU idle until 10.00

&#x20; \[ time 10.00 ] Run job   1 for 2.00 secs

&#x20; \[ time 12.00 ] Run job   1 for 1.00 secs ( DONE at 13.00 )

```



\### SJF con job casuali e arrival casuali



```bash

python3 scheduler.py -p SJF -j 3 -s 1 -A 6 -c

```



Genera 3 job con seed 1, arrival casuali in `\[0, 6)`, e li schedula con SJF non-preemptive.



\### Confronto tra policy sullo stesso workload



```bash

for p in FIFO SJF STCF; do

&#x20; echo "=== $p ==="

&#x20; python3 scheduler.py -p $p -l 10,2,4 -a 0,1,3 -c | tail -3

done

```



\---



\## Struttura del codice



| Funzione | Ruolo |

|---|---|

| `sim\_nonpreemptive(jobs, policy)` | Simula `FIFO` e `SJF`. |

| `sim\_stcf(jobs)` | Simula `STCF`; unisce in un'unica riga i segmenti consecutivi dello stesso job. |

| `sim\_rr(jobs, quantum)` | Simula `RR`. |

| `admit(pending, ready, t)` | Sposta in coda pronti i job con `arrival <= t`. |



Ogni simulatore stampa la traccia e restituisce due dizionari, `first\_run` e `completion`,

da cui il blocco finale calcola response, turnaround e wait.



Per aggiungere una nuova policy: scrivi una funzione `sim\_xxx` con la stessa interfaccia,

aggiungi il nome alla tupla di policy valide in cima allo script e richiamala nel blocco

`if options.solve`.



\---



\## Errori comuni



| Messaggio | Causa |

|---|---|

| `Error: alist has N entries but there are M jobs` | `-a` ha un numero di valori diverso dal numero di job. |

| `Error: Policy X is not available.` | Policy diversa da `FIFO`, `SJF`, `STCF`, `RR`. |

