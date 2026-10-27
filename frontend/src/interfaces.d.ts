// A file defining interfaces used in the frontend //



interface ProfessorCardProps {
  name: string;
  title: string;
  departments: string;
  imageUrl: string;
  email: string;
  phone: string;
  education: string;
  reviews: string[];
}

interface CourseCardProps {
  courseCode: string;
  name: string;
  subjectCode: string;
  catalogLevel: number | null;
  estimatedDescription: string;
  associatedProfessors: string[];
  type: string;
  sectionNumber: string;
  location: string;
  days: string;
  time: string;
  dates: string;
  instructor: string;
  reviews: string[];
}


interface CourseRecommendation {
  type: 'course';
  data: {
    courseCode: string;
    name: string;
    subjectCode: string;
    catalogLevel: number | null;
    estimatedDescription: string;
    associatedProfessors: string[];
    type: string;
    sectionNumber: string;
    location: string;
    days: string;
    time: string;
    dates: string;
    instructor: string;
    reviews: string[];
  };
}

interface ProfessorRecommendation {
  type: 'professor';
  data: {
    name: string;
    title: string;
    departments: string;
    imageUrl: string;
    email: string;
    phone: string;
    education: string;
    reviews: string[];
  };
}



interface Chat {
  id: string;
  title: string;
  timestamp: string;
}

type Recommendation = CourseRecommendation | ProfessorRecommendation;


type Content = string | { botResponse: string; newRecommendations: (CourseRecommendation | ProfessorRecommendation)[] };

interface Message {
  sender: "user" | "assistant";
  content: string;
  messageID: string;
  timestamp: string;
}
