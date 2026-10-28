import { useEffect, useState, type FormEvent } from "react";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { initializeApp } from "firebase/app";
import firebaseConfig from "../firebaseConfig";

type Course = { id: string; code: string; title: string; description: string };
type Draft = { code: string; title: string; description: string };
const emptyDraft: Draft = { code: "", title: "", description: "" };
const auth = getAuth(initializeApp(firebaseConfig));

async function requestCourses(path: string, method = "GET", body?: Draft): Promise<any> {
  const token = await auth.currentUser?.getIdToken();
  if (!token) throw new Error("Sign in to manage courses.");
  const response = await fetch(path, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

export default function MyCourses() {
  const [signedIn, setSignedIn] = useState(false);
  const [courses, setCourses] = useState<Course[]>([]);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [notice, setNotice] = useState("");

  async function reload() {
    const data = await requestCourses("/my/courses");
    setCourses(data.courses || []);
  }

  useEffect(() => onAuthStateChanged(auth, (user) => {
    setSignedIn(!!user);
    if (user) reload().catch((error: Error) => setNotice(error.message));
    else setCourses([]);
  }), []);

  async function save(event: FormEvent) {
    event.preventDefault();
    setNotice("");
    try {
      await requestCourses(editingId ? `/my/courses/${editingId}` : "/my/courses", editingId ? "PUT" : "POST", draft);
      setDraft(emptyDraft);
      setEditingId(null);
      await reload();
      setNotice("Course saved.");
    } catch (error) {
      setNotice((error as Error).message);
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this course?")) return;
    try {
      await requestCourses(`/my/courses/${id}`, "DELETE");
      await reload();
      setNotice("Course deleted.");
    } catch (error) {
      setNotice((error as Error).message);
    }
  }

  if (!signedIn) return <main><h1>My courses</h1><p>Sign in to manage courses.</p></main>;

  return (
    <main style={{ maxWidth: 760, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>My courses</h1>
      <p>Create and manage courses in your own account.</p>
      <form onSubmit={save} style={{ display: "grid", gap: "0.75rem" }}>
        <label>Code
          <input value={draft.code} maxLength={20} required onChange={(e) => setDraft({ ...draft, code: e.target.value })} />
        </label>
        <label>Title
          <input value={draft.title} maxLength={150} required onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
        </label>
        <label>Description
          <textarea value={draft.description} maxLength={1000} onChange={(e) => setDraft({ ...draft, description: e.target.value })} />
        </label>
        <div>
          <button type="submit">{editingId ? "Save changes" : "Add course"}</button>
          {editingId && <button type="button" onClick={() => { setEditingId(null); setDraft(emptyDraft); }}>Cancel</button>}
        </div>
      </form>
      {notice && <p role="status">{notice}</p>}
      <h2>Saved courses</h2>
      <ul>
        {courses.map((course) => (
          <li key={course.id}>
            <strong>{course.code}: {course.title}</strong>
            {course.description && <p>{course.description}</p>}
            <button type="button" onClick={() => { setEditingId(course.id); setDraft({ code: course.code, title: course.title, description: course.description }); }}>Edit</button>
            <button type="button" onClick={() => remove(course.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </main>
  );
}
