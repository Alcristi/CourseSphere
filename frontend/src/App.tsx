import { ThemeProvider } from "@mui/material";
import { createTheme } from '@mui/material/styles';
import { initializeApp } from "firebase/app";
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Footer from "./components/Footer/Footer";
import Header from "./components/header/Header";
import firebaseConfig from "./firebaseConfig";
import Dashboard from "./pages/dashboard/Dashboard";
import MyCourses from "./pages/MyCourses";
import Home from "./pages/home/Home";
import Login from "./pages/login/Login";
import SignUp from "./pages/signup/SignUp";


const app = initializeApp(firebaseConfig);
console.log(app.name)

const theme = createTheme({
  palette: {
    primary: {
      main: '#5c6bc0',
    },
    secondary: {
      main: '#ff4081',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    h1: {
      fontSize: '2rem',
    },
  },
  spacing: 8,
});

export default function App() {
  return (
      <ThemeProvider theme={theme}>
        <Header></Header>
        <Router>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/my-courses" element={<MyCourses />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<SignUp />} />
          </Routes>
        </Router>
        <Footer></Footer>
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="light"
        />
      </ThemeProvider>
  );
}
