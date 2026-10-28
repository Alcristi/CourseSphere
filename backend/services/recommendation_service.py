"""Interpret a student question and retrieve grounded course recommendations."""

import json
import os

from config.query_types import load_query_types
from openai import OpenAI
from database.config import required_env
from models.course_catalog_model import CourseCatalogUnavailable
from models.course_model import CourseModel
from services.course_catalog_service import CourseCatalogService
from services.embedding_service import EmbeddingService
from services.user_service import UserService


COURSE_NAMESPACES = {"contents"}
REPHRASING_COUNT = 3


def _field(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


class RecommendationService:
    """Interpret questions and assemble course recommendations."""

    def __init__(self, query, user_data=None, history=None, *, client=None, embedding_model=None, index=None, catalog=None):
        self.query = query.strip() if isinstance(query, str) else ""
        self.user_data = user_data if isinstance(user_data, dict) else {}
        self.history = [
            {"role": item["role"], "content": item["content"]}
            for item in (history or [])[-8:]
            if isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and isinstance(item.get("content"), str)
        ]
        self.client = client
        self.query_types = load_query_types()
        self.catalog = catalog or CourseCatalogService()
        self.course_model = CourseModel(index=index)
        self.embedding_service = EmbeddingService(model=embedding_model)

    @classmethod
    def answer(cls, query, history, id_token):
        user_info = UserService.optional_profile(id_token)
        return cls(query, user_info, history).get_response_to_query()

    def understand_query(self):
        if self.client is None:
            self.client = OpenAI(api_key=required_env("OPENAI_API_KEY"), timeout=12.0, max_retries=0)

        prompt = f"""You are an academic advisor at Cornell. Classify the student's latest
question using the previous messages and profile. Return only a JSON object.

Available query types and their parameter schemas:
{json.dumps(self.query_types, ensure_ascii=False)}

Student profile: {json.dumps(self.user_data, ensure_ascii=False)}

Choose exactly one listed query_type and return its required values in a
parameters object. For "Course recommendation", also return up to
{REPHRASING_COUNT} short, concrete English rephrasing sentences describing
what a course offers from the faculty's perspective, and searches=["contents"].
For "Unsupported", include a concise clarification in response.
Do not invent facts about courses, majors, minors, or professors. The app will
look up course facts and handle unavailable catalogs after classification."""
        response = self.client.responses.create(
            model=os.getenv("OPENAI_QUERY_MODEL", "gpt-6-luna"),
            input=[{"role": "developer", "content": prompt}] + self.history + [{"role": "user", "content": self.query}],
            reasoning={"effort": "none"},
            text={"format": {"type": "json_object"}},
        )
        return json.loads(response.output_text)

    def course_information(self, course_code):
        if not isinstance(course_code, str) or not course_code.strip():
            return {"botResponse": "Which course code would you like to know about?", "newRecommendations": []}
        normalized = " ".join(course_code.upper().split())
        try:
            course = self.catalog.get_course_by_code(normalized)
        except CourseCatalogUnavailable:
            return {"botResponse": "The local course catalog is unavailable right now.", "newRecommendations": []}
        if course is None:
            return {"botResponse": f"I could not find {normalized} in the current catalog.", "newRecommendations": []}
        parts = [f"{normalized} is in the local catalog."]
        title = course.get("title")
        if isinstance(title, str) and title.strip():
            parts.append(f"Title: {title.strip()}.")
        description = course.get("estimated_description")
        if isinstance(description, str) and description.strip():
            parts.append(f"Estimated description: {description.strip()}")
        else:
            parts.append("No course description is available in the local catalog.")
        return {"botResponse": " ".join(parts), "newRecommendations": []}

    def search_courses(self, rephrasings, searches):
        best = {}
        for vector in self.embedding_service.embed(rephrasings):
            for namespace in searches:
                for match in self.course_model.search_similar(vector, namespace):
                    match_id = _field(match, "id", "")
                    course_id = match_id.split(":", 1)[0] if isinstance(match_id, str) else ""
                    if not course_id:
                        continue
                    score = float(_field(match, "score", 0) or 0)
                    if course_id not in best or score > best[course_id][0]:
                        best[course_id] = (score, _field(match, "metadata", {}) or {})
        distinct = []
        seen_titles = set()
        for course_id, scored in sorted(best.items(), key=lambda item: item[1][0], reverse=True):
            metadata = scored[1] if isinstance(scored[1], dict) else {}
            title = metadata.get("title") or course_id
            key = title.casefold() if isinstance(title, str) else course_id
            if key in seen_titles:
                continue
            seen_titles.add(key)
            distinct.append((course_id, scored))
            if len(distinct) == 3:
                break
        return distinct

    def get_response_to_query(self):
        if not self.query:
            return {"botResponse": "What would you like to study?", "newRecommendations": []}

        understood = self.understand_query()
        if not isinstance(understood, dict):
            raise ValueError("Query interpretation must be a JSON object")
        query_type = understood.get("query_type")
        allowed_types = {item["query_type"] for item in self.query_types}
        if not isinstance(query_type, str) or query_type not in allowed_types:
            return {"botResponse": "I can currently recommend courses. What kind of course are you looking for?", "newRecommendations": []}

        parameters = understood.get("parameters")
        parameters = parameters if isinstance(parameters, dict) else {}
        if query_type == "Info about course":
            return self.course_information(parameters.get("course_code"))
        if query_type in {"Info about major", "Info about minor", "Info about professor"}:
            subject = query_type.removeprefix("Info about ")
            return {"botResponse": f"I do not have a verified {subject} catalog yet.", "newRecommendations": []}
        if query_type == "Unsupported":
            response = understood.get("response")
            if not isinstance(response, str) or not response.strip():
                response = "Could you ask about a course or a course recommendation?"
            return {"botResponse": response, "newRecommendations": []}
        if query_type != "Course recommendation":
            return {"botResponse": "This question type is not available yet.", "newRecommendations": []}

        rephrasings = understood.get("rephrasing")
        if not isinstance(rephrasings, list):
            rephrasings = parameters.get("interests", [])
        searches = understood.get("searches")
        if not isinstance(searches, list):
            searches = ["contents"]
        if not isinstance(rephrasings, list):
            rephrasings = []
        rephrasings = [text.strip() for text in rephrasings[:REPHRASING_COUNT] if isinstance(text, str) and text.strip()]
        searches = list(dict.fromkeys(value for value in searches if value in COURSE_NAMESPACES)) or ["contents"]
        if not rephrasings:
            return {"botResponse": "Could you tell me more about the course you want?", "newRecommendations": []}

        matches = self.search_courses(rephrasings, searches)
        if not matches:
            return {"botResponse": "I could not find matching courses in the current catalog.", "newRecommendations": []}

        course_ids = [course_id for course_id, _ in matches]
        rows = self.course_model.rows(course_ids)
        reviews = self.course_model.reviews(course_ids)
        professors = self.course_model.professors(course_ids)
        recommendations = []
        for course_id, (_, metadata) in matches:
            row = rows.get(course_id, {})
            metadata = metadata if isinstance(metadata, dict) else {}
            recommendations.append({
                "type": "course",
                "data": {
                    "courseCode": course_id,
                    "name": row.get("title") or metadata.get("title") or row.get("name") or course_id,
                    "subjectCode": row.get("subject_code") or "",
                    "catalogLevel": row.get("catalog_level"),
                    "estimatedDescription": row.get("estimated_description") or "",
                    "associatedProfessors": professors.get(course_id, []),
                    "type": row.get("type") or metadata.get("type") or "",
                    "sectionNumber": "",
                    "location": "",
                    "days": "",
                    "time": "",
                    "dates": "",
                    "instructor": row.get("instructor") or metadata.get("instructor") or "",
                    "reviews": reviews.get(course_id, []),
                },
            })
        names = ", ".join(course_id for course_id, _ in matches)
        return {"botResponse": f"I found these courses in the catalog: {names}.", "newRecommendations": recommendations}
