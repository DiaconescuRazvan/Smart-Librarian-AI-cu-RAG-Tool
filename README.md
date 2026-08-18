# 📚 Smart Librarian – AI cu RAG + Tool Calling

Smart Librarian este un chatbot AI dezvoltat în Python care recomandă cărți folosind **Retrieval-Augmented Generation (RAG)** cu **ChromaDB**, **OpenAI Embeddings** și **OpenAI GPT**.

După recomandarea unei cărți, chatbotul utilizează **Function Calling** pentru a obține automat rezumatul complet. În plus, aplicația poate genera o imagine reprezentativă pentru cartea recomandată și poate transforma recomandarea și rezumatul în fișier audio.

---

# Funcționalități

- Recomandă cărți pe baza preferințelor utilizatorului
- Căutare semantică folosind ChromaDB
- Embeddings OpenAI (`text-embedding-3-small`)
- Recomandare conversațională folosind GPT
- Function Calling pentru obținerea rezumatului complet
- Filtru pentru limbaj nepotrivit
- Generare imagine pentru cartea recomandată
- Generare fișier audio (Text-to-Speech)
- Conversații continue cu istoric salvat local
- Tab pentru vizualizarea conversațiilor anterioare
- Trimiterea mesajelor cu tasta Enter
- Răspunsuri limitate la subiecte despre cărți
- Interfață web React + API FastAPI

---

# Tehnologii folosite

- Python 3.14
- OpenAI GPT
- OpenAI Embeddings
- OpenAI Image Generation
- OpenAI Text-to-Speech
- ChromaDB
- python-dotenv
- FastAPI și Uvicorn
- React și Vite

---

# Structura proiectului

```
smart-librarian/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── librarian.py
│   │   ├── books.py
│   │   ├── models.py
│   │   └── vector_store.py
│   ├── data/book_summaries.json
│   ├── chroma_db/
│   ├── generated_images/
│   ├── generated_audio/
│   ├── conversations.json          # creat automat, ignorat de Git
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── start.bat                        # pornește aplicația cu un singur click
├── start-hidden.vbs                 # pornește serviciile fără ferestre PowerShell
└── README.md
```

---

# Instalare

## 1. Clonează proiectul

```bash
git clone <repository-url>
cd smart-librarian
```

sau descarcă proiectul și deschide folderul în Visual Studio Code.

---

## 2. Creează un mediu virtual (opțional)

Windows

```powershell
py -m venv .venv
```

Activează-l

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 3. Instalează dependențele

```powershell
py -m pip install -r backend\requirements.txt

cd frontend
npm install
```

---

## 4. Configurează OpenAI API Key

În folderul `backend`, creează fișierul

```
.env
```

și adaugă

```env
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Nu salva cheia reală în Git și nu o introduce în fișiere urmărite de Git. Fișierul
`backend/.env` este ignorat prin `.gitignore`, iar `backend/.env.example` conține
doar valori demonstrative.

---

# Rularea aplicației

### Varianta recomandată: un singur click

Din rădăcina proiectului, rulează:

```powershell
.\start.bat
```

Poți face și dublu-click pe `start.bat`. Scriptul pornește backendul,
frontendul și deschide automat `http://localhost:5173`.

### Varianta manuală

Într-un terminal pornește backendul:

```powershell
cd backend
py -3 -m uvicorn app.main:app --reload --port 8000
```

Într-un al doilea terminal pornește frontendul:

```powershell
cd frontend
npm run dev
```

Deschide `http://localhost:5173` în browser. API-ul este disponibil la
`http://localhost:8000`, iar documentația interactivă FastAPI la
`http://localhost:8000/docs`.

La prima rulare aplicația:

- încarcă cărțile din fișierul JSON;
- generează embeddings folosind OpenAI;
- creează baza vectorială ChromaDB;
- salvează toate documentele în `chroma_db`.

La rulările următoare baza vectorială este reutilizată.

---

# Exemple de întrebări

```
Vreau o carte despre libertate și control social.
```

```
Ce recomanzi pentru cineva care iubește poveștile fantastice?
```

```
Vreau o carte despre magie și prietenie.
```

```
Ce este 1984?
```

```
Vreau o carte despre război.
```

---

