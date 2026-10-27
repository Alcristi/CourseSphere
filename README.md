# CourseSphere

CourseSphere helps students find courses. The frontend uses React/Vite; the API uses Flask.

## Local setup

1. Copy `frontend/.env.example` to `frontend/.env` and fill in the Firebase **web app** settings. `VITE_*` values are public in the generated browser bundle. Restrict the Firebase API key and enforce Firebase Authentication and Realtime Database rules in the Firebase console.
2. Copy `backend/.env.example` to `backend/.env`. Fill in the OpenAI and Pinecone keys plus the Firebase **Admin service account** fields (`FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`, `FIREBASE_DATABASE_URL`). Copy the private key as one double-quoted value with `\n` between lines. These values must stay on the server.
3. From `backend/`, install `requirements.txt` and run `python app.py`. From `frontend/`, run `npm install` and `npm run dev`.

Both `.env` files are ignored by Git.

A Firebase Admin service account is required to start the current backend. The repository does not contain one. If a private key was ever committed, rotate it: deleting the file from the current checkout does not remove it from Git history.

See [backend architecture](document/ARCHITECTURE.md) for code organization, the course catalog API, and the request flow.
