# FrameIQ - Intelligent Entertainment Discovery

FrameIQ (formerly MovieHub) is a next-generation entertainment discovery platform that leverages advanced AI to provide hyper-personalized recommendations for movies, TV shows, and anime.

![FrameIQ Interface](images/FrameIQ-Intelligent-Entertainment-Discovery.jpg)

![FrameIQ Architecture](images/Gemini_Generated_Image_xoiv4uxoiv4uxoiv.png)

## 🌐 Live Demo

Check out the live demo on Google Cloud Run: [https://frameiq.com](https://frameiq-344233295407.asia-south1.run.app/)

## 🚀 Key Features

### 🧠 Advanced AI Chatbot (RAG + Hybrid Search)

- **Intelligent Retrieval:** Uses **Retrieval-Augmented Generation (RAG)** to query a vector database of over 10,000+ movies and TV shows.
- **Hybrid Search:** Combines semantic vector search (ChromaDB) with keyword search (BM25) for high-precision results.
- **Smart Fallback System:**
  1.  **LLM Knowledge:** First checks the LLM's internal knowledge.
  2.  **RAG Context:** Retrieves specific details from the vector database.
  3.  **TMDb Live Data:** Falls back to The Movie Database (TMDb) API for real-time data on new releases or obscure titles.
- **Anime Detection:** Specialized logic to detect and handle anime queries effectively.

### 🎨 Premium User Experience

- **FrameIQ Branding:** Sophisticated Purple/Gold/Teal color scheme with particle background animations.
- **Responsive Design:** Fully responsive UI built with Tailwind CSS.
- **Personalized Profiles:** Watchlists, wishlists, and viewing history tracking.

### ☁️ Modern Cloud Architecture

- **Vector Storage:** **ChromaDB Cloud** for scalable, serverless vector storage.
- **Deployment:** **Google Cloud Run** for serverless, auto-scaling application hosting.
- **Database:** PostgreSQL for robust user and media data management.
- **Image Hosting:** Cloudinary for optimized profile image delivery.

## 🛠️ Technical Implementation

### AI & RAG Architecture

The core of FrameIQ is its intelligent chat system:

1.  **User Query:** The user asks a question (e.g., "Find me a sci-fi movie like Interstellar").
2.  **Intent Analysis:** The system analyzes if the query is about movies, TV shows, or anime.
3.  **Hybrid Search:**
    - **Dense Retrieval:** Uses `all-MiniLM-L6-v2` embeddings to find semantically similar content in ChromaDB.
    - **Sparse Retrieval:** Uses BM25 to match specific keywords.
    - **Reranking:** Combines results using Reciprocal Rank Fusion (RRF).
4.  **Context Assembly:** Relevant context is fed into the LLMs.
5.  **Response Generation:** The LLM generates a natural language response.
6.  **TMDb Fallback:** If RAG confidence is low, the system queries TMDb API directly.

### Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla)
- **AI/ML:** Groq API (Multiple LLMS), ChromaDB (Vector DB), Sentence Transformers
- **Data Sources:** TMDb API, Hugging Face Datasets
- **Infrastructure:** Google Cloud Run, PostgreSQL, Cloudinary

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- API Keys: TMDb, Groq, Cloudinary
- ChromaDB Cloud Tenant/Database credentials
- PostgreSQL Database

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/RobinMillford/tv-movie-recommendations.git
    cd Tv-Movie-Recommendations-with-AI
    ```

2.  **Set up Virtual Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file:

    ```env
    SECRET_KEY=your_secret_key
    TMDB_API_KEY=your_tmdb_api_key
    GROQ_API_KEY=your_groq_api_key
    DATABASE_URL=postgresql://user:pass@host:5432/db
    CLOUDINARY_CLOUD_NAME=your_cloud_name
    CLOUDINARY_API_KEY=your_api_key
    CLOUDINARY_API_SECRET=your_api_secret

    # ChromaDB Cloud
    CHROMA_CLOUD_TENANT=your_tenant
    CHROMA_CLOUD_DATABASE=your_database
    CHROMA_CLOUD_EMAIL=your_email
    CHROMA_CLOUD_PASSWORD=your_password
    ```

5.  **Run the Application:**
    ```bash
    python app.py
    ```

## ☁️ Deployment

### Google Cloud Run

FrameIQ is optimized for Google Cloud Run:

1.  **Containerize:** `Dockerfile` is configured for production.
2.  **Build & Push:**
    ```bash
    gcloud builds submit --tag gcr.io/PROJECT_ID/frameiq-app
    ```
3.  **Deploy:**
    ```bash
    gcloud run deploy frameiq-app --image gcr.io/PROJECT_ID/frameiq-app --platform managed
    ```

### ChromaDB Cloud

Vector data is hosted on ChromaDB Cloud, ensuring persistence and scalability without managing local vector stores.

## 🤝 Contributing

Contributions are welcome! Please submit a Pull Request or open an Issue.

## 📄 License

AGPL-3.0 license. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- [TMDb](https://www.themoviedb.org/) for the extensive media database.
- [Groq](https://groq.com/) for ultra-fast LLM inference.
- [Chroma](https://www.trychroma.com/) for vector search capabilities.