# Cum funcționează aplicația

1. Utilizatorul introduce o întrebare.
2. Întrebarea este transformată într-un embedding OpenAI.
3. ChromaDB caută cele mai apropiate cărți semantic.
4. Primele rezultate sunt trimise către GPT.
5. GPT recomandă cartea cea mai potrivită.
6. GPT apelează tool-ul `get_summary_by_title()`.
7. Tool-ul returnează rezumatul complet.
8. Utilizatorul poate genera opțional o imagine reprezentativă pentru carte.
9. Utilizatorul poate genera opțional o versiune audio a recomandării și rezumatului.
10. Întrebările și răspunsurile sunt salvate în conversația curentă.
11. Istoricul poate fi încărcat din tabul `Conversații`.

---

# Arhitectura aplicației

```
                 Utilizator
                      │
                      ▼
            Întrebare utilizator
                      │
                      ▼
          OpenAI Embeddings
                      │
                      ▼
                ChromaDB
                      │
          Top rezultate relevante
                      │
                      ▼
              OpenAI GPT
                      │
             Recomandare carte
                      │
                      ▼
      Tool Calling (get_summary_by_title)
                      │
                      ▼
             Rezumat complet
          ┌───────────┴───────────┐
          ▼                       ▼
  Image Generation         Text-to-Speech
          │                       │
          ▼                       ▼
 Imagine PNG salvată      Fișier MP3 salvat
```

---

# Tool Calling

Aplicația expune funcția

```python
get_summary_by_title(title: str)
```

Modelul OpenAI apelează automat această funcție după ce selectează cartea recomandată. Funcția returnează rezumatul complet al cărții din baza locală.

---

# Image Generation

După recomandarea unei cărți, utilizatorul poate alege să genereze o imagine reprezentativă.

Aplicația trimite către OpenAI un prompt bazat pe titlul cărții și generează o imagine inspirată de temele și atmosfera acesteia.

Imaginea este salvată local în folderul:

```
backend/generated_images/
```

---

# Text-to-Speech

După afișarea recomandării și a rezumatului, utilizatorul poate genera și o versiune audio.

Aplicația utilizează modelul OpenAI Text-to-Speech pentru a transforma textul în vorbire și salvează rezultatul în format MP3 în folderul:

```
backend/generated_audio/
```

Acest fișier poate fi redat ulterior în orice player audio.

---

# Filtru limbaj nepotrivit

Înainte ca mesajul utilizatorului să fie trimis către modelul OpenAI, aplicația verifică dacă acesta conține cuvinte ofensatoare.

Dacă sunt detectate astfel de cuvinte:

- mesajul nu este trimis către LLM;
- utilizatorul primește un mesaj prin care este rugat să folosească un limbaj respectuos.

Astfel se evită consumul inutil de tokeni și se asigură o interacțiune civilizată.

---

# Conversații și confidențialitate

Fiecare conversație primește un identificator propriu. La următoarea întrebare,
istoricul recent este transmis modelului pentru a păstra contextul dialogului.
Conversațiile sunt salvate local în `backend/conversations.json` și sunt ignorate
de Git. Fișierul poate conține mesaje private și nu trebuie urcat pe GitHub.

În interfață:

- mesajele utilizatorului și ale librarianului sunt afișate ca într-un chat normal;
- `Enter` trimite întrebarea;
- `Shift + Enter` introduce o linie nouă;
- bara de scriere se golește după trimitere;
- răspunsul nou derulează automat conversația până la ultimul mesaj;
- tabul `Conversații` permite încărcarea dialogurilor salvate.

---

# Cerințe implementate

## Obligatorii

- ✔ Minimum 10 cărți
- ✔ ChromaDB ca Vector Store
- ✔ OpenAI Embeddings
- ✔ Retrieval-Augmented Generation (RAG)
- ✔ OpenAI GPT
- ✔ Function Calling
- ✔ Tool `get_summary_by_title()`
- ✔ API REST FastAPI
- ✔ Interfață web React

## Opționale

- ✔ Filtru limbaj nepotrivit
- ✔ Generare imagine pentru cartea recomandată
- ✔ Generare fișier audio (Text-to-Speech)

---

# Autor

Smart Librarian – AI cu RAG + Tool Calling